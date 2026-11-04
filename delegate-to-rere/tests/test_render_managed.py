#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
import os
from pathlib import Path
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from render_managed import BEGIN, END, render, run


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.md"
        self.source.write_text("Rére policy\n")

    def target(self, name, text):
        path = self.root / name
        path.write_bytes(text)
        return path

    def invoke(self, *targets, apply=False):
        args = ["--source", str(self.source)]
        for target in targets:
            args += ["--target", str(target)]
        return run(args + (["--apply"] if apply else []))

    def test_append_preserves_surrounding_and_second_apply_does_not_write(self):
        target = self.target("agents.md", b"before\n\nafter")
        self.assertEqual(self.invoke(target), 1)
        self.assertEqual(target.read_bytes(), b"before\n\nafter")
        self.assertEqual(self.invoke(target, apply=True), 0)
        data = target.read_bytes()
        self.assertTrue(data.startswith(b"before\n\nafter\n" + BEGIN))
        self.assertIn(b"R\xc3\xa9re policy", data)
        stat = target.stat()
        self.assertEqual(self.invoke(target, apply=True), 0)
        self.assertEqual((stat.st_ino, stat.st_mtime_ns), (target.stat().st_ino, target.stat().st_mtime_ns))
        self.assertEqual(self.invoke(target), 0)

    def test_replace_only_bounded_section_and_crlf(self):
        target = self.target("old.md", b"before\r\n" + BEGIN + b"\r\nold\r\n" + END + b"\r\nafter\r\n")
        self.assertEqual(self.invoke(target, apply=True), 0)
        self.assertEqual(target.read_bytes(), b"before\r\n" + BEGIN + b"\r\nR\xc3\xa9re policy\r\n" + END + b"\r\nafter\r\n")

    def test_invalid_marker_aborts_all_before_writes(self):
        good = self.target("good.md", b"good\n")
        bad = self.target("bad.md", BEGIN + b"\nwrong\n" + BEGIN + b"\n" + END + b"\n")
        self.assertEqual(self.invoke(good, bad, apply=True), 2)
        self.assertEqual(good.read_bytes(), b"good\n")
        for payload in (END + b"\n", BEGIN + b"\n", END + b"\n" + BEGIN + b"\n", b"x" + BEGIN + b"\n"):
            bad.write_bytes(payload)
            self.assertEqual(self.invoke(good, bad, apply=True), 2)
            self.assertEqual(good.read_bytes(), b"good\n")

    def test_symlink_resolves_target_and_mode_preserved(self):
        target = self.target("real.md", b"original\n")
        target.chmod(0o640)
        link = self.root / "link.md"
        link.symlink_to(target)
        self.assertEqual(self.invoke(link, apply=True), 0)
        self.assertTrue(link.is_symlink())
        self.assertIn(END, target.read_bytes())
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.invoke(link, target, apply=True), 2)

    def test_source_marker_rejected_and_no_write(self):
        target = self.target("target.md", b"stay\n")
        self.source.write_bytes(BEGIN + b"\n")
        self.assertEqual(self.invoke(target, apply=True), 2)
        self.assertEqual(target.read_bytes(), b"stay\n")


if __name__ == "__main__":
    unittest.main()
