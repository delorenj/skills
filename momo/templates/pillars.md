# Pillars — <PROJECT NAME>

> Per-repo decision compass for Momo (and any human/agent making calls here).
> Momo cites these by **slug** in every Bloodbank decision event (`data.basis`).
> Universal pillars (how Momo works) live in the `momo` skill; these are what
> THIS project is *for*. Keep 5–9, each decidable, each with a stable kebab-case slug.
> Delete the guidance lines once you've filled it in.

## Monetary / strategic

- **`<slug>`** — <the money/strategy compass, e.g. "ship the audit-trail MVP before
  gold-plating ingestion; every hour spent must move a user-visible capability">
- **`<slug>`** — <…>

## Moral / quality standards (lines never crossed)

- **`<slug>`** — <e.g. "never lose an event: persist before acknowledging, always">
- **`<slug>`** — <…>

## Architectural compass

- **`<slug>`** — <e.g. "Bloodbank is the only inter-service channel; no direct calls">
- **`<slug>`** — <e.g. "Holyfields JSON Schema is the single source of truth; never
  hand-edit generated Pydantic/Zod">
- **`<slug>`** — <…>

## Taste / product

- **`<slug>`** — <e.g. "prefer boring, observable, reversible over clever">

---

### How this file is used

- Momo loads it during preflight. When it makes a judgment call, it weighs these pillars,
  picks the one(s) that decide it, and records:
  `record-decision.py --decision "…" --basis "<slug>" --reasoning "…"`.
- If a per-repo product/scope pillar conflicts with a universal *process* pillar, the
  product pillar wins — EXCEPT the safety pillars (no-code-mutation, reviewer-independence,
  evidence, respect-the-contracts), which are never overridden by a project goal.
