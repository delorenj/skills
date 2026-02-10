#!/usr/bin/env bash
# Story Delegation Script
# Spawns component orchestrators via zellij to delegate cross-component tasks
# Supports multi-path iMi cluster resolution

set -euo pipefail

# Configuration
PLATFORM_ROOT="${PLATFORM_ROOT:-$(pwd)}"
ZELLIJ_SESSION="${ZELLIJ_SESSION:-33god-platform}"

# Multi-path support: search multiple roots for iMi clusters
# Can be overridden with: PLATFORM_SEARCH_ROOTS="/path1:/path2:/path3"
if [ -n "${PLATFORM_SEARCH_ROOTS:-}" ]; then
    IFS=':' read -ra SEARCH_ROOTS <<< "$PLATFORM_SEARCH_ROOTS"
else
    # Default search paths for 33GOD ecosystem
    SEARCH_ROOTS=(
        "/home/delorenj/code"
        "/home/delorenj/code/33GOD"
    )
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Function to find iMi cluster by component name
find_component_dir() {
    local component_name=$1

    for search_root in "${SEARCH_ROOTS[@]}"; do
        local candidate="${search_root}/${component_name}"
        if [ -d "${candidate}/.iMi" ]; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Delegate a cross-component story to component orchestrators via zellij.

OPTIONS:
    -s, --story FILE        Platform story file (markdown)
    -c, --components LIST   Comma-separated list of components
    -t, --task DESCRIPTION  Task description for each component
    -h, --help             Show this help message

EXAMPLES:
    # Delegate from story file
    $0 --story docs/stories/distributed-tracing.md --components "bloodbank,flume,imi"

    # Delegate with task description
    $0 --task "Add trace context support" --components "bloodbank,flume"

ENVIRONMENT:
    PLATFORM_ROOT       Platform root directory (default: current directory)
    ZELLIJ_SESSION      Zellij session name (default: 33god-platform)
EOF
    exit 1
}

# Parse arguments
STORY_FILE=""
COMPONENTS=""
TASK_DESC=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--story)
            STORY_FILE="$2"
            shift 2
            ;;
        -c|--components)
            COMPONENTS="$2"
            shift 2
            ;;
        -t|--task)
            TASK_DESC="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validation
if [ -z "$COMPONENTS" ]; then
    echo "${RED}Error: Components list is required${NC}"
    usage
fi

if [ -z "$STORY_FILE" ] && [ -z "$TASK_DESC" ]; then
    echo "${RED}Error: Either --story or --task must be provided${NC}"
    usage
fi

# Check if zellij is available
if ! command -v zellij &> /dev/null; then
    echo "${RED}Error: zellij not found. Install zellij first.${NC}"
    exit 1
fi

# Load story context if provided
STORY_CONTEXT=""
if [ -n "$STORY_FILE" ]; then
    if [ ! -f "$STORY_FILE" ]; then
        echo "${RED}Error: Story file not found: ${STORY_FILE}${NC}"
        exit 1
    fi
    STORY_CONTEXT=$(cat "$STORY_FILE")
    echo "${BLUE}📖 Loaded story from: ${STORY_FILE}${NC}"
fi

# Parse components
IFS=',' read -ra COMPONENT_LIST <<< "$COMPONENTS"

echo ""
echo "${BLUE}🚀 Delegating to ${#COMPONENT_LIST[@]} components...${NC}"
echo ""

# Check if zellij session exists, create if not
if ! zellij list-sessions 2>/dev/null | grep -q "^${ZELLIJ_SESSION}$"; then
    echo "${YELLOW}Creating zellij session: ${ZELLIJ_SESSION}${NC}"
    zellij --session "$ZELLIJ_SESSION" &
    sleep 2
fi

# Delegate to each component
for component in "${COMPONENT_LIST[@]}"; do
    # Find component using multi-path search
    if ! component_dir=$(find_component_dir "$component"); then
        echo "${RED}⚠ Component not found: ${component}${NC}"
        echo "  Searched in:"
        for root in "${SEARCH_ROOTS[@]}"; do
            echo "    - ${root}/${component}"
        done
        continue
    fi

    echo "${GREEN}→ Delegating to: ${component} (${component_dir})${NC}"

    # Create component-specific task file
    TASK_FILE="${component_dir}/docs/delegated-task-$(date +%Y%m%d-%H%M%S).md"

    cat > "$TASK_FILE" <<EOF
# Delegated Task: $(basename "$STORY_FILE" .md 2>/dev/null || echo "Cross-Component Story")
**Component**: ${component}
**Delegated**: $(date '+%Y-%m-%d %H:%M:%S')
**Source**: Platform-level orchestration

## Context

${STORY_CONTEXT}

## Component-Specific Task

${TASK_DESC}

## Acceptance Criteria

- [ ] Task implementation complete
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Integration verified with dependent components

## Notes

This task is part of a cross-component initiative. Coordinate with other component teams as needed.

**Related Components**: ${COMPONENTS}

EOF

    echo "  - Task file: ${TASK_FILE}"

    # Create or switch to component tab in zellij
    TAB_NAME="${component}"

    # Check if tab exists
    if zellij --session "$ZELLIJ_SESSION" action list-tabs 2>/dev/null | grep -q "${TAB_NAME}"; then
        echo "  - Switching to existing tab: ${TAB_NAME}"
        zellij --session "$ZELLIJ_SESSION" action go-to-tab-name "${TAB_NAME}" 2>/dev/null || true
    else
        echo "  - Creating new tab: ${TAB_NAME}"
        zellij --session "$ZELLIJ_SESSION" action new-tab --name "${TAB_NAME}" 2>/dev/null || true
        sleep 0.5
    fi

    # Navigate to component directory and invoke orchestrator
    CMD="cd ${component_dir} && echo '📋 Delegated task ready: ${TASK_FILE}' && echo '' && echo 'Run: /workflow-status to check current state' && echo 'Run: /create-story to create implementation story' && echo '' && cat ${TASK_FILE}"

    # Write command to tab
    zellij --session "$ZELLIJ_SESSION" action write-chars "${CMD}" 2>/dev/null || true
    zellij --session "$ZELLIJ_SESSION" action write 13 2>/dev/null || true  # Enter key

    echo "  ${GREEN}✓${NC} Delegated"
    echo ""
done

# Create tracking file
TRACKING_FILE="${PLATFORM_ROOT}/docs/delegated-stories-tracking.md"

cat >> "$TRACKING_FILE" <<EOF

## Delegation: $(date '+%Y-%m-%d %H:%M:%S')

**Story**: $(basename "$STORY_FILE" .md 2>/dev/null || echo "Ad-hoc delegation")
**Components**: ${COMPONENTS}

### Task Files
EOF

for component in "${COMPONENT_LIST[@]}"; do
    component_dir="${PLATFORM_ROOT}/${component}"
    if [ -d "$component_dir" ]; then
        task_files=$(find "${component_dir}/docs" -name "delegated-task-*.md" -mmin -1 2>/dev/null || true)
        if [ -n "$task_files" ]; then
            echo "- ${component}: \`${task_files}\`" >> "$TRACKING_FILE"
        fi
    fi
done

cat >> "$TRACKING_FILE" <<EOF

### Status
- [ ] All component tasks created
- [ ] All component orchestrators notified
- [ ] Integration verified

---

EOF

echo ""
echo "${GREEN}✅ Delegation complete!${NC}"
echo ""
echo "Summary:"
echo "- Components notified: ${#COMPONENT_LIST[@]}"
echo "- Zellij session: ${ZELLIJ_SESSION}"
echo "- Tracking file: ${TRACKING_FILE}"
echo ""
echo "Next steps:"
echo "1. Switch to zellij session: zellij attach ${ZELLIJ_SESSION}"
echo "2. Navigate to component tabs to monitor progress"
echo "3. Use /workflow-status in each component to check completion"
