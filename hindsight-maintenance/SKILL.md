---
name: hindsight-maintenance
description: |
  Keep the self-hosted Hindsight memory system healthy across all banks on a schedule. Runs three families of upkeep workflows — tune-up (system health: reap orphaned/stuck async jobs, repair missing public.* maintenance functions, clear failed operations, flag per-bank anomalies), optimization (prune stale/low-value memories, trigger consolidation, cross-bank pollination, novel synthesis of emergent insights), and karpathy-wiki (nightly compile of newly-retained memories into a Karpathy LLM wiki). Use when scheduling or running Hindsight memory upkeep — "nightly/weekly memory maintenance", "prune memory", "consolidate banks", "memory wiki", "hindsight health check", "dead/stuck jobs", "reap orphans", "queue is stuck", "cross-bank synthesis", or wiring cron/systemd timers for memory maintenance. Do NOT use for one-off recall/retain during normal work (use the hindsight skill), for infra-level debugging of the Hindsight container/host (use server-maintenance), or for non-Hindsight datastores.
pipeline-status: new
---

# Hindsight Maintenance

Keep the self-hosted Hindsight memory system healthy across every bank on a schedule. The
expensive, dangerous, and repetitive parts — bank enumeration, the health sweep, the
orphaned-job reaper, the new-memory watermark — are pre-paid in `scripts/`. Spend agent
judgment only on the creative optimization passes (pollination, synthesis, prune review),
never on re-deriving the CLI or SQL surface.

Endpoint `https://api.hs.delo.sh`. The database is host-native Postgres at `127.0.0.1:5432`,
database `hindsight`, **schema `hindsight` (not `public`)** — this custom schema is the root
of two upstream bugs the tune-up workflow guards against. Stack and DB repair SQL live in
`~/docker/stacks/ai/hindsight/` (`compose.yml`, `.env`, `fixes/`).

## Operating Principles

- **Read the evidence before touching anything.** Every workflow opens with `scripts/tune-up.sh`
  output or a `hindsight memory recall`, never ad-hoc `psql`/`docker logs` spelunking.
- **Destructive ops are dry-run first, user-gated second.** `memory delete`, `clear-observations`,
  and pruning are irreversible; memories are expensive to rebuild. Show the candidate set, get a
  decision, then act.
- **One bank's failure never aborts the sweep.** Iterate all banks, collect errors, keep going.
- **Never hand-roll a cross-worker DB write.** Reaping stale jobs is subtle — always use
  `scripts/reap-orphans.sh`, never a hand-written `UPDATE` (see Cross-cutting rules for why).
- **Watermarks gate "new since last run."** State lives in `~/.hindsight/maintenance/`, advanced
  only after the consuming step (wiki compile) succeeds — a crash re-processes, never skips.

## Bank enumeration (every workflow's first move)

`SKILL_DIR` is the base directory stated when this skill loaded. Set it once per shell (the
fallback below is correct on this host) so every `"$SKILL_DIR/…"` command in the references resolves:

```bash
export SKILL_DIR="${SKILL_DIR:-$HOME/.claude/skills/hindsight-maintenance}"
source "$SKILL_DIR/scripts/hs-lib.sh"   # HS_STACK_DIR, hs_db, hs_banks, hs_live_worker
hs_banks            # every bank_id, one per line (≈141)
```

## Cadence → workflow

| Cadence | Run | References |
|---|---|---|
| **nightly** | `tune-up` (detect + reap) → `karpathy-wiki` of new memories → consolidate active banks | tune-up, karpathy-wiki |
| **weekly** | `optimization`: prune review → cross-bank pollination → novel synthesis | optimization |
| **reactive** | stuck queue or post-`--force-recreate` → reap orphans; on demand → any single workflow | tune-up, scheduling |

## Intent → reference

| You want to… | Read |
|---|---|
| Health check, dead/stuck jobs, failed ops, missing functions | [references/tune-up.md](./references/tune-up.md) |
| Prune, consolidate, cross-bank pollinate, synthesize novel insight | [references/optimization.md](./references/optimization.md) |
| Nightly wiki of newly-retained memories | [references/karpathy-wiki.md](./references/karpathy-wiki.md) |
| Wire nightly/weekly/reactive schedules (systemd/cron) | [references/scheduling.md](./references/scheduling.md) |
| Exact CLI flags + maintenance SQL | [references/cli-and-sql.md](./references/cli-and-sql.md) |

## Workflow families (quick pointers; open the reference before running)

- **tune-up** — `scripts/tune-up.sh` writes a read-only health report: global queue state,
  orphaned jobs (dead-worker claims), missing `public.banks_needing_consolidation()` /
  `public.schemas_with_expired_rows()`, failed ops, and per-bank anomalies. Reap with
  `scripts/reap-orphans.sh --apply`; repair missing functions from `~/docker/stacks/ai/hindsight/fixes/`.

- **optimization** — four passes, most-destructive last:
  *consolidate* (`hindsight bank consolidate <bank>` — synthesize observations),
  *prune* (low `access_count` + age + duplicate heuristics → `memory delete`, dry-run→gate),
  *cross-bank pollination* (a theme learned in one bank surfaced into sibling banks it also serves),
  *novel synthesis* (`reflect` over memory combinations, retain emergent observations no single memory held).

- **karpathy-wiki** — `scripts/new-memories.sh <bank>` pulls memories retained since the watermark;
  hand them to the `karpathy-llm-wiki` skill's Ingest; advance the watermark on success.

## Cross-cutting rules

- **Schema is `hindsight`.** All SQL is schema-qualified (`hindsight.async_operations`,
  `hindsight.memory_units`). Maintenance *functions* live in `public.*` and are shared across
  schemas — a fresh DB or image upgrade can leave them missing; tune-up checks this every run.
- **Reaping requires the live worker to be up.** Run the container, let it claim its work, *then*
  reap — the reaper protects `worker_id = <live hostname>` claims. Reaping against a stopped
  container is unsafe.
- **Consolidation is a queued async job**, not synchronous. `hindsight bank consolidate <bank>`
  enqueues; use `--wait` to block, or check `hindsight operation list <bank>`.
- **Attribute retained memories.** Synthesis/pollination writes go back with
  `--context conventions|architecture` and a `--doc-id` so re-runs upsert instead of duplicating.
- **Persist findings.** Non-trivial maintenance outcomes get `hindsight memory retain infra …`
  (the homelab bank) so the next sweep starts informed.

## Out of Scope

- **One-off recall/retain during normal task work** → use the **hindsight** skill. This skill is
  scheduled/bulk upkeep, not the day-to-day memory API.
- **Infra-level failure of the Hindsight container or host** (crash loops, OOM, disk, Traefik,
  the container won't start) → use the **server-maintenance** skill. This skill assumes the
  service is up and reachable.
- **Debugging Hindsight application source / migrations** → that is upstream code work in the
  `vectorize-io/hindsight` image, not memory upkeep. tune-up only *detects and works around* those
  bugs (missing functions, orphaned jobs); it does not patch the image.
- **Any non-Hindsight datastore** (Postgres for other stacks, Qdrant, Redis) → not this skill.
