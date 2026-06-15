# Project-scoped variant: per-dev agent hooks in a repo (internals)

The deep dialect mechanics behind [project-scoped-hooks.md](project-scoped-hooks.md) (the
adoption guide). This is a **lean** (no lock file) instance of the SSOT config fan-out engine;
that generic engine and its full **bloodbank `services/agent-hooks` reference** live in the
**`pjangler-dev`** skill (`references/ssot-fanout-engine.md`, `references/ssot-fanout-reference.md`).

The problem this variant solves differs from the bloodbank reference: install the *same* agent
hooks for **every dev who clones a repo**, fanned out to each agent CLI's native config, with a
**per-dev opt-out** — and driven by `mise enter/leave` instead of an explicit deploy.

Live implementation: `~/code/CoachingAgentFramework/.agents/hooks/`
(`hooks.master.json` + `sync.py`). Mirror it when adding this shape to another repo.

## When to use this variant vs the bloodbank one

| | bloodbank `services/agent-hooks` | this project-scoped variant |
|---|---|---|
| Goal | one canonical event bus, many publishers | one hook set, every dev's CLIs |
| Lock file / ambiguity engine | yes (`hooks.mappings.lock.json`) | **no** — too few hooks to need it |
| Install driver | `mise run deploy` (explicit) | `mise enter` → install, `mise leave` → uninstall |
| Catalog unit | canonical CloudEvents `type` + `role` | a `lifecycle` (user_prompt / post_tool / session_end) |
| Scope | machine-global (`~/.claude`, `~/.codex`) | committed-per-repo + per-dev injected |

Reach for lean when the master has a handful of entries and you don't need
divergence memory. Keep `--check` (drift gate) and idempotent generation — those
are non-negotiable in either variant.

## The three dialects it adds

- **`claude_settings` (committed, zero-bootstrap).** Generate the `hooks` key of
  the repo's committed `.claude/settings.json`, using `$CLAUDE_PROJECT_DIR/...`
  paths (Claude expands them at runtime). Committing it *is* the install — no
  per-dev step. `sync` owns the whole `hooks` key. `--check` compares the committed
  file to a fresh render → CI drift gate.

- **`codex_hooks` (per-user injection, enter/leave).** Codex has no project-scoped
  hook file; hooks live only in the per-user `~/.codex/hooks.json` (shared with
  other projects). So inject **absolute-path** entries on enter and strip them on
  leave. Reversibility without a lock: **mark ours by the command path** — every
  injected command contains `<repo>/.agents/hooks/`, so uninstall = drop any hook
  whose command contains that marker, drop emptied groups, leave foreign entries
  byte-untouched. Back up once to `*.caf-bak`. Append at the end so existing entry
  indices (and Codex's per-hook approval state) don't shift.

- **`hermes_config` (adapter + allowlist, per-deployment).** Hermes runs hooks
  `shell=False` (argv, no shell operators), pipes the payload as JSON on stdin
  (`{hook_event_name, tool_name, tool_input, session_id, cwd, extra}`), has **no
  user-prompt event**, and requires commands in `shell-hooks-allowlist.json`.
  Two consequences:
  1. **Write an adapter, don't reuse the Claude scripts.** A single
     `hermes/hindsight-hook.sh <event>` dispatcher translates the Hermes payload
     and (critically) **pins the bank** — `resolve_bank` from the Hermes runtime
     cwd resolves to the PM *submodule*, not the repo.
  2. **Merge into the live runtime** with pyyaml (config.yaml `hooks:` block) +
     JSON (allowlist), idempotently: only write when an entry is actually missing
     (so steady-state is zero bytes and you don't reformat a running agent's
     config every enter), back up first, and add allowlist approvals preserving
     existing timestamps.

## The two mechanisms this variant introduces

These are the reusable ideas — lift them when a fan-out target is *shared/committed*
yet must be *individually overridable*.

### 1. Per-dev opt-out without git churn — a runtime guard

A committed Claude `hooks` block is identical for everyone, so you can't subtract a
hook per-dev by editing it (that dirties git, and Claude has no "disable"
semantic). Solution: **the committed command is a guard wrapper.**

```
$CLAUDE_PROJECT_DIR/.agents/hooks/lib/hook-guard.sh <hook-id> <real-hook-script>
```

`hook-guard.sh` execs the real script (stdin passes straight through) **unless**
the dev's gitignored `.agents/local.json` lists that hook id, in which case it
exits 0 *silently* (exit 1 would surface as a hook error in the agent — don't).
Same `local.json` also drives **install-time** agent skip (codex/hermes) and the
skill-linker's skill skip. One gitignored file, three readers (the engine, the
hooks, the linkers), all fail **open** if it or `jq` is missing.

shell=False targets (Hermes) can't use the `&&`/wrapper form — put the same
`hook_disabled <id>` check *inside* the adapter instead (shared via
`lib/local-config.sh`).

### 2. mise enter/leave as the install/uninstall driver

`mise.toml [hooks] enter = [... "sync.py --install --quiet"]`,
`leave = [... "sync.py --uninstall --quiet"]`, plus a `watch_files` on
`hooks.master.json` → `hooks-sync`. Install/uninstall must **never hard-fail the
shell** (exit 0 on internal error, warn to stderr); only `--check` returns nonzero.
Caveat to document: `leave` fires per-shell, so multi-shell users can race the
codex uninstall — acceptable for a solo/small team; the absolute-path marker keeps
re-install trivially idempotent.

### 3. Sibling layer — skill fan-out with global-deference

The same repo also fans **skills** out (not just hook configs), reusing the exact
`local.json` + mise-enter machinery. SSOT is `.agents/skills/` (the project's
enabled set: committed inherited skills + on-enter `./skills/*` app-skill links).
A table-driven linker symlinks each skill into every CLI that doesn't read
`.agents/` natively, with a per-target **scope**:

- **global** dir (e.g. `~/.codex/skills`, shared across projects): link ours in,
  never clobber foreign entries, remove ours on leave.
- **local** dir (e.g. `./.kimi-code/skills`, a project-scoped mirror): fully
  managed — replace stale real copies/foreign links with symlinks, prune disabled.

The reusable idea here is **`defer_to_global`**: when one dev runs a *machine-global*
skill system (`~/.agents/skills`) and a teammate doesn't, the project must provide
the full set to the teammate **without** duplicating-into / colliding-with the
global dev's per-CLI dirs. Solution — a per-dev `local.json` flag that, when set,
makes the linker **skip (and yield the slot for) any skill whose name also exists
in the global SSOT**. Auto-detected (membership test against `~/.agents/skills`),
so it needs no hand-maintained list; the teammate omits the flag and inherits
everything. This is the general answer to "share a curated set with someone whose
environment is a strict superset of the shared set."

## Adding a new agent CLI to this variant

1. Add `agents.<cli>` to `hooks.master.json`: `dialect`, `config_target`,
   `base_dir` (`$ENV/...` if the CLI injects a project-dir var, else `{repo}` for
   sync to substitute an absolute path), `timeout_unit`, `lifecycle_events`.
2. If the CLI's config is **shared/per-user**, mark injected commands by the repo
   path and implement strip-by-marker uninstall + `*.caf-bak`. If **committed**,
   own the relevant key and rely on `--check` for drift.
3. If the CLI runs hooks `shell=False` or with a different payload shape, write an
   adapter (don't reuse foreign-shaped scripts) and gate it with the shared
   `hook_disabled` check.
4. Wire it into the install/uninstall/check branches; respect `disabled_agents`.

### Worked example: adding the Kimi (`kimi-code`) dialect

Done in CAF — a clean illustration of "scout the target, then pick the closest
existing dialect." Kimi's hook engine is in its (unstripped) binary; `strings`
mining the `agent-core/src/session/hooks/` code revealed the full contract:

- **Per-user config only.** Hooks live in `~/.kimi-code/config.toml` (`KIMI_CODE_HOME`
  overrides) as a top-level `hooks` array of `{event, command, matcher?, timeout}`.
  There is **no** project-local `config.toml` (project scope covers only MCP, skills,
  instructions) — so it's **injected like Codex**, not committed like Claude.
- **Claude-compatible runtime.** Identical event names (`UserPromptSubmit`,
  `PostToolUse`, `Stop`, …); payload `{hook_event_name, session_id, cwd, prompt}` /
  `{tool_name, tool_input}` delivered as **JSON on stdin**; `spawn(command, {shell:true})`
  so `command` is a shell string; `timeout` in **seconds** (default 30); edit tools
  named `Write`/`Edit`. Net: **reuse the exact same guard-wrapped scripts** as
  Claude/Codex — no adapter needed (unlike Hermes).

The new dialect is therefore a near-clone of `codex_hooks`, differing only in the
**target file + format**: a **sentinel-bounded `[[hooks]]` block** appended to a TOML
file. The injection is **pure text** (no TOML library): strip any prior block between
the `# >>> marker BEGIN` / `# <<< marker END` sentinels, refuse if a *foreign* `hooks`
key exists (TOML would reject duplicate keys), drop an empty `hooks = []`, then append.
Strip removes exactly the one separator newline + block, so uninstall is **byte-exact**.
Marker = the repo's `.agents/hooks/` path in the command (same reversibility trick as
Codex). `disabled_agents:["kimi"]` opts out.

> Lesson for the next CLI: most coding-agent CLIs converge on the Claude hook shape
> (event names + stdin JSON + `shell:true` command + matcher). Confirm **(a)** config
> scope (project-committed vs per-user-injected) and **(b)** file format/dialect, and
> you can usually reuse the scripts verbatim — the dialect is just *where* and *how* the
> mapping is written.
