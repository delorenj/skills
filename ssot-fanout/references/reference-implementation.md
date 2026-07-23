# Reference implementation: bloodbank `services/agent-hooks`

The canonical instance of the pattern. Read this to operate or extend it; read it as a worked example
before building the pattern elsewhere.

Repo: `~/code/33GOD/bloodbank`. All paths below are under `services/agent-hooks/` unless noted.

## What it does

Several agent CLIs (Claude Code, GitHub Copilot CLI, Codex CLI, OpenClaw) each have their own hook-config
format and their own native hook names, but they all publish the **same** v1 CloudEvents lifecycle to the
Bloodbank NATS bus. The mapping from "this CLI's hook X" → "this canonical event type" lives in exactly one
place and fans out to each CLI's native config + each publisher's runtime map.

## The artifacts

| File | Role |
|---|---|
| `hooks.master.json` | **SSOT.** `lifecycle` catalog (canonical key → v1 `type`, `kind`, `ordering_bucket`, `role`) + `agents.<cli>` with `dialect`, `runner`, `config_target`, `event_map_target`, `actor`, and `bindings` (native hook → role + lifecycle + matcher/payload/extra_args). |
| `hooks.mappings.lock.json` | **Resolution memory.** `resolutions` keyed `role:<role>` / `type:<type>` → `{resolution, strategy, diverged, rationale, decided_at, decided_by}`. |
| `sync.py` | **Engine.** `--check` (gate), `--apply` (write), `--resolve` (interactive). |
| `core/event_map.py` | `resolve_map(agent_dir, _DEFAULT_MAP)` — generated map merged OVER an embedded fallback. |

Generated per agent (NEVER hand-edit): `claude/settings.hooks.json` (merge fragment), `copilot/hooks.json`,
`codex/hooks.json`, and `<agent>/event_map.generated.json`.

## Dialects in play

- **`claude_settings`** — nested `{matcher?, hooks:[{type:command, command, timeout}]}`; emitted as a
  fragment to merge into `~/.claude/settings.json` (which holds many non-bloodbank hooks too). `runner`
  uses `$HOOKS`; `payload:"empty"` → no pipe, `payload:"stdin"` → `cat | `.
- **`copilot`** — flat `{type:command, bash:"exec <runner> <arg>", timeoutSec}`; wrapper `{version:1,hooks:{}}`.
- **`codex`** — same nested shape as claude but key `timeout` in ms; `payload:"empty"` → `echo '{}' | `;
  `extra_args` (e.g. `Stop … user_stop`).
- **`hermes_config`** — hermes-agent shell hooks: a `hooks:` block (event → `[{command, timeout, matcher?}]`) YAML-merged into the agent's `config.yaml`, plus pre-approved entries seeded into `shell-hooks-allowlist.json` (commands run `shell=False`, payload on stdin). **Fleet fan-out**: instead of a single `live_target`, the install reads a **registry** (`~/.hermes/agents-registry.yaml`) and deploys into *every* agent's `<role_dir>/runtime/` (skip uninitialized, create missing config.yaml). This is the "one master → N dynamically-discovered targets" shape — the target set is data, not hardcoded.
- **`watcher`** (openclaw) — no config generated; bindings document intended coverage only. `runtime` is similarly inert.

`runner` may contain `{service_dir}`, which sync resolves to the absolute path of `services/agent-hooks`.

## Resolved decisions (in the lock, 2026-06-07)

| Lock key | Resolution | Why |
|---|---|---|
| `role:session_start` / `role:session_end` | `bloodbank.v1.agent.session.started` / `.ended` | Session events live under the `agent` domain — a legal 5-token type using allowlisted tokens. Superseded `cli.session.*`; bucket `cli_session`→`session`. New schemas at `schemas/bloodbank/v1/agent/session.{started,ended}.v1.json`. |
| `role:post_tool` | `bloodbank.v1.agent.tool.completed` | The single post-tool hook fires after execution and carries `outcome`; Claude moved off `agent.tool.invoked`. |
| `role:subagent_stop` | `bloodbank.v1.agent.invocation.completed` | Sub-agent runs are nested invocations; `agent.delegation.completed` was contract-illegal (no `delegation` entity). |

## mise tasks

- `mise run hooks:check` → `sync.py --check` (CI/drift gate; nonzero on stale artifacts or unresolved ambiguity).
- `mise run hooks:sync` → `sync.py --apply` (regenerate repo artifacts; idempotent).
- `mise run deploy` → `sync.py --apply --install` (regenerate + install into live `~/.claude/settings.json` merge, `~/.copilot` symlink, `~/.codex/hooks.json` merge; surgical, preserves foreign hooks, idempotent). `hermes`/`openclaw` are inert (`runtime`/`watcher`).
- `mise run smoketest:agent-hooks-ssot` → `sync --check` green **and** every binding builds a
  contract+schema-valid envelope (reuses each publisher's real actor identity). Folded into `mise run smoketest:schemas`.

## Procedure: add a new agent CLI

1. Add an `agents.<cli>` block to `hooks.master.json`: pick a `dialect`, set `runner`
   (use `{service_dir}` for an absolute publisher path), `actor`, `config_target`/`event_map_target`, and
   `bindings` mapping each native hook name → a `role` + canonical `lifecycle` key.
2. `mise run hooks:check`. Roles already decided in the lock (e.g. `post_tool`) resolve automatically;
   any *new* ambiguity is surfaced — `python3 sync.py --apply --resolve` to record the decision.
3. `mise run hooks:sync` to generate `<cli>/hooks.json` (or settings fragment) + `<cli>/event_map.generated.json`.
4. Write `<cli>/publish.py`: import `core.envelope.build_envelope`, `core.nats_publish.publish`,
   `core.session.SessionState`, `core.event_map.resolve_map`; source the map via
   `resolve_map(Path(__file__).parent, _DEFAULT_MAP)`; declare the same `actor` as the master entry.
5. Document the hook table in `services/agent-hooks/README.md`. `smoketest:agent-hooks-ssot` validates it.

## Why this exists (the bugs it kills)

Before the SSOT: a publisher's `EVENT_MAP` had been hand-edited to contract-illegal types while its
handlers still hardcoded the old ones (drift), and the live `~/.claude/settings.json` `Stop` hook called
an arg the map didn't know — so Claude silently published **no** session-end event. Both are the class of
failure a single source of truth plus a `check` gate makes structurally impossible.
