#!/bin/bash
#
# GOD-13: Agent Context Self-Heal Monitor
# 
# Checks agent session context usage via OpenClaw CLI.
# If >=90%, writes compaction artifact and triggers restart.
#
# Installation: Run from agent workspace cron or systemd timer
# Usage: ./god-13-context-monitor.sh [AGENT_NAME] [THRESHOLD_PERCENT]
#
# Env vars:
#   AGENT_WORKSPACE: Path to agent workspace (default: current dir)
#   OPENCLAW_CONFIG: Path to OpenClaw config (default: ~/.openclaw/config.json)
#

set -euo pipefail

# Configuration
AGENT_NAME="${1:- lenoon}"
THRESHOLD_PERCENT="${2:-90}"
AGENT_WORKSPACE="${AGENT_WORKSPACE:-.}"
OPENCLAW_CONFIG="${OPENCLAW_CONFIG:-$HOME/.openclaw/config.json}"
MEMORY_DIR="${AGENT_WORKSPACE}/memory"
COMPACTION_FILE="${MEMORY_DIR}/context-compaction-latest.md"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Helper: log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

# Validate environment
if [[ ! -d "$AGENT_WORKSPACE" ]]; then
    log_error "Agent workspace not found: $AGENT_WORKSPACE"
    exit 1
fi

if [[ ! -d "$MEMORY_DIR" ]]; then
    mkdir -p "$MEMORY_DIR"
    log "Created memory directory: $MEMORY_DIR"
fi

# Get current context usage from OpenClaw
# This queries the session status via openclaw CLI
get_context_usage() {
    local percent=0
    
    # Try via openclaw CLI first
    if command -v openclaw &>/dev/null; then
        local session_key="agent:infra:${AGENT_NAME}:main"
        local status_json
        
        # Query session status (may fail if session not active, which is OK)
        status_json=$(openclaw sessions status "$session_key" 2>/dev/null || echo '{}')
        
        # Extract context_percent from response (schema may vary)
        percent=$(echo "$status_json" | jq -r '.context_percent // .context_usage_percent // 0' 2>/dev/null || echo 0)
    fi
    
    # Fallback: estimate from MEMORY.md size if CLI fails
    if [[ "$percent" -eq 0 ]] && [[ -f "${MEMORY_DIR}/MEMORY.md" ]]; then
        local size_bytes
        size_bytes=$(stat -f%z "${MEMORY_DIR}/MEMORY.md" 2>/dev/null || stat -c%s "${MEMORY_DIR}/MEMORY.md" 2>/dev/null || echo 0)
        local max_bytes=$((200000))  # Assume 200k token budget ≈ 1MB
        percent=$((size_bytes * 100 / max_bytes))
    fi
    
    echo "$percent"
}

# Write deterministic compaction artifact
# This file is read by the agent on restart to resume work
write_compaction_artifact() {
    local timestamp
    timestamp=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    
    cat > "$COMPACTION_FILE" << 'ARTIFACT'
# Context Compaction Checkpoint — Auto-Generated

**Timestamp:** ${TIMESTAMP}
**Triggered by:** god-13-context-monitor.sh (>=90% context)

## Active Tasks
(Preserve from previous MEMORY.md or session state)

## Decisions Made
- Context self-healing enabled (GOD-13)

## Open Blockers
(None if clean state)

## Next 3 Actions on Resume
1. Read full MEMORY.md for context
2. Check git status for uncommitted work
3. Resume from last active ticket

## Handoff Context
- **Monitor run:** ${TIMESTAMP}
- **Reason:** Context >=90% detected
- **Previous size:** Check MEMORY.md mtime

---
**Resume work using MEMORY.md as primary context source.**
ARTIFACT

    # Replace placeholder timestamp
    sed -i "s/\${TIMESTAMP}/$timestamp/g" "$COMPACTION_FILE"
    
    log_success "Wrote compaction artifact: $COMPACTION_FILE"
}

# Trigger agent restart
# Method depends on how agent is deployed (systemd, docker, etc.)
trigger_restart() {
    log_warn "Context >=90% — initiating controlled restart..."
    
    # Try systemd first (most common for agent services)
    local service_name="openclaw-agent-${AGENT_NAME}.service"
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        log "Restarting systemd service: $service_name"
        systemctl restart "$service_name" || log_error "Failed to restart $service_name"
        return 0
    fi
    
    # Try docker if systemd fails
    if command -v docker &>/dev/null; then
        local container_name="agent-${AGENT_NAME}"
        if docker ps --filter "name=$container_name" --format '{{.Names}}' | grep -q "$container_name"; then
            log "Restarting Docker container: $container_name"
            docker restart "$container_name" || log_error "Failed to restart container $container_name"
            return 0
        fi
    fi
    
    # Fallback: Manual restart instruction
    log_warn "Could not auto-restart. Manual restart required:"
    log_warn "  systemctl restart openclaw-agent-${AGENT_NAME}.service"
    log_warn "  OR: docker restart agent-${AGENT_NAME}"
    return 1
}

# Main logic
main() {
    log "Context monitor starting for agent: $AGENT_NAME"
    log "Threshold: ${THRESHOLD_PERCENT}%"
    
    # Get current context usage
    local current_usage
    current_usage=$(get_context_usage)
    log "Current context usage: ${current_usage}%"
    
    # Check threshold
    if (( current_usage >= THRESHOLD_PERCENT )); then
        log_warn "ALERT: Context usage at ${current_usage}% (threshold: ${THRESHOLD_PERCENT}%)"
        
        # Write compaction artifact BEFORE restart
        write_compaction_artifact
        
        # Trigger restart
        if trigger_restart; then
            log_success "Restart initiated. Agent will resume from compaction artifact."
            exit 0
        else
            log_error "Failed to auto-restart. Manual intervention required."
            exit 1
        fi
    else
        log_success "Context usage OK (${current_usage}%)"
        exit 0
    fi
}

main "$@"
