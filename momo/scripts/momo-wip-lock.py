#!/usr/bin/env python3
"""momo-wip-lock — shared WIP=1 driver lease so interactive Momo and the Hermes
sentinel never double-drive one board (momo E2/S2.3, the coexistence gate).

Both drivers acquire the SAME advisory lease (a JSON file, conventionally
<runtime>/wip-driver.lock) before a board-driving pass. The lease PERSISTS across
processes — it is deliberately NOT a held flock, because a Momo pass spans many
separate tool-call/bash invocations over minutes. flock is used only to serialize
the check-and-set so two acquirers can't race. A lease is respected while its
heartbeat is fresh (now - heartbeat_at < ttl); a stale lease (holder died without
releasing) can be stolen after it expires.

Owners are free strings by convention: "momo" (interactive) or
"hermes:<agent_id>" (the sentinel). WIP=1 is per BOARD == per runtime, so there
is one lease file per runtime.

Protocol:
  * Driver start:  acquire <lock> <me>   -> exit 0 → drive; exit 1 → HELD, back off.
  * While driving: refresh <lock> <me>   periodically (< ttl) so the lease stays fresh.
  * Driver end:    release <lock> <me>.
  * A holder that crashed leaves a lease that expires after `ttl`; the next driver
    acquires it normally (or `--steal` to take an explicitly stale one immediately).

Commands (exit 0 = you hold it; 1 = someone else holds it fresh; 2 = usage/error):
  acquire <lockfile> <owner> [--ttl S] [--steal]
  refresh <lockfile> <owner>
  release <lockfile> <owner>
  status  <lockfile>                     # always exit 0
"""
from __future__ import annotations
import argparse, fcntl, json, os, socket, sys, tempfile, time


def _read(path: str):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _fresh(lease: dict | None, now: float) -> bool:
    return bool(lease) and (now - lease.get("heartbeat_at", 0)) < lease.get("ttl", 300)


def _write_atomic(path: str, data: dict) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def _guard(lockfile: str):
    """Sibling .flock file held only for the read-modify-write critical section."""
    g = open(lockfile + ".flock", "a")
    fcntl.flock(g, fcntl.LOCK_EX)
    return g


def acquire(lockfile: str, owner: str, ttl: int, steal: bool) -> int:
    now = time.time(); g = _guard(lockfile)
    try:
        cur = _read(lockfile)
        if cur and cur.get("owner") != owner and _fresh(cur, now) and not steal:
            print(f"HELD by {cur['owner']} (fresh, {int(now - cur['heartbeat_at'])}s ago) — back off")
            return 1
        started = cur["started_at"] if (cur and cur.get("owner") == owner and "started_at" in cur) else now
        _write_atomic(lockfile, {
            "owner": owner, "pid": os.getpid(), "host": socket.gethostname(),
            "started_at": started, "heartbeat_at": now, "ttl": ttl,
        })
        print(f"ACQUIRED by {owner}" + (" (stole stale lease)" if (cur and cur.get('owner') != owner) else ""))
        return 0
    finally:
        fcntl.flock(g, fcntl.LOCK_UN); g.close()


def refresh(lockfile: str, owner: str) -> int:
    now = time.time(); g = _guard(lockfile)
    try:
        cur = _read(lockfile)
        if not cur or cur.get("owner") != owner:
            print(f"NOT OWNER (held by {cur.get('owner') if cur else 'nobody'}) — cannot refresh")
            return 1
        cur["heartbeat_at"] = now
        _write_atomic(lockfile, cur); print("REFRESHED"); return 0
    finally:
        fcntl.flock(g, fcntl.LOCK_UN); g.close()


def release(lockfile: str, owner: str) -> int:
    g = _guard(lockfile)
    try:
        cur = _read(lockfile)
        if cur and cur.get("owner") != owner:
            print(f"NOT OWNER (held by {cur['owner']}) — not releasing"); return 1
        try:
            os.remove(lockfile)
        except FileNotFoundError:
            pass
        print("RELEASED"); return 0
    finally:
        fcntl.flock(g, fcntl.LOCK_UN); g.close()


def status(lockfile: str) -> int:
    now = time.time(); cur = _read(lockfile)
    if not cur:
        print("FREE (no lease)"); return 0
    state = "fresh" if _fresh(cur, now) else "STALE"
    print(f"{cur['owner']} — {state} (heartbeat {int(now - cur.get('heartbeat_at', 0))}s ago, "
          f"ttl {cur.get('ttl')}s, pid {cur.get('pid')}@{cur.get('host')})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["acquire", "refresh", "release", "status"])
    ap.add_argument("lockfile")
    ap.add_argument("owner", nargs="?")
    ap.add_argument("--ttl", type=int, default=300, help="freshness window in seconds (default 300)")
    ap.add_argument("--steal", action="store_true", help="take an explicitly stale lease immediately")
    a = ap.parse_args()
    if a.cmd in ("acquire", "refresh", "release") and not a.owner:
        print("owner required", file=sys.stderr); return 2
    if a.cmd == "acquire":
        return acquire(a.lockfile, a.owner, a.ttl, a.steal)
    if a.cmd == "refresh":
        return refresh(a.lockfile, a.owner)
    if a.cmd == "release":
        return release(a.lockfile, a.owner)
    return status(a.lockfile)


if __name__ == "__main__":
    raise SystemExit(main())
