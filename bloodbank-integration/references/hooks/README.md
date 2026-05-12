# Hooks — agentic coder integrations

Two harnesses already publish into bloodbank: **Claude Code** (via the `hookd` Rust daemon) and **GitHub Copilot CLI** (via the `copilot-hooks` stdlib publisher). Both fire one envelope per harness-lifecycle event onto NATS `event.<harness>.<...>` so every consumer can react uniformly.

## Reading Order

| Task | Read |
|---|---|
| Wire OR debug Claude Code hooks | `claude-code.md` |
| Wire OR debug GitHub Copilot CLI hooks | `github-copilot.md` |
| Integrate a NEW harness (Cursor, Aider, Codex CLI, OpenCode, Cody, ...) | `adding-a-harness.md` |
| Hit a confusing hook-layer failure | `gotchas.md` |

## What "harness hooks" mean in 33GOD

Modern agent CLIs all expose a hook system: a config file that maps lifecycle events (session start, prompt submitted, before/after tool use, error, stop) to shell commands. We tap those hooks to fire bloodbank events without modifying the harness itself.

The resulting events have two consumers in production right now:

- `bloodbank-event-toaster` — every event reaches `https://ntfy.delo.sh/bloodbank` for human observability.
- `bloodbank-claude-events-recorder` — a Dapr subscriber that records the agent.* lifecycle.

## Subject layout per harness

| Harness | Subject root | Status |
|---|---|---|
| Claude Code     | `event.agent.session.*`, `event.agent.tool.*`, `event.agent.prompt.*` | Functional, in production |
| GitHub Copilot  | `event.copilot.session.*`, `event.copilot.tool.*`, `event.copilot.prompt.*`, `event.copilot.error.*`, `event.copilot.agent.*` | Functional |
| _new harness_   | `event.<harness>.<entity>.<action>` | See `adding-a-harness.md` |

Claude Code uses the legacy `agent.*` root because it predates the per-harness convention. New harnesses get their own root.

## Existing implementations to mirror

| Component | Path | Language |
|---|---|---|
| Claude Code hook bridge   | `~/code/33GOD/hookd/`                            | Rust daemon (`hookd-emit` → Unix socket → daemon → broker) |
| GitHub Copilot publisher  | `~/code/33GOD/bloodbank/services/copilot-hooks/` | Python stdlib (raw NATS TCP) |
| Copilot hooks config      | `~/.copilot/hooks/bloodbank.json` (symlinked)    | JSON |
| Claude Code recorder      | `~/code/33GOD/bloodbank/services/claude-events-recorder/main.py` | Python + Dapr |

Pick the closest match when adding a new harness and copy its structure. The Copilot pattern is simpler and works for any harness whose hook config supports `bash`-on-stdin; the hookd pattern is heavier-weight (Rust daemon + Unix socket) and pays off only when you have very high event rates or need on-host enrichment.
