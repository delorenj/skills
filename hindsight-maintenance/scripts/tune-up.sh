#!/usr/bin/env bash
# Read-only health sweep for the Hindsight memory system.
# Gathers all evidence in one pass into a markdown report; changes nothing.
# Usage: tune-up.sh            -> writes report, prints its path
#        tune-up.sh --stdout   -> also echoes the report to stdout
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/hs-lib.sh"

STALE_MIN="${HS_ORPHAN_STALE_MIN:-30}"     # a 'processing' claim older than this, owned by a
                                           # non-live worker, is an orphan candidate
STATE="$(hs_state_dir)"
TS="$(date +%Y%m%d-%H%M%S)"
REPORT="$STATE/tune-up-$TS.md"
LIVE="$(hs_live_worker)"
# Docker container hostnames are hex only, so direct SQL interpolation is injection-safe.
# Empty (container down) ⇒ sentinel that no real worker_id equals, so all rows show as candidates.
LIVE_SQL="${LIVE:-__container_down__}"

{
  echo "# Hindsight tune-up — $(date -Iseconds)"
  echo
  echo "- live worker (container hostname): \`${LIVE:-<container not running>}\`"
  echo "- schema: \`$HS_SCHEMA\` · db: \`$HS_PGHOST:$HS_PGPORT\` · stale-threshold: ${STALE_MIN}m"
  echo

  echo "## 1. Container"
  echo '```'
  docker ps --filter "name=^/${HS_CONTAINER}$" --format '{{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null || echo "docker unavailable"
  echo '```'
  echo

  echo "## 2. Async queue (pending / processing)"
  echo '```'
  hs_db_table "SELECT operation_type, status, count(*)
               FROM ${HS_SCHEMA}.async_operations
               WHERE status IN ('pending','processing')
               GROUP BY 1,2 ORDER BY 1,2;"
  echo '```'
  echo

  echo "## 3. Orphaned jobs (processing, non-live worker, > ${STALE_MIN}m) — reap candidates"
  echo '```'
  hs_db_table "SELECT worker_id, operation_type, count(*), min(claimed_at) AS oldest_claim
               FROM ${HS_SCHEMA}.async_operations
               WHERE status='processing'
                 AND worker_id IS DISTINCT FROM '${LIVE_SQL}'
                 AND claimed_at < now() - interval '${STALE_MIN} minutes'
                 AND result_metadata->>'batch_id' IS NULL
               GROUP BY 1,2 ORDER BY 3 DESC;"
  echo '```'
  echo "> Non-empty ⇒ run \`reap-orphans.sh --apply\` (container must be running first)."
  echo

  echo "## 4. Missing public.* maintenance functions (upstream bug #2056)"
  echo '```'
  hs_db_table "SELECT
      to_regprocedure('public.banks_needing_consolidation()') IS NOT NULL AS banks_needing_consolidation,
      to_regprocedure('public.schemas_with_expired_rows(text,text,integer)') IS NOT NULL AS schemas_with_expired_rows;"
  echo '```'
  echo "> Any \`f\` ⇒ apply \`~/docker/stacks/ai/hindsight/fixes/01-public-maintenance-routines.sql\`."
  echo

  echo "## 5. Failed operations (last 7 days)"
  echo '```'
  hs_db_table "SELECT operation_type, count(*), max(updated_at) AS last_seen,
                      left(coalesce(max(error_message),'(none)'),100) AS sample_error
               FROM ${HS_SCHEMA}.async_operations
               WHERE status='failed' AND updated_at > now() - interval '7 days'
               GROUP BY 1 ORDER BY 2 DESC;"
  echo '```'
  echo

  echo "## 6. Per-bank anomalies (top unconsolidated backlog)"
  echo '```'
  hs_db_table "SELECT bank_id,
                      count(*) FILTER (WHERE consolidated_at IS NULL
                                         AND consolidation_failed_at IS NULL
                                         AND fact_type IN ('experience','world')) AS unconsolidated,
                      count(*) AS total
               FROM ${HS_SCHEMA}.memory_units
               GROUP BY 1
               HAVING count(*) FILTER (WHERE consolidated_at IS NULL
                                         AND consolidation_failed_at IS NULL
                                         AND fact_type IN ('experience','world')) > 0
               ORDER BY 2 DESC LIMIT 15;"
  echo '```'
  echo

  echo "## 7. Recent container warnings/errors"
  echo '```'
  docker logs "$HS_CONTAINER" --since 24h 2>&1 \
    | grep -iE 'error|warn|failed|traceback|does not exist' \
    | grep -viE '\[WORKER_STATS\]|\[PENDING_BREAKDOWN\]' \
    | tail -15 || echo "(no docker logs)"
  echo '```'
} > "$REPORT" 2>&1

echo "$REPORT"
[ "${1:-}" = "--stdout" ] && cat "$REPORT"
exit 0
