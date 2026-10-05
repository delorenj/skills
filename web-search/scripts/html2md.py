"""HTML to markdown for an agent reading untrusted pages. Standard library only, iterative, no I/O.

Page text comes from strangers, so the converter's first job is to not show an agent anything a human would not see:
scripts, styles, forms, comments and any element marked hidden are dropped with all their descendants, images become
their alt text (never a URL), and only http, https and mailto links survive. Structure a person relies on is kept:
headings, lists, link targets, code indentation and table rows. Never recurses; element depth beyond MAX_DEPTH is
dropped rather than flattened, because flattening would let an attacker unwind a hidden ancestor early.
"""
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

MAX_DEPTH = 400
#: Output amplifiers. A hostile table pads every row to the widest row, so
#: rows x columns is quadratic in emitted size (a 1 MB page amplified to ~15 GB
#: before these caps); deeply nested quotes/lists pay their prefix on every
#: line. Real tables and nesting never approach these bounds.
MAX_TABLE_ROWS = 500
MAX_TABLE_COLS = 60
MAX_PREFIX_DEPTH = 20

_DROP = frozenset("script style noscript template svg iframe object embed canvas input select option optgroup datalist "
                  "textarea button noembed noframes rp".split())
_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
_BLOCK = frozenset("p div section article header footer main aside nav figure figcaption address form fieldset details "
                   "summary center".split())
_HEADINGS = {f"h{i}": i for i in range(1, 7)}
_AUTOCLOSE = {"p": ({"p"}, set()), "li": ({"li"}, {"ul", "ol"}), "dt": ({"dt", "dd"}, {"dl"}),
              "dd": ({"dt", "dd"}, {"dl"}), "tr": ({"tr"}, {"table"}), "td": ({"td", "th"}, {"tr", "table"}),
              "th": ({"td", "th"}, {"tr", "table"})}
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)", re.I)
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_CSS_ESCAPE = re.compile(r"\\([0-9a-fA-F]{1,6})[ \t\r\n\f]?")
_SPACE = re.compile("[ \t\r\n\f\v ]+")
_CTRL = re.compile("[\x00-\x08\x0b-\x1f\x7f]")
_SAFE_SCHEMES = ("http", "https", "mailto")


def _normalize_style(value):
    # Strip CSS comments and decode \-hex escapes before matching, so
    # "display/**/:none" or "d\69splay:none" cannot smuggle a hidden rule past
    # the regex; a rule that only ever existed inside a comment disappears and
    # correctly does not count as hiding.
    value = _CSS_COMMENT.sub(" ", value)
    return _CSS_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), value)


def _hidden(attrs):
    for name, value in attrs:
        if name == "hidden" or (name == "aria-hidden" and (value or "").strip().lower() == "true"):
            return True
        if name == "type" and (value or "").strip().lower() == "hidden":
            return True
        if name == "style" and value and _HIDDEN_STYLE.search(_normalize_style(value)):
            return True
    return False


def _clean_url(base, href):
    href = (href or "").strip()
    if not href or href.startswith("#"):
        return None
    try:
        url = urljoin(base, href)
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme.lower() not in _SAFE_SCHEMES or re.search(r"[\x00-\x20\x7f]", url):
        return None
    return url.replace("(", "%28").replace(")", "%29")


class _Converter(HTMLParser):
    def __init__(self, base_url, plain, main_only=False):
        super().__init__(convert_charrefs=True)
        self.base, self.plain = base_url, plain
        self.out = []
        self.cur = []
        self.stack = []
        self.open = Counter()
        self.drop = 0
        self.title = []
        self.in_title = False
        self.lists = []
        self.quote = 0
        self.item_prefix = ""
        self.once_prefix = ""
        self.pre = None
        self.main_only = main_only
        self.main_depth = 0
        self.link = None
        self.after_link = False
        self.table_depth = 0
        self.table = None
        self.cell = None
        self.row = None
        self.row_has_th = False

    def is_site_chrome(self, tag, attrs):
        """Inside the main region, navigation landmarks are menus and tables of contents, not the page."""
        return self.main_only and self.main_depth > 0 and (
            tag == "nav" or any(n == "role" and (v or "").strip().lower() == "navigation" for n, v in attrs))

    def visible(self):
        return not self.main_only or self.main_depth > 0

    def emit_lines(self, text):
        if not self.visible():
            return
        prefix = "" if self.plain else "> " * min(self.quote, MAX_PREFIX_DEPTH)
        for line in text.split("\n"):
            self.out.append((prefix + line).rstrip() if prefix else line.rstrip())

    def blank(self):
        if self.visible() and self.cell is None and self.out and self.out[-1] != "":
            self.out.append("")

    def flush(self):
        if self.link is not None and self.cur[self.link[1]:]:
            self._wrap_link()
            self.link = (self.link[0], 0)
        text = _SPACE.sub(" ", "".join(self.cur)).strip()
        self.cur = []
        self.after_link = False
        if not text or not self.visible():
            return
        if self.cell is not None:
            self.cell.append(text)
            return
        if self.once_prefix:
            text, self.once_prefix = self.once_prefix + text, ""
        elif self.item_prefix:
            text, self.item_prefix = self.item_prefix + text, " " * len(self.item_prefix)
        self.emit_lines(text)

    def _wrap_link(self):
        url, start = self.link
        raw = "".join(self.cur[start:])
        text = _SPACE.sub(" ", raw).strip() or url
        del self.cur[start:]
        lead = " " if raw[:1].isspace() else ""
        trail = " " if raw[-1:].isspace() else ""
        self.cur.append(f"{lead}{text if self.plain else f'[{text}]({url})'}{trail}")

    def block_break(self, blank=True):
        self.flush()
        if blank:
            self.blank()

    def push(self, tag, dropped, is_main=False):
        self.stack.append((tag, dropped, is_main))
        self.open[tag] += 1
        if dropped:
            self.drop += 1
        if is_main:
            self.main_depth += 1

    def release(self, frame):
        name, dropped, is_main = frame
        self.open[name] -= 1
        if dropped:
            self.drop -= 1
        if is_main:
            self.main_depth -= 1
        self.end_effects(name, dropped)

    def pop_to(self, tag):
        while self.stack:
            frame = self.stack.pop()
            self.release(frame)
            if frame[0] == tag:
                return

    def autoclose(self, tag):
        closers, bounds = _AUTOCLOSE[tag]
        for depth, frame in enumerate(reversed(self.stack)):
            top = frame[0]
            if depth >= 32 or top in bounds:
                return
            if top in closers:
                for _ in range(depth + 1):
                    self.release(self.stack.pop())
                return

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        if tag == "title" and not self.drop and not self.title:
            self.in_title = True
        void = tag in _VOID
        if self.drop:
            # Cap the frame stack even while dropping: a hostile page of
            # nested tags inside one hidden subtree used to push unbounded
            # frames (~120 B each) and balloon memory past the input size.
            if not void and len(self.stack) < MAX_DEPTH:
                self.push(tag, True)
            return
        if tag in _AUTOCLOSE:
            self.autoclose(tag)
        dropped = tag in _DROP or _hidden(attrs) or len(self.stack) >= MAX_DEPTH or self.is_site_chrome(tag, attrs)
        if dropped:
            if not void and len(self.stack) < MAX_DEPTH:
                self.push(tag, True)
            return
        attr_map = dict(attrs)
        is_main = tag == "main" or (attr_map.get("role") or "").strip().lower() == "main"
        if not void:
            self.push(tag, False, is_main)
        self.start_effects(tag, attr_map)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in _VOID or self.open[tag] <= 0:
            return
        self.pop_to(tag)

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
            return
        if self.drop:
            return
        if self.pre is not None:
            self.pre.append(data)
            return
        if data:
            self.after_link = False
            self.cur.append(data)

    def start_effects(self, tag, attrs):
        if tag in _HEADINGS:
            self.block_break()
            self.once_prefix = "" if self.plain else "#" * _HEADINGS[tag] + " "
        elif tag in _BLOCK or tag in ("dl", "caption", "figure"):
            self.block_break()
        elif tag in ("ul", "ol"):
            self.block_break(blank=not self.lists)
            self.lists.append([tag == "ol", 0])
        elif tag == "li":
            self.flush()
            if not self.lists:
                self.lists.append([False, 0])
            frame = self.lists[-1]
            frame[1] += 1
            self.item_prefix = "  " * min(len(self.lists) - 1, MAX_PREFIX_DEPTH) + (f"{frame[1]}. " if frame[0] else "- ")
        elif tag == "dt":
            self.block_break(blank=False)
        elif tag == "dd":
            self.block_break(blank=False)
            self.item_prefix = ": "
        elif tag == "blockquote":
            self.block_break()
            self.quote += 1
        elif tag == "hr":
            self.block_break()
            if not self.plain:
                self.emit_lines("---")
            self.blank()
        elif tag == "br":
            if self.pre is not None:
                self.pre.append("\n")
            else:
                self.flush()
        elif tag == "pre":
            self.block_break()
            self.pre = []
        elif tag == "code" and self.pre is None and not self.plain:
            self.cur.append("`")
        elif tag == "table":
            self.table_depth += 1
            if self.table_depth == 1:
                self.block_break()
                self.table = []
            else:
                self.flush()
        elif tag in ("tr", "td", "th") and self.table_depth > 1:
            self.flush()
        elif tag == "tr" and self.table_depth == 1:
            self.flush()
            self.row, self.row_has_th = [], False
        elif tag in ("td", "th") and self.table_depth == 1:
            self.flush()
            if self.row is None:
                self.row, self.row_has_th = [], False
            self.cell = []
            self.row_has_th = self.row_has_th or tag == "th"
        elif tag == "a":
            url = _clean_url(self.base, attrs.get("href"))
            if self.link is not None:
                self._wrap_link()
                self.link = None
            if url is not None:
                if self.after_link:
                    self.cur.append(" | ")
                self.link = (url, len(self.cur))
        elif tag == "img":
            alt = _SPACE.sub(" ", attrs.get("alt") or "").strip()
            if alt:
                self.cur.append(f" [image: {alt}] ")

    def end_effects(self, tag, dropped):
        if dropped:
            return
        if tag in _HEADINGS:
            self.block_break()
            self.once_prefix = ""
        elif tag in _BLOCK or tag in ("dl", "caption", "figure"):
            self.block_break()
        elif tag in ("ul", "ol"):
            self.flush()
            if self.lists:
                self.lists.pop()
            self.item_prefix = ""
            if not self.lists:
                self.blank()
        elif tag == "li":
            self.flush()
            self.item_prefix = ""
        elif tag in ("dt", "dd"):
            self.flush()
            self.item_prefix = ""
        elif tag == "blockquote":
            self.block_break()
            self.quote = max(0, self.quote - 1)
        elif tag == "pre":
            self.end_pre()
        elif tag == "code" and self.pre is None and not self.plain:
            self.cur.append("`")
        elif tag == "table":
            if self.table_depth == 1:
                self.finish_row()
                self.emit_table()
            else:
                self.flush()
            self.table_depth = max(0, self.table_depth - 1)
        elif tag in ("tr", "td", "th") and self.table_depth > 1:
            self.flush()
        elif tag == "tr" and self.table_depth == 1:
            self.finish_row()
        elif tag in ("td", "th") and self.table_depth == 1:
            self.flush()
            if self.cell is not None and self.row is not None:
                self.row.append(" ".join(self.cell))
            self.cell = None
        elif tag == "a":
            if self.link is not None:
                self._wrap_link()
                self.link = None
                self.after_link = True

    def finish_row(self):
        self.flush()
        if self.cell is not None and self.row is not None:
            self.row.append(" ".join(self.cell))
            self.cell = None
        if self.row is not None and self.table is not None and any(c for c in self.row):
            self.table.append((self.row, self.row_has_th))
        self.row = None

    def emit_table(self):
        rows, self.table = self.table or [], None
        if not rows:
            return
        width = max(len(r) for r, _ in rows)
        for i, (row, has_th) in enumerate(rows):
            cells = [c.replace("|", "\\|") if not self.plain else c for c in row] + [""] * (width - len(row))
            if self.plain:
                self.emit_lines("  ".join(cells).rstrip())
            else:
                self.emit_lines("| " + " | ".join(cells) + " |")
                if i == 0 and has_th:
                    self.emit_lines("| " + " | ".join(["---"] * width) + " |")
        self.blank()

    def end_pre(self):
        text, self.pre = "".join(self.pre or []), None
        text = text.replace("\r\n", "\n").strip("\n").rstrip()
        if not text.strip():
            return
        if self.plain:
            self.emit_lines(text)
        else:
            longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
            fence = "`" * max(3, longest + 1)
            self.emit_lines(f"{fence}\n{text}\n{fence}")
        self.blank()

    def finish(self):
        if self.pre is not None:
            self.end_pre()
        self.flush()
        if self.table is not None:
            self.finish_row()
            self.emit_table()
        text = "\n".join(self.out)
        text = _CTRL.sub("", text)
        # Linear per-line rstrip; a r"[ \t]+\n" regex backtracks
        # catastrophically on long space-runs (hostile pages emitted minutes-
        # long stalls here).
        text = "\n".join(line.rstrip(" \t") for line in text.split("\n"))
        return re.sub(r"\n{3,}", "\n\n", text).strip()


_HAS_MAIN = re.compile(r"<main[\s>/]|role\s*=\s*[\"']?main", re.I)


def _run(html, base_url, plain, main_only):
    conv = _Converter(base_url or "", plain, main_only)
    try:
        conv.feed(html)
        conv.close()
    except Exception:
        pass
    title = _SPACE.sub(" ", _CTRL.sub("", "".join(conv.title))).strip()
    return title, conv.finish()


def convert(html, base_url="", plain=False, main_only=True):
    """Return (title, text): the cleaned <title> ('' if none) and the page as markdown, or plain text.

    With main_only (the default) a page that has a <main> element or role="main" is reduced to that region, which drops
    site navigation and footers; if the region is tiny next to the whole page, the whole page is returned instead."""
    html = html if isinstance(html, str) else str(html)
    if main_only and _HAS_MAIN.search(html):
        title, text = _run(html, base_url, plain, True)
        if len(text) >= 200:
            return title, text
        full_title, full = _run(html, base_url, plain, False)
        return (title or full_title), (full if len(full) >= 3 * max(len(text), 1) else text)
    return _run(html, base_url, plain, False)


if __name__ == "__main__":
    print(convert(sys.stdin.read(), sys.argv[1] if len(sys.argv) > 1 else "")[1])
