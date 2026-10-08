#!/usr/bin/env python3
"""Extract per-page (PDF) or per-spine-item (EPUB) text into page-NNN.txt files.

    extract_pages.py book.pdf  --out source/pages --first 1 --last 40 [--ocr auto|always|never]
    extract_pages.py book.epub --out source/pages

PDF: uses the text layer (pdftotext). Scanned/image-only pages (the Good Earth PDF was
entirely image-only) fall back to pdftoppm + tesseract. Numbers in file names are 1-based
PDF page numbers (or spine order), never printed folios. Existing files are kept unless
--force, so a long OCR run is resumable.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

from abk_common import AbkError

MIN_TEXT_CHARS = 40
Runner = Callable[..., subprocess.CompletedProcess]


def page_count(pdf: Path, run: Runner = subprocess.run) -> int:
    out = run(["pdfinfo", str(pdf)], capture_output=True, check=True, timeout=60).stdout.decode()
    match = re.search(r"^Pages:\s+(\d+)", out, re.MULTILINE)
    if not match:
        raise AbkError("pdfinfo did not report a page count")
    return int(match.group(1))


def text_layer(pdf: Path, page: int, run: Runner = subprocess.run) -> str:
    done = run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"],
        capture_output=True, check=True, timeout=120,
    )
    return done.stdout.decode("utf-8", errors="replace").strip()


def ocr_page(pdf: Path, page: int, dpi: int = 300, psm: int = 6, run: Runner = subprocess.run) -> str:
    # --psm 6 (uniform block) read dialogue punctuation better than the default --psm 3 on the pilot book.
    with tempfile.TemporaryDirectory() as tmp:
        stem = Path(tmp) / "p"
        run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-png", str(pdf), str(stem)],
            capture_output=True, check=True, timeout=300)
        images = sorted(Path(tmp).glob("p-*.png"))
        if len(images) != 1:
            raise AbkError(f"pdftoppm produced {len(images)} images for page {page}")
        done = run(["tesseract", str(images[0]), "stdout", "--psm", str(psm), "quiet"],
                   capture_output=True, check=True, timeout=300)
    return done.stdout.decode("utf-8", errors="replace").strip()


def extract_pdf(
    pdf: Path, out: Path, first: int, last: int | None, ocr: str = "auto", force: bool = False,
    run: Runner = subprocess.run,
) -> dict[str, list[int]]:
    if ocr not in ("auto", "always", "never"):
        raise AbkError("--ocr must be auto, always, or never")
    out.mkdir(parents=True, exist_ok=True)
    last = last or page_count(pdf, run)
    report: dict[str, list[int]] = {"text_layer": [], "ocr": [], "skipped_existing": [], "empty": []}
    for page in range(first, last + 1):
        target = out / f"page-{page:03d}.txt"
        if target.exists() and not force:
            report["skipped_existing"].append(page)
            continue
        text, source = "", "text_layer"
        if ocr != "always":
            text = text_layer(pdf, page, run)
        if ocr == "always" or (ocr == "auto" and len(text) < MIN_TEXT_CHARS):
            text, source = ocr_page(pdf, page, run=run), "ocr"
        if not text:
            report["empty"].append(page)
        target.write_text(text + "\n", encoding="utf-8")
        report[source].append(page)
    return report


class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style"):
            self.skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n\n" if tag != "br" else "\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        if tag in self.BLOCK and tag != "br":
            self.parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)


def html_to_text(markup: str) -> str:
    parser = _Text()
    parser.feed(markup)
    text = "".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_epub(epub: Path, out: Path, force: bool = False) -> dict[str, list[int]]:
    out.mkdir(parents=True, exist_ok=True)
    report: dict[str, list[int]] = {"spine": [], "skipped_existing": []}
    with zipfile.ZipFile(epub) as archive:
        container = archive.read("META-INF/container.xml").decode("utf-8")
        opf_path = re.search(r'full-path="([^"]+)"', container)
        if not opf_path:
            raise AbkError("EPUB container.xml has no rootfile")
        opf_name = opf_path.group(1)
        opf = archive.read(opf_name).decode("utf-8")
        manifest = dict(re.findall(r'<item[^>]*?id="([^"]+)"[^>]*?href="([^"]+)"', opf))
        manifest.update({k: v for v, k in re.findall(r'<item[^>]*?href="([^"]+)"[^>]*?id="([^"]+)"', opf)})
        base = opf_name.rsplit("/", 1)[0] + "/" if "/" in opf_name else ""
        order = re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf)
        for number, idref in enumerate(order, 1):
            href = manifest.get(idref)
            if not href:
                continue
            target = out / f"page-{number:03d}.txt"
            if target.exists() and not force:
                report["skipped_existing"].append(number)
                continue
            raw = archive.read(base + href.split("#")[0]).decode("utf-8", errors="replace")
            target.write_text(html_to_text(raw) + "\n", encoding="utf-8")
            report["spine"].append(number)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--first", type=int, default=1)
    parser.add_argument("--last", type=int)
    parser.add_argument("--ocr", default="auto", choices=("auto", "always", "never"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not args.source.is_file():
            raise AbkError(f"No such file: {args.source}")
        suffix = args.source.suffix.lower()
        if suffix == ".pdf":
            report = extract_pdf(args.source, args.out, args.first, args.last, args.ocr, args.force)
        elif suffix == ".epub":
            report = extract_epub(args.source, args.out, args.force)
        else:
            raise AbkError("Supported sources: .pdf, .epub (convert others first, e.g. with calibre ebook-convert)")
    except (AbkError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({k: (v if len(v) < 40 else f"{len(v)} pages") for k, v in report.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
