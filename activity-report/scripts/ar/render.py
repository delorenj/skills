"""raw.txt in, markdown and one self-contained HTML document out.

The body grammar is the one the portal parses
(`client-portal/src/components/portal/UpdateBody.tsx`), mirrored line for line
so the HTML artifact and the portal row read the same:

    ## Heading            a section heading
    - item                a bullet (also `* item`)
    | key | value |       a two-column metric row
    HH:MM  text           a timeline entry
    anything else         a paragraph

Inline, `**bold**` is the only form; an unbalanced `**` stays literal and an
empty `****` is dropped, exactly as the portal does it. Headings and metric
cells are literal (the portal does not run them through renderInline either).

Every string that reaches the HTML goes through `html.escape`. The document
carries no script, no external asset and no storage; its only stylesheet is
`assets/report.css`, inlined.
"""
from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .common import (
    AUDIENCES, EXIT_OK, AcceptanceError, ConfigError, parse_iso, read_json, to_iso_z,
    utc_now, write_text,
)

TITLE_RE = re.compile(r"^# (.+)$")
METRIC_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|$")
CLOCK_RE = re.compile(r"^(\d{1,2}:\d{2})\s+(.*)$")

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
CSS_PATH = os.path.join(SKILL_ROOT, "assets", "report.css")

AUDIENCE_LABEL = {"external": "Client update", "internal": "Internal update"}


@dataclass
class Block:
    """One parsed block. `items` holds str for bullets, (label, value) for
    metrics and (at, text) for timeline entries; `text` is for headings and
    paragraphs."""
    kind: str
    text: str = ""
    items: list = field(default_factory=list)


# -- parsing -------------------------------------------------------------------

def split_raw(raw_text: str) -> tuple[str, str]:
    """Line 1 must be `# <title>`; the rest is the body. Raises AcceptanceError."""
    text = raw_text.lstrip("﻿").replace("\r\n", "\n")
    first, _, rest = text.partition("\n")
    match = TITLE_RE.match(first.rstrip())
    if not match or not match.group(1).strip():
        raise AcceptanceError(
            "raw.txt must start with `# <title>` on line 1 (the portal row title); "
            f"line 1 is {first[:60]!r}")
    return match.group(1).strip(), rest.strip()


def inline_runs(text: str) -> list[tuple[bool, str]]:
    """Mirror of the portal's renderInline: [(is_bold, text), ...]."""
    out: list[tuple[bool, str]] = []
    rest = text
    while rest:
        open_ = rest.find("**")
        if open_ == -1:
            out.append((False, rest))
            break
        close = rest.find("**", open_ + 2)
        if close == -1:
            out.append((False, rest))
            break
        if open_ > 0:
            out.append((False, rest[:open_]))
        inner = rest[open_ + 2:close]
        if inner:
            out.append((True, inner))
        rest = rest[close + 2:]
    return out


def parse(body: str) -> list[Block]:
    """Mirror of the portal's parseUpdateBody, check order included."""
    blocks: list[Block] = []
    for raw in body.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            blocks.append(Block("heading", text=line[3:].strip()))
            continue
        if line.startswith("- ") or line.startswith("* "):
            item = line[2:].strip()
            if blocks and blocks[-1].kind == "bullets":
                blocks[-1].items.append(item)
            else:
                blocks.append(Block("bullets", items=[item]))
            continue
        metric = METRIC_RE.match(line)
        if metric:
            row = (metric.group(1), metric.group(2))
            if blocks and blocks[-1].kind == "metrics":
                blocks[-1].items.append(row)
            else:
                blocks.append(Block("metrics", items=[row]))
            continue
        clock = CLOCK_RE.match(line)
        if clock:
            entry = (clock.group(1), clock.group(2).strip())
            if blocks and blocks[-1].kind == "timeline":
                blocks[-1].items.append(entry)
            else:
                blocks.append(Block("timeline", items=[entry]))
            continue
        blocks.append(Block("paragraph", text=line))
    return blocks


# -- prose (what Hindsight's fact extractor can read) ------------------------

def strip_bold(text: str) -> str:
    """The text without its ** markers."""
    return "".join(run for _, run in inline_runs(text))


def _sentence(text: str) -> str:
    t = strip_bold(text).strip()
    if not t:
        return ""
    return t if t[-1] in ".!?:;" else t + "."


def _timeline_sentence(at: str, text: str, dates) -> str:
    date = dates(at) if dates else None
    body = strip_bold(text).strip()
    return f"On {date} at {at}, {body}" if date else f"At {at}, {body}"


def to_prose(title: str, blocks: list[Block], lead: str | None = None, dates=None) -> str:
    """Plain sentences from the portal grammar. Hindsight's extractor returns no
    facts for metric tables and `HH:MM` timeline lines (measured 2026-09-03:
    grammar-shaped text stored 0 units in 4 of 4 retains, prose stored facts in
    4 of 9), so retain sends this instead of raw.txt: one `label: value.` per
    metric row, `On <date> at HH:MM, ...` per timeline entry (`dates` maps a
    clock to its calendar date; without it, `At HH:MM, ...`), a sentence per
    bullet, headings as `Heading:` lead-ins, bold markers dropped."""
    paras: list[str] = []
    if lead:
        paras.append(_sentence(lead))
    paras.append(_sentence(title))
    for block in blocks:
        if block.kind == "heading":
            head = strip_bold(block.text).strip().rstrip(":")
            if head:
                paras.append(head + ":")
        elif block.kind == "metrics":
            paras.append(" ".join(_sentence(f"{strip_bold(k).strip()}: {strip_bold(v).strip()}") for k, v in block.items))
        elif block.kind == "timeline":
            paras.append(" ".join(_sentence(_timeline_sentence(at, text, dates)) for at, text in block.items))
        elif block.kind == "bullets":
            paras.append(" ".join(_sentence(item) for item in block.items))
        else:
            paras.append(_sentence(block.text))
    return "\n\n".join(para for para in paras if para)


# -- markdown ------------------------------------------------------------------

def to_markdown(title: str, blocks: list[Block]) -> str:
    parts = [f"# {title}"]
    for block in blocks:
        if block.kind == "heading":
            parts.append(f"## {block.text}")
        elif block.kind == "bullets":
            parts.append("\n".join(f"- {item}" for item in block.items))
        elif block.kind == "metrics":
            rows = "\n".join(f"| {label} | {value} |" for label, value in block.items)
            parts.append(f"| Metric | Value |\n|---|---|\n{rows}")
        elif block.kind == "timeline":
            parts.append("\n".join(f"- **{at}** {text}" for at, text in block.items))
        else:
            parts.append(block.text)
    return "\n\n".join(parts) + "\n"


# -- html ----------------------------------------------------------------------

def _css() -> str:
    try:
        with open(CSS_PATH, encoding="utf-8") as fh:
            css = fh.read()
    except OSError as exc:
        raise ConfigError(f"stylesheet missing: {CSS_PATH} ({exc})") from exc
    if "</style" in css.lower():
        raise ConfigError(f"stylesheet {CSS_PATH} contains </style>; refusing to inline it")
    return css.strip()


def _inline_html(text: str) -> str:
    return "".join(f"<strong>{html.escape(t)}</strong>" if bold else html.escape(t)
                   for bold, t in inline_runs(text))


def _aware(value: str) -> datetime:
    dt = parse_iso(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _tz(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(name or "UTC")
    except Exception as exc:  # ZoneInfoNotFoundError, ValueError
        raise ConfigError(f"unknown timezone {name!r}: {exc}") from exc


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def format_range(start: datetime, end: datetime) -> str:
    if start.date() == end.date():
        return f"{start.strftime('%-d %b %Y')}, {start.strftime('%H:%M')} to {end.strftime('%H:%M %Z')}"
    return f"{start.strftime('%-d %b %Y %H:%M')} to {end.strftime('%-d %b %Y %H:%M %Z')}"


def _sections(blocks: list[Block]) -> list[tuple[str | None, list[Block]]]:
    sections: list[tuple[str | None, list[Block]]] = []
    current: list[Block] = []
    heading: str | None = None
    for block in blocks:
        if block.kind == "heading":
            if current or heading is not None:
                sections.append((heading, current))
            heading, current = block.text, []
        else:
            current.append(block)
    if current or heading is not None:
        sections.append((heading, current))
    return sections


def _render_block(block: Block, tiles: bool) -> str:
    if block.kind == "bullets":
        items = "".join(f"<li>{_inline_html(item)}</li>" for item in block.items)
        return f"<ul>{items}</ul>"
    if block.kind == "metrics":
        if tiles:
            cells = "".join(f'<div class="metric"><b>{html.escape(value)}</b><span>{html.escape(label)}</span></div>'
                            for label, value in block.items)
            return f'<div class="metrics">{cells}</div>'
        rows = "".join(f"<dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd>" for label, value in block.items)
        return f'<dl class="kv">{rows}</dl>'
    if block.kind == "timeline":
        items = "".join(
            f'<li><span class="at">{html.escape(at)}</span><span class="dot" aria-hidden="true"></span>'
            f'<span class="what">{_inline_html(text)}</span></li>'
            for at, text in block.items)
        return f'<ol class="timeline">{items}</ol>'
    return f"<p>{_inline_html(block.text)}</p>"


def to_html(title: str, blocks: list[Block], meta: dict) -> str:
    """One complete document. meta: project_name, audience, window_start,
    window_end (ISO), tz, run_id, generated_at, duration_seconds."""
    audience = meta.get("audience")
    if audience not in AUDIENCES:
        raise ConfigError(f"meta.audience must be internal or external, got {audience!r}")
    tz = _tz(meta.get("tz"))
    start = _aware(meta["window_start"]).astimezone(tz)
    end = _aware(meta["window_end"]).astimezone(tz)
    duration = meta.get("duration_seconds")
    if duration is None:
        duration = int((end - start).total_seconds())
    generated = _aware(meta["generated_at"]) if meta.get("generated_at") else utc_now()
    project = str(meta.get("project_name") or "")

    e = html.escape
    out = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        f"<title>{e(project)} · {e(title)}</title>",
        "<style>",
        _css(),
        "</style>",
        "</head>",
        "<body>",
        '<main class="wrap">',
        '<header class="masthead">',
        f'<p class="eyebrow">{e(project)} · {AUDIENCE_LABEL[audience]}</p>',
        f"<h1>{e(title)}</h1>",
        f'<p class="meta"><span class="pill {audience}">{audience.capitalize()}</span>'
        f"<span>{e(format_range(start, end))}</span><span>{e(format_duration(duration))}</span></p>",
        "</header>",
    ]
    for heading, section in _sections(blocks):
        tiles = bool(section) and all(b.kind == "metrics" for b in section)
        out.append('<section class="sec">')
        if heading is not None:
            out.append(f"<h2>{e(heading)}</h2>")
        for block in section:
            out.append(_render_block(block, tiles))
        out.append("</section>")
    if audience == "internal":
        run_id = str(meta.get("run_id") or "")
        foot = (f"Generated {e(to_iso_z(generated))} · window {e(to_iso_z(start))} to {e(to_iso_z(end))}"
                f" · run {e(run_id)}")
    else:
        foot = f"Updated {e(generated.astimezone(tz).strftime('%-d %b %Y'))}"
    out += [f'<footer class="foot">{foot}</footer>', "</main>", "</body>", "</html>", ""]
    return "\n".join(out)


# -- command -------------------------------------------------------------------

def render_cmd(args) -> int:
    with open(args.raw, encoding="utf-8") as fh:
        raw_text = fh.read()
    digest = read_json(args.digest)
    if digest.get("audience") != args.audience:
        raise ConfigError(f"digest {args.digest} is for audience {digest.get('audience')!r}, "
                          f"render asked for {args.audience!r}")
    title, body = split_raw(raw_text)
    blocks = parse(body)
    project = digest.get("project") or {}
    window = digest.get("window") or {}
    meta = {
        "project_name": project.get("name") or project.get("slug") or "",
        "audience": args.audience,
        "window_start": window["start"],
        "window_end": window["end"],
        "duration_seconds": window.get("duration_seconds"),
        "tz": project.get("timezone") or "UTC",
        "run_id": digest.get("run_id") or "",
        "generated_at": to_iso_z(utc_now()),
    }
    markdown = to_markdown(title, blocks)
    document = to_html(title, blocks, meta)

    base_dir = os.path.dirname(os.path.abspath(args.digest))
    label = digest.get("label") or "report"
    md_path = args.md or os.path.join(base_dir, f"{label}-{args.audience}.md")
    html_path = args.html or os.path.join(base_dir, f"{label}-{args.audience}.html")
    write_text(md_path, markdown)
    write_text(html_path, document)
    result = {
        "title": title, "blocks": len(blocks),
        "markdown": md_path, "markdown_bytes": len(markdown.encode("utf-8")),
        "html": html_path, "html_bytes": len(document.encode("utf-8")),
    }
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"markdown: {md_path} ({result['markdown_bytes']} bytes)")
        print(f"html:     {html_path} ({result['html_bytes']} bytes)")
    return EXIT_OK
