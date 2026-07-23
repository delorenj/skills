#!/usr/bin/env bash
# Reset async jobs orphaned by a dead worker back to 'pending' so the live worker reclaims them.
#
# Hindsight's worker only recovers its OWN stale claims (poller.py recover_own_tasks resets
# WHERE status='processing' AND worker_id = <self>), and worker_id is the ephemeral container
# hostname — so every container recreate strands in-flight jobs forever. This is the missing
# cross-worker reaper. Mirrors ~/docker/stacks/ai/hindsight/fixes/02-reap-orphaned-jobs.sql.
#
# SAFETY: dry-run by default. The live worker MUST be running so its fresh claims are excluded.
# Usage: reap-orphans.sh            # dry-run: show what WOULD be reset
#        reap-orphans.sh --apply    # actually reset them
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/hs-lib.sh"

STALE_MIN="${HS_ORPHAN_STALE_MIN:-30}"
APPLY=0; [ "${1:-}" = "--apply" ] && APPLY=1

LIVE="$(hs_live_worker)"
if [ -z "$LIVE" ]; then
  echo "REFUSING: hindsight container '$HS_CONTAINER' is not running." >&2
  echo "Start it and let it claim work first — the reaper must exclude the live worker_id." >&2
  exit 2
fi

WHERE="status='processing'
       AND worker_id IS DISTINCT FROM '${LIVE}'
       AND claimed_at < now() - interval '${STALE_MIN} minutes'
       AND result_metadata->>'batch_id' IS NULL"

echo "live worker: $LIVE   stale threshold: ${STALE_MIN}m"
echo "--- orphan candidates ---"
hs_db_table "SELECT worker_id, operation_type, count(*), min(claimed_at) AS oldest
             FROM ${HS_SCHEMA}.async_operations WHERE ${WHERE}
             GROUP BY 1,2 ORDER BY 3 DESC;"

N="$(hs_db "SELECT count(*) FROM ${HS_SCHEMA}.async_operations WHERE ${WHERE};" | tr -d '[:space:]')"
echo "total candidates: ${N:-0}"

if [ "${N:-0}" -eq 0 ]; then echo "nothing to reap."; exit 0; fi

if [ "$APPLY" -eq 0 ]; then
  echo; echo "DRY-RUN. Re-run with --apply to reset these ${N} jobs to 'pending'."
  exit 0
fi

echo; echo "applying…"
hs_db "UPDATE ${HS_SCHEMA}.async_operations
       SET status='pending', worker_id=NULL, claimed_at=NULL, updated_at=now()
       WHERE ${WHERE};"
echo "reaped ${N} jobs. The live worker will reclaim them on its next poll."
