"""Event-data validation: the Bloodbank contract, checked locally before emit.

Mirrors `schemas/bloodbank/project/activity.recorded.json` (the `data` object
and its `$defs`) and `assert_project_invariants` in
`services/agent-hooks/core/validate.py` (§11.4), so nothing passes here and
then dies at `bb-emit`. Hand-rolled, stdlib only. Every message names the
field and the rule it broke.

Two entry points:

    validate_event(data)   -> None, raises ContractError
    assert_no_paths(obj)   -> None, raises ContractError

`validate_event` ends by calling `assert_no_paths`; `assemble` calls both
anyway because the second is the cheaper one to reason about in a log.
"""
from __future__ import annotations

import re
from datetime import datetime

from .common import ContractError

# -- patterns, verbatim from the schema's $defs --------------------------------

SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
AGENT_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
TICKET_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,11}-[0-9]+$")
IDENTIFIER_RE = re.compile(r"^[A-Z][A-Z0-9]{1,11}$")
WORKSPACE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SKILL_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")                      # _common/types.v1 semantic_version
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
BANK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
HTML_DOCTYPE_RE = re.compile(r"^<!(DOCTYPE|doctype) html>")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
# core/validate._RFC3339_DATETIME, the same checker the schema's date-time uses.
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")

# $defs.no_absolute_path: search semantics, every string anywhere in data.
NO_ABSOLUTE_PATH_RE = re.compile(r"(^|[^A-Za-z0-9_.])/(home|Users|root|tmp|var|etc|opt|srv|mnt)/")

# core/validate.py §11.4, verbatim. A sha must carry both a digit and a letter,
# or hex-alphabet English ("defaced", "effaced") is refused. The lookbehind
# keeps a '#abc123' CSS colour from reading as a commit.
_PROJECT_SHA = re.compile(
    r"(?<![#\w])(?=[0-9a-f]{7,40}\b)(?=[0-9a-f]*[0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b"
)
# A workstation path, not a URL path: the slash must not follow a word char
# or a dot, so 'https://x/home/' and 'a.b/tmp/' do not match.
_PROJECT_ABS_PATH = re.compile(r"(?<![\w.])/(?:home|Users|root|tmp|var|etc|opt|srv|mnt)/")

AUDIENCES = ("internal", "external")
WINDOW_BASES = ("previous_report", "cap_24h", "explicit")
EXPOSURES = ("external", "internal", "unlabeled")
TOKEN_PARTS = ("input", "output", "cache_read", "cache_write")
INTERNAL_ONLY_FIELDS = ("sources", "tickets")

# Every cap in the schema, in one place, so assemble truncates to the same
# numbers the validator refuses past.
CAPS = {
    "slug": 64, "name": 120, "repo_name": 100, "repos": 8,
    "title": 180, "raw": 5000, "markdown": 20000, "html": 262144,
    "duration_max": 2678400,
    "model": 120, "by_agent": 16, "by_cli": 16,
    "git_repos": 8, "commits": 100, "subject": 120, "author": 80, "branches": 64, "branch": 120,
    "ticket_list": 200, "tickets": 200, "ticket_title": 200, "state": 64, "labels": 8, "label": 40,
    "bank": 64,
}


# -- primitive checks ----------------------------------------------------------

def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _obj(value, path: str, allowed: tuple, required: tuple) -> dict:
    if not isinstance(value, dict):
        raise ContractError(f"{path}: must be an object")
    unknown = sorted(k for k in value if k not in allowed)
    if unknown:
        raise ContractError(f"{path}: unknown keys {unknown} (additionalProperties: false)")
    missing = [k for k in required if k not in value]
    if missing:
        raise ContractError(f"{path}: missing required keys {missing}")
    return value


def _str(value, path: str, *, min_len: int = 0, max_len: int | None = None,
         pattern: re.Pattern | None = None, nullable: bool = False, what: str = "") -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise ContractError(f"{path}: must be a string{' or null' if nullable else ''}")
    if len(value) < min_len:
        raise ContractError(f"{path}: shorter than {min_len} chars")
    if max_len is not None and len(value) > max_len:
        raise ContractError(f"{path}: longer than {max_len} chars ({len(value)})")
    if pattern is not None and not pattern.search(value):
        raise ContractError(f"{path}: {value!r} does not match {what or pattern.pattern}")
    return value


def _count(value, path: str) -> int:
    if not _is_int(value) or value < 0:
        raise ContractError(f"{path}: must be a non-negative integer")
    return value


def _bool(value, path: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{path}: must be a boolean")
    return value


def _uuid(value, path: str, *, nullable: bool) -> str | None:
    return _str(value, path, pattern=UUID_RE, nullable=nullable, what="an RFC 4122 uuid")


def _timestamp(value, path: str) -> datetime:
    _str(value, path, pattern=RFC3339_RE, what="an RFC 3339 date-time")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ContractError(f"{path}: {value!r} is not a real date-time ({exc})") from exc


def _unique(items: list, path: str) -> None:
    seen = set()
    for item in items:
        key = repr(item)
        if key in seen:
            raise ContractError(f"{path}: duplicate item {item!r} (uniqueItems)")
        seen.add(key)


def _list(value, path: str, *, max_items: int, unique: bool = False, min_items: int = 0) -> list:
    if not isinstance(value, list):
        raise ContractError(f"{path}: must be an array")
    if len(value) < min_items:
        raise ContractError(f"{path}: needs at least {min_items} item(s)")
    if len(value) > max_items:
        raise ContractError(f"{path}: more than {max_items} items ({len(value)})")
    if unique:
        _unique(value, path)
    return value


# -- sections ------------------------------------------------------------------

def _validate_project(project, path: str) -> dict:
    _obj(project, path, ("slug", "name", "identifier", "workspace", "board_id", "repos"),
         ("slug", "name", "identifier", "workspace", "board_id", "repos"))
    _str(project["slug"], f"{path}.slug", min_len=1, max_len=CAPS["slug"], pattern=SLUG_RE, what="a lowercase slug")
    _str(project["name"], f"{path}.name", min_len=1, max_len=CAPS["name"])
    _str(project["identifier"], f"{path}.identifier", pattern=IDENTIFIER_RE, nullable=True,
         what="a ticket-provider identifier like JIMB")
    _str(project["workspace"], f"{path}.workspace", pattern=WORKSPACE_RE, nullable=True, what="a workspace slug")
    _uuid(project["board_id"], f"{path}.board_id", nullable=True)
    repos = _list(project["repos"], f"{path}.repos", max_items=CAPS["repos"], unique=True, min_items=1)
    for i, name in enumerate(repos):
        _str(name, f"{path}.repos[{i}]", min_len=1, max_len=CAPS["repo_name"], pattern=REPO_NAME_RE, what="a repo name")
    return project


def _validate_window(window, path: str) -> dict:
    _obj(window, path, ("start", "end", "duration_seconds", "basis", "previous_event_id"),
         ("start", "end", "duration_seconds", "basis", "previous_event_id"))
    start = _timestamp(window["start"], f"{path}.start")
    end = _timestamp(window["end"], f"{path}.end")
    seconds = int((end - start).total_seconds())
    if seconds <= 0:
        raise ContractError(f"{path}.end must be after {path}.start")
    duration = window["duration_seconds"]
    if not _is_int(duration) or duration < 1 or duration > CAPS["duration_max"]:
        raise ContractError(f"{path}.duration_seconds: must be an integer in [1, {CAPS['duration_max']}]")
    if duration != seconds:
        raise ContractError(f"{path}.duration_seconds: must equal end - start ({seconds}s), got {duration}")
    basis = window["basis"]
    if basis not in WINDOW_BASES:
        raise ContractError(f"{path}.basis: must be one of {list(WINDOW_BASES)}, got {basis!r}")
    _uuid(window["previous_event_id"], f"{path}.previous_event_id", nullable=True)
    if basis == "cap_24h" and seconds != 86400:
        raise ContractError(f"{path}: basis cap_24h requires an 86400s window, got {seconds}s")
    if basis == "previous_report" and not window["previous_event_id"]:
        raise ContractError(f"{path}: basis previous_report requires previous_event_id")
    return window


def _validate_report(report, path: str) -> dict:
    _obj(report, path, ("title", "raw", "markdown", "html"), ("title", "raw", "markdown", "html"))
    _str(report["title"], f"{path}.title", min_len=1, max_len=CAPS["title"])
    _str(report["raw"], f"{path}.raw", min_len=1, max_len=CAPS["raw"])
    _str(report["markdown"], f"{path}.markdown", min_len=1, max_len=CAPS["markdown"])
    _str(report["html"], f"{path}.html", min_len=1, max_len=CAPS["html"])
    if not HTML_DOCTYPE_RE.search(report["html"]):
        raise ContractError(f"{path}.html: must start with <!doctype html> (a complete document, not a fragment)")
    return report


def _validate_bucket(bucket, path: str) -> int:
    _obj(bucket, path, ("input", "output", "cache_read", "cache_write", "total"),
         ("input", "output", "cache_read", "cache_write", "total"))
    for key in (*TOKEN_PARTS, "total"):
        _count(bucket[key], f"{path}.{key}")
    parts = sum(bucket[k] for k in TOKEN_PARTS)
    if parts != bucket["total"]:
        raise ContractError(f"{path}.total: must equal input + output + cache_read + cache_write ({parts}), got {bucket['total']}")
    return bucket["total"]


def _validate_tokens(tokens, path: str) -> dict:
    _obj(tokens, path, ("total", "by_agent"), ("total", "by_agent"))
    _count(tokens["total"], f"{path}.total")
    by_agent = tokens["by_agent"]
    if not isinstance(by_agent, dict):
        raise ContractError(f"{path}.by_agent: must be an object")
    if len(by_agent) > CAPS["by_agent"]:
        raise ContractError(f"{path}.by_agent: more than {CAPS['by_agent']} agents")
    grand = 0
    for agent, bucket in by_agent.items():
        _str(agent, f"{path}.by_agent key", pattern=AGENT_KEY_RE, what="an agent key like claude")
        if bucket is None:
            continue
        grand += _validate_bucket(bucket, f"{path}.by_agent.{agent}")
    if tokens["total"] != grand:
        raise ContractError(f"{path}.total: must equal the sum of by_agent totals ({grand}), got {tokens['total']}")
    return tokens


def _validate_generator(generator, path: str) -> dict:
    _obj(generator, path, ("skill", "skill_version", "run_id", "model", "dry_run"),
         ("skill", "skill_version", "run_id", "model", "dry_run"))
    _str(generator["skill"], f"{path}.skill", pattern=SKILL_RE, what="a skill name")
    _str(generator["skill_version"], f"{path}.skill_version", pattern=SEMVER_RE, what="major.minor.patch")
    _uuid(generator["run_id"], f"{path}.run_id", nullable=False)
    _str(generator["model"], f"{path}.model", max_len=CAPS["model"], nullable=True)
    _bool(generator["dry_run"], f"{path}.dry_run")
    return generator


def _validate_commit(commit, path: str) -> None:
    _obj(commit, path, ("sha", "subject", "author", "at"), ("sha", "subject", "author", "at"))
    _str(commit["sha"], f"{path}.sha", pattern=SHA_RE, what="7-40 lowercase hex")
    _str(commit["subject"], f"{path}.subject", min_len=1, max_len=CAPS["subject"])
    _str(commit["author"], f"{path}.author", min_len=1, max_len=CAPS["author"])
    _timestamp(commit["at"], f"{path}.at")


def _validate_git_repo(repo, path: str) -> None:
    _obj(repo, path, ("commits", "truncated", "branches", "files_changed", "insertions", "deletions"),
         ("commits", "truncated", "branches", "files_changed", "insertions", "deletions"))
    commits = _list(repo["commits"], f"{path}.commits", max_items=CAPS["commits"])
    for i, commit in enumerate(commits):
        _validate_commit(commit, f"{path}.commits[{i}]")
    _bool(repo["truncated"], f"{path}.truncated")
    branches = _list(repo["branches"], f"{path}.branches", max_items=CAPS["branches"], unique=True)
    for i, branch in enumerate(branches):
        _str(branch, f"{path}.branches[{i}]", min_len=1, max_len=CAPS["branch"])
    for key in ("files_changed", "insertions", "deletions"):
        _count(repo[key], f"{path}.{key}")


def _validate_ticket_keys(items, path: str) -> None:
    keys = _list(items, path, max_items=CAPS["ticket_list"], unique=True)
    for i, key in enumerate(keys):
        _str(key, f"{path}[{i}]", pattern=TICKET_KEY_RE, what="a ticket key like JIMB-214")


def _validate_sources(sources, path: str) -> dict:
    _obj(sources, path, ("git", "candystore", "board", "hindsight"), ("git", "candystore", "board", "hindsight"))
    git = sources["git"]
    if not isinstance(git, dict):
        raise ContractError(f"{path}.git: must be an object keyed by repo name")
    if len(git) > CAPS["git_repos"]:
        raise ContractError(f"{path}.git: more than {CAPS['git_repos']} repos")
    for name, repo in git.items():
        _str(name, f"{path}.git key", min_len=1, max_len=CAPS["repo_name"], pattern=REPO_NAME_RE, what="a repo name")
        _validate_git_repo(repo, f"{path}.git.{name}")
    cs = _obj(sources["candystore"], f"{path}.candystore", ("sessions", "tool_calls", "by_cli"),
              ("sessions", "tool_calls", "by_cli"))
    _count(cs["sessions"], f"{path}.candystore.sessions")
    _count(cs["tool_calls"], f"{path}.candystore.tool_calls")
    by_cli = cs["by_cli"]
    if not isinstance(by_cli, dict):
        raise ContractError(f"{path}.candystore.by_cli: must be an object")
    if len(by_cli) > CAPS["by_cli"]:
        raise ContractError(f"{path}.candystore.by_cli: more than {CAPS['by_cli']} clis")
    for cli, n in by_cli.items():
        _str(cli, f"{path}.candystore.by_cli key", pattern=AGENT_KEY_RE, what="an agent key like claude")
        _count(n, f"{path}.candystore.by_cli.{cli}")
    board = _obj(sources["board"], f"{path}.board", ("closed", "opened", "started"), ("closed", "opened", "started"))
    for key in ("closed", "opened", "started"):
        _validate_ticket_keys(board[key], f"{path}.board.{key}")
    hs = _obj(sources["hindsight"], f"{path}.hindsight", ("bank", "facts"), ("bank", "facts"))
    _str(hs["bank"], f"{path}.hindsight.bank", min_len=1, max_len=CAPS["bank"], pattern=BANK_RE, what="a bank name")
    _count(hs["facts"], f"{path}.hindsight.facts")
    return sources


def _validate_tickets(tickets, path: str) -> list:
    items = _list(tickets, path, max_items=CAPS["tickets"])
    for i, ticket in enumerate(items):
        p = f"{path}[{i}]"
        _obj(ticket, p, ("key", "title", "from_state", "to_state", "labels", "exposure"),
             ("key", "title", "from_state", "to_state", "labels", "exposure"))
        _str(ticket["key"], f"{p}.key", pattern=TICKET_KEY_RE, what="a ticket key like JIMB-214")
        _str(ticket["title"], f"{p}.title", min_len=1, max_len=CAPS["ticket_title"])
        _str(ticket["from_state"], f"{p}.from_state", max_len=CAPS["state"], nullable=True)
        _str(ticket["to_state"], f"{p}.to_state", max_len=CAPS["state"], nullable=True)
        labels = _list(ticket["labels"], f"{p}.labels", max_items=CAPS["labels"], unique=True)
        for j, label in enumerate(labels):
            _str(label, f"{p}.labels[{j}]", min_len=1, max_len=CAPS["label"])
        if ticket["exposure"] not in EXPOSURES:
            raise ContractError(f"{p}.exposure: must be one of {list(EXPOSURES)}, got {ticket['exposure']!r}")
    return items


def external_text_markers(identifier: str | None) -> list[tuple[re.Pattern, str]]:
    """The markers §11.4 refuses in external title/raw/markdown, in the validator's order."""
    markers: list[tuple[re.Pattern, str]] = []
    if isinstance(identifier, str) and identifier:
        markers.append((re.compile(rf"\b{re.escape(identifier)}-\d+\b"), "a ticket key"))
    markers.append((_PROJECT_SHA, "a commit sha"))
    markers.append((_PROJECT_ABS_PATH, "an absolute filesystem path"))
    return markers


def _external_hygiene(data: dict) -> None:
    identifier = data["project"].get("identifier")
    markers = external_text_markers(identifier)
    ticket_only = [m for m in markers if m[1] == "a ticket key"]
    report = data["report"]
    for field in ("title", "raw", "markdown"):
        for pattern, what in markers:
            hit = pattern.search(report[field])
            if hit:
                raise ContractError(
                    f"data.report.{field}: external report contains {what} ({hit.group(0)!r}); "
                    "that fact belongs on the audience=internal event")
    for pattern, what in ticket_only:
        hit = pattern.search(report["html"])
        if hit:
            raise ContractError(f"data.report.html: external report contains {what} ({hit.group(0)!r})")


# -- entry points --------------------------------------------------------------

def assert_no_paths(obj, path: str = "data") -> None:
    """Refuse an absolute workstation path in any string anywhere in the data (keys included)."""
    if isinstance(obj, str):
        hit = NO_ABSOLUTE_PATH_RE.search(obj)
        if hit:
            raise ContractError(f"{path}: contains an absolute filesystem path ({hit.group(0).strip()!r}...)")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            assert_no_paths(key, f"{path} key")
            assert_no_paths(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            assert_no_paths(value, f"{path}[{i}]")


def validate_event(data: dict) -> None:
    """Validate one event `data` object against the schema and the §11.4 invariants."""
    _obj(data, "data",
         ("schema_version", "project", "audience", "window", "report", "tokens", "generator", "sources", "tickets"),
         ("schema_version", "project", "audience", "window", "report", "tokens", "generator"))
    if not _is_int(data["schema_version"]) or data["schema_version"] != 1:
        raise ContractError("data.schema_version: must be 1")
    _validate_project(data["project"], "data.project")
    audience = data["audience"]
    if audience not in AUDIENCES:
        raise ContractError(f"data.audience: must be internal or external, got {audience!r}")
    _validate_window(data["window"], "data.window")
    _validate_report(data["report"], "data.report")
    _validate_tokens(data["tokens"], "data.tokens")
    _validate_generator(data["generator"], "data.generator")
    if audience == "external":
        present = [f for f in INTERNAL_ONLY_FIELDS if f in data]
        if present:
            raise ContractError(f"data: an external report must not carry {present}")
        _external_hygiene(data)
    else:
        missing = [f for f in INTERNAL_ONLY_FIELDS if f not in data]
        if missing:
            raise ContractError(f"data: an internal report must carry {missing}")
        _validate_sources(data["sources"], "data.sources")
        _validate_tickets(data["tickets"], "data.tickets")
    assert_no_paths(data)
