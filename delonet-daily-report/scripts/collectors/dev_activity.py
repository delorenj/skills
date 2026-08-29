"""Developer activity for one day: Candystore events correlated with git log.

Ported from ``candystore-daily-journal/scripts/generate_journal.py`` -- the one
part of the retired journal that actually ran and produced real data. The
rendering logic (``fetch_events``, ``git_log``, ``build_top_cli_table``,
``build_top_project_table``, ``build_heatmap_peak``, ``build_decisions_text``,
``build_commits_text``, ``build_git_logs_text``, ``build_operational_notes``)
is carried over. What changed, and why:

* **Three dead fetches removed.** The journal fetched ``/summary/daily``,
  ``/summary/by-project`` and ``/summary/by-cli`` on every run and never read
  the results -- the ``build_*`` helpers recompute all of it from ``/events``.
  Only ``/summary/heatmap`` is still fetched, because its value is used.
* **Heatmap peak is now the actual peak.** The journal read ``buckets[0]``,
  which is the first *(hour, project)* bucket in the response, not the busiest
  hour. Counts are summed per hour and the maximum wins.
* **``FALLBACK_PROJECTS`` is gone.** Repositories come from ``project_roots``
  in the operator config. Code no longer holds a list of the user's projects.
* **Coverage is the configuration, not the event stream.** Every configured
  root is git-logged on every run and lands in exactly one outcome bucket
  (logged / no-commits / missing / git-failed), each of them counted in
  ``metrics``. The first cut of this collector intersected the configured roots
  with the project names in the day's Candystore events and logged only the
  intersection: on 2026-08-15 that reported ``complete`` with "14 commit(s) in
  4 repository(ies)" while five other CONFIGURED roots held 25 more commits it
  never mentioned. A root the events do not name is a quiet repository, not an
  absent one, and the difference is exactly the lie this package exists to
  prevent.
* **Ambiguity is reported, never resolved by dropping.** Two configured roots
  sharing a basename are both logged and the collision is stated; the previous
  ``roots.setdefault(path.name, path)`` kept the first and discarded the second
  without a trace. Two spellings of one repository collapse to a single root,
  and that is stated too.
* **The git sweep states its own scope in every claim it makes.** The window
  is read across ALL refs of each repository -- branches, tags and fetched
  remote-tracking refs -- because reading only what is reachable from the
  checked-out HEAD makes a false coverage claim on a machine where feature
  branches are normal, and that scope was recorded nowhere. On 2026-08-15
  intelliforia's HEAD was ``design/admin-portal-overhaul`` and this section
  said the root "was read and had no commits" while ``fix(staging): move to
  stg.intelliforia.com`` sat on another ref; on 2026-08-17 pjangler's HEAD was
  a fix branch and eight commits, five of them on ``main``, were absent from a
  report that claimed 9 of 9 repositories covered. ``refs/stash`` and
  ``refs/notes/*`` are excluded from the sweep: a stash entry is uncommitted
  work in progress, not a commit of the day. The obvious consequences are
  handled rather than ignored -- a commit reachable from several refs is
  counted once (by SHA), a commit reachable only from a ref other than HEAD is
  counted *and marked as such* so an unmerged branch cannot pass itself off as
  landed work, and a rebase or cherry-pick copy (same author date and subject
  as another commit in the same window) is counted once, so replaying a
  long-lived branch cannot make the day look busier than it was. The
  ``git_scope`` option selects ``head`` for operators who want the narrower
  read; whichever scope is in force, the summary, the metrics and a caveat all
  name it, so neither a reader nor a machine consumer can mistake the number
  for coverage the sweep did not achieve.
* **Truncation is stated, never silent.** ``decisions[:30]``, ``commits[:30]``
  and ``notes[:20]`` used to drop the remainder without a word. Every cut now
  emits a caveat naming both numbers ("showing 30 of 43").
* **Status is derived, never assumed.** Candystore unreachable is ``failed``
  with the URL and the error in the reason; a git log that fails, a configured
  root with no readable repository, an unusable ``project_roots`` entry, an
  unread heatmap, or a truncated event pagination is ``partial``. ``complete``
  means every source named here was read in full -- every configured project
  root included, whether or not the day's events mention it -- at the git scope
  this section declares in its own summary, metrics and caveats.

Read-only throughout: HTTP GETs against Candystore and ``git log`` with an
explicit timeout. Nothing here writes to any source.

Config
------
``config["project_roots"]``   absolute repository paths (section option
``project_roots`` overrides for standalone use).
``section["options"]``        ``candystore_url`` (env ``CANDYSTORE_URL`` wins),
``page_size``, ``max_pages``, ``http_timeout_seconds``, ``git_timeout_seconds``,
``git_scope`` (``all-refs`` default, or ``head``), ``max_decisions``,
``max_commit_sessions``, ``max_operational_notes``, ``max_project_rows``,
``max_detail_lines``.

Standalone::

    python3 -m collectors.dev_activity --date 2026-08-17 [--config PATH]

prints the SectionArtifact JSON on stdout and exits non-zero when the section
failed, so a scheduler cannot log success over a dead collector.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, NamedTuple

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from collectors.base import (  # noqa: E402
    SECTION_RESULT_FIELDS,
    SectionResult,
    allowlist,
)
from reportctl_contracts import ConfigError  # noqa: E402

SECTION_ID = "dev-activity"

DEFAULT_CANDYSTORE_URL = "http://127.0.0.1:8683"
DEFAULT_PAGE_SIZE = 1000
DEFAULT_MAX_PAGES = 50
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_GIT_TIMEOUT = 60
DEFAULT_MAX_DECISIONS = 30
DEFAULT_MAX_COMMIT_SESSIONS = 30
DEFAULT_MAX_OPERATIONAL_NOTES = 20
DEFAULT_MAX_PROJECT_ROWS = 20
DEFAULT_MAX_DETAIL_LINES = 400

#: How much of each repository the git sweep reads. ``all-refs`` is the default
#: because it is the only scope under which "this root had no commits" is a
#: statement about the repository rather than about the branch that happens to
#: be checked out. ``head`` is available for operators who want the narrower
#: read; it is never silent -- see ``scope_caveat``.
GIT_SCOPE_ALL = "all-refs"
GIT_SCOPE_HEAD = "head"
GIT_SCOPES = (GIT_SCOPE_ALL, GIT_SCOPE_HEAD)
DEFAULT_GIT_SCOPE = GIT_SCOPE_ALL

#: Refs kept out of the ``all-refs`` sweep. A stash entry is uncommitted work in
#: progress that would be counted as a commit of the day, and ``refs/notes/*``
#: holds annotation commits about other commits, not work.
EXCLUDED_REF_GLOBS = ("refs/stash", "refs/notes/*")

#: Field separator inside one ``git log`` record. Not a character a commit
#: subject can contain, so a subject can never forge an extra field.
GIT_FIELD_SEP = "\x1f"

#: git's way of saying HEAD points at no commit yet. Not a failure: the refs
#: that do exist were still read.
UNBORN_HEAD_MARKERS = (
    "does not have any commits yet",
    "unknown revision",
    "ambiguous argument 'HEAD'",
)

#: Candystore's ``type`` column carries two eras of the same names forever: the
#: retired five-token ``bloodbank.v1.<domain>.<entity>.<action>`` on the ~713k
#: rows already written, and the version-free four-token name on everything
#: published since the version token was dropped. Nothing rewrites the history,
#: so a read that matches only one shape under-reports -- matching only the new
#: shape loses every row older than the migration, and matching only ``v1``
#: loses every row newer than it (which is what this collector was doing: a
#: day whose agents published seven version-free session-end events and zero
#: ``v1`` ones rendered as a day with no sessions).
#:
#: So every constant below is stored canonically and every comparison goes
#: through ``canonical_type``, which folds the two shapes together the same way
#: Candystore's own ``SCOPE_TYPE_EXPR`` does. This is the read side; the
#: publish side in ``scripts/run.py`` emits the new shape only.
_VERSION_TOKEN_RE = re.compile(r"^bloodbank\.v[0-9]+\.")


def canonical_type(event_type: Any) -> str:
    """Fold a retired ``v<N>.`` token out of an event type.

    ``bloodbank.v1.agent.session.ended`` and ``bloodbank.agent.session.ended``
    are the same fact under two spellings and must compare equal. A non-string
    type is not a type; it becomes ``""`` and matches nothing.
    """
    if not isinstance(event_type, str):
        return ""
    return _VERSION_TOKEN_RE.sub("bloodbank.", event_type, count=1)


DECISION_TYPE = "bloodbank.repo.decision.recorded"
SESSION_ENDED_TYPE = "bloodbank.agent.session.ended"
OPERATIONAL_TYPES = frozenset(
    {
        "bloodbank.finance.sync.started",
        "bloodbank.finance.sync.failed",
        "bloodbank.finance.sync.completed",
        "bloodbank.system.process.exited",
        "bloodbank.audio.session.started",
        "bloodbank.audio.status.updated",
    }
)

#: The structural field allowlist applied to every Candystore event the moment
#: it arrives. Only these keys survive, at any depth -- so no raw event payload
#: (tool arguments, environment, file contents, provider responses) can reach a
#: rendered line, an artifact, or the narrator. Adding a rendered field means
#: adding its key here on purpose; nothing arrives by accident.
EVENT_FIELDS = frozenset(
    {
        # envelope
        "type",
        "time",
        "cli",
        "project",
        "correlationid",
        "data",
        # data payload keys the builders below read
        "git_commits",
        "total_turns",
        "issue",
        "name",
        "repo",
        "title",
        "decision",
        "incident_summary",
        "error",
    }
)

#: Same idea for the heatmap response.
HEATMAP_FIELDS = frozenset({"buckets", "hour", "count"})


class SourceUnavailable(RuntimeError):
    """A source could not be read. The message becomes the section reason."""


class PeakHour(NamedTuple):
    hour: str
    count: int

    @property
    def text(self) -> str:
        return f"{self.hour} ({self.count} events)"


class Commit(NamedTuple):
    """One commit in the window, and whether HEAD can reach it."""

    sha: str
    short: str
    authored: str
    subject: str
    on_head: bool

    @property
    def identity(self) -> tuple[str, str]:
        """What makes two commits the same *work*.

        A rebase or a cherry-pick produces a new SHA for an unchanged patch but
        keeps the author date and the subject. Two commits sharing both are one
        piece of work counted once; the SHA alone would count it twice and make
        a replayed branch look like a productive day.
        """
        return (self.authored, self.subject)


class RepoLog(NamedTuple):
    """One repository's contribution to the day, with the scope it was read at.

    ``state`` is ``ok``, ``missing`` or ``failed`` exactly as before. ``commits``
    is the number of distinct pieces of work; ``on_head`` and ``off_head`` split
    it by reachability from the checked-out branch, and ``replays`` counts the
    copies collapsed into ``commits``. Every one of these numbers is reported --
    a count whose scope is not stated is the defect this type exists to prevent.
    """

    state: str
    text: str
    commits: int = 0
    on_head: int = 0
    off_head: int = 0
    replays: int = 0
    scope: str = DEFAULT_GIT_SCOPE
    head_label: str = "HEAD"


class Block(NamedTuple):
    """A rendered block plus how much of it the reader is actually seeing."""

    text: str
    shown: int
    total: int

    @property
    def truncated(self) -> bool:
        return self.total > self.shown


@dataclass
class RootPlan:
    """Which repositories this run is accountable for, and why.

    Coverage is the operator's ``project_roots`` -- the whole list, every run.
    The day's events decide nothing about which repositories are logged; they
    only tell us which of those roots were *active*, and which projects were
    active with no configured root at all (``unconfigured``, the inverse gap).
    """

    selected: list[tuple[str, Path]] = field(default_factory=list)
    active: list[str] = field(default_factory=list)
    unconfigured: list[str] = field(default_factory=list)
    collisions: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)


@dataclass
class GitSummary:
    """Per-root outcome. Every configured root lands in exactly one bucket.

    ``logged`` (read, had commits), ``quiet`` (read, no commits), ``missing``
    (no readable repository at the path) and ``failed`` (git log errored) are
    disjoint and together account for ``configured``. ``accounted_for`` is the
    self-check: if the buckets do not add up, the section says so rather than
    presenting an unexplained subtotal.
    """

    text: str = ""
    configured: list[str] = field(default_factory=list)
    logged: list[str] = field(default_factory=list)
    quiet: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unconfigured: list[str] = field(default_factory=list)
    collisions: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    active: list[str] = field(default_factory=list)
    commit_count: int = 0
    scope: str = DEFAULT_GIT_SCOPE
    on_head_count: int = 0
    off_head_count: int = 0
    replay_count: int = 0
    off_head_repos: list[str] = field(default_factory=list)
    replay_repos: list[str] = field(default_factory=list)

    @property
    def scope_text(self) -> str:
        """The one phrase every claim in this section is qualified by."""
        if self.scope == GIT_SCOPE_HEAD:
            return "the checked-out branch of each repository only"
        return "all refs of each repository"

    def scope_caveat(self, report_date: str) -> str:
        """What this sweep did and did not see, stated whether or not it matters.

        Emitted every run. A scope that is only mentioned when it happens to
        have cost something is a scope the reader cannot rely on.
        """
        if self.scope == GIT_SCOPE_HEAD:
            return (
                f"git scope is {GIT_SCOPE_HEAD!r} (option git_scope): only commits reachable "
                f"from each repository's checked-out branch were read on {report_date}, so "
                "work on any branch not merged into it is absent from every git number in "
                "this section, including the repositories reported as having no commits"
            )
        excluded = ", ".join(EXCLUDED_REF_GLOBS)
        # Kept under the 300-character cap the risks roll-up clips at, so the
        # scope is never the part of the sentence that gets cut off.
        return (
            f"git scope is {GIT_SCOPE_ALL!r}: every ref of each configured repository was "
            f"read for {report_date} -- branches, tags and fetched remote-tracking refs, "
            f"excluding {excluded} -- not only the checked-out branch; work that exists "
            "only in a clone this host has not fetched is out of reach"
        )

    @property
    def read(self) -> list[str]:
        """Roots whose history was actually read -- with or without commits."""
        return self.logged + self.quiet

    @property
    def unread(self) -> int:
        """Configured roots whose history could not be read at all."""
        return len(self.missing) + len(self.failed)

    def accounted_for(self) -> bool:
        return len(self.configured) == len(self.read) + self.unread


# --------------------------------------------------------------------------
# Candystore
# --------------------------------------------------------------------------


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


def fetch_events(
    base_url: str,
    date_from: str,
    date_to: str,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = DEFAULT_MAX_PAGES,
    timeout: int = DEFAULT_HTTP_TIMEOUT,
) -> tuple[list[dict[str, Any]], bool]:
    """Page through ``/events``.

    Returns ``(events, truncated)``. ``truncated`` is True when the page budget
    ran out with a full page still coming -- the caller must degrade rather
    than present a partial window as the whole day.
    """
    events: list[dict[str, Any]] = []
    offset = 0
    for _ in range(max_pages):
        url = (
            f"{base_url}/events?from={date_from}&to={date_to}"
            f"&limit={page_size}&offset={offset}"
        )
        page = fetch_json(url, timeout)
        if not isinstance(page, dict):
            raise SourceUnavailable(f"{url} returned {type(page).__name__}, expected an object")
        batch = page.get("events")
        if not isinstance(batch, list):
            raise SourceUnavailable(f"{url} returned no events array")
        events.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < page_size:
            return events, False
        offset += page_size
    return events, True


def sanitize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the structural field allowlist to raw Candystore events."""
    return [item for item in allowlist(events, EVENT_FIELDS) if isinstance(item, dict)]


# --------------------------------------------------------------------------
# git
# --------------------------------------------------------------------------


def _run_git(
    project_dir: Path, args: list[str], timeout: int
) -> tuple[str, str, str]:
    """Run one git command. Returns ``(state, stdout, stderr)``.

    ``state`` is ``ok`` or ``failed``; a non-zero exit, a timeout and an OS
    error all become ``failed`` with the message the caller renders, so no git
    problem can be mistaken for a quiet repository.
    """
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "-C", str(project_dir), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "failed", "", f"git timed out after {timeout}s"
    except OSError as exc:
        return "failed", "", f"git could not run: {exc}"
    if result.returncode != 0:
        return "failed", "", result.stderr.strip() or f"exit {result.returncode}"
    return "ok", result.stdout, ""


def _parse_commits(stdout: str, *, on_head: bool) -> list[Commit]:
    """Parse ``%H<US>%h<US>%aI<US>%s`` records. A malformed line is dropped."""
    commits: list[Commit] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(GIT_FIELD_SEP)
        if len(parts) != 4:
            continue
        sha, short, authored, subject = parts
        commits.append(Commit(sha, short, authored, subject, on_head))
    return commits


def _head_reachable(
    project_dir: Path, date_from: str, date_to: str, timeout: int
) -> tuple[str, set[str], str]:
    """SHAs the checked-out HEAD can reach in the window.

    Returns ``(state, shas, error)``. An unborn or detached-nowhere HEAD is not
    an error -- the refs that do exist were still read; it simply means nothing
    in the window is reachable from HEAD, which is exactly what the empty set
    says.
    """
    state, stdout, stderr = _run_git(
        project_dir,
        ["log", "HEAD", f"--since={date_from}", f"--until={date_to}", "--format=%H"],
        timeout,
    )
    if state != "ok":
        if any(marker in stderr for marker in UNBORN_HEAD_MARKERS):
            return "ok", set(), ""
        return "failed", set(), stderr
    return "ok", {line.strip() for line in stdout.splitlines() if line.strip()}, ""


def _head_label(project_dir: Path, timeout: int) -> str:
    """The checked-out branch, best effort. Never a failure on its own."""
    state, stdout, _ = _run_git(project_dir, ["rev-parse", "--abbrev-ref", "HEAD"], timeout)
    name = stdout.strip() if state == "ok" else ""
    return name or "HEAD"


def git_log(
    project_dir: Path,
    date_from: str,
    date_to: str,
    *,
    timeout: int = DEFAULT_GIT_TIMEOUT,
    scope: str = DEFAULT_GIT_SCOPE,
) -> RepoLog:
    """Commits in the window, at a scope the result carries with it.

    Under ``all-refs`` (the default) the sweep is every ref except
    ``refs/stash`` and ``refs/notes/*``, and each commit is marked with whether
    the checked-out HEAD can reach it. Under ``head`` only HEAD's history is
    read. The first cut of this collector read HEAD and said so nowhere, so a
    repository whose day's work sat on a feature branch was reported as a
    repository with no commits.

    A path that does not exist and a path that is not a repository are different
    operator situations, so they carry different text; a git failure is
    ``failed`` and never a quiet day.
    """
    if scope not in GIT_SCOPES:
        scope = DEFAULT_GIT_SCOPE
    if not project_dir.exists():
        return RepoLog("missing", f"(project root does not exist: {project_dir})", scope=scope)
    if not (project_dir / ".git").exists():
        return RepoLog("missing", f"(no .git in {project_dir})", scope=scope)

    fmt = f"--format=%H{GIT_FIELD_SEP}%h{GIT_FIELD_SEP}%aI{GIT_FIELD_SEP}%s"
    window = [f"--since={date_from}", f"--until={date_to}"]
    if scope == GIT_SCOPE_ALL:
        args = ["log"]
        args.extend(f"--exclude={glob}" for glob in EXCLUDED_REF_GLOBS)
        args.extend(["--all", *window, fmt])
    else:
        args = ["log", *window, fmt]

    state, stdout, stderr = _run_git(project_dir, args, timeout)
    if state != "ok":
        if any(marker in stderr for marker in UNBORN_HEAD_MARKERS):
            return RepoLog("ok", "(no commits)", scope=scope)
        return RepoLog("failed", f"(git log failed: {stderr})", scope=scope)

    commits = _parse_commits(stdout, on_head=scope == GIT_SCOPE_HEAD)
    head_label = "HEAD"
    if scope == GIT_SCOPE_ALL and commits:
        # Only worth asking once there is something to classify -- and asking
        # only then keeps an unborn HEAD in an otherwise empty repository from
        # ever looking like a git failure.
        head_state, reachable, head_error = _head_reachable(
            project_dir, date_from, date_to, timeout
        )
        if head_state != "ok":
            return RepoLog(
                "failed",
                f"(git log read all refs but could not determine what HEAD reaches, "
                f"so the scope of the result is unknown: {head_error})",
                scope=scope,
            )
        commits = [commit._replace(on_head=commit.sha in reachable) for commit in commits]
        head_label = _head_label(project_dir, timeout)

    return _render_commits(commits, scope, head_label)


def _render_commits(commits: list[Commit], scope: str, head_label: str) -> RepoLog:
    """Deduplicate, mark and render one repository's commits.

    Three distinct things are counted separately and all of them are reported:
    a commit reachable from several refs is one commit (git's own walk already
    unifies it; the SHA set makes that guarantee ours), a commit reachable only
    from a ref other than HEAD is real work that has not landed, and a commit
    repeating another's author date and subject is a rebase or cherry-pick copy
    of work already counted.
    """
    by_sha: dict[str, Commit] = {}
    for commit in commits:
        existing = by_sha.get(commit.sha)
        if existing is None:
            by_sha[commit.sha] = commit
        elif commit.on_head and not existing.on_head:
            by_sha[commit.sha] = commit
    unique = list(by_sha.values())
    if not unique:
        return RepoLog("ok", "(no commits)", scope=scope, head_label=head_label)

    # HEAD-reachable copies win the identity, so the replay is the one marked.
    ordered = sorted(unique, key=lambda item: not item.on_head)
    original: dict[tuple[str, str], Commit] = {}
    replay_of: dict[str, Commit] = {}
    for commit in ordered:
        first = original.get(commit.identity)
        if first is None:
            original[commit.identity] = commit
        else:
            replay_of[commit.sha] = first

    lines: list[str] = []
    off_head = sum(1 for commit in unique if not commit.on_head)
    if scope == GIT_SCOPE_ALL and off_head:
        lines.append(
            f"  (checked out: {head_label}; {off_head} of {len(unique)} commit(s) below "
            f"are not reachable from it)"
        )
    for commit in unique:
        marks: list[str] = []
        if scope == GIT_SCOPE_ALL and not commit.on_head:
            marks.append(f"not reachable from {head_label}")
        replay = replay_of.get(commit.sha)
        if replay is not None:
            marks.append(f"same author date and subject as {replay.short}, counted once")
        suffix = f"  [{'; '.join(marks)}]" if marks else ""
        lines.append(f"  {commit.short} {commit.subject}{suffix}")

    return RepoLog(
        state="ok",
        text="\n".join(lines),
        commits=len(unique) - len(replay_of),
        on_head=sum(1 for commit in unique if commit.on_head),
        off_head=off_head,
        replays=len(replay_of),
        scope=scope,
        head_label=head_label,
    )


# --------------------------------------------------------------------------
# renderers (carried over from the journal)
# --------------------------------------------------------------------------


def build_top_cli_table(events: list[dict[str, Any]]) -> str:
    counts = Counter(event.get("cli") or "unknown" for event in events)
    rows = counts.most_common()
    if not rows:
        return "  (none)"
    width = max(len(str(name)) for name, _ in rows)
    return "\n".join(f"  {str(name):<{width}}  {count:>6}" for name, count in rows)


def build_top_project_table(
    events: list[dict[str, Any]], limit: int = DEFAULT_MAX_PROJECT_ROWS
) -> Block:
    counts = Counter(event.get("project") or "unknown" for event in events)
    total = len(counts)
    rows = counts.most_common(limit)
    if not rows:
        return Block("  (none)", 0, 0)
    width = max(len(str(name)) for name, _ in rows)
    lines = [f"  {str(name):<{width}}  {count:>6}" for name, count in rows]
    if total > len(rows):
        lines.append(f"  ... showing {len(rows)} of {total} projects")
    return Block("\n".join(lines), len(rows), total)


def build_heatmap_peak(events: list[dict[str, Any]]) -> PeakHour | None:
    """Busiest hour derived from the events themselves (the heatmap fallback)."""
    counts: Counter[str] = Counter()
    for event in events:
        stamp = event.get("time")
        if isinstance(stamp, str) and len(stamp) >= 13:
            counts[f"{stamp[:13]}:00:00Z"] += 1
    if not counts:
        return None
    hour, count = max(counts.items(), key=lambda item: (item[1], item[0]))
    return PeakHour(hour, count)


def peak_hour_from_heatmap(heatmap: Any) -> PeakHour | None:
    """Busiest hour from ``/summary/heatmap``, summed across project buckets.

    The journal used ``buckets[0]``, which is one project's count in the most
    recent hour -- not the peak. Counts are aggregated per hour here.
    """
    if not isinstance(heatmap, dict):
        return None
    buckets = heatmap.get("buckets")
    if not isinstance(buckets, list) or not buckets:
        return None
    totals: Counter[str] = Counter()
    for bucket in buckets:
        if not isinstance(bucket, dict):
            continue
        hour, count = bucket.get("hour"), bucket.get("count")
        if isinstance(hour, str) and hour.strip() and isinstance(count, int) and count >= 0:
            totals[hour.strip()] += count
    if not totals:
        return None
    hour, count = max(totals.items(), key=lambda item: (item[1], item[0]))
    return PeakHour(hour, count)


def build_decisions_text(
    events: list[dict[str, Any]], limit: int = DEFAULT_MAX_DECISIONS
) -> Block:
    decisions = [
        event for event in events if canonical_type(event.get("type")) == DECISION_TYPE
    ]
    if not decisions:
        return Block("  (no recorded decisions)", 0, 0)
    lines = []
    for decision in decisions[:limit]:
        data = decision.get("data") or {}
        data = data if isinstance(data, dict) else {}
        issue = data.get("issue") or data.get("name") or "(no issue)"
        repo = data.get("repo") or decision.get("project") or "unknown"
        title = data.get("title") or data.get("decision") or "(no title)"
        first_line = str(title).splitlines()[0] if str(title).strip() else "(no title)"
        lines.append(f"  [{repo}] {issue}: {first_line}")
    shown = len(lines)
    if len(decisions) > shown:
        lines.append(f"  ... showing {shown} of {len(decisions)} decisions")
    return Block("\n".join(lines), shown, len(decisions))


def build_commits_text(
    events: list[dict[str, Any]], limit: int = DEFAULT_MAX_COMMIT_SESSIONS
) -> Block:
    committed = []
    for event in events:
        if canonical_type(event.get("type")) != SESSION_ENDED_TYPE:
            continue
        data = event.get("data")
        if isinstance(data, dict) and data.get("git_commits"):
            committed.append(event)
    if not committed:
        return Block("  (no commits in session-end events)", 0, 0)
    lines = []
    for event in committed[:limit]:
        data = event.get("data") or {}
        commits = data.get("git_commits") or []
        count = len(commits) if isinstance(commits, (list, tuple)) else 1
        project = event.get("project") or "unknown"
        turns = data.get("total_turns", "?")
        cli = event.get("cli") or "?"
        lines.append(f"  {project} ({cli}, {turns} turns): {count} commit(s)")
    shown = len(lines)
    if len(committed) > shown:
        lines.append(f"  ... showing {shown} of {len(committed)} committing sessions")
    return Block("\n".join(lines), shown, len(committed))


def build_operational_notes(
    events: list[dict[str, Any]], limit: int = DEFAULT_MAX_OPERATIONAL_NOTES
) -> Block:
    notes = []
    for event in events:
        event_type = event.get("type")
        if canonical_type(event_type) not in OPERATIONAL_TYPES:
            continue
        data = event.get("data")
        data = data if isinstance(data, dict) else {}
        project = event.get("project") or "unknown"
        summary = data.get("incident_summary") or data.get("error") or "(no detail)"
        first_line = str(summary).splitlines()[0]
        notes.append(f"  [{project}] {str(event_type).split('.')[-1]}: {first_line}")
    if not notes:
        return Block("  (no notable operational events)", 0, 0)
    lines = notes[:limit]
    shown = len(lines)
    if len(notes) > shown:
        lines = lines + [f"  ... showing {shown} of {len(notes)} operational events"]
    return Block("\n".join(lines), shown, len(notes))


def _real(path: Path) -> str:
    """Identity of a root on disk, so two spellings of one repo are one root."""
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def resolve_project_dirs(events: list[dict[str, Any]], project_roots: list[str]) -> RootPlan:
    """Plan the git sweep: EVERY configured repository, in config order.

    This used to intersect the configured roots with the project names in the
    day's Candystore events and log only the intersection, so a configured root
    that happened not to appear in the event stream was dropped with no caveat
    and no metric. On 2026-08-15 that hid 25 of the day's 39 commits behind a
    ``complete``. Coverage is now the configuration, full stop.

    Two roots that resolve to the same path collapse to one (recorded in
    ``duplicates`` -- one repository, counted once). Two DIFFERENT roots sharing
    a basename are both kept, disambiguated by path, and recorded in
    ``collisions``; the old ``dict.setdefault(path.name, path)`` silently threw
    the second one away.
    """
    selected: list[tuple[str, Path]] = []
    duplicates: list[str] = []
    seen: dict[str, str] = {}
    by_name: dict[str, list[Path]] = {}

    for root in project_roots:
        if not isinstance(root, str) or not root.strip():
            continue
        path = Path(root.strip()).expanduser()
        identity = _real(path)
        if identity in seen:
            duplicates.append(
                f"configured project root {root} is the same repository as "
                f"{seen[identity]} and was logged once, not twice"
            )
            continue
        seen[identity] = root
        # A root like "/" has no basename; fall back to the path so no
        # repository is ever rendered under an empty heading.
        name = path.name or str(path)
        selected.append((name, path))
        by_name.setdefault(name, []).append(path)

    collisions = [
        f"{len(paths)} configured project roots share the name {name!r} "
        f"({', '.join(str(item) for item in paths)}); each one is logged and "
        f"reported separately, and events naming {name!r} cannot be attributed "
        f"to just one of them"
        for name, paths in sorted(by_name.items())
        if len(paths) > 1
    ]
    labelled = [
        (name if len(by_name[name]) == 1 else f"{name} [{path}]", path)
        for name, path in selected
    ]

    names: list[str] = []
    for event in events:
        project = event.get("project")
        if not isinstance(project, str):
            continue
        base = project.strip().removesuffix(".git")
        if base and base != "unknown" and base not in names:
            names.append(base)
    names.sort()

    return RootPlan(
        selected=labelled,
        active=[name for name in names if name in by_name],
        unconfigured=[name for name in names if name not in by_name],
        collisions=collisions,
        duplicates=duplicates,
    )


def build_git_logs_text(
    events: list[dict[str, Any]],
    project_roots: list[str],
    date_from: str,
    date_to: str,
    *,
    timeout: int = DEFAULT_GIT_TIMEOUT,
    scope: str = DEFAULT_GIT_SCOPE,
) -> GitSummary:
    plan = resolve_project_dirs(events, project_roots)
    scope = scope if scope in GIT_SCOPES else DEFAULT_GIT_SCOPE
    summary = GitSummary(
        unconfigured=plan.unconfigured,
        collisions=plan.collisions,
        duplicates=plan.duplicates,
        active=plan.active,
        configured=[name for name, _ in plan.selected],
        scope=scope,
    )
    if not plan.selected:
        summary.text = "(no project roots configured)"
        return summary
    blocks = []
    for name, path in plan.selected:
        log = git_log(path, date_from, date_to, timeout=timeout, scope=scope)
        blocks.append(f"=== {name} ===\n{log.text}")
        if log.state == "ok" and log.commits:
            summary.logged.append(name)
            summary.commit_count += log.commits
            summary.on_head_count += log.on_head
            summary.off_head_count += log.off_head
            summary.replay_count += log.replays
            if log.off_head:
                summary.off_head_repos.append(
                    f"{name} {log.off_head} of {log.on_head + log.off_head} "
                    f"(checked out: {log.head_label})"
                )
            if log.replays:
                summary.replay_repos.append(f"{name} {log.replays}")
        elif log.state == "ok":
            summary.quiet.append(name)
        elif log.state == "missing":
            summary.missing.append(f"{name} {log.text}")
        else:
            summary.failed.append(f"{name}: {log.text.strip('()')}")
    summary.text = "\n\n".join(blocks)
    return summary


# --------------------------------------------------------------------------
# collection
# --------------------------------------------------------------------------


def _positive_int(options: dict[str, Any], key: str, default: int, caveats: list[str]) -> int:
    value = options.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        if key in options:
            caveats.append(f"option {key}={value!r} is not a positive integer; used {default}")
        return default
    return value


def _root_list(value: Any) -> tuple[list[str], list[str]]:
    """Split configured roots into usable paths and unusable entries.

    The unusable ones are returned rather than dropped: a project root the
    operator wrote down and this collector could not use is a hole in coverage,
    and a hole in coverage is never allowed to be silent.
    """
    if not isinstance(value, (list, tuple)):
        return [], []
    usable: list[str] = []
    unusable: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            usable.append(item.strip())
        else:
            unusable.append(repr(item))
    return usable, unusable


def _git_scope(options: dict[str, Any], caveats: list[str]) -> str:
    """Resolve ``git_scope``. An unusable value is reported, never obeyed.

    Falling back silently would be the original defect wearing a config key:
    the run would read one scope while the operator believed another.
    """
    value = options.get("git_scope")
    if value is None:
        return DEFAULT_GIT_SCOPE
    if isinstance(value, str) and value.strip() in GIT_SCOPES:
        return value.strip()
    caveats.append(
        f"option git_scope={value!r} is not one of {', '.join(GIT_SCOPES)}; "
        f"used {DEFAULT_GIT_SCOPE}"
    )
    return DEFAULT_GIT_SCOPE


def _named(values: list[str], limit: int = 8) -> str:
    if len(values) <= limit:
        return ", ".join(values)
    return ", ".join(values[:limit]) + f", and {len(values) - limit} more"


@dataclass
class _Settings:
    """Every tunable, resolved once. A bad value is reported, never obeyed."""

    candystore_url: str
    page_size: int
    max_pages: int
    http_timeout: int
    git_timeout: int
    git_scope: str
    max_decisions: int
    max_commit_sessions: int
    max_operational_notes: int
    max_project_rows: int
    max_detail_lines: int


def _settings(options: dict[str, Any], caveats: list[str]) -> _Settings:
    configured = options.get("candystore_url")
    configured = (
        configured.strip()
        if isinstance(configured, str) and configured.strip()
        else DEFAULT_CANDYSTORE_URL
    )
    environment = os.environ.get("CANDYSTORE_URL", "").strip()
    url = (environment or configured).rstrip("/")
    if environment and url != configured.rstrip("/"):
        caveats.append(
            f"candystore_url {configured} overridden by the CANDYSTORE_URL environment "
            f"variable ({url})"
        )
    return _Settings(
        candystore_url=url,
        page_size=_positive_int(options, "page_size", DEFAULT_PAGE_SIZE, caveats),
        max_pages=_positive_int(options, "max_pages", DEFAULT_MAX_PAGES, caveats),
        http_timeout=_positive_int(
            options, "http_timeout_seconds", DEFAULT_HTTP_TIMEOUT, caveats
        ),
        git_timeout=_positive_int(options, "git_timeout_seconds", DEFAULT_GIT_TIMEOUT, caveats),
        git_scope=_git_scope(options, caveats),
        max_decisions=_positive_int(options, "max_decisions", DEFAULT_MAX_DECISIONS, caveats),
        max_commit_sessions=_positive_int(
            options, "max_commit_sessions", DEFAULT_MAX_COMMIT_SESSIONS, caveats
        ),
        max_operational_notes=_positive_int(
            options, "max_operational_notes", DEFAULT_MAX_OPERATIONAL_NOTES, caveats
        ),
        max_project_rows=_positive_int(
            options, "max_project_rows", DEFAULT_MAX_PROJECT_ROWS, caveats
        ),
        max_detail_lines=_positive_int(
            options, "max_detail_lines", DEFAULT_MAX_DETAIL_LINES, caveats
        ),
    )


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
    """Collect developer activity for ``report_date``. Never raises.

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
                summary=f"{section_id}: no activity collected, no report date was given",
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
            summary=f"{section_id}: no activity collected, the report date was unusable",
        )
    start = dt.datetime.combine(day, dt.time.min, tzinfo=dt.UTC)
    end = start + dt.timedelta(days=1)
    date_from = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    date_to = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    settings = _settings(options, caveats)
    candystore_url = settings.candystore_url

    # ---- events: the section cannot exist without them -------------------
    try:
        raw_events, paginated_out = fetch_events(
            candystore_url,
            date_from,
            date_to,
            page_size=settings.page_size,
            max_pages=settings.max_pages,
            timeout=settings.http_timeout,
        )
    except SourceUnavailable as exc:
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"Candystore event history unavailable: {exc}",
            summary=(
                f"{section_id}: no developer activity collected for {report_date}; "
                f"Candystore at {candystore_url} could not be read"
            ),
            metrics={"candystore_reachable": False, "candystore_url": candystore_url},
            caveats=caveats,
        )

    events = sanitize_events(raw_events)
    degraded: list[str] = []
    if paginated_out:
        degraded.append(
            f"event pagination stopped at the {settings.max_pages}-page budget "
            f"({len(events)} events read); the day is not fully covered"
        )

    # ---- heatmap: used, with an events fallback --------------------------
    peak = None
    heatmap_read = True
    try:
        heatmap = allowlist(
            fetch_json(
                f"{candystore_url}/summary/heatmap"
                f"?group=project&from={date_from}&to={date_to}",
                settings.http_timeout,
            ),
            HEATMAP_FIELDS,
        )
        peak = peak_hour_from_heatmap(heatmap)
        if peak is None:
            caveats.append("heatmap returned no usable buckets; peak hour derived from events")
    except SourceUnavailable as exc:
        heatmap_read = False
        degraded.append(f"heatmap unavailable ({exc}); peak hour derived from events instead")
    if peak is None:
        peak = build_heatmap_peak(events)

    # ---- derived counts --------------------------------------------------
    sessions = {
        event.get("correlationid")
        for event in events
        if isinstance(event.get("correlationid"), str) and event["correlationid"].strip()
    }
    decisions = [
        event for event in events if canonical_type(event.get("type")) == DECISION_TYPE
    ]
    committing_sessions = [
        event
        for event in events
        if canonical_type(event.get("type")) == SESSION_ENDED_TYPE
        and isinstance(event.get("data"), dict)
        and event["data"].get("git_commits")
    ]
    projects = {
        (event.get("project") or "unknown").removesuffix(".git")
        for event in events
        if isinstance(event.get("project"), str)
    }
    projects.discard("unknown")

    # ---- rendered blocks -------------------------------------------------
    cli_table = build_top_cli_table(events)
    project_table = build_top_project_table(events, settings.max_project_rows)
    decision_block = build_decisions_text(events, settings.max_decisions)
    commit_block = build_commits_text(events, settings.max_commit_sessions)
    notes_block = build_operational_notes(events, settings.max_operational_notes)

    for block, label in (
        (project_table, "projects"),
        (decision_block, "decisions"),
        (commit_block, "committing sessions"),
        (notes_block, "operational events"),
    ):
        if block.truncated:
            caveats.append(f"{label} truncated: showing {block.shown} of {block.total}")

    # ---- git -------------------------------------------------------------
    raw_roots = options.get("project_roots")
    root_source = "section option project_roots"
    if not isinstance(raw_roots, (list, tuple)) or not raw_roots:
        raw_roots = config.get("project_roots")
        root_source = "config project_roots"
    project_roots, unusable_roots = _root_list(raw_roots)
    if unusable_roots:
        degraded.append(
            f"{len(unusable_roots)} {root_source} entry(ies) are not usable paths and were "
            f"skipped: {_named(unusable_roots)}"
        )
    if not project_roots:
        degraded.append("no project_roots configured; per-repository git logs were skipped")
        git = GitSummary(text="(no project roots configured)")
    else:
        git = build_git_logs_text(
            events,
            project_roots,
            date_from,
            date_to,
            timeout=settings.git_timeout,
            scope=settings.git_scope,
        )
        # Stated every run, before any finding that depends on it: a number
        # whose scope is not on the page is a coverage claim nobody can check.
        caveats.append(git.scope_caveat(report_date))
        if git.failed:
            degraded.append(
                f"git log failed for {len(git.failed)} configured repository(ies): "
                f"{_named(git.failed)}"
            )
        if git.missing:
            degraded.append(
                f"{len(git.missing)} configured project root(s) could not be read as a git "
                f"repository: {_named(git.missing)}"
            )
        if not git.accounted_for():
            degraded.append(
                f"per-root accounting does not add up: {len(git.configured)} configured "
                f"root(s) but {len(git.read) + git.unread} outcome(s) recorded"
            )
        if git.quiet:
            caveats.append(
                f"{len(git.quiet)} configured project root(s) were read across "
                f"{git.scope_text} and had no commits on {report_date}: {_named(git.quiet)}"
            )
        if git.off_head_count:
            caveats.append(
                f"{git.off_head_count} of {git.commit_count + git.replay_count} commit(s) "
                "are not reachable from their repository's checked-out branch (unmerged or "
                f"otherwise off-HEAD work) and are counted here: {_named(git.off_head_repos)}"
            )
        if git.replay_count:
            caveats.append(
                f"{git.replay_count} commit(s) repeat the author date and subject of another "
                "commit in the same window (rebase or cherry-pick copies) and were counted "
                f"once, not twice: {_named(git.replay_repos)}"
            )
        caveats.extend(git.collisions)
        caveats.extend(git.duplicates)
        if git.unconfigured:
            caveats.append(
                f"{len(git.unconfigured)} project(s) active in events have no configured "
                f"project root, so no git log was read for them: {_named(git.unconfigured)}"
            )

    # ---- detail ----------------------------------------------------------
    detail: list[str] = []
    for heading, body in (
        ("=== Events by CLI ===", cli_table),
        ("=== Events by project ===", project_table.text),
        ("=== Decisions recorded ===", decision_block.text),
        ("=== Sessions that committed ===", commit_block.text),
        ("=== Operational notes ===", notes_block.text),
        ("=== Git log by repository ===", git.text),
    ):
        detail.append(heading)
        detail.extend(body.splitlines())
        detail.append("")
    while detail and not detail[-1]:
        detail.pop()
    if len(detail) > settings.max_detail_lines:
        caveats.append(
            f"detail truncated: showing {settings.max_detail_lines} of {len(detail)} "
            "rendered lines"
        )
        detail = detail[: settings.max_detail_lines]

    # ---- status: derived from what actually happened ---------------------
    status = "complete"
    reason = ""
    if degraded:
        status = "partial"
        reason = "; ".join(degraded)

    summary = (
        f"{len(events)} events across {len(projects)} project(s) on {report_date}: "
        f"{len(sessions)} session(s), {len(decisions)} decision(s), "
        f"{len(committing_sessions)} committing session(s), "
        f"{git.commit_count} commit(s) across {len(git.read)} of "
        f"{len(git.configured)} configured repository(ies)"
    )
    if git.configured:
        # The scope travels with the number, in the one sentence most readers
        # and every downstream summary consumer will see.
        summary += f" read across {git.scope_text}"
        if git.scope == GIT_SCOPE_ALL and git.commit_count:
            summary += (
                f" ({git.on_head_count} on the checked-out branch, "
                f"{git.off_head_count} only on other refs)"
            )
    if git.unread:
        summary += f", {git.unread} of them unread"
    if peak is not None:
        summary += f"; peak {peak.text}"
    summary += "."

    metrics: dict[str, Any] = {
        "event_count": len(events),
        "session_count": len(sessions),
        "decision_count": len(decisions),
        "commit_count": len(committing_sessions),
        "project_count": len(projects),
        "peak_hour": peak.hour if peak else "unavailable",
        "peak_hour_event_count": peak.count if peak else 0,
        "git_commit_count": git.commit_count,
        "git_scope": git.scope,
        "git_commits_on_head": git.on_head_count,
        "git_commits_off_head": git.off_head_count,
        "git_commit_replays_collapsed": git.replay_count,
        "git_repos_with_off_head_commits": len(git.off_head_repos),
        "git_roots_configured": len(git.configured),
        "git_repos_logged": len(git.logged),
        "git_repos_no_commits": len(git.quiet),
        "git_repos_failed": len(git.failed),
        "git_repos_missing": len(git.missing),
        "git_roots_unread": git.unread,
        "git_roots_unusable": len(unusable_roots),
        "git_roots_duplicated": len(git.duplicates),
        "git_root_name_collisions": len(git.collisions),
        "git_roots_active_in_events": len(git.active),
        "projects_without_root": len(git.unconfigured),
        "candystore_reachable": True,
        "candystore_url": candystore_url,
        "heatmap_read": heatmap_read,
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
            section.get("collector") == "dev_activity" or section.get("id") == SECTION_ID
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
    return {"project_roots": [], "sections": [], "max_age_hours": 24}, (
        "no usable config found; running with no project roots"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="collectors.dev_activity",
        description="Collect one day of developer activity as a SectionArtifact.",
    )
    parser.add_argument(
        "--date",
        default=(dt.date.today() - dt.timedelta(days=1)).isoformat(),
        help="report date, YYYY-MM-DD (default: yesterday)",
    )
    parser.add_argument("--config", help="operator config; defaults are tried when omitted")
    parser.add_argument("--run-id", default=None, help="run identifier to stamp on the artifact")
    args = parser.parse_args(argv)

    run_id = args.run_id or f"dev-activity-{args.date}-{dt.datetime.now(dt.UTC):%H%M%S}"
    try:
        config, note = _load(Path(args.config).expanduser() if args.config else None)
    except (ConfigError, OSError) as exc:
        result = SectionResult(
            id=SECTION_ID,
            status="failed",
            reason=f"config unusable: {exc}",
            summary=f"{SECTION_ID}: no activity collected, the config could not be loaded",
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
