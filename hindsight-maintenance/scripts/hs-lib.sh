#!/usr/bin/env bash
# Shared helpers for hindsight-maintenance workflows. Source, don't execute:
#   source "$SKILL_DIR/scripts/hs-lib.sh"
#
# Deliberately does NOT set -euo pipefail — that is the calling script's choice,
# so sourcing into an interactive shell can't nuke it.

HS_STACK_DIR="${HS_STACK_DIR:-$HOME/docker/stacks/ai/hindsight}"
HS_ENV="${HS_ENV:-$HS_STACK_DIR/.env}"
HS_SCHEMA="${HS_SCHEMA:-hindsight}"
HS_PGHOST="${HS_PGHOST:-127.0.0.1}"
HS_PGPORT="${HS_PGPORT:-5432}"
HS_CONTAINER="${HS_CONTAINER:-hindsight}"
HS_STATE_DIR="${HS_STATE_DIR:-$HOME/.hindsight/maintenance}"

_hs_load_env() {
  if [ ! -f "$HS_ENV" ]; then
    echo "hs-lib: DB env not found at '$HS_ENV' (set HS_STACK_DIR or HS_ENV)" >&2
    return 1
  fi
  set -a; . "$HS_ENV"; set +a          # export HINDSIGHT_DB_USER/PASSWORD/NAME
}

# hs_db "SQL"        -> tuples only, pipe-delimited, unaligned (for scripting)
hs_db() {
  _hs_load_env || return 1
  PGPASSWORD="$HINDSIGHT_DB_PASSWORD" psql \
    -h "$HS_PGHOST" -p "$HS_PGPORT" \
    -U "${HINDSIGHT_DB_USER:-hindsight}" -d "${HINDSIGHT_DB_NAME:-hindsight}" \
    -X -A -F'|' -t -c "$1"
}

# hs_db_table "SQL"  -> same, but WITH a header row (for human-readable reports)
hs_db_table() {
  _hs_load_env || return 1
  PGPASSWORD="$HINDSIGHT_DB_PASSWORD" psql \
    -h "$HS_PGHOST" -p "$HS_PGPORT" \
    -U "${HINDSIGHT_DB_USER:-hindsight}" -d "${HINDSIGHT_DB_NAME:-hindsight}" \
    -X -A -F'|' -c "$1"
}

# hs_banks           -> every bank_id, one per line
hs_banks() {
  hindsight bank list -o json | jq -r '.[].bank_id'
}

# hs_live_worker     -> hostname of the running hindsight container (== current worker_id),
#                       or empty string if the container is not running
hs_live_worker() {
  docker inspect -f '{{.Config.Hostname}}' "$HS_CONTAINER" 2>/dev/null || true
}

hs_state_dir() { mkdir -p "$HS_STATE_DIR"; printf '%s\n' "$HS_STATE_DIR"; }
