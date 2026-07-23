---
pipeline-status: new
---
# optimization — compound the memory, don't just store it

Read for the weekly quality pass. Four passes, ordered least→most destructive. Run consolidate and
pollination freely; **prune and any `delete`/`clear-observations` are dry-run → user-gated.**

Scope first: 141 banks is too many to reflect over nightly. Pick the working set — banks with the
largest unconsolidated backlog (tune-up section 6) plus banks touched this week
(`hs_db "SELECT bank_id FROM hindsight.memory_units WHERE created_at > now()-interval '7 days' GROUP BY 1"`).

## 1. Consolidate (safe, enqueues async work)

Turn raw `experience`/`world` facts into durable `observation`s via the built-in engine.

```bash
# Working set = banks touched this week OR with a real backlog (tune-up section 6). Bind it, then loop.
WORKING_SET=$(hs_db "SELECT bank_id FROM ${HS_SCHEMA}.memory_units
                     WHERE created_at > now()-interval '7 days' GROUP BY 1")
for b in $WORKING_SET; do hindsight bank consolidate "$b"; done   # enqueues one job per bank
```

These run on the worker queue — watch with `scripts/tune-up.sh` or `hindsight operation list <bank>`.
Use `--wait` only for a single foreground bank. If many banks show `consolidation_failed_at`, the LLM
provider is failing (see tune-up); fix that before re-consolidating.

## 2. Prune (DESTRUCTIVE — dry-run, then gate)

Target low-value memories: never recalled, old, not observations, or near-duplicates.

```bash
# Dry-run candidate set for one bank (never-recalled + >90d + not an observation)
hs_db_table "SELECT id, created_at, access_count, left(text,80)
             FROM hindsight.memory_units
             WHERE bank_id='<bank>' AND access_count=0
               AND created_at < now()-interval '90 days' AND fact_type<>'observation'
             ORDER BY created_at ASC LIMIT 50;"
```

Review the set. Present counts + a sample to the user, get an explicit go, then:
`hindsight memory delete <bank> <unit_id>` per approved id. Never bulk-delete unseen. Prefer raising
the age/`access_count` bar over deleting borderline facts — recall is cheap, regret is not.

Near-duplicate detection is a judgment call: recall a memory's own text against its bank
(`hindsight memory recall <bank> "<text>" -b low`) and if several near-identical facts come back,
keep the richest, delete the rest — again gated.

## 3. Cross-bank pollination (additive, no deletes)

A fact learned in one bank often serves siblings. Example: an `infra` fix about the Cloudflare tunnel
is relevant to every stack behind it.

1. For a source bank, pull its recent high-signal facts (`fact_type IN ('observation','world')`).
2. For each, pick candidate sibling banks (related project/domain) and recall the fact's theme there:
   `hindsight memory recall <sibling> "<theme>" -b mid`.
3. If the sibling clearly lacks it, retain a bridged copy — attributed and idempotent:
   ```bash
   hindsight memory retain <sibling> "<fact> (cross-bank from <source>)" \
     --context conventions --doc-id "pollinate-<source>-<short-hash>"
   ```
The `--doc-id` makes re-runs upsert, so weekly pollination never duplicates. Only pollinate facts that
are genuinely portable (conventions, infra, tooling) — not project-specific detail.

## 4. Novel synthesis (additive — the emergent-idea pass)

The point of memory is compounding: insights that exist in no single memory but fall out of combining
several. Use `reflect` (agentic, applies bank identity) with a synthesis prompt:

```bash
hindsight memory reflect <bank> \
  "Across everything retained here, what patterns, contradictions, or decisions emerge that no single
   memory states outright? List only genuinely new syntheses, each grounded in specific facts." \
  -b high --include-facts
```

Judge each candidate: is it actually new, and grounded in cited facts? Discard restated singles.
Retain survivors as observations, attributed and idempotent:

```bash
hindsight memory retain <bank> "<synthesized insight>" \
  --context architecture --doc-id "synth-<bank>-<yyyymmww>"
```

Cross-bank synthesis is the ambitious version: `reflect` over a source bank, then test whether the
insight reframes a *different* bank, and retain it there. Rare but high-value — keep the bar high.

## Guardrails

- **Every write is attributed and idempotent** (`--context`, `--doc-id`) so the weekly run converges
  instead of inflating the store.
- **Deletes are always gated.** No exceptions, no "obvious" bulk deletes.
- **Log the pass**: `hindsight memory retain infra "weekly optimization <date>: <banks touched>, <n> pruned, <n> synthesized" --context session-summary`.
