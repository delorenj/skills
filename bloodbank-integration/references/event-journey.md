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
  │ 2. resolve that webhook's op:// secret reference (cached in-process, 1h)
  │ 3. verify HMAC before normalization or publication
  │ 4. resolve board_id through pjangler project enrollment
  │    (every .project.json; wins on the repo slug), then
  │    ~/.hermes/agents-registry.yaml (HERMES_AGENTS_REGISTRY)
  │ 5. normalize Plane action to provider-neutral repo fact
  │    (a board nothing claims → Unrouted output → ntfy `lifecycle`
  │     "Unrouted Board", once per board per 24h; nothing published)
  │ 6. event id = uuid5(dedupe key); creation/delete/comment/board facts
  │    also carry Nats-Msg-Id (updates do not: their key is inferred)
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
- Resolved secrets are cached in-process for an hour and served stale when
  1Password is unreachable, so a vault rate limit no longer drops deliveries.

Canonical webhook IDs, secret references, action mapping, identity routing, and
idempotency rules live in `bloodbank/docs/plane-event-normalization.md`.

### Plane normalization

The provider aliases are declared in the schemas themselves — an
`x-provider-aliases` entry on `data.provider_event_type` of the canonical
schema — and everything else (n8n trigger aliases, the normalizer, this table)
derives from that declaration:

| Plane action | Provider provenance | Canonical fact (declares the alias) |
|---|---|---|
| project create | `plane.board.created` | `bloodbank.repo.board.created` |
| issue create | `plane.ticket.created` | `bloodbank.repo.task.created` |
| issue update / state activity / delete | `plane.ticket.updated`, `plane.ticket.transitioned`, `plane.ticket.deleted` | `bloodbank.repo.task.updated` |
| issue comment create | `plane.ticket.commented` | `bloodbank.repo.task.appended` |

The subject is the canonical one (`bloodbank.evt.repo.task.created`, …). The
provider name stays in `data.provider_event_type`; the wire contract stays
provider-neutral. A Plane retry derives the same deterministic event ID, and
Candystore's idempotent insert prevents a second durable fact.
`repo.board.created` for a board no project claims carries `repo: null`.

**Who emits these facts: only this normalizer.** An agent, PM or script never
publishes `repo.task.*` or `repo.board.*`. It writes Plane (`px task create`,
`px move`; on a Krebs-managed board `bloodbank.cmd.lifecycle.task.invoke` with
`data.command.operation: create`) and the webhook echo becomes the fact.

**Missed deliveries.** Plane does not retry an HTTP error, so a ticket created
while n8n is down never reaches the bus by webhook. *Plane Ingress Reconcile*
(`U4hYm3BYPPeZNDHQ`, every 10 min) republishes missing creation facts through
the same normalizer (`data.trigger_source: plane-reconcile`, same event id and
`Nats-Msg-Id`, at most 20 per sweep). Updates, transitions and comments made
during an outage are not recovered.

### The n8n ticket lanes (n8n-nodes-bloodbank 0.7.2)

```text
bloodbank.evt.repo.task.created / .updated
  ▼ Bloodbank Trigger (alias plane.ticket.created / plane.ticket.transitioned;
  │   durable JetStream pull consumer, acked after the execution)
33GOD Agent Fleet node (Groom Ticket / Delegate Ticket)
  ├─ Dispatched → bloodbank.cmd.agent.invocation.start
  │    command_id = uuid5(causing event id, operation, agent) → redelivery dedups
  │    data.context {reason: ticket-grooming|ticket-delegation, repo, ticket_key,
  │                  ticket_id, board_id, workspace, title, phase, …}
  └─ Skipped → bloodbank.evt.agent.invocation.skipped
       data {reason, skip_code: provider_event_guard|phase_guard|ineligible|
             invalid_policy|fenced|no_route, target_agent_id|null, context{…}}
```

A skip is a fact on the bus, not a silent green execution: "why did nobody
groom this ticket?" is answered by querying Candystore for
`bloodbank.agent.invocation.skipped` with the ticket's `data.context.board_id`.

| Workflow (id) | Starts on | ntfy `lifecycle` push |
|---|---|---|
| Plane → Bloodbank (`iMw484J1ZCqKME2C`) | Plane webhook | Unrouted Board (1/board/24h) |
| Plane Ingress Reconcile (`U4hYm3BYPPeZNDHQ`) | every 10 min | Recovered missed ticket |
| Ticket Grooming (`6wAGA5pdrmHLyhs2`) | `plane.ticket.created` | Triage Started / Triage Skipped |
| Ticket Delegation (`8mmqdMwQYA28ZwUj`) | `plane.ticket.transitioned` into Todo | Delegation Started / Skipped (not `phase_guard`, `provider_event_guard`) |
| Ticket Pickup Chip (`wWXgCZiiIBWaRRzE`) | `agent.invocation.started/completed/failed` with `data.context.reason` in the two lanes; hourly stale-chip sweep | none |

- **Fleet node:** outputs Dispatched and Skipped; mapping params are visible
  expressions over the envelope; the registry path is `HERMES_AGENTS_REGISTRY`
  (default `~/.hermes/agents-registry.yaml`); `providerEventGuard` is strict (set
  and absent on the item → skip).
- **The chip is stateless.** The gateway echoes the command's `data.context` on
  `agent.invocation.started`, `.completed` and `.failed`; the chip adds
  `agent:working` on started and removes it on the end event. It leaves the label
  if the ticket moved into *In Progress* or gained an assignee during the turn
  (a claim). `agent:working` is pipeline-owned: lane prompts tell agents never to
  touch it, and the Plane MCP refuses writes to it.
- **Plane's v1 PATCH replaces the whole label list** (no per-label endpoint), so
  every label writer re-reads the issue and changes one label at a time.

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
  │ 3. check the Bloodbank route block (no enabled key = enabled)
  │ 4. journal command digest + state in mode-0600 SQLite
  │ 5. dispatch to the selected Hermes profile
  │ 6. wait for Hermes processing-complete
  ▼
Lifecycle event publications on `bloodbank.evt.*`
  ├─ conversation.turn.started
  ├─ agent.invocation.started              (echo the command's data.context)
  ├─ agent.invocation.completed OR agent.invocation.failed   (same echo)
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
      enabled: true          # or ABSENT: no key means enabled
      gateway_scope: fleet
      target_agent_id: <same-agent-id>
```

`enabled: false` switches the route off; any other present value (`"true"`,
`null`, `1`) is invalid and treated as off.

The gateway does not infer permission from a running systemd unit, Telegram
configuration, profile existence, or a past successful command. A running
gateway with zero eligible entries is healthy but intentionally unroutable.

## Which component owns what?

| Boundary | Owner | Responsibility |
|---|---|---|
| Plane webhook registration and payload | Plane | Fires signed provider actions |
| HTTPS/raw-body HMAC and provider normalization | n8n + Bloodbank custom node | Authenticates provenance and emits one canonical fact |
| Schemas, subjects, streams, transport contract | Bloodbank | Contract and event/command backbone authority |
| Project/board identity | `.project.json` → pjangler project registry | Maps provider board IDs without workspace guessing |
| Agent identity and routing | `~/.hermes/agents-registry.yaml`, the org chart Flume writes | Resolves `target_agent_id` to a profile and a gateway route |
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
- **"The n8n execution was green, so the ticket was handled."** No. Check the
  Fleet node's Skipped output, or `bloodbank.agent.invocation.skipped` on the bus.
- **"The board has no tickets."** An archived Plane board reads as 0 issues and
  0 states through the API with no error. Check `archived_at` / count in the
  Plane DB before calling it empty.
- **"A command belongs in Candystore."** The command is short-lived intent; its
  execution lifecycle events are the durable audit facts.
