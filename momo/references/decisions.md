# Decisions as Bloodbank events

There is no built-in hook that fires when an agent makes a decision, so Momo fires one
itself. Every consequential judgment call becomes a canonical Bloodbank **decision event**
carrying the decision, the **pillars it rests on**, and the reasoning. This is what makes
Momo's autonomy auditable — the operator (and Hermes, and dashboards) can query *why* Momo
did what it did.

Plane ticket lifecycle facts are already emitted by the signed Plane → n8n →
Bloodbank ingress. Do not append or publish a second task-created/updated/appended
event after board CRUD. This file covers the additional judgment fact only.

## The mechanism

```bash
python3 <skill_dir>/scripts/record-decision.py \
  --decision "<one-line decision>" \
  --basis "<pillar-slug>" [--basis "<pillar-slug>" ...] \
  --reasoning "<why: the tradeoff, what you rejected>" \
  [--issue <TICKET-KEY>] [--actor momo] [--dry-run] [--local-only]
```

The script (repo-agnostic; resolves the slug from `.project.json`):

1. **Always** appends the full CloudEvents envelope to the durable local trail
   `<repo>/_bmad-output/implementation-artifacts/bloodbank-events.jsonl` — the same spool
   the Hermes sentinel reads. A decision is never lost even if the bus is down.
2. **Best-effort** publishes to the live Bloodbank bus (NATS v3) on subject
   `bloodbank.evt.repo.decision.recorded` via bloodbank's stdlib publisher. If NATS is
   unreachable it warns and exits 3 (decision safe in the trail; bus is behind) — it does
   not fail the decision.

Use `--dry-run` to inspect the envelope without emitting; `--local-only` when the bus is
knowingly offline.

## The contract (get this exactly right)

- **CloudEvents `type` = `bloodbank.repo.decision.recorded`** — exactly 4 dotted tokens.
  The version token was removed from the contract; `bloodbank.v1.repo.decision.recorded` is
  now REJECTED outright by `bb-emit`. The repo slug goes in **`data.repo`**, NEVER in the
  type. The 5-token form `bloodbank.repo.<repo>.decision.recorded` is INVALID — it fails the
  contract regex and the entity allowlist and will be rejected by the bus validator.
- **NATS subject** = the type with the `evt` kind-marker inserted:
  `bloodbank.evt.repo.decision.recorded`. The script derives both from one constant, so
  they can never drift.
- **`data`** (schema: repo + decision required; `additionalProperties: true`):
  - `repo` — the project slug.
  - `decision` — the one-line statement.
  - `basis` — **array of pillar slugs** (the schema-blessed home for what the decision rests
    on). Prefer stable slugs from `references/pillars.md` and `<repo>/.momo/pillars.md`.
  - `reasoning` — prose why.
  - `decided_by` (=`momo`), `decided_at`, optional `issue`, `artifacts_root`.
- **Envelope** is a full CloudEvent (`kind=event`, `domain=repo`, `actor.agent_id=momo`,
  `ordering_key=repo:<slug>`, `producer=agent:momo`, `service=<slug>`) — so it validates
  against the existing schema at `bloodbank/schemas/bloodbank/repo/decision.recorded.json`.
  No schema-tree change is needed; the type already exists and validates.

## When to record (mandatory)

- Pulling a **To Do** (or Backlog) ticket into active work on your own judgment.
- **Accepting** or **holding** a review-lane ticket.
- **Cutting scope** / deferring an AC to unblock a dependent.
- Choosing an **approach or architecture** among alternatives.
- **Stopping** the board-clearing loop (name the stop condition).
- **Rolling back** a review-accepted ticket a dependent proved broken.
- A **board_id / binding self-heal** (shared-state change Hermes will read).

Trivial, obvious, or purely mechanical steps do **not** need an event — reserve the trail
for calls where knowing the *why* later has value.

## Verify a live event landed

The `event-toaster` subscribes `bloodbank.evt.>` and forwards to `ntfy.delo.sh/bloodbank`:

```bash
docker logs bloodbank-event-toaster --tail 5
curl -s 'https://ntfy.delo.sh/bloodbank/json?poll=1&since=120s'
```

## Note on the sentinel scripts

The sentinel scripts (`issue-autonomous-review.sh`, close gate) publish nothing. They used
to mint a repo-lane `…issue.*` family via the local `emit-event.py`; it was never consumed
and its shape was invalid (repo slug inside the type, `issue` outside the §7 entity
allowlist), so it was deleted on 2026-08-28. Their verdict is the exit code, the review
report, the issue evidence file, and the ticket comment.

`record-decision.py` is therefore the only publisher on this path: use it for the *judgment*
decisions worth a durable record. Do not hand-roll a replacement family for the scripts.
