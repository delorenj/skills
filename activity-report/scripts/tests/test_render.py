import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import render  # noqa: E402
from ar.common import AcceptanceError, ConfigError  # noqa: E402

FX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "publish")
META = {
    "project_name": "Smoketest Project", "audience": "internal",
    "window_start": "2026-09-02T07:00:00Z", "window_end": "2026-09-03T07:00:00Z",
    "tz": "America/New_York", "run_id": "4c1f2e8a-3b5d-4e6f-9a7b-1c2d3e4f5a6b",
    "generated_at": "2026-09-03T07:05:00Z", "duration_seconds": 86400,
}


def read(name):
    with open(os.path.join(FX, name), encoding="utf-8") as fh:
        return fh.read()


class SplitRaw(unittest.TestCase):
    def test_title_and_body(self):
        title, body = render.split_raw("# Hello there\n\nbody line\n")
        self.assertEqual(title, "Hello there")
        self.assertEqual(body, "body line")

    def test_missing_title_line(self):
        with self.assertRaises(AcceptanceError):
            render.split_raw("Hello\nbody")
        with self.assertRaises(AcceptanceError):
            render.split_raw("## Heading\nbody")
        with self.assertRaises(AcceptanceError):
            render.split_raw("#Hello\nbody")

    def test_empty_title(self):
        with self.assertRaises(AcceptanceError):
            render.split_raw("#   \nbody")

    def test_crlf_and_bom(self):
        title, body = render.split_raw("﻿# T\r\n\r\nline one\r\nline two\r\n")
        self.assertEqual(title, "T")
        self.assertEqual(body, "line one\nline two")


class Inline(unittest.TestCase):
    def test_balanced(self):
        self.assertEqual(render.inline_runs("a **b** c"), [(False, "a "), (True, "b"), (False, " c")])

    def test_unbalanced_stays_literal(self):
        self.assertEqual(render.inline_runs("a **b c"), [(False, "a **b c")])

    def test_empty_bold_dropped(self):
        self.assertEqual(render.inline_runs("a **** c"), [(False, "a "), (False, " c")])

    def test_leading_bold(self):
        self.assertEqual(render.inline_runs("**x**"), [(True, "x")])


class Parse(unittest.TestCase):
    def test_grammar_order_and_merging(self):
        blocks = render.parse("## H\n- a\n* b\n\n- c\n| k | v |\n| k2 | v2 |\n09:30 did\n9:05 more\nplain\n# hash para\n| a | b | c |\n")
        kinds = [b.kind for b in blocks]
        # three cells still match the portal's metric regex: the lazy second group swallows "b | c"
        self.assertEqual(kinds, ["heading", "bullets", "metrics", "timeline", "paragraph", "paragraph", "metrics"])
        self.assertEqual(blocks[0].text, "H")
        self.assertEqual(blocks[1].items, ["a", "b", "c"])
        self.assertEqual(blocks[2].items, [("k", "v"), ("k2", "v2")])
        self.assertEqual(blocks[3].items, [("09:30", "did"), ("9:05", "more")])
        self.assertEqual(blocks[5].text, "# hash para")
        self.assertEqual(blocks[6].items, [("a", "b | c")])

    def test_blank_and_whitespace_lines(self):
        self.assertEqual(render.parse("\n   \n  - x  \n"), [render.Block("bullets", items=["x"])])


class Markdown(unittest.TestCase):
    def test_exact(self):
        blocks = render.parse("## H\n- a **b**\n| k | v |\n09:30 did\npara")
        md = render.to_markdown("T", blocks)
        self.assertEqual(md, "# T\n\n## H\n\n- a **b**\n\n| Metric | Value |\n|---|---|\n| k | v |\n\n- **09:30** did\n\npara\n")


class Html(unittest.TestCase):
    def doc(self, body, **meta):
        m = dict(META)
        m.update(meta)
        blocks = render.parse(body)
        return render.to_html("Title <here>", blocks, m)

    def test_document_shape(self):
        html = self.doc("## A\n- x\n")
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn('<meta charset="utf-8">', html)
        self.assertIn('name="viewport"', html)
        self.assertIn("<title>Smoketest Project · Title &lt;here&gt;</title>", html)
        self.assertEqual(html.count("<style>"), 1)
        self.assertIn("--accent:#0e7c86", html)
        self.assertIn("prefers-color-scheme:dark", html)
        self.assertIn("@media print", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("http", html.split("</style>")[1])

    def test_everything_escaped(self):
        html = self.doc("## <b>h</b>\n- <script>alert(1)</script>\n| <k> | <v> |\n09:30 <t>\n<p>para</p>")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<h2>&lt;b&gt;h&lt;/b&gt;</h2>", html)
        self.assertIn("&lt;p&gt;para&lt;/p&gt;", html)

    def test_masthead_and_footer_internal(self):
        html = self.doc("- x")
        self.assertIn('<p class="eyebrow">Smoketest Project · Internal update</p>', html)
        self.assertIn('<span class="pill internal">Internal</span>', html)
        self.assertIn("2 Sep 2026 03:00 to 3 Sep 2026 03:00 EDT", html)
        self.assertIn("<span>24h</span>", html)
        self.assertIn("run 4c1f2e8a-3b5d-4e6f-9a7b-1c2d3e4f5a6b", html)
        self.assertIn("Generated 2026-09-03T07:05:00Z", html)

    def test_masthead_and_footer_external(self):
        html = self.doc("- x", audience="external")
        self.assertIn("Client update", html)
        self.assertIn('<span class="pill external">External</span>', html)
        self.assertIn('<footer class="foot">Updated 3 Sep 2026</footer>', html)
        self.assertNotIn("4c1f2e8a", html)
        self.assertNotIn("Generated", html)

    def test_sections_metrics_timeline(self):
        html = self.doc("intro\n## Numbers\n| Sessions | 6 |\n| Commits | 4 |\n## Mixed\n| k | v |\n- b\n## Day\n09:30 did **it**\n")
        self.assertEqual(html.count('<section class="sec">'), 4)
        self.assertIn('<div class="metrics"><div class="metric"><b>6</b><span>Sessions</span></div>', html)
        self.assertIn('<dl class="kv"><dt>k</dt><dd>v</dd></dl>', html)
        self.assertIn('<ol class="timeline"><li><span class="at">09:30</span>', html)
        self.assertIn("did <strong>it</strong>", html)
        self.assertIn("<p>intro</p>", html)

    def test_duration_and_range_formats(self):
        self.assertEqual(render.format_duration(86400), "24h")
        self.assertEqual(render.format_duration(23400), "6h 30m")
        self.assertEqual(render.format_duration(2700), "45m")
        html = self.doc("- x", window_start="2026-09-02T13:00:00Z", window_end="2026-09-02T20:30:00Z", duration_seconds=27000)
        self.assertIn("2 Sep 2026, 09:00 to 16:30 EDT", html)
        self.assertIn("<span>7h 30m</span>", html)

    def test_bad_audience_or_tz(self):
        with self.assertRaises(ConfigError):
            self.doc("- x", audience="client")
        with self.assertRaises(ConfigError):
            self.doc("- x", tz="Mars/Olympus")

    def test_fixture_bodies_have_no_paths_or_keys_in_external(self):
        title, body = render.split_raw(read("external.raw.txt"))
        html = render.to_html(title, render.parse(body), dict(META, audience="external"))
        self.assertNotIn("SMK-", html)
        self.assertNotIn("/home/", html)


class RenderCmd(unittest.TestCase):
    def test_defaults_next_to_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            digest = os.path.join(tmp, "2026-09-03T0300-internal.digest.json")
            with open(os.path.join(FX, "internal.digest.json"), encoding="utf-8") as src, open(digest, "w", encoding="utf-8") as dst:
                dst.write(src.read())
            raw = os.path.join(tmp, "in.raw.txt")
            with open(raw, "w", encoding="utf-8") as fh:
                fh.write(read("internal.raw.txt"))
            args = types.SimpleNamespace(raw=raw, digest=digest, md=None, html=None, audience="internal", project=None, json=True)
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(render.render_cmd(args), 0)
            out = json.loads(buf.getvalue())
            self.assertEqual(out["markdown"], os.path.join(tmp, "2026-09-03T0300-internal.md"))
            self.assertEqual(out["html"], os.path.join(tmp, "2026-09-03T0300-internal.html"))
            with open(out["html"], encoding="utf-8") as fh:
                html = fh.read()
            self.assertTrue(html.startswith("<!doctype html>"))
            self.assertIn("Invoice drafts land in the CRM", html)

    def test_audience_mismatch(self):
        args = types.SimpleNamespace(raw=os.path.join(FX, "internal.raw.txt"), digest=os.path.join(FX, "internal.digest.json"),
                                     md=None, html=None, audience="external", project=None, json=False)
        with self.assertRaises(ConfigError):
            render.render_cmd(args)


if __name__ == "__main__":
    unittest.main()
