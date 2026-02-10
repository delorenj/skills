#!/usr/bin/env bash
# Integration Map Generator
# Generates Mermaid diagrams showing iMi cluster component interactions
# Supports multi-path scanning for nested cluster structures

set -euo pipefail

# Configuration
PLATFORM_ROOT="${PLATFORM_ROOT:-$(pwd)}"
OUTPUT_FILE="${OUTPUT_FILE:-${PLATFORM_ROOT}/docs/integration-map.md}"

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
BLUE='\033[0;34m'
NC='\033[0m'

echo "🗺️  Generating integration map for iMi clusters..."
echo "Search roots:"
for root in "${SEARCH_ROOTS[@]}"; do
    echo "  - ${root}"
done
echo ""

# Find all iMi clusters (identified by .iMi/ directory)
components=()
for search_root in "${SEARCH_ROOTS[@]}"; do
    if [ ! -d "$search_root" ]; then
        continue
    fi

    # Find directories containing .iMi/ (these are iMi clusters)
    # maxdepth 2: search_root (0) → component_dir (1) → .iMi (2)
    while IFS= read -r -d '' imi_marker; do
        cluster_dir=$(dirname "$imi_marker")
        cluster_name=$(basename "$cluster_dir")

        components+=("$cluster_name:$cluster_dir")
        echo "  Found: ${cluster_name} (iMi cluster)"
    done < <(find "$search_root" -maxdepth 2 -type d -name ".iMi" -print0 2>/dev/null)
done

echo "Found ${#components[@]} components"
echo ""

# Initialize output
cat > "$OUTPUT_FILE" <<EOF
# 33GOD Platform Integration Map
Generated: $(date '+%Y-%m-%d %H:%M:%S')

## System Architecture Overview

\`\`\`mermaid
graph TB
    subgraph "33GOD Platform"
EOF

# Scan for common integration patterns
declare -A component_types
declare -A component_dependencies

for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"

    echo "Analyzing: ${component_name}"

    # Determine component type based on common patterns
    component_type="service"

    if [[ "$component_name" =~ (ui|frontend|web|client) ]]; then
        component_type="frontend"
    elif [[ "$component_name" =~ (api|backend|server) ]]; then
        component_type="backend"
    elif [[ "$component_name" =~ (event|queue|bus|bloodbank) ]]; then
        component_type="event_backbone"
    elif [[ "$component_name" =~ (session|task|workflow|flume) ]]; then
        component_type="orchestrator"
    elif [[ "$component_name" =~ (cli|imi|tool) ]]; then
        component_type="cli"
    elif [[ "$component_name" =~ (db|database|storage) ]]; then
        component_type="storage"
    fi

    component_types["$component_name"]=$component_type

    # Scan for dependencies (docker-compose, package.json, pyproject.toml)
    dependencies=""

    if [ -f "${component_dir}/docker-compose.yml" ]; then
        # Extract service dependencies from docker-compose
        deps=$(grep -E "^    [a-z_-]+:" "${component_dir}/docker-compose.yml" 2>/dev/null | sed 's/://g' | sed 's/^    //' || true)
        dependencies="${dependencies} ${deps}"
    fi

    if [ -f "${component_dir}/package.json" ]; then
        # Extract workspace dependencies
        deps=$(grep -A 20 '"dependencies"' "${component_dir}/package.json" 2>/dev/null | grep '@33god' | sed 's/.*"@33god\/\([^"]*\)".*/\1/' || true)
        dependencies="${dependencies} ${deps}"
    fi

    if [ -f "${component_dir}/pyproject.toml" ]; then
        # Extract Python dependencies
        deps=$(grep -A 20 '\[tool.poetry.dependencies\]' "${component_dir}/pyproject.toml" 2>/dev/null | grep '33god' | sed 's/.*33god-\([^ ]*\).*/\1/' || true)
        dependencies="${dependencies} ${deps}"
    fi

    component_dependencies["$component_name"]="$dependencies"
done

# Generate mermaid nodes
for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"
    component_type=${component_types[$component_name]}

    # Choose node style based on type
    case $component_type in
        frontend)
            echo "        ${component_name}[${component_name}<br/>Frontend]" >> "$OUTPUT_FILE"
            echo "        style ${component_name} fill:#e1f5ff" >> "$OUTPUT_FILE"
            ;;
        backend)
            echo "        ${component_name}[${component_name}<br/>Backend API]" >> "$OUTPUT_FILE"
            echo "        style ${component_name} fill:#fff3e0" >> "$OUTPUT_FILE"
            ;;
        event_backbone)
            echo "        ${component_name}{{${component_name}<br/>Event Backbone}}" >> "$OUTPUT_FILE"
            echo "        style ${component_name} fill:#f3e5f5" >> "$OUTPUT_FILE"
            ;;
        orchestrator)
            echo "        ${component_name}[${component_name}<br/>Orchestrator]" >> "$OUTPUT_FILE"
            echo "        style ${component_name} fill:#e8f5e9" >> "$OUTPUT_FILE"
            ;;
        cli)
            echo "        ${component_name}[${component_name}<br/>CLI Tool]" >> "$OUTPUT_FILE"
            echo "        style ${component_name} fill:#fce4ec" >> "$OUTPUT_FILE"
            ;;
        storage)
            echo "        ${component_name}[(${component_name}<br/>Storage)]" >> "$OUTPUT_FILE"
            echo "        style ${component_name} fill:#f1f8e9" >> "$OUTPUT_FILE"
            ;;
        *)
            echo "        ${component_name}[${component_name}]" >> "$OUTPUT_FILE"
            ;;
    esac
done

# Generate connections
echo "" >> "$OUTPUT_FILE"

for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"
    deps=${component_dependencies[$component_name]}

    # Create edges for dependencies
    for dep in $deps; do
        # Check if dependency is a known component
        for target_entry in "${components[@]}"; do
            IFS=':' read -r target_name target_dir <<< "$target_entry"
            if [[ "$dep" == "$target_name" || "$dep" =~ "$target_name" ]]; then
                echo "        ${component_name} --> ${target_name}" >> "$OUTPUT_FILE"
            fi
        done
    done
done

cat >> "$OUTPUT_FILE" <<EOF
    end
\`\`\`

## Component Registry

EOF

# Generate component details
for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"
    component_type=${component_types[$component_name]}

    cat >> "$OUTPUT_FILE" <<EOF

### ${component_name}

**Type**: ${component_type}
**Location**: \`${component_dir}\`

EOF

    # Check for README
    if [ -f "${component_dir}/README.md" ]; then
        # Extract first paragraph as description
        description=$(head -20 "${component_dir}/README.md" | grep -v '^#' | grep -v '^$' | head -1 || echo "No description")
        echo "**Description**: ${description}" >> "$OUTPUT_FILE"
    fi

    # Dependencies
    deps=${component_dependencies[$component_name]}
    if [ -n "$deps" ]; then
        echo "" >> "$OUTPUT_FILE"
        echo "**Dependencies**:" >> "$OUTPUT_FILE"
        for dep in $deps; do
            echo "- \`${dep}\`" >> "$OUTPUT_FILE"
        done
    fi

    # API endpoints (if backend)
    if [[ "$component_type" == "backend" ]]; then
        if [ -f "${component_dir}/openapi.yml" ] || [ -f "${component_dir}/openapi.json" ]; then
            echo "- 📄 OpenAPI specification available" >> "$OUTPUT_FILE"
        fi
    fi

    # Event schemas (if event backbone)
    if [[ "$component_type" == "event_backbone" ]]; then
        if [ -d "${component_dir}/schemas" ]; then
            schema_count=$(find "${component_dir}/schemas" -name "*.json" -o -name "*.yaml" | wc -l || echo 0)
            echo "- 📋 Event schemas: ${schema_count} defined" >> "$OUTPUT_FILE"
        fi
    fi
done

# Add event flow section if event backbone detected
has_event_backbone=false
for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"
    if [[ "${component_types[$component_name]}" == "event_backbone" ]]; then
        has_event_backbone=true
        EVENT_BACKBONE_NAME="$component_name"
        break
    fi
done

if [ "$has_event_backbone" = true ]; then
    cat >> "$OUTPUT_FILE" <<EOF

## Event Flow Diagram

\`\`\`mermaid
sequenceDiagram
    autonumber
EOF

    # Generate example event flow
    producers=()
    consumers=()

    for component_entry in "${components[@]}"; do
        IFS=':' read -r component_name component_dir <<< "$component_entry"
        component_type=${component_types[$component_name]}

        if [[ "$component_type" =~ (cli|frontend|orchestrator) ]]; then
            producers+=("$component_name")
        fi
        if [[ "$component_type" =~ (backend|orchestrator|service) ]]; then
            consumers+=("$component_name")
        fi
    done

    # Generate sample event flows
    if [ ${#producers[@]} -gt 0 ] && [ ${#consumers[@]} -gt 0 ]; then
        producer=${producers[0]}
        consumer=${consumers[0]}

        cat >> "$OUTPUT_FILE" <<EOF
    participant ${producer}
    participant ${EVENT_BACKBONE_NAME}
    participant ${consumer}

    ${producer}->>+${EVENT_BACKBONE_NAME}: Publish Event (e.g., task.created)
    ${EVENT_BACKBONE_NAME}-->>-${consumer}: Route Event
    ${consumer}->>+${EVENT_BACKBONE_NAME}: Process & Emit Result (e.g., task.completed)
    ${EVENT_BACKBONE_NAME}-->>-${producer}: Deliver Result
\`\`\`

> **Note**: This is a simplified example flow. Actual event patterns may vary by component.
EOF
    fi
fi

# Add integration notes section
cat >> "$OUTPUT_FILE" <<EOF

## Integration Notes

### Common Patterns

1. **Event-Driven Communication**: Components communicate via ${EVENT_BACKBONE_NAME:-event backbone}
2. **API-First Design**: Backend services expose REST/GraphQL APIs
3. **CLI Tools**: Command-line interfaces for developer workflows
4. **Orchestration Layer**: Coordinates multi-step workflows across components

### Data Flow

- **User Actions** → CLI/Frontend → Event Backbone → Backend Services
- **System Events** → Event Backbone → Subscribers → State Updates
- **Task Execution** → Orchestrator → Event Backbone → Execution Services

### Dependency Guidelines

- Components should minimize direct dependencies
- Prefer event-based communication over direct API calls
- Use API gateways for external integrations
- Maintain backward compatibility for event schemas

EOF

echo ""
echo "${GREEN}✓ Integration map generated: ${OUTPUT_FILE}${NC}"
echo ""
echo "Component types identified:"
for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"
    echo "  - ${component_name}: ${component_types[$component_name]}"
done
