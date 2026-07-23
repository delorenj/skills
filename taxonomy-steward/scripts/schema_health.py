#!/usr/bin/env python3
"""Measure taxonomy health across a markdown tree — the evidence a steward acts on.

Reports: tag frequency + singleton fat-tail + notes:tag ratio, near-duplicate tags,
per-field fill-rate (orphan/dead fields + base-candidate fields), naming-convention
inconsistency (kebab vs snake, same field in both forms), and enum/value sprawl on
controlled fields. No writes. Needs PyYAML.

  schema_health.py <dir> [--recent-days N] [--json] [--watch f1,f2,...]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: `uv run python schema_health.py ...` or pip install pyyaml")

SKIP = {".git", ".venv", "node_modules", "__pycache__", ".stversions", ".obsidian",
        ".curator", "_bmad", "_bmad-output", ".trash"}
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
WATCH_DEFAULT = ["category", "kind", "asset-kind", "pipeline-status", "contact-type", "status"]


def parse_fm(path):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    m = FM_RE.match(text)
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else {}
    except Exception:
        return None  # unparseable


def norm_tag(t):
    return re.sub(r"[-_\s]+", " ", str(t).strip().lower()).rstrip("s")


def collect(root, recent_days):
    notes, unparseable = [], 0
    cutoff = None
    if recent_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=recent_days)
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            p = Path(dirpath) / f
            fm = parse_fm(p)
            if fm is None:
                unparseable += 1
                continue
            if cutoff:
                try:
                    mt = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                    if mt < cutoff:
                        continue
                except OSError:
                    continue
            notes.append(fm)
    return notes, unparseable


def as_list(v):
    if v is None or v == "":
        return []
    return v if isinstance(v, list) else [v]


def analyze(notes, watch):
    n = len(notes)
    tag_counter = Counter()
    notes_with_tags = 0
    for fm in notes:
        tags = as_list(fm.get("tags"))
        if tags:
            notes_with_tags += 1
        tag_counter.update(str(t) for t in tags)

    distinct = len(tag_counter)
    singletons = [t for t, c in tag_counter.items() if c == 1]
    ratio = round(distinct / notes_with_tags, 3) if notes_with_tags else 0.0

    near = defaultdict(list)
    for t in tag_counter:
        near[norm_tag(t)].append(t)
    near_dups = {k: v for k, v in near.items() if len(v) > 1}

    field_counter = Counter()
    for fm in notes:
        field_counter.update(fm.keys())
    fill = {k: round(c / n, 3) for k, c in field_counter.items()} if n else {}
    orphans = sorted([k for k, r in fill.items() if r < 0.05])
    base_cands = sorted([k for k, r in fill.items() if r >= 0.90])

    keys = set(field_counter)
    snake = sorted(k for k in keys if "_" in k)
    kebab = sorted(k for k in keys if "-" in k)
    dual = sorted(k for k in keys if k.replace("_", "-") in keys and "_" in k)

    enums = {}
    for field in watch:
        vals = Counter()
        for fm in notes:
            for v in as_list(fm.get(field)):
                vals[str(v)] += 1
        if vals:
            enums[field] = vals

    return {
        "notes": n, "notes_with_tags": notes_with_tags,
        "distinct_tags": distinct, "singleton_tags": len(singletons),
        "notes_to_tag_ratio": ratio,
        "singletons": sorted(singletons),
        "near_duplicate_tags": near_dups,
        "field_fill_rate": dict(sorted(fill.items(), key=lambda x: -x[1])),
        "orphan_fields": orphans, "base_candidate_fields": base_cands,
        "snake_case_keys": snake, "kebab_case_keys": kebab, "dual_convention_keys": dual,
        "enum_values": {k: dict(v.most_common()) for k, v in enums.items()},
    }


def report(r):
    out = []
    out.append(f"notes analyzed: {r['notes']}  (with tags: {r['notes_with_tags']})")
    out.append("")
    out.append("── TAG HEALTH ──")
    out.append(f"  distinct tags: {r['distinct_tags']}   singletons: {r['singleton_tags']}")
    ratio = r["notes_to_tag_ratio"]
    flag = "  ⚠ EXPLOSION (→1)" if ratio >= 0.6 else ""
    out.append(f"  notes:tag ratio (distinct/tagged-notes): {ratio}{flag}")
    if r["near_duplicate_tags"]:
        out.append(f"  near-duplicate tag clusters: {len(r['near_duplicate_tags'])}")
        for k, v in list(r["near_duplicate_tags"].items())[:15]:
            out.append(f"    merge? {v}")
    out.append("")
    out.append("── FIELD HEALTH ──")
    out.append(f"  base-candidate fields (fill ≥90%): {r['base_candidate_fields']}")
    out.append(f"  orphan/dead fields (fill <5%): {r['orphan_fields']}")
    if r["dual_convention_keys"]:
        out.append(f"  ⚠ same field in both kebab+snake: {r['dual_convention_keys']}")
    out.append(f"  snake_case keys (convention drift?): {r['snake_case_keys']}")
    out.append("")
    out.append("── ENUM/VALUE SPRAWL (controlled fields) ──")
    for field, vals in r["enum_values"].items():
        n_vals = len(vals)
        flag = "  ⚠ sprawl" if n_vals > 12 else ""
        out.append(f"  {field}: {n_vals} distinct{flag}")
        top = list(vals.items())[:8]
        out.append(f"    {top}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir", type=Path)
    ap.add_argument("--recent-days", type=int, default=0, help="only notes modified in last N days (emergent-pattern scan)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--watch", default=",".join(WATCH_DEFAULT), help="controlled fields to profile")
    a = ap.parse_args()
    notes, bad = collect(a.dir, a.recent_days)
    r = analyze(notes, [w.strip() for w in a.watch.split(",") if w.strip()])
    r["unparseable"] = bad
    if a.json:
        print(json.dumps(r, indent=2, default=str))
    else:
        print(report(r))
        if bad:
            print(f"\n(unparseable frontmatter: {bad})")


if __name__ == "__main__":
    main()
