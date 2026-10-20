"""Annotated agent-turn facts for one day from Candystore.

Reads ``bloodbank.conversation.turn.annotated`` events -- the typed per-turn
facts the bloodbank turn-enricher publishes onto the bus (signal, action,
artifacts, blocker, outcome, thread linkage) -- and renders one day of them
as a SectionResult: how many annotated turns, which projects they touched,
what the top actions were, and where the blockers were.

Design decisions, and why:

* **Pagination walks backwards by ``offset``; ``since`` is ignored by
  Candystore.** Events arrive newest-first, so the collector pages until the
  oldest event on the page predates the report day's start (in the configured
  timezone), then filters by exact UTC bounds itself. A full page at the page
  budget means the read may be truncated and the section degrades to
  ``partial`` -- it never presents a partial window as the whole day.
* **The day is the operator's day, not UTC's.** ``config["timezone"]``
  (IANA name, ``America/New_York`` default) defines the local-day bounds,
  which are mapped to UTC before comparing against event timestamps. An
  unusable timezone is reported in a caveat and falls back to the host zone,
  matching ``pr_maintenance``.
* **Low-signal turns are excluded from the metrics but never hidden.** A
  turn whose ``data.signal`` is below ``signal_floor`` (default 0.5) carries
  no actionable fact, so it does not count toward ``annotated_turns``,
  ``avg_signal``, projects, actions or blockers -- but its count is stated in
  a caveat, because a day where the enricher mostly produced noise is itself
  a fact about the day.
* **Status is derived, never assumed.** Candystore unreachable is ``failed``
  with the URL and error in the reason; truncated pagination is ``partial``;
  a day with zero in-window annotated turns is ``empty`` with a reason;
  ``complete`` means every event down to the day boundary was read.

Read-only throughout: HTTP GETs against Candystore with an explicit timeout.

Config
------
``config["timezone"]``        IANA zone for the report day (default
``America/New_York``).
``section["options"]``        ``candystore_url`` (env ``CANDYSTORE_URL``
wins), ``page_size``, ``max_pages``, ``http_timeout_seconds``,
``signal_floor``.

Standalone::

    python3 -m collectors.turn_facts --date 2026-10-20 [--config PATH]

prints the SectionArtifact JSON on stdout and exits non-zero when the section
failed, so a scheduler cannot log success over a dead collector.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from collectors.base import (  # noqa: E402
    SECTION_RESULT_FIELDS,
    SectionResult,
    allowlist,
)
from reportctl_contracts import ConfigError  # noqa: E402

SECTION_ID = "turn-facts"

TURN_TYPE = "bloodbank.conversation.turn.annotated"

DEFAULT_CANDYSTORE_URL = "http://127.0.0.1:8683"
DEFAULT_PAGE_SIZE = 500
DEFAULT_MAX_PAGES = 20
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_SIGNAL_FLOOR = 0.5
DEFAULT_TIMEZONE = "America/New_York"
MAX_ACTIONS_PER_PROJECT = 3
TOP_PROJECTS_IN_SUMMARY = 3

#: Structural field allowlist on every Candystore event the moment it arrives.
#: Only these keys survive, at any depth -- no raw payload (tool arguments,
#: extractor output, working directories) can reach a rendered line, an
#: artifact, or the narrator.
EVENT_FIELDS = frozenset(
    {
        "type",
        "time",
        "project",
        "actor",
        "cli",
        "data",
        "signal",
        "action",
        "artifacts",
        "blocker",
        "outcome",
        "thread_id",
        "target_event_id",
    }
)


class SourceUnavailable(RuntimeError):
    """A source could not be read. The message becomes the section reason."""


def fetch_json(url: str, timeout: int = DEFAULT_HTTP_TIMEOUT) -> Any:
    """GET one JSON document, turning every failure into ``SourceUnavailable``."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise SourceUnavailable(f"HTTP {exc.code} from {url}") from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        raise SourceUnavailable(f"cannot reach {url}: {reason}") from exc
    try:
        return json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SourceUnavailable(f"{url} did not return JSON: {exc}") from exc


def _parse_time(value: Any) -> dt.datetime | None:
    """Event ``.time`` as an aware UTC datetime, or None if unusable."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        moment = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=dt.UTC)
    return moment.astimezone(dt.UTC)


def fetch_turn_events(
    base_url: str,
    day_start_utc: dt.datetime,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    timeout: int = DEFAULT_HTTP_TIMEOUT,
) -> tuple[list[dict[str, Any]], bool, list[str]]:
    """Page ``/events?type=...turn.annotated`` backwards to the day's start.

    Candystore answers newest-first and ignores ``since``, so the stop
    condition is local: keep paging until a page's oldest event predates
    ``day_start_utc`` (the whole day is then covered) or the stream runs dry.
    Returns ``(events, truncated, caveats)``; ``truncated`` means the page
    budget ran out with a full page still coming and the day may not be fully
    covered.
    """
    caveats: list[str] = []
    collected: list[dict[str, Any]] = []
    offset = 0
    for _ in range(max_pages):
        query = urllib.parse.urlencode(
            {"type": TURN_TYPE, "limit": page_size, "offset": offset}
        )
        url = f"{base_url}/events?{query}"
        page = fetch_json(url, timeout)
        if not isinstance(page, dict):
            raise SourceUnavailable(
                f"{url} returned {type(page).__name__}, expected an object"
            )
        batch = page.get("events")
        if not isinstance(batch, list):
            raise SourceUnavailable(f"{url} returned no events array")
        events = [item for item in batch if isinstance(item, dict)]
        collected.extend(events)
        if len(events) < page_size:
            return collected, False, caveats
        oldest = _parse_time(events[-1].get("time")) if events else None
        if oldest is None:
            caveats.append(
                "the oldest event on a page had no usable timestamp; pagination "
                "stopped there and the day may not be fully covered"
            )
            return collected, True, caveats
        if oldest < day_start_utc:
            return collected, False, caveats
        offset += page_size
    return collected, True, caveats


def _resolve_timezone(config: dict[str, Any], caveats: list[str]) -> dt.tzinfo:
    """The report day's timezone. A bad name is reported, never obeyed."""
    name = config.get("timezone") if isinstance(config, dict) else None
    if isinstance(name, str) and name.strip():
        try:
            return ZoneInfo(name.strip())
        except (ZoneInfoNotFoundError, ValueError):
            caveats.append(
                f"config timezone {name!r} is not a known IANA zone; used the host "
                "local timezone for the day bounds"
            )
    elif name is None:
        return ZoneInfo(DEFAULT_TIMEZONE)
    else:
        caveats.append(
            f"config timezone {name!r} is not a string; used the host local "
            "timezone for the day bounds"
        )
    local = dt.datetime.now().astimezone().tzinfo
    return local if local is not None else dt.UTC


def _signal_floor(options: dict[str, Any], caveats: list[str]) -> float:
    value = options.get("signal_floor", DEFAULT_SIGNAL_FLOOR)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        caveats.append(
            f"option signal_floor={value!r} is not a number; used {DEFAULT_SIGNAL_FLOOR}"
        )
        return DEFAULT_SIGNAL_FLOOR
    return float(value)


def _positive_int(options: dict[str, Any], key: str, default: int, caveats: list[str]) -> int:
    value = options.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        if key in options:
            caveats.append(f"option {key}={value!r} is not a positive integer; used {default}")
        return default
    return value


def _allowlisted(result: SectionResult) -> SectionResult:
    """Structural allowlist on the way out: only SectionResult keys survive."""
    return SectionResult(**allowlist(asdict(result), SECTION_RESULT_FIELDS))


def collect(
    section_cfg: dict[str, Any],
    report_date: str | None = None,
    config: dict[str, Any] | None = None,
    *,
    date: str | None = None,
) -> SectionResult:
    """Collect one day of annotated agent-turn facts. Never raises.

    ``date=`` is accepted as an alias so the keyword call style used by
    ``reportctl collect`` works unchanged alongside the positional contract.
    """
    section_id = SECTION_ID
    if isinstance(section_cfg, dict) and isinstance(section_cfg.get("id"), str):
        section_id = section_cfg["id"].strip() or SECTION_ID
    report_date = report_date if report_date is not None else date
    if report_date is None:
        return _allowlisted(
            SectionResult(
                id=section_id,
                status="failed",
                reason="collect() was called without a report date",
                summary=f"{section_id}: no turn facts collected, no report date was given",
            )
        )
    try:
        return _allowlisted(_collect(section_id, section_cfg or {}, report_date, config or {}))
    except Exception as exc:  # noqa: BLE001 - a crash must degrade, never propagate
        return _allowlisted(
            SectionResult(
                id=section_id,
                status="failed",
                reason=f"{type(exc).__name__}: {exc}",
                summary=f"{section_id}: collector raised {type(exc).__name__}",
            )
        )


def _collect(
    section_id: str,
    section_cfg: dict[str, Any],
    report_date: str,
    config: dict[str, Any],
) -> SectionResult:
    caveats: list[str] = []
    options = section_cfg.get("options")
    options = options if isinstance(options, dict) else {}

    try:
        day = dt.date.fromisoformat(str(report_date))
    except ValueError:
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"report_date {report_date!r} is not an ISO YYYY-MM-DD date",
            summary=f"{section_id}: no turn facts collected, the report date was unusable",
        )

    tz = _resolve_timezone(config, caveats)
    start_local = dt.datetime.combine(day, dt.time.min, tzinfo=tz)
    end_local = start_local + dt.timedelta(days=1)
    start_utc = start_local.astimezone(dt.UTC)
    end_utc = end_local.astimezone(dt.UTC)

    configured = options.get("candystore_url")
    configured = (
        configured.strip()
        if isinstance(configured, str) and configured.strip()
        else DEFAULT_CANDYSTORE_URL
    )
    environment = os.environ.get("CANDYSTORE_URL", "").strip()
    candystore_url = (environment or configured).rstrip("/")
    if environment and candystore_url != configured.rstrip("/"):
        caveats.append(
            f"candystore_url {configured} overridden by the CANDYSTORE_URL environment "
            f"variable ({candystore_url})"
        )
    page_size = _positive_int(options, "page_size", DEFAULT_PAGE_SIZE, caveats)
    max_pages = _positive_int(options, "max_pages", DEFAULT_MAX_PAGES, caveats)
    http_timeout = _positive_int(
        options, "http_timeout_seconds", DEFAULT_HTTP_TIMEOUT, caveats
    )
    signal_floor = _signal_floor(options, caveats)

    try:
        raw_events, truncated, fetch_caveats = fetch_turn_events(
            candystore_url,
            start_utc,
            page_size=page_size,
            max_pages=max_pages,
            timeout=http_timeout,
        )
    except SourceUnavailable as exc:
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"Candystore turn-event history unavailable: {exc}",
            summary=(
                f"{section_id}: no turn facts collected for {report_date}; "
                f"Candystore at {candystore_url} could not be read"
            ),
            metrics={"candystore_reachable": False, "candystore_url": candystore_url},
            caveats=caveats,
        )
    caveats.extend(fetch_caveats)

    events = [item for item in allowlist(raw_events, EVENT_FIELDS) if isinstance(item, dict)]

    in_window: list[dict[str, Any]] = []
    for event in events:
        moment = _parse_time(event.get("time"))
        if moment is None:
            continue
        if start_utc <= moment < end_utc:
            in_window.append(event)

    if not in_window:
        status = "partial" if truncated else "empty"
        reason_parts = [
            f"no {TURN_TYPE} events on {report_date} "
            f"({start_utc:%Y-%m-%dT%H:%M:%SZ} to {end_utc:%Y-%m-%dT%H:%M:%SZ} UTC)"
        ]
        if truncated:
            reason_parts.append(
                f"pagination also stopped at the {max_pages}-page budget, so older "
                "events that might fall in the window were never read"
            )
        return SectionResult(
            id=section_id,
            status=status,
            reason="; ".join(reason_parts),
            summary=(
                f"{section_id}: no annotated agent turns recorded for {report_date}."
            ),
            metrics={
                "annotated_turns": 0,
                "projects": 0,
                "turns_with_blockers": 0,
                "avg_signal": 0.0,
                "candystore_reachable": True,
                "candystore_url": candystore_url,
            },
            caveats=caveats,
        )

    # ---- signal floor: excluded from metrics, never hidden ----------------
    kept: list[dict[str, Any]] = []
    skipped_low_signal = 0
    for event in in_window:
        data = event.get("data")
        data = data if isinstance(data, dict) else {}
        signal = data.get("signal")
        if isinstance(signal, bool) or not isinstance(signal, (int, float)):
            skipped_low_signal += 1
            continue
        if float(signal) < signal_floor:
            skipped_low_signal += 1
            continue
        kept.append(event)
    if skipped_low_signal:
        caveats.append(
            f"{skipped_low_signal} annotated turn(s) on {report_date} had "
            f"data.signal below {signal_floor} or missing and were excluded from "
            "the metrics"
        )

    if not kept:
        return SectionResult(
            id=section_id,
            status="empty",
            reason=(
                f"all {skipped_low_signal} annotated turn(s) on {report_date} fell "
                f"below the signal floor of {signal_floor}"
            ),
            summary=(
                f"{section_id}: {skipped_low_signal} annotated turn(s) on {report_date} "
                f"but none at or above signal {signal_floor}."
            ),
            metrics={
                "annotated_turns": 0,
                "projects": 0,
                "turns_with_blockers": 0,
                "avg_signal": 0.0,
                "low_signal_turns": skipped_low_signal,
                "candystore_reachable": True,
                "candystore_url": candystore_url,
            },
            caveats=caveats,
        )

    # ---- aggregation ------------------------------------------------------
    per_project: dict[str, list[dict[str, Any]]] = {}
    blockers: list[tuple[str, str]] = []
    signals: list[float] = []
    for event in kept:
        project = event.get("project")
        project = project.strip() if isinstance(project, str) and project.strip() else "unknown"
        data = event.get("data")
        data = data if isinstance(data, dict) else {}
        per_project.setdefault(project, []).append(event)
        signal = data.get("signal")
        signals.append(float(signal) if isinstance(signal, (int, float)) else 0.0)
        blocker = data.get("blocker")
        if isinstance(blocker, str) and blocker.strip():
            text = blocker.strip().splitlines()[0]
            # The enricher writes the literal "none"/"null"/"n/a" when a turn
            # has no blocker; rendering that as BLOCKED would invent blockers.
            if text.lower() not in {"none", "null", "n/a", "no blocker"}:
                blockers.append((project, text))

    detail: list[str] = []
    for project in sorted(per_project):
        turns = per_project[project]
        actions = Counter()
        for event in turns:
            data = event.get("data")
            data = data if isinstance(data, dict) else {}
            action = data.get("action")
            if isinstance(action, str) and action.strip():
                actions[action.strip()] += 1
        top = [name for name, _ in actions.most_common(MAX_ACTIONS_PER_PROJECT)]
        action_text = ", ".join(top) if top else "(none recorded)"
        detail.append(f"{project}: {len(turns)} turns, top actions: {action_text}")
    for project, blocker in blockers:
        detail.append(f"{project}: BLOCKED - {blocker}")

    ranked = sorted(per_project.items(), key=lambda item: (-len(item[1]), item[0]))
    top_projects = ranked[:TOP_PROJECTS_IN_SUMMARY]
    top_text = ", ".join(f"{name} ({len(turns)})" for name, turns in top_projects)
    if len(ranked) > len(top_projects):
        top_text += f", and {len(ranked) - len(top_projects)} more"
    summary = (
        f"On {report_date} agents produced {len(kept)} annotated turn(s) across "
        f"{len(per_project)} project(s); busiest: {top_text}. "
        f"{len(blockers)} turn(s) reported a blocker."
    )

    status = "complete"
    reason = ""
    if truncated:
        status = "partial"
        reason = (
            f"event pagination stopped at the {max_pages}-page budget "
            f"({len(events)} events read); turns earlier in the day may be missing"
        )

    metrics: dict[str, Any] = {
        "annotated_turns": len(kept),
        "projects": len(per_project),
        "turns_with_blockers": len(blockers),
        "avg_signal": round(sum(signals) / len(signals), 3),
        "low_signal_turns": skipped_low_signal,
        "candystore_reachable": True,
        "candystore_url": candystore_url,
    }

    return SectionResult(
        id=section_id,
        status=status,
        reason=reason,
        summary=summary,
        metrics=metrics,
        detail=detail,
        caveats=caveats,
    )


# --------------------------------------------------------------------------
# standalone entry point
# --------------------------------------------------------------------------

DEFAULT_CONFIG_PATH = Path("~/.config/delonet-daily-report/report.json").expanduser()
EXAMPLE_CONFIG_PATH = SCRIPTS_DIR.parent / "assets" / "example-config.v2.json"


def _section_for(config: dict[str, Any]) -> dict[str, Any]:
    for section in config.get("sections", []):
        if isinstance(section, dict) and (
            section.get("collector") == "turn_facts" or section.get("id") == SECTION_ID
        ):
            return section
    return {"id": SECTION_ID, "options": {}, "max_age_hours": config.get("max_age_hours", 24)}


def _load(path: Path | None) -> tuple[dict[str, Any], str | None]:
    """Load a config. Explicit paths are strict; the fallback chain is stated."""
    from reportctl_config import load_config

    if path is not None:
        return load_config(path), None
    for candidate in (DEFAULT_CONFIG_PATH, EXAMPLE_CONFIG_PATH):
        try:
            return load_config(candidate), f"using config {candidate}"
        except (ConfigError, OSError):
            continue
    return {"timezone": DEFAULT_TIMEZONE, "sections": [], "max_age_hours": 24}, (
        "no usable config found; running with defaults"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="collectors.turn_facts",
        description="Collect one day of annotated agent-turn facts as a SectionArtifact.",
    )
    parser.add_argument(
        "--date",
        default=(dt.date.today() - dt.timedelta(days=1)).isoformat(),
        help="report date, YYYY-MM-DD (default: yesterday)",
    )
    parser.add_argument("--config", help="operator config; defaults are tried when omitted")
    parser.add_argument("--run-id", default=None, help="run identifier to stamp on the artifact")
    args = parser.parse_args(argv)

    run_id = args.run_id or f"turn-facts-{args.date}-{dt.datetime.now(dt.UTC):%H%M%S}"
    try:
        config, note = _load(Path(args.config).expanduser() if args.config else None)
    except (ConfigError, OSError) as exc:
        result = SectionResult(
            id=SECTION_ID,
            status="failed",
            reason=f"config unusable: {exc}",
            summary=f"{SECTION_ID}: no turn facts collected, the config could not be loaded",
        )
        print(json.dumps(result.to_artifact(run_id, 24), indent=2))
        return 1
    if note:
        print(note, file=sys.stderr)

    section = _section_for(config)
    result = collect(section, args.date, config)
    max_age = section.get("max_age_hours") or config.get("max_age_hours") or 24
    artifact = result.to_artifact(run_id, int(max_age))
    print(json.dumps(artifact, indent=2))
    return 1 if artifact["status"] == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
