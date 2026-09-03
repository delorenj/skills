# Data sources

What each collector reads, the rules it applies, and the traps that produced wrong
numbers before. The contract for the output is `assets/schemas/digest.schema.json`;
the module map is `internals.md`. Everything here is stdlib Python 3.11 with no
credentials on disk.

## Window

`ar/window.py resolve(project, audience, ...)`

- `end` is now (or `--until`). `start` is the previous report's window end for the
  same project *and audience*, found in Candystore (`bloodbank.project.activity.recorded`,
  newest by `data.window.end`, dry runs ignored), clamped to `now - cap`:
  `start = max(previous_end, now - cap_hours)`.
- `basis`: `previous_report` when the previous end was used (its event id goes into
  `previous_event_id`); `cap_24h` when there was no usable previous report and the cap is
  24 h (the contract requires exactly 86400 s); `explicit` for `--since`/`--until`, or a
  configured `cap_hours` that is not 24.
- A previous end in the future (clock skew, a report emitted with a later `--until`)
  is clamped to `now - 1 s` with a caveat.
- Shorter than `window.min_minutes` is exit 4 (`NothingToDo`) unless `--force`.
- `previous_report` in the digest is filled whenever a previous report exists, even
  when the window did not chain from it, so the compose agent can avoid repeating it.
- The label is the window end in the project timezone: `2026-09-03T0300`.

## Candystore (required; unreachable is exit 2)

`ar/candystore.py`, `GET $CANDYSTORE_URL/events` (default `http://127.0.0.1:8683`),
params `type` (comma list), `from`, `to`, `limit` (max 1000), `offset`. The answer is
`{events, total, limit, offset}`, newest first.

The five rules, each paid for by a wrong daily count:

1. **Never pass `project=`.** The store's project column is the basename of the cwd
   the producer reported, which is `unknown` for a third of Hermes events and the
   worktree name for anything done in a worktree. Scope is decided client-side from the
   cwd (rule 3).
2. **Read both namespaces.** Every type exists as `bloodbank.<x>` and
   `bloodbank.v1.<x>`, and Copilot/Kimi emit `tool.tool_call.completed` instead of
   `agent.tool.completed`. `canonical_type` folds all of them; the `TOOL_TYPES` list
   requests every spelling in one call.
3. **The working directory is in one of four places.** `data.working_directory`
   (Claude, Codex), `data.payload.cwd` (Hermes, Copilot), `data.cwd`, and for some
   Hermes hooks only inside the JSON string at `data.payload.raw`. `cwd_of` walks that
   chain. An event is in scope when the cwd sits under a scope root or a worktree
   (`config.ScopeSet.contains`, boundary match: `james-brennan-other` never matches
   `james-brennan`). Events with no cwd at all are attributed to no project and counted
   in a caveat.
4. **Sessions are distinct `invocation_id`** (fallback `session_id`, then
   `correlationid`), never event volume. A session that made 900 tool calls is one
   session.
5. **A missing outcome is `unknown`, not success.** `outcome`/`status`/`success` are
   read in that order; `error`, `failed`, `failure`, `timeout`, `denied`, `blocked`
   and `success: false` are failures.

Also:

- `to` is inclusive in the store, so events with `time >= end` are dropped client-side
  and the window is half-open `[start, end)`.
- Paging stops when a page is shorter than the echoed `limit` or the offset reaches
  `total`; `coverage` in the digest says how much was read and whether the page cap
  truncated it.
- `cli_of`: `actor.cli`, then the top-level `cli`, then `data.cli`, then a producer map
  (`hermes-agent` is `hermes`). Keys are normalised to `^[a-z][a-z0-9_-]{0,31}$`.
- Deploys are commands matching `\bdeploy\b`, `ecs-build-push` or `wrangler deploy`
  (word-boundary, not substring: `test_deploy_gate.py` and heredoc bodies produced
  100+ false deploys a day).
- `failures` and `deploy_commands` are capped at 40 with a caveat; `by_tool` keeps the
  top 12.
- `sessions_ended` sums `agent.session.ended` events in scope: `count`, `turns`,
  `duration_seconds`, `by_cli`. Turn and duration fields differ by producer and are
  read from `data`, `data.payload` and `data.metrics`.

### Tickets from events

`repo.task.{created,updated,appended,closed}` for the project slug (`data.slug`, else
`data.repo`/`data.project`). Records merge by `ticket_id` (an `appended` event carries
`comment.issue`).

- A **real state transition** is a `created` event, or an `updated` event whose
  `changed_fields` contains `state`. `previous_phase` is the old value of *whatever
  changed* (a uuid on a state change, the old title on a rename), so a title edit is
  never a transition.
- `closed` = the **last** transition in the window lands in a `completed`/`cancelled`
  group (Done, Cancelled). `started` = any transition into the `started` group
  (In Progress). `opened` = a `created` event. `commented` = an `appended` event.
- `from_state` is the state before the first in-window transition (a uuid, resolved
  to a name via the Plane states list); `to_state` is the phase after the last one.
- Keys come from `ticket_key`, else `<identifier>-<sequence_id>`; a comment-only ticket
  with no key needs the live board read to be listed, otherwise it is dropped with a
  caveat.
- Decisions: `repo.decision.recorded`, title from `title`/`decision`, note from
  `"<issue>: " + reasoning`, capped at 50.

## Git

`ar/gitscan.py`, per scope root:

- `git log --no-merges --since --until --exclude=refs/stash --exclude=refs/notes/* --all`
  plus `git log HEAD` in every linked worktree (`--all` already walks other worktrees'
  HEADs; the explicit pass covers a worktree git does not list). Commits are keyed by
  sha and filtered client-side to `[start, end)` on the committer date. `--until` is
  inclusive at second resolution, so the range passed to git ends one second early.
- **Never `str.splitlines()` on git output**: it splits on `\x1e`, the record
  separator the numstat pass uses, and silently produced zero insertions.
- Replays (a rebase or cherry-pick copy) share the author date and subject; one copy is
  kept (the default-branch one, else the newest) and the rest are counted in `replays`.
- `on_default` = reachable from `refs/heads/<default>` or `refs/remotes/origin/<default>`
  within the window; the default is `origin/HEAD`, else `main`, else `master`.
- Branches come from `for-each-ref --sort=-committerdate` (refs/heads and refs/remotes),
  probed with `rev-list --count` until the tips fall before the window; the default
  branch is listed first, then by commit count; capped at 64.
- Stats are from `--numstat`, uncommitted files from `status --porcelain -z`
  (renames consume two entries).
- A root that is not a checkout is `state: missing` with a caveat, never fatal.

## Board (Plane)

`ar/board.py`, `https://plane.delo.sh/api/v1/workspaces/<ws>/projects/<board>/…` with
`X-API-Key` and a mandatory `User-Agent` (Cloudflare answers 403 to urllib's default).
Lists page with `per_page=100` and `next_cursor`.

- **Key chain**, read at call time and never written anywhere:
  `board.api_key_ref` (`op://…` via `op read`, or `env:NAME`) → `$PLANE_API_KEY` →
  `$PLANE_<WORKSPACE>_API_KEY` → a builtin per-workspace `op://` reference
  (`automaticai`, `33god`). A literal key in config is refused.
- Labels and states are cached for 24 h at
  `$XDG_CACHE_HOME/activity-report/plane/<workspace>/<board>/{labels,states}.json`
  (names and ids only). A stale cache stands in when the list fails, with a caveat.
- **Exposure is read from the ticket's CURRENT labels**: a live `GET issues/<id>/`
  per ticket, newest first, up to `board.max_live_fetches`, because the label a PM adds
  after the fact is the decision. Past the budget the event snapshot's labels are used
  (dicts `{id, name, color}` or uuids) and a caveat says so.
- `xp:internal` beats `xp:external`; neither is `unlabeled`. In an external digest an
  internal ticket is removed and its title goes to `<label>-external.lint.json`
  (`denied_titles`), an external one is `surface: always` (and listed in
  `surface_always`), an unlabeled one is `surface: judgment` with no excerpt.
- Board unavailable or no key: the external digest withholds every ticket; the
  internal digest lists them as `unlabeled`. Both say so in a caveat.
- Plane's issue GET has no `description_stripped`; excerpts strip `description_html`
  (600 chars).
- `ensure-labels` creates only the missing label(s), only with `--confirm`, and refreshes
  the cache. On JIMB, `xp:external` already exists; `xp:internal` does not.

## Hindsight is colour

`ar/hindsight.py`, the `hindsight` CLI against `config.hindsight_bank(project)`.

- `memory list <bank> -o json -l 200 -s <offset>` is newest-first with no date filter;
  items are filtered client-side on `date` to the window, `invalidated_at` items are
  dropped, and anything with `context` starting `activity-report:` (the skill's own
  retained reports) is excluded so a report never quotes its predecessor as a fact.
  Paging stops as soon as a page is entirely older than the window.
- `memory recall <bank> "<query>" -o json --budget high --max-tokens 2048` gives up to
  20 asides.
- **Nothing from Hindsight is a count or a claim.** The compose agent may quote it as
  memory; every fact in the report must trace to Candystore, git or the board. Any
  failure is `status: unavailable` with a caveat; the run never stops for it.
- `retain` stores the finished report with `--context activity-report:<audience>`,
  `--doc-id activity-report:<slug>:<audience>:<label>` and `--timestamp <window end>`;
  it warns and returns false on failure.

## Tokens

`ar/tokens.py`, transcripts on this machine only.

- **Claude**: `~/.claude/projects/**/*.jsonl`, subagents under `<session>/subagents/`.
  Files with mtime older than `start - 1 h` are skipped; the first line carrying `cwd`
  decides scope. Each `assistant` line with `message.usage` is a sample, **deduplicated
  by `message.id`** (a message is written several times while it streams; the last copy
  wins, and counting every copy quadruples the number). `input = input_tokens`,
  `cache_read = cache_read_input_tokens`, `cache_write = cache_creation_input_tokens`.
- **Codex**: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (day directories from the
  day before the window start to the end day, local time), scope from
  `session_meta.payload.cwd`. `token_count` events carry a **cumulative**
  `total_token_usage`, so a session's usage in the window is the last total before the
  end minus the last total before the start. `input_tokens` includes the cached part:
  `input = input_tokens - cached_input_tokens`, `cache_read = cached_input_tokens`,
  `cache_write = cache_write_input_tokens` (always 0 so far), `output = output_tokens`
  (reasoning is inside it and reported separately in `detail`).
- **Kimi** has no transcript source and is always null.
- An agent with no in-scope transcript is `null`, not zero; a transcript in scope with
  no usage in the window is zero.

## Path scrubbing

Every string in the digest except `scope` and `git.repos[].worktrees[].path` has
`/home/<user>/x`, `/Users/<user>/x` and `/root/x` rewritten to `~/x` and `/tmp/x`,
`/var/x`, `/etc/x`, `/opt/x`, `/srv/x`, `/mnt/x` to `tmp/x` etc. The validator then
refuses any remaining absolute path, so a machine-specific path can never reach the
event or the client.

## Follow-ups

- **Publish usage in `agent.session.ended`** (tokens per agent per session, with the
  cwd) so the transcript scraper can retire; it is the only collector that reads
  files a producer already knows better.
- Candystore could carry a `working_directory` for every producer; until then the
  `payload.raw` fallback stays.
