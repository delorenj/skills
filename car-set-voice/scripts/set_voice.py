#!/usr/bin/env python3
"""car-set-voice: set a tile's car reply voice for the Holocene car desk (HOLOC-23).

    set_voice.py [--json] --agent <agent id> --voice <name | display name | 'walken two' | default> [--by car|cli|skill]
    set_voice.py [--json] --agent <agent id> --clear
    set_voice.py [--json] --list

The voice is validated against vox's list (`voxxy -q voice list --json`; `GET $MEMO_VOX_URL/voices` when MEMO_VOX_URL is
set), resolved to its name, and written through the watcher's own verb (`memo_trace.py voice <agent> <name> --json`),
which sets tiles.<agent>.voice in the desk's flag file under its lock. Car only: no Telegram/Hermes voice is touched.

stdout: one JSON object. Exit: 0 done, 2 bad arguments, 3 refused (unknown voice), 1 failed. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

MEMO_TRACE = Path(os.environ.get("HOLOCENE_MEMO_TRACE")
                  or Path.home() / "code/33GOD/holocene/services/inbox-watcher/memo_trace.py")
NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
       "8": "eight", "9": "nine"}
DEFAULT_WORDS = {"default", "thedefault", "normal", "usual", "theusual", "standard", "reset", "clear", "none"}


def out(obj: dict, code: int) -> int:
    print(json.dumps(obj))
    return code


def key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def voices() -> list[dict]:
    """vox's voices: GET $MEMO_VOX_URL/voices when that names a vox, else `voxxy -q voice list --json`, else vox.delo.sh."""
    url = os.environ.get("MEMO_VOX_URL")
    tries = ([("http", url)] if url else []) + [("voxxy", None), ("http", "https://vox.delo.sh")]
    for how, u in tries:
        try:
            if how == "voxxy":
                r = subprocess.run(["voxxy", "-q", "voice", "list", "--json"], capture_output=True, text=True, timeout=2.0)
                data = json.loads(r.stdout) if r.returncode == 0 else None
            else:
                with urllib.request.urlopen(f"{u.rstrip('/')}/voices", timeout=2.0) as resp:
                    data = json.loads(resp.read())
        except (OSError, ValueError, subprocess.TimeoutExpired):
            continue
        rows = [{"name": str(v["name"]), "display_name": str(v.get("display_name") or "")}
                for v in (data or []) if isinstance(v, dict) and v.get("name")]
        if rows:
            return rows
    return []


def resolve(said: str, catalog: list[dict]) -> str | None:
    """The same rule as the watcher's converse.resolve_voice: the name, the name with its digits spoken, the display name
    (shortest name on a tie), a display name's first or last word that no other voice shares."""
    names = sorted({v["name"] for v in catalog}, key=lambda n: (len(n), n))
    disp = {v["name"]: re.sub(r"\s+", " ", (v.get("display_name") or "").lower()).strip() for v in catalog}
    idx: dict[str, str] = {}
    for n in names:
        idx.setdefault(key(n), n)
        idx.setdefault(key(re.sub(r"\d", lambda d: " " + NUM[d.group(0)], n)), n)
    for n in names:
        if disp.get(n):
            idx.setdefault(key(disp[n]), n)
    for pick in (lambda w: w[-1], lambda w: w[0]):
        owners: dict[str, set] = {}
        for n in names:
            w = disp.get(n, "").split()
            if len(w) > 1:
                owners.setdefault(pick(w), set()).add(n)
        for w, o in owners.items():
            if len(o) == 1:
                idx.setdefault(key(w), next(iter(o)))
    return idx.get(key(said))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="accepted for the tool contract; the output is always JSON")
    ap.add_argument("--agent")
    ap.add_argument("--voice")
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--by", default="skill", choices=("car", "cli", "skill"))
    try:
        a = ap.parse_args()
    except SystemExit:
        return out({"ok": False, "error": "bad arguments"}, 2)
    if a.list:
        cat = voices()
        return out({"ok": bool(cat), "voices": cat}, 0 if cat else 1)
    if not a.agent or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", a.agent):
        return out({"ok": False, "error": "--agent <agent id> is required"}, 2)
    if not a.clear and not (a.voice or "").strip():
        return out({"ok": False, "error": "--voice <voice> or --clear is required"}, 2)
    clear = a.clear or key(a.voice) in DEFAULT_WORDS
    name = None
    if not clear:
        cat = voices()
        if not cat:
            return out({"ok": False, "error": "vox's voice list could not be read"}, 1)
        name = resolve(a.voice, cat)
        if name is None:
            return out({"ok": False, "error": f"there's no voice called {a.voice}", "valid": [v["name"] for v in cat]}, 3)
    if not MEMO_TRACE.is_file():
        return out({"ok": False, "error": f"the watcher's verb is missing: {MEMO_TRACE}"}, 1)
    cmd = [sys.executable, "-B", str(MEMO_TRACE), "voice", a.agent, *(["--clear"] if clear else [name]), "--json", "--by", a.by]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as e:
        return out({"ok": False, "error": f"memo_trace.py voice failed: {type(e).__name__}"}, 1)
    try:
        res = json.loads((r.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        return out({"ok": False, "error": f"memo_trace.py voice rc={r.returncode}: {(r.stderr or '').strip()[-160:]}"}, 1)
    if r.returncode != 0 or not res.get("ok"):
        return out({"ok": False, "error": res.get("error") or f"memo_trace.py voice rc={r.returncode}",
                    "valid": res.get("valid")}, 3 if r.returncode == 3 else 1)
    return out({"ok": True, "agent": a.agent, "voice": None if clear else res.get("voice"), "cleared": clear,
                "display_name": res.get("display_name"), "spoken": res.get("spoken"),
                "default_voice": res.get("default_voice")}, 0)


if __name__ == "__main__":
    sys.exit(main())
