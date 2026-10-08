import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
import render_chapter as rc
from abk_common import AbkError, read_json, wav_metadata

DESIGN = "Warm mature woman, measured literary delivery."
REFTEXT = "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window."


def manifest(extra_voices=None, segments=None):
    return {
        "title": "Tiny", "chapter": 1, "settings": {"cfg": 2.0, "steps": 12},
        "voices": {"narrator": {"description": DESIGN, "reference_text": REFTEXT},
                   "boy": {"description": "Brisk boy", "reference_text": REFTEXT}, **(extra_voices or {})},
        "segments": segments or [
            {"speaker": "narrator", "text": "It was a grey morning. The old man coughed twice.", "paragraph": 1},
            {"speaker": "boy", "text": "Where is the tea?", "paragraph": 1},
            {"speaker": "narrator", "text": "Nobody answered him.", "paragraph": 2},
        ],
    }


def fake_master(raw, mastered, mp3, rate):
    shutil.copyfile(raw, mastered)
    mp3.write_bytes(b"ID3fake")


class ChunkTests(unittest.TestCase):
    def test_chunks_cover_text_exactly_and_respect_limits(self):
        text = " ".join(f"Sentence number {i} is here." for i in range(80))
        chunks = rc.chunk_text(text, target=100, sentence_max=150)
        self.assertEqual(" ".join(chunks), text)
        self.assertTrue(all(len(c) <= 150 for c in chunks))
        self.assertGreater(len(chunks), 10)

    def test_long_sentence_splits_on_punctuation_then_whitespace(self):
        text = "word, " * 60 + "end."
        chunks = rc.chunk_text(text, target=80, sentence_max=120)
        self.assertEqual(" ".join(chunks), rc.normalized(text))

    def test_unbreakable_word_and_empty_refused(self):
        with self.assertRaises(AbkError):
            rc.chunk_text("x" * 700)
        with self.assertRaises(AbkError):
            rc.chunk_text("   ")


class ManifestTests(unittest.TestCase):
    def test_validation_rules(self):
        rc.validate_manifest(manifest())
        bad = manifest()
        bad["voices"]["narrator"]["description"] = "uses (parens)"
        with self.assertRaises(AbkError):
            rc.validate_manifest(bad)
        bad = manifest()
        bad["segments"][0]["speaker"] = "ghost"
        with self.assertRaises(AbkError):
            rc.validate_manifest(bad)
        bad = manifest()
        bad["settings"] = {"cfg": 9}
        with self.assertRaises(AbkError):
            rc.validate_manifest(bad)
        bad = manifest()
        bad["segments"][2]["paragraph"] = 0
        with self.assertRaises(AbkError):
            rc.validate_manifest(bad)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.manifest_path = self.dir / "chapter.json"
        self.manifest_path.write_text(json.dumps(manifest()))
        self.out = self.dir / "audio"
        self.engine = rc.Engine(core_container="vox")
        self.fake = helpers.FakeEngine()
        patcher = mock.patch.object(rc.subprocess, "run", self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        master = mock.patch.object(rc, "master_audio", fake_master)
        master.start()
        self.addCleanup(master.stop)

    def prepared(self):
        return rc.prepare(self.manifest_path, self.out, self.engine)

    def test_synth_command_targets_core_container_or_host(self):
        self.assertEqual(rc.Engine(core_container="vox").synth_command()[:4], ["docker", "exec", "-i", "vox"])
        self.assertEqual(rc.Engine(core_container="").synth_command()[0], "curl")

    def test_prepare_counts_tokens_and_is_idempotent(self):
        plan = self.prepared()
        self.assertEqual(len(plan["designs"]), 2)
        self.assertEqual(plan["designs"][0]["text"], f"({'Brisk boy'}){REFTEXT}")
        self.assertEqual(plan["model_revision"], "a" * 40)
        self.assertEqual(rc.prepare(self.manifest_path, self.out, self.engine), plan)
        changed = manifest()
        changed["segments"][2]["text"] = "Somebody answered him."
        self.manifest_path.write_text(json.dumps(changed))
        with self.assertRaises(AbkError):
            rc.load_plan(self.manifest_path, self.out, self.engine)

    def test_unused_voice_is_never_designed(self):
        data = manifest(extra_voices={"ghost": {"description": "Unused", "reference_text": REFTEXT}})
        self.manifest_path.write_text(json.dumps(data))
        plan = self.prepared()
        self.assertEqual([d["id"] for d in plan["designs"]], ["boy", "narrator"])

    def test_full_render_then_resume_costs_zero_calls(self):
        plan = self.prepared()
        rc.voices(plan, self.out, self.engine)
        design_calls = len(self.fake.calls)
        self.assertEqual(design_calls, 2)
        self.assertTrue(self.fake.calls[0]["text"].startswith("("))
        self.assertNotIn("reference_audio_b64", self.fake.calls[0])
        result = rc.render(plan, self.out, self.engine)
        self.assertEqual(result["status"], "assembled")
        chunk_calls = self.fake.calls[design_calls:]
        self.assertEqual(len(chunk_calls), len(plan["chunks"]))
        self.assertTrue(all("reference_audio_b64" in c and not c["text"].startswith("(") for c in chunk_calls))
        wav = wav_metadata(self.out / "chapter.raw.wav")
        self.assertGreater(result["raw"]["pause_frames"], 0)
        self.assertEqual(wav["frames"], result["raw"]["wav"]["frames"])
        before = len(self.fake.calls)
        again = rc.render(plan, self.out, self.engine)
        self.assertEqual(again["new_calls"], 0)
        self.assertEqual(len(self.fake.calls), before)
        report = rc.report(self.out)
        self.assertEqual(report["totals"]["failed_calls"], 0)
        self.assertEqual(report["by_phase"]["design"]["requests"], 2)

    def test_preview_concatenates_references_in_cast_order(self):
        plan = self.prepared()
        rc.voices(plan, self.out, self.engine)
        with mock.patch.object(rc, "encode_mp3", lambda wav, mp3: mp3.write_bytes(b"ID3")):
            result = rc.preview(plan, self.out, self.engine)
        self.assertEqual(result["order"], ["boy", "narrator"])
        self.assertGreater(result["seconds"], 0.1)
        self.assertTrue((self.out / "voice-preview.mp3").is_file())

    def test_render_requires_frozen_references(self):
        plan = self.prepared()
        with self.assertRaises(AbkError):
            rc.render(plan, self.out, self.engine)

    def test_limit_gives_a_partial_render_without_assembly(self):
        plan = self.prepared()
        rc.voices(plan, self.out, self.engine)
        result = rc.render(plan, self.out, self.engine, limit=1)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["chunks_done"], 1)
        self.assertFalse((self.out / "chapter.mp3").exists())
        info = rc.status(plan, self.out)
        self.assertEqual(info["chunks_done"], 1)
        self.assertEqual(info["next_chunk"], plan["chunks"][1]["id"])
        done = rc.render(plan, self.out, self.engine)
        self.assertEqual(done["status"], "assembled")
        self.assertEqual(done["new_calls"], len(plan["chunks"]) - 1)

    def test_fallback_engine_is_a_hard_failure(self):
        self.fake.engine_name = "elevenlabs"
        plan = self.prepared()
        with self.assertRaises(AbkError) as ctx:
            rc.voices(plan, self.out, self.engine)
        self.assertIn("fallback is forbidden", str(ctx.exception))
        self.assertEqual([r["status"] for r in rc.request_records(self.out)], ["failure"])

    def test_failed_request_blocks_until_retry_failed(self):
        plan = self.prepared()
        rc.voices(plan, self.out, self.engine)
        self.fake.fail_on = {"Where is the tea"}
        with self.assertRaises(subprocess.CalledProcessError):
            rc.render(plan, self.out, self.engine)
        self.fake.fail_on = set()
        with self.assertRaises(AbkError) as ctx:
            rc.render(plan, self.out, self.engine)
        self.assertIn("--retry-failed", str(ctx.exception))
        self.assertEqual(rc.render(plan, self.out, self.engine, retry_failed=True)["status"], "assembled")
        summary = rc.report(self.out)["totals"]
        self.assertEqual(summary["failed_calls"], 1)

    def test_redo_rerolls_one_chunk_and_keeps_the_ledger_honest(self):
        plan = self.prepared()
        rc.voices(plan, self.out, self.engine)
        rc.render(plan, self.out, self.engine)
        target = plan["chunks"][1]["id"]
        old_hash = read_json(self.out / "chunks" / f"{target}.json")["wav"]["sha256"]
        with self.assertRaises(AbkError):
            rc.redo(plan, self.out, [target], "  ")
        with self.assertRaises(AbkError):
            rc.redo(plan, self.out, ["999999"], "x")
        result = rc.redo(plan, self.out, [target], "ASR: opening mangled")
        self.assertEqual(result["retired_chunks"], [target])
        self.assertFalse((self.out / "chapter.mp3").exists())
        self.fake.calls.clear()
        again = rc.render(plan, self.out, self.engine)
        self.assertEqual(again["new_calls"], 1)
        self.assertEqual(len(self.fake.calls), 1)
        self.assertEqual(again["status"], "assembled")
        self.assertTrue((self.out / "chapter.mp3").exists())
        new_hash = read_json(self.out / "chunks" / f"{target}.json")["wav"]["sha256"]
        self.assertTrue(old_hash and new_hash)
        totals = rc.report(self.out)["totals"]
        self.assertEqual(totals["successful_calls"], 2 + len(plan["chunks"]) + 1)  # old take still counted
        self.assertEqual(totals["failed_calls"], 0)

    def test_corrupted_cache_is_refused(self):
        plan = self.prepared()
        rc.voices(plan, self.out, self.engine)
        rc.render(plan, self.out, self.engine, limit=1)
        first = self.out / "chunks" / f"{plan['chunks'][0]['id']}.wav"
        first.write_bytes(helpers.make_wav(0.01, value=5))
        with self.assertRaises(AbkError):
            rc.render(plan, self.out, self.engine)

    def test_stray_cache_files_are_refused(self):
        plan = self.prepared()
        rc.voices(plan, self.out, self.engine)
        (self.out / "chunks").mkdir()
        (self.out / "chunks" / "stray.wav").write_bytes(b"x")
        with self.assertRaises(AbkError):
            rc.render(plan, self.out, self.engine)

    def test_pinned_voice_skips_design_and_conditions_on_the_file(self):
        clip = self.dir / "narrator.wav"
        clip.write_bytes(helpers.make_wav(0.4, value=300))
        data = manifest()
        data["voices"]["narrator"] = {"reference_audio": "narrator.wav"}
        self.manifest_path.write_text(json.dumps(data))
        plan = self.prepared()
        self.assertEqual([d["id"] for d in plan["designs"]], ["boy"])
        self.assertIn("narrator", plan["pinned"])
        rc.voices(plan, self.out, self.engine)
        rc.render(plan, self.out, self.engine)
        self.assertEqual(len(self.fake.calls), 1 + len(plan["chunks"]))
        clip.write_bytes(helpers.make_wav(0.4, value=301))  # pinned file drifted after prepare
        with self.assertRaises(AbkError):
            rc.load_plan(self.manifest_path, self.out, self.engine)

    def test_tokenizer_none_still_plans(self):
        engine = rc.Engine(tokenizer="none")
        plan = rc.build_plan(self.manifest_path, engine)
        self.assertEqual(plan["model_revision"], "unversioned")
        self.assertIsNone(plan["chunks"][0]["input_text_tokens"])
        self.assertEqual(plan["planned_input_text_tokens"], {"design": 0, "chapter": 0})

    def test_cli_end_to_end_mirrors_into_book_json(self):
        import book

        root = self.dir / "book"
        book.init_book(root, "Tiny")
        manifest_path = root / "chapters/01/chapter.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(manifest()))
        out = root / "chapters/01/audio"
        base = ["--manifest", str(manifest_path), "--output", str(out), "--book", str(root)]
        for command in (["prepare"], ["voices"], ["render"], ["status"]):
            self.assertEqual(rc.main([command[0], *base]), 0, command)
        data = book.load(root)
        self.assertEqual(sorted(data["voices"]), ["boy", "narrator"])
        self.assertEqual(data["voices"]["boy"]["mode"], "designed")
        self.assertEqual(data["progress"]["furthest"]["stage"], "assembled")
        kinds = {a["kind"]: a["status"] for a in data["artifacts"]}
        self.assertEqual(kinds["chunk-cache"], "complete")
        self.assertEqual(kinds["chapter-mp3"], "complete")
        self.assertEqual(book.verify_artifacts(root), [])

    def test_llm_metrics_never_estimates(self):
        self.assertIsNone(rc.llm_metrics(None)["input_tokens"])
        snapshot = {"source": "x", "totals": {k: 1 for k in (
            "input_tokens", "output_tokens", "reasoning_tokens", "cache_read_tokens", "cache_write_tokens",
            "reported_total_tokens", "messages_missing_usage")}}
        snapshot["totals"]["messages_missing_usage"] = 1
        self.assertIsNone(rc.llm_metrics(snapshot)["input_tokens"])
        with self.assertRaises(AbkError):
            rc.llm_metrics({"totals": {}})

    def test_assemble_rejects_mismatched_formats(self):
        a, b = self.dir / "a.wav", self.dir / "b.wav"
        a.write_bytes(helpers.make_wav(0.1, rate=8000))
        b.write_bytes(helpers.make_wav(0.1, rate=16000))
        item = {"paragraph": 1, "segment": 0}
        with self.assertRaises(AbkError):
            rc.assemble_wav([(item, a), (item, b)], self.dir / "o.wav")

    def test_pauses_by_boundary_type(self):
        p = lambda para, seg: {"paragraph": para, "segment": seg}  # noqa: E731
        self.assertEqual(rc.pause_frames(p(1, 0), p(1, 0), 1000), 0)
        self.assertEqual(rc.pause_frames(p(1, 0), p(1, 1), 1000), 120)
        self.assertEqual(rc.pause_frames(p(1, 1), p(2, 2), 1000), 280)


if __name__ == "__main__":
    unittest.main()
