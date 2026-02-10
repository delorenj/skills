#!/usr/bin/env bash
# Platform Status Aggregation Script
# Aggregates BMAD workflow status from all iMi cluster components
# Supports multi-path scanning for nested cluster structures

set -euo pipefail

# Configuration
PLATFORM_ROOT="${PLATFORM_ROOT:-$(pwd)}"
OUTPUT_FILE="${OUTPUT_FILE:-${PLATFORM_ROOT}/docs/platform-status.md}"

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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status indicators
COMPLETED="✓"
REQUIRED_NOT_STARTED="⚠"
CURRENT_PHASE="→"
OPTIONAL="-"

echo "🔍 Scanning for iMi cluster components with BMAD workflows..."
echo "Search roots:"
for root in "${SEARCH_ROOTS[@]}"; do
    echo "  - ${root}"
done
echo ""

# Find all iMi clusters (identified by .iMi/ directory) with BMAD initialized
components=()
for search_root in "${SEARCH_ROOTS[@]}"; do
    if [ ! -d "$search_root" ]; then
        echo "${YELLOW}⚠ Search root not found: ${search_root}${NC}"
        continue
    fi

    # Find directories containing .iMi/ (these are iMi clusters)
    # maxdepth 2: search_root (0) → component_dir (1) → .iMi (2)
    while IFS= read -r -d '' imi_marker; do
        cluster_dir=$(dirname "$imi_marker")
        cluster_name=$(basename "$cluster_dir")

        # Check if this cluster has BMAD initialized
        if [ -d "${cluster_dir}/bmad" ] && [ -f "${cluster_dir}/bmad/config.yaml" ]; then
            components+=("$cluster_name:$cluster_dir")
            echo "  Found: ${cluster_name} (iMi cluster with BMAD)"
        fi
    done < <(find "$search_root" -maxdepth 2 -type d -name ".iMi" -print0 2>/dev/null)
done

if [ ${#components[@]} -eq 0 ]; then
    echo "${RED}No components with BMAD workflows found${NC}"
    exit 1
fi

echo "Found ${#components[@]} components with BMAD workflows"
echo ""

# Initialize output
cat > "$OUTPUT_FILE" <<EOF
# 33GOD Platform Status Report
Generated: $(date '+%Y-%m-%d %H:%M:%S')

## Component Overview

EOF

# Aggregate status from each component
for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"

    echo "Analyzing: ${component_name}"

    status_file="${component_dir}/docs/bmm-workflow-status.yaml"
    config_file="${component_dir}/bmad/config.yaml"

    # Component header
    cat >> "$OUTPUT_FILE" <<EOF

### ${component_name}

EOF

    # Check if config exists
    if [ -f "$config_file" ]; then
        project_type=$(grep "^project_type:" "$config_file" | sed 's/project_type: *"\?\([^"]*\)"\?/\1/' || echo "unknown")
        project_level=$(grep "^project_level:" "$config_file" | sed 's/project_level: *\([0-9]\)/\1/' || echo "?")

        echo "- **Type**: ${project_type}" >> "$OUTPUT_FILE"
        echo "- **Level**: ${project_level}" >> "$OUTPUT_FILE"
    else
        echo "- **Status**: ${RED}Config not found${NC}" >> "$OUTPUT_FILE"
    fi

    # Check workflow status
    if [ -f "$status_file" ]; then
        echo "- **Workflow Status**:" >> "$OUTPUT_FILE"

        # Parse YAML for workflow completion
        # Analysis phase
        product_brief=$(grep "product-brief:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")
        brainstorm=$(grep "brainstorm:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")
        research=$(grep "research:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")

        # Planning phase
        prd=$(grep "prd:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")
        tech_spec=$(grep "tech-spec:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")

        # Solutioning phase
        architecture=$(grep "architecture:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")

        # Implementation phase
        sprint_planning=$(grep "sprint-planning:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")

        # Determine status symbols
        get_status_symbol() {
            local status=$1
            case "$status" in
                required) echo "$REQUIRED_NOT_STARTED" ;;
                recommended) echo "$OPTIONAL" ;;
                optional) echo "$OPTIONAL" ;;
                skipped) echo "-" ;;
                *.md|*.yaml) echo "$COMPLETED" ;;
                *) echo "?" ;;
            esac
        }

        echo "  - Analysis: $(get_status_symbol "$product_brief") product-brief, $(get_status_symbol "$brainstorm") brainstorm, $(get_status_symbol "$research") research" >> "$OUTPUT_FILE"
        echo "  - Planning: $(get_status_symbol "$prd") prd, $(get_status_symbol "$tech_spec") tech-spec" >> "$OUTPUT_FILE"
        echo "  - Solutioning: $(get_status_symbol "$architecture") architecture" >> "$OUTPUT_FILE"
        echo "  - Implementation: $(get_status_symbol "$sprint_planning") sprint-planning" >> "$OUTPUT_FILE"
    else
        echo "- **Status**: ${YELLOW}Workflow status file not found${NC}" >> "$OUTPUT_FILE"
    fi

    echo "" >> "$OUTPUT_FILE"
done

# Add summary section
cat >> "$OUTPUT_FILE" <<EOF

## Platform-Wide Summary

### Component Readiness
EOF

# Calculate readiness metrics
total_components=${#components[@]}
components_with_prd=0
components_with_architecture=0
components_in_implementation=0

for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"
    status_file="${component_dir}/docs/bmm-workflow-status.yaml"

    if [ -f "$status_file" ]; then
        prd=$(grep "prd:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")
        architecture=$(grep "architecture:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")
        sprint=$(grep "sprint-planning:" "$status_file" | sed 's/.*: *"\?\([^"]*\)"\?/\1/' || echo "optional")

        [[ "$prd" =~ \.md$ ]] && ((components_with_prd++))
        [[ "$architecture" =~ \.md$ ]] && ((components_with_architecture++))
        [[ "$sprint" =~ \.md$ ]] && ((components_in_implementation++))
    fi
done

cat >> "$OUTPUT_FILE" <<EOF

- Total components tracked: ${total_components}
- Components with PRD: ${components_with_prd}/${total_components}
- Components with architecture: ${components_with_architecture}/${total_components}
- Components in implementation phase: ${components_in_implementation}/${total_components}

### Recommendations

EOF

# Generate recommendations based on status
if [ $components_with_prd -lt $total_components ]; then
    echo "- **Planning Gap**: $((total_components - components_with_prd)) components missing PRDs. Consider running \`/prd\` for these components." >> "$OUTPUT_FILE"
fi

if [ $components_with_architecture -lt $total_components ]; then
    echo "- **Architecture Gap**: $((total_components - components_with_architecture)) components missing architecture docs. Run \`/architecture\` for Level 2+ components." >> "$OUTPUT_FILE"
fi

if [ $components_in_implementation -eq 0 ]; then
    echo "- **Implementation Blocked**: No components have started implementation. Begin with \`/sprint-planning\` on priority components." >> "$OUTPUT_FILE"
fi

echo ""
echo "${GREEN}${COMPLETED} Platform status report generated: ${OUTPUT_FILE}${NC}"
echo ""
echo "Summary:"
echo "- Total components: ${total_components}"
echo "- Components with PRD: ${components_with_prd}/${total_components}"
echo "- Components with architecture: ${components_with_architecture}/${total_components}"
echo "- In implementation: ${components_in_implementation}/${total_components}"
