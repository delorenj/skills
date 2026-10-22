---
name: car-set-model
description: "Use when the driver (or an operator) wants the in-car desk to
  think with another model for a tile: deepseek flash, deepseek pro, free or
  auto. Sets the per-agent desk model alias (its routes go in front of the
  default ladder), persisted; never Anthropic; the agent's own Hermes model is
  untouched."
metadata:
  tool:
    contract: tool.json
    entrypoint: scripts/set_model.py
    effect: writes-desk-prefs
    consumers: [car-desk]
---

# car-set-model

Sets which model the Holocene car desk (the fast conversation layer of the voice-memo watcher, HOLOC-23) answers one tile
with. One tile is one agent (`holocene-pm`, ...). The choice is per agent, survives restarts and applies from the next
turn, with no restart. It changes the desk's ladder only: the agent's own Hermes model, the direct-turn model and the
model a delegated brief runs on are not touched.

## Aliases

One versioned table, `services/inbox-watcher/car_desk_aliases.json` in the holocene repo, shared by the watcher, its
`memo:model` verb and this script:

| alias | routes put in front of the default ladder | phrases |
| --- | --- | --- |
| `deepseek-flash` | Hyper `deepseek-v4.1-flash-1017` (4 s), DeepSeek API `deepseek-flash` (5 s) | deepseek flash, flash |
| `deepseek-pro` | Hyper `deepseek-v4-pro-0813` (6 s), DeepSeek API `deepseek-v4-pro` (9 s), budget 16 s | deepseek pro, pro |
| `free` | gateway `automaticai/free` on the holocene-converse token (8 s) | free, free model |
| `auto` | gateway `automaticai/auto/fast` on the holocene-converse token (7 s) | auto, autorouter |
| `default` | none: the unit's ladder (r1 Hyper flash, r2 DeepSeek flash, r3 auto/fast) | default model |

The rest of the default ladder still backs the alias up (the same upstream is never tried twice). Never Anthropic: the
watcher refuses any Claude route, bare `automaticai/auto`, `/orchestrator`, `/subagent` and `openrouter/auto`, and allows
`automaticai/auto/fast` and `automaticai/free` only on the holocene-converse token, whose gateway scope holds no
Anthropic route (re-checked with `GET /models`; an answer from a forbidden model is thrown away).

## Who calls it

- **The car desk** (consumer `car-desk`): `tool.json` (`car_set_model(model)`) is offered to the fast model and
  validated before the entrypoint runs (no shell, 3 s). "switch to deepseek pro", "use the free model", "switch the
  model to auto", "reset the model" run it with no LLM call; the driver hears "Holocene PM now thinks with Deep Seek Pro."
- **An operator or another agent**: run the script, or `mise -C ~/code/33GOD/holocene run memo:model <agent> <alias>`.

## Run it

```bash
scripts/set_model.py --json --agent holocene-pm --model "deepseek pro"
scripts/set_model.py --json --agent holocene-pm --model default
scripts/set_model.py --json --list
```

## Contract

- stdout: one JSON object, `{"ok": true, "agent", "model", "label", "spoken", "ladder", "cleared"}` or `{"ok": false, "error"}`.
- Exit codes: 0 done, 2 bad arguments, 3 refused (unknown alias, or an alias with a refused route), 1 failed.
- Effect: writes through the watcher's verb `memo_trace.py model <agent> <alias> --json --by <by>` (sets
  `tiles.<agent>.model` in `~/.local/state/holocene-auto/inbox-watcher/converse.json` under its fcntl lock). It stores an
  alias, never a key: keys stay `op://` item-UUID references in the table, read by the watcher.
- Environment: `HOLOCENE_MEMO_TRACE` (default `~/code/33GOD/holocene/services/inbox-watcher/memo_trace.py`),
  `HOLOCENE_CAR_DESK_ALIASES` (default `car_desk_aliases.json` next to it), `MEMO_STATE_DIR` passed through.
