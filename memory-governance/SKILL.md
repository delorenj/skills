---
name: memory-governance
description: Govern OpenClaw memory architecture, cadence, and promotion workflows. Use when configuring or debugging heartbeat vs cron responsibilities, enabling/tuning QMD memory backend, designing memory-writing policy (daily logs vs MEMORY.md), implementing nightly dream-cycle compaction/promotion, or creating deterministic memory templates/scripts.
---

# Memory Governance

Standardize memory behavior so recall stays reliable and operational noise stays out of long-term memory.

## Workflow

1. **Audit runtime cadence + memory backend**
2. **Normalize ownership of clocks** (heartbeat vs cron vs QMD timer)
3. **Apply memory write policy** (daily logs vs long-term memory)
4. **Run deterministic compaction/promotion artifacts**

For conceptual model details, read `references/operating-model.md`.

## 1) Audit first (deterministic)

Run:

```bash
python scripts/cadence_audit.py --output memory/cadence-audit-latest.md
```

Interpretation rules:
- Heartbeat must own triage/dispatch loops.
- Cron must own exact-time scheduling only.
- QMD update timer is independent and should not be conflated with heartbeat/cron.

## 2) Canonical clock ownership

Apply these invariants:
- **Heartbeat:** ongoing agent triage/dispatch
- **Cron:** exact-time reminders / isolated scheduled work
- **QMD update interval:** index freshness only

If cron jobs duplicate heartbeat behavior, remove/disable them.

## 3) Memory writing policy

Use this split consistently:
- `memory/YYYY-MM-DD.md` for raw daily execution context.
- `MEMORY.md` for curated durable context only.

Promote to `MEMORY.md` only when likely useful beyond the current week.

## 4) Deterministic scripts

### A) Compaction artifact template

Generates canonical checkpoint file with required 5 sections.

```bash
python scripts/compaction_checkpoint.py \
  --output memory/context-compaction-latest.md \
  --active-task "<task>" \
  --decision "<decision>" \
  --blocker "<blocker>" \
  --next-action "<action-1>" \
  --next-action "<action-2>" \
  --next-action "<action-3>" \
  --handoff "<critical link/file>"
```

### B) Promotion review scaffold

Scans recent daily logs and generates a candidate checklist for durable memory promotion.

```bash
python scripts/promotion_review.py --memory-dir memory --days 2
```

Writes: `memory/promotion-review-YYYY-MM-DD.md`

### C) Cadence audit report

```bash
python scripts/cadence_audit.py --config ~/.openclaw/openclaw.json --cron ~/.openclaw/cron/jobs.json
```

## Operating rules

- Prefer deterministic scripts for repeatable memory operations.
- Keep policy concise and centralized (single canonical policy file).
- Do not store secrets in memory markdown.
- Nightly dream cycle should own compaction + promotion hygiene.
