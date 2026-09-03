"""digest + raw.txt + markdown + html -> the event `data` object, validated.

The mapping is the table in references/internals.md. Everything is truncated
to the schema's caps here rather than refused, because the caps are about
event size, not about the report: a repo with 140 commits still gets its
event, with `truncated: true`. Text caps (title 180, raw 5000) are NOT
truncated: lint refused those already, and if it did not, the contract
check at the end fails loudly rather than silently shortening prose.
"""
from __future__ import annotations

import json
import os

from . import __version__
from .common import (
    AUDIENCES, EXIT_OK, SKILL_NAME, TOKEN_AGENTS, ConfigError, SkillError, parse_iso, read_json,
    to_iso_z, write_json,
)
from .contract import (
    AGENT_KEY_RE, BANK_RE, CAPS, EXPOSURES, REPO_NAME_RE, SHA_RE, TICKET_KEY_RE, TOKEN_PARTS,
    assert_no_paths, validate_event,
)
from .render import split_raw


def _trunc(value, n: int) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= n else text[:n]


def _int(value) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _ts(value) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return to_iso_z(parse_iso(value))
    except ValueError:
        return None


def _unique_str(items, cap_items: int, cap_len: int) -> list[str]:
    out: list[str] = []
    for item in items or []:
        text = _trunc(item, cap_len).strip()
        if text and text not in out:
            out.append(text)
        if len(out) >= cap_items:
            break
    return out


def _project(digest: dict) -> dict:
    src = digest.get("project") or {}
    return {
        "slug": src.get("slug"),
        "name": _trunc(src.get("name") or src.get("slug"), CAPS["name"]),
        "identifier": src.get("identifier") or None,
        "workspace": src.get("workspace") or None,
        "board_id": src.get("board_id") or None,
        "repos": _unique_str(src.get("repos"), CAPS["repos"], CAPS["repo_name"]),
    }


def _window(digest: dict) -> dict:
    src = digest.get("window") or {}
    return {
        "start": src.get("start"),
        "end": src.get("end"),
        "duration_seconds": src.get("duration_seconds"),
        "basis": src.get("basis"),
        "previous_event_id": src.get("previous_event_id") or None,
    }


def _bucket(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    bucket = {part: _int(raw.get(part)) for part in TOKEN_PARTS}
    bucket["total"] = sum(bucket.values())
    return bucket


def _tokens(digest: dict) -> dict:
    by_agent_raw = (digest.get("tokens") or {}).get("by_agent") or {}
    by_agent = {agent: _bucket(by_agent_raw.get(agent)) for agent in TOKEN_AGENTS}
    total = sum(bucket["total"] for bucket in by_agent.values() if bucket)
    return {"total": total, "by_agent": by_agent}


def _git(digest: dict) -> dict:
    git: dict = {}
    for repo in (digest.get("git") or {}).get("repos") or []:
        if not isinstance(repo, dict) or repo.get("state") != "ok":
            continue
        name = repo.get("name")
        if not isinstance(name, str) or not REPO_NAME_RE.match(name) or len(name) > CAPS["repo_name"]:
            continue
        if len(git) >= CAPS["git_repos"]:
            break
        commits = []
        for commit in repo.get("commits") or []:
            if not isinstance(commit, dict):
                continue
            sha = str(commit.get("sha") or commit.get("short") or "").strip().lower()
            at = _ts(commit.get("at"))
            if not SHA_RE.match(sha) or at is None:
                continue
            commits.append({
                "sha": sha,
                "subject": _trunc(commit.get("subject"), CAPS["subject"]).strip() or "(no subject)",
                "author": _trunc(commit.get("author"), CAPS["author"]).strip() or "unknown",
                "at": at,
            })
        truncated = bool(repo.get("truncated")) or len(commits) > CAPS["commits"]
        git[name] = {
            "commits": commits[:CAPS["commits"]],
            "truncated": truncated,
            "branches": _unique_str(repo.get("branches"), CAPS["branches"], CAPS["branch"]),
            "files_changed": _int(repo.get("files_changed")),
            "insertions": _int(repo.get("insertions")),
            "deletions": _int(repo.get("deletions")),
        }
    return git


def _ticket_keys(items) -> list[str]:
    keys: list[str] = []
    for item in items or []:
        key = item.get("key") if isinstance(item, dict) else item
        if isinstance(key, str) and TICKET_KEY_RE.match(key) and key not in keys:
            keys.append(key)
        if len(keys) >= CAPS["ticket_list"]:
            break
    return keys


def _sources(digest: dict) -> dict:
    cs = digest.get("candystore") or {}
    by_cli: dict = {}
    for cli, count in (cs.get("by_cli") or {}).items():
        key = str(cli).strip().lower()
        if AGENT_KEY_RE.match(key) and key not in by_cli:
            by_cli[key] = _int(count)
        if len(by_cli) >= CAPS["by_cli"]:
            break
    board = digest.get("board") or {}
    hs = digest.get("hindsight") or {}
    items = hs.get("items")
    facts = len(items) if isinstance(items, list) else _int(items)
    bank = _trunc(hs.get("bank") or "", CAPS["bank"]).strip()
    if not bank or not BANK_RE.match(bank):
        bank = _trunc((digest.get("project") or {}).get("slug") or "unknown", CAPS["bank"])
    return {
        "git": _git(digest),
        "candystore": {
            "sessions": _int(cs.get("sessions")),
            "tool_calls": _int(cs.get("tool_calls_total")),
            "by_cli": by_cli,
        },
        "board": {
            "closed": _ticket_keys(board.get("closed")),
            "opened": _ticket_keys(board.get("opened")),
            "started": _ticket_keys(board.get("started")),
        },
        "hindsight": {"bank": bank, "facts": facts},
    }


def _tickets(digest: dict) -> list[dict]:
    out: list[dict] = []
    for ticket in ((digest.get("board") or {}).get("tickets") or []):
        if not isinstance(ticket, dict):
            continue
        key = ticket.get("key")
        if not isinstance(key, str) or not TICKET_KEY_RE.match(key):
            continue
        from_state = ticket.get("from_state")
        to_state = ticket.get("to_state")
        exposure = ticket.get("exposure")
        out.append({
            "key": key,
            "title": _trunc(ticket.get("title"), CAPS["ticket_title"]).strip() or key,
            "from_state": _trunc(from_state, CAPS["state"]) if isinstance(from_state, str) and from_state else None,
            "to_state": _trunc(to_state, CAPS["state"]) if isinstance(to_state, str) and to_state else None,
            "labels": _unique_str(ticket.get("labels"), CAPS["labels"], CAPS["label"]),
            "exposure": exposure if exposure in EXPOSURES else "unlabeled",
        })
        if len(out) >= CAPS["tickets"]:
            break
    return out


def assemble(digest: dict, raw_text: str, markdown: str, html: str, model: str | None, dry_run: bool) -> dict:
    audience = digest.get("audience")
    if audience not in AUDIENCES:
        raise ConfigError(f"digest.audience must be internal or external, got {audience!r}")
    title, body = split_raw(raw_text)
    data = {
        "schema_version": 1,
        "project": _project(digest),
        "audience": audience,
        "window": _window(digest),
        "report": {"title": title, "raw": body, "markdown": markdown, "html": html},
        "tokens": _tokens(digest),
        "generator": {
            "skill": SKILL_NAME,
            "skill_version": __version__,
            "run_id": digest.get("run_id"),
            "model": _trunc(model, CAPS["model"]) if model else None,
            "dry_run": bool(dry_run),
        },
    }
    if audience == "internal":
        data["sources"] = _sources(digest)
        data["tickets"] = _tickets(digest)
    validate_event(data)
    assert_no_paths(data)
    return data


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def assemble_cmd(args) -> int:
    digest = read_json(args.digest)
    if digest.get("audience") != args.audience:
        raise ConfigError(f"digest {args.digest} is for audience {digest.get('audience')!r}, "
                          f"assemble asked for {args.audience!r}")
    model = args.model
    if not model:
        try:
            from .config import load_project
            project = load_project(getattr(args, "project", None))
            model = ((project.config or {}).get("compose") or {}).get("model") or None
        except SkillError:
            model = None
    data = assemble(digest, _read(args.raw), _read(args.md), _read(args.html), model, bool(args.dry_run))
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.digest)),
                                   f"{digest.get('label') or 'report'}-{args.audience}.event.json")
    write_json(out, data)
    size = os.path.getsize(out)
    result = {"event": out, "bytes": size, "run_id": data["generator"]["run_id"], "audience": args.audience,
              "dry_run": data["generator"]["dry_run"], "model": data["generator"]["model"],
              "title": data["report"]["title"]}
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    else:
        print(f"event: {out} ({size} bytes, {args.audience}, run {data['generator']['run_id']}, "
              f"dry_run={str(data['generator']['dry_run']).lower()}) — contract ok")
    return EXIT_OK
