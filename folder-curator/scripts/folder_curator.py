#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6"]
# ///
"""folder-curator — deterministic classify / rename / enrich / route engine.

One declarative contract (taxonomy.yaml), three executors. This is the CLI executor,
shared by the agent (SKILL.md) and — transitionally — the n8n Execute Command node.

Subcommands
  plan <file>      Print the JSON intake plan (destination, canonical name, frontmatter). No writes.
  apply <file>     Execute the plan (move + rename + enrich); idempotent via the ledger.
  reindex          Regenerate <root>/_context-stack.md and restore mtimes from `updated`.
  normalize        Bring existing category files into canonical name + frontmatter (--dry-run default).
  triage           Recursively reconcile the whole tree: relocate misfiled files, rename, enrich, and
                   run transforms (e.g. PDF->markdown + S3 archive). --apply to write; dry-run default.

Contract resolution: assets/taxonomy.default.yaml (resolved from this script's realpath),
deep-merged with <client-root>/.curator/taxonomy.yaml when present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

# ─────────────────────────────── contract ──────────────────────────────────────


def deep_merge(base, over):
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = deep_merge(base.get(k), v) if k in out else v
        return out
    return over if over is not None else base


def default_contract_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "taxonomy.default.yaml"


def load_contract(client_root: Path) -> dict:
    contract = yaml.safe_load(default_contract_path().read_text(encoding="utf-8")) or {}
    override = client_root / ".curator" / "taxonomy.yaml"
    if override.exists():
        ov = yaml.safe_load(override.read_text(encoding="utf-8")) or {}
        contract = deep_merge(contract, ov)
    return contract


# ─────────────────────────────── frontmatter ───────────────────────────────────

_FM_RE = re.compile(r"^﻿?---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_MD_EXT = {".md", ".markdown"}


def read_frontmatter(path: Path):
    """Return (frontmatter_dict_or_None, body). None frontmatter => non-markdown."""
    if path.suffix.lower() not in _MD_EXT:
        return None, None
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {}, ""
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    if isinstance(fm, dict):
        # Formatters may unquote ISO dates, which YAML then parses into
        # date/datetime objects; downstream slicing expects strings.
        fm = {
            k: (v.isoformat() if isinstance(v, date) else v)
            for k, v in fm.items()
        }
    return (fm if isinstance(fm, dict) else {}), m.group(2)


def dump_frontmatter(fm: dict, order: list) -> str:
    ordered = {k: fm[k] for k in order if k in fm}
    for k, v in fm.items():
        ordered.setdefault(k, v)
    body = yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, default_flow_style=False).strip()
    return f"---\n{body}\n---\n"


def read_meta_sidecar(path: Path, suffixes) -> dict:
    for suf in suffixes:
        cand = path.with_name(path.stem + suf)
        if cand.exists():
            try:
                return json.loads(cand.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
    return {}


def find_sidecar(path: Path, suffixes):
    for suf in suffixes:
        cand = path.with_name(path.stem + suf)
        if cand.exists():
            return cand
    return None


def is_sidecar(path: Path, suffixes) -> bool:
    return any(path.name.endswith(suf) for suf in suffixes)


# ─────────────────────────────── naming ────────────────────────────────────────

_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def first_heading(body: str | None):
    if not body:
        return None
    m = _H1_RE.search(body)
    return m.group(1).strip() if m else None


def apply_repairs(name: str, contract: dict) -> str:
    for rule in contract.get("naming", {}).get("repairs", []):
        name = re.sub(rule["match"], rule["replace"], name)
    return name


_DATE_RE = r"(\d{4})[-]?(\d{2})[-]?(\d{2})(?:[-_ T]?(\d{2})[.:]?(\d{2})(?:[.:]?(\d{2}))?)?"


def _parse_dt(v):
    """Coerce a str / PyYAML date / datetime into a naive datetime, or None."""
    if isinstance(v, datetime):
        return v.replace(tzinfo=None)
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def extract_datetime(stem: str, fm: dict | None, path: Path):
    """Return (datetime, has_time). A leading filename date/time is the primary source;
    an explicit `captured` overrides it ONLY when it disagrees on the calendar day (e.g. a
    transcript named 20260713 whose `captured` is the 2026-07-12 call date). When they agree,
    the filename's finer time is kept — this keeps naming idempotent for timestamped items
    (a date-only `captured` must not erase an `HHMMSS` filename). Falls back to other
    frontmatter dates, then file mtime."""
    fm = fm or {}
    fdt, fhas_time = None, False
    m = re.match("^" + _DATE_RE, stem)
    if m:
        try:
            y, mo, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if m.group(4) and m.group(5):
                fdt, fhas_time = datetime(y, mo, dd, int(m.group(4)), int(m.group(5)), int(m.group(6) or 0)), True
            else:
                fdt = datetime(y, mo, dd)
        except ValueError:
            fdt = None
    captured = _parse_dt(fm["captured"]) if fm.get("captured") else None
    if fdt is not None:
        if captured and captured.date() != fdt.date():
            return captured, False
        return fdt, fhas_time
    if captured:
        return captured, False
    for k in ("date", "created", "modified"):
        if fm.get(k) and (d := _parse_dt(fm[k])):
            return d, False
    return datetime.fromtimestamp(path.stat().st_mtime), False


def slugify(text: str, max_words: int) -> str:
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", " ", text).strip().lower()
    words = [w for w in text.split(" ") if w][:max_words]
    return re.sub(r"-+", "-", "-".join(words)).strip("-")


def clean_slug_source(text: str) -> str:
    """Strip date/time runs and file-extension tokens from a title used as a slug fallback."""
    text = re.sub(r"\d{2,4}(?:[-.: _]\d{2}){1,5}", " ", text)
    text = re.sub(r"\.(ogg|mp3|m4a|wav|webm|aac|pdf|txt|md|json|vtt|srt|docx?)\b", " ", text, flags=re.IGNORECASE)
    return text


def derive_name(path: Path, fm: dict | None, body: str | None, contract: dict):
    """Return (dt, has_time, slug, kind_from_name, ext, human_title)."""
    naming = contract.get("naming", {})
    raw = apply_repairs(path.name, contract)
    ext = Path(raw).suffix.lower()
    stem = raw[: -len(ext)] if ext else raw

    for sub in naming.get("strip_substrings", []):
        stem = re.sub(re.escape(sub), " ", stem, flags=re.IGNORECASE)

    dt, has_time = extract_datetime(stem, fm, path)

    # remove a leading date/time token from the stem (same pattern used to extract it)
    rest = re.sub(r"^" + _DATE_RE + r"[-_ ]*", "", stem)

    # a leading medium token becomes `kind`
    kind_from_name = None
    parts = re.split(r"[-_ ]+", rest, maxsplit=1)
    if parts and parts[0].lower() in naming.get("medium_tokens", {}):
        kind_from_name = naming["medium_tokens"][parts[0].lower()]
        rest = parts[1] if len(parts) > 1 else ""

    human_title = re.sub(r"\s+", " ", rest).strip(" -_—·|")
    slug = slugify(rest, naming.get("slug_max_words", 12))
    if not slug:
        fallback = (fm or {}).get("title") or first_heading(body)
        if fallback:
            cleaned = re.sub(r"\s+", " ", clean_slug_source(str(fallback))).strip(" -_—·|:")
            human_title = cleaned or human_title
            slug = slugify(clean_slug_source(str(fallback)), naming.get("slug_max_words", 12))
    return dt, has_time, slug, kind_from_name, ext, human_title


# ─────────────────────────────── classification ────────────────────────────────


def _rule_matches(rule: dict, path: Path, fm: dict | None, meta: dict) -> bool:
    hit = False
    if "name_regex" in rule:
        if not re.search(rule["name_regex"], path.name):
            return False
        hit = True
    if "ext" in rule:
        if path.suffix.lower() not in [e.lower() for e in rule["ext"]]:
            return False
        hit = True
    if "has_frontmatter_key" in rule:
        keys = rule["has_frontmatter_key"]
        keys = [keys] if isinstance(keys, str) else keys
        if not fm or not any(k in fm for k in keys):
            return False
        hit = True
    if "meta_json_true" in rule:
        if meta.get(rule["meta_json_true"]) is not True:
            return False
        hit = True
    if "meta_json_key" in rule:
        if rule["meta_json_key"] not in meta:
            return False
        hit = True
    if "meta_json_min" in rule:
        for k, minv in rule["meta_json_min"].items():
            if not isinstance(meta.get(k), (int, float)) or meta.get(k, 0) < minv:
                return False
        hit = True
    return hit


def classify(path: Path, fm: dict | None, meta: dict, contract: dict):
    """Return (category, kind_override_or_None, confidence).

    Exactly one matching category -> route it (medium confidence). Zero or MORE THAN ONE
    (keyword collision, e.g. a workshop PDF that merely mentions "transcript") -> park in
    the review queue (ingest folder, low confidence) for the agent/human to route.
    """
    matches = []  # (category, kind)
    for category, spec in contract.get("categories", {}).items():
        for rule in spec.get("rules", []):
            if _rule_matches(rule, path, fm, meta):
                matches.append((category, rule.get("kind")))
                break
    review = contract.get("review", {})
    if len({c for c, _ in matches}) == 1:
        return matches[0][0], matches[0][1], "medium"
    return review.get("category", "client_dropbox"), None, review.get("confidence", "low")


# ─────────────────────────────── secrets ───────────────────────────────────────


def secret_reason(path: Path, contract: dict):
    sec = contract.get("secrets", {})
    if sec.get("name_regex") and re.search(sec["name_regex"], path.name):
        return f"filename matches secret pattern"
    if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".zip", ".mp3", ".ogg", ".m4a", ".wav"}:
        return None
    try:
        data = path.read_text(encoding="utf-8")[: sec.get("content_scan_max_bytes", 262144)]
    except (UnicodeDecodeError, OSError):
        return None
    for pat in sec.get("content_regex", []):
        if re.search(pat, data):
            return "content matches secret pattern"
    return None


# ─────────────────────────────── frontmatter build ─────────────────────────────


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def build_frontmatter(path, fm, body, category, kind, dt, contract, *, bump_updated: bool, title_hint=None):
    fspec = contract.get("frontmatter", {})
    out = dict(fm or {})

    for old, canon in fspec.get("aliases", {}).items():
        if old in out and canon not in out:
            out[canon] = out.pop(old)
        else:
            out.pop(old, None)

    out["category"] = category
    out["kind"] = kind
    if not out.get("title"):
        out["title"] = (first_heading(body) or title_hint or path.stem.replace("-", " ").replace("_", " ").strip().title())
    out.setdefault("source", path.name)
    out["captured"] = dt.date().isoformat()
    if bump_updated:
        out["updated"] = now_iso()  # intake/touch => pop to top
    elif not out.get("updated"):
        # migration of an undated file: inherit its real mtime as the freshness signal
        out["updated"] = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
    for k, v in fspec.get("defaults", {}).items():
        out.setdefault(k, v)

    for k in fspec.get("lowercase_value_keys", []):
        if isinstance(out.get(k), str):
            out[k] = out[k].lower()
    # PyYAML auto-parses ISO timestamps into date/datetime objects; re-emit as canonical strings
    for k in fspec.get("datetime_keys", []):
        v = out.get(k)
        if isinstance(v, datetime):
            out[k] = v.isoformat(timespec="seconds")
        elif isinstance(v, date):
            out[k] = datetime(v.year, v.month, v.day).astimezone().isoformat(timespec="seconds")
    for k in fspec.get("date_only_keys", []):
        v = out.get(k)
        if isinstance(v, datetime):
            out[k] = v.date().isoformat()
        elif isinstance(v, date):
            out[k] = v.isoformat()
    # Catch-all: any OTHER frontmatter key PyYAML auto-parsed into a date/datetime
    # (arbitrary fields not declared in datetime_keys/date_only_keys, e.g.
    # `interview_date:`, `start:`) must be canonicalized to a string here — otherwise
    # it stays a date object and blows up every json.dumps boundary (CLI plan/apply/
    # triage, HTTP serve, bloodbank emit) with "Object of type date is not JSON
    # serializable". datetime is a subclass of date, so test datetime first.
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.isoformat(timespec="seconds")
        elif isinstance(v, date):
            out[k] = v.isoformat()
    return out


# ─────────────────────────────── planning ──────────────────────────────────────


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def unique_destination(dest_dir: Path, base: str, ext: str, dt, has_time, contract, src: Path | None = None) -> str:
    src_resolved = src.resolve() if src else None

    def taken(name: str) -> bool:
        p = dest_dir / name
        # the source file's own name is NOT a collision (keeps plan/apply idempotent)
        return p.exists() and (src_resolved is None or p.resolve() != src_resolved)

    cand = f"{base}{ext}"
    if not taken(cand):
        return cand
    tstamp = dt.strftime(contract["naming"]["datetime_prefix"]) if has_time else dt.strftime("%Y-%m-%d") + "-" + dt.strftime("%H%M")
    base2 = re.sub(r"^\d{4}-\d{2}-\d{2}", tstamp, base, count=1)
    cand = f"{base2}{ext}"
    n = 2
    while taken(cand):
        cand = f"{base2}-{n}{ext}"
        n += 1
    return cand


def make_plan(path: Path, client_root: Path, contract: dict) -> dict:
    rel_src = str(path.relative_to(client_root)) if path.is_absolute() else str(path)
    file_hash = content_hash(path)
    reason = secret_reason(path, contract)
    if reason:
        sec = contract["secrets"]
        return {
            "source": rel_src,
            "action": "quarantine",
            "category": None,
            "destination": sec["quarantine_dir"],
            "normalized_name": path.name,
            "kind": "secret",
            "confidence": "high",
            "pipeline-status": sec.get("pipeline-status", "blocked"),
            "file_hash_sha256": file_hash,
            "reason": reason,
            "frontmatter": None,
        }

    fm, body = read_frontmatter(path)
    meta = read_meta_sidecar(path, contract.get("sidecar_suffixes", []))
    category, kind_override, confidence = classify(path, fm, meta, contract)
    dt, has_time, slug, kind_from_name, ext, human_title = derive_name(path, fm, body, contract)

    spec = contract["categories"].get(category, {})
    kind = kind_override or kind_from_name or spec.get("ingest_default_kind") or spec.get("default_kind") or "note"
    if not slug:
        slug = kind

    date_str = dt.strftime(contract["naming"]["datetime_prefix"]) if (has_time and category == "client_dropbox") else dt.strftime(contract["naming"]["date_prefix"])
    base = f"{date_str}-{slug}"
    dest_dir = client_root / category
    normalized = unique_destination(dest_dir, base, ext, dt, has_time, contract, src=path)

    new_fm = build_frontmatter(path, fm, body, category, kind, dt, contract, bump_updated=True, title_hint=human_title) if fm is not None else None
    already_here = path.parent == dest_dir and path.name == normalized
    sidecar = find_sidecar(path, contract.get("sidecar_suffixes", []))
    return {
        "source": rel_src,
        "action": "keep" if already_here else "route",
        "category": category,
        "destination": f"{category}/{normalized}",
        "normalized_name": normalized,
        "kind": kind,
        "title": (new_fm or {}).get("title") or human_title or path.stem,
        "confidence": confidence,
        "pipeline-status": (new_fm or {}).get("pipeline-status", ["new"]) if new_fm else ["new"],
        "sidecar": sidecar.name if sidecar else None,
        "purpose": contract.get("purpose") if confidence == "low" else None,
        "file_hash_sha256": file_hash,
        "updated": (new_fm or {}).get("updated"),
        "frontmatter": new_fm,
    }


# ─────────────────────────────── ledger ────────────────────────────────────────


def ledger_path(client_root: Path, contract: dict) -> Path:
    return client_root / contract.get("state", {}).get("ledger_file", ".curator/ledger.json")


def load_ledger(client_root, contract) -> dict:
    p = ledger_path(client_root, contract)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_ledger(client_root, contract, ledger):
    p = ledger_path(client_root, contract)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def set_mtime(path: Path, updated):
    d = _parse_dt(updated)
    if not d:
        return
    try:
        ts = d.timestamp()
        os.utime(path, (ts, ts))
    except (OSError, OverflowError, ValueError):
        pass


# ─────────────────────────────── apply ─────────────────────────────────────────


def do_apply(path: Path, client_root: Path, contract: dict, *, reconcile: bool = False) -> dict:
    plan = make_plan(path, client_root, contract)
    ledger = load_ledger(client_root, contract)
    chash = content_hash(path)
    # The content-hash short-circuit keeps the intake/event path idempotent (never process the
    # same bytes twice). `triage` sets reconcile=True so a file you MOVED by hand (same bytes,
    # wrong folder) still gets relocated — it only ever calls apply on non-"keep" plans.
    if not reconcile and chash in ledger and ledger[chash].get("status") == "done":
        plan["action"] = "skip"
        plan["note"] = "already in ledger"
        return plan

    if plan["action"] == "quarantine":
        qdir = client_root / plan["destination"]
        qdir.mkdir(parents=True, exist_ok=True)
        target = qdir / path.name
        os.replace(path, target)
        sc = find_sidecar(path, contract.get("sidecar_suffixes", []))
        if sc:
            os.replace(sc, qdir / sc.name)
        ledger[chash] = {"path": str(target.relative_to(client_root)), "status": "blocked", "kind": "secret", "updated": now_iso()}
        save_ledger(client_root, contract, ledger)
        return plan

    dest_dir = client_root / plan["category"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / plan["normalized_name"]

    fm, body = read_frontmatter(path)
    updated_iso = now_iso()
    if fm is not None and plan["frontmatter"] is not None:
        plan["frontmatter"]["updated"] = updated_iso
        order = contract["frontmatter"]["order"]
        dest.write_text(dump_frontmatter(plan["frontmatter"], order) + "\n" + (body or "").lstrip("\n"), encoding="utf-8")
        if dest != path:
            path.unlink()
    else:
        os.replace(path, dest)

    sc = find_sidecar(path, contract.get("sidecar_suffixes", []))
    if sc:
        for suf in contract.get("sidecar_suffixes", []):
            if sc.name.endswith(suf):
                os.replace(sc, dest_dir / (dest.stem + suf))
                break

    set_mtime(dest, updated_iso)
    ledger[chash] = {"path": str(dest.relative_to(client_root)), "status": "done", "category": plan["category"],
                     "kind": plan["kind"], "title": (plan["frontmatter"] or {}).get("title") or plan.get("title") or dest.stem,
                     "updated": updated_iso, "captured": (plan["frontmatter"] or {}).get("captured")}
    save_ledger(client_root, contract, ledger)
    do_reindex(client_root, contract)
    return plan


# ─────────────────────────────── reindex ───────────────────────────────────────


def iter_content_files(client_root: Path, contract: dict):
    rec = contract.get("recency", {})
    gen = set(contract.get("generated_files", []))
    for d in rec.get("index_dirs", []):
        base = client_root / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            if is_sidecar(p, contract.get("sidecar_suffixes", [])) or p.name in gen:
                continue
            if any(part in contract.get("ignore_dirs", []) or (contract.get("ignore_hidden") and part.startswith(".")) for part in p.relative_to(client_root).parts):
                continue
            yield p
    for f in rec.get("index_root_files", []):
        p = client_root / f
        if p.is_file():
            yield p


def file_record(path: Path, client_root: Path, contract: dict, ledger: dict):
    fm, body = read_frontmatter(path)
    rel = str(path.relative_to(client_root))
    if fm:
        updated = fm.get("updated") or fm.get("modified")
        title = fm.get("title") or first_heading(body) or path.stem
        category = fm.get("category") or path.parent.name
        kind = fm.get("kind") or ""
    else:
        led = next((v for v in ledger.values() if v.get("path") == rel), {})
        updated = led.get("updated")
        title = led.get("title") or path.stem
        category = led.get("category") or path.parent.name
        kind = led.get("kind") or ""
    if not updated:
        updated = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
    return {"rel": rel, "updated": updated, "title": title, "category": category, "kind": kind}


def do_reindex(client_root: Path, contract: dict) -> int:
    rec = contract.get("recency", {})
    ledger = load_ledger(client_root, contract)
    records = [file_record(p, client_root, contract, ledger) for p in iter_content_files(client_root, contract)]

    def sort_key(r):
        # Always return a timezone-AWARE datetime. A single naive value (e.g. a date-only
        # `updated: 2026-07-18`) must never make the sort throw and take the whole pipeline
        # down — coerce naive -> UTC, and sink unparseable values to an aware minimum.
        try:
            dt = datetime.fromisoformat(str(r["updated"]).replace("Z", "+00:00"))
        except (ValueError, AttributeError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    records.sort(key=sort_key, reverse=True)

    if rec.get("restore_mtime"):
        for p in iter_content_files(client_root, contract):
            rel = str(p.relative_to(client_root))
            r = next((x for x in records if x["rel"] == rel), None)
            if r:
                set_mtime(p, r["updated"])

    lines = [
        "---",
        "category: index",
        "kind: context-stack",
        f"updated: {now_iso()}",
        "pipeline-status:",
        "  - processed",
        "---",
        f"# Context stack — {client_root.name}",
        "",
        "Cross-medium, newest-first by `updated`. Generated by `folder-curator reindex`; do not hand-edit.",
        "",
        "| Updated | Category | Kind | Title | File |",
        "|---|---|---|---|---|",
    ]
    for r in records:
        disp = r["updated"][:16].replace("T", " ")
        wl = r["rel"].rsplit(".", 1)[0]
        lines.append(f"| {disp} | {r['category']} | {r['kind']} | {r['title']} | [[{wl}]] |")
    (client_root / rec.get("index_file", "_context-stack.md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)


# ─────────────────────────────── normalize ─────────────────────────────────────


def do_normalize(client_root: Path, contract: dict, apply_changes: bool):
    changes = []
    ledger = load_ledger(client_root, contract)
    order = contract["frontmatter"]["order"]
    for category in contract.get("recency", {}).get("index_dirs", []):
        base = client_root / category
        if not base.is_dir():
            continue
        for path in sorted(base.iterdir()):
            if not path.is_file() or is_sidecar(path, contract.get("sidecar_suffixes", [])):
                continue
            if path.name in contract.get("generated_files", []):
                continue
            reason = secret_reason(path, contract)
            if reason:
                changes.append({"file": str(path.relative_to(client_root)), "action": "quarantine", "reason": reason})
                if apply_changes:
                    do_apply(path, client_root, contract)
                continue
            fm, body = read_frontmatter(path)
            dt, has_time, slug, kind_from_name, ext, human_title = derive_name(path, fm, body, contract)
            cspec = contract["categories"].get(category, {})
            kind = kind_from_name or (fm or {}).get("kind") or cspec.get("ingest_default_kind") or cspec.get("default_kind") or "note"
            if not slug:
                slug = kind
            date_str = dt.strftime(contract["naming"]["datetime_prefix"]) if (has_time and category == "client_dropbox") else dt.strftime(contract["naming"]["date_prefix"])
            stem_base = f"{date_str}-{slug}"
            new_name = f"{stem_base}{ext}"
            if new_name != path.name and (base / new_name).exists():
                new_name = unique_destination(base, stem_base, ext, dt, has_time, contract, src=path)
            new_fm = build_frontmatter(path, fm, body, category, kind, dt, contract, bump_updated=False, title_hint=human_title) if fm is not None else None
            changes.append({
                "file": str(path.relative_to(client_root)),
                "action": "rename+enrich" if new_name != path.name else "enrich",
                "new_name": new_name,
                "kind": kind,
                "frontmatter_keys": sorted(new_fm.keys()) if new_fm else None,
            })
            if not apply_changes:
                continue
            dest = base / new_name
            if new_fm is not None:
                dest.write_text(dump_frontmatter(new_fm, order) + "\n" + (body or "").lstrip("\n"), encoding="utf-8")
                if dest != path:
                    path.unlink()
            elif dest != path:
                os.replace(path, dest)
            sc = find_sidecar(path, contract.get("sidecar_suffixes", []))
            if sc:
                for suf in contract.get("sidecar_suffixes", []):
                    if sc.name.endswith(suf):
                        os.replace(sc, base / (dest.stem + suf))
                        break
            updated_val = (new_fm or {}).get("updated") or datetime.fromtimestamp(dest.stat().st_mtime).astimezone().isoformat(timespec="seconds")
            set_mtime(dest, updated_val)
            ledger[content_hash(dest)] = {
                "path": str(dest.relative_to(client_root)), "status": "done", "category": category,
                "kind": kind, "title": (new_fm or {}).get("title") or human_title or dest.stem,
                "updated": updated_val, "captured": (new_fm or {}).get("captured"),
            }
    if apply_changes:
        save_ledger(client_root, contract, ledger)
        do_reindex(client_root, contract)
    return changes


# ─────────────────────────────── serve (HTTP) ──────────────────────────────────


def do_serve(host: str, port: int) -> None:
    """Expose the engine over HTTP so the n8n custom node calls it in-process
    (POST /plan, POST /apply with {"file","client_root"}; GET /health). Same engine as
    the CLI — no reimplementation, no drift."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self._send(200, {"status": "ok"}) if self.path == "/health" else self._send(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                req = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "invalid JSON body"})
            f = req.get("file") or req.get("file_path")
            if not f:
                return self._send(400, {"error": "'file' is required"})
            root = Path(req.get("client_root") or req.get("curated_dir") or ".").resolve()
            path = Path(f).resolve()
            try:
                contract = load_contract(root)
                if self.path == "/plan":
                    self._send(200, make_plan(path, root, contract))
                elif self.path == "/apply":
                    self._send(200, do_apply(path, root, contract))
                else:
                    self._send(404, {"error": "not found"})
            except Exception as exc:  # surface as JSON to the caller
                self._send(500, {"error": f"{type(exc).__name__}: {exc}"})

        def log_message(self, *args):
            pass

    srv = ThreadingHTTPServer((host, port), Handler)
    print(f"folder-curator serve: http://{host}:{port}  (POST /plan, POST /apply, GET /health)", flush=True)
    srv.serve_forever()


# ─────────────────────────────── export (client view) ──────────────────────────


def do_export(client_root: Path, contract: dict, audience: str, to: Path) -> int:
    """Copy content files whose frontmatter `audience` is `audience` or `shared` into `to`,
    preserving category structure (content-only). Files with no `audience` stay internal —
    this is what keeps profile.md and internal synthesis out of a client-facing view."""
    import shutil

    include = {audience, "shared"}
    n = 0
    for p in iter_content_files(client_root, contract):
        fm, _ = read_frontmatter(p)
        if (fm or {}).get("audience") in include:
            dest = to / p.relative_to(client_root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            sc = find_sidecar(p, contract.get("sidecar_suffixes", []))
            if sc:
                shutil.copy2(sc, dest.parent / sc.name)
            n += 1
    return n


# ─────────────────────────── transforms & triage ───────────────────────────────
# `triage` is the recursive reconcile driver: walk the tree, and for every file that
# isn't already correctly filed (make_plan action != "keep"), route/rename/enrich it —
# fixing anything you dropped in the wrong folder by hand. Correctly-filed files are
# skipped whether or not you've edited them ("ignore edits"). PDFs additionally run the
# pdf_to_markdown transform, whose convert+archive+delete lives once and is shared with
# the n8n subworkflow (safety invariant: back up + verify BEFORE any local delete).


def _bin(name: str) -> str:
    """Resolve a host CLI, falling back to ~/.local/bin (minimal-PATH callers)."""
    return shutil.which(name) or str(Path.home() / ".local" / "bin" / name)


def emit_event(event_type: str, data: dict) -> bool:
    """Fire a Bloodbank event via bb-emit (NATS-direct). Best-effort; never raises."""
    try:
        r = subprocess.run([_bin("bb-emit"), "--type", event_type, "--source", "folder-curator"],
                           input=json.dumps(data, default=str), text=True, capture_output=True, timeout=20)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return False


def s3_archive(src: Path, dest_spec: str, verify: bool) -> bool:
    """`mc cp` src to <alias/bucket/prefix>/<name>, then confirm with `mc stat`.
    Returns True ONLY on a verified REMOTE upload — the gate for deleting a local original.

    Guards mc's dangerous footgun: an UNKNOWN alias is silently treated as a local path, so a
    misconfigured dest would `cp` locally and `stat` would "verify" that local file — greenlighting
    a delete with no real backup. We therefore require the first path segment to be a configured
    mc alias before trusting any cp/stat."""
    mc = _bin("mc")
    alias = dest_spec.split("/", 1)[0]
    try:
        a = subprocess.run([mc, "alias", "ls", alias], capture_output=True, text=True, timeout=30)
        if a.returncode != 0:
            return False  # not a real remote — refuse (never fall back to a local copy)
        key = f"{dest_spec.rstrip('/')}/{src.name}"
        r = subprocess.run([mc, "cp", "--quiet", str(src), key], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return False
        if verify:
            v = subprocess.run([mc, "stat", key], capture_output=True, text=True, timeout=60)
            return v.returncode == 0
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def convert_pdf(path: Path) -> str | None:
    """Convert a PDF to markdown via the pdf2md primitive. None on failure."""
    try:
        r = subprocess.run([_bin("pdf2md"), str(path)], capture_output=True, text=True, timeout=600)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _git_tracked_files(root: Path):
    """Files git would consider: tracked + untracked, MINUS .gitignore. None if not a git repo.
    This is what keeps triage out of generated trees (runtime/, .curator/, node_modules/, …)
    without having to enumerate them — the repo's own .gitignore is the source of truth."""
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        return [root / p for p in r.stdout.split("\0") if p]
    except (OSError, subprocess.SubprocessError):
        return None


def iter_triage_files(client_root: Path, contract: dict):
    """Yield candidate files under client_root. In a git repo, start from what git tracks
    (honoring .gitignore), then prune ignored/hidden dirs, generated files, sidecars, and
    protected front-door files (profile.md, AGENTS.md, …). Falls back to os.walk otherwise."""
    tconf = contract.get("triage", {})
    ignore_dirs = set(contract.get("ignore_dirs", [])) | set(tconf.get("skip_dirs", []))
    ignore_hidden = contract.get("ignore_hidden", True)
    protect = set(tconf.get("protect_files", []))
    generated = set(contract.get("generated_files", []))
    sidecars = contract.get("sidecar_suffixes", [])

    def keep(p: Path) -> bool:
        rel = p.relative_to(client_root)
        if any(seg in ignore_dirs for seg in rel.parts):
            return False
        if ignore_hidden and any(seg.startswith(".") for seg in rel.parts):
            return False
        if p.name in protect or p.name in generated or is_sidecar(p, sidecars):
            return False
        return p.is_file()

    tracked = _git_tracked_files(client_root)
    if tracked is not None:
        for p in sorted(tracked):
            if keep(p):
                yield p
        return
    for dirpath, dirnames, filenames in os.walk(client_root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not (ignore_hidden and d.startswith("."))]
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            if keep(p):
                yield p


def transform_pdf(path: Path, client_root: Path, contract: dict, tconf: dict, via: str, apply: bool) -> dict:
    """Handle a PDF per the pdf_to_markdown contract. `via=event` delegates to the n8n
    subworkflow (emit curator.file.received); `via=inline` converts+archives+deletes here."""
    rel = str(path.relative_to(client_root))
    if via == "event":
        entry = {"file": rel, "action": "pdf->md (delegate to n8n)", "status": "planned"}
        if apply:
            ok = emit_event("bloodbank.v1.curator.file.received", {
                "file": str(path.resolve()), "client_root": str(client_root),
                "content_type": "application/pdf", "transform": "pdf_to_markdown"})
            entry["status"] = "emitted" if ok else "emit-failed"
        return entry

    # inline: convert -> archive+verify -> route md -> delete original (strict order)
    backup = tconf.get("backup", {})
    dest_spec = backup.get("dest")
    verify = backup.get("verify", True)
    delete_after = tconf.get("delete_original_after", True)
    entry = {"file": rel, "action": "pdf->md (inline)",
             "archive_to": f"{dest_spec}/{path.name}" if dest_spec else None,
             "delete_local": delete_after, "status": "planned"}
    if not apply:
        return entry
    md = convert_pdf(path)
    if md is None:
        entry["status"] = "failed"; entry["error"] = "conversion failed"
        emit_event("bloodbank.v1.curator.file.failed", {"file": rel, "stage": "convert"})
        return entry
    if not dest_spec or not s3_archive(path, dest_spec, verify):
        entry["status"] = "failed"; entry["error"] = "s3 archive/verify failed — original kept"
        emit_event("bloodbank.v1.curator.file.failed", {"file": rel, "stage": "archive"})
        return entry
    md_path = path.with_suffix(".md")
    if md_path.exists():
        md_path = path.with_name(path.stem + "-converted.md")
    md_path.write_text(md, encoding="utf-8")
    plan = do_apply(md_path, client_root, contract, reconcile=True)
    if delete_after:
        path.unlink()
    entry.update(status="done", markdown=plan.get("destination"), deleted_local=delete_after)
    emit_event("bloodbank.v1.curator.file.routed", {
        "file": rel, "destination": plan.get("destination"), "kind": plan.get("kind"),
        "transformed_from": "pdf", "archived": f"{dest_spec}/{path.name}"})
    return entry


def do_triage(client_root: Path, contract: dict, apply: bool, via_override: str | None = None) -> dict:
    tconf = contract.get("triage", {})
    pdf_conf = contract.get("transforms", {}).get("pdf_to_markdown", {})
    pdf_enabled = bool(pdf_conf.get("enabled", False))
    via = via_override or pdf_conf.get("via", "event")
    results = []
    touched = False
    for path in iter_triage_files(client_root, contract):
        if path.suffix.lower() == ".pdf" and pdf_enabled:
            results.append(transform_pdf(path, client_root, contract, pdf_conf, via, apply))
            touched = touched or apply
            continue
        plan = make_plan(path, client_root, contract)
        act = plan["action"]
        if act == "keep":
            continue  # already correctly filed — leave it (ignores content edits)
        # Secrets always act (high confidence, non-negotiable guardrail).
        if act == "quarantine":
            results.append({"file": plan["source"], "action": "quarantine",
                            "destination": plan.get("destination"), "reason": plan.get("reason")})
            if apply:
                do_apply(path, client_root, contract, reconcile=True)
                touched = True
            continue
        # act == "route": relocate/rename/enrich ONLY on a confident match. A low-confidence
        # plan means no rule matched — reconcile must NOT yank a file you placed deliberately
        # into the review queue. Flag it and leave it exactly where it is.
        if plan.get("confidence") == "low":
            results.append({"file": plan["source"], "action": "review (left in place)",
                            "would_have_suggested": plan.get("destination"), "confidence": "low"})
            continue
        results.append({"file": plan["source"], "action": "route",
                        "destination": plan.get("destination"), "category": plan.get("category"),
                        "confidence": plan.get("confidence")})
        if apply:
            do_apply(path, client_root, contract, reconcile=True)
            touched = True
    if apply and touched:
        do_reindex(client_root, contract)
    return {"mode": "apply" if apply else "dry-run",
            "transform_via": via if pdf_enabled else None,
            "count": len(results), "changes": results}


# ─────────────────────────────── cli ───────────────────────────────────────────


def resolve_root(args) -> Path:
    return Path(args.client_root).resolve() if args.client_root else Path.cwd()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="folder-curator", description=__doc__)
    ap.add_argument("--client-root", help="client repo root (default: cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="print JSON intake plan (no writes)")
    p.add_argument("file")
    a = sub.add_parser("apply", help="execute the plan (move+rename+enrich)")
    a.add_argument("file")
    sub.add_parser("reindex", help="regenerate _context-stack.md + restore mtimes")
    n = sub.add_parser("normalize", help="migrate existing files to canonical name+frontmatter")
    n.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    tr = sub.add_parser("triage", help="recursively reconcile the tree: route misfiles, rename, enrich, run transforms")
    tr.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    tr.add_argument("--via", choices=["event", "inline"], help="override the PDF transform mode for this run")
    s = sub.add_parser("serve", help="run the HTTP engine service (for the n8n custom node)")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8787)
    e = sub.add_parser("export", help="copy client-facing files (audience client/shared) to a dir")
    e.add_argument("--audience", default="client")
    e.add_argument("--to", required=True)

    args = ap.parse_args(argv)
    if args.cmd == "serve":
        return do_serve(args.host, args.port)
    root = resolve_root(args)
    contract = load_contract(root)

    if args.cmd == "plan":
        print(json.dumps(make_plan(Path(args.file).resolve(), root, contract), indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "apply":
        print(json.dumps(do_apply(Path(args.file).resolve(), root, contract), indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "reindex":
        n = do_reindex(root, contract)
        print(f"reindexed {n} files -> {contract['recency']['index_file']}")
    elif args.cmd == "normalize":
        changes = do_normalize(root, contract, args.apply)
        print(json.dumps({"mode": "apply" if args.apply else "dry-run", "count": len(changes), "changes": changes}, indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "triage":
        print(json.dumps(do_triage(root, contract, args.apply, args.via), indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "export":
        n = do_export(root, contract, args.audience, Path(args.to).resolve())
        print(json.dumps({"exported": n, "audience": args.audience, "to": args.to}))


if __name__ == "__main__":
    main()
