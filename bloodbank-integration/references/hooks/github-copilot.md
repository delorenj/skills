# GitHub Copilot CLI → bloodbank

Stdlib Python script publishes directly to NATS via raw TCP. No daemon, no virtualenv, no third-party dependency. One script + one hooks-config file.

## Architecture

```
Copilot CLI hook → ~/.copilot/hooks/bloodbank.json
                  → bash entry → python3 copilot_hook_publish.py <hookName>
                  → NATS event.copilot.<dotted>
                  → bloodbank-event-toaster → ntfy.delo.sh/bloodbank
```

Files:

- Publisher: `~/code/33GOD/bloodbank/services/copilot-hooks/copilot_hook_publish.py`
- Canonical hooks config: `~/code/33GOD/bloodbank/services/copilot-hooks/hooks.json`
- User-level install: `~/.copilot/hooks/bloodbank.json` (symlink to the canonical)
- Repo README: `~/code/33GOD/bloodbank/services/copilot-hooks/README.md`

## Supported hooks

Reference: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks>.

| Copilot hook         | NATS subject                       | Envelope `type`            |
|----------------------|------------------------------------|----------------------------|
| `sessionStart`       | `event.copilot.session.started`    | `copilot.session.started`  |
| `sessionEnd`         | `event.copilot.session.ended`      | `copilot.session.ended`    |
| `userPromptSubmitted`| `event.copilot.prompt.submitted`   | `copilot.prompt.submitted` |
| `preToolUse`         | `event.copilot.tool.pre`           | `copilot.tool.pre`         |
| `postToolUse`        | `event.copilot.tool.post`          | `copilot.tool.post`        |
| `errorOccurred`      | `event.copilot.error.occurred`     | `copilot.error.occurred`   |
| `agentStop`          | `event.copilot.agent.stopped`      | `copilot.agent.stopped`    |

Unknown hook names fall through a camelCase→dotted transform (`fooBarBaz` → `foo.bar.baz`).

## Install / verify

Install (symlinks the canonical config into Copilot's user-level hooks dir):

```bash
mkdir -p ~/.copilot/hooks
ln -snf ~/code/33GOD/bloodbank/services/copilot-hooks/hooks.json ~/.copilot/hooks/bloodbank.json
```

Verify end-to-end without launching Copilot:

```bash
SCRIPT=~/code/33GOD/bloodbank/services/copilot-hooks/copilot_hook_publish.py
for h in sessionStart sessionEnd userPromptSubmitted preToolUse postToolUse errorOccurred agentStop; do
  echo "{\"probe\":\"$h\"}" | python3 "$SCRIPT" "$h"
done
docker logs bloodbank-event-toaster --tail 20 | grep 'toasted: copilot'
```

You should see all seven `copilot.*` lines, and matching titles on `https://ntfy.delo.sh/bloodbank`.

## Why stdlib instead of nats-py

bloodbank's own Python project doesn't depend on nats-py. Keeping the publisher dep-free means the hook installs without a venv anywhere on the system, and it's trivial to drop into other harnesses.

NATS' PUB protocol is text-based — `CONNECT {...}\r\nPUB <subject> <size>\r\n<body>\r\nPING\r\n` — and one TCP round-trip suffices for a fire-and-forget publish.

## Configuration knobs

Set in the hook entry's `env` block or in the surrounding shell:

| Env var | Default | Purpose |
|---|---|---|
| `BLOODBANK_NATS_HOST`    | `127.0.0.1` | NATS host |
| `BLOODBANK_NATS_PORT`    | `4222`      | NATS port |
| `BLOODBANK_NATS_TIMEOUT` | `3.0`       | Connect/publish timeout (seconds) |
| `BLOODBANK_HOOK_STRICT`  | _(unset)_   | When `1`, non-zero exit on publish failure (default fails open) |
| `BLOODBANK_HOOK_VERBOSE` | _(unset)_   | When set, log "published <subject>" to stderr |

## Fail-open contract

The publisher exits `0` on connect/publish failures by default. A broken NATS does not slow Copilot or block tool use. Set `BLOODBANK_HOOK_STRICT=1` while debugging to surface failures.
