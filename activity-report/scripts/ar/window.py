"""Window resolution: from the previous same-audience report to now, capped.

The previous report is the newest non-dry-run
`bloodbank.project.activity.recorded` event in Candystore for this slug and
audience. Its `window.end` is where the new window starts, unless that lies
further back than `window.cap_hours`, in which case the cap wins and the
digest says so. `--since` / `--until` make an explicit window that does not
chain. Candystore being down is fatal here too: without it the boundary is
unknowable, and a guessed window double-reports or drops a day.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from . import candystore
from .common import AUDIENCES, ConfigError, NothingToDo, label_for, parse_iso, to_iso_z, utc_now
from .config import load_project

BASIS_PREVIOUS = "previous_report"
BASIS_CAP = "cap_24h"
BASIS_EXPLICIT = "explicit"
CAP_24H_SECONDS = 86400


@dataclass
class Window:
    start: datetime
    end: datetime
    basis: str
    previous_event_id: str | None
    previous: dict | None
    caveats: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> int:
        return int((self.end - self.start).total_seconds())

    def label(self, tz: str) -> str:
        return label_for(self.end, tz)

    def as_dict(self) -> dict:
        return {
            "start": to_iso_z(self.start),
            "end": to_iso_z(self.end),
            "duration_seconds": self.duration_seconds,
            "basis": self.basis,
            "previous_event_id": self.previous_event_id,
        }


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0)


def _parse_flag(value: str, flag: str) -> datetime:
    try:
        return _utc(parse_iso(value))
    except ValueError as exc:
        raise ConfigError(f"{flag} {value!r} is not an ISO-8601 timestamp") from exc


def resolve(project, audience: str, now: datetime | None = None, since: str | None = None,
            until: str | None = None, force: bool = False) -> Window:
    """Raises NothingToDo when the window is shorter than window.min_minutes (unless force)."""
    if audience not in AUDIENCES:
        raise ConfigError(f"audience must be one of {list(AUDIENCES)}, got {audience!r}")
    now = _utc(now) if now is not None else utc_now()
    cfg = project.config.get("window") or {}
    cap_hours = float(cfg.get("cap_hours") or 24)
    min_minutes = int(cfg.get("min_minutes") or 0)
    cap = timedelta(hours=cap_hours)
    caveats: list[str] = []

    end = _parse_flag(until, "--until") if until else now
    previous = candystore.find_previous_report(project.slug, audience, now)
    prev_end = _utc(parse_iso(previous["window_end"])) if previous else None
    prev_id = previous.get("event_id") if previous else None

    if since:
        start = _parse_flag(since, "--since")
        basis = BASIS_EXPLICIT
        if prev_end is not None and start > prev_end:
            caveats.append(f"explicit window starts after the previous {audience} report ended ({to_iso_z(prev_end)}); "
                           "the gap between them is not covered")
        elif prev_end is not None and start < prev_end:
            caveats.append(f"explicit window overlaps the previous {audience} report (ended {to_iso_z(prev_end)})")
    elif until:
        cap_start = end - cap
        basis = BASIS_EXPLICIT
        if prev_end is not None and cap_start <= prev_end < end:
            start = prev_end
        else:
            start = cap_start
            if prev_end is None:
                caveats.append(f"no previous {audience} report within {candystore.PREVIOUS_LOOKBACK_DAYS} days; "
                               f"window is the {cap_hours:g} h cap before --until")
            else:
                caveats.append(f"previous {audience} report ended {to_iso_z(prev_end)}, outside the {cap_hours:g} h cap "
                               "before --until; window is the cap")
    else:
        cap_start = end - cap
        if prev_end is not None and prev_end > now - timedelta(seconds=1):
            caveats.append(f"previous {audience} report ends at {to_iso_z(prev_end)}, which is not before now; "
                           "start clamped to one second ago")
            prev_end = now - timedelta(seconds=1)
        if prev_end is not None and prev_end >= cap_start:
            start, basis = prev_end, BASIS_PREVIOUS
        else:
            start = cap_start
            if int(cap.total_seconds()) == CAP_24H_SECONDS:
                basis = BASIS_CAP
            else:
                basis = BASIS_EXPLICIT
                caveats.append(f"window is the configured cap of {cap_hours:g} h; basis recorded as explicit because "
                               "cap_24h means exactly 24 h")
            if prev_end is None:
                caveats.append(f"no previous {audience} report within {candystore.PREVIOUS_LOOKBACK_DAYS} days; "
                               f"window is the {cap_hours:g} h cap")
            else:
                caveats.append(f"previous {audience} report ended {to_iso_z(prev_end)}, older than the {cap_hours:g} h cap; "
                               "window is the cap and the gap since then is not covered")

    if end <= start:
        raise ConfigError(f"window end {to_iso_z(end)} is not after start {to_iso_z(start)}")
    duration = int((end - start).total_seconds())
    if duration < min_minutes * 60:
        if not force:
            raise NothingToDo(f"window {to_iso_z(start)} -> {to_iso_z(end)} is {duration}s, shorter than "
                              f"window.min_minutes={min_minutes}; pass --force to report anyway")
        caveats.append(f"window is {duration}s, shorter than window.min_minutes={min_minutes}; forced")

    # Lineage only when this window continues the previous report; an explicit
    # window that happens to start where it ended still records no previous id.
    previous_event_id = prev_id if basis == BASIS_PREVIOUS and isinstance(prev_id, str) else None
    return Window(start=start, end=end, basis=basis, previous_event_id=previous_event_id,
                  previous=previous, caveats=caveats)


def window_cmd(args) -> int:
    project = load_project(args.project)
    window = resolve(project, args.audience, since=args.since, until=args.until, force=args.force)
    label = window.label(project.tz)
    previous = None
    if window.previous:
        previous = {"event_id": window.previous.get("event_id"), "window_end": window.previous.get("window_end"),
                    "title": window.previous.get("title")}
    if args.json:
        print(json.dumps({"project": project.slug, "audience": args.audience, "window": window.as_dict(),
                          "label": label, "previous_report": previous, "caveats": window.caveats}, indent=2))
        return 0
    print(f"window    {to_iso_z(window.start)} -> {to_iso_z(window.end)}  ({window.duration_seconds}s, basis {window.basis})")
    print(f"label     {label}  (tz {project.tz})")
    if previous:
        print(f"previous  {previous['event_id']}  ended {previous['window_end']}  {previous['title'] or ''}".rstrip())
    else:
        print(f"previous  none within {candystore.PREVIOUS_LOOKBACK_DAYS} days")
    for caveat in window.caveats:
        print(f"caveat    {caveat}")
    return 0
