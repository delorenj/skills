# Event + Command Contract Lifecycle

Use this when adding, changing, deprecating, or pruning Bloodbank contracts.

## Trigger phrases

- "add a new event"
- "add a command"
- "schema drift"
- "deprecate/remove old events"
- "new workflow observability event"

## Core distinctions (non-negotiable)

- **Event** = immutable fact (`X happened`).
- **Command** = mutable request (`please do X`).
- **Schema-first always**: Holyfields defines contracts before producer/consumer code.

## Naming conventions

- Events: `domain.entity.action` (past-tense action preferred)
  - e.g. `artifact.audio_file.detected`
- Commands (routing): `command.{agent}.{action}`
  - envelope schema remains `command/envelope.v1.json`

## End-to-end workflow (generic)

### 0) Classify the contract change

Pick one:
1. **New contract** (add schema + wiring)
2. **Schema evolution** (compatible update)
3. **Breaking change** (new `.v2` contract + migration)
4. **Deprecation/prune** (remove unvetted contract)

If ambiguous, pause and ask for explicit owner approval (usually Grolf for cross-domain impact).

---

### 1) Contract proposal (small but explicit)

Capture these fields before coding:
- Contract type: Event or Command
- Name / routing key
- Producer(s)
- Consumer(s)
- Required payload fields
- Correlation semantics (`correlation_ids` / `command_id`)
- Success and failure outcomes

---

### 2) Holyfields schema authoring

Create or update schema in:
- `~/code/33GOD/holyfields/schemas/...`

Rules:
- Extend `_common/base_event.v1.json` for envelope fields.
- Set `properties.event_type.const` when applicable.
- Keep required fields minimal and real.
- For breaking changes, create a new versioned schema instead of mutating in place.

---

### 3) Generate bindings + drift checks

In Holyfields repo:
- Run generator tasks (project-standard command path)
- Run drift checks
- Confirm generated Python/TS artifacts are updated

Gate:
- No unresolved drift allowed before producer/consumer edits proceed.

---

### 4) Producer integration

Wire producer(s):
- Use generated/compat models where available.
- Build valid envelope (`event_id`, `event_type`, `timestamp`, `version`, `source`, `correlation_ids`, `payload`).
- Ensure `source` is object-shaped (not a string).

For commands:
- Ensure payload includes `command_id`, `target_agent`, `action`, `command_payload`.
- Route as `command.{agent}.{action}`.

---

### 5) Consumer integration

- Bind queue/routing for the new contract.
- Implement happy-path + failure-path handlers.
- Emit result/failure events where required.
- Verify idempotency/TTL behavior for command flows.

---

### 6) Observability + Test Board integration

Holocene must be updated in the same change set:
- Add contract to vetted list (if approved for active use).
- Ensure Test Board default payload generation works.
- Verify journey states in real flow:
  1. Creating Event
  2. Event Created
  3. Posting to RabbitMQ
  4. In Queue (seconds)
  5. Consumed / Timed Out

---

### 7) Verification checklist (required)

- [ ] Publish test payload succeeds (HTTP/API).
- [ ] Event visible on WS stream.
- [ ] Event persists in Candystore.
- [ ] Consumer ack/result behavior verified.
- [ ] Holocene Test Board path verified.
- [ ] GOD docs updated if architecture/ownership changed.

Attach evidence (command outputs or screenshots).

---

### 8) Deprecation/prune protocol

If removing contracts:
1. Confirm not in active producer/consumer paths.
2. Remove schema from Holyfields.
3. Regenerate bindings and resolve drift.
4. Remove from Test Board vetted list.
5. Keep change ticketed and documented.

Git preserves history; do not keep dead contracts in active registry solely for nostalgia.

## Minimal execution artifact set

For every contract change, output:
1. Contract summary (1–2 paragraphs)
2. Files changed (schema + producer + consumer + observability)
3. Verification evidence
4. Rollback note (if breaking)
