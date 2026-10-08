import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import helpers  # noqa: F401
import extract_pages as ep


class FakeRun:
    def __init__(self, layer_text):
        self.layer_text = layer_text
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append(command[0])
        if command[0] == "pdftotext":
            page = int(command[command.index("-f") + 1])
            return subprocess.CompletedProcess(command, 0, self.layer_text.get(page, "").encode(), b"")
        if command[0] == "pdftoppm":
            Path(command[-1] + "-1.png").write_bytes(b"png")
            return subprocess.CompletedProcess(command, 0, b"", b"")
        if command[0] == "tesseract":
            return subprocess.CompletedProcess(command, 0, b"OCR TEXT FOR A SCANNED PAGE, long enough to keep.\n", b"")
        if command[0] == "pdfinfo":
            return subprocess.CompletedProcess(command, 0, b"Pages:          3\n", b"")
        raise AssertionError(command)


class PdfTests(unittest.TestCase):
    def test_text_layer_preferred_and_ocr_fallback_for_scans_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pages"
            run = FakeRun({1: "A real text layer with plenty of characters on page one."})
            report = ep.extract_pdf(Path("x.pdf"), out, 1, None, "auto", run=run)
            self.assertEqual((report["text_layer"], report["ocr"]), ([1], [2, 3]))
            self.assertTrue((out / "page-002.txt").read_text().startswith("OCR TEXT"))
            calls = len(run.calls)
            again = ep.extract_pdf(Path("x.pdf"), out, 1, 3, "auto", run=run)
            self.assertEqual(again["skipped_existing"], [1, 2, 3])
            self.assertEqual(len(run.calls), calls)

    def test_never_ocr_leaves_empty_pages_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = ep.extract_pdf(Path("x.pdf"), Path(tmp), 1, 1, "never", run=FakeRun({}))
            self.assertEqual(report["empty"], [1])

    def test_bad_ocr_mode_refused(self):
        with self.assertRaises(ep.AbkError):
            ep.extract_pdf(Path("x.pdf"), Path("."), 1, 1, "sometimes")


class EpubTests(unittest.TestCase):
    def test_spine_order_and_html_stripping(self):
        with tempfile.TemporaryDirectory() as tmp:
            epub = Path(tmp) / "b.epub"
            with zipfile.ZipFile(epub, "w") as z:
                z.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>')
                z.writestr("OEBPS/content.opf",
                           '<package><manifest><item id="b" href="ch2.xhtml"/><item id="a" href="ch1.xhtml"/></manifest>'
                           '<spine><itemref idref="a"/><itemref idref="b"/></spine></package>')
                z.writestr("OEBPS/ch1.xhtml", "<html><body><h1>One</h1><p>First &amp; best.</p><script>x()</script></body></html>")
                z.writestr("OEBPS/ch2.xhtml", "<html><body><p>Second.</p></body></html>")
            out = Path(tmp) / "pages"
            report = ep.extract_epub(epub, out)
            self.assertEqual(report["spine"], [1, 2])
            self.assertEqual((out / "page-001.txt").read_text().split(), ["One", "First", "&", "best."])
            self.assertEqual((out / "page-002.txt").read_text().strip(), "Second.")

    def test_cli_rejects_unknown_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "b.mobi"
            f.write_bytes(b"x")
            self.assertEqual(ep.main([str(f), "--out", str(Path(tmp) / "o")]), 1)


if __name__ == "__main__":
    unittest.main()
