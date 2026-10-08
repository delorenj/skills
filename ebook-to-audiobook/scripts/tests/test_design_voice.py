import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
import book
import design_voice as dv
import render_chapter as rc
from abk_common import AbkError

DESCRIPTION = "Twenty-year-old woman, grounded plain restrained middle-low register."
REFTEXT = "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window."


class DesignVoiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.book = Path(self.tmp.name) / "book"
        book.init_book(self.book, "Tiny")
        self.fake = helpers.FakeEngine()
        patcher = mock.patch.object(rc.subprocess, "run", self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.engine = rc.Engine(core_container="vox", tokenizer="none")

    def test_design_takes_then_freeze_registers_and_build_pins(self):
        takes = dv.design(self.book, "o_lan", DESCRIPTION, REFTEXT, self.engine, takes=2)
        self.assertEqual([t["take"] for t in takes], [1, 2])
        self.assertEqual(self.fake.calls[0]["text"], f"({DESCRIPTION}){REFTEXT}")
        self.assertNotIn("reference_audio_b64", self.fake.calls[0])
        self.assertEqual({k: self.fake.calls[0][k] for k in ("cfg", "steps")}, {"cfg": 2.0, "steps": 12})
        listing = dv.list_takes(self.book, "o_lan")
        self.assertEqual(listing["takes"][1]["description"], DESCRIPTION)
        self.assertEqual(listing["takes"][1]["reference_text"], REFTEXT)
        row = dv.freeze(self.book, "o_lan", 2, "O-lan", chapter=1)
        self.assertEqual(row["mode"], "designed")
        self.assertEqual(row["reference_audio"]["path"], "voices/o_lan.wav")
        self.assertEqual(row["reference_audio"]["sha256"], takes[1]["sha256"])
        with self.assertRaises(AbkError):  # replacing a book voice is deliberate
            dv.freeze(self.book, "o_lan", 1, "O-lan")
        # a later chapter only names the speaker; build --book pins the frozen clip
        import prepare_chapter as pc

        text = self.book / "chapters/01/chapter.txt"
        text.parent.mkdir(parents=True)
        text.write_text("“Yes,” she said.\n")
        speakers = text.parent / "speakers.json"
        speakers.write_text(json.dumps({"voices": {"narrator": {"description": "Warm mature woman, measured.",
                                                                "reference_text": REFTEXT},
                                                   "o_lan": {"character": "O-lan"}}, "quotes": ["o_lan"]}))
        self.assertEqual(pc.main(["build", "--text", str(text), "--speakers", str(speakers),
                                  "--book", str(self.book), "--chapter", "1"]), 0)
        manifest = json.loads((self.book / "chapters/01/chapter.json").read_text())
        self.assertTrue(manifest["voices"]["o_lan"]["reference_audio"].endswith("voices/o_lan.wav"))

    def test_rules_and_fallback_engine(self):
        with self.assertRaises(AbkError):
            dv.design(self.book, "x", "has (parens)", REFTEXT, self.engine)
        with self.assertRaises(AbkError):
            dv.design(self.book, "x", DESCRIPTION, "too short", self.engine)
        with self.assertRaises(AbkError):
            dv.design(self.book, "../x", DESCRIPTION, REFTEXT, self.engine)
        self.fake.engine_name = "elevenlabs"
        with self.assertRaises(AbkError) as ctx:
            dv.design(self.book, "x", DESCRIPTION, REFTEXT, self.engine)
        self.assertIn("fallback is forbidden", str(ctx.exception))

    def test_failed_take_blocks_until_retry_failed_and_keeps_its_number(self):
        self.fake.fail_on = {"morning light"}
        with self.assertRaises(AbkError):
            dv.design(self.book, "x", DESCRIPTION, REFTEXT, self.engine)
        self.fake.fail_on = set()
        with self.assertRaises(AbkError) as ctx:
            dv.design(self.book, "x", DESCRIPTION, REFTEXT, self.engine)
        self.assertIn("--retry-failed", str(ctx.exception))
        retried = dv.design(self.book, "x", DESCRIPTION, REFTEXT, self.engine, retry_failed=True)
        self.assertEqual(retried[0]["take"], 1)
        self.assertEqual(dv.design(self.book, "x", DESCRIPTION, REFTEXT, self.engine)[0]["take"], 2)
        self.assertEqual(dv.list_takes(self.book, "x")["unfinished_or_failed"], [])

    def test_cli_round_trip_and_samples_file(self):
        base = ["--book", str(self.book), "--id", "narrator"]
        self.assertEqual(dv.main(["design", *base, "--description", DESCRIPTION, "--reference-text", REFTEXT]), 0)
        samples = Path(self.tmp.name) / "s.json"
        self.assertEqual(dv.main(["list", *base, "--samples-out", str(samples)]), 0)
        rows = json.loads(samples.read_text())
        self.assertEqual(rows[0]["expected"], REFTEXT)
        self.assertEqual(rows[0]["kind"], "ref")
        self.assertEqual(dv.main(["freeze", *base, "--take", "1", "--character", "Narrator"]), 0)
        self.assertEqual(dv.main(["freeze", *base, "--take", "9", "--character", "Narrator", "--replace"]), 1)
        self.assertIn("narrator", book.load(self.book)["voices"])


if __name__ == "__main__":
    unittest.main()
