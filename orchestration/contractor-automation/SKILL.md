---
name: contractor-automation
description: Use for stateless cron or event-driven contractor jobs.
---

# Contractor Automation

Design and deliver bounded automation jobs that are triggered by a schedule, an event, or an operator command without turning every job into another long-lived agent.

A **contractor** is a versioned run contract. It borrows an existing execution carrier, receives explicit inputs and authority, produces a receipt, and ends. It does not own an inbox, personality, profile, memory bank, or durable conversation.

## Use this skill when

- a scheduled job should inspect state and advance work;
- a webhook or event should trigger an agentic task;
- several narrow lifecycle reactions need a common execution contract;
- the system already has project, board, agent, or service registries that must remain authoritative;
- an autonomous loop needs idempotency, WIP limits, leases, compensation, and audit evidence.

Do not use it for a genuinely conversational agent, a stateful service, a simple deterministic script that needs no reasoning, or a one-off foreground task.

## Core model

Keep four identities separate:

1. **Contract** — what may run: id, version, trigger, inputs, limits, effects, receipt.
2. **Carrier** — the existing agent/profile/service that supplies runtime and credentials.
3. **Work item** — the ticket, event, repository, or entity being acted on.
4. **Invocation** — one attributable attempt with correlation, causation, and idempotency keys.

The carrier remains the security and audit actor. The invocation also records contractor id/version. Do not create one profile per contractor merely to give the job a name.

## Trigger selection

| Need | Trigger |
| --- | --- |
| React to a created/updated entity | Event |
| React to a lifecycle transition | Event, filtered by normalized previous/current phase |
| Periodically select from a pool | Cron |
| Long implementation/review | Durable command dispatched by a short control pass |
| Cheap deterministic health check | Script-only scheduler job, not an LLM contractor |

Prefer events for known changes. Use cron for selection, reconciliation, or missed-event recovery—not as a euphemism for polling everything because the event path was never finished.

## Control pass versus worker

A bounded scheduler run is the **control plane**:

1. reload live truth;
2. acquire the shared lease/WIP slot;
3. select at most the configured amount of work;
4. issue an idempotent durable command;
5. wait only for dispatch acceptance;
6. record a machine-readable receipt;
7. exit.

The durable invocation is the **worker plane**. It may implement, test, review, or wait on external systems. Do not make a short cron run babysit an hour-long worker. Do not use in-process delegation when the parent ending would discard the child.

## Minimum contract

Every contractor manifest must declare:

- stable `contractor_id` and integer version;
- owner and execution carrier selector;
- exactly one trigger;
- immutable input schema;
- memory/continuity policy;
- wall-clock and item-count budgets;
- effect allowlist, denied by default;
- lease/concurrency/WIP policy;
- deterministic idempotency key recipe;
- retry and compensation behavior;
- receipt schema and terminal outcomes;
- required skills/toolsets and workdir resolution;
- audit event/correlation requirements.

Recommended terminal outcomes: `idle`, `busy`, `dispatched`, `completed`, `blocked`, and `failed`. Prose such as “looks good” is not a receipt.

## Event-driven boundaries

- Events are immutable facts; commands are targeted intent.
- A provider write that already emits a canonical fact must not be followed by a hand-published duplicate of that fact.
- Semantic decisions may produce a separate derived fact when it means something the provider update alone cannot prove.
- Workflow engines should validate, filter, resolve a route, and publish. Keep model reasoning and business policy out of click-only workflow nodes.
- Resolve targets from the canonical registry on each run. A running gateway is not proof that a target is eligible.
- Preserve correlation and causation from trigger event through command, invocation lifecycle, effects, and receipt.

## Source-of-truth rule

Assign one owner for each concern before writing code:

- project/entity identity and enablement;
- business/lifecycle policy;
- contractor behavior;
- runtime provisioning;
- transport schemas;
- workflow routing;
- provider mutation;
- audit projection.

Do not copy prompts, provider IDs, credentials, or scheduler job IDs into project manifests. Project configuration should select a versioned contract and contain only project overrides. Generated runtime IDs stay in ignored runtime state.

## Build workflow

### 1. Establish live truth

Inspect the canonical project manifest, registry projection, provider state, existing scheduler jobs, active workers/leases, transport schemas, workflow exports, and service route eligibility. Treat prose as a claim until code and runtime agree.

### 2. Write the contract before the prompt

Specify trigger, inputs, effects, budgets, idempotency, compensation, and receipt. The prompt should name the contract and work item; behavior lives in the versioned skill/manifest.

### 3. Prove the dispatch primitive

Before implementing business behavior, prove a minimal command can:

- be schema-validated;
- resolve one eligible carrier;
- survive redelivery without duplicate execution;
- start a fresh non-continuing invocation;
- preserve project rules while obeying the declared memory policy;
- emit started/completed/failed lifecycle evidence.

### 4. Deliver one vertical tracer bullet

Use a real provider-generated fixture, not a hand-written fantasy payload. Run the path from trigger through router, bus, carrier, provider effect, and durable projection. Test one behavior end to end before adding more contracts.

### 5. Provision declaratively

Add plan/apply/status/disable operations to the existing project provisioner. Reconcile scheduler jobs by stable logical name through the scheduler’s supported API. A second apply must produce no diff. Refuse configurations that enable two autonomous drivers for the same pool.

### 6. Roll out by blast radius

Pilot on an internal/sandbox project, inject gateway and provider failures, replay messages, and verify compensation. Migrate existing projects disabled by default; activate them one at a time after project policy and credentials pass.

## Board automation rules

When contractors operate a work board:

- priority belongs in the provider’s priority field;
- component belongs in a module/component field;
- iteration belongs in a cycle/milestone field;
- start date is set on first entry to active work, not ticket creation;
- assignee remains empty while an item is in a pull-based pool;
- labels carry semantic type/cross-cutting concerns, not duplicates of priority, state, cycle, or module;
- absence of an eligible cycle is valid—leave it blank;
- a thin ticket is refined before it becomes implementation-ready;
- QA/review uses a carrier independent from the implementer;
- “Done” is accepted only from evidence, never from a column change alone.

Model each lifecycle reaction narrowly: ticket fortification, work start, QA entry, QA rejection, and completion validation are different contracts even when one router dispatches them.

Do not add a periodic whole-board drift job until concrete missed-event evidence justifies it. Event reactions plus a bounded selection pass are the simpler default.

## TDD and verification

For each vertical slice:

1. write one failing behavior test;
2. run it and confirm the expected failure;
3. implement the minimum path;
4. run the focused and full affected suites;
5. inject duplicate, out-of-order, route-disabled, gateway-down, and partial-effect failures;
6. use a separate adversarial reviewer;
7. cross the real external boundary before calling it complete.

Verification must prove:

- at most the allowed work items were affected;
- retries converge without duplicate comments, commands, or mutations;
- lease/WIP prevents a second worker;
- a failed dispatch does not leave a false active claim;
- memory/continuity policy is enforced;
- provider effects and semantic events remain distinct;
- lifecycle evidence reaches the durable projection;
- declarative apply converges on its second run.

## Pitfalls

- **Agent proliferation:** naming a job by creating a profile, bot, and memory bank.
- **Cron theater:** attempting long implementation inside a short scheduler budget.
- **Split brain:** old heartbeat and new contractor both selecting work.
- **Workflow intelligence:** burying policy in an unversioned workflow canvas.
- **Registry forks:** hardcoded project-to-agent switch tables.
- **Label soup:** encoding fields the board already models natively.
- **Fake idempotency:** deduplicating only the command while effects can repeat.
- **Unsafe completion:** emitting “completed” because the provider state says Done.
- **Mock-bound proof:** tests pass but the actual webhook, broker, auth boundary, or provider was never crossed.

## 33GOD specialization

For the 33GOD board/Plane/Bloodbank/Hermes/Pjangler pattern, load [references/33god-board-contractors.md](references/33god-board-contractors.md). Treat it as architecture guidance and a discovery checklist; verify the live fleet before any mutation.

## Related skills

- `event-driven-architecture` — broker, saga, outbox, DLQ, and consumer patterns. This overlaps at the transport layer; Contractor Automation owns ephemeral agentic run contracts and scheduler/worker separation.
- `bloodbank-integration` — canonical Bloodbank schema and command/event journeys.
- `momo` — project-manager orchestration and board-clearing policy.
- `project-lifecycle` / `task-triage` — provider operations and ticket refinement.
- `pjangler` / `33god-projects` — declarative project/runtime provisioning.
- `test-driven-development` — required RED/GREEN discipline.
