#!/usr/bin/env python3
"""Apply an interval pass's board writes: the agent decides, the driver acts.

The agent writes ONE plan file (a new file each pass, so Hermes' write guard never refuses it)
and runs this once. This script, not the model, takes the board-driver lease, enforces the
comment tag, the allowed verbs and the write cap, skips a comment already posted, releases the
lease no matter what, writes the agent's roadmap and archives the plan. That turns "remember to
release the lease, chain the commands, avoid heredocs, don't repeat yourself" from prompt rules
the model can drop into code it can't.

Plan file (JSON):
  {"writes": [
     {"op": "comment", "ref": "TOLT-12", "text": "..."},
     {"op": "move",    "ref": "TOLT-12", "lane": "Todo", "text": "..."},
     {"op": "release", "ref": "TOLT-12", "text": "...", "lane": "Backlog"},   # lane optional: px
                                                                              # release lands in Todo
     {"op": "close",   "ref": "TOLT-12", "text": "..."},
     {"op": "create",  "title": "...", "labels": ["path:launch"], "priority": "high",
                       "description": "...", "key": "TOLT-LD:slug"}],
   "roadmap": "# full roadmap text (optional; omit on a quiet pass)"}

Usage:
  px-apply.py PLAN --cwd REPO --tag "[em]" --ops comment,move,release,close --max 8 \
      [--lease LOCKFILE --owner OWNER] [--roadmap PATH]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

LOCK = Path.home() / "code/33GOD/momo/skill/scripts/momo-wip-lock.py"
REF = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
LANES = {"Backlog", "Todo", "In Progress"}


def px(cwd: str, *args: str) -> str:
    r = subprocess.run(["px", *args], cwd=cwd, capture_output=True, text=True, timeout=120)
    return ((r.stdout or r.stderr).strip().splitlines() or ["(no output)"])[0] + ("" if r.returncode == 0 else f" [exit {r.returncode}]")


def posted(cwd: str, ref: str) -> set[str]:
    try:
        out = subprocess.run(["px", "task", "get", ref, "--json"], cwd=cwd, capture_output=True, text=True, timeout=60).stdout
        cs = json.loads(out)["ticket"].get("comments") or []
    except Exception:
        return set()
    return {re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c.get("comment_html") or ""))).strip() for c in cs}


def lease(cmd: str, a) -> bool:
    if not a.lease:
        return True
    return subprocess.run([sys.executable, str(LOCK), cmd, a.lease, a.owner], capture_output=True, text=True).returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--ops", required=True)
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--lease")
    ap.add_argument("--owner", default="interval-pass")
    ap.add_argument("--roadmap")
    a = ap.parse_args()

    plan_path = Path(a.plan)
    try:
        plan = json.loads(plan_path.read_text())
    except Exception as e:
        print(f"PLAN UNREADABLE: {e}. Nothing written.")
        return 1
    archive = plan_path.with_suffix(".applied.json")
    plan_path.replace(archive)  # never applied twice, and next pass's write_file sees a new file

    allowed = set(a.ops.split(","))
    writes = plan.get("writes") or []
    if len(writes) > a.max:
        print(f"CAP: {len(writes)} writes planned, applying the first {a.max}")
        writes = writes[: a.max]

    def tagged(t: str) -> str:
        t = (t or "").strip()
        return t if t.startswith(a.tag) else f"{a.tag} {t}"

    if writes and not lease("acquire", a):
        print(f"LEASE HELD by someone else: no board writes this pass ({len(writes)} planned, dropped).")
        writes = []
    try:
        seen: dict[str, set[str]] = {}
        for w in writes:
            op, ref = w.get("op"), w.get("ref", "")
            if op not in allowed:
                print(f"SKIP {op} {ref}: op not allowed for this pass")
                continue
            if op != "create" and not REF.match(ref):
                print(f"SKIP {op} {ref!r}: bad ref")
                continue
            text = tagged(w.get("text", ""))
            if op == "comment":
                if text in seen.setdefault(ref, posted(a.cwd, ref)):
                    print(f"SKIP comment {ref}: already posted")
                    continue
                print(f"comment {ref}: {px(a.cwd, 'comment', ref, '-m', text)}")
            elif op == "move":
                lane = w.get("lane")
                if lane not in LANES:
                    print(f"SKIP move {ref}: lane {lane!r} not in {sorted(LANES)}")
                    continue
                print(f"move {ref}: {px(a.cwd, 'move', ref, lane, '-m', text)}")
            elif op == "release":
                print(f"release {ref}: {px(a.cwd, 'release', ref, '-m', text)}")
                if w.get("lane") in LANES - {"Todo"}:
                    print(f"  then move {ref}: {px(a.cwd, 'move', ref, w['lane'], '-m', tagged('parked'))}")
            elif op == "close":
                print(f"close {ref}: {px(a.cwd, 'close', ref, '-m', text)}")
            elif op == "create":
                args = ["task", "create", w.get("title", "").strip(), "-d", w.get("description", "")]
                if w.get("labels"):
                    args += ["-l", ",".join(w["labels"])]
                if w.get("priority"):
                    args += ["--priority", w["priority"]]
                if w.get("key"):
                    args += ["--idempotency-key", w["key"]]
                print(f"create {w.get('title', '')[:60]!r}: {px(a.cwd, *args)}")
    finally:
        if writes:
            lease("release", a)

    if a.roadmap and (plan.get("roadmap") or "").strip():
        Path(a.roadmap).write_text(plan["roadmap"].rstrip() + "\n")
        print(f"roadmap written: {a.roadmap}")
    print(f"done; plan archived at {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
