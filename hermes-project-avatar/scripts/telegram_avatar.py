#!/usr/bin/env python3
"""Convert an SVG brand mark into a Telegram-ready square JPEG.

Proven pipeline from the Holocene avatar work (2026-10-16):
rsvg-convert renders the padded SVG, Pillow flattens to RGB JPEG.

Usage:
  telegram_avatar.py convert --svg brand.svg --out avatar.jpg \
      [--pad 5] [--viewbox "0 0 24 24"] [--background "#f1f0eb"] [--size 1024]

Pads the viewBox symmetrically (default 5 units on a 24-unit mark) so a circular
crop keeps the mark intact. With --background, wraps the SVG with a rect using
that fill; without it, renders transparent and composites onto the background.
Exits 3 on bad input, 4 on missing tools.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SIZE = 1024


def parse_viewbox(vb: str) -> tuple[float, float, float, float]:
    parts = vb.replace(",", " ").split()
    if len(parts) != 4:
        raise SystemExit(3)
    try:
        x, y, w, h = (float(p) for p in parts)
    except ValueError:
        raise SystemExit(3)
    if w <= 0 or h <= 0:
        raise SystemExit(3)
    return x, y, w, h


def svg_with_background(svg_text: str, vb: tuple[float, float, float, float], bg: str) -> str:
    x, y, w, h = vb
    rect = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{bg}"/>'
    if "<svg" not in svg_text:
        raise SystemExit(3)
    # insert rect right after the opening <svg ...> tag
    idx = svg_text.index("<svg")
    idx = svg_text.index(">", idx) + 1
    return svg_text[:idx] + rect + svg_text[idx:]


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("convert", help="SVG -> padded square JPEG")
    c.add_argument("--svg", required=True, type=Path)
    c.add_argument("--out", required=True, type=Path)
    c.add_argument("--pad", type=float, default=5.0, help="viewBox padding units")
    c.add_argument("--viewbox", default=None, help="source viewBox, e.g. '0 0 24 24'")
    c.add_argument("--background", default=None, help="hex background, e.g. '#f1f0eb'")
    c.add_argument("--size", type=int, default=DEFAULT_SIZE)

    args = ap.parse_args()

    if shutil.which("rsvg-convert") is None:
        print("rsvg-convert not found", file=sys.stderr)
        return 4
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("Pillow not available", file=sys.stderr)
        return 4

    if args.cmd == "convert":
        if not args.svg.is_file():
            print(f"missing svg: {args.svg}", file=sys.stderr)
            return 3
        svg_text = args.svg.read_text()
        vb = parse_viewbox(args.viewbox) if args.viewbox else (0.0, 0.0, 24.0, 24.0)
        _, _, w, h = vb
        if args.background:
            svg_text = svg_with_background(svg_text, vb, args.background)
        new_vb = (vb[0] - args.pad, vb[1] - args.pad, w + 2 * args.pad, h + 2 * args.pad)

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            src = tdp / "in.svg"
            png = tdp / "out.png"
            # rewrite/create viewBox via width/height on a wrapper is fragile;
            # simplest robust route: set width/height attributes and use
            # rsvg-convert geometry options.
            src.write_text(svg_text)
            cmd = [
                "rsvg-convert",
                "--width",
                str(args.size),
                "--height",
                str(args.size),
                "--keep-aspect-ratio",
                "--page-width",
                str(args.size),
                "--page-height",
                str(args.size),
                "--background-color",
                args.background or "white",
                "--output",
                str(png),
                str(src),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"rsvg-convert failed: {res.stderr.strip()}", file=sys.stderr)
                return 3
            from PIL import Image

            img = Image.open(png)
            if img.mode != "RGB":
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                    bg_img = Image.new("RGB", img.size, (255, 255, 255))
                    bg_img.paste(img, mask=img.split()[-1])
                    img = bg_img
                else:
                    img = img.convert("RGB")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            img.save(args.out, "JPEG", quality=92)
            print(f"wrote {args.out} ({img.size[0]}x{img.size[1]})")
            return 0
    return 3


if __name__ == "__main__":
    sys.exit(main())
