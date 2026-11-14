#!/usr/bin/env python3
"""board-lease — shared board-driver lease so an interactive session and a Hermes
agent pass never double-drive one board (formerly momo-wip-lock.py).

It is NOT a WIP limit. It serializes short board selection and transitions
only, so two drivers never write the board in the same instant. It never gates
how many tickets are in progress and must never be used to refuse dispatching a
different ready ticket: a PM runs many workers in parallel, one owner per
ticket. (Formerly momo-wip-lock.py; the CLI and lease file format are unchanged.)
Release this driver lease before waiting on workers.

Both drivers acquire the SAME advisory lease (a JSON file, conventionally
<runtime>/wip-driver.lock) before a board-driving pass. The lease PERSISTS across
processes — it is deliberately NOT a held flock, because a board pass spans many
separate tool-call/bash invocations over minutes. flock is used only to serialize
the check-and-set so two acquirers can't race. A lease is respected while its
heartbeat is fresh (now - heartbeat_at < ttl); a stale lease (holder died without
releasing) can be stolen after it expires.

Owners are free strings by convention: "interactive" (a person-driven session), "claude:<job>" (a
wrapper job) or "hermes:<agent_id>:<pass-or-turn tag>" (a Hermes agent). ONE owner
string per driving pass or turn, unique to it: two passes of the same agent (a
heartbeat pass and a Telegram/Bloodbank turn) are two drivers and must serialize,
so they never share the bare "hermes:<agent_id>". There is one board-driver lease
per runtime.

Reentrancy: acquire is reentrant ONLY for the identical owner string. So a pass
must never invent a fresh owner name while a wrapper already holds the lease for
it: the lease is then HELD by "someone else" (really: yourself) and the pass backs
off for nothing. The rules:
  * A launcher (heartbeat.sh) that acquires the lease FOR the agent hands it the
    exact owner in the prompt (and exports HERMES_BOARD_LEASE_PATH/_OWNER/_TTL for
    its own child scripts; a gateway-run session's terminal never sees them). That
    lease is the agent's: held/refresh/release, and re-acquire after an early
    release, with that exact owner, never under another name. `owner` may be
    omitted on acquire, refresh, release and held; it then defaults to
    $HERMES_BOARD_LEASE_OWNER when that is set.
  * An agent acquiring on its own (no launcher) picks one owner for the turn,
    "hermes:<agent_id>:<turn tag>", writes it out literally and reuses that exact
    string, so its own re-acquire/refresh is reentrant. It never regenerates it.
  * Any other fresh owner (an interactive session, a job, another agent, another pass of your own
    desk) is another driver: back off.
A reentrant acquire keeps the existing ttl unless --ttl is given, so a wrapper's
long pass lease is never shortened by the agent re-asserting it.

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
  held    <lockfile> [owner]             # exit 0 only if <owner> holds it fresh (yours); else 1
  status  <lockfile>                     # always exit 0
"""
from __future__ import annotations
import argparse, fcntl, json, os, socket, sys, tempfile, time


DEFAULT_TTL = 300
OWNER_ENV = "HERMES_BOARD_LEASE_OWNER"


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


def acquire(lockfile: str, owner: str, ttl: int | None, steal: bool) -> int:
    now = time.time(); g = _guard(lockfile)
    try:
        cur = _read(lockfile)
        if cur and cur.get("owner") != owner and _fresh(cur, now) and not steal:
            print(f"HELD by {cur['owner']} (fresh, {int(now - cur['heartbeat_at'])}s ago) — back off")
            return 1
        mine = bool(cur) and cur.get("owner") == owner
        started = cur["started_at"] if (mine and "started_at" in cur) else now
        # Reentrant acquire keeps the lease's own ttl unless one is asked for.
        eff_ttl = ttl if ttl is not None else (cur.get("ttl", DEFAULT_TTL) if mine else DEFAULT_TTL)
        _write_atomic(lockfile, {
            "owner": owner, "pid": os.getpid(), "host": socket.gethostname(),
            "started_at": started, "heartbeat_at": now, "ttl": eff_ttl,
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


def held(lockfile: str, owner: str) -> int:
    """0 = `owner` holds a fresh lease (it is yours: refresh/release it, never
    re-acquire under another name); 1 = free, stale, or held by someone else."""
    now = time.time(); cur = _read(lockfile)
    if cur and cur.get("owner") == owner and _fresh(cur, now):
        print(f"HELD BY YOU ({owner}) — fresh, {int(now - cur['heartbeat_at'])}s ago"); return 0
    if cur and _fresh(cur, now):
        print(f"HELD by {cur['owner']} (fresh) — not you ({owner}); back off"); return 1
    print("NOT HELD (free or stale)"); return 1


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
    ap.add_argument("cmd", choices=["acquire", "refresh", "release", "held", "status"])
    ap.add_argument("lockfile")
    ap.add_argument("owner", nargs="?")
    ap.add_argument("--ttl", type=int, default=None,
                    help=f"freshness window in seconds (default {DEFAULT_TTL}; a reentrant acquire keeps the lease's own)")
    ap.add_argument("--steal", action="store_true", help="take an explicitly stale lease immediately")
    a = ap.parse_args()
    if a.cmd in ("acquire", "refresh", "release", "held") and not a.owner:
        a.owner = os.environ.get(OWNER_ENV) or None
    if a.cmd in ("acquire", "refresh", "release", "held") and not a.owner:
        print(f"owner required (or export {OWNER_ENV})", file=sys.stderr); return 2
    if a.cmd == "acquire":
        return acquire(a.lockfile, a.owner, a.ttl, a.steal)
    if a.cmd == "refresh":
        return refresh(a.lockfile, a.owner)
    if a.cmd == "release":
        return release(a.lockfile, a.owner)
    if a.cmd == "held":
        return held(a.lockfile, a.owner)
    return status(a.lockfile)


if __name__ == "__main__":
    raise SystemExit(main())
