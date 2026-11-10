#!/usr/bin/env python3
"""deal-position: init, snapshot, lint and render an AutomaticAI deal position.

Stdlib only (pandoc is used for render if present).

  position.py init <dir> --engagement ID --counterparty "Name (Co)"
  position.py snapshot <dir>          # copy POSITION.md -> history/<as_of>.md
  position.py lint <dir>/POSITION.md  # exit 1 with reasons on failure
  position.py render <dir>            # -> <dir>/site/index.html
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "references" / "template.md"

SCHEMAS = {"automaticai.position/v1"}

SECTIONS_V1 = [
    "Evaluation",
    "Moves since last position",
    "The board",
    "Players",
    "The game",
    "Our line",
    "Candidate moves",
    "Open loops",
    "Threats",
    "Doctrine check",
    "Keep private",
    "Sources",
]
REQUIRED_KEYS = [
    "schema", "engagement", "counterparty", "as_of", "move", "previous",
    "to_move", "initiative", "evaluation", "phase", "next_move", "delta",
]
ENUMS = {
    "evaluation": ["winning", "better", "slightly-better", "equal",
                   "slightly-worse", "worse", "losing"],
    "initiative": ["us", "them", "neither"],
    "to_move": ["us", "them"],
    "phase": ["opening", "middlegame", "endgame"],
}
CONFIDENCE = {"verified-live", "verified-doc", "inferred", "stale-suspect"}
TABLES = {
    "The board": ["Area", "Fact", "As of", "Source", "Confidence"],
    "Candidate moves": ["Player", "Move", "Probability", "Our best reply"],
    "Open loops": ["Item", "Owner", "State", "Due", "Source"],
}
MOVE_LINE = re.compile(r"^(\d+)\.\s+(.*)$")
PLACEHOLDER = re.compile(r"<(?:[A-Z][^<>\n]*|[a-z]+ [^<>\n]*\|[^<>\n]*)>")


# ---------------------------------------------------------------- parsing
def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("no YAML frontmatter (file must start with '---')")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("frontmatter not closed with '---'")
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"frontmatter line without key: {line!r}")
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, text[end + 5:]


def parse_as_of(value: str) -> dt.datetime:
    stamp = dt.datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError(f"as_of {value!r} has no UTC offset")
    return stamp


def h2_sections(body: str) -> list[tuple[str, str]]:
    """Return [(heading, content)] for each '## ' heading outside code fences."""
    out: list[tuple[str, list[str]]] = []
    fenced = False
    for line in body.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            out.append((line[3:].strip(), []))
        elif out:
            out[-1][1].append(line)
    return [(h, "\n".join(c)) for h, c in out]


def table_rows(content: str) -> tuple[list[str] | None, list[list[str]]]:
    lines = [l.strip() for l in content.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return None, []
    cells = lambda l: [c.strip() for c in l.strip("|").split("|")]
    header = cells(lines[0])
    rows = [cells(l) for l in lines[2:]]
    return header, rows


def stamp_slug(as_of: str) -> str:
    return parse_as_of(as_of).strftime("%Y%m%dT%H%M%z")


# ---------------------------------------------------------------- lint
def lint(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        meta, body = split_frontmatter(path.read_text())
    except (OSError, ValueError) as exc:
        return [str(exc)]

    for key in REQUIRED_KEYS:
        if not meta.get(key):
            errors.append(f"frontmatter: missing '{key}'")
    if meta.get("schema") and meta["schema"] not in SCHEMAS:
        errors.append(f"frontmatter: unknown schema {meta['schema']!r}; known: {sorted(SCHEMAS)}")
    for key, allowed in ENUMS.items():
        if meta.get(key) and meta[key] not in allowed:
            errors.append(f"frontmatter: {key}={meta[key]!r} not in {allowed}")
    as_of = None
    if meta.get("as_of"):
        try:
            as_of = parse_as_of(meta["as_of"])
        except ValueError as exc:
            errors.append(f"frontmatter: {exc}")
    move = None
    if meta.get("move"):
        if meta["move"].isdigit():
            move = int(meta["move"])
        else:
            errors.append(f"frontmatter: move={meta['move']!r} is not an integer")

    # sections, exact order
    sections = h2_sections(body)
    names = [h for h, _ in sections]
    if names != SECTIONS_V1:
        missing = [s for s in SECTIONS_V1 if s not in names]
        extra = [s for s in names if s not in SECTIONS_V1]
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"unexpected {extra}")
        if not detail:
            detail.append(f"order is {names}")
        errors.append("sections: must be exactly " + " > ".join(SECTIONS_V1) + "; " + "; ".join(detail))
    by_name = dict(sections)
    for name, content in sections:
        if not content.strip():
            errors.append(f"section '{name}' is empty (write 'None this move.')")

    # tables
    for name, cols in TABLES.items():
        content = by_name.get(name)
        if content is None:
            continue
        header, rows = table_rows(content)
        if header is None:
            if "none this move" not in content.lower():
                errors.append(f"section '{name}': needs a table with columns {cols}")
            continue
        if header != cols:
            errors.append(f"section '{name}': columns {header} != {cols}")
            continue
        for i, row in enumerate(rows, 1):
            if len(row) != len(cols):
                errors.append(f"'{name}' row {i}: {len(row)} cells, expected {len(cols)}")
                continue
            if name == "The board":
                if row[4] not in CONFIDENCE:
                    errors.append(f"board row {i}: confidence {row[4]!r} not in {sorted(CONFIDENCE)}")
                if not row[3]:
                    errors.append(f"board row {i}: empty source")
                if not row[2]:
                    errors.append(f"board row {i}: empty 'As of'")
        if name == "The board" and not rows:
            errors.append("board: no rows")

    # leftover template instructions
    for lineno, line in enumerate(body.splitlines(), 1):
        if PLACEHOLDER.search(line):
            errors.append(f"body line {lineno}: unreplaced template placeholder: {line.strip()[:80]}")

    # move log continuity
    moves_path = path.parent / "moves.md"
    if not moves_path.exists():
        errors.append("moves.md: missing next to POSITION.md")
    else:
        numbers = []
        for lineno, line in enumerate(moves_path.read_text().splitlines(), 1):
            m = MOVE_LINE.match(line)
            if not m:
                continue
            numbers.append(int(m.group(1)))
            fields = [f.strip() for f in m.group(2).split("·")]
            if len(fields) < 5 or not all(fields[:5]):
                errors.append(f"moves.md line {lineno}: want 'date · player · move · source · effect'")
            elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fields[0]):
                errors.append(f"moves.md line {lineno}: date {fields[0]!r} is not YYYY-MM-DD")
        if numbers != list(range(1, len(numbers) + 1)):
            errors.append(f"moves.md: numbering not contiguous from 1: {numbers}")
        if move is not None and numbers and numbers[-1] != move:
            errors.append(f"frontmatter move={move} but moves.md ends at {numbers[-1]}")

    # previous must exist and be older
    prev = meta.get("previous", "")
    if prev and prev != "none":
        prev_path = path.parent / prev
        if not prev_path.exists():
            errors.append(f"previous: {prev} does not exist")
        elif as_of is not None:
            try:
                prev_meta, _ = split_frontmatter(prev_path.read_text())
                if parse_as_of(prev_meta["as_of"]) >= as_of:
                    errors.append(f"as_of {meta['as_of']} does not advance past previous {prev_meta['as_of']}")
                if prev_meta.get("move", "").isdigit() and move is not None and int(prev_meta["move"]) > move:
                    errors.append("move number went backwards from previous position")
            except (KeyError, ValueError) as exc:
                errors.append(f"previous: unreadable ({exc})")
    return errors


# ---------------------------------------------------------------- commands
def template_block() -> str:
    text = TEMPLATE.read_text()
    m = re.search(r"```markdown\n(.*?)\n```", text, re.S)
    if not m:
        raise SystemExit(f"no ```markdown block in {TEMPLATE}")
    return m.group(1) + "\n"


def cmd_init(args: argparse.Namespace) -> int:
    d = Path(args.dir)
    (d / "history").mkdir(parents=True, exist_ok=True)
    pos = d / "POSITION.md"
    if pos.exists():
        print(f"{pos} exists; refusing to overwrite", file=sys.stderr)
        return 1
    body = template_block()
    body = body.replace("<engagement id from engagements.md, e.g. james-brennan>", args.engagement)
    body = body.replace("<person (company)>", args.counterparty)
    body = body.replace('<history/<as_of>.md, or "none">', "none")
    pos.write_text(body)
    moves = d / "moves.md"
    if not moves.exists():
        moves.write_text(f"# Move log: {args.counterparty}\n\n")
    print(f"initialised {d} (fill POSITION.md, then lint)")
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    d = Path(args.dir)
    pos = d / "POSITION.md"
    if not pos.exists():
        print("no POSITION.md yet; nothing to snapshot")
        return 0
    meta, _ = split_frontmatter(pos.read_text())
    target = d / "history" / f"{stamp_slug(meta['as_of'])}.md"
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        if target.read_text() == pos.read_text():
            print(f"already archived: {target}")
            return 0
        print(f"{target} exists with different content; refusing", file=sys.stderr)
        return 1
    shutil.copyfile(pos, target)
    print(f"archived -> {target.relative_to(d)}  (set previous: {target.relative_to(d)} in the new position)")
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    errors = lint(Path(args.path))
    if errors:
        print(f"FAIL {args.path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK {args.path}")
    return 0


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a66;--line:#e2dfd8;--acc:#2f5d50;--chip:#eef3f0}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#ecebe6;--mut:#9c9a93;--line:#2c2b28;--acc:#8fc2b0;--chip:#1f2a26}}
body{background:var(--bg);color:var(--fg);font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;max-width:980px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:1.7rem;margin:.2em 0}h2{font-size:1.2rem;margin-top:2.2em;padding-top:.6em;border-top:1px solid var(--line);color:var(--acc)}
h3{font-size:1.02rem;margin-bottom:.3em}
table{border-collapse:collapse;width:100%;font-size:.88rem;display:block;overflow-x:auto}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
code{font-size:.85em}a{color:var(--acc)}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin:12px 0 4px}
.meta div{background:var(--chip);border-radius:8px;padding:8px 10px}.meta b{display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.next{background:var(--chip);border-left:4px solid var(--acc);padding:10px 14px;border-radius:6px;margin:10px 0}
.private{color:var(--mut);font-size:.8rem}
"""


def cmd_render(args: argparse.Namespace) -> int:
    d = Path(args.dir)
    meta, body = split_frontmatter((d / "POSITION.md").read_text())
    moves = (d / "moves.md").read_text() if (d / "moves.md").exists() else ""
    moves = re.sub(r"^# .*\n", "", moves, count=1)
    title_m = re.search(r"^# (.+)$", body, re.M)
    title = title_m.group(1) if title_m else f"The Position: {meta.get('counterparty', '')}"
    body = re.sub(r"^# .+\n", "", body, count=1)
    md = body + "\n\n## Move log\n\n" + moves
    if shutil.which("pandoc"):
        content = subprocess.run(
            ["pandoc", "-f", "gfm", "-t", "html5"], input=md, capture_output=True, text=True, check=True
        ).stdout
    else:
        content = "<pre>" + html.escape(md) + "</pre>"
    chips = "".join(
        f"<div><b>{html.escape(k.replace('_', ' '))}</b>{html.escape(meta.get(k, ''))}</div>"
        for k in ("evaluation", "initiative", "to_move", "phase", "as_of", "move")
    )
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<p class="private">INTERNAL: AutomaticAI only. Never forward to the counterparty. Schema {html.escape(meta.get('schema', ''))}.</p>
<h1>{html.escape(title)}</h1>
<div class="meta">{chips}</div>
<div class="next"><b>Next move:</b> {html.escape(meta.get('next_move', ''))}<br><b>Delta:</b> {html.escape(meta.get('delta', ''))}</div>
{content}
</body></html>
"""
    out = d / "site" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    print(f"rendered -> {out}  (slug: {meta.get('engagement', 'deal')}-position-{stamp_slug(meta['as_of'])[:13].replace('T', '')})")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init"); s.add_argument("dir"); s.add_argument("--engagement", required=True); s.add_argument("--counterparty", required=True); s.set_defaults(fn=cmd_init)
    s = sub.add_parser("snapshot"); s.add_argument("dir"); s.set_defaults(fn=cmd_snapshot)
    s = sub.add_parser("lint"); s.add_argument("path"); s.set_defaults(fn=cmd_lint)
    s = sub.add_parser("render"); s.add_argument("dir"); s.set_defaults(fn=cmd_render)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
