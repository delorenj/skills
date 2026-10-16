#!/usr/bin/env python3
"""Convert an SVG brand mark into a circle-safe, centered square JPEG.

SCOPE: this helper ONLY converts (SVG -> square raster). It is NOT a Telegram
upload pipeline: no bot token handling, no upload, no profile-photo
verification. The upload and read-only verification steps are documented in
the skill's SKILL.md and are performed by the agent, not by this script.

Usage:
  telegram_avatar.py convert --svg brand.svg --out avatar.jpg \
      [--pad 5] [--background "#f1f0eb"] [--size 1024] [--viewbox "0 0 24 24"]

Behavior:
  - The mark's viewBox is read from the SVG itself; --viewbox overrides it.
  - --pad expands the canvas symmetrically around the mark (in units of the
    mark's larger viewBox dimension), so the mark stays centered, keeps its
    aspect ratio, and clears an inscribed circular crop.
  - Output is an RGB JPEG of exactly --size x --size px on the requested
    background (default white), flattened opaque.
  - Prints one JSON line including a content_hash of (source bytes, viewBox,
    pad, background, size) for receipt gating: a new design at the same file
    path produces a different hash.

Safety: input is parsed as XML with DOCTYPE/ENTITY declarations and external
href/url() references rejected. Exits 3 on invalid input, 4 on missing tools.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_SIZE = 1024
DEFAULT_PAD = 5.0
MAX_SIZE = 16384
MAX_ABS_COORD = 1e9
HASH_VERSION = "avatar-convert/1"

_HEX_BG_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_EXTERNAL_URL_RE = re.compile(r"url\(\s*['\"]?\s*(?!#)", re.IGNORECASE)


def fail(msg: str, code: int = 3) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return code


def fmt_num(value: float) -> str:
    """Format a coordinate compactly, avoiding exponent notation and -0."""
    if value == 0:
        return "0"
    out = f"{value:.6f}".rstrip("0").rstrip(".")
    return out if out not in ("", "-", "-0") else "0"


def parse_viewbox(vb: str) -> tuple[float, float, float, float]:
    """Parse 'min-x min-y width height' (space or comma separated).

    Raises ValueError on arity, syntax, nonfinite values, absurd magnitudes,
    or nonpositive width/height.
    """
    parts = vb.replace(",", " ").split()
    if len(parts) != 4:
        raise ValueError(f"viewBox must have 4 numbers, got {len(parts)}: {vb!r}")
    try:
        x, y, w, h = (float(p) for p in parts)
    except ValueError as exc:
        raise ValueError(f"viewBox numbers not parseable: {vb!r}") from exc
    for name, val in (("min-x", x), ("min-y", y), ("width", w), ("height", h)):
        if not math.isfinite(val):
            raise ValueError(f"viewBox {name} is not finite: {val!r}")
        if abs(val) > MAX_ABS_COORD:
            raise ValueError(f"viewBox {name} magnitude too large: {val!r}")
    if w <= 0 or h <= 0:
        raise ValueError(f"viewBox width/height must be positive, got {w!r} x {h!r}")
    return x, y, w, h


def parse_length(value: str, what: str) -> float:
    """Parse a CSS-ish SVG length ('24', '24px') as a positive finite float."""
    v = value.strip().lower().removesuffix("px")
    try:
        n = float(v)
    except ValueError as exc:
        raise ValueError(f"{what} not parseable as a length: {value!r}") from exc
    if not math.isfinite(n) or n <= 0 or n > MAX_ABS_COORD:
        raise ValueError(f"{what} must be finite and positive: {value!r}")
    return n


def check_safe_xml(svg_bytes: bytes) -> ET.Element:
    """Parse the SVG safely; reject DOCTYPE/entities/external references.

    Returns the root element. Raises ValueError with a truthful reason.
    """
    try:
        text = svg_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"svg is not valid UTF-8: {exc}") from exc
    for token in ("<!DOCTYPE", "<!ENTITY"):
        if token in text:
            raise ValueError(f"svg contains forbidden {token} declaration")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError(f"svg is not well-formed XML: {exc}") from exc

    def local(tag: str | None) -> str:
        return (tag or "").rsplit("}", 1)[-1].lower()

    if local(root.tag) != "svg":
        raise ValueError(f"root element is <{local(root.tag)}>, not <svg>")

    def walk(el: ET.Element) -> None:
        for key, value in el.attrib.items():
            if local(key) == "href":
                v = value.strip()
                if not (v.startswith("#") or v.startswith("data:")):
                    raise ValueError(f"svg contains external href: {v!r}")
            if _EXTERNAL_URL_RE.search(value):
                raise ValueError(f"svg contains external url() reference: {value!r}")
        for child in el:
            walk(child)

    walk(root)
    return root


def resolve_viewbox(root: ET.Element, override: str | None) -> tuple[float, float, float, float]:
    """Resolve the mark's viewBox: --viewbox override > viewBox attr > width/height."""
    if override:
        return parse_viewbox(override)
    attr_vb = None
    width_attr = None
    height_attr = None
    for key, value in root.attrib.items():
        lk = key.rsplit("}", 1)[-1].lower()
        if lk == "viewbox":
            attr_vb = value
        elif lk == "width":
            width_attr = value
        elif lk == "height":
            height_attr = value
    if attr_vb is not None:
        return parse_viewbox(attr_vb)
    if width_attr is not None and height_attr is not None:
        return (0.0, 0.0, parse_length(width_attr, "width"), parse_length(height_attr, "height"))
    raise ValueError(
        "svg has no viewBox (and no width/height to derive one); "
        "pass --viewbox 'min-x min-y width height'"
    )


def build_padded_svg(
    root: ET.Element,
    vb: tuple[float, float, float, float],
    pad: float,
    background: str,
    size: int,
) -> str:
    """Wrap the mark in a square canvas: padded, centered, aspect preserved.

    The original root becomes a nested <svg> placed 1:1 at its viewBox rect,
    so fills, gradients, and internal references keep working. The wrapper
    viewBox is the square that contains the symmetrically padded mark.
    """
    mx, my, mw, mh = vb
    # Equal padding in output pixels: scale pad units by each axis' share of
    # the mark's larger dimension.
    span = max(mw, mh)
    pad_x = pad * (mw / span)
    pad_y = pad * (mh / span)
    inner_w = mw + 2 * pad_x
    inner_h = mh + 2 * pad_y
    side = max(inner_w, inner_h)
    vx = mx - pad_x - (side - inner_w) / 2
    vy = my - pad_y - (side - inner_h) / 2

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root.set("viewBox", f"{fmt_num(mx)} {fmt_num(my)} {fmt_num(mw)} {fmt_num(mh)}")
    root.set("x", fmt_num(mx))
    root.set("y", fmt_num(my))
    root.set("width", fmt_num(mw))
    root.set("height", fmt_num(mh))
    inner = ET.tostring(root, encoding="unicode")

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="{fmt_num(vx)} {fmt_num(vy)} {fmt_num(side)} {fmt_num(side)}" '
        f'width="{size}" height="{size}">'
        f'<rect x="{fmt_num(vx)}" y="{fmt_num(vy)}" '
        f'width="{fmt_num(side)}" height="{fmt_num(side)}" fill="{background}"/>'
        f"{inner}"
        "</svg>"
    )


def bg_rgb(background: str) -> tuple[int, int, int]:
    """Convert '#rgb' or '#rrggbb' to an RGB tuple."""
    h = background.lstrip("#")
    if len(h) == 3:
        return tuple(int(h[i] * 2, 16) for i in range(3))  # type: ignore[return-value]
    return tuple(int(h[i : i + 2], 16) for i in range(0, 6, 2))  # type: ignore[return-value]


def content_hash(
    svg_path: Path,
    vb: tuple[float, float, float, float],
    pad: float,
    background: str,
    size: int,
) -> str:
    """Stable digest of everything that determines the rendered avatar.

    Covers source bytes + render parameters, so a new design at the same file
    path yields a different hash (receipt no-op gating depends on this).
    """
    payload = json.dumps(
        {
            "v": HASH_VERSION,
            "svg_sha256": hashlib.sha256(svg_path.read_bytes()).hexdigest(),
            "viewBox": list(vb),
            "pad": pad,
            "background": background.lower(),
            "size": size,
        },
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def cmd_convert(args: argparse.Namespace) -> int:
    if not args.svg.is_file():
        return fail(f"missing svg: {args.svg}")
    try:
        svg_bytes = args.svg.read_bytes()
    except OSError as exc:
        return fail(f"unreadable svg: {exc}")

    try:
        root = check_safe_xml(svg_bytes)
        vb = resolve_viewbox(root, args.viewbox)
    except ValueError as exc:
        return fail(str(exc))

    if not math.isfinite(args.pad) or args.pad < 0:
        return fail(f"--pad must be finite and >= 0, got {args.pad!r}")
    if args.size <= 0 or args.size > MAX_SIZE:
        return fail(f"--size must be an integer in 1..{MAX_SIZE}, got {args.size}")
    if not _HEX_BG_RE.match(args.background):
        return fail(f"--background must be '#rgb' or '#rrggbb', got {args.background!r}")

    padded = build_padded_svg(root, vb, args.pad, args.background, args.size)
    digest = content_hash(args.svg, vb, args.pad, args.background, args.size)

    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.svg"
        png = Path(td) / "out.png"
        src.write_text(padded)
        res = subprocess.run(
            ["rsvg-convert", "--format", "png", "--output", str(png), str(src)],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            return fail(f"rsvg-convert failed: {res.stderr.strip()}")
        from PIL import Image

        img = Image.open(png)
        if img.size != (args.size, args.size):
            return fail(
                f"renderer produced {img.size[0]}x{img.size[1]}, expected {args.size}x{args.size}"
            )
        if "A" in img.getbands() or img.mode not in ("RGB", "L"):
            rgba = img.convert("RGBA")
            flat = Image.new("RGB", rgba.size, bg_rgb(args.background))
            flat.paste(rgba, mask=rgba.split()[-1])
            img = flat
        else:
            img = img.convert("RGB")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        img.save(args.out, "JPEG", quality=92)

    print(
        json.dumps(
            {
                "out": str(args.out),
                "size": args.size,
                "viewBox": list(vb),
                "pad": args.pad,
                "background": args.background.lower(),
                "content_hash": digest,
            }
        )
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Convert an SVG brand mark to a circle-safe centered square JPEG. "
            "Conversion ONLY: no Telegram upload or verification."
        )
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("convert", help="SVG -> padded, centered square JPEG")
    c.add_argument("--svg", required=True, type=Path, help="source SVG path")
    c.add_argument("--out", required=True, type=Path, help="output JPEG path")
    c.add_argument(
        "--pad",
        type=float,
        default=DEFAULT_PAD,
        help=f"padding in units of the mark's larger viewBox dimension (default {DEFAULT_PAD})",
    )
    c.add_argument(
        "--viewbox",
        default=None,
        help="override the mark's viewBox, e.g. '0 0 24 24' (default: read from the SVG)",
    )
    c.add_argument(
        "--background",
        default="#ffffff",
        help="opaque background as '#rgb' or '#rrggbb' (default #ffffff)",
    )
    c.add_argument(
        "--size", type=int, default=DEFAULT_SIZE, help=f"output square px (default {DEFAULT_SIZE})"
    )
    args = ap.parse_args()

    if shutil.which("rsvg-convert") is None:
        print("error: rsvg-convert not found", file=sys.stderr)
        return 4
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("error: Pillow not available", file=sys.stderr)
        return 4

    if args.cmd == "convert":
        return cmd_convert(args)
    return 3


if __name__ == "__main__":
    sys.exit(main())
