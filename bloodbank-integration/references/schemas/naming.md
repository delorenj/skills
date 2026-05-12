# Naming: event_type, NATS subject, routing key

A single dotted token chain drives three things: the JSON Schema filename, the CloudEvents `type` field, and the NATS subject. Get the name right once; rename costs are nontrivial.

## The convention

```
<domain>.<entity>.<action>

domain  — top-level area: agent, system, artifact, llm, theboard, github, fireflies, ...
entity  — the noun being acted on: session, tool, prompt, heartbeat, version, ...
action  — what happened, past tense: started, ended, invoked, requested, completed, recorded, ...
```

Lowercase, dot-separated, `^[a-z0-9]+(\.[a-z0-9]+)+$`. No camelCase, no underscores, no hyphens.

Examples already in the wild (confirmed by reading `holyfields/schemas/` + live `event-toaster` logs):

| Schema file | `type` (CloudEvents) | NATS subject |
|---|---|---|
| `agent/session.started.v1.json` | `agent.session.started` | `event.agent.session.started` |
| `agent/session.ended.v1.json` | `agent.session.ended` | `event.agent.session.ended` |
| `agent/tool.invoked.v1.json` | `agent.tool.invoked` | `event.agent.tool.invoked` |
| `agent/tool.requested.v1.json` | `agent.tool.requested` | `event.agent.tool.requested` |
| `system/heartbeat.tick.v1.json` | `system.heartbeat.tick` | `event.system.heartbeat.tick` |
| `artifact/lifecycle.v1.json` | `artifact.lifecycle.*` (parameterized) | `event.artifact.lifecycle.*` |

## Three name surfaces, one source

| Surface | Value derived from `type` |
|---|---|
| CloudEvents `type` field | the type itself, e.g. `agent.tool.invoked` |
| Dapr topic name | the type itself, e.g. `agent.tool.invoked` |
| NATS subject (under Dapr) | `event.` + type, e.g. `event.agent.tool.invoked` |
| v2 RabbitMQ routing key | the type itself (legacy path only) |

The `event.` prefix on NATS subjects is what lets `event-toaster` wildcard-subscribe on `event.>` to catch everything.

## Subject classes

NATS subjects on the bloodbank bus come in three flavors. Pick the right prefix:

| Subject prefix | Meaning | Producer | Consumer |
|---|---|---|---|
| `event.<dotted>`     | A thing happened. Fire-and-forget. | Service that owns the fact | Any number; no reply expected |
| `command.<target>.<verb>` | An instruction targeting a specific agent. May have a TTL. | Anyone (often `hookd_bridge`) | The named agent; FSM-guarded |
| `reply.<target>.<verb>`   | A reply to a command. Carries `correlation_id`. | The agent that handled the command | The original issuer |

If you're adding a new event, you almost always want `event.*`. Reach for `command.*` only when issuing an FSM-guarded directive to a specific agent (Lenoon, OpenClaw, etc.).

## Action verb tense

- Events: **past tense** (`started`, `ended`, `invoked`, `recorded`, `completed`, `failed`).
- Commands: **imperative** (`run_drift_check`, `claim_card`, `run_git_maintenance`).
- Heartbeats are the lone exception — `system.heartbeat.tick` is present tense by long-standing convention.

## When the dotted name has more than three tokens

Allowed when an additional `<sub-entity>` adds clarity, e.g. `agent.subagent.completed`. Keep the structure recognizable: `<domain>.<entity>[.<sub-entity>].<action>`.

## Anti-patterns

- Two-token names like `agent.invoked` (which entity? what action?). Always at least three tokens.
- Mixing tenses (`agent.session.start` vs `agent.session.ended` — pick past consistently for events).
- Putting the producer name in the subject (`event.heartbeat-tick.system.tick`). The producer goes in the envelope's `source` field.
- Publishing to a subject that doesn't match the envelope's `type`. The toaster will fire correctly but downstream consumers may filter by `type` and silently miss it.
