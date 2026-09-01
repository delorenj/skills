# The full 33GOD event and command journey

Read this when the question is not merely "how do I publish?" but "what happens
from the original action to every meaningful consumer?" It names the live
transport, security, identity, durability, and observation boundaries.

## Mental model

| Lane | Meaning | Subject | Retention | Durable history |
|---|---|---|---|---|
| Event | An immutable fact that already happened | `bloodbank.evt.<domain>.<entity>.<action>` | `BLOODBANK_EVENTS`, limits retention, seven days | Candystore projects it into PostgreSQL |
| Command | Targeted intent asking one consumer to act | `bloodbank.cmd.<domain>.<entity>.<action>` | `BLOODBANK_COMMANDS`, work-queue retention, one day | Not projected directly; the consumer emits lifecycle events |
| Reply | Short-lived correlated response when a request/reply contract needs one | `bloodbank.rpy.<domain>.<entity>.<action>` | `BLOODBANK_COMMANDS`, one day | Not a source-of-truth history |

Do not put an agent ID, repo slug, workspace, or board into extra subject tokens.
Routing data belongs in the schema-defined envelope. Events are broadcast facts;
commands have one intentional consumer.

`BLOODBANK_EVENTS` binds exactly one subject: `bloodbank.evt.>`. There is no
version tier to enumerate any more, so there is nothing to register a new
wildcard for — the stream admits every event kind by construction. Candystore
binds the same `bloodbank.evt.>` so durable history receives everything the
stream admits. The wildcard does not authorize producers to invent subjects:
the schemas and `validate.py`'s domain/entity/action allowlists remain the
admission boundary, and they are checked at publish time, not at bind time.

## Journey A: Plane fact to durable 33GOD history

```text
Plane workspace (33god or automaticai)
  │ HTTPS POST /webhook/plane
  │ X-Plane-Signature + exact raw request body
  ▼
n8n workflow `Plane → Bloodbank` (iMw484J1ZCqKME2C)
  │ 1. read payload.webhook_id
  │ 2. resolve that webhook's op:// secret reference
  │ 3. verify HMAC before normalization or publication
  │ 4. resolve board_id through ~/.hermes/agents-registry.yaml
  │ 5. normalize Plane action to provider-neutral repo fact
  ▼
NATS `bloodbank.evt.repo.*`
  ├─ JetStream `BLOODBANK_EVENTS` retains the immutable envelope
  ├─ event-toaster core subscription fans out to ntfy for human observation
  └─ Dapr durable `candystore-events` subscription (`bloodbank.evt.>`)
       ▼
     Candystore `/events/all` → idempotent PostgreSQL insert
       ├─ query API `http://127.0.0.1:8683/events`
       └─ Holocene reads selected history/health views from Candystore
```

The `automaticai` string in this journey is a workspace tenant slug on the same
self-hosted Plane instance and personal infrastructure. It is not a separate
company, service boundary, n8n instance, or credential authority.

### Plane security boundary

- TLS encrypts the network hop to `n8n.delo.sh`.
- HMAC authenticates the exact raw request body; HMAC is not encryption.
- Each Plane webhook has its own secret. The node selects it by `webhook_id` and
  resolves only the corresponding `op://DeLoSecrets/...` reference at runtime.
- Unknown webhook IDs and invalid signatures stop before NATS publication.
- n8n's webhook node must preserve the raw body. Re-serializing parsed JSON
  changes bytes and causes a valid signature to fail.
- The retired host relay on port `8477` is not part of the live journey.

Canonical webhook IDs, secret references, action mapping, identity routing, and
idempotency rules live in `bloodbank/docs/plane-event-normalization.md`.

### Plane normalization

| Plane action | Provider provenance | Canonical fact | NATS subject |
|---|---|---|---|
| project create | `plane.board.created` | `bloodbank.repo.board.created` | `bloodbank.evt.repo.board.created` |
| issue create | `plane.ticket.created` | `bloodbank.repo.task.created` | `bloodbank.evt.repo.task.created` |
| issue update/state activity | `plane.ticket.updated` or `plane.ticket.transitioned` | `bloodbank.repo.task.updated` | `bloodbank.evt.repo.task.updated` |
| issue comment create | `plane.ticket.commented` | `bloodbank.repo.task.appended` | `bloodbank.evt.repo.task.appended` |
| issue delete | `plane.ticket.deleted` | `bloodbank.repo.task.updated` | `bloodbank.evt.repo.task.updated` |

The provider name stays in `data.provider_event_type`; the wire contract stays
provider-neutral. A Plane retry derives the same deterministic event ID, and
Candystore's idempotent insert prevents a second durable fact.

## Journey B: targeted command to Hermes execution and facts

```text
Command producer (PM/control plane/operator adapter)
  │ full CloudEvents command envelope
  │ subject: bloodbank.cmd.agent.invocation.start
  │ data.target_agent_id + data.prompt + idempotency_key
  ▼
JetStream `BLOODBANK_COMMANDS` (work-queue retention)
  ▼ durable pull consumer `bloodbank-hermes-gateway`
Fleet-shared `hermes-fleet-bloodbank-gateway.service`
  │ 1. cap size and validate command/schema/actor/prompt
  │ 2. resolve target_agent_id through fleet registry
  │ 3. require explicit Bloodbank eligibility (default deny)
  │ 4. journal command digest + state in mode-0600 SQLite
  │ 5. dispatch to the selected Hermes profile
  │ 6. wait for Hermes processing-complete
  ▼
Lifecycle event publications on `bloodbank.evt.*`
  ├─ conversation.turn.started
  ├─ agent.invocation.started
  ├─ agent.invocation.completed OR agent.invocation.failed
  └─ conversation.turn.completed
       ├─ `BLOODBANK_EVENTS`
       ├─ Candystore durable projection
       ├─ Holocene fleet/velocity read model
       └─ event-toaster → ntfy
```

The gateway acknowledges a command only after Hermes processing and terminal
lifecycle publication complete. Its SQLite execution journal makes redelivery
idempotent at the Hermes-execution boundary and preserves the exact lifecycle
payloads. JetStream is still at-least-once; this is not a global exactly-once
claim.

### Command routing gate

A registry route is eligible only when all of these are true:

```yaml
agents:
  <agent-id>:
    profile_name: <nonblank-profile>
    bloodbank:
      enabled: true
      gateway_scope: fleet
      target_agent_id: <same-agent-id>
```

The gateway does not infer permission from a running systemd unit, Telegram
configuration, profile existence, or a past successful command. A running
gateway with zero eligible entries is healthy but intentionally unroutable.

## Which component owns what?

| Boundary | Owner | Responsibility |
|---|---|---|
| Plane webhook registration and payload | Plane | Fires signed provider actions |
| HTTPS/raw-body HMAC and provider normalization | n8n + Bloodbank custom node | Authenticates provenance and emits one canonical fact |
| Schemas, subjects, streams, transport contract | Bloodbank | Contract and event/command backbone authority |
| Project/board/agent identity | `.project.json` → PJangler fleet registry | Maps provider board IDs and target agent IDs without workspace guessing |
| Durable event projection | Candystore | Dapr subscription, idempotent insert, query API |
| Agent command consumption | Hermes fleet gateway | Validates, authorizes, journals, dispatches, and emits lifecycle facts |
| Operator read model | Holocene | Reads selected Candystore/fleet state; does not become event authority |
| Human notification | event-toaster / ntfy | Best-effort observation; not durable proof |

## End-to-end proof checklist

### Plane event

1. Confirm the Plane webhook is active and targets
   `https://n8n.delo.sh/webhook/plane` with all intended event flags.
2. Confirm n8n workflow `iMw484J1ZCqKME2C` is active and raw-body handling is
   enabled.
3. Trigger one safe Plane action.
4. Confirm the n8n execution accepted the known `webhook_id` and HMAC.
5. Confirm the expected NATS subject or event-toaster observation.
6. Query Candystore by producer and type, for example:
   `GET /events?producer=n8n-plane-webhook&type=bloodbank.repo.task.created`.
7. Match `id`, `workspace`, `board_id`, `repo`, and
   `data.provider_event_type` across the trace.

### Hermes command

1. Confirm `BLOODBANK_COMMANDS` binds `bloodbank.cmd.>` and the fleet
   gateway service is active.
2. Audit the target's current registry eligibility; do not rely on history.
3. Validate the full envelope, including `kind=command`, `actor`,
   `schemaref=bloodbank.agent.invocation.start.v1`, nonempty `data.prompt`,
   `data.target_agent_id`, and an idempotency key.
4. Publish only if the action itself is authorized; a smoke test invokes a real
   agent.
5. Match the command ID/correlation ID in the gateway journal and the emitted
   started/terminal events in Candystore.

## Common false conclusions

- **"n8n returned 200, so the event is durable."** No. Prove the Candystore row.
- **"ntfy showed it, so Candystore has it."** No. The toaster and Candystore are
  independent consumers.
- **"The gateway service is running, so commands can execute."** No. Prove the
  current registry route is eligible.
- **"automaticai is another infrastructure owner."** No. It is a Plane workspace
  slug on the same self-hosted instance.
- **"Plane can use `/event` or port 8477 too."** Not in the live canonical path.
- **"A command belongs in Candystore."** The command is short-lived intent; its
  execution lifecycle events are the durable audit facts.
