"""Prove the event was projected, independently of what the emitter said.

Polls Candystore's `/events` for an event of our type whose
`data.generator.run_id` is this run's id (and whose `data.audience` matches
when asked). The emitter reporting success is not evidence the projection
saw it, and the projection is what every consumer reads.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta

from .common import (
    CANDYSTORE_URL, EVENT_TYPE, EXIT_OK, AcceptanceError, SourceUnavailable, to_iso_z, utc_now,
)

POLL_SECONDS = 3
LOOKBACK = timedelta(hours=2)
LIMIT = 50


def events_url() -> str:
    query = urllib.parse.urlencode({
        "type": EVENT_TYPE,
        "from": to_iso_z(utc_now() - LOOKBACK),
        "limit": LIMIT,
    })
    return f"{CANDYSTORE_URL.rstrip('/')}/events?{query}"


def fetch_events() -> list[dict]:
    with urllib.request.urlopen(events_url(), timeout=10) as resp:
        payload = json.load(resp)
    if isinstance(payload, dict):
        payload = payload.get("events") or []
    return [ev for ev in payload if isinstance(ev, dict)]


def _matches(event: dict, run_id: str, audience: str | None) -> dict | None:
    data = event.get("data") or {}
    generator = data.get("generator") or {}
    if generator.get("run_id") != run_id:
        return None
    if audience and data.get("audience") != audience:
        return None
    return {
        "id": event.get("id"),
        "audience": data.get("audience"),
        "time": event.get("time"),
        "dry_run": generator.get("dry_run"),
    }


def verify(run_id: str, timeout_seconds: int = 90, audience: str | None = None, expect: int = 1) -> dict:
    expect = max(1, int(expect or 1))
    started = time.monotonic()
    deadline = started + max(0, int(timeout_seconds))
    found: dict = {}
    polls = failures = 0
    last_error = ""
    while True:
        polls += 1
        try:
            events = fetch_events()
        except (urllib.error.URLError, OSError, ValueError) as exc:
            failures += 1
            last_error = str(exc)
            events = []
        for event in events:
            hit = _matches(event, run_id, audience)
            if hit:
                found[hit["id"] or len(found)] = hit
        if len(found) >= expect:
            return {"found": list(found.values()), "polls": polls,
                    "elapsed_seconds": round(time.monotonic() - started, 1), "url": events_url()}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(POLL_SECONDS, remaining))
    if failures == polls:
        raise SourceUnavailable(f"Candystore at {CANDYSTORE_URL} never answered in {timeout_seconds}s ({last_error})")
    who = f" for audience {audience}" if audience else ""
    raise AcceptanceError(
        f"no {EVENT_TYPE} event with generator.run_id {run_id}{who} in Candystore after {timeout_seconds}s "
        f"({polls} polls, {len(found)} of {expect} found)")


def verify_cmd(args) -> int:
    result = verify(args.run_id, args.timeout_seconds, getattr(args, "audience", None), getattr(args, "expect", 1))
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
        return EXIT_OK
    for hit in result["found"]:
        print(f"verified: event {hit['id']} ({hit['audience']}, {hit['time']}, dry_run={hit['dry_run']}) "
              f"for run {args.run_id}")
    print(f"candystore answered after {result['polls']} poll(s), {result['elapsed_seconds']}s")
    return EXIT_OK
