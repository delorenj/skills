import json
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
import prepare_chapter as pc
from abk_common import AbkError

PARAS = [
    "It was a grey morning. “Come here,” said the old man. He coughed.",
    "“Where is the tea?” asked the boy, and the old man laughed.",
    "Nothing else happened that day.",
]
VOICES = {
    "narrator": {"description": "Warm mature woman, measured literary delivery.",
                 "reference_text": "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window."},
    "old_man": {"description": "Elderly male, dry weathered voice.",
                "reference_text": "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window."},
    "boy": {"description": "Adolescent boy, brisk and impatient.",
            "reference_text": "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window."},
}


class QuoteTests(unittest.TestCase):
    def test_quote_spans_numbered_with_context(self):
        spans = pc.quote_spans(PARAS)
        self.assertEqual([s["text"] for s in spans], ["Come here,", "Where is the tea?"])
        self.assertEqual(spans[1]["paragraph"], 2)
        self.assertIn("grey morning", spans[0]["before"])

    def test_unbalanced_quotes_refused(self):
        paragraphs = ["“Start of a quote that never ends.", "Next paragraph”"]
        with self.assertRaises(AbkError):
            pc.check_delimiters(paragraphs, pc.quote_spans(paragraphs), pc.DEFAULT_QUOTE)


class SegmentTests(unittest.TestCase):
    def test_segments_reconstruct_and_attribute(self):
        turns = pc.parse_turns(["old_man", ["boy", "Where is the tea?"]])
        segments = pc.split_segments(PARAS, turns, VOICES, "narrator")
        self.assertEqual([s["speaker"] for s in segments],
                         ["narrator", "old_man", "narrator", "boy", "narrator", "narrator"])
        self.assertEqual(segments[1]["text"], "Come here,")
        self.assertTrue(all("“" not in s["text"] for s in segments))

    def test_wrong_count_unknown_speaker_and_changed_text_refused(self):
        with self.assertRaises(AbkError):
            pc.split_segments(PARAS, pc.parse_turns(["old_man"]), VOICES, "narrator")
        with self.assertRaises(AbkError):
            pc.split_segments(PARAS, pc.parse_turns(["ghost", "boy"]), VOICES, "narrator")
        with self.assertRaises(AbkError) as ctx:
            pc.split_segments(PARAS, pc.parse_turns([["old_man", "Come here!"], "boy"]), VOICES, "narrator")
        self.assertIn("changed", str(ctx.exception))

    def test_voice_design_rules(self):
        with self.assertRaises(AbkError):
            pc.validate_voice_design("x", {"description": "has (parens)", "reference_text": "a " * 16})
        with self.assertRaises(AbkError):
            pc.validate_voice_design("x", {"description": "word " * 21, "reference_text": "a " * 16})
        with self.assertRaises(AbkError):
            pc.validate_voice_design("x", {"description": "fine", "reference_text": "too short"})
        pc.validate_voice_design("x", {"reference_audio": "../voices/x.wav"})  # pinned: no prompt needed

    def test_build_manifest_reports_unused_voices(self):
        spec = {"title": "T", "chapter": 1, "voices": VOICES, "quotes": ["old_man", "old_man"]}
        manifest = pc.build_manifest(PARAS, spec)
        self.assertEqual(manifest["unused_voices"], ["boy"])
        self.assertEqual(manifest["settings"], {"cfg": 2.0, "steps": 12})

    def test_narrator_only_chapter(self):
        spec = {"title": "T", "chapter": 2, "voices": {"narrator": VOICES["narrator"]}}
        manifest = pc.build_manifest(["Plain prose, no dialogue at all."], spec)
        self.assertEqual(len(manifest["segments"]), 1)


class TextTests(unittest.TestCase):
    def test_assemble_text_markers_folio_join_corrections_and_wraps(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = Path(tmp)
            (pages / "page-001.txt").write_text("CHAPTER ONE\nIt was a dark morn-\ning and the cat sat.\n\nSecond para starts\n7\n")
            (pages / "page-002.txt").write_text("and continues here with a typo teh end.\n\nThird para.\n8\n")
            (pages / "page-003.txt").write_text("CHAPTER TWO\nNever included.\n9\n")
            paragraphs, report = pc.assemble_text(
                pages, 1, 3, start_marker="CHAPTER ONE", end_marker="CHAPTER TWO", strip_folio=True,
                join_previous={2}, corrections=[{"page": 2, "before": "teh", "after": "the"}],
            )
            self.assertEqual(paragraphs, [
                "It was a dark morning and the cat sat.",
                "Second para starts and continues here with a typo the end.",
                "Third para.",
            ])
            self.assertEqual(report["wrap_repairs"], 1)
            self.assertEqual(report["joined_pages"], [2])
            with self.assertRaises(AbkError):
                pc.assemble_text(pages, 1, 2, strip_folio=True, corrections=[{"page": 2, "before": "absent", "after": "x"}])
            with self.assertRaises(AbkError):
                pc.assemble_text(pages, 1, 4)

    def test_auto_join_only_when_sentence_unfinished(self):
        with tempfile.TemporaryDirectory() as tmp:
            pages = Path(tmp)
            (pages / "page-001.txt").write_text("A sentence that stops mid\n")
            (pages / "page-002.txt").write_text("way and ends.\n\nNew para.\n")
            paragraphs, _ = pc.assemble_text(pages, 1, 2, auto_join=True)
            self.assertEqual(paragraphs, ["A sentence that stops mid way and ends.", "New para."])


class CliTests(unittest.TestCase):
    def test_build_cli_with_book_pins_existing_voice(self):
        import book

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "book"
            book.init_book(root, "Tiny")
            clip = Path(tmp) / "narrator.wav"  # outside the book: add_voice copies it into voices/
            clip.write_bytes(helpers.make_wav(0.3))
            book.add_voice(root, "narrator", "designed", "Narrator", description="warm", reference_text="x y", reference_audio=clip)
            text = root / "chapter.txt"
            text.write_text("\n\n".join(PARAS) + "\n")
            speakers = root / "speakers.json"
            voices = dict(VOICES)
            speakers.write_text(json.dumps({"voices": voices, "quotes": ["old_man", "boy"]}))
            self.assertEqual(pc.main(["build", "--text", str(text), "--speakers", str(speakers),
                                      "--book", str(root), "--chapter", "1"]), 0)
            manifest = json.loads((root / "chapters/01/chapter.json").read_text())
            self.assertEqual(manifest["title"], "Tiny")
            self.assertTrue(manifest["voices"]["narrator"]["reference_audio"].endswith("voices/narrator.wav"))
            self.assertNotIn("reference_audio", manifest["voices"]["boy"])

    def test_quotes_cli_and_failures_exit_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = Path(tmp) / "c.txt"
            text.write_text("“Open only.\n")
            self.assertEqual(pc.main(["quotes", "--text", str(text)]), 1)


if __name__ == "__main__":
    unittest.main()
