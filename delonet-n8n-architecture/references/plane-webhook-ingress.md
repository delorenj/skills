# Plane webhook ingress

Read this when operating, reviewing, or debugging the canonical Plane → 33GOD
event boundary in n8n.

## Live identity

| Item | Value |
|---|---|
| Public endpoint | `https://n8n.delo.sh/webhook/plane` |
| Workflow | `Plane → Bloodbank` |
| Workflow ID | `iMw484J1ZCqKME2C` |
| Trigger | Webhook `POST`, path `plane`, raw body enabled |
| Action node | `Normalize and Publish` (`n8n-nodes-bloodbank.planeBloodbank`) |
| Broker | host NATS at `127.0.0.1:4222` |
| Identity registry | `~/.hermes/agents-registry.yaml` |

Both `33god` and `automaticai` Plane workspaces use this workflow. The latter is
only a workspace tenant slug on the same self-hosted personal Plane instance;
it is not an AutomaticAI company/service boundary or a second n8n system.

## Required node topology

```text
[Plane Webhook: raw HTTPS POST]
              │ exact bytes + headers
              ▼
[Normalize and Publish]
  1. extract payload.webhook_id
  2. select its op:// secret reference
  3. verify X-Plane-Signature over raw bytes
  4. resolve payload project/board through fleet registry
  5. normalize provider action to Bloodbank schema
  6. publish one deterministic event to NATS
              │
              ▼
[JSON acknowledgement]
```

Do not insert a Set, Code, JSON parse/stringify, or workspace-routing node ahead
of signature verification. The custom node owns the whole authenticated
normalization boundary because splitting those steps would make it easy to
verify different bytes from the ones eventually published.

## Secret contract

The node stores a JSON allowlist from Plane `webhook_id` to 1Password reference,
never raw values. Current references are recorded in
`bloodbank/docs/plane-event-normalization.md`. Runtime resolves only the matched
reference.

Selection by workspace is forbidden:

- workspace names are payload data, not credential identity;
- one workspace can have many webhooks;
- an attacker must not be able to choose a secret by editing an unsigned field;
- unknown webhook IDs must fail closed.

## Output contract

The node maps Plane provider activity onto provider-neutral facts:

| Provider provenance | Bloodbank type | Subject |
|---|---|---|
| `plane.board.created` | `bloodbank.repo.board.created` | `bloodbank.evt.repo.board.created` |
| `plane.ticket.created` | `bloodbank.repo.task.created` | `bloodbank.evt.repo.task.created` |
| `plane.ticket.updated` / `plane.ticket.transitioned` / `plane.ticket.deleted` | `bloodbank.repo.task.updated` | `bloodbank.evt.repo.task.updated` |
| `plane.ticket.commented` | `bloodbank.repo.task.appended` | `bloodbank.evt.repo.task.appended` |

`data.provider_event_type` preserves provenance. The raw provider entity is
preserved under the schema's ticket, board, or comment field. Board identity is
resolved from the shared fleet registry; never guess a repo from workspace
alone.

## Security semantics

- HTTPS/TLS encrypts the request in transit.
- HMAC authenticates integrity and possession of the webhook secret; it is not
  encryption.
- 1Password is the secret authority. Workflow JSON may contain `op://` references
  but never plaintext secret values.
- The deterministic event ID makes provider retries safe at NATS/Candystore.
- An HTTP 200 from n8n is not durable proof; query Candystore.

## Verification

1. Confirm one active workflow with the identity above.
2. Confirm every intended Plane webhook points to the HTTPS endpoint and carries
   all intended event flags.
3. Confirm Webhook `rawBody: true` and that the custom node is first downstream.
4. Test known ID + valid signature → one canonical event.
5. Test known ID + invalid signature → reject, no event.
6. Test unknown ID → reject, no secret resolution, no event.
7. Test a reserialized form of the same JSON → reject.
8. Query Candystore:

```bash
curl -fsS 'http://127.0.0.1:8683/events?producer=n8n-plane-webhook&limit=10'
```

Match workspace, board ID, repo, canonical type, provider provenance, and event
ID. Toaster/ntfy is a useful live observer, but only Candystore proves the
durable projection.

## Retired alternatives

- port-`8477` `plane-webhook-bridge` user service;
- a second workflow per workspace;
- a shared secret guessed from workspace;
- Bloodbank HTTP `/event` (RabbitMQ v2);
- direct Plane → NATS without raw-body HMAC verification.

The source for the retired bridge remains rollback material; its presence in Git
does not make it an active dependency.
