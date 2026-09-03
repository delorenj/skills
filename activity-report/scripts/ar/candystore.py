"""Candystore: the HTTP client and every count the digest derives from events.

Five rules, each paid for by a wrong daily count (see references/data-sources.md):

1. Never pass `project=`; the store's project column is the cwd basename.
   Scope is decided here, from the event's working directory against the
   project's ScopeSet (roots + linked worktrees), on a path boundary.
2. The working directory lives in `data.working_directory` for Claude,
   Antigravity and Codex, in `data.payload.cwd` for Hermes and Copilot, and for
   a few Hermes rows only inside the `data.payload.raw` JSON string.
3. `to` is inclusive; events at exactly the window end are dropped here so
   two consecutive windows never share an event.
4. Both namespaces (`bloodbank.x` and `bloodbank.v1.x`) are queried and folded
   through `canonical_type`, along with the pre-rename `tool.tool_call.*` types.
5. A missing outcome is `unknown`, never success; sessions are distinct
   `invocation_id`s, never event volume.

An unreachable store raises SourceUnavailable (exit 2). There is no git-only
digest.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta

from .common import CANDYSTORE_URL, SourceUnavailable, parse_iso, to_iso_z

TIMEOUT_SECONDS = 30
NAMESPACES = ("bloodbank.", "bloodbank.v1.")


def _both(*names: str) -> list[str]:
    return [ns + name for name in names for ns in NAMESPACES]


TOOL_TYPES = _both("agent.tool.completed", "tool.tool_call.completed")
SESSION_TYPES = _both("agent.session.ended")
TASK_TYPES = _both("repo.task.created", "repo.task.updated", "repo.task.appended")
DECISION_TYPES = _both("repo.decision.recorded")
REPORT_TYPES = _both("project.activity.recorded")

_VERSIONED = re.compile(r"^bloodbank\.v[0-9]+\.")
_RENAMED = {"bloodbank.tool.tool_call.": "bloodbank.agent.tool."}
_AGENT_KEY_BAD = re.compile(r"[^a-z0-9_-]+")
_PRODUCER_CLI = {
    "claude-code": "claude", "codex-cli": "codex", "hermes-agent": "hermes", "kimi-code": "kimi",
    "copilot-cli": "copilot", "antigravity": "antigravity", "opencode": "opencode",
}
SUCCESS_OUTCOMES = {"success", "ok", "succeeded", "completed"}
FAILURE_OUTCOMES = {"error", "failed", "failure", "timeout", "exception", "denied"}
_SEG = r"(?:^|[;&|(]\s*|\b(?:then|do|exec|sudo|time|nohup)\s+)"   # the start of a shell command segment
DEPLOY_RE = re.compile(
    _SEG + r"(?:"
    r"mise\s+run\s+\S*deploy"
    r"|(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?\S*deploy"
    r"|wrangler\s+(?:pages\s+)?deploy\b"
    r"|(?:fly|flyctl|cdk|serverless|sls|firebase|vercel|railway|copilot|sam|eb|kamal)\s+deploy\b"
    r"|aws\s+ecs\s+update-service\b"
    r"|gh\s+workflow\s+run\s+\S*deploy"
    r"|(?:bash\s+|sh\s+|\./)?\S*(?:deploy|ecs-build-push)\S*\.(?:sh|py)\b"
    r")", re.IGNORECASE)
CLOSED_PHASES = ("Done", "Cancelled")
CLOSED_GROUPS = ("completed", "cancelled")
STARTED_PHASE = "In Progress"
STARTED_GROUP = "started"

FAILURE_CAP = 40
DEPLOY_CAP = 40
BY_TOOL_TOP = 12
BRANCH_CAP = 64
DECISION_CAP = 50
DETAIL_CHARS = 160
PREVIOUS_LOOKBACK_DAYS = 45
PREVIOUS_PAGE = 25
PREVIOUS_MAX_PAGES = 8
RAW_PARSE_LIMIT = 65536


# -- HTTP ---------------------------------------------------------------------

def fetch_json(url: str, timeout: int = TIMEOUT_SECONDS) -> dict:
    """GET a JSON object. Every failure is SourceUnavailable: the store is required."""
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "activity-report"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        raise SourceUnavailable(f"Candystore answered HTTP {exc.code} for {url}") from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise SourceUnavailable(f"Candystore unreachable at {url}: {exc}") from exc
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise SourceUnavailable(f"Candystore returned non-JSON for {url}") from exc
    if not isinstance(payload, dict):
        raise SourceUnavailable(f"Candystore returned a {type(payload).__name__}, not an object, for {url}")
    return payload


def event_time(event: dict) -> datetime | None:
    value = event.get("time") or event.get("timestamp")
    if not isinstance(value, str):
        return None
    try:
        return parse_iso(value)
    except ValueError:
        return None


def _events_url(base_url: str, params: dict) -> str:
    return f"{base_url.rstrip('/')}/events?{urllib.parse.urlencode(params, safe=',:')}"


def _fetch_pages(types: list[str], start: datetime, end: datetime | None, base_url: str = CANDYSTORE_URL,
                 page_size: int = 1000, max_pages: int = 100) -> tuple[list[dict], int, bool, int]:
    """Offset-paged GET /events. Returns (events with time < end, total, truncated, pages)."""
    params: dict = {"type": ",".join(types), "from": to_iso_z(start)}
    if end is not None:
        params["to"] = to_iso_z(end)
    params["limit"] = page_size
    params["offset"] = 0
    events: list[dict] = []
    total, pages, truncated = 0, 0, False
    while True:
        if pages >= max_pages:
            truncated = True
            break
        body = fetch_json(_events_url(base_url, params))
        batch = body.get("events")
        if not isinstance(batch, list):
            raise SourceUnavailable(f"Candystore /events answered without an events list ({base_url})")
        if pages == 0:
            try:
                total = int(body.get("total") or 0)
            except (TypeError, ValueError):
                total = 0
        pages += 1
        events.extend(e for e in batch if isinstance(e, dict))
        params["offset"] += len(batch)
        try:
            effective = int(body.get("limit") or page_size)
        except (TypeError, ValueError):
            effective = page_size
        if not batch or len(batch) < effective or params["offset"] >= total:
            break
    if end is not None:
        kept = []
        for e in events:
            at = event_time(e)
            if at is not None and at < end:
                kept.append(e)
        events = kept
    return events, total, truncated, pages


def fetch_events(types: list[str], start: datetime, end: datetime, base_url: str = CANDYSTORE_URL,
                 page_size: int = 1000, max_pages: int = 100) -> tuple[list[dict], int, bool]:
    events, total, truncated, _pages = _fetch_pages(types, start, end, base_url, page_size, max_pages)
    return events, total, truncated


# -- event accessors ------------------------------------------------------------

def canonical_type(t) -> str:
    """Fold `bloodbank.v1.x` onto `bloodbank.x` and the renamed tool types onto agent.tool.*."""
    if not isinstance(t, str):
        return ""
    t = _VERSIONED.sub("bloodbank.", t)
    for old, new in _RENAMED.items():
        if t.startswith(old):
            t = new + t[len(old):]
    return t


def event_kind(event: dict) -> str:
    """The last segment of the canonical type: completed, ended, created, updated, appended, recorded."""
    return canonical_type(event.get("type")).rsplit(".", 1)[-1]


def cwd_of(event: dict) -> str | None:
    """The working directory the event was produced in, whichever producer wrote it."""
    data = event.get("data")
    if not isinstance(data, dict):
        return None
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    for value in (data.get("working_directory"), payload.get("cwd"), data.get("cwd")):
        if isinstance(value, str) and value.strip():
            return value.strip()
    raw = payload.get("raw")
    if isinstance(raw, str) and '"cwd"' in raw and len(raw) <= RAW_PARSE_LIMIT:
        try:
            parsed = json.loads(raw)
        except ValueError:
            return None
        if isinstance(parsed, dict):
            value = parsed.get("cwd")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


_CONTAINERS = ("", "payload", "payload.tool_input", "arguments", "payload.arguments")


def _dig(obj, dotted: str):
    for part in dotted.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def field(event: dict, name: str):
    """Look `name` (dotted allowed) up in data, then data.payload, payload.tool_input, arguments."""
    data = event.get("data")
    if not isinstance(data, dict):
        return None
    for prefix in _CONTAINERS:
        container = _dig(data, prefix) if prefix else data
        if isinstance(container, dict):
            value = _dig(container, name)
            if value is not None:
                return value
    return None


def agent_key(raw) -> str:
    """Normalise a CLI name onto the event contract's agent key pattern."""
    if not isinstance(raw, str) or not raw.strip():
        return "unknown"
    key = _AGENT_KEY_BAD.sub("-", raw.strip().lower()).strip("-")
    if not key:
        return "unknown"
    if not key[0].isalpha():
        key = "cli-" + key
    return key[:32]


def cli_of(event: dict) -> str:
    actor = event.get("actor")
    raw = actor.get("cli") if isinstance(actor, dict) else None
    if not raw:
        raw = event.get("cli")
    if not raw:
        data = event.get("data")
        raw = data.get("cli") if isinstance(data, dict) else None
    if not raw:
        raw = _PRODUCER_CLI.get(str(event.get("producer") or ""))
    return agent_key(raw)


def session_of(event: dict) -> str | None:
    for value in (field(event, "invocation_id"), field(event, "session_id"), event.get("correlationid")):
        if isinstance(value, str) and value:
            return value
    return None


def outcome_class(event: dict) -> str:
    """success | failed | unknown. A missing outcome is unknown, never success."""
    outcome = field(event, "outcome")
    if isinstance(outcome, bool):
        return "success" if outcome else "failed"
    if isinstance(outcome, str):
        text = outcome.strip().lower()
        if text in SUCCESS_OUTCOMES:
            return "success"
        if text in FAILURE_OUTCOMES:
            return "failed"
    return "unknown"


def command_of(event: dict) -> str | None:
    value = field(event, "command")
    if isinstance(value, str) and value.strip():
        return " ".join(value.split())
    return None


def is_deploy_command(command) -> bool:
    """True when the invocation itself deploys: a deploy verb in command position on the first line
    (mise run x:deploy, bash scripts/relay-ecs-build-push.sh, wrangler deploy, gh workflow run deploy…).
    Reading, grepping or patching a file that mentions a deploy is not a deploy."""
    if not isinstance(command, str) or not command.strip():
        return False
    first = command.lstrip().split("\n", 1)[0]
    return bool(DEPLOY_RE.search(first))


def failure_detail(event: dict) -> str:
    for name in ("error", "error_message", "stderr"):
        value = field(event, name)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())[:DETAIL_CHARS]
    command = command_of(event)
    if command:
        return command[:DETAIL_CHARS]
    for name in ("description", "file_path", "pattern", "query", "url"):
        value = field(event, name)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())[:DETAIL_CHARS]
    tool_input = field(event, "tool_input")
    if isinstance(tool_input, dict):
        for value in tool_input.values():
            if isinstance(value, str) and value.strip():
                return " ".join(value.split())[:DETAIL_CHARS]
    outcome = field(event, "outcome")
    return f"outcome={outcome!s}"[:DETAIL_CHARS]


def _iso(event: dict) -> str | None:
    at = event_time(event)
    return to_iso_z(at) if at else None


def _sorted_counter(counter: Counter, top: int | None = None) -> dict:
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    if top is not None:
        items = items[:top]
    return {k: v for k, v in items}


# -- collectors -------------------------------------------------------------------

def collect_tools(scope, window, base_url: str = CANDYSTORE_URL) -> dict:
    """The digest "candystore" block minus sessions_ended (plus a caveats list digest.py hoists)."""
    events, total, truncated, pages = _fetch_pages(TOOL_TYPES, window.start, window.end, base_url)
    caveats: list[str] = []
    in_scope: list[dict] = []
    no_cwd = 0
    for event in events:
        cwd = cwd_of(event)
        if cwd is None:
            no_cwd += 1
            continue
        if scope.contains(cwd):
            in_scope.append(event)

    by_cli: Counter = Counter()
    by_tool: Counter = Counter()
    sessions: dict[str, str] = {}
    branches: set[str] = set()
    deploys: list[dict] = []
    failures: list[dict] = []
    failed = unknown = 0
    for event in in_scope:
        cli = cli_of(event)
        by_cli[cli] += 1
        tool = field(event, "tool_name")
        by_tool[str(tool) if tool else "unknown"] += 1
        sid = session_of(event)
        if sid:
            sessions.setdefault(sid, cli)
        branch = field(event, "git_branch")
        if isinstance(branch, str) and branch.strip():
            branches.add(branch.strip())
        klass = outcome_class(event)
        if klass == "failed":
            failed += 1
        elif klass == "unknown":
            unknown += 1
        command = command_of(event)
        raw_command = field(event, "command")     # the collapsed copy has no first line to judge by
        if is_deploy_command(raw_command if isinstance(raw_command, str) else command):
            deploys.append({"at": _iso(event), "cli": cli, "command": command[:DETAIL_CHARS]})
        if klass == "failed":
            failures.append({"at": _iso(event), "cli": cli, "tool": str(tool) if tool else "unknown",
                             "detail": failure_detail(event)})

    deploys.sort(key=lambda d: d["at"] or "", reverse=True)
    failures.sort(key=lambda f: f["at"] or "", reverse=True)
    if truncated:
        caveats.append(f"Candystore paging stopped after {pages} pages ({len(events)} of {total} tool events fetched); "
                       "tool counts are a floor")
    if no_cwd:
        caveats.append(f"{no_cwd} tool events in the window carried no working directory and were attributed to no project")
    if len(failures) > FAILURE_CAP:
        caveats.append(f"failures list capped at {FAILURE_CAP} of {len(failures)}")
    if len(deploys) > DEPLOY_CAP:
        caveats.append(f"deploy_commands list capped at {DEPLOY_CAP} of {len(deploys)}")
    branch_list = sorted(branches)
    if len(branch_list) > BRANCH_CAP:
        caveats.append(f"branches_touched capped at {BRANCH_CAP} of {len(branch_list)}")
        branch_list = branch_list[:BRANCH_CAP]

    return {
        "reachable": True,
        "base_url": base_url,
        "tool_calls_total": len(in_scope),
        "failed": failed,
        "unknown_outcome": unknown,
        "by_cli": _sorted_counter(by_cli),
        "by_tool": _sorted_counter(by_tool, BY_TOOL_TOP),
        "sessions": len(sessions),
        "sessions_by_cli": _sorted_counter(Counter(sessions.values())),
        "branches_touched": branch_list,
        "deploy_commands": deploys[:DEPLOY_CAP],
        "failures": failures[:FAILURE_CAP],
        "coverage": {"total": total, "fetched": len(events), "pages": pages, "truncated": truncated},
        "caveats": caveats,
    }


def _int(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return int(value)


def collect_sessions_ended(scope, window, base_url: str = CANDYSTORE_URL) -> dict:
    events, _total, _truncated, _pages = _fetch_pages(SESSION_TYPES, window.start, window.end, base_url)
    count = turns = duration = 0
    by_cli: Counter = Counter()
    for event in events:
        if not scope.contains(cwd_of(event)):
            continue
        count += 1
        by_cli[cli_of(event)] += 1
        turns += _int(field(event, "total_turns"))
        duration += _int(field(event, "duration_seconds"))
    return {"count": count, "turns": turns, "duration_seconds": duration, "by_cli": _sorted_counter(by_cli)}


def _belongs(event: dict, slug: str) -> bool:
    data = event.get("data")
    if not isinstance(data, dict):
        return False
    if data.get("slug"):
        return data.get("slug") == slug
    return data.get("repo") == slug or data.get("project") == slug


def _new_record(ticket_id: str | None, key: str | None) -> dict:
    return {
        "key": key, "ticket_id": ticket_id, "title": None, "phase": None, "state_group": None,
        "labels": [], "description": None, "kinds": [], "events": 0,
        "first_seen": None, "last_seen": None, "opened": False, "commented": False,
        "transitions": [], "last_transition": None, "closed": False, "started": False,
    }


def collect_tickets(slug: str, window, identifier: str | None = None, base_url: str = CANDYSTORE_URL) -> list[dict]:
    """Raw ticket records for `slug`, one per ticket, deduped to the last transition.

    A transition is a `created` event or an `updated` event whose
    `changed_fields` contains "state" (`data.previous_phase` is the old value
    of whatever changed: a state uuid on state changes, the old title on a
    rename). `closed` is decided by the LAST transition landing in
    Done/Cancelled; `started` by any transition into In Progress.
    """
    events, _total, _truncated, _pages = _fetch_pages(TASK_TYPES, window.start, window.end, base_url)
    mine = [e for e in events if _belongs(e, slug)]
    mine.sort(key=lambda e: event_time(e) or window.start)
    by_id: dict[str, dict] = {}
    by_key: dict[str, dict] = {}
    records: list[dict] = []
    for event in mine:
        data = event.get("data") or {}
        kind = event_kind(event)
        ticket = data.get("ticket") if isinstance(data.get("ticket"), dict) else {}
        comment = data.get("comment") if isinstance(data.get("comment"), dict) else {}
        ticket_id = data.get("ticket_id") or ticket.get("id") or comment.get("issue")
        ticket_id = ticket_id if isinstance(ticket_id, str) and ticket_id else None
        key = data.get("ticket_key") or data.get("key")
        if not key and identifier and ticket.get("sequence_id") is not None:
            key = f"{identifier}-{ticket['sequence_id']}"
        key = key if isinstance(key, str) and key else None
        rec = by_id.get(ticket_id) if ticket_id else None
        if rec is None and key:
            rec = by_key.get(key)
        if rec is None:
            rec = _new_record(ticket_id, key)
            records.append(rec)
        if ticket_id:
            rec["ticket_id"] = rec["ticket_id"] or ticket_id
            by_id[ticket_id] = rec
        if key:
            rec["key"] = rec["key"] or key
            by_key[key] = rec
        at = event_time(event)
        iso = to_iso_z(at) if at else None
        rec["first_seen"] = rec["first_seen"] or iso
        rec["last_seen"] = iso or rec["last_seen"]
        rec["events"] += 1
        if kind and kind not in rec["kinds"]:
            rec["kinds"].append(kind)
        title = data.get("title") or ticket.get("name")
        if isinstance(title, str) and title.strip():
            rec["title"] = title.strip()
        if isinstance(ticket.get("labels"), list):
            rec["labels"] = list(ticket["labels"])
        description = ticket.get("description_stripped")
        if isinstance(description, str) and description.strip():
            rec["description"] = description
        state = ticket.get("state")
        group = state.get("group") if isinstance(state, dict) else None
        phase = data.get("phase") or (state.get("name") if isinstance(state, dict) else None)
        phase = phase if isinstance(phase, str) and phase else None
        if phase:
            rec["phase"] = phase
        if isinstance(group, str) and group:
            rec["state_group"] = group
        if kind == "created":
            rec["opened"] = True
            rec["transitions"].append({"at": iso, "from_state_id": None, "to_phase": phase, "to_group": group})
        elif kind == "appended":
            rec["commented"] = True
        elif kind == "updated":
            changed = data.get("changed_fields")
            if isinstance(changed, list) and "state" in changed:
                previous = data.get("previous_phase")
                rec["transitions"].append({
                    "at": iso,
                    "from_state_id": previous if isinstance(previous, str) and previous else None,
                    "to_phase": phase, "to_group": group,
                })
    for rec in records:
        transitions = rec["transitions"]
        last = transitions[-1] if transitions else None
        rec["last_transition"] = last
        rec["closed"] = bool(last) and (last["to_group"] in CLOSED_GROUPS or last["to_phase"] in CLOSED_PHASES)
        rec["started"] = any(t["to_group"] == STARTED_GROUP or t["to_phase"] == STARTED_PHASE for t in transitions)
    records.sort(key=lambda r: r["last_seen"] or "", reverse=True)
    return records


def collect_decisions(slug: str, window, base_url: str = CANDYSTORE_URL) -> list[dict]:
    events, _total, _truncated, _pages = _fetch_pages(DECISION_TYPES, window.start, window.end, base_url)
    out: list[dict] = []
    for event in events:
        if not _belongs(event, slug):
            continue
        data = event.get("data") or {}
        title = data.get("title") or data.get("decision")
        if not isinstance(title, str) or not title.strip():
            continue
        note = data.get("note") or data.get("reasoning") or ""
        note = " ".join(str(note).split())
        issue = data.get("issue")
        if isinstance(issue, str) and issue.strip():
            note = f"{issue.strip()}: {note}" if note else issue.strip()
        out.append({"at": _iso(event), "title": " ".join(title.split())[:200], "note": note[:600]})
    out.sort(key=lambda d: d["at"] or "", reverse=True)
    return out[:DECISION_CAP]


def find_previous_report(slug: str, audience: str, now: datetime, base_url: str = CANDYSTORE_URL) -> dict | None:
    """The newest non-dry-run activity.recorded event for (slug, audience) within 45 days."""
    since = now - timedelta(days=PREVIOUS_LOOKBACK_DAYS)
    params: dict = {"type": ",".join(REPORT_TYPES), "from": to_iso_z(since), "limit": PREVIOUS_PAGE, "offset": 0}
    best: tuple | None = None
    for _page in range(PREVIOUS_MAX_PAGES):
        body = fetch_json(_events_url(base_url, params))
        batch = body.get("events")
        if not isinstance(batch, list):
            raise SourceUnavailable(f"Candystore /events answered without an events list ({base_url})")
        for event in batch:
            if not isinstance(event, dict):
                continue
            data = event.get("data") or {}
            project = data.get("project") if isinstance(data.get("project"), dict) else {}
            generator = data.get("generator") if isinstance(data.get("generator"), dict) else {}
            if project.get("slug") != slug or data.get("audience") != audience or generator.get("dry_run"):
                continue
            event_id = event.get("id") or event.get("event_id")
            window_end = (data.get("window") or {}).get("end") if isinstance(data.get("window"), dict) else None
            if not isinstance(event_id, str) or not isinstance(window_end, str):
                continue
            try:
                end_dt = parse_iso(window_end)
            except ValueError:
                continue
            candidate = (end_dt, event_time(event) or end_dt, event_id, event)
            if best is None or candidate[:2] > best[:2]:
                best = candidate
        try:
            total = int(body.get("total") or 0)
        except (TypeError, ValueError):
            total = 0
        params["offset"] += len(batch)
        if best is not None or not batch or params["offset"] >= total:
            break
    if best is None:
        return None
    end_dt, _seen, event_id, event = best
    report = (event.get("data") or {}).get("report")
    report = report if isinstance(report, dict) else {}
    return {"event_id": event_id, "window_end": to_iso_z(end_dt),
            "title": report.get("title") if isinstance(report.get("title"), str) else None,
            "raw": report.get("raw") if isinstance(report.get("raw"), str) else None}


def find_events_by_run_id(run_id: str, since: datetime, base_url: str = CANDYSTORE_URL) -> list[dict]:
    events, _total, _truncated, _pages = _fetch_pages(REPORT_TYPES, since, None, base_url, page_size=100, max_pages=5)
    matches = []
    for event in events:
        generator = ((event.get("data") or {}).get("generator") or {}) if isinstance(event.get("data"), dict) else {}
        if event.get("correlationid") == run_id or (isinstance(generator, dict) and generator.get("run_id") == run_id):
            matches.append(event)
    return matches
