# Hooks — agentic coder integrations

All supported agent CLIs publish lifecycle events through one Bloodbank hook
surface:

```bash
python3 ~/.agents/hooks/bloodbank/publish.py --client <claude|codex|copilot|hermes> --hook <native-event>
```

The symlink `~/.agents/hooks/bloodbank` points at
`~/code/33GOD/bloodbank/services/agent-hooks`. Generated configs for Claude,
Codex, Copilot, and Hermes all invoke that canonical entrypoint. Per-client
`claude/publish.py`, `codex/publish.py`, `copilot/publish.py`, and
`hermes/publish.py` remain as compatibility wrappers only.

## Reading Order

| Task | Read |
|---|---|
| Wire OR debug Claude Code hooks | `claude-code.md` |
| Wire OR debug GitHub Copilot CLI hooks | `github-copilot.md` |
| Integrate a NEW harness (Cursor, Aider, OpenCode, Cody, ...) | `adding-a-harness.md` |
| Hit a confusing hook-layer failure | `gotchas.md` |

## What "harness hooks" mean in 33GOD

Modern agent CLIs expose a hook system: a config file maps lifecycle events
(session start/end, prompt submitted, before/after tool use, error, stop) to
commands. Bloodbank taps those public hooks and emits provider-neutral
CloudEvents without modifying the harness.

Client-specific differences are isolated in
`services/agent-hooks/clients/<client>.py`:

- native hook names and config dialect
- stdin/env/argv payload parsing
- session-id, model, tool-result, and error-shape quirks
- data shaping for the shared CloudEvents envelope

Everything else is shared in `core/`: event-map resolution, session
causation/correlation, envelope construction, validation, NATS publish,
fail-open logging, and strict-mode behavior.

## Subject layout

All agent CLI hooks emit provider-neutral Bloodbank types. Provider identity
lives in `actor`, not in `type`.

| Semantic event | CloudEvents `type` | NATS subject |
|---|---|---|
| Session started | `bloodbank.agent.session.started` | `bloodbank.evt.agent.session.started` |
| Session ended | `bloodbank.agent.session.ended` | `bloodbank.evt.agent.session.ended` |
| Prompt/turn started | `bloodbank.conversation.turn.started` | `bloodbank.evt.conversation.turn.started` |
| Tool requested | `bloodbank.agent.tool.requested` | `bloodbank.evt.agent.tool.requested` |
| Tool completed | `bloodbank.agent.tool.completed` | `bloodbank.evt.agent.tool.completed` |
| Invocation started | `bloodbank.agent.invocation.started` | `bloodbank.evt.agent.invocation.started` |
| Invocation completed | `bloodbank.agent.invocation.completed` | `bloodbank.evt.agent.invocation.completed` |
| Invocation failed | `bloodbank.agent.invocation.failed` | `bloodbank.evt.agent.invocation.failed` |

`bloodbank-event-toaster` subscribes to `bloodbank.evt.>` and forwards every
event to `https://ntfy.delo.sh/bloodbank`.

## Current implementation

| Component | Path |
|---|---|
| Canonical entrypoint | `~/code/33GOD/bloodbank/services/agent-hooks/publish.py` |
| Client adapters | `~/code/33GOD/bloodbank/services/agent-hooks/clients/` |
| Shared publisher pipeline | `~/code/33GOD/bloodbank/services/agent-hooks/core/publisher.py` |
| Hook SSOT | `~/code/33GOD/bloodbank/services/agent-hooks/hooks.master.json` |
| Sync/install engine | `~/code/33GOD/bloodbank/services/agent-hooks/sync.py` |
| Operator-facing mount | `~/.agents/hooks/bloodbank` |

Use `cd ~/code/33GOD/bloodbank && mise run deploy` to regenerate and install
live configs. Use `mise run health:hooks:check` to validate deployed configs
without publishing.
