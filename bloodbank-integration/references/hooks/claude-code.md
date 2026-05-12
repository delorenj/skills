# Claude Code → bloodbank

Claude Code's hook system writes tool-mutation events to a Unix socket; the `hookd` Rust daemon reads them, enriches them, and publishes to bloodbank.

## Architecture

```
Claude Code hook → bin/hookd-emit → Unix socket → hookd (Rust) → bloodbank (RabbitMQ)
                                                                ↓
                                                  Dapr subscriber: claude-events-recorder
```

Source of truth: `~/code/33GOD/hookd/README.md` and `hookd/src/`.

## What gets published

| Claude Code hook | Envelope `type` | NATS subject (where Dapr forwards) |
|---|---|---|
| `SessionStart`       | `agent.session.started`        | `event.agent.session.started` |
| `SessionEnd`         | `agent.session.ended`          | `event.agent.session.ended` |
| `UserPromptSubmit`   | `agent.prompt.submitted`       | `event.agent.prompt.submitted` |
| `PreToolUse`         | `agent.tool.requested`         | `event.agent.tool.requested` |
| `PostToolUse`        | `agent.tool.invoked`           | `event.agent.tool.invoked` |
| `SubagentStop`       | `agent.subagent.completed`     | `event.agent.subagent.completed` |
| `Stop`               | `agent.session.ended` (variant)| `event.agent.session.ended` |

(See `bloodbank/services/claude-events-recorder/main.py:SUBSCRIPTIONS` for the live consumer's view of which subjects exist.)

## Install / verify

1. `cargo run` (or `cargo build --release && ./target/release/hookd`) in `~/code/33GOD/hookd/`.
2. Claude Code's `~/.claude/settings.json` already maps each hook to `bin/hookd-emit`. Confirm by searching the file for `hookd-emit`.
3. Trigger any tool use in Claude Code, then check:
   - `docker logs bloodbank-event-toaster --tail 5` should show a `toasted: agent.tool.invoked` line.
   - `curl -s https://ntfy.delo.sh/bloodbank/json?poll=1&since=30s | jq .title` should include `agent.tool.invoked`.

## Why a Rust daemon instead of a stdlib script?

Three reasons:

1. **Volume.** Tool-use events can arrive in bursts (parallel tool calls). The daemon batches and decouples publish latency from hook latency.
2. **Enrichment.** The daemon resolves git branch / commit / pwd / session_id once and stamps every event, instead of every hook script re-discovering them.
3. **Unix socket.** The hook script (`hookd-emit`) writes a single line and exits — no NATS connection setup per event.

If you don't have either of (1) or (2), the simpler Copilot pattern (stdlib NATS TCP) is fine.

## Not to be confused with `hookd_bridge`

Despite the name, `bloodbank/hookd_bridge/` is a **different** component: HTTP→AMQP for command envelopes from OpenClaw. See `bloodbank/hookd_bridge/__init__.py` for the boundary callout.
