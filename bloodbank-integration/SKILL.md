---
name: bloodbank-integration
description: "Integrate services or agent harnesses with the 33GOD Bloodbank event bus. Covers schemas in Bloodbank schemas/ and docs/event-naming.md, producing events (NATS preferred; Dapr, HTTP /publish, hookd_bridge alternatives), consuming events (NATS, Dapr, FastStream, event-toaster), and agent hook wiring. Use for event publish/consume, authoring schemas, integrating harnesses (Claude Code, Copilot CLI, OpenCode, Cursor, Aider, Codex CLI), or debugging missing envelopes. Triggers: bloodbank, event bus, publish, subscribe, NATS subject, holyfields legacy, CloudEvents, hookd, event-toaster, ntfy.delo.sh/bloodbank, agent.session.started, agent.tool.invoked, command.{agent}.{action}. Skip for generic brokers, n8n, hindsight memory, or non-event-bus 33GOD."
---

# Bloodbank Integration

Route here when a service or harness needs to **emit** or **consume** events on the 33GOD bloodbank bus. The bus is the only sanctioned inter-service channel — never bypass it with direct calls.

## Operating Principles

- **Bus is canon.** All inter-service traffic flows through bloodbank. Direct service-to-service calls are an anti-pattern enforced repo-wide.
- **Schema first.** Every event has a JSON Schema under `bloodbank/schemas/`. Generate Pydantic/Zod from it; never hand-craft envelopes.
- **NATS is the current bus.** v3 (Dapr + NATS JetStream + CloudEvents 1.0) is the live target. v2 (RabbitMQ topic exchange) still runs but is migration-only territory.
- **Subject convention is load-bearing.** `event.<domain>.<entity>.<action>` for events, `command.<target>.<verb>` for commands, `reply.<target>.<verb>` for replies. The catch-all `event-toaster` listens on `event.>`.
- **Fail open at the boundary.** Hooks must never block the host agent. Producer libs should swallow publish failures by default.

## Triage Table

Match the user's intent against the signals on the left; load the cited file first.

| Signal in the request | Load |
|---|---|
| "define / author / version / change an event schema", `.json` under `bloodbank/schemas/`, "pydantic model", "Zod schema", "generated types" | `references/schemas/README.md` |
| "what should I name this event / subject", "dotted convention", "event_type", "routing key" | `references/schemas/naming.md` |
| "how do I publish / fire / emit", "send an event", "publish to bloodbank", "from <language>" | `references/producers/README.md` |
| "Dapr publish", "HTTP /publish", "hookd_bridge", "from a bash hook" | `references/producers/methods.md` |
| "how do I consume / subscribe / listen", "build a consumer", "react to events", "downstream service" | `references/consumers/README.md` |
| "Dapr subscriber", "FastStream", "event-toaster", "catch-all", "ntfy notification" | `references/consumers/methods.md` |
| "wire Claude Code hooks", "wire Copilot hooks", "integrate <harness> into bloodbank", "agent lifecycle events" | `references/hooks/README.md` |
| "add a new harness" (Cursor, Aider, OpenCode, Cody, Codex CLI, etc.) | `references/hooks/adding-a-harness.md` |
| "envelope didn't arrive", "consumer not getting messages", "subject mismatch", "drift" | the matching topic's `gotchas.md` |

## Decision Tree: Which Producer Path?

```
Are you in a 33GOD service container with a Dapr sidecar?
├─ Yes → Dapr pub/sub. Subject = "event.<type>", pubsub component = bloodbank-v3-pubsub.
│        See references/producers/methods.md → "Dapr publish".
└─ No
   ├─ One-shot from a shell hook (Claude Code, Copilot, etc.)?
   │  → Stdlib NATS publisher (raw TCP, no nats-py). See bloodbank/services/copilot-hooks/.
   ├─ Long-running Python service on the host?
   │  → nats-py direct, subject "event.<type>". See references/producers/methods.md.
   ├─ External webhook (Plane, GitHub, etc.) with HTTP only?
   │  → POST to bloodbank's /event (typed webhook) or /publish (generic). RabbitMQ path.
   └─ HTTP client that needs to issue a COMMAND envelope (not an event)?
      → POST to hookd_bridge :18790/hooks/agent. See bloodbank/hookd_bridge/.
```

## Decision Tree: Which Consumer Path?

```
Do you own a 33GOD service container with a Dapr sidecar?
├─ Yes → Dapr subscriber. Declare /dapr/subscribe routes. Reference: services/claude-events-recorder/main.py.
└─ No
   ├─ Need wildcard fan-in across many subjects (observability, audit, notify)?
   │  → NATS core subscribe on "event.>" (no JetStream consumer, no durability).
   │    Reference: services/event-toaster/main.py.
   ├─ Need durable, replay-capable consumption on a specific subject?
   │  → NATS JetStream durable consumer. Subjects defined in compose/v3/nats/streams.json.
   ├─ Legacy v2 consumer or RabbitMQ-only environment?
   │  → FastStream RabbitMQ consumer bound to exchange bloodbank.events.v1. Avoid for new work.
   └─ Just want desktop notifications for everything?
      → Subscribe to https://ntfy.delo.sh/bloodbank (event-toaster already publishes there).
```

## Cross-Cutting Rules

These apply regardless of producer/consumer path or language:

- **Envelope shape is fixed.** CloudEvents 1.0 + 33GOD extension fields (`producer`, `service`, `domain`, `schemaref`, `correlationid`, `causationid`). The canonical base lives at `bloodbank/schemas/_common/cloudevent_base.v1.json`; every event schema `allOf`-extends it.
- **`type` and NATS subject are bound.** The Dapr topic / NATS subject for an event is always `event.<type>` where `<type>` is the envelope's dotted `type` field. Never publish to a subject that doesn't match the envelope type.
- **Schema versioning is in the filename.** `schemas/agent/session.started.v1.json` is v1; a breaking change becomes `.v2.json` with a new `dataschema` URI.
- **Never hand-edit generated artifacts** under `bloodbank/packages/*/generated`. Edit the JSON Schema, regenerate, commit both.
- **Use Hindsight memory bank `bloodbank` for integration notes** — broker-level decisions, subject-naming surprises, consumer wiring gotchas live there, not in the code.
- **Test producers with the toaster.** `bloodbank-event-toaster` subscribes to `event.>` and forwards every envelope to `https://ntfy.delo.sh/bloodbank`. If you don't see your event there, it didn't make it to NATS.

## Reading Order

For the most common entry points:

| Task | Read first | Then |
|---|---|---|
| Author a brand-new event end-to-end | `references/schemas/README.md` | `references/producers/README.md`, `references/consumers/README.md` |
| Add a producer to an existing event | `references/producers/README.md` | `references/producers/methods.md` |
| Add a consumer to an existing event | `references/consumers/README.md` | `references/consumers/methods.md` |
| Integrate a new agent harness | `references/hooks/README.md` | `references/hooks/adding-a-harness.md` |
| Debug a missing event | The relevant topic's `gotchas.md` | `references/producers/gotchas.md` AND `references/consumers/gotchas.md` |

## Out of Scope

This skill does NOT cover:

- **Generic RabbitMQ / NATS / Kafka setup or tuning** unrelated to bloodbank's topology. Use the broker vendor's documentation; this skill assumes the v3 stack (`compose/v3/docker-compose.yml`) is already running.
- **n8n workflow authoring or routing decisions.** Use `workflow-router` to choose between n8n, bloodbank, and other automation tools.
- **Hindsight memory recall/retain.** Use the `hindsight` skill for memory-bank operations even when wiring bloodbank events that *carry* memory references.
- **Non-event-bus parts of 33GOD** (Candystore persistence internals, Candybar UI work, Bloodbank generator implementation). Use the `33god-ecosystem` hub for routing, or the project's own AGENTS.md.
- **Generating Pydantic/Zod code from schemas.** Run Bloodbank's own `mise run generate:all`; this skill points at the workflow but does not re-document the generator internals.
- **Claude Code / Copilot CLI hook semantics themselves** (timeout flags, OS-specific behavior). Use the vendor docs; this skill covers the *wiring* layer between those hooks and bloodbank.
