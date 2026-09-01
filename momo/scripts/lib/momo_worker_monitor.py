"""momo_worker_monitor — heartbeat/timeout and retry policy for worker hand-backs.

Strategy pattern: the policy decides whether a stale/abandoned handback should be
retried, given the retry state. A separate watcher polls the bundle and exits
with a machine-readable status so Momo can act.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# Insert canonical lib path
_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB))

from momo_handback import (  # type: ignore[import]  # noqa: E402
    HandbackBundle,
    HandbackError,
    default_spool,
    is_stale,
    load,
    next_retry_wait,
    save,
)


class WorkerMonitorError(Exception):
    pass


@dataclass
class WatchResult:
    issue: str
    state: str  # healthy | stale | retrying | exhausted | finished
    seconds_since_heartbeat: float
    attempt: int
    max_attempts: int
    wait_seconds: int
    reason: str


def _now_epoch() -> float:
    return time.time()


def default_policy(bundle: HandbackBundle, now: float | None = None) -> WatchResult:
    """Default fixed-count backoff retry policy.

    - If status is terminal (DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT):
      state = finished.
    - If heartbeat fresh: healthy.
    - If stale and attempts remain: retrying.
    - If stale and no attempts remain: exhausted.
    """
    now = now or _now_epoch()
    issue = bundle.issue or "unknown"
    status = bundle.status
    if status in {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"}:
        return WatchResult(
            issue=issue,
            state="finished",
            seconds_since_heartbeat=0.0,
            attempt=bundle.retries.attempt,
            max_attempts=bundle.retries.max_attempts,
            wait_seconds=0,
            reason=f"terminal status {status}",
        )

    seconds = 0.0
    try:
        seconds = now - datetime_fromiso(bundle.heartbeat.last_seen_at).timestamp()
    except Exception:
        seconds = float("inf")
    stale = is_stale(bundle, now)

    if not stale:
        return WatchResult(
            issue=issue,
            state="healthy",
            seconds_since_heartbeat=seconds,
            attempt=bundle.retries.attempt,
            max_attempts=bundle.retries.max_attempts,
            wait_seconds=0,
            reason="heartbeat fresh",
        )

    if bundle.retries.attempt < bundle.retries.max_attempts:
        return WatchResult(
            issue=issue,
            state="retrying",
            seconds_since_heartbeat=seconds,
            attempt=bundle.retries.attempt,
            max_attempts=bundle.retries.max_attempts,
            wait_seconds=next_retry_wait(bundle),
            reason=f"stale {int(seconds)}s; retry {bundle.retries.attempt + 1}/{bundle.retries.max_attempts}",
        )

    return WatchResult(
        issue=issue,
        state="exhausted",
        seconds_since_heartbeat=seconds,
        attempt=bundle.retries.attempt,
        max_attempts=bundle.retries.max_attempts,
        wait_seconds=0,
        reason=f"stale {int(seconds)}s; retries exhausted",
    )


def datetime_fromiso(s: str) -> Any:
    from datetime import datetime, timezone
    # Python 3.11+ handles Z; for older versions normalize.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def watch(
    issue: str,
    spool: Path | None = None,
    policy: Callable[[HandbackBundle, float | None], WatchResult] | None = None,
) -> WatchResult:
    policy = policy or default_policy
    bundle = load(issue, spool)
    return policy(bundle, _now_epoch())


def record_retry(issue: str, spool: Path | None = None) -> Path:
    """Increment the retry counter and update heartbeat so the next watcher knows
    a retry was dispatched."""
    bundle = load(issue, spool)
    bundle.retries.attempt += 1
    bundle.bump_heartbeat()
    bundle.status = ""  # reset terminal status if any, worker must re-finalize
    return save(bundle, spool)


def run_once(args: argparse.Namespace) -> int:
    result = watch(args.issue, args.spool)
    out = {
        "issue": result.issue,
        "state": result.state,
        "seconds_since_heartbeat": result.seconds_since_heartbeat,
        "attempt": result.attempt,
        "max_attempts": result.max_attempts,
        "wait_seconds": result.wait_seconds,
        "reason": result.reason,
    }
    print(json.dumps(out, indent=2))
    # Exit codes aligned with shell callers:
    # 0 = healthy / finished (no action)
    # 1 = stale, retry dispatched (caller should respawn worker)
    # 2 = exhausted / error
    if result.state in {"healthy", "finished"}:
        return 0
    if result.state == "retrying":
        if args.dispatch:
            record_retry(args.issue, args.spool)
            subprocess.Popen(
                args.dispatch,
                env={**os.environ, "MOMO_ISSUE": result.issue, "MOMO_ATTEMPT": str(result.attempt + 1)},
            )
        return 1
    return 2


def poll_loop(args: argparse.Namespace) -> int:
    last_state = ""
    while True:
        result = watch(args.issue, args.spool)
        if result.state != last_state:
            print(json.dumps({
                "issue": result.issue,
                "state": result.state,
                "attempt": result.attempt,
                "reason": result.reason,
            }, indent=2))
            last_state = result.state
        if result.state in {"finished", "exhausted"}:
            return 0 if result.state == "finished" else 2
        if result.state == "retrying" and args.dispatch:
            record_retry(args.issue, args.spool)
            subprocess.Popen(
                args.dispatch,
                env={**os.environ, "MOMO_ISSUE": result.issue, "MOMO_ATTEMPT": str(result.attempt + 1)},
            )
        time.sleep(args.interval)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Monitor a worker hand-back bundle")
    ap.add_argument("--issue", required=True)
    ap.add_argument("--spool", type=Path)
    ap.add_argument("--dispatch", help="command to run when a retry is triggered")
    ap.add_argument("--poll", action="store_true", help="poll until terminal")
    ap.add_argument("--interval", type=int, default=30, help="poll interval seconds")
    args = ap.parse_args(argv)
    try:
        if args.poll:
            return poll_loop(args)
        return run_once(args)
    except HandbackError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
