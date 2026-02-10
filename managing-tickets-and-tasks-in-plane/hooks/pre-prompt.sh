#!/bin/bash
#
# Pre-Prompt Hook: Check Plane Board State (Multi-Workspace)
#
# Purpose: Proactively guide user to optimal work based on current board state
# Trigger: Before every user prompt (automatic via Claude hooks)
#
# Multi-workspace support: Automatically detects workspace from context
#

set -euo pipefail

# Source workspace detector
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/workspace-detector.sh"

# Detect current workspace
WORKSPACE=$(get_current_workspace)

# Get workspace configuration
PLANE_API_KEY=$(get_workspace_api_key "$WORKSPACE")
PLANE_BASE_URL=$(get_workspace_base_url "$WORKSPACE")
PLANE_PROJECT_ID=$(get_workspace_project_id "$WORKSPACE")

# Only run if API key is available
if [ -z "$PLANE_API_KEY" ]; then
  # Silent exit - no Plane integration for this workspace
  exit 0
fi

# Cache configuration
CACHE_DIR="${HOME}/.cache/claude-plane/${WORKSPACE}"
CACHE_TTL=300  # 5 minutes

# Ensure cache directory exists
mkdir -p "$CACHE_DIR"

# Get user prompt from argument
USER_PROMPT="${1:-}"

# Function: Get current git branch ticket ID
get_branch_ticket_id() {
  git branch --show-current 2>/dev/null | grep -oP '(CWS-\d+|STORY-\d+|[A-Z]+-\d+)' || echo ""
}

# Function: Get active in-progress tickets
get_active_tickets() {
  local cache_file="$CACHE_DIR/active-tickets.json"
  local cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || echo 0) ))

  # Use cache if fresh
  if [ -f "$cache_file" ] && [ $cache_age -lt $CACHE_TTL ]; then
    cat "$cache_file"
    return
  fi

  # Fetch from Plane API
  local response=$(curl -s -X GET \
    "https://${PLANE_BASE_URL}/api/v1/workspaces/${WORKSPACE}/projects/${PLANE_PROJECT_ID}/issues/?state=in-progress" \
    -H "X-Api-Key: $PLANE_API_KEY" \
    -H "Content-Type: application/json" 2>/dev/null || echo "{}")

  echo "$response" > "$cache_file"
  echo "$response"
}

# Function: Check for conflicts
check_conflicts() {
  local current_ticket="$1"
  local prompt="$2"

  # Get active tickets
  local active_tickets=$(get_active_tickets)

  # Check if API returned valid JSON
  if ! echo "$active_tickets" | jq empty 2>/dev/null; then
    # Invalid response, skip checks
    return
  fi

  # Count in-progress tickets
  local in_progress_count=$(echo "$active_tickets" | jq '. | length' 2>/dev/null || echo 0)

  # Get WIP limits for this workspace
  local wip_limits=$(get_workspace_wip_limits "$WORKSPACE")
  local individual_limit=$(echo "$wip_limits" | jq -r '.individual')

  # WIP limit check
  if [ "$in_progress_count" -gt "$individual_limit" ]; then
    echo "⚠️  Board State Alert: WIP Limit Exceeded (Workspace: $WORKSPACE)"
    echo ""
    echo "Current in-progress tickets: $in_progress_count (recommend max $individual_limit)"
    echo "Consider completing existing work before starting new tasks."
    echo ""
  fi

  # Current ticket context
  if [ -n "$current_ticket" ]; then
    echo "📍 Current Context: Working on [$current_ticket] (Workspace: $WORKSPACE)"
    echo ""
    echo "✓ Proceeding with current work."
  fi
}

# Function: Recommend ticket
recommend_ticket() {
  local active_tickets=$(get_active_tickets)

  # Check if API returned valid JSON
  if ! echo "$active_tickets" | jq empty 2>/dev/null; then
    return
  fi

  local urgent_tickets=$(echo "$active_tickets" | jq -r '.[] | select(.priority == "urgent") | .name' 2>/dev/null | head -1)

  if [ -n "$urgent_tickets" ]; then
    echo ""
    echo "💡 Suggestion: Urgent ticket available: [$urgent_tickets]"
    echo "Consider prioritizing this before other work."
  fi
}

# Main execution
main() {
  # Silent mode: Only output if issues found
  local current_ticket=$(get_branch_ticket_id)

  # Check for conflicts
  check_conflicts "$current_ticket" "$USER_PROMPT"

  # Recommend ticket if no current context
  if [ -z "$current_ticket" ]; then
    recommend_ticket
  fi
}

# Run if not sourced
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main "$@"
fi
