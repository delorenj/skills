#!/usr/bin/env python3
"""car-set-model: set a tile's desk model alias for the Holocene car desk (HOLOC-23).

    set_model.py [--json] --agent <agent id> --model <deepseek-flash | deepseek-pro | free | auto | default | a phrase>
    set_model.py [--json] --agent <agent id> --clear
    set_model.py [--json] --list

The alias is resolved against the shared table (car_desk_aliases.json in the watcher's directory) and written through
the watcher's own verb (`memo_trace.py model <agent> <alias> --json`), which re-checks every route of the alias against
the never-Anthropic rule and sets tiles.<agent>.model in the desk's flag file under its lock. The agent's own Hermes model
is not touched.

stdout: one JSON object. Exit: 0 done, 2 bad arguments, 3 refused, 1 failed. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

MEMO_TRACE = Path(os.environ.get("HOLOCENE_MEMO_TRACE")
                  or Path.home() / "code/33GOD/holocene/services/inbox-watcher/memo_trace.py")
ALIASES = Path(os.environ.get("HOLOCENE_CAR_DESK_ALIASES") or MEMO_TRACE.parent / "car_desk_aliases.json")
DEFAULT_WORDS = {"default", "thedefault", "normal", "usual", "theusual", "standard", "reset", "clear", "none"}
# the never-Anthropic rule, as the watcher applies it (the two router names only on the scoped token: the verb checks that)
FORBIDDEN = re.compile(r"(claude|anthropic|sonnet|opus|haiku|fable|(?:^|/)openrouter/auto)", re.I)
ROUTERS_OK = {"automaticai/auto/fast", "automaticai/free"}


def out(obj: dict, code: int) -> int:
    print(json.dumps(obj))
    return code


def key(text: str) -> str:
    """The watcher's converse._alias_key: no 'model'/'brain' words, no leading article, letters and digits only."""
    t = re.sub(r"[^a-z0-9' ]+", " ", (text or "").lower())
    t = re.sub(r"\b(?:model|models|brain|llm)\b", " ", t).strip()
    t = re.sub(r"^(?:the|a)\s+", "", t)
    return re.sub(r"[^a-z0-9]+", "", t)


def table() -> dict:
    try:
        doc = json.loads(ALIASES.read_text(encoding="utf-8"))
        return doc if isinstance(doc.get("models"), dict) else {}
    except (OSError, ValueError, AttributeError):
        return {}


def resolve(said: str, tab: dict) -> str | None:
    idx: dict[str, str] = {}
    for alias, e in (tab.get("models") or {}).items():
        for p in [alias, e.get("label") or "", e.get("spoken") or "", *(e.get("phrases") or [])]:
            if key(str(p)):
                idx.setdefault(key(str(p)), alias)
    return idx.get(key(said))


def unsafe(entry: dict) -> list[str]:
    bad = []
    for r in entry.get("routes") or []:
        m = str(r.get("model") or "")
        if FORBIDDEN.search(m) or (re.search(r"(?:^|/)auto(?:/|$)", m) and m not in ROUTERS_OK):
            bad.append(m)
        if r.get("key_ref") and not str(r["key_ref"]).startswith("op://"):
            bad.append(f"{r.get('id')}: key_ref is not an op:// reference")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="accepted for the tool contract; the output is always JSON")
    ap.add_argument("--agent")
    ap.add_argument("--model")
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--by", default="skill", choices=("car", "cli", "skill"))
    try:
        a = ap.parse_args()
    except SystemExit:
        return out({"ok": False, "error": "bad arguments"}, 2)
    tab = table()
    if not tab:
        return out({"ok": False, "error": f"the alias table cannot be read: {ALIASES}"}, 1)
    if a.list:
        return out({"ok": True, "version": tab.get("version"),
                    "aliases": {k: {"label": e.get("label"), "routes": [r.get("model") for r in e.get("routes") or []]}
                                for k, e in tab["models"].items()}}, 0)
    if not a.agent or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", a.agent):
        return out({"ok": False, "error": "--agent <agent id> is required"}, 2)
    if not a.clear and not (a.model or "").strip():
        return out({"ok": False, "error": "--model <alias> or --clear is required"}, 2)
    clear = a.clear or key(a.model) in DEFAULT_WORDS
    alias = None
    if not clear:
        alias = resolve(a.model, tab)
        if alias is None:
            return out({"ok": False, "error": f"there's no model called {a.model}",
                        "valid": sorted(tab["models"]) + ["default"]}, 3)
        bad = unsafe(tab["models"][alias])
        if bad:
            return out({"ok": False, "error": f"refused by the never-Anthropic rule: {', '.join(bad)}"}, 3)
    if not MEMO_TRACE.is_file():
        return out({"ok": False, "error": f"the watcher's verb is missing: {MEMO_TRACE}"}, 1)
    cmd = [sys.executable, "-B", str(MEMO_TRACE), "model", a.agent, *(["--clear"] if clear else [alias]), "--json", "--by", a.by]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as e:
        return out({"ok": False, "error": f"memo_trace.py model failed: {type(e).__name__}"}, 1)
    try:
        res = json.loads((r.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        return out({"ok": False, "error": f"memo_trace.py model rc={r.returncode}: {(r.stderr or '').strip()[-160:]}"}, 1)
    if r.returncode != 0 or not res.get("ok"):
        return out({"ok": False, "error": res.get("error") or f"memo_trace.py model rc={r.returncode}"},
                   3 if r.returncode == 3 else 1)
    return out({"ok": True, "agent": a.agent, "model": res.get("model"), "label": res.get("label"),
                "spoken": res.get("spoken"), "cleared": clear, "ladder": res.get("ladder")}, 0)


if __name__ == "__main__":
    sys.exit(main())
