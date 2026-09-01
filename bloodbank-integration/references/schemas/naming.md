# Naming: CloudEvents type and NATS subject

Authoritative source: `~/code/33GOD/bloodbank/docs/event-naming.md`.

Bloodbank separates the semantic event identity from the transport subject.
Get both right; downstream routing, schema validation, and JetStream stream
binding depend on it.

## CloudEvents `type`

Every event type is exactly four dotted tokens:

```text
bloodbank.<domain>.<entity>.<action>
```

Examples:

| Meaning | CloudEvents `type` |
|---|---|
| Agent session started | `bloodbank.agent.session.started` |
| Agent tool completed | `bloodbank.agent.tool.completed` |
| Conversation turn started | `bloodbank.conversation.turn.started` |
| System heartbeat received | `bloodbank.system.heartbeat.received` |

Provider, CLI, model, repo, and agent IDs do **not** go in `type`; use `actor`,
`source`, envelope metadata, or `data`.

## NATS subject

Subjects mirror `type` but insert the transport kind after `bloodbank`:

```text
bloodbank.<kind>.<domain>.<entity>.<action>
```

| Kind | Envelope `kind` | Subject prefix | Stream |
|---|---|---|---|
| `evt` | `event` | `bloodbank.evt.` | `BLOODBANK_EVENTS` |
| `cmd` | `command` | `bloodbank.cmd.` | `BLOODBANK_COMMANDS` |
| `rpy` | `reply` | `bloodbank.rpy.` | `BLOODBANK_COMMANDS` |

Example:

```text
type     bloodbank.agent.tool.completed
subject  bloodbank.evt.agent.tool.completed
```

The subject's `(domain, entity, action)` must match `type` exactly. The kind
marker is transport routing; `envelope.kind` remains authoritative.

## Subject filters

- `bloodbank.evt.agent.tool.completed` — exactly that event.
- `bloodbank.evt.agent.>` — all agent events.
- `bloodbank.evt.>` — event catch-all used by `bloodbank-event-toaster`.
- `bloodbank.cmd.agent.invocation.start` — command to start an invocation;
  target agent lives in `data.target_agent_id`, not in the subject path.

The legacy `event.>` / `command.>` / `reply.>` prefixes are deprecated.

## Action verb tense

- Events: past tense / past participle (`started`, `ended`, `completed`,
  `failed`, `received`, `clocked_in`).
- Commands: imperative present (`start`, `complete`, `invoke`, `clock_in`).
- Replies: same action as the command they answer.

## Anti-patterns

- `agent.session.started` — missing the `bloodbank` vendor prefix.
- `bloodbank.copilot.tool.completed` — provider encoded in `type`.
- `event.agent.tool.completed` — legacy subject prefix.
- `bloodbank.evt.agent.tool.invoked` when the envelope `type` is
  `bloodbank.agent.tool.completed`.
- Encoding target agent IDs in the command subject path.
