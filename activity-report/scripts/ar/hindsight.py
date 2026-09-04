"""Hindsight: list/recall for the digest, retain for the finished report.

Hindsight is colour, never truth. Nothing here decides a count; everything it
returns is an aside for the compose agent, and every failure degrades to
`status: unavailable` with a caveat instead of stopping the run. Memories the
skill wrote itself (context `activity-report:<audience>`) are excluded from
the listing so a report never quotes the previous report back as a fact.

Retain is the one write, and it is verified: the CLI's "Stored 1 memory units"
counts documents, not facts, so the document's memory_unit_count is read back
and an empty extraction is retried under the same id.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .common import AUDIENCES, AcceptanceError, ConfigError, eprint, parse_iso, read_json, to_iso_z
from .config import hindsight_bank, load_project
from .render import parse, split_raw, to_prose

HINDSIGHT_BIN = os.environ.get("HINDSIGHT_BIN", "hindsight")
CONTEXT_PREFIX = "activity-report:"
LIST_PAGE = 200
LIST_MAX_PAGES = 5
ITEM_CAP = 40
RECALL_CAP = 20
TEXT_CHARS = 500
LIST_TIMEOUT = 60
RECALL_TIMEOUT = 120
RETAIN_TIMEOUT = 120


class HindsightFailed(Exception):
    pass


def _run(args: list[str], timeout: int) -> str:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise HindsightFailed(f"{args[0]} is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise HindsightFailed(f"{' '.join(args[:3])} timed out after {timeout}s") from exc
    except OSError as exc:
        raise HindsightFailed(f"{' '.join(args[:3])}: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        raise HindsightFailed(f"{' '.join(args[:3])} exited {proc.returncode}: {detail[-1][:200] if detail else 'no output'}")
    return proc.stdout


def _json(text: str):
    try:
        return json.loads(text)
    except ValueError as exc:
        raise HindsightFailed("hindsight returned non-JSON output") from exc


def _text_of(item: dict) -> str | None:
    for name in ("text", "content", "fact", "memory"):
        value = item.get(name)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return None


def _when(item: dict):
    for name in ("date", "occurred_start", "mentioned_at", "created_at"):
        value = item.get(name)
        if isinstance(value, str) and value:
            try:
                return parse_iso(value)
            except ValueError:
                continue
    return None


def _list(bank: str, window) -> tuple[list[dict], int]:
    """Memories recorded inside the window, newest first; (items, scanned)."""
    items: list[dict] = []
    offset = scanned = 0
    for _ in range(LIST_MAX_PAGES):
        out = _run([HINDSIGHT_BIN, "memory", "list", bank, "-o", "json", "-l", str(LIST_PAGE), "-s", str(offset)], LIST_TIMEOUT)
        body = _json(out)
        batch = body.get("items") if isinstance(body, dict) else body
        if not isinstance(batch, list):
            raise HindsightFailed("hindsight memory list returned no items list")
        for item in batch:
            if not isinstance(item, dict):
                continue
            scanned += 1
            if item.get("invalidated_at"):
                continue
            context = item.get("context")
            if isinstance(context, str) and context.startswith(CONTEXT_PREFIX):
                continue
            at = _when(item)
            text = _text_of(item)
            if at is None or text is None or not (window.start <= at < window.end):
                continue
            items.append({"at": to_iso_z(at), "fact_type": item.get("fact_type") if isinstance(item.get("fact_type"), str) else None,
                          "text": text[:TEXT_CHARS]})
        offset += len(batch)
        total = body.get("total") if isinstance(body, dict) else None
        if not batch or len(batch) < LIST_PAGE or (isinstance(total, int) and offset >= total):
            break
        dates = [d for d in (_when(i) for i in batch if isinstance(i, dict)) if d is not None]
        if dates and dates == sorted(dates, reverse=True) and dates[-1] < window.start:
            break   # the listing is newest-first and this page already passed the window
    items.sort(key=lambda i: i["at"], reverse=True)
    return items, scanned


def _recall(bank: str, query: str) -> list[str]:
    out = _run([HINDSIGHT_BIN, "memory", "recall", bank, query, "-o", "json", "--budget", "high", "--max-tokens", "2048"],
               RECALL_TIMEOUT)
    body = _json(out)
    results = body.get("results") if isinstance(body, dict) else body
    if not isinstance(results, list):
        return []
    texts: list[str] = []
    for item in results:
        text = _text_of(item) if isinstance(item, dict) else (item if isinstance(item, str) else None)
        if text and text[:TEXT_CHARS] not in texts:
            texts.append(text[:TEXT_CHARS])
        if len(texts) >= RECALL_CAP:
            break
    return texts


def collect(project, window) -> dict:
    """The digest "hindsight" block. Never raises."""
    cfg = project.config.get("hindsight") or {}
    caveats: list[str] = []
    try:
        bank = hindsight_bank(project)
    except ConfigError as exc:
        return {"bank": None, "status": "unavailable", "items": [], "recall": {"query": None, "items": []},
                "caveats": [f"hindsight: {exc}"]}
    block = {"bank": bank, "status": "ok", "items": [], "recall": {"query": None, "items": []}, "caveats": caveats}
    if cfg.get("recall") is False:
        block["status"] = "disabled"
        return block
    list_ok = recall_ok = False
    try:
        items, _scanned = _list(bank, window)
        if len(items) > ITEM_CAP:
            caveats.append(f"hindsight items capped at {ITEM_CAP} of {len(items)}")
        block["items"] = items[:ITEM_CAP]
        list_ok = True
    except (HindsightFailed, Exception) as exc:  # noqa: BLE001 - colour never stops the run
        caveats.append(f"hindsight list failed: {exc}")
    query = (f"what changed for {project.name} between {to_iso_z(window.start)} and {to_iso_z(window.end)}: "
             "wins, blockers, decisions")
    block["recall"]["query"] = query
    try:
        block["recall"]["items"] = _recall(bank, query)
        recall_ok = True
    except (HindsightFailed, Exception) as exc:  # noqa: BLE001
        caveats.append(f"hindsight recall failed: {exc}")
    if not list_ok and not recall_ok:
        block["status"] = "unavailable"
    return block


AUDIENCE_WORD = {"internal": "Internal", "external": "Client-facing"}
RETAIN_TRIES = 3
RETAIN_BACKOFF = (20, 40)      # seconds before the second and the third try
DOCUMENT_TIMEOUT = 30
FLOOR_WORDS = 150              # a retain must store at least one unit per this many words


def _bounds(window) -> tuple[datetime | None, datetime | None]:
    """(start, end) as aware datetimes from a Window, a digest window dict, or a bare end value."""
    if isinstance(window, dict):
        start, end = window.get("start"), window.get("end")
    else:
        start, end = getattr(window, "start", None), getattr(window, "end", window)

    def as_dt(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return parse_iso(value)
            except ValueError:
                return None
        return None
    return as_dt(start), as_dt(end)


def timeline_dater(start, end, tz: str):
    """A function from a project-local `HH:MM` to the calendar date it belongs
    to inside the window, so a timeline fact carries its own date instead of
    depending on the lead sentence. One date when the window sits inside a
    day; across one midnight a clock at or after the window's own start clock
    is the first day and an earlier one the second (the timeline is in order
    and the window is at most a day). Longer windows return None and the
    sentence keeps its bare clock."""
    if start is None or end is None:
        return lambda at: None
    try:
        zone = ZoneInfo(tz)
    except Exception:  # noqa: BLE001 - validated at config time; never fail a retain over it
        return lambda at: None
    first, last = start.astimezone(zone), end.astimezone(zone)
    span = (last.date() - first.date()).days
    start_clock = first.hour * 60 + first.minute

    def date_for(at: str) -> str | None:
        try:
            hours, minutes = at.split(":")
            clock = int(hours) * 60 + int(minutes)
        except ValueError:
            return None
        if span == 0:
            return first.date().isoformat()
        if span == 1:
            return (first.date() if clock >= start_clock else last.date()).isoformat()
        return None
    return date_for


def retain_text(project, audience: str, raw_text: str, window) -> str:
    """The prose rendition Hindsight is given (see render.to_prose); raw.txt
    itself only when it does not parse as a report."""
    try:
        title, body = split_raw(raw_text)
    except AcceptanceError:
        return raw_text
    start, end = _bounds(window)
    when = to_iso_z(end) if end is not None else "unknown"
    name = getattr(project, "name", None) or project.slug
    lead = (f"{AUDIENCE_WORD.get(audience, audience)} activity report for {name} ({project.slug}), "
            f"window ending {when}")
    return to_prose(title, parse(body), lead=lead, dates=timeline_dater(start, end, getattr(project, "tz", "UTC")))


def doc_id_for(project, audience: str, label: str) -> str:
    """One Hindsight document per window. A re-run of the same window replaces
    it (Hindsight's default update_mode), and a retry after an empty
    extraction re-extracts in full: the delta skip only covers chunks a
    successful retain stored, and a zero-fact retain stores none."""
    return f"{CONTEXT_PREFIX}{project.slug}:{audience}:{label}"


def retain_audiences(project) -> list[str]:
    """Which audiences are written to memory; internal only unless configured.
    The client-facing text is spin by design and is not the record."""
    value = (project.config.get("hindsight") or {}).get("retain_audiences")
    return [a for a in value if a in AUDIENCES] if isinstance(value, list) else ["internal"]


def unit_count(bank: str, doc_id: str) -> int | None:
    """memory_unit_count of a document: the only truthful measure of a retain.
    The CLI answers "Stored 1 memory units" for an extraction that stored none."""
    body = _json(_run([HINDSIGHT_BIN, "document", "get", bank, doc_id, "-o", "json"], DOCUMENT_TIMEOUT))
    count = body.get("memory_unit_count") if isinstance(body, dict) else None
    return count if isinstance(count, int) and not isinstance(count, bool) else None


def unit_floor(text: str) -> int:
    """The fewest memory units a retain of `text` may store and count as a
    retain. Zero is not the only failure: the same 767-word report stored 2,
    21, 4 and 23 units on four consecutive tries (2026-09-04), and 2 facts
    from a day's report is an extraction that quit, not a quiet day."""
    return max(1, len(text.split()) // FLOOR_WORDS)


def retain(project, audience: str, raw_text: str, window, label: str, tries: int = RETAIN_TRIES,
           sleep=time.sleep) -> dict:
    """Store the report, as prose, in the project's bank and verify it landed
    as facts. Never raises; every failure is a warning and `retained: False`.

    Hindsight's extractor answers with zero facts on a fair share of calls
    (measured 2026-09-03/04 on this host: a quarter to a half of all retains),
    so one retain is not a retain. Each try re-retains the same document id
    and reads memory_unit_count back; the run moves on after `tries` empties.
    """
    result = {"retained": False, "bank": None, "doc_id": None, "units": None, "floor": None, "attempts": 0, "reason": None}
    cfg = project.config.get("hindsight") or {}
    if cfg.get("retain") is False:
        result["reason"] = "hindsight.retain is false"
    elif audience not in retain_audiences(project):
        result["reason"] = f"{audience} is not in hindsight.retain_audiences {retain_audiences(project)}"
    elif not isinstance(raw_text, str) or not raw_text.strip():
        result["reason"] = "empty report text"
    if result["reason"]:
        eprint(f"activity-report: retain skipped: {result['reason']}")
        return result
    try:
        bank = hindsight_bank(project)
    except ConfigError as exc:
        result["reason"] = str(exc)
        eprint(f"activity-report: retain skipped: {exc}")
        return result
    _start, end = _bounds(window)
    doc_id = doc_id_for(project, audience, label)
    result.update({"bank": bank, "doc_id": doc_id})
    text = retain_text(project, audience, raw_text, window)
    result["floor"] = floor = unit_floor(text)
    args = [HINDSIGHT_BIN, "memory", "retain", bank, text, "--context", f"{CONTEXT_PREFIX}{audience}", "--doc-id", doc_id]
    if end is not None:
        args += ["--timestamp", to_iso_z(end)]
    tries = max(1, int(tries or 1))
    for attempt in range(1, tries + 1):
        result["attempts"] = attempt
        if attempt > 1:
            sleep(RETAIN_BACKOFF[min(attempt - 2, len(RETAIN_BACKOFF) - 1)])
        try:
            _run(args, RETAIN_TIMEOUT)
        except (HindsightFailed, Exception) as exc:  # noqa: BLE001 - memory never stops the run
            result["reason"] = str(exc)
            eprint(f"activity-report: retain try {attempt}/{tries} failed: {exc}")
            continue
        try:
            units = unit_count(bank, doc_id)
        except (HindsightFailed, Exception) as exc:  # noqa: BLE001
            result["reason"] = f"stored, but the unit count could not be read: {exc}"
            eprint(f"activity-report: retain (warning): {result['reason']}")
            return result
        result["units"] = units
        if units is None:
            result["reason"] = "stored, but the document reports no memory_unit_count"
            eprint(f"activity-report: retain (warning): {result['reason']}")
            return result
        if units >= floor:
            result.update({"retained": True, "reason": None})
            return result
        result["reason"] = f"extraction stored {units} units (floor {floor}) on try {attempt}/{tries}"
        eprint(f"activity-report: retain try {attempt}/{tries}: {units} units for {doc_id}, floor {floor}")
    eprint(f"activity-report: retain failed (warning): {result['reason']} (the event is published; memory is not)")
    return result


def retain_cmd(args) -> int:
    project = load_project(args.project)
    try:
        with open(args.raw, encoding="utf-8") as fh:
            raw_text = fh.read()
    except OSError as exc:
        raise ConfigError(f"cannot read {args.raw}: {exc}") from exc
    try:
        digest = read_json(args.digest)
    except (OSError, ValueError) as exc:
        raise ConfigError(f"cannot read digest {args.digest}: {exc}") from exc
    if not isinstance(digest, dict) or not isinstance(digest.get("window"), dict) or not digest.get("label"):
        raise ConfigError(f"{args.digest} is not a digest (no window/label)")
    if digest.get("audience") != args.audience:
        raise ConfigError(f"{args.digest} is a {digest.get('audience')} digest, not {args.audience}")
    tries = int(getattr(args, "tries", RETAIN_TRIES) or RETAIN_TRIES)
    result = retain(project, args.audience, raw_text, digest["window"], digest["label"], tries=tries)
    if args.json:
        print(json.dumps(result))
    elif result["retained"]:
        print(f"retained  {result['bank']}  {result['doc_id']}  units={result['units']} (floor {result['floor']})  tries={result['attempts']}")
    elif result["doc_id"]:
        print(f"retain    NOT verified for {result['doc_id']}: {result['reason']}")
    else:
        print(f"retain    skipped: {result['reason']}")
    # Warning-level for the runner (it logs a non-zero exit and goes on), but a
    # hand repair should see the failure in its exit code.
    return 0 if result["retained"] or not result["doc_id"] else 1
