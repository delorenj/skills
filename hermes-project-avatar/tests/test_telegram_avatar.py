"""Regression tests for hermes-project-avatar scripts/telegram_avatar.py.

Run with an interpreter that has Pillow + pytest (on this host /usr/bin/python3):

    /usr/bin/python3 -m pytest all-skills/hermes-project-avatar/tests/ -q

Every rendering assertion measures real pixels of the produced JPEG (via
Pillow); nothing is mocked. rsvg-convert must be installed.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "telegram_avatar.py"

SQUARE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<path d="M2 2h20v20H2z" fill="#000000"/></svg>'
)
TALL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 24">'
    '<rect x="0" y="0" width="8" height="24" fill="#000000"/></svg>'
)
ALT_DESIGN_SQUARE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<circle cx="12" cy="12" r="10" fill="#bb2d14"/></svg>'
)


def run_convert(*argv: str, svg_text: str | None = None, svg_name: str = "mark.svg"):
    """Run the script in a temp dir; returns (proc, tmp_path, out_path)."""
    tmp = Path(tempfile.mkdtemp(prefix="avatar-test-"))
    svg = tmp / svg_name
    if svg_text is not None:
        svg.write_text(svg_text)
    out = tmp / "avatar.jpg"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "convert", "--svg", str(svg), "--out", str(out), *argv],
        capture_output=True,
        text=True,
        env={**os.environ, "TMPDIR": str(tmp)},
    )
    return proc, tmp, out, svg


def ink_bbox(path: Path, bg: tuple[int, int, int] = (255, 255, 255), tol: int = 40):
    """Bounding box (x0, x1, y0, y1) of pixels that differ from bg, plus size."""
    img = Image.open(path)
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            pixel: tuple[int, ...] = tuple(img_rgb.getpixel((x, y)))  # type: ignore[union-assign,arg-type]
            r, g, b = pixel[0], pixel[1], pixel[2]
            if abs(r - bg[0]) > tol or abs(g - bg[1]) > tol or abs(b - bg[2]) > tol:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise AssertionError(f"no ink found in {path}")
    return img_rgb.size, (min(xs), max(xs), min(ys), max(ys))


class TestPaddingGeometry(unittest.TestCase):
    def test_pad_changes_pixel_bbox(self):
        """--pad must actually change the rendered mark's pixel bbox."""
        runs = {}
        for pad in ("0", "5", "10"):
            proc, _tmp, out, _ = run_convert("--size", "200", "--pad", pad, svg_text=SQUARE_SVG)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            (w, h), (x0, x1, y0, y1) = ink_bbox(out)
            self.assertEqual((w, h), (200, 200))
            runs[pad] = (x1 - x0, y1 - y0, x0, y0)
        # Larger pad => strictly smaller mark bbox and larger symmetric margins.
        self.assertGreater(runs["0"][0], runs["5"][0])
        self.assertGreater(runs["5"][0], runs["10"][0])
        self.assertEqual(runs["0"][0], runs["0"][1])  # square mark stays square
        for pad in runs:
            bw, bh, x0, y0 = runs[pad]
            self.assertLessEqual(
                abs(x0 - (199 - (x0 + bw - 1))), 1, f"pad {pad}: L/R margins differ"
            )
            self.assertLessEqual(
                abs(y0 - (199 - (y0 + bh - 1))), 1, f"pad {pad}: T/B margins differ"
            )

    def test_non_square_mark_centered_circle_safe(self):
        """An 8x24 mark must land centered, keep aspect, and clear the inscribed circle."""
        proc, _tmp, out, _ = run_convert("--size", "200", svg_text=TALL_SVG)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        (w, h), (x0, x1, y0, y1) = ink_bbox(out)
        self.assertEqual((w, h), (200, 200))
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        # centered: margins equal on each axis (within 1px rasterization)
        self.assertLessEqual(abs(x0 - (199 - x1)), 1, "not horizontally centered")
        self.assertLessEqual(abs(y0 - (199 - y1)), 1, "not vertically centered")
        # aspect ratio preserved (8:24), not stretched to fill the square
        self.assertAlmostEqual(bh / bw, 24 / 8, delta=0.1)
        # circle-safe: every bbox corner is inside the inscribed circle
        cx = cy = 99.5
        radius = 100.0
        for corner in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            d = math.dist(corner, (cx, cy))
            self.assertLess(d, radius, f"corner {corner} outside inscribed circle")

    def test_default_viewbox_reads_actual_svg(self):
        """Without --viewbox the geometry comes from the SVG's own viewBox.

        For the 8x24 mark at size 200 with pad 5 (span=24): pad_y=5, pad_x=5*8/24,
        side=34 -> mark width 8/34*200 ~= 47px, margins ~= 76px / 29px. A default
        of 24x24 (the old bug) would instead fill ~141px with ~29px margins both axes.
        """
        proc, _tmp, out, _ = run_convert("--size", "200", svg_text=TALL_SVG)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        meta = json.loads(proc.stdout)
        self.assertEqual(meta["viewBox"], [0.0, 0.0, 8.0, 24.0])
        (_w, _h), (x0, x1, y0, y1) = ink_bbox(out)
        self.assertAlmostEqual((x1 - x0 + 1), 8 / 34 * 200, delta=2)
        self.assertAlmostEqual((y1 - y0 + 1), 24 / 34 * 200, delta=2)
        # And an explicit WRONG override must change the geometry (proof the
        # default is really derived from the file, not a constant).
        proc2, _tmp2, out2, _ = run_convert(
            "--size", "200", "--viewbox", "0 0 24 24", svg_text=TALL_SVG
        )
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        meta2 = json.loads(proc2.stdout)
        self.assertEqual(meta2["viewBox"], [0.0, 0.0, 24.0, 24.0])
        _, (x0b, x1b, y0b, y1b) = ink_bbox(out2)
        self.assertNotEqual((x0, x1, y0, y1), (x0b, x1b, y0b, y1b))

    def test_deterministic_output(self):
        proc, _tmp, out, _svg = run_convert("--size", "100", svg_text=SQUARE_SVG)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        first = out.read_bytes()
        proc2, _, out2, _ = run_convert("--size", "100", svg_text=SQUARE_SVG)
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        self.assertEqual(first, out2.read_bytes(), "same input must render byte-identical")


class TestOutputFormat(unittest.TestCase):
    def test_rgb_square_requested_bg(self):
        proc, _tmp, out, _ = run_convert(
            "--size", "123", "--background", "#f1f0eb", svg_text=SQUARE_SVG
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        meta = json.loads(proc.stdout)
        self.assertEqual(meta["size"], 123)
        img = Image.open(out)
        self.assertEqual(img.format, "JPEG")
        self.assertEqual(img.mode, "RGB")
        self.assertEqual(img.size, (123, 123))
        # corners are exactly the requested background (flat area, JPEG-stable)
        for corner in ((0, 0), (122, 0), (0, 122), (122, 122), (61, 2)):
            r, g, b = img.getpixel(corner)
            self.assertAlmostEqual(r, 0xF1, delta=2)
            self.assertAlmostEqual(g, 0xF0, delta=2)
            self.assertAlmostEqual(b, 0xEB, delta=2)
        # 3-digit hex form is accepted too
        proc3, _, out3, _ = run_convert("--size", "64", "--background", "#fff", svg_text=SQUARE_SVG)
        self.assertEqual(proc3.returncode, 0, proc3.stderr)
        self.assertEqual(Image.open(out3).getpixel((0, 0)), (255, 255, 255))


class TestReceiptHashGating(unittest.TestCase):
    def test_hash_is_stable_and_path_independent_of_content(self):
        """content_hash gates receipts: same bytes+params -> same hash; any
        change (new design at the SAME path, bg, pad, size) -> different hash."""
        proc_a, tmp_a, _out_a, svg_a = run_convert(
            "--size", "100", "--background", "#f1f0eb", svg_text=SQUARE_SVG
        )
        self.assertEqual(proc_a.returncode, 0, proc_a.stderr)
        hash_a = json.loads(proc_a.stdout)["content_hash"]
        self.assertTrue(hash_a.startswith("sha256:"))

        # identical rerun -> identical hash
        proc_b, _, _, _ = run_convert(
            "--size", "100", "--background", "#f1f0eb", svg_text=SQUARE_SVG
        )
        self.assertEqual(json.loads(proc_b.stdout)["content_hash"], hash_a)

        # NEW DESIGN, SAME FILE PATH: overwrite the same mark.svg in place
        svg_a.write_text(ALT_DESIGN_SQUARE_SVG)
        r = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "convert",
                "--svg",
                str(svg_a),
                "--out",
                str(tmp_a / "again.jpg"),
                "--size",
                "100",
                "--background",
                "#f1f0eb",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(
            json.loads(r.stdout)["content_hash"],
            hash_a,
            "new design at the same path MUST change the hash",
        )

        # different render params -> different hash
        for extra in (["--background", "#ffffff"], ["--pad", "3"], ["--size", "101"]):
            r2 = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "convert",
                    "--svg",
                    str(svg_a),
                    "--out",
                    str(tmp_a / "v.jpg"),
                    "--size",
                    "100",
                    "--background",
                    "#f1f0eb",
                    *extra,
                ],
                capture_output=True,
                text=True,
            )
            # note: for the --size variant the base differs too; still must differ
            self.assertNotEqual(json.loads(r2.stdout)["content_hash"], hash_a)


BAD_CASES = [
    ("missing svg", {"svg_text": None, "argv": ["--size", "100"]}),
    ("not xml", {"svg_text": "not xml at all", "argv": ["--size", "100"]}),
    (
        "unclosed tag",
        {"svg_text": '<svg xmlns="http://www.w3.org/2000/svg"><rect', "argv": ["--size", "100"]},
    ),
    (
        "doctype / xxe",
        {
            "svg_text": '<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4"/>',
            "argv": ["--size", "100"],
        },
    ),
    (
        "entity declaration",
        {
            "svg_text": '<svg xmlns="http://www.w3.org/2000/svg" xmlns:x="urn:x" '
            'viewBox="0 0 4 4"><!ENTITY e "x"/></svg>',
            "argv": ["--size", "100"],
        },
    ),
    (
        "external image href",
        {
            "svg_text": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4">'
            '<image href="http://evil.example/x.png" width="4" height="4"/></svg>',
            "argv": ["--size", "100"],
        },
    ),
    (
        "external use href",
        {
            "svg_text": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4">'
            '<use href="http://evil.example/#frag"/></svg>',
            "argv": ["--size", "100"],
        },
    ),
    (
        "external url() fill",
        {
            "svg_text": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4">'
            '<rect width="4" height="4" fill="url(http://evil.example/g)"/></svg>',
            "argv": ["--size", "100"],
        },
    ),
    (
        "fragment url() is fine but no viewBox override",
        {
            "svg_text": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 4 4">'
            '<rect width="4" height="4" fill="url(#local)"/></svg>',
            "argv": ["--size", "0"],
        },
    ),  # rejected for size, not the url
    (
        "no viewBox at all",
        {
            "svg_text": '<svg xmlns="http://www.w3.org/2000/svg"><rect width="4" height="4"/></svg>',
            "argv": ["--size", "100"],
        },
    ),
    (
        "viewBox too few numbers",
        {"svg_text": SQUARE_SVG, "argv": ["--viewbox", "0 0 24", "--size", "100"]},
    ),
    (
        "viewBox negative width",
        {"svg_text": SQUARE_SVG, "argv": ["--viewbox", "0 0 -2 24", "--size", "100"]},
    ),
    ("viewBox nan", {"svg_text": SQUARE_SVG, "argv": ["--viewbox", "0 0 nan 24", "--size", "100"]}),
    ("viewBox inf", {"svg_text": SQUARE_SVG, "argv": ["--viewbox", "0 0 inf 24", "--size", "100"]}),
    (
        "viewBox overflow",
        {"svg_text": SQUARE_SVG, "argv": ["--viewbox", "0 0 1e400 24", "--size", "100"]},
    ),
    ("pad negative", {"svg_text": SQUARE_SVG, "argv": ["--pad", "-1", "--size", "100"]}),
    ("pad nan", {"svg_text": SQUARE_SVG, "argv": ["--pad", "nan", "--size", "100"]}),
    ("pad inf", {"svg_text": SQUARE_SVG, "argv": ["--pad", "inf", "--size", "100"]}),
    ("size zero", {"svg_text": SQUARE_SVG, "argv": ["--size", "0"]}),
    ("size negative", {"svg_text": SQUARE_SVG, "argv": ["--size", "-5"]}),
    ("size absurd", {"svg_text": SQUARE_SVG, "argv": ["--size", "99999999"]}),
    (
        "background not hex",
        {"svg_text": SQUARE_SVG, "argv": ["--background", "white", "--size", "100"]},
    ),
    (
        "background partial hex",
        {"svg_text": SQUARE_SVG, "argv": ["--background", "#f1f0", "--size", "100"]},
    ),
]


class TestInvalidInputs(unittest.TestCase):
    def test_bad_inputs_rejected_truthfully(self):
        for name, spec in BAD_CASES:
            with self.subTest(name):
                proc, _tmp, out, _ = run_convert(*spec["argv"], svg_text=spec["svg_text"])
                self.assertEqual(
                    proc.returncode,
                    3,
                    f"{name}: expected exit 3, got {proc.returncode}; stderr={proc.stderr!r}",
                )
                # truthful: a real error message, not a traceback, no output file
                self.assertTrue(
                    proc.stderr.startswith("error: "),
                    f"{name}: stderr lacks truthful error message: {proc.stderr!r}",
                )
                self.assertNotIn("Traceback", proc.stderr)
                self.assertFalse(out.exists(), f"{name}: output file must not be created")

    def test_missing_renderer_is_exit_4(self):
        tmp = Path(tempfile.mkdtemp(prefix="avatar-notools-"))
        svg = tmp / "m.svg"
        svg.write_text(SQUARE_SVG)
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        env["PATH"] = "/nonexistent-dir-for-test"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "convert",
                "--svg",
                str(svg),
                "--out",
                str(tmp / "o.jpg"),
                "--size",
                "100",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        if shutil.which("rsvg-convert"):
            self.assertEqual(proc.returncode, 4, proc.stderr)
            self.assertIn("rsvg-convert", proc.stderr)
        else:  # pragma: no cover
            self.skipTest("rsvg-convert not installed; script would report exit 4")


if __name__ == "__main__":
    unittest.main()
