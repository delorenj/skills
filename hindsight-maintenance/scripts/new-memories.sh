#!/usr/bin/env bash
# Emit memories retained since the last watermark for a bank (the karpathy-wiki feed).
#
# Usage:
#   new-memories.sh <bank>                 # rows since watermark (default: 24h ago if unset)
#   new-memories.sh <bank> --since <ISO>   # rows since an explicit timestamp
#   new-memories.sh <bank> --count         # just how many are new (for scheduling decisions)
#   new-memories.sh <bank> --advance <ISO> # set the watermark (call AFTER a successful compile)
#
# Output rows: id|created_at|fact_type|context|text   (pipe-delimited, one memory per line)
# Watermark file: $HS_STATE_DIR/wiki-<bank>.watermark
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/hs-lib.sh"

BANK="${1:-}"; [ -z "$BANK" ] && { echo "usage: new-memories.sh <bank> [--since ISO|--count|--advance ISO]" >&2; exit 1; }
shift
MODE="rows"; SINCE=""; ADVANCE=""
case "${1:-}" in
  --since)   SINCE="${2:-}";;
  --count)   MODE="count";;
  --advance) MODE="advance"; ADVANCE="${2:-}";;
  "")        ;;
  *) echo "unknown option: $1" >&2; exit 1;;
esac

STATE="$(hs_state_dir)"
WM="$STATE/wiki-${BANK}.watermark"

if [ "$MODE" = "advance" ]; then
  [ -z "$ADVANCE" ] && { echo "--advance needs an ISO timestamp" >&2; exit 1; }
  printf '%s\n' "$ADVANCE" > "$WM"
  echo "watermark[$BANK] = $ADVANCE"
  exit 0
fi

# Resolve the lower bound: explicit --since, else watermark file, else 24h ago.
if [ -z "$SINCE" ]; then
  if [ -f "$WM" ]; then SINCE="$(cat "$WM")"; else SINCE="$(date -Iseconds -d '24 hours ago')"; fi
fi
SINCE_SQL="${SINCE//\'/}"   # timestamps carry no quotes; strip any defensively

if [ "$MODE" = "count" ]; then
  hs_db "SELECT count(*) FROM ${HS_SCHEMA}.memory_units
         WHERE bank_id='${BANK//\'/}' AND created_at > '${SINCE_SQL}';" | tr -d '[:space:]'
  echo
  exit 0
fi

# Rows, oldest first, so the caller can advance the watermark to the last created_at it processed.
hs_db "SELECT id, created_at, fact_type, coalesce(context,''),
              regexp_replace(text, '[[:cntrl:]]+', ' ', 'g')
       FROM ${HS_SCHEMA}.memory_units
       WHERE bank_id='${BANK//\'/}' AND created_at > '${SINCE_SQL}'
       ORDER BY created_at ASC;"
