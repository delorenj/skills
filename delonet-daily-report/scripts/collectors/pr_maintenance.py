"""Nightly PR maintenance, read straight from pr-crusher's durable state.

pr-crusher keeps a versioned state tree under ``~/.local/state/pr-crusher``::

    repos/<slug>/summary.json              the most recent tick, in full
    repos/<slug>/journal.json              append-only run history
    repos/<slug>/runs/tick-*/summary.json  one file per tick, subject to retention

Those files are the source of record here because **pr-crusher's Bloodbank
publisher is switched off**: its lifecycle entries carry
``publish_status: "skipped"`` with ``detail: "publisher disabled"``, so none of
this activity reaches Candystore. Every run says so in ``caveats`` -- silence in
the event bus means "not published", never "nothing happened".

Three outcomes are kept strictly apart, because collapsing them is the bug class
this pipeline exists to kill:

* **did not run** -- state is readable and no tick completed inside the window.
  ``status="complete"``; the summary says pr-crusher did not run.
* **ran and found nothing** -- ticks completed and triaged no pull requests.
  ``status="complete"``; the summary says so and names the ticks.
* **state unreadable** -- the tree, a repository, or a tick file could not be
  read. ``status="failed"`` when nothing could be read, ``status="partial"``
  when only part could, always with a reason naming what was missing.

Section status describes *this collector's* data completeness, not pr-crusher's
health. A tick whose provider failed is reported loudly in the summary and the
detail, but it does not make the section ``failed``: the collector read that
failure successfully, and burying a successful read of bad news under a failed
status is just a different lie.

The collector is read-only. It opens files, and does not shell out at all.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:  # normal import: ``python3 -m collectors.pr_maintenance`` or run.py
    from .base import SectionResult, allowlist, run_collector
except ImportError:  # pragma: no cover - direct-script execution
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from collectors.base import SectionResult, allowlist, run_collector

SECTION_ID = "pr-maintenance"
DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / "pr-crusher"
#: The only state schema this parser was written against and verified on.
SUPPORTED_STATE_VERSION = 1
DEFAULT_MAX_TICK_RUNS = 5
DEFAULT_MAX_TEXT_CHARS = 400
#: How many unusable state files are named individually. The count is always
#: exact in ``metrics.state_files_unusable``; only the listing is bounded.
MAX_ERROR_CAVEATS = 20

#: Structural field allowlist for a tick ``summary.json``. Keys are matched at
#: every depth; anything pr-crusher writes that is not named here -- provider
#: transcripts, environment captures, future fields nobody has reviewed -- is
#: dropped at ingest, before a single value is interpreted or rendered.
TICK_FIELDS = frozenset(
    {
        # envelope
        "version",
        "tick",
        "run_id",
        "started_at",
        "completed_at",
        "success",
        "repository",
        "automerge",
        "provider",
        "provider_status",
        "provider_returncode",
        # merge gates
        "merge_outcomes",
        "number",
        "allowed",
        "attempted",
        "reasons",
        # provider result
        "result",
        "schema_version",
        "status",
        "summary",
        "actions",
        "kind",
        "detail",
        "merge_candidates",
        "ci",
        "coverage",
        "disposition",
        "grade",
        "draft",
        "mergeable",
        "threads_resolved",
        "head_sha",
        # resume + lifecycle
        "resume",
        "noop_streak",
        "updated_at",
        "lifecycle",
        "type",
        "publish_status",
        # counted but never interpreted; the v1 schema does not describe it
        "action_outcomes",
    }
)

#: Structural field allowlist for ``journal.json``. ``actions`` is deliberately
#: excluded: the journal's action log restates what the tick summaries already
#: carry, and the journal is used here only as a cross-check on which ticks ran.
JOURNAL_FIELDS = frozenset(
    {
        "version",
        "repository",
        "github_repository",
        "runs",
        "at",
        "phase",
        "run_id",
        "tick",
        "success",
        "resume",
        "status",
        "noop_streak",
        "updated_at",
    }
)


class SourceError(Exception):
    """A source file could not be read or parsed. Always becomes a reason."""


# --------------------------------------------------------------------------- #
# reading
# --------------------------------------------------------------------------- #


def _read_json(path: Path, fields: frozenset[str]) -> Any:
    """Read one JSON file and immediately bound it to ``fields``.

    Allowlisting happens here, at ingest, so no unreviewed source payload exists
    in this process for longer than one expression.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SourceError(f"{path} is missing") from exc
    except OSError as exc:
        raise SourceError(f"{path} cannot be read: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SourceError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SourceError(f"{path} is a {type(data).__name__}, expected a JSON object")
    return allowlist(data, fields)


def _clip(value: Any, limit: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}... (clipped from {len(text)} chars)"


def _repo_label(slug: str, *docs: Any) -> str:
    """A display name that cannot carry a credential.

    Only the owner/name path of a remote is ever kept; if a remote URL had
    userinfo attached, the userinfo is discarded by construction rather than by
    matching it against any pattern.
    """
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        github = doc.get("github_repository")
        if isinstance(github, str) and github.count("/") == 1 and github.strip():
            return github.strip()
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        remote = doc.get("repository")
        if not isinstance(remote, str) or not remote.strip():
            continue
        remote = remote.strip()
        if "://" in remote:
            path = urlsplit(remote).path
        elif ":" in remote:
            path = remote.split(":", 1)[1]
        else:
            path = remote
        path = path.strip("/")
        if path.endswith(".git"):
            path = path[: -len(".git")]
        if path:
            return path
    return slug


def _parse_moment(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        moment = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        return None
    return moment.astimezone(dt.UTC)


def _window(report_date: str, tz: dt.tzinfo) -> tuple[dt.datetime, dt.datetime]:
    day = dt.date.fromisoformat(report_date)
    start = dt.datetime.combine(day, dt.time.min, tzinfo=tz)
    return start.astimezone(dt.UTC), (start + dt.timedelta(days=1)).astimezone(dt.UTC)


def _resolve_timezone(config: dict[str, Any], caveats: list[str]) -> dt.tzinfo:
    name = config.get("timezone") if isinstance(config, dict) else None
    if isinstance(name, str) and name.strip():
        try:
            return ZoneInfo(name.strip())
        except (ZoneInfoNotFoundError, ValueError):
            caveats.append(
                f"config timezone {name!r} is not a known IANA zone; used the host "
                "local zone for the report window"
            )
    local = dt.datetime.now().astimezone().tzinfo
    return local if local is not None else dt.UTC


def _option(section_cfg: dict[str, Any], key: str, default: Any) -> Any:
    options = section_cfg.get("options") if isinstance(section_cfg, dict) else None
    if isinstance(options, dict) and key in options:
        return options[key]
    return default


def _positive_int(value: Any, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return default
    return value


# --------------------------------------------------------------------------- #
# per-repository state
# --------------------------------------------------------------------------- #


def _tick_in_window(
    tick: dict[str, Any], start: dt.datetime, end: dt.datetime
) -> tuple[bool, str | None]:
    completed = _parse_moment(tick.get("completed_at"))
    if completed is None:
        return False, "has no readable completed_at, so it cannot be placed in the window"
    return start <= completed < end, None


def _read_repo(
    repo_dir: Path, start: dt.datetime, end: dt.datetime
) -> dict[str, Any]:
    """Everything known about one tracked repository, plus what could not be read."""
    slug = repo_dir.name
    state: dict[str, Any] = {
        "slug": slug,
        "label": slug,
        "ticks": [],
        "errors": [],
        "notes": [],
        # the streak as of the last tick inside the window, and as of the most
        # recent tick on record -- kept apart so a report about a past day never
        # quotes a number that was produced after that day ended
        "noop_streak_window": None,
        "noop_streak_latest": None,
        "latest_tick": None,
        "latest_completed_at": None,
        "journal_only_ticks": [],
        "readable": False,
    }

    latest: dict[str, Any] | None = None
    try:
        latest = _read_json(repo_dir / "summary.json", TICK_FIELDS)
        state["readable"] = True
    except SourceError as exc:
        state["errors"].append(str(exc))

    journal: dict[str, Any] | None = None
    try:
        journal = _read_json(repo_dir / "journal.json", JOURNAL_FIELDS)
        state["readable"] = True
    except SourceError as exc:
        state["errors"].append(str(exc))

    state["label"] = _repo_label(slug, journal, latest)
    if isinstance(latest, dict):
        state["latest_tick"] = latest.get("tick")
        state["latest_completed_at"] = latest.get("completed_at")
        resume = latest.get("resume")
        if isinstance(resume, dict) and isinstance(resume.get("noop_streak"), int):
            state["noop_streak_latest"] = resume["noop_streak"]

    runs_dir = repo_dir / "runs"
    tick_paths: list[Path] = []
    run_dir_names: set[str] = set()
    if runs_dir.is_dir():
        try:
            tick_paths = sorted(p for p in runs_dir.glob("tick-*/summary.json"))
            run_dir_names = {p.name for p in runs_dir.glob("tick-*") if p.is_dir()}
            state["readable"] = True
        except OSError as exc:
            state["errors"].append(f"{runs_dir} cannot be listed: {exc}")
    elif runs_dir.exists():
        state["errors"].append(f"{runs_dir} exists but is not a directory")
    else:
        state["notes"].append(f"{runs_dir} does not exist; no per-tick detail is available")

    for path in tick_paths:
        try:
            tick = _read_json(path, TICK_FIELDS)
        except SourceError as exc:
            state["errors"].append(str(exc))
            continue
        inside, problem = _tick_in_window(tick, start, end)
        if problem is not None:
            state["errors"].append(f"{path} {problem}")
            continue
        if not inside:
            continue
        state["ticks"].append(tick)
        version = tick.get("version")
        if version != SUPPORTED_STATE_VERSION:
            state["errors"].append(
                f"{path} reports state version {version!r}, expected "
                f"{SUPPORTED_STATE_VERSION}; its fields may be misread"
            )

    # Cross-check against the journal: retention may have removed a run
    # directory whose tick still ran. A tick we know about but cannot detail is
    # a gap, and it is recorded as one.
    if isinstance(journal, dict):
        runs = journal.get("runs")
        if isinstance(runs, list):
            for entry in runs:
                if not isinstance(entry, dict) or entry.get("phase") != "completed":
                    continue
                moment = _parse_moment(entry.get("at"))
                if moment is None or not (start <= moment < end):
                    continue
                run_id = entry.get("run_id")
                if isinstance(run_id, str) and run_id in run_dir_names:
                    continue  # the run directory exists; any read failure is an error above
                state["journal_only_ticks"].append(entry)
        else:
            state["errors"].append(
                f"{repo_dir / 'journal.json'} has no readable runs array"
            )

    state["ticks"].sort(key=lambda item: (item.get("tick") or 0, item.get("run_id") or ""))
    if state["ticks"]:
        resume = state["ticks"][-1].get("resume")
        if isinstance(resume, dict) and isinstance(resume.get("noop_streak"), int):
            state["noop_streak_window"] = resume["noop_streak"]
    return state


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #


def _tick_lines(tick: dict[str, Any], max_chars: int) -> list[str]:
    result = tick.get("result") if isinstance(tick.get("result"), dict) else {}
    lines = [
        "  tick {tick} {run_id} completed={completed} provider={provider} "
        "provider_status={pstatus} result_status={rstatus} success={success} "
        "automerge={automerge}".format(
            tick=tick.get("tick"),
            run_id=tick.get("run_id"),
            completed=tick.get("completed_at"),
            provider=tick.get("provider"),
            pstatus=tick.get("provider_status"),
            rstatus=result.get("status"),
            success=tick.get("success"),
            automerge=tick.get("automerge"),
        )
    ]
    candidates = result.get("merge_candidates")
    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            lines.append(
                "    PR #{number} ci={ci} coverage={coverage} grade={grade} "
                "disposition={disposition} mergeable={mergeable} draft={draft} "
                "threads_resolved={threads} head={head}".format(
                    number=candidate.get("number"),
                    ci=candidate.get("ci"),
                    coverage=candidate.get("coverage"),
                    grade=candidate.get("grade"),
                    disposition=candidate.get("disposition"),
                    mergeable=candidate.get("mergeable"),
                    draft=candidate.get("draft"),
                    threads=candidate.get("threads_resolved"),
                    head=str(candidate.get("head_sha"))[:12],
                )
            )
    outcomes = tick.get("merge_outcomes")
    if isinstance(outcomes, list):
        for outcome in outcomes:
            if not isinstance(outcome, dict):
                continue
            reasons = outcome.get("reasons")
            reason_text = (
                "; ".join(str(item) for item in reasons) if isinstance(reasons, list) else ""
            )
            lines.append(
                "    merge gate PR #{number} allowed={allowed} attempted={attempted}"
                "{reasons}".format(
                    number=outcome.get("number"),
                    allowed=outcome.get("allowed"),
                    attempted=outcome.get("attempted"),
                    reasons=f" reasons: {_clip(reason_text, max_chars)}" if reason_text else "",
                )
            )
    summary = result.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.append(f"    summary: {_clip(summary, max_chars)}")
    actions = result.get("actions")
    if isinstance(actions, list):
        for action in actions:
            if not isinstance(action, dict):
                continue
            lines.append(
                f"    {action.get('kind')}: {_clip(action.get('detail', ''), max_chars)}"
            )
    return lines


# --------------------------------------------------------------------------- #
# counting
# --------------------------------------------------------------------------- #


@dataclass
class Tally:
    """Everything counted across the tracked repositories, plus what to print."""

    detail: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    ticks_in_window: int = 0
    ticks_failed: int = 0
    ticks_noop: int = 0
    repos_with_ticks: int = 0
    merges_attempted: int = 0
    #: Raised only by an explicit completion record. pr-crusher state schema v1
    #: has no such field, so an attempted merge is counted as unconfirmed rather
    #: than assumed successful -- inventing a completion here is precisely the
    #: false green this pipeline exists to prevent.
    merges_completed: int = 0
    merges_unconfirmed: int = 0
    published: int = 0
    skipped_publications: int = 0
    action_outcomes: int = 0
    triaged: set[tuple[str, Any]] = field(default_factory=set)
    candidates: set[tuple[str, Any]] = field(default_factory=set)
    publisher_details: set[str] = field(default_factory=set)
    noop_streaks: list[int] = field(default_factory=list)

    @property
    def noop_streak(self) -> int:
        """The longest idle streak any tracked repository is sitting on."""
        return max(self.noop_streaks) if self.noop_streaks else 0


def _count_tick(tally: Tally, slug: str, tick: dict[str, Any]) -> None:
    result = tick.get("result") if isinstance(tick.get("result"), dict) else {}
    if tick.get("success") is not True:
        tally.ticks_failed += 1
    if result.get("status") == "noop" or tick.get("provider_status") == "noop":
        tally.ticks_noop += 1
    for candidate in result.get("merge_candidates") or []:
        if isinstance(candidate, dict) and candidate.get("number") is not None:
            tally.candidates.add((slug, candidate["number"]))
            tally.triaged.add((slug, candidate["number"]))
    for outcome in tick.get("merge_outcomes") or []:
        if not isinstance(outcome, dict):
            continue
        if outcome.get("number") is not None:
            tally.triaged.add((slug, outcome["number"]))
        if outcome.get("attempted") is True:
            tally.merges_attempted += 1
            tally.merges_unconfirmed += 1
    outcomes = tick.get("action_outcomes")
    if isinstance(outcomes, list):
        tally.action_outcomes += len(outcomes)
    for entry in tick.get("lifecycle") or []:
        if not isinstance(entry, dict):
            continue
        publish_status = entry.get("publish_status")
        if publish_status == "published":
            tally.published += 1
            continue
        tally.skipped_publications += 1
        tally.publisher_details.add(
            f"{publish_status}: {entry.get('detail')}"
            if entry.get("detail")
            else str(publish_status)
        )


def _tally(
    repos: list[dict[str, Any]], report_date: str, max_ticks: int, max_chars: int
) -> Tally:
    """Count every repository's window, and render the per-repository detail."""
    tally = Tally()
    for repo in repos:
        streak = repo["noop_streak_window"]
        if not isinstance(streak, int):
            streak = repo["noop_streak_latest"]
        if isinstance(streak, int):
            tally.noop_streaks.append(streak)

        ticks, journal_only = repo["ticks"], repo["journal_only_ticks"]
        tally.ticks_in_window += len(ticks) + len(journal_only)
        if ticks or journal_only:
            tally.repos_with_ticks += 1

        tally.detail.append(f"=== {repo['label']} ({repo['slug']}) ===")
        if isinstance(repo["noop_streak_window"], int):
            tally.detail.append(
                f"  noop streak at the end of the window: {repo['noop_streak_window']}"
            )
        elif isinstance(repo["noop_streak_latest"], int):
            tally.detail.append(
                f"  noop streak {repo['noop_streak_latest']} as of the most recent tick "
                f"{repo['latest_tick']} ({repo['latest_completed_at']}), which is outside "
                "the window"
            )
        for note in repo["notes"]:
            tally.detail.append(f"  note: {note}")
        if not ticks and not journal_only:
            tally.detail.append(f"  no tick completed in the window for {report_date}")

        for tick in ticks:
            _count_tick(tally, repo["slug"], tick)

        shown = ticks[:max_ticks]
        for tick in shown:
            tally.detail.extend(_tick_lines(tick, max_chars))
        if len(ticks) > len(shown):
            message = (
                f"{repo['label']}: showing {len(shown)} of {len(ticks)} ticks that "
                "completed in the window"
            )
            tally.detail.append(f"  {message}")
            tally.caveats.append(message)

        for entry in journal_only:
            tally.detail.append(
                f"  tick {entry.get('tick')} {entry.get('run_id')} completed "
                f"{entry.get('at')} -- recorded in journal.json, but its run directory "
                "is absent so no PR detail could be read"
            )
    return tally


# --------------------------------------------------------------------------- #
# the collector
# --------------------------------------------------------------------------- #


def collect(
    section_cfg: dict[str, Any] | None = None,
    report_date: str = "",
    config: dict[str, Any] | None = None,
    *,
    section: dict[str, Any] | None = None,
    date: str | None = None,
) -> SectionResult:
    """Read pr-crusher state for ``report_date`` and report it honestly.

    ``section``/``date`` are accepted as aliases for ``section_cfg``/
    ``report_date`` so either calling convention in the package works.
    """
    section_cfg = section_cfg if isinstance(section_cfg, dict) else (section or {})
    config = config if isinstance(config, dict) else {}
    report_date = (date or report_date or "").strip()
    section_id = section_cfg.get("id") or SECTION_ID

    caveats: list[str] = []
    tz = _resolve_timezone(config, caveats)
    try:
        start, end = _window(report_date, tz)
    except ValueError:
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"report date {report_date!r} is not an ISO YYYY-MM-DD date",
            summary="pr maintenance: no window could be computed for the report date",
            caveats=caveats,
        )

    state_dir = Path(
        str(_option(section_cfg, "state_dir", _option(section_cfg, "state_root", DEFAULT_STATE_DIR)))
    ).expanduser()
    max_ticks = _positive_int(_option(section_cfg, "max_tick_runs", DEFAULT_MAX_TICK_RUNS), DEFAULT_MAX_TICK_RUNS)
    max_chars = _positive_int(
        _option(section_cfg, "max_text_chars", DEFAULT_MAX_TEXT_CHARS), DEFAULT_MAX_TEXT_CHARS
    )

    window_label = f"{report_date} ({tz})"
    if not state_dir.is_dir():
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"pr-crusher state directory {state_dir} does not exist or is not a directory",
            summary=(
                f"pr maintenance: unreadable -- pr-crusher state directory {state_dir} is "
                "absent, so whether any PR maintenance ran on "
                f"{report_date} is unknown"
            ),
            caveats=caveats,
        )
    repos_dir = state_dir / "repos"
    if not repos_dir.is_dir():
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"pr-crusher repository state directory {repos_dir} does not exist",
            summary=(
                f"pr maintenance: unreadable -- {repos_dir} is absent, so whether any PR "
                f"maintenance ran on {report_date} is unknown"
            ),
            caveats=caveats,
        )
    try:
        repo_dirs = sorted(path for path in repos_dir.iterdir() if path.is_dir())
    except OSError as exc:
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"{repos_dir} cannot be listed: {exc}",
            summary=f"pr maintenance: unreadable -- {repos_dir} cannot be listed",
            caveats=caveats,
        )

    repos = [_read_repo(path, start, end) for path in repo_dirs]
    tally = _tally(repos, report_date, max_ticks, max_chars)
    caveats.extend(tally.caveats)
    detail = [
        f"window: {start.isoformat().replace('+00:00', 'Z')} .. "
        f"{end.isoformat().replace('+00:00', 'Z')} for {window_label}",
        f"state directory: {state_dir}",
        *tally.detail,
    ]
    errors = [error for repo in repos for error in repo["errors"]]
    unreadable = [repo for repo in repos if not repo["readable"]]

    # ---- publisher visibility ----------------------------------------------
    # pr-crusher's activity does not reach Candystore, so silence on the bus
    # must never be read as silence in the repositories.
    if tally.skipped_publications:
        caveats.append(
            f"pr-crusher did not publish {tally.skipped_publications} lifecycle event(s) "
            f"to Bloodbank ({'; '.join(sorted(tally.publisher_details))}); this activity "
            "is absent from Candystore and was read from pr-crusher's durable state instead"
        )
    else:
        caveats.append(
            "pr-crusher activity is read from its durable state, not Candystore: its "
            "Bloodbank publisher has been observed disabled, so absence of PR events on "
            "the bus does not mean absence of PR activity"
        )
    if tally.published:
        caveats.append(f"{tally.published} pr-crusher lifecycle event(s) did reach Bloodbank")
    if tally.action_outcomes:
        caveats.append(
            f"{tally.action_outcomes} pr-crusher action outcome(s) were recorded in the "
            "window; the v1 state schema does not describe their shape, so they are "
            "counted but not interpreted"
        )

    # ---- status derivation, from what actually happened ---------------------
    status = "complete"
    reasons: list[str] = []

    if repos and len(unreadable) == len(repos):
        status = "failed"
        reasons.append(
            "no tracked repository's pr-crusher state could be read "
            f"({len(unreadable)} of {len(repos)} unreadable)"
        )
    elif unreadable:
        status = "partial"
        reasons.append(
            f"{len(unreadable)} of {len(repos)} tracked repositories had unreadable state: "
            + ", ".join(repo["slug"] for repo in unreadable)
        )

    if status != "failed" and errors:
        status = "partial"
        reasons.append(f"{len(errors)} pr-crusher state file(s) could not be used")
    caveats.extend(errors[:MAX_ERROR_CAVEATS])
    if len(errors) > MAX_ERROR_CAVEATS:
        caveats.append(
            f"{len(errors) - MAX_ERROR_CAVEATS} further unusable state file(s) are counted "
            "in metrics.state_files_unusable but not listed individually"
        )

    journal_only_total = sum(len(repo["journal_only_ticks"]) for repo in repos)
    if journal_only_total and status != "failed":
        status = "partial"
        reasons.append(
            f"{journal_only_total} tick(s) ran inside the window but their run directories "
            "are gone, so their PR detail could not be read"
        )

    if tally.merges_unconfirmed and status != "failed":
        status = "partial"
        reasons.append(
            f"{tally.merges_unconfirmed} merge(s) were attempted but pr-crusher state "
            "schema v1 records no completion field, so merges_completed cannot be confirmed"
        )
        caveats.append(
            "merges_completed counts only confirmed merges; attempted merges with no "
            "completion record are reported as unconfirmed, never as completed"
        )

    if not repos:
        caveats.append(
            f"{repos_dir} tracks no repositories, so pr-crusher has no work to report"
        )

    # ---- summary ------------------------------------------------------------
    if status == "failed":
        summary = (
            f"pr maintenance: unreadable -- {reasons[0] if reasons else 'state could not be read'}"
        )
    elif not repos:
        summary = (
            f"pr maintenance: pr-crusher tracks no repositories, so nothing ran on {report_date}."
        )
    elif tally.ticks_in_window == 0:
        summary = (
            f"pr maintenance: pr-crusher did not run on {report_date} -- no tick completed "
            f"in the window across {len(repos)} tracked repositor"
            f"{'y' if len(repos) == 1 else 'ies'}."
        )
    else:
        pieces = [
            f"pr maintenance: {tally.ticks_in_window} tick(s) across "
            f"{tally.repos_with_ticks} of {len(repos)} tracked repositories on {report_date}",
            f"{len(tally.triaged)} PR(s) triaged, {len(tally.candidates)} merge candidate(s)",
            f"{tally.merges_attempted} merge(s) attempted, "
            f"{tally.merges_completed} confirmed merged",
        ]
        if tally.ticks_failed:
            pieces.append(f"{tally.ticks_failed} tick(s) did not succeed")
        if tally.ticks_noop:
            pieces.append(f"{tally.ticks_noop} tick(s) were no-ops")
        summary = "; ".join(pieces) + "."

    return SectionResult(
        id=section_id,
        status=status,
        reason="; ".join(reasons),
        summary=summary,
        metrics={
            "repos_tracked": len(repos),
            "ticks_in_window": tally.ticks_in_window,
            "prs_triaged": len(tally.triaged),
            "merge_candidates": len(tally.candidates),
            "merges_attempted": tally.merges_attempted,
            "merges_completed": tally.merges_completed,
            "noop_streak": tally.noop_streak,
            "ticks_failed": tally.ticks_failed,
            "ticks_noop": tally.ticks_noop,
            "repos_with_ticks": tally.repos_with_ticks,
            "bloodbank_events_published": tally.published,
            "bloodbank_events_skipped": tally.skipped_publications,
            "merges_unconfirmed": tally.merges_unconfirmed,
            "state_files_unusable": len(errors),
        },
        detail=detail,
        caveats=caveats,
    )


# --------------------------------------------------------------------------- #
# standalone entry point
# --------------------------------------------------------------------------- #


def _default_date() -> str:
    return (dt.date.today() - dt.timedelta(days=1)).isoformat()


def _standalone_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Config and section for a standalone run, plus caveats about where they came from."""
    caveats: list[str] = []
    config: dict[str, Any] = {}
    section_cfg: dict[str, Any] = {
        "id": SECTION_ID,
        "title": "Nightly PR Maintenance",
        "collector": "pr_maintenance",
        "required": False,
        "enabled": True,
        "max_age_hours": 24,
        "options": {},
    }
    if args.config:
        from reportctl_config import load_config  # local import: standalone only

        config = load_config(Path(args.config))
        wanted = args.section or SECTION_ID
        matches = [
            item
            for item in config["sections"]
            if item["id"] == wanted or item["collector"] == "pr_maintenance"
        ]
        if not matches:
            raise SourceError(
                f"{args.config} defines no section using the pr_maintenance collector"
            )
        section_cfg = matches[0]
    else:
        local = dt.datetime.now().astimezone().tzinfo
        caveats.append(
            f"standalone run without --config: used the host local timezone ({local}) "
            "and this collector's built-in defaults; the effective state directory is "
            "named in the detail"
        )
    if args.state_dir:
        section_cfg = dict(section_cfg)
        section_cfg["options"] = dict(section_cfg.get("options") or {})
        section_cfg["options"]["state_dir"] = args.state_dir
        caveats.append(f"state directory overridden on the command line: {args.state_dir}")
    return config, section_cfg, caveats


def main(argv: list[str] | None = None) -> int:
    """Print the SectionArtifact and exit non-zero unless it is complete."""
    parser = argparse.ArgumentParser(
        prog="collectors.pr_maintenance",
        description="Collect nightly PR maintenance from pr-crusher durable state.",
    )
    parser.add_argument("--date", default=_default_date(), help="report date, YYYY-MM-DD")
    parser.add_argument("--config", help="reportctl schema v2 config to take options from")
    parser.add_argument("--section", help="section id to use from --config")
    parser.add_argument("--state-dir", help="override the pr-crusher state directory")
    parser.add_argument("--run-id", help="run identifier recorded in the artifact")
    args = parser.parse_args(argv)

    run_id = args.run_id or f"cli-{dt.datetime.now(dt.UTC):%Y%m%dT%H%M%SZ}"
    try:
        config, section_cfg, extra_caveats = _standalone_inputs(args)
    except Exception as exc:  # noqa: BLE001 - a bad config must not crash the collector
        result = SectionResult(
            id=SECTION_ID,
            status="failed",
            reason=f"{type(exc).__name__}: {exc}",
            summary="pr maintenance: standalone inputs could not be resolved",
        )
        config, extra_caveats = {}, []
    else:
        result = run_collector(
            lambda cfg: collect(cfg, args.date, config), section_cfg
        )
        result.caveats = list(result.caveats) + extra_caveats

    max_age = 24
    if isinstance(config.get("max_age_hours"), int):
        max_age = config["max_age_hours"]
    try:
        artifact = result.to_artifact(run_id, max_age)
    except Exception as exc:  # noqa: BLE001 - never crash; emit an honest failure
        artifact = SectionResult(
            id=SECTION_ID,
            status="failed",
            reason=f"artifact could not be built: {type(exc).__name__}: {exc}",
            summary="pr maintenance: the collector result could not be rendered",
        ).to_artifact(run_id, max_age)
    print(json.dumps(artifact, indent=2, ensure_ascii=False))
    return 0 if artifact["status"] == "complete" else (2 if artifact["status"] == "failed" else 1)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
