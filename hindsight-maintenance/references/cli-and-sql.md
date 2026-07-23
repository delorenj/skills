---
pipeline-status: new
---
# CLI & SQL reference

The verified command and query surface the maintenance workflows call. Read this when you need
an exact flag or a hand-written query; the workflow references assume it.

## Connection facts

- CLI: `hindsight` (config `~/.hindsight/config` → `api_url=https://api.hs.delo.sh`, `api_key`).
- DB: host-native Postgres `127.0.0.1:5432`, database `hindsight`, **schema `hindsight`**.
  Creds in `~/docker/stacks/ai/hindsight/.env` (`HINDSIGHT_DB_USER/PASSWORD/NAME`).
- `scripts/hs-lib.sh` wraps all of this: `hs_db "SQL"`, `hs_db_table "SQL"`, `hs_banks`, `hs_live_worker`.
- Maintenance *functions* (`banks_needing_consolidation`, `schemas_with_expired_rows`) live in
  `public.*`, shared across schemas — see the two bugs below.

## Hindsight CLI (verified flags)

Add `-o json` to any command for machine-readable output.

```bash
# Banks
hindsight bank list                         # all banks -> [{bank_id,name,mission,disposition,...}]
hindsight bank stats <bank>                 # {total_nodes,total_links,total_documents,
                                            #  nodes_by_fact_type{world,experience,observation},
                                            #  pending_operations,failed_operations}
hindsight bank disposition <bank>           # profile + disposition traits
hindsight bank graph <bank> [-t <fact>] [-l <n>]
hindsight bank consolidate <bank> [--wait] [--poll-interval <s>]   # ENQUEUES an async job
hindsight bank clear-observations <bank>    # DESTRUCTIVE: drop all observations for a bank
hindsight bank config <bank>                # effective hierarchical config
hindsight bank set-config <bank> [--retain-mission ..] [--observations-mission ..]
                                            # [--reflect-mission ..] [--disposition-skepticism 1-5] ...

# Memories
hindsight memory list <bank> [-t <fact>] [-q <text>] [-l <limit>] [-s <offset>]
hindsight memory recall <bank> "<query>" [-b low|mid|high] [--tags a,b] [--max-tokens N]
hindsight memory reflect <bank> "<query>" [-b mid] [-c <context>] [--include-facts] [-s schema.json]
hindsight memory retain <bank> "<text>" --context <cat> [--doc-id <id>]
hindsight memory retain-files <bank> <path> [-r] [-c <context>] [--async]
hindsight memory delete <bank> <unit_id>    # DESTRUCTIVE, irreversible

# Async operations
hindsight operation list <bank>             # queue for one bank
hindsight operation get <bank> <op_id>
hindsight operation cancel <bank> <op_id>   # cancel a PENDING op

# Curated layers
hindsight mental-model list|get|create|update|delete|refresh|history <bank> [<id>]
hindsight directive list|get|create|update|delete <bank> [<id>]
```

Context categories: `architecture, conventions, debugging, deployment, dependencies,
preferences, session-summary, code-edit`. Fact types: `world, experience, opinion`
(stored `observation` is the consolidated type).

## Maintenance SQL (schema = `hindsight`)

```sql
-- Global queue snapshot
SELECT operation_type, status, count(*) FROM hindsight.async_operations
WHERE status IN ('pending','processing') GROUP BY 1,2 ORDER BY 1,2;

-- New memories since a watermark (the wiki feed)
SELECT id, created_at, fact_type, context, text FROM hindsight.memory_units
WHERE bank_id = :bank AND created_at > :since ORDER BY created_at ASC;

-- Prune candidates: never-recalled, old, not an observation
SELECT id, bank_id, created_at, access_count, left(text,80) FROM hindsight.memory_units
WHERE bank_id = :bank AND access_count = 0
  AND created_at < now() - interval '90 days'
  AND fact_type <> 'observation' ORDER BY created_at ASC;

-- Unconsolidated backlog per bank
SELECT bank_id, count(*) FROM hindsight.memory_units
WHERE consolidated_at IS NULL AND consolidation_failed_at IS NULL
  AND fact_type IN ('experience','world') GROUP BY 1 ORDER BY 2 DESC;
```

`memory_units` columns of interest: `id, bank_id, document_id, text, context, fact_type,
access_count, created_at, updated_at, tags[], consolidated_at, consolidation_failed_at,
source_memory_ids[], event_date`.

## Two upstream bugs this skill works around

Both are triggered by our non-`public` schema and are **detected by `scripts/tune-up.sh`**; the
repairs are checked into `~/docker/stacks/ai/hindsight/fixes/` (see that dir's `README.md`).

1. **Missing `public.*` maintenance functions** (issue #2056). Migrations `e5f6a7b8c9d0` and repair
   `b2d4f6a8c1e3` only create the shared routines when alembic `target_schema` is empty or `public`;
   we run schema `hindsight`, so they stamp as applied but create nothing. Repair:
   `fixes/01-public-maintenance-routines.sql` (idempotent — re-run after any DB rebuild or image upgrade).
   Detect: `SELECT to_regprocedure('public.banks_needing_consolidation()') IS NOT NULL;`

2. **Jobs orphaned on container recreate.** `recover_own_tasks()` only recovers `worker_id = <self>`,
   and `worker_id` is the container hostname → no cross-worker reaper. Repair:
   `fixes/02-reap-orphaned-jobs.sql` / `scripts/reap-orphans.sh --apply` (live container required).
