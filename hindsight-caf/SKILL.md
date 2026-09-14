---
name: hindsight-caf
description: Project-scoped Hindsight memory for CoachingAgentFramework. Statically linked to the CoachingAgentFramework bank on the self-hosted Hindsight instance at https://api.hs.delo.sh, or to a locally-provisioned fallback stack when the shared server is unreachable. Use when retaining or recalling memory for this repo only, or when a developer needs to set up local Hindsight because the shared server is unavailable. Trigger with "recall CAF memory", "retain CAF context", "hindsight CoachingAgentFramework", "local hindsight setup", or any task scoped to this project's memory bank.
---

# Hindsight Memory for CoachingAgentFramework

Static-bank Hindsight operations for the Coaching Agent Framework repo. All recall and retain calls target the `CoachingAgentFramework` bank on the self-hosted instance at `https://api.hs.delo.sh`, or on a locally-provisioned fallback stack when the shared server is unavailable.

## Operating Principles

- **One bank only.** Every operation uses `CoachingAgentFramework`.
- **Recall before acting.** Check Hindsight before starting non-trivial work in this repo.
- **Retain high-signal facts.** Store conventions, decisions, debugging lessons, and preferences.
- **Prefer scripts.** Use the helpers in `scripts/` so the bank and endpoint never drift.
- **Local fallback is automatic.** The mise enter gate checks reachability; if the shared Hindsight is unreachable, it provisions a local Docker stack and points the repo `.env` at it.

## Quick Navigation

| Task | Command |
|---|---|
| Recall context | `./skills/hindsight-caf/scripts/recall.sh "<query>"` |
| Retain a fact | `./skills/hindsight-caf/scripts/retain.sh "<fact>" <context>` |
| Reflect/synthesize | `./skills/hindsight-caf/scripts/reflect.sh "<question>"` |
| Check bank stats | `hindsight bank stats CoachingAgentFramework` |
| Manual local setup | `mise run hindsight-local-setup` |
| Check current reachability | `hindsight health` |

## Bank & Endpoint

- **Bank**: `CoachingAgentFramework`
- **Default API URL**: `https://api.hs.delo.sh`
- **Local fallback URL**: `http://127.0.0.1:18888`
- **Web UI**: `https://hs.delo.sh` (shared); `http://127.0.0.1:19999` (local)

The Hindsight CLI should already point at `https://api.hs.delo.sh`. If not:

```bash
hindsight configure --api-url https://api.hs.delo.sh --api-key <key>
```

## Helpers

Scripts live in `./skills/hindsight-caf/scripts/` and hardcode the bank.

### Retain

```bash
./skills/hindsight-caf/scripts/retain.sh "Auth middleware requires X-Request-ID header" conventions
```

Context categories: `architecture`, `conventions`, `debugging`, `deployment`, `dependencies`, `preferences`, `session-summary`, `code-edit`.

Upsert a grouped fact with `--doc-id`:

```bash
./skills/hindsight-caf/scripts/retain.sh "Sprint goal shifted to onboarding gates" session-summary --doc-id caf-sprint-2026-06
```

### Recall

```bash
./skills/hindsight-caf/scripts/recall.sh "How is auth wired in this repo?"
```

JSON output for inspection:

```bash
./skills/hindsight-caf/scripts/recall.sh "testing patterns" --json | jq '.results[].text'
```

### Reflect

Reflect runs an agentic search-and-synthesis pass with citations.

```bash
./skills/hindsight-caf/scripts/reflect.sh "What architectural decisions shaped the auth flow?"
```

## Local / Offline Hindsight

When a developer cannot reach the shared Hindsight server, the repo can fall back to a self-contained local Docker stack. The stack is provisioned under `~/.local/share/hindsight-caf/` and consists of a Hindsight API + Control Plane container plus a `pgvector`-enabled Postgres container.

### How it is triggered

`mise enter` runs `.mise/scripts/hindsight-gate.sh`, which:

1. Loads the repo `.env`.
2. Runs `hindsight health` against the currently configured API URL.
3. If healthy, exits silently.
4. If unhealthy, checks the per-dev opt-out in `.agents/local.json`.
5. If not opted out, runs `mise run hindsight-local-setup` to create/start the local stack and rewrite `.env` to use it.

Run the setup manually at any time:

```bash
mise run hindsight-local-setup
```

### Opting out

To disable the automatic local fallback, add this to `.agents/local.json` (gitignored):

```json
{
  "hooks": {
    "disabled": ["hindsight-local-setup"]
  }
}
```

Or set the environment variable before entering the repo:

```bash
export HINDSIGHT_LOCAL_SETUP=0
```

### What the setup creates

- `~/.local/share/hindsight-caf/compose.yml`
- `~/.local/share/hindsight-caf/.env`
- A Docker volume `hindsight-caf_postgres-data` for persistence
- `HINDSIGHT_API_URL=http://127.0.0.1:18888` and `HINDSIGHT_API_KEY=local-dev` in the repo `.env`
- The `CoachingAgentFramework` bank if it does not already exist

### Requirements

- Docker Engine + Docker Compose v2
- `hindsight` CLI on PATH (install from the Hindsight release page if missing)
- For LLM-powered retain/consolidation/reflect: either an OpenRouter API key (`OPENROUTER_API_KEY`) or a local OpenAI-compatible endpoint (override via `HINDSIGHT_API_LLM_BASE_URL`).

## Direct CLI Usage

If you prefer the raw CLI, the bank is always `CoachingAgentFramework`:

```bash
hindsight memory recall CoachingAgentFramework "query"
hindsight memory retain CoachingAgentFramework "fact" --context conventions
hindsight memory reflect CoachingAgentFramework "question" --context "architecture review"
```

## When to Retain

- Discovered a bug fix or workaround specific to CAF
- Learned a project convention, naming rule, or pattern
- User stated a preference that should persist
- Completed a significant task — summarize what was done
- Captured something that did **not** work (negative knowledge)

## When to Recall

- Before starting a non-trivial task in this repo
- When making architectural or tooling decisions
- When the user asks about past CAF work or patterns
- When entering an unfamiliar area of the codebase

## Out of Scope

- **Multi-bank routing.** Use the global `hindsight` skill for cross-project or multi-agent bank resolution.
- **Other repos.** This skill targets only `CoachingAgentFramework`.
- **Hindsight plugin/hook setup.** Use the global `hindsight` skill for OpenClaw, Claude Code, or Codex hook installation.
- **MCP tool definitions or prompt engineering.** This skill covers only CLI memory operations for CAF.
