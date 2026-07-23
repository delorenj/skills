#!/usr/bin/env python3
"""domain-drain — the reusable Layer-2 runtime for the domain-triage skill.

A domain is data (a `.curator/taxonomy.yaml` with a `domain:` block + a Hindsight
bank + a TRIAGE.md). This tool is the reusable orchestration around them — it does
the deterministic plumbing that is identical for every domain, so the ONLY per-file
work left is the LLM judgment call (which entity? which sub-type?).

Three verbs:

  discover [--root DIR]
      Find every domain under DIR: a dir whose .curator/taxonomy.yaml carries a
      top-level `domain:` block. Prints name, dir, bank, entity_key, _triage count.

  prep DOMAIN_DIR FILE
      Emit ONE JSON "decision packet" an agent needs to route FILE: the Layer-1
      folder-curator plan, a text preview (pdftotext for PDFs, head for .md), the
      domain registry (entities/contacts/agencies) from the contract, and a short
      recency recall from the domain's Hindsight bank. Replaces the 4-5 manual
      commands per file with one call. No writes.

  apply DOMAIN_DIR FILE --entity NAME [options] [--apply]
      Execute a routing decision: enrich the entity labels into a .md's frontmatter
      (preserving existing keys), then move FILE (+ any sidecar) to the entity's
      destination, creating the folder on first contact. Dry-run unless --apply.
      Optionally --retain a learned fact to the bank. Routing honors the contract's
      routing.mode, entity_key, stage_subtrees, and sub_rule_subtree/recruiters_subtree.

This tool NEVER guesses an entity — the agent passes the decision; the tool executes
it deterministically. It refuses to run folder-curator `apply` at an entity-organized
root (that would reshuffle files by type); it only ever `plan`s for Layer 1.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("domain-drain: needs PyYAML (pip install pyyaml)")

_FM_RE = re.compile(r"^﻿?---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


# ─────────────────────────── contract / discovery ──────────────────────────────

_REGISTRY_KEYS = ("entities", "companies", "clients", "repositories", "repos", "projects")


def registry_entities(dom: dict) -> list:
    """The entity registry, under the canonical `entities:` key or a legacy/natural
    alias (`companies:` for jobhunting, `clients:` for a client domain, etc.)."""
    for k in _REGISTRY_KEYS:
        v = dom.get(k)
        if isinstance(v, list):
            return v
    return []


def load_contract(domain_dir: Path) -> dict:
    p = domain_dir / ".curator" / "taxonomy.yaml"
    if not p.exists():
        sys.exit(f"domain-drain: no contract at {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if "domain" not in data:
        sys.exit(f"domain-drain: {p} has no `domain:` block (not a triage domain)")
    return data


def discover(root: Path) -> list[dict]:
    out = []
    for tax in sorted(root.rglob(".curator/taxonomy.yaml")):
        try:
            data = yaml.safe_load(tax.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        dom = data.get("domain")
        if not isinstance(dom, dict):
            continue
        ddir = tax.parent.parent
        triage = ddir / "_triage"
        n = len([f for f in triage.iterdir() if f.is_file()]) if triage.is_dir() else 0
        out.append({
            "name": dom.get("name", ddir.name),
            "dir": str(ddir),
            "bank": dom.get("memory_bank", dom.get("name")),
            "entity_key": dom.get("routing", {}).get("entity_key"),
            "triage_pending": n,
        })
    return out


# ─────────────────────────────── frontmatter ───────────────────────────────────

def read_frontmatter(path: Path):
    if path.suffix.lower() not in {".md", ".markdown"}:
        return None, None
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), m.group(2)


def write_frontmatter(path: Path, fm: dict, body: str):
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False).strip()
    path.write_text(f"---\n{dumped}\n---\n\n{body.lstrip(chr(10))}", encoding="utf-8")


# ─────────────────────────────── content preview ───────────────────────────────

def content_preview(path: Path, limit: int = 6000) -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        exe = shutil.which("pdftotext")
        if not exe:
            return "(pdftotext not installed — cannot read PDF text)"
        try:
            r = subprocess.run([exe, "-layout", str(path), "-"], capture_output=True, text=True, timeout=60)
            return r.stdout[:limit] if r.returncode == 0 else f"(pdftotext failed: {r.stderr[:200]})"
        except (OSError, subprocess.SubprocessError) as e:
            return f"(pdftotext error: {e})"
    if suf in {".md", ".markdown", ".txt"}:
        try:
            return path.read_text(encoding="utf-8", errors="replace")[:limit]
        except OSError as e:
            return f"(read error: {e})"
    return f"(binary/{suf or 'no-ext'} — no text preview)"


# ─────────────────────────────── layer 1 (plan) ────────────────────────────────

def folder_curator_plan(domain_dir: Path, file: Path) -> dict:
    exe = shutil.which("folder-curator") or str(Path.home() / ".local" / "bin" / "folder-curator")
    try:
        r = subprocess.run([exe, "--client-root", str(domain_dir), "plan", str(file)],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return {"error": r.stderr.strip()[:400] or "plan failed"}
        return json.loads(r.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        return {"error": f"{type(e).__name__}: {e}"}


def bank_recall(bank: str, query: str) -> str:
    exe = shutil.which("hindsight")
    if not exe or not bank:
        return "(hindsight unavailable)"
    try:
        r = subprocess.run([exe, "memory", "recall", bank, query, "--budget", "low"],
                           capture_output=True, text=True, timeout=30)
        # strip ANSI so the packet is clean for an agent to read
        return re.sub(r"\x1b\[[0-9;]*m", "", r.stdout)[:4000] if r.returncode == 0 else "(recall failed)"
    except (OSError, subprocess.SubprocessError):
        return "(recall timed out)"


# ─────────────────────────────── routing (apply) ───────────────────────────────

def destination_dir(domain_dir: Path, dom: dict, entity: str, *, stage: str | None,
                    agency: str | None, subtree: str | None) -> Path:
    routing = dom.get("routing", {})
    if subtree:  # explicit override
        return domain_dir / subtree.replace("<Entity>", entity).replace("<Client>", entity).replace("<Company>", entity).replace("<Agency>", agency or entity)
    if agency:  # sub-typed entity (e.g. external recruiter) -> sub_rule_subtree
        sub = dom.get("recruiters_subtree") or routing.get("sub_rule_subtree") or "Recruiters/<Agency>/"
        return domain_dir / sub.replace("<Agency>", agency)
    # stage-aware (e.g. automaticai Clients/ vs Prospects/)
    stage_map = routing.get("stage_subtrees") or {}
    if stage and stage in stage_map:
        return domain_dir / stage_map[stage].replace("<Client>", entity).replace("<Entity>", entity).replace("<Company>", entity)
    # look the entity up in the registry for an explicit folder (folder may != name)
    for e in registry_entities(dom):
        if str(e.get("name", "")).lower() == entity.lower() and e.get("folder"):
            return domain_dir / e["folder"]
        for alias in e.get("aliases", []) or []:
            if str(alias).lower() == entity.lower() and e.get("folder"):
                return domain_dir / e["folder"]
    return domain_dir / entity  # default: <Entity>/ at the root


def apply_decision(domain_dir: Path, file: Path, dom: dict, args) -> dict:
    entity_key = args.entity_key or dom.get("routing", {}).get("entity_key", "entity")
    dest_dir = destination_dir(domain_dir, dom, args.entity, stage=args.stage,
                               agency=args.agency, subtree=args.subtree)
    dest = dest_dir / file.name
    plan = {
        "file": str(file), "entity_key": entity_key, "entity": args.entity,
        "destination": str(dest), "apply": bool(args.apply),
        "frontmatter_changes": {}, "moved": False, "retained": False,
    }

    # 1. enrich frontmatter (markdown only; preserve existing keys)
    if file.suffix.lower() in {".md", ".markdown"}:
        fm, body = read_frontmatter(file)
        fm = dict(fm or {})
        changes = {entity_key: args.entity}
        if args.subtype:
            changes["contact-type"] = args.subtype
        if args.stage:
            changes["engagement-stage"] = args.stage
        if args.confidence:
            changes["confidence"] = args.confidence
        if args.reason:
            changes["route-reason"] = args.reason
        changes["pipeline-status"] = ["processed"]
        fm.update(changes)
        plan["frontmatter_changes"] = changes
        if args.apply:
            write_frontmatter(file, fm, body or "")

    # 2. move (+ sidecar)
    if args.apply:
        dest_dir.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.resolve() != file.resolve():
            plan["error"] = f"destination exists: {dest}"
            return plan
        shutil.move(str(file), str(dest))
        for suf in (".meta.json", ".sha256"):
            sc = file.with_name(file.stem + suf)
            if sc.exists():
                shutil.move(str(sc), str(dest_dir / sc.name))
        plan["moved"] = True

    # 3. learn
    if args.retain and args.apply:
        bank = dom.get("memory_bank") or dom.get("name")
        exe = shutil.which("hindsight")
        if exe and bank:
            try:
                subprocess.run([exe, "memory", "retain", bank, args.retain, "--context", "conventions"],
                               capture_output=True, text=True, timeout=45)
                plan["retained"] = True
            except (OSError, subprocess.SubprocessError):
                pass
    return plan


# ─────────────────────────────────── cli ───────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(prog="domain-drain", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="find domains under a root")
    d.add_argument("--root", default=".")

    p = sub.add_parser("prep", help="emit a decision packet for FILE (no writes)")
    p.add_argument("domain_dir")
    p.add_argument("file")

    a = sub.add_parser("apply", help="execute a routing decision (dry-run unless --apply)")
    a.add_argument("domain_dir")
    a.add_argument("file")
    a.add_argument("--entity", required=True, help="the resolved entity (company/client/repo)")
    a.add_argument("--entity-key", help="override routing.entity_key")
    a.add_argument("--stage", help="stage_subtrees key, e.g. active|prospect")
    a.add_argument("--agency", help="route under the sub-rule subtree (external recruiter agency)")
    a.add_argument("--subtree", help="explicit destination subtree override")
    a.add_argument("--subtype", help="contact-type sub-label")
    a.add_argument("--confidence", help="low|medium|high")
    a.add_argument("--reason", help="route-reason to record")
    a.add_argument("--retain", help="a fact to retain to the domain bank")
    a.add_argument("--apply", action="store_true", help="actually write/move (default: dry-run)")

    args = ap.parse_args(argv)

    if args.cmd == "discover":
        print(json.dumps(discover(Path(args.root).resolve()), indent=2))
        return
    domain_dir = Path(args.domain_dir).resolve()
    data = load_contract(domain_dir)
    dom = data["domain"]
    file = Path(args.file).resolve()

    if args.cmd == "prep":
        one_line = f"{file.name}: {content_preview(file, 400)}".replace("\n", " ")[:300]
        packet = {
            "domain": dom.get("name"),
            "domain_dir": str(domain_dir),
            "entity_key": dom.get("routing", {}).get("entity_key"),
            "file": str(file),
            "layer1_plan": folder_curator_plan(domain_dir, file),
            "registry": {
                "entities": registry_entities(dom),
                "contacts": dom.get("contacts", []),
                "recruiter_agencies": dom.get("recruiter_agencies", []),
                "heuristics": dom.get("heuristics", []),
            },
            "content_preview": content_preview(file),
            "bank_recall": bank_recall(dom.get("memory_bank") or dom.get("name"), one_line),
        }
        print(json.dumps(packet, indent=2, ensure_ascii=False, default=str))
        return

    if args.cmd == "apply":
        print(json.dumps(apply_decision(domain_dir, file, dom, args), indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
