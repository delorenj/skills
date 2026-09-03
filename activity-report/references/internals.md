# Internals: modules, file layout, and the digest contract

Developer reference for the skill's own code. Users read `SKILL.md`; this file
is for whoever changes `scripts/`.

## Layout

```
scripts/activity-report      entry point (python3); ~/.local/bin/activity-report symlinks here
scripts/run.sh               the unattended chain (lock, log, stages, per audience)
scripts/install-timer.sh     systemd user timer installer
scripts/ar/cli.py            argparse tree; dispatches to <module>.<name>_cmd(args) -> int
scripts/ar/common.py         exit codes, error classes, time helpers, runtime file layout
scripts/ar/config.py         .project.json resolution, defaults, scope set, init
scripts/ar/window.py         window resolution against the previous same-audience event
scripts/ar/candystore.py     HTTP client + derived counts (tools, sessions, tickets, decisions)
scripts/ar/gitscan.py        commits across all refs and linked worktrees
scripts/ar/board.py          Plane client: labels, states, issues, exposure, ensure-labels
scripts/ar/hindsight.py      list/recall (collect) and retain
scripts/ar/tokens.py         Claude + Codex transcript usage inside the window
scripts/ar/digest.py         orchestrates the collectors into <label>-<audience>.digest.json
scripts/ar/lint.py           the audience lint (external bans, denied titles, caps)
scripts/ar/render.py         raw.txt -> blocks -> markdown + self-contained html
scripts/ar/assemble.py       digest + bodies -> event data (the Bloodbank contract)
scripts/ar/contract.py       event-data validation and the absolute-path scan
scripts/ar/emit.py           bb-emit over stdin (--check, then --strict)
scripts/ar/verify.py         Candystore read-back by generator.run_id
scripts/ar/portal.py         portal row (automatic-ai adapter, D1 over the Cloudflare REST API)
scripts/ar/schedule.py       per-project timer drop-in, install/status
scripts/tests/               stdlib unittest; fixtures are captured live shapes
```

## Exit codes and errors (`ar/common.py`)

| code | constant | raised as |
|---|---|---|
| 0 | `EXIT_OK` | |
| 2 | `EXIT_CONFIG` | `ConfigError`, `SourceUnavailable`, `ContractError` |
| 3 | `EXIT_ACCEPTANCE` | `AcceptanceError` (lint error, event not projected, files missing) |
| 4 | `EXIT_NOTHING` | `NothingToDo` (window shorter than `window.min_minutes`; `--force` overrides) |
| 5 | `EXIT_LOCKED` | `Locked` |

`cli.main` catches `SkillError` and returns its `exit_code`; modules raise, they
do not `sys.exit`.

## Files of one run

`runtime_paths(project, label, audience)` in `common.py` is the single source of
these names. `label` = window end in the project timezone as `YYYY-MM-DDTHHMM`.

```
<repo_path>/<output.runtime_dir>/<slug>/        (gitignored)
  <label>-<audience>.digest.json   collect
  <label>-<audience>.raw.txt       compose (the ONLY file the agent writes; line 1 = `# <title>`)
  <label>-<audience>.md            render
  <label>-<audience>.html          render
  <label>-<audience>.event.json    assemble (the event `data` object)
  <label>-<audience>.compose.json  run.sh (claude --output-format json stdout)
  <label>-<audience>.emit.json     emit (bb-emit stdout, --check and publish)
  <label>-external.lint.json       collect, external only (see below)
  .lock                            run.sh flock, one per project
<repo_path>/<output.durable_html_dir>/<label>-<audience>.html   run.sh copy (tracked on purpose)
${XDG_STATE_HOME:-~/.local/state}/activity-report/<slug>/<label>-<audience>.log
~/.cache/activity-report/plane/<workspace>/<board_id>/{labels,states}.json  (24 h)
```

## Module interface

Signatures the other modules rely on. `project` is `ar.config.Project`;
`window` is `ar.window.Window`; `scope` is `ar.config.ScopeSet`.

```python
# config.py
DEFAULTS: dict                                   # the full activity_report block with defaults
load_project(slug: str | None = None, cwd: str | None = None) -> Project
    # Project: slug, name, identifier|None, workspace|None, board_id|None, provider_type|None,
    #          repo_path, extra_repo_paths: list[str], config: dict (DEFAULTS deep-merged with the block),
    #          tz: str, project_json_path: str, ticket_provider: dict
scope_set(project) -> ScopeSet                   # .roots, .worktrees (abs paths), .contains(path), .as_dict()
resolve_cmd(args) -> int ; init_cmd(args) -> int

# window.py
@dataclass Window: start: datetime(UTC), end: datetime(UTC), basis: str, previous_event_id: str|None,
                   previous: dict|None, caveats: list[str]
    .duration_seconds -> int ; .label(tz) -> str ; .as_dict() -> the digest "window" block
resolve(project, audience, now=None, since=None, until=None, force=False) -> Window   # raises NothingToDo
window_cmd(args) -> int

# candystore.py
fetch_events(types: list[str], start, end, base_url=CANDYSTORE_URL, page_size=1000, max_pages=100)
    -> tuple[list[dict], int, bool]              # (events with time < end, total reported, truncated)
canonical_type(t: str) -> str ; cwd_of(event) -> str|None ; field(event, name) -> object
collect_tools(scope, window) -> dict             # the digest "candystore" block minus sessions_ended
collect_sessions_ended(scope, window) -> dict    # the "sessions_ended" sub-block
collect_tickets(slug, window) -> list[dict]      # raw ticket events, deduped to last transition per key
collect_decisions(slug, window) -> list[dict]
find_previous_report(slug, audience, now, base_url=CANDYSTORE_URL) -> dict|None
    # newest non-dry-run event for (slug, audience) within 45 days: {event_id, window_end, title, raw}
find_events_by_run_id(run_id, since, base_url=CANDYSTORE_URL) -> list[dict]

# gitscan.py
scan(project, scope, window) -> dict             # the digest "git" block

# board.py
enrich(project, ticket_events, window, audience) -> tuple[dict, dict|None]
    # (the digest "board" block, the lint.json dict for external or None)
ensure_labels(project, confirm: bool) -> dict ; ensure_labels_cmd(args) -> int

# hindsight.py
collect(project, window) -> dict                 # the digest "hindsight" block; never raises
retain_text(project, audience, raw_text, window_end) -> str ; doc_id_for(project, audience, label, run_id, attempt=1) -> str ; retain(project, audience, raw_text, window_end, label, run_id=None, attempt=1) -> bool ; retain_cmd(args) -> int

# tokens.py
collect(scope, window) -> dict                   # the digest "tokens" block

# digest.py
collect(project, audience, window, run_id, out_path=None) -> dict ; collect_cmd(args) -> int
validate_digest(d: dict) -> None                 # raises ContractError

# lint.py
@dataclass Finding: level ("error"|"warning"), rule, excerpt, line: int|None
lint(raw_text, audience, project_identifier: str|None, config_lint: dict, digest=None, lint_json=None) -> list[Finding]
lint_cmd(args) -> int

# render.py
split_raw(raw_text) -> tuple[str, str]           # (title, body) ; raises AcceptanceError without `# title`
parse(body) -> list[Block] ; to_markdown(title, blocks) -> str ; to_html(title, blocks, meta: dict) -> str
    # meta: project_name, audience, window_start, window_end (ISO), tz, run_id, generated_at, duration_seconds
render_cmd(args) -> int

# assemble.py
assemble(digest, raw_text, markdown, html, model: str|None, dry_run: bool) -> dict ; assemble_cmd(args) -> int

# contract.py
validate_event(data: dict) -> None ; assert_no_paths(obj) -> None   # raise ContractError

# emit.py
emit(event_data: dict, dry_run: bool) -> dict ; emit_cmd(args) -> int
verify.py: verify(run_id, timeout_seconds=90) -> dict ; verify_cmd(args) -> int
portal.py: publish(event_data, project, dry_run) -> dict ; portal_cmd(args) -> int
schedule.py: render_dropin(project) -> str ; install_timer_cmd(args) -> int ; timer_status_cmd(args) -> int
```

## The digest (`<label>-<audience>.digest.json`)

Everything the compose agent is allowed to know. Absolute paths appear ONLY in
`scope` (the event never copies it). Timestamps are RFC 3339 UTC with `Z`.

```jsonc
{
  "schema_version": 1,
  "run_id": "uuid4",                       // == envelope correlationid; both audiences share it
  "generated_at": "2026-09-03T07:00:12Z",
  "audience": "internal",                  // or "external"
  "label": "2026-09-03T0300",              // window.end in project tz
  "project": { "slug": "james-brennan", "name": "James Brennan", "identifier": "JIMB",
               "workspace": "automaticai", "board_id": "uuid|null",
               "repos": ["james-brennan", "client-portal"],      // basenames of every root, ≤8
               "timezone": "America/New_York" },
  "window": { "start": "…Z", "end": "…Z", "duration_seconds": 86400,
              "basis": "previous_report|cap_24h|explicit", "previous_event_id": "uuid|null" },
  "previous_report": { "event_id": "uuid", "window_end": "…Z", "title": "…", "raw_excerpt": "first 600 chars" } | null,
  "scope": { "roots": ["/abs/path"], "worktrees": ["/abs/path"] },
  "candystore": {
    "reachable": true, "base_url": "http://127.0.0.1:8683",
    "tool_calls_total": 0, "failed": 0, "unknown_outcome": 0,
    "by_cli": { "claude": 0 }, "by_tool": { "Bash": 0 },            // by_tool = top 12
    "sessions": 0, "sessions_by_cli": { "claude": 0 },              // sessions = distinct invocation_id
    "branches_touched": ["main"],
    "deploy_commands": [ { "at": "…Z", "cli": "claude", "command": "first 160 chars" } ],
    "failures": [ { "at": "…Z", "cli": "claude", "tool": "Bash", "detail": "first 160 chars" } ],   // cap 40
    "sessions_ended": { "count": 0, "turns": 0, "duration_seconds": 0, "by_cli": {} },
    "coverage": { "total": 0, "fetched": 0, "pages": 0, "truncated": false }
  },
  "git": {
    "commit_count": 0,
    "repos": [ {
      "name": "james-brennan", "state": "ok|missing|failed", "default_branch": "main",
      "commit_count": 0, "on_default": 0, "off_default": 0, "replays": 0, "truncated": false,
      "commits": [ { "sha": "40-hex", "short": "7-hex", "at": "…Z", "author": "…", "subject": "…", "on_default": true } ],  // newest first, ≤100
      "branches": ["main"],                                          // branches carrying window commits, ≤64
      "worktrees": [ { "path": "/abs", "branch": "jimb-169|null", "head": "short", "uncommitted_files": 0 } ],
      "uncommitted_files": 0, "files_changed": 0, "insertions": 0, "deletions": 0
    } ]
  },
  "board": {
    "provider": "plane", "status": "ok|unavailable|unsupported", "labels_resolved": true,
    "exposure_labels": { "external": "xp:external", "internal": "xp:internal" },
    "tickets": [ { "key": "JIMB-214", "title": "…", "from_state": "In Progress|null", "to_state": "Done|null",
                   "event_kinds": ["updated"], "labels": ["xp:external"], "exposure": "external|internal|unlabeled",
                   "surface": "always|judgment|null",               // external digest only; null for internal
                   "description_excerpt": "first 600 chars|null", "url": "https://…|null",
                   "first_seen": "…Z", "last_seen": "…Z" } ],
    "opened": ["JIMB-1"], "closed": [], "started": [], "commented": [],
    "decisions": [ { "at": "…Z", "title": "…", "note": "…" } ]
  },
  "hindsight": { "bank": "james-brennan", "status": "ok|unavailable|disabled",
                 "items": [ { "at": "…Z", "fact_type": "…", "text": "…" } ],           // cap 40
                 "recall": { "query": "…", "items": ["…"] } },                          // cap 20
  "tokens": { "total": 0,
              "by_agent": { "claude": { "input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "total": 0 } | null,
                            "codex": { … } | null, "kimi": null },
              "detail": { } },                                        // free-form colour, never copied to the event
  "caveats": ["…"]
}
```

External digests differ in exactly two ways: tickets with exposure `internal`
are removed from `board.tickets` and from `opened`/`closed`/`started`/`commented`
(their titles go to the lint file instead), and every remaining ticket carries
`surface` (`always` for exposure `external`, `judgment` for `unlabeled`).

## `<label>-external.lint.json`

Written by `collect --audience external`; read by `lint`. The compose agent
never sees it.

```json
{ "identifiers": ["JIMB"],
  "denied_titles": ["Fix the retry loop in the closeout path"],
  "surface_always": [ { "key": "JIMB-214", "title": "Draft invoice reaches GorillaDesk" } ] }
```

## Event data (assemble)

The event `data` object is fixed by the Bloodbank schema
`schemas/bloodbank/project/activity.recorded.json`; `assemble.py` maps:

| event field | from |
|---|---|
| `schema_version` | `1` |
| `project` | digest.project minus `timezone` |
| `audience`, `window` | digest |
| `report.title` | raw.txt line 1 without `# ` (≤180) |
| `report.raw` | raw.txt body only (≤5000, portal grammar) |
| `report.markdown`, `report.html` | render output (≤20000 / ≤262144; html starts `<!doctype html>`) |
| `tokens` | digest.tokens pruned to `by_agent.{claude,codex,kimi}`; `total` recomputed as the sum of non-null bucket totals |
| `generator` | `{skill: "activity-report", skill_version: ar.__version__, run_id: digest.run_id, model, dry_run}` |
| `sources` (internal only) | `git: {<repo.name>: {commits: [{sha, subject≤120, author≤80, at}]≤100, truncated, branches≤64, files_changed, insertions, deletions}}` for repos with state ok; `candystore: {sessions, tool_calls: tool_calls_total, by_cli}`; `board: {closed, opened, started}`; `hindsight: {bank, facts: len(items)}` |
| `tickets` (internal only) | `[{key, title≤200, from_state, to_state, labels≤8, exposure}]` ≤200 |

External events carry neither `sources` nor `tickets`. `contract.assert_no_paths`
refuses any string matching `(^|[^A-Za-z0-9_.])/(home|Users|root|tmp|var|etc|opt|srv|mnt)/`
anywhere in the data, and `validate_event` checks every cap above before emit.
