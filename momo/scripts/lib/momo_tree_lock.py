"""momo_tree_lock — advisory lock against background auto-commits (33GPM-8).

Active Momo/Hermes sessions can acquire a per-repo tree lock. Background automation
(commit bots, heartbeat auto-commit scripts) must call `guard` before writing and
back off when the tree is locked. Locks auto-expire if the holder crashes.

Design pattern: Command — acquire/refresh/release/status/guard are discrete
commands on a shared TreeLock receiver.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import socket
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TTL_SECONDS = 300


class TreeLockError(Exception):
    pass


class TreeLockedError(TreeLockError):
    pass


@dataclass
class TreeLockRecord:
    owner: str
    session_id: str = ""
    pid: int = field(default_factory=os.getpid)
    host: str = field(default_factory=socket.gethostname)
    acquired_at: str = field(default_factory=lambda: _now_iso())
    heartbeat_at: str = field(default_factory=lambda: _now_iso())
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    reason: str = ""

    def bump(self) -> None:
        self.heartbeat_at = _now_iso()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_lockfile(root: Path | None = None) -> Path:
    d = root or _repo_root()
    return d / ".momo" / "tree.lock"


def _repo_root(start: str | Path | None = None) -> Path:
    d = Path(start or os.getcwd()).resolve()
    while d != d.parent:
        if (d / ".project.json").is_file():
            return d
        d = d.parent
    raise TreeLockError("no .project.json found; not inside a CommonProject repo")


def _read(path: Path) -> dict[str, Any] | None:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tree-lock-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _is_fresh(record: dict[str, Any], now: float | None = None) -> bool:
    now = now or time.time()
    try:
        hb = datetime.fromisoformat(record.get("heartbeat_at", "1970-01-01T00:00:00+00:00")).timestamp()
    except Exception:
        return False
    ttl = record.get("ttl_seconds", DEFAULT_TTL_SECONDS)
    return (now - hb) < ttl


def acquire(
    owner: str,
    *,
    session_id: str = "",
    reason: str = "",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    steal: bool = False,
    root: Path | None = None,
) -> Path:
    """Acquire the tree lock. Raises TreeLockedError if another owner holds it fresh."""
    path = default_lockfile(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    guard = open(path.with_suffix(path.suffix + ".flock"), "a")
    fcntl.flock(guard, fcntl.LOCK_EX)
    try:
        cur = _read(path)
        if cur and cur.get("owner") != owner and _is_fresh(cur) and not steal:
            raise TreeLockedError(
                f"tree locked by {cur.get('owner')} (pid {cur.get('pid')}@{cur.get('host')}, "
                f"heartbeat {cur.get('heartbeat_at')})"
            )
        rec = TreeLockRecord(
            owner=owner,
            session_id=session_id,
            reason=reason,
            ttl_seconds=ttl_seconds,
        )
        _write_atomic(path, asdict(rec))
        return path
    finally:
        fcntl.flock(guard, fcntl.LOCK_UN)
        guard.close()


def refresh(owner: str, *, root: Path | None = None) -> Path:
    path = default_lockfile(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    guard = open(path.with_suffix(path.suffix + ".flock"), "a")
    fcntl.flock(guard, fcntl.LOCK_EX)
    try:
        cur = _read(path)
        if not cur:
            raise TreeLockError("no active lock to refresh")
        if cur.get("owner") != owner:
            raise TreeLockedError(
                f"tree locked by {cur.get('owner')}; cannot refresh as {owner}"
            )
        cur["heartbeat_at"] = _now_iso()
        _write_atomic(path, cur)
        return path
    finally:
        fcntl.flock(guard, fcntl.LOCK_UN)
        guard.close()


def release(owner: str, *, root: Path | None = None) -> bool:
    path = default_lockfile(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    guard = open(path.with_suffix(path.suffix + ".flock"), "a")
    fcntl.flock(guard, fcntl.LOCK_EX)
    try:
        cur = _read(path)
        if cur and cur.get("owner") != owner:
            return False
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return True
    finally:
        fcntl.flock(guard, fcntl.LOCK_UN)
        guard.close()


def status(*, root: Path | None = None) -> dict[str, Any]:
    path = default_lockfile(root)
    cur = _read(path)
    if not cur:
        return {"locked": False, "owner": "", "fresh": False}
    return {
        "locked": True,
        "owner": cur.get("owner"),
        "fresh": _is_fresh(cur),
        "record": cur,
    }


def guard(*, root: Path | None = None, owner: str | None = None) -> dict[str, Any]:
    """Return status; if a fresh lock is held by someone else, raise TreeLockedError.

    Background auto-commit tools call this before mutating the working tree.
    """
    st = status(root=root)
    if not st["locked"] or not st["fresh"]:
        return st
    if owner and st["owner"] == owner:
        return st
    raise TreeLockedError(
        f"tree locked by {st['owner']} (reason: {st['record'].get('reason', '')})"
    )


def _cmd_acquire(args: argparse.Namespace) -> int:
    try:
        p = acquire(
            args.owner,
            session_id=args.session_id,
            reason=args.reason,
            ttl_seconds=args.ttl,
            steal=args.steal,
        )
        print(f"ACQUIRED {p}")
        return 0
    except TreeLockedError as exc:
        print(f"LOCKED: {exc}", file=sys.stderr)
        return 1


def _cmd_refresh(args: argparse.Namespace) -> int:
    try:
        refresh(args.owner)
        print("REFRESHED")
        return 0
    except TreeLockError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _cmd_release(args: argparse.Namespace) -> int:
    ok = release(args.owner)
    print("RELEASED" if ok else "NOT OWNER")
    return 0 if ok else 1


def _cmd_status(args: argparse.Namespace) -> int:
    print(json.dumps(status(), indent=2))
    return 0


def _cmd_guard(args: argparse.Namespace) -> int:
    try:
        st = guard(owner=args.owner)
        print(json.dumps(st, indent=2))
        return 0
    except TreeLockedError as exc:
        print(f"GUARD_FAIL: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Advisory lock against background commits")
    sub = ap.add_subparsers(dest="cmd", required=True)

    acq = sub.add_parser("acquire", help="acquire the tree lock")
    acq.add_argument("--owner", required=True)
    acq.add_argument("--session-id", default="")
    acq.add_argument("--reason", default="")
    acq.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS)
    acq.add_argument("--steal", action="store_true")
    acq.set_defaults(func=_cmd_acquire)

    ref = sub.add_parser("refresh", help="refresh heartbeat")
    ref.add_argument("--owner", required=True)
    ref.set_defaults(func=_cmd_refresh)

    rel = sub.add_parser("release", help="release the lock")
    rel.add_argument("--owner", required=True)
    rel.set_defaults(func=_cmd_release)

    st = sub.add_parser("status", help="show lock state")
    st.set_defaults(func=_cmd_status)

    gd = sub.add_parser("guard", help="fail if another owner holds a fresh lock")
    gd.add_argument("--owner", default="", help="treat this owner as allowed")
    gd.set_defaults(func=_cmd_guard)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
