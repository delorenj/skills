---
name: hindsight-caf
description: Project-scoped Hindsight memory for CoachingAgentFramework. Statically linked to the CoachingAgentFramework bank on the self-hosted Hindsight instance at https://api.hs.delo.sh. Use when retaining or recalling memory for this repo only — no bank resolution, no multi-bank routing. Trigger with "recall CAF memory", "retain CAF context", "hindsight CoachingAgentFramework", or any task scoped to this project's memory bank.
---

# Hindsight Memory for CoachingAgentFramework

Static-bank Hindsight operations for the Coaching Agent Framework repo. All recall and retain calls target the `CoachingAgentFramework` bank on the self-hosted instance at `https://api.hs.delo.sh`.

## Operating Principles

- **One bank only.** Every operation uses `CoachingAgentFramework`.
- **Recall before acting.** Check Hindsight before starting non-trivial work in this repo.
- **Retain high-signal facts.** Store conventions, decisions, debugging lessons, and preferences.
- **Prefer scripts.** Use the helpers in `scripts/` so the bank and endpoint never drift.

## Quick Navigation

| Task | Command |
|---|---|
| Recall context | `./skills/hindsight-caf/scripts/recall.sh "<query>"` |
| Retain a fact | `./skills/hindsight-caf/scripts/retain.sh "<fact>" <context>` |
| Reflect/synthesize | `./skills/hindsight-caf/scripts/reflect.sh "<question>"` |
| Check bank stats | `hindsight bank stats CoachingAgentFramework` |

## Bank & Endpoint

- **Bank**: `CoachingAgentFramework`
- **API URL**: `https://api.hs.delo.sh`
- **Web UI**: `https://hs.delo.sh`

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
