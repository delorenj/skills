#!/usr/bin/env bash
# Lists existing n8n workflows with metadata for discoverability.
# Used by the workflow-router skill to prevent reinventing automation.
#
# Usage:
#   bash list_n8n_workflows.sh         # full mode, fetches descriptions per workflow
#   bash list_n8n_workflows.sh --fast  # summary only, skips per-workflow fetch
#   bash list_n8n_workflows.sh --json  # raw JSON array of full workflow records
#
# Auth resolution order:
#   1. N8N_API_KEY env var
#   2. 1Password CLI: op read "op://DeLoSecrets/n8n/Saved on localhost/Cont"
#
# Note: n8n's /workflows list endpoint does NOT include the description field.
# Full mode performs N+1 fetches to populate descriptions, which IS the registry.

set -euo pipefail

N8N_HOST="${N8N_HOST:-https://n8n.delo.sh}"
MODE="${1:-pretty}"

for cmd in curl jq; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "ERROR: '$cmd' is required but not installed." >&2
    exit 1
  }
done

if [ -z "${N8N_API_KEY:-}" ]; then
  if command -v op >/dev/null 2>&1; then
    if ! N8N_API_KEY=$(op read "op://DeLoSecrets/n8n/Saved on localhost/Cont" 2>/dev/null); then
      echo "ERROR: N8N_API_KEY not set and 1Password fetch failed." >&2
      echo "Either:" >&2
      echo "  - export N8N_API_KEY=<your-token>" >&2
      echo "  - run 'eval \$(op signin)' first" >&2
      exit 2
    fi
  else
    echo "ERROR: N8N_API_KEY not set and 'op' CLI not found." >&2
    exit 2
  fi
fi

list_response=$(curl -sf \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Accept: application/json" \
  "$N8N_HOST/api/v1/workflows?limit=250") || {
  echo "ERROR: failed to fetch workflow list from $N8N_HOST" >&2
  exit 3
}

count=$(echo "$list_response" | jq '.data | length')

if [ "$count" -eq 0 ]; then
  echo "No workflows found in n8n at $N8N_HOST."
  exit 0
fi

case "$MODE" in
  --fast|-f)
    echo "# n8n Workflows ($count total, summary mode)"
    echo "Host: $N8N_HOST"
    echo
    echo "$list_response" | jq -r '.data[] |
      "## \(.name)",
      "- ID: \(.id)",
      "- Active: \(.active | tostring)",
      "- Tags: " + (((.tags // []) | map(if type == "object" then .name else . end) | join(", ")) | if . == "" then "(none)" else . end),
      ""
    '
    ;;

  --json|-j)
    ids=$(echo "$list_response" | jq -r '.data[].id')
    echo "["
    first=1
    for id in $ids; do
      detail=$(curl -sf -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_HOST/api/v1/workflows/$id")
      [ $first -eq 0 ] && echo ","
      echo "$detail" | jq '{id, name, active, tags: ((.tags // []) | map(.name)), description}'
      first=0
    done
    echo "]"
    ;;

  pretty|*)
    echo "# n8n Workflows ($count total, full mode)"
    echo "Host: $N8N_HOST"
    echo
    ids=$(echo "$list_response" | jq -r '.data[].id')
    missing_count=0
    for id in $ids; do
      detail=$(curl -sf -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_HOST/api/v1/workflows/$id")
      has_desc=$(echo "$detail" | jq -r '.description // "" | length > 0')
      [ "$has_desc" = "false" ] && missing_count=$((missing_count + 1))
      echo "$detail" | jq -r '
        "## \(.name)",
        "- ID: \(.id)",
        "- Active: \(.active | tostring)",
        "- Tags: " + (((.tags // []) | map(if type == "object" then .name else . end) | join(", ")) | if . == "" then "(none)" else . end),
        "- Description: " + ((.description // "" | gsub("\n"; " | ")) | if . == "" then "(MISSING)" else . end),
        ""
      '
    done
    echo "---"
    echo "Workflows missing structured descriptions: $missing_count / $count"
    ;;
esac
