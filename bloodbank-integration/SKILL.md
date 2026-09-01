---
name: bloodbank-integration
description: "Integrate producers, consumers, webhooks, or agent harnesses with the 33GOD Bloodbank event and command pipeline. Covers the full event journey, schemas in Bloodbank schemas/ and docs/event-naming.md, Plane webhook ingress through n8n, NATS/Dapr publication, Candystore projection, Holocene/toaster read sides, the fleet-shared Hermes command gateway, and canonical agent hooks. Use for event publish/consume, webhook normalization, command dispatch, authoring schemas, integrating harnesses (Claude Code, Copilot CLI, OpenCode, Cursor, Aider, Codex CLI, Hermes), or tracing a message end-to-end. Triggers: bloodbank, event bus, publish, subscribe, NATS subject, CloudEvents, Plane webhook, n8n Plane to Bloodbank, Candystore projection, event-toaster, ntfy.delo.sh/bloodbank, bloodbank.agent.session.started, bloodbank.agent.tool.completed, bloodbank.cmd.agent.invocation.start. Skip for generic brokers, general n8n workflow authoring, hindsight memory, or non-event-bus 33GOD."
---

# Bloodbank Integration

Route here when a service or harness needs to **emit** or **consume** events on the 33GOD bloodbank bus. The bus is the only sanctioned inter-service channel — never bypass it with direct calls.

## Operating Principles

- **Bus is canon.** All inter-service traffic flows through bloodbank. Direct service-to-service calls are an anti-pattern enforced repo-wide.
- **Schema first.** Every event has a JSON Schema under `bloodbank/schemas/`. Build envelopes through the canonical builder/validator path, and keep manual envelope examples derivable from the schema and naming contract.
- **NATS is the current bus.** v3 (Dapr + NATS JetStream + CloudEvents 1.0) is the live target. v2 (RabbitMQ topic exchange) still runs but is migration-only territory.
- **Facts and intent take different lanes.** Events are immutable facts on `bloodbank.evt.*`; commands are targeted intent on `bloodbank.cmd.*`. Candystore projects events, not commands. A command consumer emits lifecycle events so execution still becomes durable history.
- **Subject convention is load-bearing.** CloudEvents `type` is `bloodbank.<domain>.<entity>.<action>`. NATS subjects are `bloodbank.evt.<domain>.<entity>.<action>` for events, `bloodbank.cmd.<domain>.<entity>.<action>` for commands, and `bloodbank.rpy.<domain>.<entity>.<action>` for replies. The catch-all `event-toaster` listens on `bloodbank.evt.>`.
- **Plane enters through one provenance boundary.** Both self-hosted Plane workspaces post over HTTPS to the active `Plane → Bloodbank` n8n workflow. The custom node selects the 1Password secret by payload `webhook_id`, verifies `X-Plane-Signature` over the raw body, resolves the board through the Hermes registry, normalizes the provider action, and publishes NATS-direct. Port `8477` and Bloodbank HTTP `/event` are not active Plane paths.
- **Agent hooks use one publisher.** All CLI lifecycle hooks call `~/.agents/hooks/bloodbank/publish.py --client <agent> --hook <native-event>`. Client-specific prep lives in `services/agent-hooks/clients/<agent>.py`; per-client `publish.py` files are wrappers.
- **Fail open at the boundary.** Hooks must never block the host agent. Producer libs should swallow publish failures by default.

## Triage Table

Match the user's intent against the signals on the left; load the cited file first.

| Signal in the request | Load |
|---|---|
| "show the whole pipeline", "where does this event go", "producer to consumer", "event vs command", "trace this message" | `references/event-journey.md` |
| "Plane webhook", "HMAC error", "which n8n workflow", "automaticai workspace", "port 8477" | `references/event-journey.md`, then `docs/plane-event-normalization.md` |
| "define / author / version / change an event schema", `.json` under `bloodbank/schemas/`, "schema validation", "wire contract" | `references/schemas/README.md` |
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
├─ Yes → Dapr pub/sub. Subject = "bloodbank.evt.<domain>.<entity>.<action>", pubsub component = bloodbank-pubsub.
│        See references/producers/methods.md → "Dapr publish".
└─ No
   ├─ One-shot from a shell hook (Claude Code, Copilot, etc.)?
   │  → Canonical agent-hook publisher (stdlib raw TCP, no nats-py). See bloodbank/services/agent-hooks/.
   ├─ Long-running Python service on the host?
   │  → nats-py direct, subject "bloodbank.evt.<...>". See references/producers/methods.md.
   ├─ Plane webhook?
   │  → HTTPS `n8n.delo.sh/webhook/plane` → active `Plane → Bloodbank` workflow →
   │    custom HMAC/normalization node → NATS event. See references/event-journey.md.
   ├─ Another external webhook with HTTP only?
   │  → Build an authenticated ingress adapter that validates + normalizes before NATS.
   │    `/event` and `/publish` are legacy RabbitMQ paths, not defaults for new work.
   └─ HTTP client that needs to issue a COMMAND envelope (not an event)?
      → POST to hookd_bridge :18790/hooks/agent. See bloodbank/hookd_bridge/; command subject is `bloodbank.cmd.agent.invocation.start`.
```

## Decision Tree: Which Consumer Path?

```
Do you own a 33GOD service container with a Dapr sidecar?
├─ Yes → Dapr subscriber. Declare /dapr/subscribe routes. Reference: services/claude-events-recorder/main.py.
└─ No
   ├─ Need wildcard fan-in across many subjects (observability, audit, notify)?
   │  → NATS core subscribe on "bloodbank.evt.>" (no JetStream consumer, no durability).
   │    Reference: services/event-toaster/main.py.
   ├─ Need durable, replay-capable consumption on a specific subject?
   │  → NATS JetStream durable consumer. Subjects defined in compose/nats/streams.json.
   ├─ Legacy v2 consumer or RabbitMQ-only environment?
   │  → FastStream RabbitMQ consumer bound to exchange bloodbank.events.v1. Avoid for new work.
   └─ Just want desktop notifications for everything?
      → Subscribe to https://ntfy.delo.sh/bloodbank (event-toaster already publishes there).
```

## Cross-Cutting Rules

These apply regardless of producer/consumer path or language:

- **Envelope shape is fixed.** CloudEvents 1.0 + 33GOD extension fields (`producer`, `service`, `domain`, `schemaref`, `correlationid`, `causationid`). The canonical base lives at `bloodbank/schemas/_common/cloudevent_base.v1.json`; every event schema `allOf`-extends it.
- **`type` and NATS subject are bound.** The Dapr topic / NATS subject for an event is always the envelope's `subject`, derived from `type` by inserting `evt` after `bloodbank` (`bloodbank.agent.tool.completed` → `bloodbank.evt.agent.tool.completed`). Never publish to a subject that doesn't match the envelope.
- **The schema tree is keyed by domain, not version.** `schemas/bloodbank/agent/session.started.json`. A breaking payload change does NOT become a `.v2.json` — it becomes a new `action` or `entity`, i.e. a different fact with its own type and subject (event-naming.md §3.1). Only `dataschema`/`schemaref` carry a revision number.
- **Do not make schemas optional.** Edit the JSON Schema first, then validate with `mise run smoketest:schemas`.
- **Use Hindsight memory bank `bloodbank` for integration notes** — broker-level decisions, subject-naming surprises, consumer wiring gotchas live there, not in the code.
- **Test producers with the toaster.** `bloodbank-event-toaster` subscribes to `bloodbank.evt.>` and forwards every envelope to `https://ntfy.delo.sh/bloodbank`. If you don't see your event there, it didn't make it to NATS.
- **Prove durable arrival in Candystore.** The canonical projection subscribes through Dapr to `bloodbank.evt.>` and exposes loopback query API `GET http://127.0.0.1:8683/events`. A toaster notification proves live fan-out; a Candystore row proves durable projection.
- **Do not treat a running command gateway as routability.** The fleet gateway is default-deny. Before claiming commands can execute, count registry entries with `bloodbank.enabled: true`, `gateway_scope: fleet`, a matching `target_agent_id`, and a nonblank `profile_name`.

## Reading Order

For the most common entry points:

| Task | Read first | Then |
|---|---|---|
| Understand or prove the whole event/command journey | `references/event-journey.md` | the producer/consumer method it identifies |
| Author a brand-new event end-to-end | `references/schemas/README.md` | `references/producers/README.md`, `references/consumers/README.md` |
| Add a producer to an existing event | `references/producers/README.md` | `references/producers/methods.md` |
| Add a consumer to an existing event | `references/consumers/README.md` | `references/consumers/methods.md` |
| Integrate a new agent harness | `references/hooks/README.md` | `references/hooks/adding-a-harness.md` |
| Debug a missing event | The relevant topic's `gotchas.md` | `references/producers/gotchas.md` AND `references/consumers/gotchas.md` |

## Out of Scope

This skill does NOT cover:

- **Generic RabbitMQ / NATS / Kafka setup or tuning** unrelated to bloodbank's topology. Use the broker vendor's documentation; this skill assumes the v3 stack (`compose/v3/docker-compose.yml`) is already running.
- **General n8n workflow authoring or routing decisions.** Use `delonet-n8n-architecture` for canvas/node design. This skill still owns the Plane ingress contract at the n8n→Bloodbank boundary.
- **Hindsight memory recall/retain.** Use the `hindsight` skill for memory-bank operations even when wiring bloodbank events that *carry* memory references.
- **Non-event-bus parts of 33GOD** (Candystore persistence internals, Candybar UI work, Bloodbank validator implementation). Use the `33god-ecosystem` hub for routing, or the project's own AGENTS.md.
- **Schema validator internals.** This skill points at the schema workflow; change `scripts/validate_schemas.sh` and naming smoke tests in the Bloodbank repo when the validator itself changes.
- **Claude Code / Copilot CLI hook semantics themselves** (timeout flags, OS-specific behavior). Use the vendor docs; this skill covers the *wiring* layer between those hooks and bloodbank.
