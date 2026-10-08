import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
import book
from abk_common import AbkError


class BookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "my-book"
        self.addCleanup(self.tmp.cleanup)

    def init(self):
        return book.init_book(self.dir, "The Good Earth", "Pearl S. Buck")

    def test_init_creates_layout_and_refuses_overwrite(self):
        data = self.init()
        self.assertEqual(data["slug"], "the-good-earth")
        for name in ("source/pages", "research", "voices", "chapters", "usage"):
            self.assertTrue((self.dir / name).is_dir())
        with self.assertRaises(AbkError):
            self.init()

    def test_init_hashes_source(self):
        source = Path(self.tmp.name) / "b.pdf"
        source.write_bytes(b"%PDF fake")
        data = book.init_book(self.dir, "T", source=source)
        self.assertEqual(data["source"]["kind"], "pdf")
        self.assertEqual(len(data["source"]["sha256"]), 64)

    def test_designed_voice_requires_prompt_and_rejects_parentheses(self):
        self.init()
        with self.assertRaises(AbkError):
            book.add_voice(self.dir, "x", "designed", "X")
        with self.assertRaises(AbkError):
            book.add_voice(self.dir, "x", "designed", "X", description="(old)", reference_text="t")
        with self.assertRaises(AbkError):
            book.add_voice(self.dir, "../x", "designed", "X", description="d", reference_text="t")

    def test_voice_audio_is_copied_hashed_and_replace_is_explicit(self):
        self.init()
        clip = Path(self.tmp.name) / "ref.wav"
        clip.write_bytes(helpers.make_wav(0.2))
        row = book.add_voice(self.dir, "narrator", "designed", "Narrator", description="warm woman",
                             reference_text="a b c", reference_audio=clip, chapter=1)
        self.assertEqual(row["reference_audio"]["path"], "voices/narrator.wav")
        self.assertTrue((self.dir / "voices/narrator.wav").is_file())
        with self.assertRaises(AbkError):
            book.add_voice(self.dir, "narrator", "designed", "Narrator", description="d", reference_text="t")
        again = book.add_voice(self.dir, "narrator", "designed", "Narrator", description="d2",
                               reference_text="t", reference_audio=clip, chapter=2, replace=True)
        self.assertEqual(again["chapters"], [1, 2])

    def test_selected_voice_needs_slug_or_audio(self):
        self.init()
        with self.assertRaises(AbkError):
            book.add_voice(self.dir, "v", "selected", "V")
        row = book.add_voice(self.dir, "v", "selected", "V", engine="vibevoice", voxxy_slug="rick")
        self.assertEqual(row["voxxy_slug"], "rick")

    def test_progress_furthest_is_a_high_water_mark(self):
        self.init()
        book.set_progress(self.dir, 2, "rendering", chunks_done=10, chunks_total=50, chunk_id="000010")
        data = book.set_progress(self.dir, 1, "qa")  # re-touching an earlier chapter
        self.assertEqual(data["furthest"]["chapter"], 2)
        self.assertEqual(data["current"]["chapter"], 1)
        data = book.set_progress(self.dir, 2, "rendering", chunks_done=11, chunks_total=50)
        self.assertEqual(data["furthest"]["chunks_done"], 11)
        with self.assertRaises(AbkError):
            book.set_progress(self.dir, 2, "rendering", chunks_done=9, chunks_total=3)
        with self.assertRaises(AbkError):
            book.set_progress(self.dir, 2, "bogus")

    def test_artifacts_are_idempotent_by_path_and_verify_detects_drift(self):
        self.init()
        mp3 = self.dir / "chapters/01/audio/chapter.mp3"
        mp3.parent.mkdir(parents=True)
        mp3.write_bytes(b"one")
        first = book.add_artifact(self.dir, "chapter-mp3", mp3, chapter=1, status="partial")
        second = book.add_artifact(self.dir, "chapter-mp3", mp3, chapter=1, status="complete")
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(book.load(self.dir)["artifacts"]), 1)
        self.assertEqual(book.verify_artifacts(self.dir), [])
        mp3.write_bytes(b"two")
        problems = book.verify_artifacts(self.dir)
        self.assertEqual(problems[0]["issue"], "checksum-mismatch")
        self.assertEqual(book.load(self.dir)["artifacts"][0]["status"], "stale")
        mp3.unlink()
        self.assertEqual(book.verify_artifacts(self.dir, mark_stale=False)[0]["issue"], "missing")
        with self.assertRaises(AbkError):
            book.add_artifact(self.dir, "x", self.dir / "nope")

    def test_directory_artifact_records_file_count(self):
        self.init()
        chunks = self.dir / "chapters/01/audio/chunks"
        chunks.mkdir(parents=True)
        (chunks / "000001.wav").write_bytes(b"x")
        row = book.add_artifact(self.dir, "chunk-cache", chunks, chapter=1, status="partial")
        self.assertEqual(row["files"], 1)
        self.assertIsNone(row["sha256"])

    def test_resume_hint_follows_stage(self):
        self.init()
        self.assertIn("Research", book.resume_hint(self.dir)["next"])
        book.set_progress(self.dir, 1, "rendering", chunks_done=3, chunks_total=9)
        self.assertIn("render_chapter.py render", book.resume_hint(self.dir)["next"])
        book.set_progress(self.dir, 1, "done")
        self.assertIn("chapter 2", book.resume_hint(self.dir)["next"])

    def test_import_render_marks_pinned_voices_as_used_in_the_new_chapter(self):
        self.init()
        clip = Path(self.tmp.name) / "n.wav"
        clip.write_bytes(helpers.make_wav(0.2))
        book.add_voice(self.dir, "narrator", "designed", "Narrator", description="d", reference_text="t",
                       reference_audio=clip, chapter=1)
        out = self.dir / "chapters/02/audio"
        out.mkdir(parents=True)
        plan = {"manifest": {"voices": {"narrator": {"reference_audio": "x"}}}, "designs": [],
                "pinned": {"narrator": {"path": "x", "sha256": "y"}},
                "chunks": [{"id": "000001", "text": "Hello there."}]}
        (out / "prepared.json").write_text(json.dumps(plan))
        summary = book.import_render(self.dir, 2, out)
        self.assertEqual(book.load(self.dir)["voices"]["narrator"]["chapters"], [1, 2])
        self.assertEqual(summary["stage"], "voices")
        self.assertEqual(book.load(self.dir)["progress"]["furthest"]["chapter"], 2)

    def test_cli_round_trip(self):
        self.assertEqual(book.main(["--dir", str(self.dir), "init", "--title", "Tiny Book"]), 0)
        self.assertEqual(book.main(["--dir", str(self.dir), "progress", "set", "--chapter", "1", "--stage", "prepared"]), 0)
        self.assertEqual(book.main(["--dir", str(self.dir), "show"]), 0)
        self.assertEqual(book.main(["--dir", str(self.dir), "voice", "add", "bad", "--mode", "designed", "--character", "B"]), 1)
        self.assertEqual(json.loads((self.dir / "book.json").read_text())["progress"]["furthest"]["stage"], "prepared")

    def test_missing_book_is_a_clean_error(self):
        self.assertEqual(book.main(["--dir", str(self.dir), "show"]), 1)


if __name__ == "__main__":
    unittest.main()
