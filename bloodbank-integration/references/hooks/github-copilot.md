# GitHub Copilot CLI -> Bloodbank

Copilot hooks are generated from Bloodbank's hook SSOT and installed as:

```text
~/.copilot/hooks/bloodbank.json -> ~/code/33GOD/bloodbank/services/agent-hooks/copilot/hooks.json
```

Each generated hook invokes the canonical publisher:

```bash
exec python3 ~/.agents/hooks/bloodbank/publish.py --client copilot --hook <hookName>
```

## Architecture

```
Copilot CLI hook
  -> ~/.copilot/hooks/bloodbank.json
  -> ~/.agents/hooks/bloodbank/publish.py --client copilot --hook <hookName>
  -> clients/copilot.py
  -> core.publisher + core.envelope + core.nats_publish
  -> bloodbank.evt.<domain>.<entity>.<action>
```

The publisher is stdlib-only and fail-open by default; no virtualenv or
`nats-py` is required for hook execution.

## Supported hooks

Reference: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks>.

| Copilot hook | CloudEvents `type` | NATS subject |
|---|---|---|
| `sessionStart` | `bloodbank.agent.session.started` | `bloodbank.evt.agent.session.started` |
| `sessionEnd` | `bloodbank.agent.session.ended` | `bloodbank.evt.agent.session.ended` |
| `userPromptSubmitted` | `bloodbank.conversation.turn.started` | `bloodbank.evt.conversation.turn.started` |
| `preToolUse` | `bloodbank.agent.tool.requested` | `bloodbank.evt.agent.tool.requested` |
| `postToolUse` | `bloodbank.agent.tool.completed` | `bloodbank.evt.agent.tool.completed` |
| `errorOccurred` | `bloodbank.agent.invocation.failed` | `bloodbank.evt.agent.invocation.failed` |
| `agentStop` | `bloodbank.agent.invocation.completed` | `bloodbank.evt.agent.invocation.completed` |

Provider identity stays in `actor.cli=copilot` and
`actor.provider=github_copilot`; it is not encoded into `type`.

## Install / verify

```bash
cd ~/code/33GOD/bloodbank
mise run deploy
BLOODBANK_ENABLED=false python3 services/agent-hooks/health/hook_healthcheck.py --check
```

Manual smoke:

```bash
for h in sessionStart sessionEnd userPromptSubmitted preToolUse postToolUse errorOccurred agentStop; do
  printf '{"probe":"%s"}' "$h" \
    | HOME="$(mktemp -d)" BLOODBANK_ENABLED=false \
      python3 ~/.agents/hooks/bloodbank/publish.py --client copilot --hook "$h"
done
```

With NATS running, set `BLOODBANK_HOOK_VERBOSE=1` and tail
`bloodbank-event-toaster`.

## Configuration knobs

| Env var | Default | Purpose |
|---|---|---|
| `BLOODBANK_NATS_HOST` | `127.0.0.1` | NATS host |
| `BLOODBANK_NATS_PORT` | `4222` | NATS port |
| `BLOODBANK_NATS_TIMEOUT` | `3.0` | Connect/publish timeout in seconds |
| `BLOODBANK_ENABLED` | `true` | `false` disables publishing while still exercising local hook code |
| `BLOODBANK_HOOK_STRICT` | unset | `1` returns non-zero on publish failure |
| `BLOODBANK_HOOK_VERBOSE` | unset | Log `published <subject>` to stderr |

## Legacy wrappers

`services/agent-hooks/copilot/publish.py` is still callable, but it is a thin
wrapper around the canonical publisher. Add new behavior in
`clients/copilot.py` or shared `core/`.
