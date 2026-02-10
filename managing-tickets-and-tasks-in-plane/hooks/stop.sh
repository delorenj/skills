#!/bin/bash
#
# Stop Hook: Update Plane Ticket After Session (Multi-Workspace)
#
# Purpose: Capture session work in ticket for team visibility
# Trigger: End of coding session (automatic via Claude hooks)
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

# Log configuration
LOG_DIR="${HOME}/.cache/claude-plane/${WORKSPACE}/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function: Get active ticket from git branch
get_active_ticket() {
  git branch --show-current 2>/dev/null | grep -oP '(CWS-\d+|STORY-\d+|[A-Z]+-\d+)' || echo ""
}

# Function: Get session summary
get_session_summary() {
  local ticket_id="$1"
  local session_start="${SESSION_START_TIME:-$(date -d '2 hours ago' +%s)}"
  local session_end=$(date +%s)
  local duration_minutes=$(( (session_end - session_start) / 60 ))

  # Get git changes
  local files_changed=$(git diff --cached --name-only 2>/dev/null | wc -l)
  local lines_added=$(git diff --cached --numstat 2>/dev/null | awk '{add+=$1} END {print add}')
  local lines_removed=$(git diff --cached --numstat 2>/dev/null | awk '{del+=$2} END {print del}')

  # Get recent commits (last 2 hours)
  local commits=$(git log --since="${session_start}" --pretty=format:"- %s" 2>/dev/null)

  # Format summary
  cat <<EOF
## Development Log

### Session $(date +%Y-%m-%d) $(date +%H:%M)
**Developer:** $(git config user.name 2>/dev/null || echo "Unknown")
**Duration:** ${duration_minutes}m
**Branch:** $(git branch --show-current 2>/dev/null || echo "unknown")
**Workspace:** $WORKSPACE

**Changes:**
- Files changed: $files_changed
- Lines added: ${lines_added:-0}
- Lines removed: ${lines_removed:-0}

**Commits:**
${commits:-No commits this session}

**Files Modified:**
$(git diff --cached --name-only 2>/dev/null | sed 's/^/- /' || echo "No staged changes")

---
EOF
}

# Function: Prompt for status update
prompt_status_update() {
  local ticket_id="$1"

  echo ""
  echo "Session complete. Update ticket status?"
  echo ""
  echo "Current ticket: [$ticket_id] (Workspace: $WORKSPACE)"
  echo ""
  echo "1) Keep in-progress (more work needed)"
  echo "2) Mark completed (ready for review)"
  echo "3) Mark blocked (waiting on something)"
  echo "4) Skip update"
  echo ""
  read -p "Select option (1-4): " -n 1 -r
  echo ""

  case $REPLY in
    1) echo "in-progress" ;;
    2) echo "completed" ;;
    3) echo "blocked" ;;
    *) echo "skip" ;;
  esac
}

# Function: Update ticket in Plane
update_ticket() {
  local ticket_id="$1"
  local session_log="$2"
  local new_status="$3"

  # Get current ticket data
  local ticket_data=$(curl -s -X GET \
    "https://${PLANE_BASE_URL}/api/v1/workspaces/${WORKSPACE}/projects/${PLANE_PROJECT_ID}/issues/?search=$ticket_id" \
    -H "X-Api-Key: $PLANE_API_KEY" \
    -H "Content-Type: application/json" 2>/dev/null || echo "[]")

  local ticket_uuid=$(echo "$ticket_data" | jq -r '.[0].id // empty' 2>/dev/null)

  if [ -z "$ticket_uuid" ]; then
    echo "⚠️  Warning: Ticket [$ticket_id] not found in Plane workspace [$WORKSPACE]"
    echo "Session log saved locally: $LOG_DIR/session-$(date +%Y%m%d-%H%M%S).md"
    echo "$session_log" > "$LOG_DIR/session-$(date +%Y%m%d-%H%M%S).md"
    return 1
  fi

  # Get current description
  local current_description=$(echo "$ticket_data" | jq -r '.[0].description // ""')

  # Append session log to description
  local updated_description=$(cat <<EOF
$current_description

$session_log
EOF
  )

  # Update ticket
  local update_payload=$(jq -n \
    --arg desc "$updated_description" \
    --arg status "$new_status" \
    '{description: $desc, state: $status}')

  local response=$(curl -s -X PATCH \
    "https://${PLANE_BASE_URL}/api/v1/workspaces/${WORKSPACE}/projects/${PLANE_PROJECT_ID}/issues/$ticket_uuid/" \
    -H "X-Api-Key: $PLANE_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$update_payload" 2>/dev/null)

  if echo "$response" | jq -e '.id' >/dev/null 2>&1; then
    echo "✓ Ticket updated: [$ticket_id]"
    echo "Status: $new_status"
    return 0
  else
    echo "⚠️  Failed to update ticket"
    echo "Response: $response"
    return 1
  fi
}

# Main execution
main() {
  echo ""
  echo "═══════════════════════════════════════"
  echo "  Plane Ticket Update (Workspace: $WORKSPACE)"
  echo "═══════════════════════════════════════"
  echo ""

  # Detect active ticket
  local ticket_id=$(get_active_ticket)

  if [ -z "$ticket_id" ]; then
    echo "No active ticket detected (branch name doesn't contain ticket ID)"
    echo "Skipping ticket update."
    return 0
  fi

  # Generate session summary
  local session_log=$(get_session_summary "$ticket_id")

  echo "Detected ticket: [$ticket_id]"
  echo ""
  echo "Session Summary:"
  echo "$session_log" | head -15
  echo ""

  # Prompt for status update
  local new_status=$(prompt_status_update "$ticket_id")

  if [ "$new_status" = "skip" ]; then
    echo "Skipping ticket update."
    return 0
  fi

  # Update ticket
  update_ticket "$ticket_id" "$session_log" "$new_status"

  echo ""
  echo "View ticket: https://${PLANE_BASE_URL}/${WORKSPACE}/projects/${PLANE_PROJECT_ID}/issues/$ticket_id"
  echo ""
}

# Run if not sourced
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main "$@"
fi
