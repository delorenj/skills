"""The self-check: did this report pipeline actually deliver, day by day?

This is the section that would have caught the 2026-08-18 failure, where a
scheduler logged "completed successfully" over a command that exited 2 and the
emitted Bloodbank event hardcoded ``outcome.status="complete"``. Two independent
false greens, neither visible anywhere.

It reads two *independent* sources and refuses to believe either one alone:

* the archive this pipeline writes -- ``<archive_dir>/<YYYY>/<MM>/<DD>/current.json``
  must exist, point at a generation directory that exists, and that generation's
  ``report.json`` must validate;
* Candystore's audit trail -- ``bloodbank.reporting.report.completed`` events
  over the same window, read under both the current four-token name and the
  retired ``bloodbank.v1.`` spelling that history keeps (see ``query_types``).

Agreement is unremarkable. **Disagreement is the whole point**, and both
directions are defects that get named explicitly:

``published-but-never-archived`` (event-without-archive)
    something published a completion event while nothing valid was archived --
    i.e. the emitter lied, exactly as it did on 2026-08-18.

``archived-but-never-published`` (archive-without-event)
    a report was archived but its completion event never reached Candystore --
    publication failed, so nothing downstream can see the report exists.

Every day in the lookback window ends up classified as exactly one of
``delivered``, ``missing``, ``invalid``, ``unpublished-but-archived`` (generations
staged, the pointer swap never happened), ``in-progress``, or ``unknown`` (that day
could not be read, so no claim is made about it), and carries an independent
cross-check verdict of ``agreed``, ``published-but-never-archived``,
``archived-but-never-published``, or ``unchecked``.

The day this run is producing (``report_date``) has not been published yet at
collect time -- publication happens later in the pipeline -- so it is reported as
``in-progress`` and excluded from the ``missing`` tally. It is still cross-checked
against Candystore: a completion event for a day this run has not yet published
means an *earlier* run claimed a report that is not there.

Two different questions, two different fields. Conflating them is what broke
this collector twice, in opposite directions.

``status`` -- could this collector do its work?
    ``complete``
        Every source it needs was read and the answer is trustworthy. **This
        includes the answer "six days are missing and here they are."** A gap
        the collector correctly found is a finished job, not a broken one.
    ``partial``
        A source could not be read: Candystore (so nothing corroborates the
        archive answer), or one or more individual days of the archive (so no
        claim is made about those days). Everything that *was* read is still
        reported in full.
    ``failed``
        The archive could not be read, so no claim about any day is possible;
        or the report date is unusable; or the collector crashed.

``metrics.delivery_health`` -- was the news good?
    ``ok``, ``degraded``, ``failed``, or ``unknown``. This is the delivery
    verdict, and it belongs here, in ``summary``, in ``caveats``, and in the
    rendered document -- never in ``status``.

The verdict used to live in ``status``, and the result was a latch that could
never reopen. ``report-delivery`` is a *required* section, a required section
that is not ``complete`` failed the run, a failed run publishes a generation
that ``verify_published`` refuses, and a refused generation is exactly what
``_scan_day`` classifies ``invalid``. So one missed day made tomorrow's window
hold a gap, which failed tomorrow's run, forever -- the report that tells you
something is wrong being suppressed as a failure. Reporting bad news accurately
is success. The bad news goes in the content, loudly, and the run exits 0 so a
human actually receives it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # normal package import (``python3 -m collectors.report_delivery``)
    from .base import SectionResult, allowlist, run_collector
except ImportError:  # pragma: no cover - direct-file execution
    from base import SectionResult, allowlist, run_collector  # type: ignore[no-redef]

from reportctl_archive import verify_published  # noqa: E402
from reportctl_config import load_config  # noqa: E402
from reportctl_contracts import ConfigError  # noqa: E402
from reportctl_runtime import archive_paths  # noqa: E402

SECTION_ID = "report-delivery"
SKILL_ROOT = Path(__file__).resolve().parents[2]
LIVE_CONFIG = Path("~/.config/delonet-daily-report/report.json")
EXAMPLE_CONFIG = SKILL_ROOT / "assets" / "example-config.v2.json"

DEFAULT_CANDYSTORE_URL = "http://127.0.0.1:8683"
DEFAULT_EVENT_TYPE = "bloodbank.reporting.report.completed"

#: Candystore keeps both eras of an event name forever: the retired five-token
#: ``bloodbank.v1.<domain>.<entity>.<action>`` on every row written before the
#: version token was dropped, and the version-free four-token name since. This
#: collector cross-checks the archive against *history*, so asking for one
#: shape alone manufactures a delivery gap for the other era's days -- every
#: pre-migration report would read "archived-but-never-published". Candystore's
#: ``type`` filter takes a comma-separated list, so both spellings ride one
#: query. The publish side in ``scripts/run.py`` emits the new shape only.
_VERSION_TOKEN_RE = re.compile(r"^bloodbank\.v[0-9]+\.")


def query_types(event_type: str) -> str:
    """Every spelling of one event name, as Candystore's ``type`` filter value.

    The configured type is honoured verbatim and joined with its canonical
    (version-free) form and the retired ``v1`` form, so a config that still
    names the old shape reads the new rows too.
    """
    canonical = _VERSION_TOKEN_RE.sub("bloodbank.", event_type, count=1)
    shapes = [canonical]
    for alias in (event_type, canonical.replace("bloodbank.", "bloodbank.v1.", 1)):
        if alias not in shapes:
            shapes.append(alias)
    return ",".join(shapes)
DEFAULT_LOOKBACK_DAYS = 7
DEFAULT_HTTP_TIMEOUT = 10
PAGE_SIZE = 500
MAX_PAGES = 40
REASON_CAP = 400
MAX_DISAGREEMENT_CAVEATS = 12

#: Config keys this collector cannot work without.
REQUIRED_CONFIG_KEYS = ("artifact_dir", "archive_dir", "sections", "core_sections")

DELIVERED = "delivered"
MISSING = "missing"
INVALID = "invalid"
UNPUBLISHED = "unpublished-but-archived"
IN_PROGRESS = "in-progress"
#: The archive could not be read -- the whole root, or just this day. Never a
#: claim about a day: it is the refusal to make one, and it degrades the
#: collection (``partial``) rather than being counted as a delivery gap.
UNKNOWN = "unknown"

#: Cross-check verdicts. The two disagreement labels are the whole reason this
#: section reads two sources instead of trusting either one.
AGREED = "agreed"
EVENT_WITHOUT_ARCHIVE = "published-but-never-archived"
ARCHIVE_WITHOUT_EVENT = "archived-but-never-published"
UNCHECKED = "unchecked"

#: Day statuses that mean "this day was due and no valid report exists for it".
#: Two statuses are deliberately absent. ``in-progress``: the run doing the
#: checking has not published its own day yet, and reporting the currently
#: executing run as a delivery failure would be its own false claim.
#: ``unknown``: the day could not be read, and an unread day is not evidence of
#: a missed report -- it is the absence of evidence either way.
GAP_STATUSES = (MISSING, INVALID, UNPUBLISHED)

#: Structural allowlist for a Candystore event. Everything else in the envelope
#: -- actor, producer, delivery, artifact paths -- is dropped the moment the
#: payload is parsed, so no raw source object ever reaches the artifact.
EVENT_FIELDS = frozenset(
    {"id", "type", "time", "data", "run_id", "report_date", "outcome", "status", "sections"}
)
EVENT_OPAQUE = frozenset({"sections"})

#: Structural allowlist for a per-day record before it is rendered.
DAY_FIELDS = frozenset(
    {"date", "status", "reason", "generation", "events", "claimed", "run_ids", "cross_check"}
)


def _iso_z(moment: dt.datetime) -> str:
    return moment.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def _clip(text: Any, cap: int = REASON_CAP) -> str:
    value = " ".join(str(text).split())
    return value if len(value) <= cap else value[: cap - 3] + "..."


def _int_option(options: dict[str, Any], key: str, default: int, low: int, high: int,
                caveats: list[str]) -> int:
    raw = options.get(key, default)
    if isinstance(raw, bool) or not isinstance(raw, int) or not low <= raw <= high:
        if key in options:
            caveats.append(
                f"options.{key}={raw!r} is not an integer in [{low}, {high}]; used {default}"
            )
        return default
    return raw


def _candystore_url(options: dict[str, Any], caveats: list[str]) -> str:
    configured = options.get("candystore_url")
    base = (
        configured
        if isinstance(configured, str) and configured.strip()
        else DEFAULT_CANDYSTORE_URL
    )
    override = os.environ.get("CANDYSTORE_URL", "").strip()
    if override and override != base:
        caveats.append(f"CANDYSTORE_URL={override} overrode the configured {base}")
        base = override
    return base.rstrip("/")


def _window_days(report_date: dt.date, lookback: int) -> list[dt.date]:
    return [report_date - dt.timedelta(days=offset) for offset in range(lookback - 1, -1, -1)]


# --------------------------------------------------------------------------- #
# Source 1: this pipeline's own archive
# --------------------------------------------------------------------------- #


def _archive_usable(config: dict[str, Any]) -> str:
    """Return "" when the archive can be read, else why it cannot.

    A *nonexistent* archive root is readable and means "nothing was ever
    published" -- a finding, not a source failure. A root that is a file, or one
    the process cannot enter, is a source failure: reporting seven missing days
    from an unreadable directory would be an invention.
    """
    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in config]
    if missing:
        return f"config is missing {', '.join(missing)}; the archive cannot be located or validated"
    for key in ("artifact_dir", "archive_dir"):
        value = config[key]
        if not isinstance(value, str) or not value.strip():
            return f"config.{key} is not a path"
    root = Path(config["archive_dir"])
    if root.exists() and not root.is_dir():
        return f"archive_dir {root} exists but is not a directory"
    if root.is_dir() and not os.access(root, os.R_OK | os.X_OK):
        return f"archive_dir {root} is not readable"
    return ""


def _generations(archive_root: Path) -> list[str]:
    generations = archive_root / "generations"
    if not generations.is_dir():
        return []
    return sorted(
        entry.name
        for entry in generations.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


def _scan_day(config: dict[str, Any], day: str) -> dict[str, Any]:
    """Classify one day of the archive. Never trusts the pointer by itself."""
    paths = archive_paths(config, day)
    marker = Path(paths["commit_marker"])
    generations = _generations(Path(paths["archive_root"]))
    if not marker.exists():
        if generations:
            return {
                "date": day,
                "status": UNPUBLISHED,
                "reason": (
                    f"{len(generations)} generation(s) staged under {paths['archive_root']} "
                    "but current.json was never written; the publish transaction did not finish"
                ),
                "generation": "",
            }
        return {
            "date": day,
            "status": MISSING,
            "reason": f"no current.json and no staged generation under {paths['archive_root']}",
            "generation": "",
        }
    outcome = verify_published(config, day)
    if outcome.get("ok"):
        return {
            "date": day,
            "status": DELIVERED,
            "reason": "",
            "generation": Path(str(outcome.get("generation") or "")).name,
        }
    return {
        "date": day,
        "status": INVALID,
        "reason": _clip("; ".join(str(item) for item in outcome.get("problems", []))
                        or "current.json exists but the published generation did not verify"),
        "generation": Path(str(outcome.get("generation") or "")).name,
    }


def _scan_archive(config: dict[str, Any], days: list[str]) -> dict[str, dict[str, Any]]:
    scanned: dict[str, dict[str, Any]] = {}
    for day in days:
        try:
            scanned[day] = _scan_day(config, day)
        except Exception as exc:  # noqa: BLE001 - one bad day must not hide the others
            # UNKNOWN, not INVALID. The read failed, so nothing is known about
            # this day -- calling it invalid would invent a delivery failure out
            # of a permissions error, and (since findings no longer touch the
            # section status) would do it silently.
            scanned[day] = {
                "date": day,
                "status": UNKNOWN,
                "reason": _clip(f"archive check raised {type(exc).__name__}: {exc}"),
                "generation": "",
            }
    return scanned


# --------------------------------------------------------------------------- #
# Source 2: Candystore's audit trail
# --------------------------------------------------------------------------- #


def _fetch_page(url: str, timeout: int) -> Any:
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - localhost
        return json.loads(response.read().decode("utf-8"))


def _fetch_events(
    base_url: str, event_type: str, start: dt.datetime, end: dt.datetime, timeout: int
) -> tuple[list[dict[str, Any]] | None, str]:
    """Read completion events. Returns ``(None, reason)`` when Candystore fails.

    Read-only: a single filtered GET per page, no mutation of anything.
    """
    events: list[dict[str, Any]] = []
    for page in range(MAX_PAGES):
        query = urlencode(
            {
                "type": query_types(event_type),
                "from": _iso_z(start),
                "to": _iso_z(end),
                "limit": PAGE_SIZE,
                "offset": page * PAGE_SIZE,
            }
        )
        url = f"{base_url}/events?{query}"
        try:
            payload = _fetch_page(url, timeout)
        except urllib.error.HTTPError as exc:
            return None, _clip(f"{base_url} returned HTTP {exc.code} for /events")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return None, _clip(f"{base_url} is unreachable: {exc}")
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return None, _clip(f"{base_url} returned a non-JSON /events body: {exc}")
        except Exception as exc:  # noqa: BLE001 - an unread source is partial, never fatal
            return None, _clip(f"{base_url} read failed with {type(exc).__name__}: {exc}")
        if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
            return None, _clip(f"{base_url} returned an /events body without an events array")
        batch = [item for item in payload["events"] if isinstance(item, dict)]
        events.extend(
            allowlist(item, EVENT_FIELDS, opaque_keys=EVENT_OPAQUE) for item in batch
        )
        if len(payload["events"]) < PAGE_SIZE:
            return events, ""
    # Every page came back full. There may be more, and a cross-check against a
    # silently truncated event set would invent "missing" events. Refuse it.
    return None, _clip(
        f"{base_url} returned more than {MAX_PAGES * PAGE_SIZE} {event_type} events for the "
        "window; the page budget was exhausted, so the event set is incomplete"
    )


def _bucket_events(
    events: list[dict[str, Any]], days: set[str]
) -> tuple[dict[str, dict[str, Any]], int]:
    """Group allowlisted events by the day they claim to report on."""
    buckets: dict[str, dict[str, Any]] = {}
    unattributed = 0
    for event in events:
        data = event.get("data")
        data = data if isinstance(data, dict) else {}
        report_date = data.get("report_date")
        if not isinstance(report_date, str) or report_date not in days:
            if not isinstance(report_date, str):
                unattributed += 1
            continue
        outcome = data.get("outcome")
        outcome = outcome if isinstance(outcome, dict) else {}
        claimed = outcome.get("status")
        run_id = data.get("run_id")
        bucket = buckets.setdefault(report_date, {"count": 0, "claimed": [], "run_ids": []})
        bucket["count"] += 1
        if isinstance(claimed, str) and claimed not in bucket["claimed"]:
            bucket["claimed"].append(claimed)
        if isinstance(run_id, str) and len(bucket["run_ids"]) < 3:
            bucket["run_ids"].append(run_id)
    return buckets, unattributed


# --------------------------------------------------------------------------- #
# Cross-check
# --------------------------------------------------------------------------- #


def _cross_check(days: list[dict[str, Any]]) -> list[str]:
    """Stamp each day with its cross-check verdict; name every contradiction.

    Mutates ``day["cross_check"]`` in place and returns one line per
    disagreement, in window order. Both directions are defects and both are
    named: an event with no archive means the emitter claimed a report it never
    produced; an archive with no event means publication failed and nothing
    downstream can see the report exists.

    Each line carries both vocabularies -- the day-level label and the older
    ``event-without-archive`` / ``archive-without-event`` direction names -- so
    neither a human nor a grep can miss one for spelling it the other way.
    """
    found: list[str] = []
    for day in days:
        events = int(day.get("events") or 0)
        status = day["status"]
        if status == UNKNOWN:
            # No archive claim exists for this day, so no contradiction can be
            # established. Silence here, not a manufactured disagreement.
            day["cross_check"] = UNCHECKED
            continue
        claimed = ", ".join(day.get("claimed") or []) or "unstated"
        if events and status != DELIVERED:
            day["cross_check"] = EVENT_WITHOUT_ARCHIVE
            detail = (
                "this run has not published it yet" if status == IN_PROGRESS else status
            )
            found.append(
                f"DISAGREEMENT {day['date']} {EVENT_WITHOUT_ARCHIVE} "
                f"(event-without-archive): {events} completion "
                f"event(s) claim status {claimed}, but the archive says {detail} -- "
                "an earlier run reported success it did not achieve"
            )
        elif not events and status == DELIVERED:
            day["cross_check"] = ARCHIVE_WITHOUT_EVENT
            found.append(
                f"DISAGREEMENT {day['date']} {ARCHIVE_WITHOUT_EVENT} "
                "(archive-without-event): a valid report is "
                "published but no reporting.report.completed event reached Candystore -- "
                "event publication failed, so nothing downstream can see this report"
            )
        else:
            day["cross_check"] = AGREED
    return found


def _streak(days: list[dict[str, Any]]) -> int:
    """Consecutive delivered days, counting back from the newest *due* day.

    A day this run has not published yet is not due, so it neither extends nor
    breaks the streak. Any other non-delivered day breaks it.
    """
    streak = 0
    for day in reversed(days):
        if day["status"] == IN_PROGRESS:
            continue
        if day["status"] != DELIVERED:
            break
        streak += 1
    return streak


# --------------------------------------------------------------------------- #
# Collector
# --------------------------------------------------------------------------- #


def _collect(
    section_cfg: dict[str, Any], report_date: str, config: dict[str, Any]
) -> SectionResult:
    section_id = section_cfg.get("id") or SECTION_ID
    options = section_cfg.get("options")
    options = options if isinstance(options, dict) else {}
    caveats: list[str] = []

    try:
        target = dt.date.fromisoformat(report_date)
    except (TypeError, ValueError):
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"report_date {report_date!r} is not an ISO YYYY-MM-DD date",
            summary=f"{section_id}: cannot self-check without a valid report date",
        )

    lookback = _int_option(options, "lookback_days", DEFAULT_LOOKBACK_DAYS, 1, 90, caveats)
    timeout = _int_option(options, "http_timeout_seconds", DEFAULT_HTTP_TIMEOUT, 1, 60, caveats)
    event_type = options.get("event_type")
    if not isinstance(event_type, str) or not event_type.strip():
        event_type = DEFAULT_EVENT_TYPE
    base_url = _candystore_url(options, caveats)

    window = [day.isoformat() for day in _window_days(target, lookback)]
    window_set = set(window)

    # ---- source 1: the archive -------------------------------------------- #
    archive_error = _archive_usable(config)
    scanned = {} if archive_error else _scan_archive(config, window)
    archive_ok = not archive_error
    if archive_ok:
        root = Path(config["archive_dir"])
        if not root.exists():
            caveats.append(
                f"archive root {root} does not exist; no report has ever been published there"
            )

    # ---- source 2: Candystore --------------------------------------------- #
    start = dt.datetime.combine(target - dt.timedelta(days=lookback), dt.time.min, tzinfo=dt.UTC)
    end = dt.datetime.combine(target + dt.timedelta(days=2), dt.time.min, tzinfo=dt.UTC)
    events, events_error = _fetch_events(base_url, event_type, start, end, timeout)
    buckets, unattributed = ({}, 0) if events is None else _bucket_events(events, window_set)
    events_ok = events is not None
    if unattributed:
        caveats.append(
            f"{unattributed} {event_type} event(s) carry no data.report_date and could not be "
            "attributed to a day"
        )

    # ---- merge ------------------------------------------------------------- #
    days: list[dict[str, Any]] = []
    for day in window:
        record = dict(
            scanned.get(day)
            or {"date": day, "status": UNKNOWN, "reason": "", "generation": ""}
        )
        if day == report_date and archive_ok and record["status"] == MISSING:
            record["status"] = IN_PROGRESS
            record["reason"] = "this run is producing this day; it publishes after collection"
        bucket = buckets.get(day, {})
        record["events"] = int(bucket.get("count", 0)) if events_ok else 0
        record["claimed"] = list(bucket.get("claimed", []))
        record["run_ids"] = list(bucket.get("run_ids", []))
        record["cross_check"] = UNCHECKED
        days.append(allowlist(record, DAY_FIELDS))

    tally = {status: 0 for status in (DELIVERED, MISSING, INVALID, UNPUBLISHED, IN_PROGRESS)}
    for record in days:
        tally[record["status"]] = tally.get(record["status"], 0) + 1
    duplicates = [record["date"] for record in days if record["events"] > 1]
    if events_ok and duplicates:
        caveats.append(
            "duplicate completion events for " + ", ".join(duplicates)
            + "; more than one run claimed the same day"
        )

    cross_checked = archive_ok and events_ok
    disagreements = _cross_check(days) if cross_checked else []
    for line in disagreements[:MAX_DISAGREEMENT_CAVEATS]:
        caveats.append(line)
    if len(disagreements) > MAX_DISAGREEMENT_CAVEATS:
        caveats.append(
            f"{len(disagreements) - MAX_DISAGREEMENT_CAVEATS} further disagreement(s) are in detail"
        )

    # ---- the delivery verdict ---------------------------------------------- #
    # A day the run is currently producing is not due yet, so it is excluded
    # from the gap count: the executing run must never be reported as its own
    # delivery failure.
    unreadable_days = [record["date"] for record in days if record["status"] == UNKNOWN]
    # A day the archive could not be read for is not due, not delivered, and not
    # a gap. It is unknown, and every ratio has to say so rather than absorb it.
    due = (
        (len(window) - tally[IN_PROGRESS] - len(unreadable_days)) if archive_ok else len(window)
    )
    gaps = sum(tally[name] for name in GAP_STATUSES) if archive_ok else 0
    event_without_archive = sum(
        1 for record in days if record["cross_check"] == EVENT_WITHOUT_ARCHIVE
    )
    archive_without_event = sum(
        1 for record in days if record["cross_check"] == ARCHIVE_WITHOUT_EVENT
    )

    problems: list[str] = []
    if gaps:
        named = [
            f"{tally[name]} {label}"
            for name, label in (
                (MISSING, "missing"),
                (INVALID, "invalid"),
                (UNPUBLISHED, "archived but never published"),
            )
            if tally[name]
        ]
        problems.append(
            f"{gaps} of {due} due day(s) in {window[0]}..{window[-1]} have no valid published "
            f"report ({', '.join(named)})"
        )
    if event_without_archive:
        problems.append(
            f"{event_without_archive} day(s) carry a completion event with no archived report "
            "-- an earlier run reported success it did not achieve"
        )
    if archive_without_event:
        problems.append(
            f"{archive_without_event} day(s) are archived with no completion event in "
            "Candystore -- event publication failed"
        )

    if not archive_ok or not due:
        # Nothing could be assessed: either the archive was unreadable, or every
        # day in the window was unreadable or not yet due. "ok" over that would
        # be a verdict nobody reached.
        delivery_health = UNKNOWN
    elif problems:
        delivery_health = "failed" if not tally[DELIVERED] else "degraded"
    else:
        delivery_health = "ok"

    # The verdict leads the caveat list, ahead of the per-day disagreement lines
    # and any option notes. ``risks-watchlist`` renders the first 20 caveats of
    # every section, so a headline placed here reaches the top of the document
    # whatever else this collector recorded.
    caveats[:0] = [f"DELIVERY {delivery_health.upper()}: {problem}" for problem in problems]

    # ---- status: could this collector do its job? -------------------------- #
    # Only source readability may touch it. What the sources SAID -- six missing
    # days, five phantom completion events -- is the finding, and a finding is
    # the job done, not the job failed. See the module docstring for the latch
    # this rule exists to prevent.
    unread: list[str] = []
    if unreadable_days:
        shown = ", ".join(unreadable_days[:5])
        more = f" and {len(unreadable_days) - 5} more" if len(unreadable_days) > 5 else ""
        unread.append(
            f"{len(unreadable_days)} day(s) could not be read from the archive "
            f"({shown}{more}); no delivery claim is made about them"
        )
    if not events_ok:
        unread.append(f"Candystore not read: {events_error}")

    if not archive_ok:
        status = "failed"
        reason = _clip(
            f"the archive could not be read, so no claim about any day is possible: "
            f"{archive_error}"
            + ("" if events_ok else f"; Candystore not read either: {events_error}"),
            1200,
        )
    elif unread:
        status = "partial"
        reason = _clip(
            "; ".join(unread) + "; what was read is reported in full below",
            1200,
        )
    else:
        status, reason = "complete", ""

    unknown = UNKNOWN
    metrics: dict[str, Any] = {
        "days_checked": len(window),
        "days_delivered": tally[DELIVERED] if archive_ok else unknown,
        "days_missing": tally[MISSING] if archive_ok else unknown,
        "days_invalid": tally[INVALID] if archive_ok else unknown,
        "days_unpublished_but_archived": tally[UNPUBLISHED] if archive_ok else unknown,
        "days_in_progress": tally[IN_PROGRESS] if archive_ok else unknown,
        "days_unreadable": len(unreadable_days) if archive_ok else unknown,
        "days_event_without_archive": event_without_archive if cross_checked else unknown,
        "days_archive_without_event": archive_without_event if cross_checked else unknown,
        "delivery_gaps": gaps if archive_ok else unknown,
        "delivery_health": delivery_health,
        "events_found": sum(record["events"] for record in days) if events_ok else unknown,
        "archive_event_disagreements": len(disagreements) if cross_checked else unknown,
        "consecutive_delivered_streak": _streak(days) if archive_ok else unknown,
        "lookback_days": lookback,
        "archive_readable": archive_ok,
        "candystore_reachable": events_ok,
    }

    detail: list[str] = [
        f"window {window[0]}..{window[-1]} ({len(window)} days), report_date {report_date}",
        f"delivery health {delivery_health}"
        + (": " + "; ".join(problems) if problems else ""),
        f"archive {config.get('archive_dir', '(unset)')}: "
        + ("readable" if archive_ok else f"UNREADABLE - {archive_error}"),
        f"candystore {base_url} type={event_type}: "
        + ("reachable" if events_ok else f"UNREACHABLE - {events_error}"),
    ]
    for record in days:
        parts = [record["date"], record["status"]]
        if events_ok:
            parts.append(f"events={record['events']}")
            if record["claimed"]:
                parts.append("claimed=" + ",".join(record["claimed"]))
        if record["cross_check"] not in (AGREED, UNCHECKED):
            parts.append(f"cross_check={record['cross_check']}")
        if record["generation"]:
            parts.append(f"generation={record['generation']}")
        if record["reason"]:
            parts.append(f"reason={record['reason']}")
        detail.append(" ".join(parts))
    detail.extend(disagreements)

    if status == "failed":
        summary = (
            f"{section_id}: delivery could not be checked -- the archive could not be read "
            f"for {window[0]}..{window[-1]}, so this section makes no claim about any day"
        )
    else:
        delivered = tally[DELIVERED]
        # The verdict first. A reader who stops after one clause must still have
        # been told the pipeline is missing days.
        headline = (
            f"DELIVERY {delivery_health.upper()} -- " + "; ".join(problems) + ". "
            if problems
            else ""
        )
        summary = (
            f"{section_id}: {headline}"
            f"{delivered} of {due} due days delivered over {window[0]}..{window[-1]}"
            f" ({gaps} gap(s)); "
            + (
                f"{metrics['events_found']} completion event(s), "
                f"{metrics['archive_event_disagreements']} archive/event disagreement(s)"
                if events_ok
                else "Candystore not read, so no cross-check was possible"
            )
            + f"; delivered streak {metrics['consecutive_delivered_streak']}."
        )

    return SectionResult(
        id=section_id,
        status=status,
        reason=reason,
        summary=summary,
        metrics=metrics,
        detail=detail,
        caveats=caveats,
    )


def collect(
    section_cfg: dict[str, Any],
    report_date: str,
    config: dict[str, Any] | None = None,
    *,
    date: str | None = None,
) -> SectionResult:
    """Collect the report-delivery self-check. Never raises to the caller."""
    section_id = SECTION_ID
    try:
        if isinstance(section_cfg, dict) and isinstance(section_cfg.get("id"), str):
            section_id = section_cfg["id"]
        return _collect(
            section_cfg if isinstance(section_cfg, dict) else {},
            report_date if isinstance(report_date, str) else (date or ""),
            config if isinstance(config, dict) else {},
        )
    except Exception as exc:  # noqa: BLE001 - a crash degrades the report, never aborts it
        return SectionResult(
            id=section_id,
            status="failed",
            reason=_clip(f"{type(exc).__name__}: {exc}"),
            summary=f"{section_id}: self-check raised {type(exc).__name__}",
        )


# --------------------------------------------------------------------------- #
# Standalone entry point
# --------------------------------------------------------------------------- #


def _resolve_config(explicit: str | None) -> tuple[dict[str, Any], list[str], list[str]]:
    if explicit:
        candidates = [Path(explicit).expanduser()]
    else:
        candidates = []
        env = os.environ.get("DELONET_REPORT_CONFIG", "").strip()
        if env:
            candidates.append(Path(env).expanduser())
        candidates.extend([LIVE_CONFIG.expanduser(), EXAMPLE_CONFIG])
    errors: list[str] = []
    for path in candidates:
        try:
            config = load_config(path)
        except (ConfigError, OSError, ValueError) as exc:
            errors.append(_clip(f"{path}: {exc}", 200))
            continue
        caveats = (
            [f"config {path} used after earlier candidates failed: {'; '.join(errors)}"]
            if errors
            else []
        )
        return config, caveats, []
    return {}, [], errors


def _resolve_section(config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    for section in config.get("sections", []) if isinstance(config, dict) else []:
        if isinstance(section, dict) and (
            section.get("id") == SECTION_ID or section.get("collector") == "report_delivery"
        ):
            return section, []
    return (
        {"id": SECTION_ID, "title": "Daily Report and Delivery Health", "options": {},
         "max_age_hours": 24},
        [f"config declares no {SECTION_ID} section; collector defaults were used"],
    )


def _fallback_artifact(section_id: str, run_id: str, reason: str) -> dict[str, Any]:
    now = _iso_z(dt.datetime.now(dt.UTC))
    return {
        "schema_version": 2,
        "run_id": run_id,
        "topic_id": section_id,
        "generated_at": now,
        "fresh_until": now,
        "status": "failed",
        "reason": _clip(reason),
        "summary": f"{section_id}: could not build a section artifact",
        "caveats": ["artifact construction failed; this record exists so the gap is visible"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="collectors.report_delivery",
        description=(
            "Self-check the daily report pipeline: archive delivery vs Candystore completion "
            "events. Prints one SectionArtifact as JSON on stdout."
        ),
        epilog=(
            "The exit code answers 'could the check run', not 'is delivery healthy': 0 when "
            "both sources were read, 1 when one could not be (partial) or the archive could "
            "not be (failed). A window full of undelivered days is a SUCCESSFUL check with "
            "bad news, so it exits 0 -- read metrics.delivery_health for the verdict, which "
            "is also written to stderr whenever it is not ok."
        ),
    )
    parser.add_argument(
        "--date",
        default=(dt.date.today() - dt.timedelta(days=1)).isoformat(),
        help="report date (YYYY-MM-DD); defaults to yesterday",
    )
    parser.add_argument("--config", help="operator config; defaults to the live config")
    parser.add_argument("--run-id", help="reuse an existing run identifier")
    args = parser.parse_args(argv)

    config, caveats, errors = _resolve_config(args.config)
    section_cfg, section_caveats = _resolve_section(config)
    caveats = caveats + section_caveats
    if errors:
        caveats.append("no usable config: " + "; ".join(errors))

    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = args.run_id or f"standalone-{stamp}-{uuid.uuid4().hex[:8]}"
    result = run_collector(lambda cfg: collect(cfg, args.date, config), section_cfg)
    result.caveats = caveats + list(result.caveats)

    max_age = section_cfg.get("max_age_hours") or config.get("max_age_hours") or 24
    try:
        artifact = result.to_artifact(run_id, int(max_age))
    except Exception as exc:  # noqa: BLE001 - never exit without an honest record
        artifact = _fallback_artifact(result.id, run_id, f"{type(exc).__name__}: {exc}")
    print(json.dumps(artifact, indent=2, sort_keys=True))
    # Two facts, two channels. stdout is the artifact; the delivery verdict goes
    # to stderr so an operator watching a terminal is never left with exit 0 as
    # the only thing they saw about a pipeline that is missing days.
    health = (artifact.get("metrics") or {}).get("delivery_health")
    if health != "ok":
        print(f"delivery health {health}: {artifact['summary']}", file=sys.stderr)
    return 0 if artifact["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
