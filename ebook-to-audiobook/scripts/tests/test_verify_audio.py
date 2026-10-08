import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
import verify_audio as va


class WerTests(unittest.TestCase):
    def test_word_errors_counts_operations(self):
        r = va.word_errors("The quick brown fox", "the quick red fox jumps")
        self.assertEqual((r["substitutions"], r["deletions"], r["insertions"]), (1, 0, 1))
        self.assertAlmostEqual(r["wer"], 2 / 4)

    def test_punctuation_and_case_ignored(self):
        self.assertEqual(va.word_errors("Hello, World!", "hello world")["wer"], 0)

    def test_empty_reference_semantics(self):
        self.assertEqual(va.word_errors("", "")["wer"], 0.0)
        self.assertIsNone(va.word_errors("", "noise")["wer"])

    def test_spaced_picks_even_coverage(self):
        self.assertEqual(va.spaced(list(range(10)), 3), [0, 4, 9])
        self.assertEqual(va.spaced([1, 2], 5), [1, 2])
        with self.assertRaises(va.VerificationError):
            va.spaced([1], 0)


class SelectionTests(unittest.TestCase):
    def make_root(self, tmp):
        root = Path(tmp)
        (root / "chunks").mkdir()
        (root / "refs").mkdir()
        manifest = root / "chapter.json"
        manifest.write_text(json.dumps({"voices": {
            "narrator": {"description": "d", "reference_text": "ref words here"},
            "pinned": {"reference_audio": "../v.wav"},
        }}))
        (root / "refs" / "narrator.wav").write_bytes(helpers.make_wav())
        for i in range(1, 6):
            wav = root / "chunks" / f"{i:06d}.wav"
            wav.write_bytes(helpers.make_wav())
            wav.with_suffix(".json").write_text(json.dumps(
                {"request": {"item": {"text": f"chunk text {i}", "speaker": "narrator"}}}))
        return root, manifest

    def test_auto_selection_uses_refs_then_spaced_chunks_and_skips_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = self.make_root(tmp)
            samples, selection = va.select_samples(manifest, root, "all", None, 3)
            self.assertEqual([s.kind for s in samples], ["ref", "chunk", "chunk", "chunk"])
            self.assertEqual(selection["available_chunks"], 5)
            self.assertEqual(samples[0].expected, "ref words here")
            self.assertEqual(samples[-1].expected, "chunk text 5")

    def test_sample_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(va.VerificationError):
                va.sample_from_object({"path": "a.mp3", "expected": "x", "speaker": "s", "kind": "chunk"}, Path(tmp))
            with self.assertRaises(va.VerificationError):
                va.sample_from_object({"path": "a.wav", "expected": "x", "speaker": "s", "kind": "other"}, Path(tmp))

    def test_output_cannot_clobber_renderer_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest = self.make_root(tmp)
            samples, _ = va.select_samples(manifest, root, "chunks", None, 2)
            for bad in (root / "metrics.json", root / "chunks" / "x.json", manifest, root / "out.txt"):
                with self.assertRaises(va.VerificationError):
                    va.validate_output(bad, samples, manifest, None, root)
            va.validate_output(root / "qa-chunks.json", samples, manifest, None, root)


class TranscribeTests(unittest.TestCase):
    def test_command_is_cpu_only_niced_and_bounded(self):
        command = va.docker_command(900)
        self.assertIn("CUDA_VISIBLE_DEVICES=", command)
        self.assertIn("/usr/bin/nice", command)
        self.assertTrue(any(part.endswith("s") and part.replace(".", "").rstrip("s").isdigit() for part in command))

    def test_parse_records_flags_protocol_errors(self):
        good = {"path": "a", "model_revision": va.MODEL_REVISION, "status": "ok", "transcript": "hi",
                "wall_seconds": 1.0, "model_load_seconds": 2.0}
        out = (json.dumps(good) + "\n" + json.dumps({**good, "path": "zzz"}) + "\nnot json\n").encode()
        results, errors = va.parse_records(out, {"a", "b"})
        self.assertIn("a", results)
        self.assertEqual(len(errors), 2)

    def test_verify_end_to_end_with_mocked_asr(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "c.wav"
            wav.write_bytes(helpers.make_wav())
            sample = va.Sample(wav, "the cat sat", "narrator", "chunk")

            def fake(records, timeout):
                row = {"path": records[0]["path"], "model_revision": va.MODEL_REVISION, "status": "ok",
                       "transcript": "the cat sat down", "wall_seconds": 1.0, "model_load_seconds": 1.0}
                return {records[0]["path"]: row}, {"timed_out": False, "error": None, "protocol_errors": [], "returncode": 0}

            with mock.patch.object(va, "transcribe_records", fake):
                report = va.verify([sample], 10, {"source": "test"})
            self.assertEqual(report["status"], "complete")
            self.assertEqual(report["summary"]["insertions"], 1)
            self.assertAlmostEqual(report["summary"]["micro_wer"], 1 / 3)

    def test_unavailable_asr_leaves_samples_unscored_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "c.wav"
            wav.write_bytes(helpers.make_wav())
            with mock.patch.object(va.subprocess, "Popen", side_effect=OSError("no docker")):
                report = va.verify([va.Sample(wav, "x y", "n", "chunk")], 10, {})
            self.assertEqual(report["status"], "incomplete")
            self.assertIsNone(report["summary"]["micro_wer"])


if __name__ == "__main__":
    unittest.main()
