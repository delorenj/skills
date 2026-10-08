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

    def test_resume_hint_follows_stage_with_runnable_commands(self):
        self.init()
        hint = book.resume_hint(self.dir)
        self.assertIn("Research", hint["next"])
        self.assertTrue(any("extract_pages.py" in c for c in hint["commands"]))
        book.set_chapter(self.dir, 1, output=self.dir / "chapters/01/take2", manifest=self.dir / "chapters/01/chapter.json")
        book.set_progress(self.dir, 1, "rendering", chunks_done=3, chunks_total=9, chunk_id="000003")
        hint = book.resume_hint(self.dir)
        self.assertIn("after chunk 000003", hint["next"])
        render = [c for c in hint["commands"] if "render_chapter.py render" in c][0]
        self.assertIn(str((self.dir / "chapters/01/take2").resolve()), render)  # the recorded output, not a guess
        self.assertIn(f"--book {self.dir.resolve()}", render)
        self.assertTrue(Path(render.split()[2]).is_file())  # absolute script path that exists
        book.set_progress(self.dir, 1, "researched")  # earlier stage never drags furthest back
        self.assertEqual(book.resume_hint(self.dir)["stage"], "rendering")
        book.set_progress(self.dir, 1, "done")
        hint = book.resume_hint(self.dir)
        self.assertIn("chapter 2", hint["next"])
        self.assertEqual((hint["chapter"], hint["stage"]), (2, "new"))
        self.assertEqual(hint["unfinished_earlier_chapters"], [])

    def test_non_wav_reference_audio_is_refused_early(self):
        self.init()
        clip = Path(self.tmp.name) / "voice.mp3"
        clip.write_bytes(b"ID3")
        with self.assertRaises(AbkError) as ctx:
            book.add_voice(self.dir, "v", "cloned", "V", reference_audio=clip)
        self.assertIn("ffmpeg", str(ctx.exception))

    def _render_dir(self, chapter, designs=(), chunks=2):
        out = self.dir / f"chapters/{chapter:02d}/audio"
        out.mkdir(parents=True, exist_ok=True)
        plan = {"manifest": {"voices": {d: {"description": "d", "reference_text": "t"} for d in designs}},
                "designs": [{"id": d} for d in designs], "pinned": {},
                "chunks": [{"id": f"{i + 1:06d}", "text": f"Chunk {i + 1}."} for i in range(chunks)]}
        (out / "prepared.json").write_text(json.dumps(plan))
        return out

    def test_import_render_stage_tracks_disk_and_regresses_after_redo(self):
        self.init()
        out = self._render_dir(1, designs=("narrator",))
        manifest = self.dir / "chapters/01/chapter.json"
        self.assertEqual(book.import_render(self.dir, 1, out, manifest)["stage"], "prepared")  # voices not designed yet
        self.assertEqual(book.load(self.dir)["chapters"]["1"]["manifest"], "chapters/01/chapter.json")
        self.assertIn("render_chapter.py voices", " ".join(book.resume_hint(self.dir)["commands"]))
        (out / "refs").mkdir()
        (out / "refs/narrator.wav").write_bytes(helpers.make_wav(0.2))
        self.assertEqual(book.import_render(self.dir, 1, out)["stage"], "voices")
        (out / "chunks").mkdir()
        (out / "chunks/000001.wav").write_bytes(helpers.make_wav(0.1))
        summary = book.import_render(self.dir, 1, out)
        self.assertEqual((summary["stage"], summary["next_chunk"]), ("rendering", "000002"))
        furthest = book.load(self.dir)["progress"]["furthest"]
        self.assertEqual((furthest["chunk_id"], furthest["char_offset"]), ("000001", len("Chunk 1.") + 1))
        (out / "chunks/000002.wav").write_bytes(helpers.make_wav(0.1))
        (out / "chapter.mp3").write_bytes(b"ID3")
        (out / "assembly.json").write_text(json.dumps({"timestamp_utc": "2026-10-07T10:00:00+00:00"}))
        self.assertEqual(book.import_render(self.dir, 1, out)["stage"], "assembled")
        qa = {"status": "complete", "selection": {"selected_chunks": 2}, "timestamp_utc": "2026-10-07T11:00:00+00:00"}
        (out / "qa-all.json").write_text(json.dumps(qa))
        self.assertEqual(book.import_render(self.dir, 1, out)["stage"], "qa")
        book.set_progress(self.dir, 1, "done")
        self.assertEqual(book.import_render(self.dir, 1, out)["stage"], "qa")  # idempotent rerun keeps sign-off
        self.assertEqual(book.load(self.dir)["chapters"]["1"]["status"], "done")
        # redo: one chunk and the assembled outputs move away
        (out / "chunks/000002.wav").unlink()
        (out / "chapter.mp3").unlink()
        summary = book.import_render(self.dir, 1, out)
        self.assertEqual((summary["stage"], summary["regressed_from"]), ("rendering", "done"))
        self.assertIn("chapters/01/audio/chapter.mp3", summary["stale"])
        data = book.load(self.dir)
        self.assertEqual(data["chapters"]["1"]["status"], "rendering")
        self.assertEqual(data["progress"]["furthest"]["stage"], "rendering")
        mp3 = [a for a in data["artifacts"] if a["kind"] == "chapter-mp3"][0]
        self.assertEqual(mp3["status"], "stale")

    def test_redoing_an_earlier_chapter_never_drags_a_later_furthest_back(self):
        self.init()
        book.set_progress(self.dir, 2, "rendering", chunks_done=1, chunks_total=5)
        book.set_progress(self.dir, 1, "done")
        out = self._render_dir(1)
        summary = book.import_render(self.dir, 1, out)
        self.assertEqual(summary["regressed_from"], "done")
        self.assertEqual(book.load(self.dir)["progress"]["furthest"]["chapter"], 2)
        self.assertEqual(book.resume_hint(self.dir)["unfinished_earlier_chapters"], [{"chapter": 1, "status": "voices"}])

    def test_import_render_reports_a_voice_clip_conflict(self):
        self.init()
        clip = Path(self.tmp.name) / "n.wav"
        clip.write_bytes(helpers.make_wav(0.2, value=1))
        book.add_voice(self.dir, "narrator", "designed", "Narrator", description="d", reference_text="t", reference_audio=clip)
        out = self._render_dir(2, designs=("narrator",))
        (out / "refs").mkdir()
        (out / "refs/narrator.wav").write_bytes(helpers.make_wav(0.2, value=2))  # chapter built without --book
        summary = book.import_render(self.dir, 2, out)
        self.assertEqual(summary["conflicts"][0]["voice"], "narrator")
        self.assertEqual(book.load(self.dir)["voices"]["narrator"]["reference_audio"]["sha256"],
                         book.file_hash(self.dir / "voices/narrator.wav"))

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
