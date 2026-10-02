#!/usr/bin/env python3
"""Tests for html2md. Run: python3 scripts/test_html2md.py (no network)."""
import importlib.machinery
import importlib.util
import os
import sys
import time
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
_loader = importlib.machinery.SourceFileLoader("html2md", os.path.join(HERE, "html2md.py"))
h2m = importlib.util.module_from_spec(importlib.util.spec_from_loader("html2md", _loader))
_loader.exec_module(h2m)

BASE = "https://example.org/dir/page"


def md(html, base=BASE, plain=False):
    return h2m.convert(html, base, plain)[1]


class DropRules(unittest.TestCase):
    def test_elements_dropped_with_all_descendants(self):
        for tag in ("script", "style", "noscript", "template", "svg", "iframe", "object", "canvas"):
            out = md(f"<p>keep</p><{tag}>SECRET <b>SECRET2</b></{tag}><p>after</p>")
            self.assertEqual(out, "keep\n\nafter", tag)

    def test_void_embed_contributes_nothing_and_does_not_hide_following_text_like_a_browser(self):
        self.assertEqual(md('<p>a</p><embed src="x.swf"><p>b</p>'), "a\n\nb")

    def test_form_controls_are_dropped(self):
        out = md("<p>a</p><select><option>SECRET</option></select><textarea>SECRET</textarea><button>SECRET</button>"
                 "<input value=SECRET><p>b</p>")
        self.assertEqual(out, "a\n\nb")

    def test_comments_doctype_and_processing_instructions(self):
        self.assertEqual(md("<!DOCTYPE html><!-- SECRET --><?php SECRET ?><p>x</p><!--[if IE]>SECRET<![endif]-->"), "x")

    def test_every_form_of_hidden_element(self):
        forms = ['<div hidden>', '<div aria-hidden="true">', '<div aria-hidden="TRUE">', '<div style="display:none">',
                 '<div style="DISPLAY : NONE !important">', '<div style="color:red; visibility : hidden">',
                 '<span hidden="">', '<section style=" display:none ">']
        for opener in forms:
            tag = opener[1:].split()[0].rstrip(">")
            out = md(f"<p>keep</p>{opener}SECRET <b>SECRET2</b></{tag}><p>after</p>")
            self.assertNotIn("SECRET", out, opener)
            self.assertIn("keep", out)
            self.assertIn("after", out)

    def test_things_that_do_not_hide(self):
        for opener in ('<div class="hidden">', '<div aria-hidden="false">', '<div style="display:block">',
                       '<div style="color:red">', '<div data-hidden="true">'):
            self.assertIn("VISIBLE", md(f"{opener}VISIBLE</div>"), opener)

    def test_nesting_of_hidden_and_visible(self):
        self.assertEqual(md("<div hidden><p>A</p><div><p>B</p></div></div><p>C</p>"), "C")
        self.assertEqual(md("<p>A</p><div hidden>x<p>y</p></div><div>z</div>"), "A\n\nz")
        self.assertNotIn("INNER", md('<div hidden><div style="display:block">INNER</div></div>'))

    def test_self_closing_hidden_div_hides_what_follows_like_a_browser(self):
        out = md("<p>a</p><div hidden/>SECRET</div><p>b</p>")
        self.assertNotIn("SECRET", out)
        self.assertIn("a", out)
        self.assertIn("b", out)

    def test_title_is_captured_and_cleaned(self):
        self.assertEqual(h2m.convert("<head><title> A \n  B </title></head><p>x</p>")[0], "A B")
        self.assertEqual(h2m.convert("<p>x</p>")[0], "")
        self.assertEqual(h2m.convert("<svg><title>NOPE</title></svg><title>Real</title>")[0], "Real")
        self.assertNotIn("Real", md("<title>Real</title><p>body</p>"))


class Structure(unittest.TestCase):
    def test_headings(self):
        for n in range(1, 7):
            self.assertEqual(md(f"<h{n}>Head</h{n}>"), "#" * n + " Head")
            self.assertEqual(md(f"<h{n}>Head</h{n}>", plain=True), "Head")
        self.assertEqual(md("<h1>One<br>Two</h1>"), "# One\nTwo")

    def test_paragraphs_and_blocks_are_separated_by_one_blank_line(self):
        self.assertEqual(md("<p>a</p><p>b</p><div>c</div><section>d</section>"), "a\n\nb\n\nc\n\nd")
        self.assertEqual(md("<p>a</p>\n\n\n\n<p>b</p>"), "a\n\nb")

    def test_lists(self):
        self.assertEqual(md("<ul><li>a</li><li>b<ul><li>c</li></ul></li></ul>"), "- a\n- b\n  - c")
        self.assertEqual(md("<ol><li>a</li><li>b</li></ol><ol><li>c</li></ol>"), "1. a\n2. b\n\n1. c")
        self.assertEqual(md("<ol><li>a<ul><li>x</li></ul></li><li>b</li></ol>"), "1. a\n  - x\n2. b")

    def test_implied_end_tags(self):
        self.assertEqual(md("<ul><li>a<li>b<li>c</ul>"), "- a\n- b\n- c")
        self.assertEqual(md("<p>a<p>b"), "a\n\nb")
        self.assertEqual(md("<dl><dt>t1<dd>d1<dt>t2<dd>d2</dl>"), "t1\n: d1\nt2\n: d2")

    def test_blockquote_hr_br_dl(self):
        self.assertIn("> q1", md("<blockquote><p>q1</p><p>q2</p></blockquote>"))
        self.assertIn("> q2", md("<blockquote><p>q1</p><p>q2</p></blockquote>"))
        self.assertNotIn(">", md("<blockquote><p>q1</p></blockquote>", plain=True))
        self.assertEqual(md("<p>a</p><hr><p>b</p>"), "a\n\n---\n\nb")
        self.assertEqual(md("<p>a</p><hr><p>b</p>", plain=True), "a\n\nb")
        self.assertEqual(md("a<br>b<br/>c"), "a\nb\nc")
        self.assertEqual(md("<dl><dt>Term</dt><dd>Meaning</dd></dl>"), "Term\n: Meaning")

    def test_pre_preserves_whitespace_and_indentation(self):
        code = "def f(x):\n    if x < 3:\n        return {1: 2}\n\n    return 0"
        escaped = code.replace("<", "&lt;")
        out = md(f"<pre><code>\n{escaped}\n</code></pre>")
        self.assertEqual(out, f"```\n{code}\n```")
        self.assertEqual(md(f"<pre>{escaped}</pre>", plain=True), code)

    def test_pre_fence_adapts_to_backticks_inside_the_code(self):
        out = md("<pre>a ``` b</pre>")
        self.assertTrue(out.startswith("````\n") and out.endswith("\n````"), out)
        self.assertTrue(md("<pre>a ```` b</pre>").startswith("`````\n"))

    def test_inline_code_and_br_in_pre(self):
        self.assertEqual(md("<p>use <code>x = 1</code> here</p>"), "use `x = 1` here")
        self.assertEqual(md("use <code>x</code>", plain=True), "use x")
        self.assertEqual(md("<pre>a<br>b</pre>"), "```\na\nb\n```")

    def test_tables(self):
        self.assertEqual(md("<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"),
                         "| A | B |\n| --- | --- |\n| 1 | 2 |")
        self.assertEqual(md("<table><tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></table>"),
                         "| 1 | 2 |\n| 3 | 4 |")
        self.assertEqual(md("<table><tr><td>1</td><td>2</td><td>3</td></tr><tr><td>4</td></tr></table>"),
                         "| 1 | 2 | 3 |\n| 4 |  |  |")
        self.assertEqual(md("<table><tr><td>a|b</td></tr></table>"), "| a\\|b |")
        self.assertEqual(md("<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>", plain=True),
                         "A  B\n1  2")

    def test_table_cells_do_not_glue_or_leak(self):
        out = md("<table><thead><tr><th>Plan</th><th>Price</th></tr></thead><tbody><tr><td>Pro</td><td>$5</td></tr></tbody></table>")
        self.assertIn("| Pro | $5 |", out)
        out = md("<table><tr><td><p>a</p><p>b</p></td><td><ul><li>x</li><li>y</li></ul></td></tr></table>")
        self.assertEqual(out, "| a b | x y |")
        out = md("<table><tr><td>outer<table><tr><td>inner</td></tr></table></td></tr></table>")
        self.assertEqual(out, "| outer inner |")
        self.assertEqual(md("<table><caption>Cap</caption><tr><td>x</td></tr></table>"), "Cap\n\n| x |")

    def test_unclosed_table_and_row_are_still_emitted(self):
        self.assertEqual(md("<table><tr><td>a<td>b<tr><td>c"), "| a | b |\n| c |  |")


class Links(unittest.TestCase):
    def test_links_are_resolved_against_the_base(self):
        self.assertEqual(md('<a href="/x?y=1">rel</a>'), "[rel](https://example.org/x?y=1)")
        self.assertEqual(md('<a href="other">rel</a>'), "[rel](https://example.org/dir/other)")
        self.assertEqual(md('<a href="https://a.test/p">abs</a>'), "[abs](https://a.test/p)")
        self.assertEqual(md('<a href="//cdn.test/p">proto</a>'), "[proto](https://cdn.test/p)")
        self.assertEqual(md('<a href="mailto:a@b.test">mail</a>'), "[mail](mailto:a@b.test)")

    def test_unsafe_and_pointless_links_keep_only_the_text(self):
        for href in ("javascript:alert(1)", "JAVASCRIPT:alert(1)", "data:text/html,x", "vbscript:x", "file:///etc/passwd",
                     "ftp://x.test/", "#frag", "", "   ", "http://bad host/", "tel:123"):
            self.assertEqual(md(f'<a href="{href}">text</a>'), "text", href)

    def test_link_edge_cases(self):
        self.assertEqual(md('<a href="https://a.test/">   </a>'), "[https://a.test/](https://a.test/)")
        self.assertEqual(md('<a href="https://a.test/"><b>bold</b> <i>it</i></a>'), "[bold it](https://a.test/)")
        self.assertEqual(md('<a href="https://a.test/p(1)">x</a>'), "[x](https://a.test/p%281%29)")
        self.assertEqual(md('<a href="https://a.test/" title="SECRET">x</a>'), "[x](https://a.test/)")
        self.assertEqual(md('<a href="https://a.test/">one <a href="https://b.test/">two</a></a>'),
                         "[one](https://a.test/) [two](https://b.test/)")
        self.assertEqual(md('<a href="https://a.test/">x', plain=True), "x")
        self.assertEqual(md('<a href="https://a.test/">x'), "[x](https://a.test/)")

    def test_adjacent_links_are_separated(self):
        out = md('<nav><a href="/h">Home</a><a href="/p">Products</a><a href="/c">Pricing</a></nav>')
        self.assertEqual(out, "[Home](https://example.org/h) | [Products](https://example.org/p) | [Pricing](https://example.org/c)")
        self.assertEqual(md('<a href="/a">A</a> <a href="/b">B</a>'), "[A](https://example.org/a) [B](https://example.org/b)")
        self.assertEqual(md('<ul><li><a href="/a">A</a></li><li><a href="/b">B</a></li></ul>'),
                         "- [A](https://example.org/a)\n- [B](https://example.org/b)")

    def test_link_spanning_a_block_boundary(self):
        out = md('<a href="https://a.test/">first<div>second</div></a>')
        self.assertIn("[first](https://a.test/)", out)
        self.assertIn("[second](https://a.test/)", out)


class Images(unittest.TestCase):
    def test_alt_text_only_and_never_a_src(self):
        out = md('<p>x <img src="https://evil.test/p.png?d=SECRET" alt="a logo"> y</p>')
        self.assertEqual(out, "x [image: a logo] y")
        self.assertNotIn("evil", out)
        self.assertEqual(md('<img src="https://evil.test/p.png">'), "")
        self.assertEqual(md('<img src="https://evil.test/p.png" alt="  ">'), "")
        self.assertEqual(md('<a href="https://a.test/"><img src="x.png" alt="logo"></a>'), "[[image: logo]](https://a.test/)")
        self.assertEqual(md('<img src="x" alt="a">', plain=True), "[image: a]")


class TextHandling(unittest.TestCase):
    def test_entities_and_whitespace(self):
        self.assertEqual(md("<p>a &amp; b &lt;b&gt; &#8364; &eacute;</p>"), "a & b <b> € é")
        self.assertEqual(md("<p>  a \n\t b  c  </p>"), "a b c")
        self.assertEqual(md("<p>a</p>\n\n<p>b   </p>   \n"), "a\n\nb")

    def test_inline_elements_are_transparent_without_markers(self):
        self.assertEqual(md("<p><strong>a</strong> <em>b</em><u>c</u><s>d</s><mark>e</mark><span>f</span><sup>2</sup></p>"),
                         "a bcdef2")

    def test_plain_mode_has_no_markdown(self):
        out = md('<h1>T</h1><p>See <a href="https://a.test/">link</a> and <code>x</code></p><ul><li>one</li></ul>'
                 '<blockquote>q</blockquote><pre>c</pre>', plain=True)
        self.assertEqual(out, "T\n\nSee link and x\n\n- one\n\nq\n\nc")
        for marker in ("#", "](", "`", ">", "```"):
            self.assertNotIn(marker, out)

    def test_control_characters_never_reach_the_output(self):
        out = md("<p>a\x00b\x01c\x1bd\x7fe</p><pre>x\x00y</pre>")
        for ch in ("\x00", "\x01", "\x1b", "\x7f"):
            self.assertNotIn(ch, out)
        self.assertIn("abcde", out)


class Hostile(unittest.TestCase):
    def test_malformed_input_never_raises(self):
        for html in ("<div><p>unclosed", "</div></p></span>stray", "a < b and c > d", '<a href="x', "<", "<<<>>>", "<!--",
                     "<script>never closed", "<style>", "<![CDATA[x]]>", "<div <p>>", "<a href=>x</a>", "\x00\x01\x02" * 100,
                     "<table><td><tr></table></table>", "<li><li><li>", "<b><i></b></i>", "&#xFFFFFFF;&#99999999999;", "",
                     bytes(range(256)).decode("latin-1")):
            title, out = h2m.convert(html, BASE)
            self.assertIsInstance(out, str, html[:20])
        self.assertIn("a < b and c > d", md("a < b and c > d"))
        self.assertNotIn("SECRET", md("<script>SECRET <p>SECRET2</p>"))

    def test_hidden_ancestor_cannot_be_unwound_by_nesting_tricks(self):
        out = md("<div hidden>" + "<div>" * 500 + "SECRET" + "</div>" * 100 + "STILLHIDDEN")
        self.assertNotIn("SECRET", out)
        self.assertNotIn("STILLHIDDEN", out)
        out = md("<div hidden>" + "<div>" * 500 + "SECRET" + "</div>" * 600 + "<p>AFTER</p>")
        self.assertNotIn("SECRET", out)
        self.assertIn("AFTER", out)

    def test_depth_cap_drops_instead_of_flattening(self):
        self.assertIn("OK", md("<div>" * 350 + "OK" + "</div>" * 350))
        out = md("<div>" * 500 + "DEEP" + "</div>" * 500 + "<p>AFTER</p>")
        self.assertNotIn("DEEP", out)
        self.assertIn("AFTER", out)

    def test_pathological_nesting_and_stray_closers_are_fast(self):
        start = time.monotonic()
        md("<div>" * 100_000 + "x" + "</div>" * 100_000)
        md("</div>" * 200_000 + "<p>y</p>")
        md("<a href='/x'>" * 50_000)
        self.assertLess(time.monotonic() - start, 15)

    def test_a_three_megabyte_page_converts_quickly(self):
        block = ('<div class="row"><h2>Title</h2><p>Lorem ipsum dolor sit amet, <a href="/p/1">consectetur</a> adipiscing '
                 'elit, sed do <b>eiusmod</b> tempor.</p><ul><li>one</li><li>two</li></ul><table><tr><td>1</td><td>2</td></tr>'
                 '</table><script>var x = 1;</script></div>\n')
        page = "<html><head><title>Big</title></head><body>" + block * (3_000_000 // len(block)) + "</body></html>"
        start = time.monotonic()
        title, out = h2m.convert(page, BASE)
        self.assertLess(time.monotonic() - start, 15)
        self.assertEqual(title, "Big")
        self.assertIn("[consectetur](https://example.org/p/1)", out)
        self.assertNotIn("var x", out)

    def test_nothing_hidden_or_active_ever_leaks_into_the_output(self):
        page = ('<html><head><title>T</title><style>.a{}</style></head><body><p>visible</p>'
                '<div hidden>H1</div><p style="display:none">H2</p><span aria-hidden="true">H3</span>'
                '<noscript>H4</noscript><template>H5</template><!-- H6 --><script>H7</script>'
                '<img src="https://evil.test/track.gif?H8" alt=""><iframe src="https://evil.test/H9"></iframe>'
                '<svg><text>H10</text></svg><textarea>H11</textarea><input value="H12"><button>H13</button></body></html>')
        out = md(page)
        self.assertEqual(out, "visible")
        for forbidden in ("<script", "display:none", "evil.test", "track.gif"):
            self.assertNotIn(forbidden, out)


class MainContent(unittest.TestCase):
    ARTICLE = "<p>" + "Real article text. " * 20 + "</p>"

    def page(self, body):
        return f"<html><head><title>T</title></head><body>{body}</body></html>"

    def test_page_with_main_is_reduced_to_it(self):
        out = md(self.page(f'<header><nav><a href="/h">Home</a></nav></header><main><h1>Real</h1>{self.ARTICLE}</main><footer>Footer</footer>'))
        self.assertTrue(out.startswith("# Real"))
        self.assertNotIn("Home", out)
        self.assertNotIn("Footer", out)

    def test_role_main_counts_and_multiple_regions_are_all_kept(self):
        out = md(self.page(f'<nav>NAVJUNK</nav><div role="main">{self.ARTICLE}</div><nav>MORE</nav>'))
        self.assertIn("Real article", out)
        self.assertNotIn("NAVJUNK", out)
        both = md(self.page(f"<main><p>{'A' * 150}</p></main><aside>SIDE</aside><main><p>{'B' * 150}</p></main>"))
        self.assertIn("A" * 150, both)
        self.assertIn("B" * 150, both)
        self.assertNotIn("SIDE", both)

    def test_tiny_main_falls_back_to_the_whole_page(self):
        out = md(self.page("<nav>" + "Navigation words here. " * 30 + "</nav><main>Short</main>"))
        self.assertIn("Navigation words", out)

    def test_main_only_can_be_switched_off(self):
        html = self.page(f"<nav>NAVJUNK</nav><main>{self.ARTICLE}</main>")
        self.assertIn("NAVJUNK", h2m.convert(html, BASE, False, main_only=False)[1])
        self.assertNotIn("NAVJUNK", h2m.convert(html, BASE)[1])

    def test_hidden_content_inside_main_is_still_dropped(self):
        out = md(self.page(f'<main>{self.ARTICLE}<div hidden>SECRET</div><script>SECRET2</script></main>'))
        self.assertNotIn("SECRET", out)

    def test_tables_lists_and_code_inside_main_survive_and_nothing_outside_leaks(self):
        out = md(self.page('<table><tr><td>OUTSIDE</td></tr></table><pre>OUTCODE</pre><ul><li>OUTLIST</li></ul>'
                           f'<main>{self.ARTICLE}<table><tr><th>A</th></tr><tr><td>1</td></tr></table><pre>x = 1</pre></main>'))
        self.assertIn("| A |", out)
        self.assertIn("x = 1", out)
        for outside in ("OUTSIDE", "OUTCODE", "OUTLIST"):
            self.assertNotIn(outside, out)

    def test_navigation_landmarks_inside_main_are_dropped_but_not_without_main(self):
        inside = md(self.page(f'<main><nav>TOCJUNK</nav><div role="navigation">MENUJUNK</div>{self.ARTICLE}</main>'))
        self.assertNotIn("TOCJUNK", inside)
        self.assertNotIn("MENUJUNK", inside)
        self.assertIn("Real article", inside)
        self.assertIn("Home", md('<nav><a href="/h">Home</a></nav><p>x</p>'))
        self.assertIn("TOCJUNK", h2m.convert(self.page(f"<main><nav>TOCJUNK</nav>{self.ARTICLE}</main>"), BASE, False, main_only=False)[1])

    def test_title_is_kept_even_when_the_head_is_outside_main(self):
        self.assertEqual(h2m.convert(self.page(f"<main>{self.ARTICLE}</main>"), BASE)[0], "T")


if __name__ == "__main__":
    unittest.main(verbosity=2)
