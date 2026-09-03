"""Orchestrate the collectors into `<label>-<audience>.digest.json`.

Order: resolve project and scope, window, Candystore (required), git, board,
Hindsight, tokens. Each collector returns its block with a `caveats` list;
those are hoisted, prefixed with the source, into the top-level `caveats`.
Every string in the digest except the scope and the worktree paths has
absolute paths scrubbed (`/home/<user>/x` becomes `~/x`), then
`validate_digest` refuses anything that still does not match the contract.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime

from . import board, candystore, gitscan, hindsight, tokens, window as window_mod
from .common import AUDIENCES, TOKEN_AGENTS, ConfigError, ContractError, parse_iso, runtime_paths, to_iso_z, utc_now, write_json
from .config import load_project, scope_set

SCHEMA_VERSION = 1
TOP_KEYS = ("schema_version", "run_id", "generated_at", "audience", "label", "project", "window", "previous_report",
            "scope", "candystore", "git", "board", "hindsight", "tokens", "caveats")
RAW_EXCERPT_CHARS = 600
REPO_CAP = 8
COMMIT_CAP = 100
BRANCH_CAP = 64
TICKET_CAP = 200
LABEL_CAP = 8
FAILURE_CAP = 40
BY_TOOL_CAP = 12
HINDSIGHT_ITEM_CAP = 40
RECALL_CAP = 20

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
LABEL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}$")
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
AGENT_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
TICKET_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,11}-[0-9]+$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
ABSOLUTE_PATH_RE = re.compile(r"(^|[^A-Za-z0-9_.])/(home|Users|root|tmp|var|etc|opt|srv|mnt)/")
_HOME_RE = re.compile(r"(^|(?<=[^A-Za-z0-9_.]))/(?:home|Users)/[^/\s'\"]*/?")
_ROOT_RE = re.compile(r"(^|(?<=[^A-Za-z0-9_.]))/root/")
_OTHER_RE = re.compile(r"(^|(?<=[^A-Za-z0-9_.]))/(tmp|var|etc|opt|srv|mnt)/")
WINDOW_BASES = ("previous_report", "cap_24h", "explicit")
BOARD_STATUSES = ("ok", "unavailable", "unsupported")
HINDSIGHT_STATUSES = ("ok", "unavailable", "disabled")
REPO_STATES = ("ok", "missing", "failed")
EXPOSURES = ("external", "internal", "unlabeled")


# -- helpers --------------------------------------------------------------------

def scrub_paths(text: str) -> str:
    """`/home/<user>/x` -> `~/x`; `/tmp/x` -> `tmp/x`. Keeps the readable tail, drops the machine."""
    text = _HOME_RE.sub("~/", text)
    text = _ROOT_RE.sub("~/", text)
    return _OTHER_RE.sub(lambda m: m.group(2) + "/", text)


def scrub(obj):
    if isinstance(obj, str):
        return scrub_paths(obj)
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    return obj


def _hoist(caveats: list[str], block: dict, source: str) -> dict:
    for caveat in block.pop("caveats", None) or []:
        caveats.append(f"{source}: {caveat}")
    return block


def normalise_run_id(value: str | None) -> str:
    if not value:
        return str(uuid.uuid4())
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as exc:
        raise ConfigError(f"--run-id {value!r} is not a UUID") from exc


def digest_path(project, label: str, audience: str, out_path: str | None = None) -> str:
    return os.path.abspath(out_path) if out_path else runtime_paths(project, label, audience)["digest"]


def lint_json_path(project, label: str, out_path: str | None = None) -> str:
    if out_path:
        return os.path.join(os.path.dirname(os.path.abspath(out_path)), f"{label}-external.lint.json")
    return runtime_paths(project, label, "external")["lint_json"]


# -- collect --------------------------------------------------------------------

def collect(project, audience: str, window, run_id: str, out_path: str | None = None) -> dict:
    """Build, validate and write the digest for one audience. Returns the digest."""
    if audience not in AUDIENCES:
        raise ConfigError(f"audience must be one of {list(AUDIENCES)}, got {audience!r}")
    run_id = normalise_run_id(run_id)
    label = window.label(project.tz)
    scope = scope_set(project)
    caveats: list[str] = [f"window: {c}" for c in window.caveats]
    for missing in scope.missing:
        caveats.append(f"scope: configured root {missing} is not a git checkout")

    candy = _hoist(caveats, candystore.collect_tools(scope, window), "candystore")
    candy["sessions_ended"] = candystore.collect_sessions_ended(scope, window)
    candy = {k: candy[k] for k in ("reachable", "base_url", "tool_calls_total", "failed", "unknown_outcome", "by_cli",
                                   "by_tool", "sessions", "sessions_by_cli", "branches_touched", "deploy_commands",
                                   "failures", "sessions_ended", "coverage")}
    ticket_events = candystore.collect_tickets(project.slug, window, identifier=project.identifier)
    decisions = candystore.collect_decisions(project.slug, window)
    git = _hoist(caveats, gitscan.scan(project, scope, window), "git")
    board_block, lint_json = board.enrich(project, ticket_events, window, audience)
    board_block = _hoist(caveats, board_block, "board")
    board_block["decisions"] = decisions
    hs = _hoist(caveats, hindsight.collect(project, window), "hindsight")
    tok = _hoist(caveats, tokens.collect(scope, window), "tokens")

    previous = None
    if window.previous:
        raw = window.previous.get("raw")
        previous = {
            "event_id": window.previous.get("event_id"),
            "window_end": window.previous.get("window_end"),
            "title": window.previous.get("title"),
            "raw_excerpt": raw[:RAW_EXCERPT_CHARS] if isinstance(raw, str) else None,
        }

    repos = list(project.repo_names)
    if len(repos) > REPO_CAP:
        caveats.append(f"project: {len(repos)} repos configured; project.repos lists the first {REPO_CAP}")
        repos = repos[:REPO_CAP]

    # Absolute paths survive only in scope and git.repos[].worktrees[].path.
    for repo in git.get("repos") or []:
        worktrees = repo.pop("worktrees", [])
        repo.update(scrub(repo))
        repo["worktrees"] = [{**scrub({k: v for k, v in wt.items() if k != "path"}), "path": wt.get("path")} for wt in worktrees]
        repo = {k: repo[k] for k in ("name", "state", "default_branch", "commit_count", "on_default", "off_default", "replays",
                                     "truncated", "commits", "branches", "worktrees", "uncommitted_files", "files_changed",
                                     "insertions", "deletions")}
    git["repos"] = [{k: r[k] for k in ("name", "state", "default_branch", "commit_count", "on_default", "off_default", "replays",
                                       "truncated", "commits", "branches", "worktrees", "uncommitted_files", "files_changed",
                                       "insertions", "deletions")} for r in git.get("repos") or []]

    digest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at": to_iso_z(utc_now()),
        "audience": audience,
        "label": label,
        "project": {
            "slug": project.slug, "name": project.name, "identifier": project.identifier,
            "workspace": project.workspace, "board_id": project.board_id, "repos": repos, "timezone": project.tz,
        },
        "window": window.as_dict(),
        "previous_report": scrub(previous),
        "scope": {"roots": list(scope.roots), "worktrees": list(scope.worktrees)},
        "candystore": scrub(candy),
        "git": git,
        "board": scrub(board_block),
        "hindsight": scrub(hs),
        "tokens": scrub(tok),
        "caveats": scrub(caveats),
    }
    validate_digest(digest)
    write_json(digest_path(project, label, audience, out_path), digest)
    if audience == "external" and lint_json is not None:
        write_json(lint_json_path(project, label, out_path), scrub(lint_json))
    return digest


# -- validation -----------------------------------------------------------------

def _fail(path: str, rule: str):
    raise ContractError(f"digest.{path}: {rule}")


def _obj(value, path: str, required: tuple = ()) -> dict:
    if not isinstance(value, dict):
        _fail(path, "must be an object")
    for key in required:
        if key not in value:
            _fail(path, f"missing key {key!r}")
    return value


def _count(value, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail(path, "must be a non-negative integer")
    return value


def _str(value, path: str, *, max_len: int | None = None, nullable: bool = False, pattern=None) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        _fail(path, "must be a string")
    if max_len is not None and len(value) > max_len:
        _fail(path, f"longer than {max_len} characters")
    if pattern is not None and not pattern.match(value):
        _fail(path, f"does not match {pattern.pattern}")
    return value


def _list(value, path: str, *, max_items: int | None = None) -> list:
    if not isinstance(value, list):
        _fail(path, "must be a list")
    if max_items is not None and len(value) > max_items:
        _fail(path, f"more than {max_items} items")
    return value


def _timestamp(value, path: str, nullable: bool = False) -> datetime | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        _fail(path, "must be an RFC 3339 UTC timestamp ending in Z")
    try:
        return parse_iso(value)
    except ValueError:
        _fail(path, "is not a timestamp")
    return None


def _enum(value, path: str, allowed: tuple, nullable: bool = False):
    if value is None and nullable:
        return None
    if value not in allowed:
        _fail(path, f"must be one of {list(allowed)}, got {value!r}")
    return value


def _bucket(value, path: str) -> int | None:
    if value is None:
        return None
    _obj(value, path, ("input", "output", "cache_read", "cache_write", "total"))
    parts = sum(_count(value[k], f"{path}.{k}") for k in ("input", "output", "cache_read", "cache_write"))
    total = _count(value["total"], f"{path}.total")
    if total != parts:
        _fail(path, f"total {total} is not the sum of its parts ({parts})")
    return total


def _no_paths(obj, path: str) -> None:
    if isinstance(obj, str):
        if ABSOLUTE_PATH_RE.search(obj):
            _fail(path, f"carries an absolute path: {obj[:80]!r}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _no_paths(item, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for key, item in obj.items():
            _no_paths(item, f"{path}.{key}")


def validate_digest(d: dict) -> None:
    """Raise ContractError unless `d` has the shape references/internals.md promises the compose agent."""
    _obj(d, "", TOP_KEYS)
    if d["schema_version"] != SCHEMA_VERSION:
        _fail("schema_version", f"must be {SCHEMA_VERSION}")
    _str(d["run_id"], "run_id", pattern=UUID_RE)
    _timestamp(d["generated_at"], "generated_at")
    audience = _enum(d["audience"], "audience", AUDIENCES)
    _str(d["label"], "label", pattern=LABEL_RE)

    project = _obj(d["project"], "project", ("slug", "name", "identifier", "workspace", "board_id", "repos", "timezone"))
    _str(project["slug"], "project.slug", max_len=64)
    _str(project["name"], "project.name", max_len=120)
    _str(project["identifier"], "project.identifier", nullable=True, max_len=12)
    for i, name in enumerate(_list(project["repos"], "project.repos", max_items=REPO_CAP)):
        _str(name, f"project.repos[{i}]", max_len=100, pattern=REPO_NAME_RE)

    window = _obj(d["window"], "window", ("start", "end", "duration_seconds", "basis", "previous_event_id"))
    start = _timestamp(window["start"], "window.start")
    end = _timestamp(window["end"], "window.end")
    seconds = int((end - start).total_seconds())
    if seconds <= 0:
        _fail("window", "end must be after start")
    if _count(window["duration_seconds"], "window.duration_seconds") != seconds:
        _fail("window.duration_seconds", f"must equal end - start ({seconds})")
    basis = _enum(window["basis"], "window.basis", WINDOW_BASES)
    _str(window["previous_event_id"], "window.previous_event_id", nullable=True, pattern=UUID_RE)
    if basis == "cap_24h" and seconds != 86400:
        _fail("window", f"basis cap_24h requires exactly 86400 s, got {seconds}")
    if basis == "previous_report" and not window["previous_event_id"]:
        _fail("window.previous_event_id", "required when basis is previous_report")

    if d["previous_report"] is not None:
        previous = _obj(d["previous_report"], "previous_report", ("event_id", "window_end", "title", "raw_excerpt"))
        _str(previous["event_id"], "previous_report.event_id", pattern=UUID_RE)
        _timestamp(previous["window_end"], "previous_report.window_end")
        _str(previous["raw_excerpt"], "previous_report.raw_excerpt", nullable=True, max_len=RAW_EXCERPT_CHARS)

    scope = _obj(d["scope"], "scope", ("roots", "worktrees"))
    for key in ("roots", "worktrees"):
        for i, item in enumerate(_list(scope[key], f"scope.{key}")):
            if not isinstance(item, str) or not os.path.isabs(item):
                _fail(f"scope.{key}[{i}]", "must be an absolute path")

    candy = _obj(d["candystore"], "candystore", ("reachable", "base_url", "tool_calls_total", "failed", "unknown_outcome",
                                                  "by_cli", "by_tool", "sessions", "sessions_by_cli", "branches_touched",
                                                  "deploy_commands", "failures", "sessions_ended", "coverage"))
    if candy["reachable"] is not True:
        _fail("candystore.reachable", "must be true; an unreachable store is exit 2, not a digest")
    for key in ("tool_calls_total", "failed", "unknown_outcome", "sessions"):
        _count(candy[key], f"candystore.{key}")
    for key in ("by_cli", "sessions_by_cli"):
        for agent, n in _obj(candy[key], f"candystore.{key}").items():
            _str(agent, f"candystore.{key} key", pattern=AGENT_KEY_RE)
            _count(n, f"candystore.{key}.{agent}")
    if len(_obj(candy["by_tool"], "candystore.by_tool")) > BY_TOOL_CAP:
        _fail("candystore.by_tool", f"more than {BY_TOOL_CAP} tools")
    _list(candy["branches_touched"], "candystore.branches_touched", max_items=BRANCH_CAP)
    for i, item in enumerate(_list(candy["failures"], "candystore.failures", max_items=FAILURE_CAP)):
        _obj(item, f"candystore.failures[{i}]", ("at", "cli", "tool", "detail"))
    for i, item in enumerate(_list(candy["deploy_commands"], "candystore.deploy_commands")):
        _obj(item, f"candystore.deploy_commands[{i}]", ("at", "cli", "command"))
    ended = _obj(candy["sessions_ended"], "candystore.sessions_ended", ("count", "turns", "duration_seconds", "by_cli"))
    for key in ("count", "turns", "duration_seconds"):
        _count(ended[key], f"candystore.sessions_ended.{key}")
    _obj(candy["coverage"], "candystore.coverage", ("total", "fetched", "pages", "truncated"))

    git = _obj(d["git"], "git", ("commit_count", "repos"))
    _count(git["commit_count"], "git.commit_count")
    seen_repos: set[str] = set()
    for i, repo in enumerate(_list(git["repos"], "git.repos", max_items=REPO_CAP)):
        p = f"git.repos[{i}]"
        _obj(repo, p, ("name", "state", "default_branch", "commit_count", "on_default", "off_default", "replays", "truncated",
                       "commits", "branches", "worktrees", "uncommitted_files", "files_changed", "insertions", "deletions"))
        name = _str(repo["name"], f"{p}.name", max_len=100, pattern=REPO_NAME_RE)
        if name in seen_repos:
            _fail(f"{p}.name", "duplicate repo name")
        seen_repos.add(name)
        _enum(repo["state"], f"{p}.state", REPO_STATES)
        for key in ("commit_count", "on_default", "off_default", "replays", "uncommitted_files", "files_changed", "insertions", "deletions"):
            _count(repo[key], f"{p}.{key}")
        if not isinstance(repo["truncated"], bool):
            _fail(f"{p}.truncated", "must be a boolean")
        commits = _list(repo["commits"], f"{p}.commits", max_items=COMMIT_CAP)
        if repo["truncated"] != (repo["commit_count"] > len(commits)):
            _fail(f"{p}.truncated", "must be true exactly when commit_count exceeds the listed commits")
        for j, commit in enumerate(commits):
            cp = f"{p}.commits[{j}]"
            _obj(commit, cp, ("sha", "short", "at", "author", "subject", "on_default"))
            _str(commit["sha"], f"{cp}.sha", pattern=SHA_RE)
            _str(commit["short"], f"{cp}.short", pattern=SHA_RE)
            _timestamp(commit["at"], f"{cp}.at")
            _str(commit["author"], f"{cp}.author", max_len=80)
            _str(commit["subject"], f"{cp}.subject", max_len=120)
            if not isinstance(commit["on_default"], bool):
                _fail(f"{cp}.on_default", "must be a boolean")
        for j, branch in enumerate(_list(repo["branches"], f"{p}.branches", max_items=BRANCH_CAP)):
            _str(branch, f"{p}.branches[{j}]", max_len=120)
        for j, wt in enumerate(_list(repo["worktrees"], f"{p}.worktrees")):
            _obj(wt, f"{p}.worktrees[{j}]", ("path", "branch", "head", "uncommitted_files"))
            if not isinstance(wt["path"], str) or not os.path.isabs(wt["path"]):
                _fail(f"{p}.worktrees[{j}].path", "must be an absolute path")

    board_block = _obj(d["board"], "board", ("provider", "status", "labels_resolved", "exposure_labels", "tickets", "opened",
                                             "closed", "started", "started", "commented", "decisions"))
    _enum(board_block["status"], "board.status", BOARD_STATUSES)
    _obj(board_block["exposure_labels"], "board.exposure_labels", ("external", "internal"))
    keys: set[str] = set()
    for i, ticket in enumerate(_list(board_block["tickets"], "board.tickets", max_items=TICKET_CAP)):
        tp = f"board.tickets[{i}]"
        _obj(ticket, tp, ("key", "title", "from_state", "to_state", "event_kinds", "labels", "exposure", "surface",
                          "description_excerpt", "url", "first_seen", "last_seen"))
        key = _str(ticket["key"], f"{tp}.key", pattern=TICKET_KEY_RE)
        if key in keys:
            _fail(f"{tp}.key", "duplicate ticket key")
        keys.add(key)
        _str(ticket["title"], f"{tp}.title", max_len=200)
        _str(ticket["from_state"], f"{tp}.from_state", nullable=True, max_len=64)
        _str(ticket["to_state"], f"{tp}.to_state", nullable=True, max_len=64)
        _list(ticket["event_kinds"], f"{tp}.event_kinds")
        for j, label in enumerate(_list(ticket["labels"], f"{tp}.labels", max_items=LABEL_CAP)):
            _str(label, f"{tp}.labels[{j}]", max_len=40)
        exposure = _enum(ticket["exposure"], f"{tp}.exposure", EXPOSURES)
        if audience == "internal":
            if ticket["surface"] is not None:
                _fail(f"{tp}.surface", "must be null in an internal digest")
        else:
            if exposure == "internal":
                _fail(f"{tp}.exposure", "internal tickets never appear in an external digest")
            expected = "always" if exposure == "external" else "judgment"
            if ticket["surface"] != expected:
                _fail(f"{tp}.surface", f"must be {expected!r} for exposure {exposure}")
        _str(ticket["description_excerpt"], f"{tp}.description_excerpt", nullable=True, max_len=600)
        _str(ticket["url"], f"{tp}.url", nullable=True)
        _timestamp(ticket["first_seen"], f"{tp}.first_seen")
        _timestamp(ticket["last_seen"], f"{tp}.last_seen")
    for key in ("opened", "closed", "started", "commented"):
        for i, item in enumerate(_list(board_block[key], f"board.{key}", max_items=TICKET_CAP)):
            _str(item, f"board.{key}[{i}]", pattern=TICKET_KEY_RE)
            if item not in keys:
                _fail(f"board.{key}[{i}]", "names a ticket that is not in board.tickets")
    for i, item in enumerate(_list(board_block["decisions"], "board.decisions")):
        _obj(item, f"board.decisions[{i}]", ("at", "title", "note"))

    hs = _obj(d["hindsight"], "hindsight", ("bank", "status", "items", "recall"))
    _enum(hs["status"], "hindsight.status", HINDSIGHT_STATUSES)
    _str(hs["bank"], "hindsight.bank", nullable=True, max_len=64)
    for i, item in enumerate(_list(hs["items"], "hindsight.items", max_items=HINDSIGHT_ITEM_CAP)):
        _obj(item, f"hindsight.items[{i}]", ("at", "fact_type", "text"))
    recall = _obj(hs["recall"], "hindsight.recall", ("query", "items"))
    _list(recall["items"], "hindsight.recall.items", max_items=RECALL_CAP)

    tok = _obj(d["tokens"], "tokens", ("total", "by_agent", "detail"))
    by_agent = _obj(tok["by_agent"], "tokens.by_agent", TOKEN_AGENTS)
    if set(by_agent) != set(TOKEN_AGENTS):
        _fail("tokens.by_agent", f"keys must be exactly {list(TOKEN_AGENTS)}")
    if by_agent["kimi"] is not None:
        _fail("tokens.by_agent.kimi", "must be null (no transcript source)")
    total = sum(t for t in (_bucket(by_agent[a], f"tokens.by_agent.{a}") for a in TOKEN_AGENTS) if t is not None)
    if _count(tok["total"], "tokens.total") != total:
        _fail("tokens.total", f"must be the sum of the non-null buckets ({total})")
    _obj(tok["detail"], "tokens.detail")

    for i, caveat in enumerate(_list(d["caveats"], "caveats")):
        _str(caveat, f"caveats[{i}]")

    for key in TOP_KEYS:
        if key == "scope":
            continue
        if key == "git":
            for i, repo in enumerate(git["repos"]):
                _no_paths({k: v for k, v in repo.items() if k != "worktrees"}, f"git.repos[{i}]")
                for j, wt in enumerate(repo["worktrees"]):
                    _no_paths({k: v for k, v in wt.items() if k != "path"}, f"git.repos[{i}].worktrees[{j}]")
            continue
        _no_paths(d[key], key)


# -- command --------------------------------------------------------------------

def _summary_lines(digest: dict, path: str, lint_path: str | None) -> list[str]:
    w = digest["window"]
    c = digest["candystore"]
    g = digest["git"]
    b = digest["board"]
    h = digest["hindsight"]
    t = digest["tokens"]
    by_cli = ", ".join(f"{k}={v}" for k, v in c["by_cli"].items()) or "-"
    repos = ", ".join(f"{r['name']}={r['commit_count']}" + ("" if r["state"] == "ok" else f" ({r['state']})") for r in g["repos"]) or "-"
    agents = ", ".join(f"{k}={v['total'] if v else 'null'}" for k, v in t["by_agent"].items())
    lines = [
        f"digest    {path}",
        f"window    {w['start']} -> {w['end']}  ({w['duration_seconds']}s, basis {w['basis']})  label {digest['label']}",
        f"candystore tool calls {c['tool_calls_total']} (failed {c['failed']}, unknown {c['unknown_outcome']}); "
        f"sessions {c['sessions']}; by_cli {by_cli}; ended {c['sessions_ended']['count']}",
        f"git       {g['commit_count']} commits: {repos}",
        f"board     {b['status']}; tickets {len(b['tickets'])}; opened {len(b['opened'])} closed {len(b['closed'])} "
        f"started {len(b['started'])} commented {len(b['commented'])}; decisions {len(b['decisions'])}",
        f"hindsight {h['status']}; items {len(h['items'])}; recall {len(h['recall']['items'])}",
        f"tokens    total {t['total']}; {agents}",
    ]
    if lint_path:
        lines.append(f"lint      {lint_path}")
    for caveat in digest["caveats"]:
        lines.append(f"caveat    {caveat}")
    return lines


def collect_cmd(args) -> int:
    project = load_project(args.project)
    window = window_mod.resolve(project, args.audience, since=args.since, until=args.until, force=args.force)
    run_id = normalise_run_id(getattr(args, "run_id", None))
    out = getattr(args, "out", None)
    digest = collect(project, args.audience, window, run_id, out_path=out)
    path = digest_path(project, digest["label"], args.audience, out)
    lint_path = lint_json_path(project, digest["label"], out) if args.audience == "external" else None
    if args.json:
        print(json.dumps(digest, indent=2, ensure_ascii=False))
        return 0
    for line in _summary_lines(digest, path, lint_path):
        print(line)
    return 0
