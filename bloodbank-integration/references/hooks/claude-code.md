# Claude Code -> Bloodbank

Claude Code Bloodbank hooks are generated from Bloodbank's hook SSOT and
installed into `~/.claude/settings.json`. They call the canonical publisher:

```bash
python3 ~/.agents/hooks/bloodbank/publish.py --client claude --hook <event-type>
```

`~/.agents/hooks/bloodbank` is a symlink to
`~/code/33GOD/bloodbank/services/agent-hooks`.

## Architecture

```
Claude Code hook
  -> ~/.claude/settings.json command
  -> ~/.agents/hooks/bloodbank/publish.py --client claude --hook <arg>
  -> clients/claude.py
  -> core.publisher + core.envelope + core.nats_publish
  -> bloodbank.evt.<domain>.<entity>.<action>
```

Claude-specific behavior lives in `services/agent-hooks/clients/claude.py`:
payload parsing, git/cwd context, tool outcome inference, session file location,
tool counters, and session archive.

## What gets published

| Claude hook | Publisher arg | CloudEvents `type` | NATS subject |
|---|---|---|---|
| `SessionStart` | `session-start` | `bloodbank.agent.session.started` | `bloodbank.evt.agent.session.started` |
| `UserPromptSubmit` | `prompt-submitted` | `bloodbank.conversation.turn.started` | `bloodbank.evt.conversation.turn.started` |
| `PreToolUse` | `tool-request` | `bloodbank.agent.tool.requested` | `bloodbank.evt.agent.tool.requested` |
| `PostToolUse` | `tool-action` | `bloodbank.agent.tool.completed` | `bloodbank.evt.agent.tool.completed` |
| `SubagentStop` | `subagent-stopped` | `bloodbank.agent.invocation.completed` | `bloodbank.evt.agent.invocation.completed` |
| `Stop` | `session-end` | `bloodbank.agent.session.ended` | `bloodbank.evt.agent.session.ended` |

Provider identity stays in the envelope actor:
`actor.cli=claude`, `actor.provider=anthropic`.

## Install / verify

```bash
cd ~/code/33GOD/bloodbank
mise run deploy
BLOODBANK_ENABLED=false python3 services/agent-hooks/health/hook_healthcheck.py --check
```

Manual smoke without touching the live session:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"ls"}}' \
  | HOME="$(mktemp -d)" BLOODBANK_ENABLED=false \
    python3 ~/.agents/hooks/bloodbank/publish.py --client claude --hook tool-action
```

With NATS running, set `BLOODBANK_HOOK_VERBOSE=1` and confirm
`bloodbank-event-toaster` sees `bloodbank.evt.agent.tool.completed`.

## Legacy wrappers

`services/agent-hooks/claude/publish.py` remains callable for one migration
cycle and re-exports the old constants health tooling imports, but it is a thin
wrapper. New logic belongs in `clients/claude.py` or shared `core/`, not in the
wrapper.
