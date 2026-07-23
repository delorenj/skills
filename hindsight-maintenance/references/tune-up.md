---
pipeline-status: new
---
# tune-up — "check the brakes"

Read before any health/cleanup run (nightly first step, or reactively when the queue looks stuck).
Goal: prove the system is healthy or produce a ranked list of what to fix. Read-only until you reap.

## Procedure

1. **Sweep (read-only).**
   ```bash
   REPORT=$("$SKILL_DIR/scripts/tune-up.sh")   # writes ~/.hindsight/maintenance/tune-up-<ts>.md
   cat "$REPORT"
   ```
   The report has seven sections: container status, queue, orphaned jobs, missing functions,
   failed ops, per-bank unconsolidated backlog, recent container warnings.

2. **Triage against these expectations.** Anything off-baseline is an anomaly:

   | Section | Healthy | Anomaly → action |
   |---|---|---|
   | Container | `Up … (healthy)` | not healthy → **stop, hand to server-maintenance skill** |
   | Queue | small, draining | large/growing `pending` with idle worker → check orphans (below) |
   | Orphaned jobs | `(0 rows)` | any rows → **reap** (step 3) |
   | Missing functions | `t | t` | any `f` → **repair** (step 4) |
   | Failed ops (7d) | `(0 rows)` or a few LLM blips | a spike of one type → inspect `error_message`, likely LLM-provider flakiness |
   | Unconsolidated backlog | low | large per-bank → `hindsight bank consolidate <bank>` (see optimization) |
   | Warnings | recall/retain noise | `[STUCK_STACK]`, repeated `APIConnectionError`, `empty message content` → LLM provider (OpenRouter/deepseek) is flaky; not a DB problem |

3. **Reap orphaned jobs** (only if section 3 is non-empty and the container is running):
   ```bash
   "$SKILL_DIR/scripts/reap-orphans.sh"           # dry-run: confirm the candidate set
   "$SKILL_DIR/scripts/reap-orphans.sh" --apply   # reset to 'pending'; live worker reclaims them
   ```
   Never reap against a stopped container — the reaper must exclude the live `worker_id`.

4. **Repair missing functions** (only if section 4 shows any `f`):
   ```bash
   cd ~/docker/stacks/ai/hindsight
   set -a; . .env; set +a
   PGPASSWORD="$HINDSIGHT_DB_PASSWORD" psql -h 127.0.0.1 -U "$HINDSIGHT_DB_USER" -d "$HINDSIGHT_DB_NAME" \
     -f fixes/01-public-maintenance-routines.sql
   ```
   Idempotent. Then re-run the sweep to confirm `t | t`.

5. **Persist the outcome.** If anything non-trivial was fixed:
   ```bash
   hindsight memory retain infra "tune-up <date>: <what was wrong> → <what was done>" --context deployment
   ```

## Failure modes

- **Queue frozen but no orphans and functions present** → look at section 5/7. Repeated
  `[STUCK_STACK]`/provider errors mean the LLM backend is failing consolidation, not the queue.
  That is an OpenRouter/model issue (check `HINDSIGHT_API_*_LLM_MODEL` in `.env`), not a reap target.
- **Orphans reappear every run** → something keeps recreating the container. Expected after each
  `docker compose up -d --force-recreate`; drain to `pending=0` before recreating, or wire the
  reactive post-recreate hook in scheduling.md.
