#!/usr/bin/env python3
"""Optional LLM usage accounting for an audiobook build (kept apart from TTS tokens).

    usage.py capture SESSION_ID [SESSION_ID ...] [--children] --out usage/snapshot.json
    usage.py cost --snapshot usage/snapshot.json --pricing usage/pricing.json
    usage.py energy --seconds 1460 --low-watts 150 --high-watts 350 --usd-per-kwh 0.15
    usage.py record --book DIR --chapter N --label build --snapshot usage/snapshot.json [--pricing P]

Why this exists: a 50-minute chapter cost 9,906 TTS text tokens but 17.3M LLM tokens of
research/engineering/orchestration. Those are different tokenizers and different bills; never
add them. Rules that kept the numbers honest in the pilot:
  * Read OpenCode's own message rows (assistant messages with time.completed), per session AND
    its delegated child sessions (`--children`), because subagents carry most of the tokens.
  * Exclude the still-running assistant message; say so in the snapshot caveats.
  * cache reads repeat on every request: totals are consumption, not unique content.
  * OpenCode's `cost` field is 0 on subscription routes. That is not proof of zero cost nor of a
    charge. API-equivalent dollars are a counterfactual comparison, labeled as such.
  * Prices are never baked in: pass a pricing file you can cite (see references/usage-accounting.md).
"""
from __future__ import annotations

import argparse
import datetime
import errno
import json
import math
import os
import pty
import select
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from abk_common import AbkError, read_json, utc_now, write_json

DB_PATH = Path(os.environ.get("OPENCODE_DB", Path.home() / ".local/share/opencode/opencode.db"))
RATE_FIELDS = {
    "input_tokens": "uncached_input_per_million", "cache_read_tokens": "cache_read_per_million",
    "cache_write_tokens": "cache_write_per_million", "output_tokens": "output_per_million",
}


# ------------------------------------------------------------------- capture


def child_sessions(session_ids: list[str], db_path: Path = DB_PATH) -> list[str]:
    """Return session_ids plus every transitive child (subagent) session, parents first."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        seen = list(dict.fromkeys(session_ids))
        frontier = list(seen)
        while frontier:
            marks = ",".join("?" * len(frontier))
            rows = conn.execute(f"select id from session where parent_id in ({marks}) order by time_created", frontier).fetchall()
            frontier = [row[0] for row in rows if row[0] not in seen]
            seen.extend(frontier)
        return seen
    finally:
        conn.close()


def export_session_from_db(session_id: str, db_path: Path = DB_PATH) -> dict[str, Any]:
    """Rebuild the legacy `opencode export` shape from the read-only sqlite store.

    OpenCode v2 removed the `export` subcommand, and a hung TUI can still leave the DB readable:
    always prefer this path.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        session = conn.execute(
            "select id, parent_id, directory, title, time_created from session where id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise AbkError(f"Session not found: {session_id}")
        messages = [
            {"info": {"id": message_id, **json.loads(data)}}
            for message_id, data in conn.execute(
                "select id, data from message where session_id = ? order by time_created, id", (session_id,)
            )
        ]
    finally:
        conn.close()
    return {
        "info": {"id": session[0], "parentID": session[1], "directory": session[2], "title": session[3],
                 "time": {"created": session[4]}},
        "messages": messages,
    }


def export_session_from_cli(session_id: str, timeout: float = 30) -> dict[str, Any]:
    """Legacy `opencode export` (run under a pty, as the pilot did)."""
    master, slave = pty.openpty()
    process = subprocess.Popen(["opencode", "--pure", "export", session_id], stdout=slave,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    os.close(slave)
    deadline = time.monotonic() + timeout
    data = bytearray()
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Session export timed out: {session_id}")
            ready, _, _ = select.select([master], [], [], remaining)
            if not ready:
                raise TimeoutError(f"Session export timed out: {session_id}")
            try:
                chunk = os.read(master, 65536)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            data.extend(chunk)
        if process.wait(timeout=max(0.1, deadline - time.monotonic())) != 0:
            raise AbkError(f"Session export failed: {session_id}")
        return json.loads(data)
    finally:
        os.close(master)
        if process.poll() is None:
            process.kill()
        process.wait()


def export_session(session_id: str) -> dict[str, Any]:
    try:
        return export_session_from_db(session_id)
    except (sqlite3.Error, OSError):
        return export_session_from_cli(session_id)


def summarize_session(data: dict[str, Any]) -> dict[str, Any]:
    totals: dict[str, Any] = {
        "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "cache_read_tokens": 0,
        "cache_write_tokens": 0, "reported_total_tokens": 0, "opencode_reported_cost_usd": 0.0,
        "completed_assistant_messages": 0, "incomplete_assistant_messages_excluded": 0,
        "messages_missing_total_tokens": 0, "messages_missing_usage": 0, "messages_missing_cost": 0,
    }
    models: set[str] = set()
    providers: set[str] = set()
    for message in data.get("messages", []):
        info = message.get("info", {})
        if info.get("role") != "assistant":
            continue
        if not info.get("time", {}).get("completed"):
            totals["incomplete_assistant_messages_excluded"] += 1
            continue
        totals["completed_assistant_messages"] += 1
        tokens = info.get("tokens", {}) or {}
        if not tokens:
            totals["messages_missing_usage"] += 1
        cache = tokens.get("cache", {}) or {}
        for target, source in (("input_tokens", "input"), ("output_tokens", "output"), ("reasoning_tokens", "reasoning")):
            totals[target] += tokens.get(source, 0) or 0
        totals["cache_read_tokens"] += cache.get("read", 0) or 0
        totals["cache_write_tokens"] += cache.get("write", 0) or 0
        if tokens.get("total") is None:
            totals["messages_missing_total_tokens"] += 1
        else:
            totals["reported_total_tokens"] += tokens["total"]
        if info.get("cost") is None:
            totals["messages_missing_cost"] += 1
        else:
            totals["opencode_reported_cost_usd"] += info["cost"]
        models.add(info.get("modelID", "unknown"))
        providers.add(info.get("providerID", "unknown"))
    return {
        "session_id": data["info"]["id"], "parent_session_id": data["info"].get("parentID"),
        "title": data["info"].get("title"), "models": sorted(models), "providers": sorted(providers), **totals,
    }


def capture(session_ids: list[str], children: bool = False, exporter=export_session, db_path: Path = DB_PATH) -> dict[str, Any]:
    ids = child_sessions(session_ids, db_path) if children else list(dict.fromkeys(session_ids))
    sessions = [summarize_session(exporter(sid)) for sid in ids]
    keys = [k for k, v in sessions[0].items() if isinstance(v, (int, float)) and not isinstance(v, bool)]
    totals = {key: sum(session[key] for session in sessions) for key in keys}
    return {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "source": "OpenCode completed assistant-message usage fields",
        "scope": "Explicit sessions" + (" plus delegated child sessions" if children else ""),
        "totals": totals, "sessions": sessions, "actual_llm_charge_usd": None,
        "caveats": [
            "Excludes assistant messages not yet completed when captured (including the one writing this).",
            "Repeated context/cache reads count on every request; totals are consumption, not unique content.",
            "Reasoning and cache fields are reported separately; do not add them to reported_total_tokens again.",
            "A zero OpenCode-reported cost is not proof of zero provider cost or subscription consumption.",
            "VoxCPM2 text tokens use another tokenizer and are recorded separately in metrics.json.",
            "Search API charges, OCR CPU work, GPU electricity, and other infrastructure are not included.",
        ],
    }


# ---------------------------------------------------------------------- cost


def api_equivalent(usage: dict[str, Any], pricing: dict[str, Any]) -> dict[str, Any]:
    """Counterfactual cost at published per-million rates. Missing inputs -> null, never a guess."""
    rates = pricing.get("rates_usd_per_million", {})
    counts = {f: usage.get(f) for f in RATE_FIELDS}
    for field, value in counts.items():
        if value is not None and (type(value) is not int or value < 0):
            raise AbkError(f"Invalid token count: {field}")
    for field, key in RATE_FIELDS.items():
        rate = rates.get(key)
        if rate is not None and (not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < 0):
            raise AbkError(f"Invalid rate: {key}")
    if any(counts[f] is None or rates.get(RATE_FIELDS[f]) is None for f in RATE_FIELDS):
        return {"usd": None, "breakdown_usd": None, "basis": "Incomplete usage or rates; not estimated"}
    breakdown = {f: counts[f] * rates[RATE_FIELDS[f]] / 1_000_000 for f in RATE_FIELDS}
    return {
        "usd": sum(breakdown.values()), "breakdown_usd": breakdown, "not_actual_charge": True,
        "basis": pricing.get("basis", "Counterfactual API-equivalent pricing, not a subscription charge"),
    }


def per_request_tier_note(pricing: dict[str, Any]) -> str | None:
    threshold = pricing.get("long_context_threshold_input_tokens")
    return (f"Rates assume every request stayed at or under {threshold} input tokens; "
            "above that, long-context multipliers apply per request and aggregate snapshots cannot show it.") if threshold else None


def electricity_scenario(seconds: float, low_watts: float, high_watts: float, usd_per_kwh: float) -> dict[str, Any]:
    values = [seconds, low_watts, high_watts, usd_per_kwh]
    if any(not math.isfinite(v) or v < 0 for v in values) or high_watts < low_watts:
        raise AbkError("Energy assumptions must be finite, nonnegative, and ordered")
    low, high = (seconds * w / 3_600_000 for w in (low_watts, high_watts))
    return {"kwh_low": low, "kwh_high": high, "usd_low": low * usd_per_kwh, "usd_high": high * usd_per_kwh,
            "measured": False, "note": "Scenario from assumed watts, not a power-meter reading"}


def by_session_cost(snapshot: dict[str, Any], pricing: dict[str, Any]) -> dict[str, Any]:
    return {s["session_id"]: api_equivalent(s, pricing) for s in snapshot["sessions"]}


# ----------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("session_ids", nargs="+")
    cap.add_argument("--children", action="store_true", help="include delegated child sessions")
    cap.add_argument("--out", type=Path, required=True)
    cost = sub.add_parser("cost")
    cost.add_argument("--snapshot", type=Path, required=True)
    cost.add_argument("--pricing", type=Path, required=True)
    energy = sub.add_parser("energy")
    energy.add_argument("--seconds", type=float, required=True)
    energy.add_argument("--low-watts", type=float, required=True)
    energy.add_argument("--high-watts", type=float, required=True)
    energy.add_argument("--usd-per-kwh", type=float, required=True)
    rec = sub.add_parser("record", help="append a usage entry to book.json")
    rec.add_argument("--book", type=Path, required=True)
    rec.add_argument("--chapter", type=int)
    rec.add_argument("--label", required=True)
    rec.add_argument("--snapshot", type=Path, required=True)
    rec.add_argument("--pricing", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            if not args.out.parent.is_dir():
                raise AbkError(f"Output parent must already exist: {args.out.parent}")
            report = capture(args.session_ids, args.children)
            write_json(args.out, report)
            result: Any = report["totals"]
        elif args.command == "cost":
            snapshot, pricing = read_json(args.snapshot), read_json(args.pricing)
            result = {"total": api_equivalent(snapshot["totals"], pricing),
                      "by_session": by_session_cost(snapshot, pricing), "tier_note": per_request_tier_note(pricing)}
        elif args.command == "energy":
            result = electricity_scenario(args.seconds, args.low_watts, args.high_watts, args.usd_per_kwh)
        else:
            import book as bookmod

            snapshot = read_json(args.snapshot)
            entry = {
                "label": args.label, "chapter": args.chapter, "recorded_utc": utc_now(),
                "snapshot": str(args.snapshot), "totals": snapshot["totals"],
                "api_equivalent_usd": api_equivalent(snapshot["totals"], read_json(args.pricing))["usd"] if args.pricing else None,
                "actual_llm_charge_usd": snapshot.get("actual_llm_charge_usd"),
            }
            with bookmod.locked(args.book) as data:
                data["usage"].append(entry)
            result = entry
    except (AbkError, OSError, KeyError, sqlite3.Error, TimeoutError, json.JSONDecodeError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
