#!/usr/bin/env bash
# Component Inventory Script
# Scans all iMi cluster components and generates maturity assessment matrix
# Supports multi-path scanning for nested cluster structures

set -euo pipefail

# Configuration
PLATFORM_ROOT="${PLATFORM_ROOT:-$(pwd)}"
OUTPUT_FILE="${OUTPUT_FILE:-${PLATFORM_ROOT}/docs/component-inventory.md}"

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
RED='\033[0;31m'
NC='\033[0m'

echo "📦 Generating component inventory for iMi clusters..."
echo "Search roots:"
for root in "${SEARCH_ROOTS[@]}"; do
    echo "  - ${root}"
done
echo ""

# Find all iMi clusters (identified by .iMi/ directory)
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

        components+=("$cluster_name:$cluster_dir")
        echo "  Found: ${cluster_name} (iMi cluster)"
    done < <(find "$search_root" -maxdepth 2 -type d -name ".iMi" -print0 2>/dev/null)
done

if [ ${#components[@]} -eq 0 ]; then
    echo "${RED}No components found${NC}"
    exit 1
fi

echo "Found ${#components[@]} potential components"
echo ""

# Initialize output
cat > "$OUTPUT_FILE" <<EOF
# 33GOD Component Inventory
Generated: $(date '+%Y-%m-%d %H:%M:%S')

## Maturity Assessment Matrix

| Component | BMAD Init | Planning | Architecture | Tests | Docs | Production | Maturity |
|-----------|-----------|----------|--------------|-------|------|------------|----------|
EOF

# Assess each component
declare -A maturity_scores

for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"

    echo "Assessing: ${component_name}"

    # Initialize scores
    bmad_init="❌"
    planning="❌"
    architecture="❌"
    tests="❌"
    docs="❌"
    production="❌"
    maturity_score=0

    # Check BMAD initialization
    if [ -d "${component_dir}/bmad" ] && [ -f "${component_dir}/docs/bmm-workflow-status.yaml" ]; then
        bmad_init="✅"
        ((maturity_score+=1))
    fi

    # Check planning artifacts (PRD or Tech Spec)
    if [ -d "${component_dir}/docs" ]; then
        if ls "${component_dir}/docs"/*prd*.md 1> /dev/null 2>&1 || \
           ls "${component_dir}/docs"/*tech-spec*.md 1> /dev/null 2>&1; then
            planning="✅"
            ((maturity_score+=2))
        fi
    fi

    # Check architecture documentation
    if [ -d "${component_dir}/docs" ]; then
        if ls "${component_dir}/docs"/*architecture*.md 1> /dev/null 2>&1 || \
           ls "${component_dir}/docs"/*arch*.md 1> /dev/null 2>&1; then
            architecture="✅"
            ((maturity_score+=2))
        fi
    fi

    # Check for tests
    if [ -d "${component_dir}/tests" ] || [ -d "${component_dir}/test" ] || \
       [ -f "${component_dir}/pytest.ini" ] || [ -f "${component_dir}/jest.config.js" ]; then
        tests="✅"
        ((maturity_score+=2))
    fi

    # Check for documentation
    if [ -f "${component_dir}/README.md" ] || [ -d "${component_dir}/docs" ]; then
        docs="✅"
        ((maturity_score+=1))
    fi

    # Check production readiness indicators
    # (Dockerfile, docker-compose, deployment configs)
    if [ -f "${component_dir}/Dockerfile" ] || \
       [ -f "${component_dir}/docker-compose.yml" ] || \
       [ -d "${component_dir}/.github/workflows" ]; then
        production="⚠️"  # Partial
        ((maturity_score+=1))
    fi

    # Determine maturity level
    maturity_level="🔴 Early"
    if [ $maturity_score -ge 8 ]; then
        maturity_level="🟢 Mature"
    elif [ $maturity_score -ge 5 ]; then
        maturity_level="🟡 Developing"
    elif [ $maturity_score -ge 2 ]; then
        maturity_level="🟠 Emerging"
    fi

    maturity_scores["$component_name"]=$maturity_score

    # Write row to table
    echo "| ${component_name} | ${bmad_init} | ${planning} | ${architecture} | ${tests} | ${docs} | ${production} | ${maturity_level} |" >> "$OUTPUT_FILE"
done

# Add component details section
cat >> "$OUTPUT_FILE" <<EOF

## Component Details

EOF

for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"

    cat >> "$OUTPUT_FILE" <<EOF

### ${component_name}

**Location**: \`${component_dir}\`

**Maturity Score**: ${maturity_scores[$component_name]}/9

**Status Indicators**:
EOF

    # BMAD status
    if [ -d "${component_dir}/bmad" ]; then
        echo "- ✅ BMAD initialized" >> "$OUTPUT_FILE"
        if [ -f "${component_dir}/docs/bmm-workflow-status.yaml" ]; then
            workflow_status=$(cat "${component_dir}/docs/bmm-workflow-status.yaml")
            echo "  - Workflow tracking active" >> "$OUTPUT_FILE"
        fi
    else
        echo "- ❌ BMAD not initialized - Run \`/workflow-init\` in component directory" >> "$OUTPUT_FILE"
    fi

    # Planning status
    if [ -d "${component_dir}/docs" ]; then
        prd_count=$(ls "${component_dir}/docs"/*prd*.md 2>/dev/null | wc -l || echo 0)
        spec_count=$(ls "${component_dir}/docs"/*tech-spec*.md 2>/dev/null | wc -l || echo 0)

        if [ $prd_count -gt 0 ]; then
            echo "- ✅ PRD documented (${prd_count} files)" >> "$OUTPUT_FILE"
        fi
        if [ $spec_count -gt 0 ]; then
            echo "- ✅ Tech specs documented (${spec_count} files)" >> "$OUTPUT_FILE"
        fi
        if [ $prd_count -eq 0 ] && [ $spec_count -eq 0 ]; then
            echo "- ❌ No planning artifacts - Run \`/prd\` or \`/tech-spec\`" >> "$OUTPUT_FILE"
        fi
    fi

    # Test coverage
    if [ -d "${component_dir}/tests" ] || [ -d "${component_dir}/test" ]; then
        test_file_count=$(find "${component_dir}" -name "*test*.py" -o -name "*test*.ts" -o -name "*test*.js" | wc -l || echo 0)
        echo "- ✅ Tests present (${test_file_count} test files)" >> "$OUTPUT_FILE"
    else
        echo "- ❌ No test directory found" >> "$OUTPUT_FILE"
    fi

    # Dependencies
    if [ -f "${component_dir}/package.json" ]; then
        echo "- 📦 Node.js project (package.json)" >> "$OUTPUT_FILE"
    fi
    if [ -f "${component_dir}/pyproject.toml" ] || [ -f "${component_dir}/requirements.txt" ]; then
        echo "- 🐍 Python project" >> "$OUTPUT_FILE"
    fi
    if [ -f "${component_dir}/Cargo.toml" ]; then
        echo "- 🦀 Rust project" >> "$OUTPUT_FILE"
    fi

    # Integration points
    if [ -f "${component_dir}/docker-compose.yml" ]; then
        echo "- 🐳 Docker Compose configuration present" >> "$OUTPUT_FILE"
    fi
done

# Add recommendations section
cat >> "$OUTPUT_FILE" <<EOF

## Recommendations

### By Maturity Level

**Mature Components** (Score 8-9):
EOF

mature_components=()
developing_components=()
emerging_components=()
early_components=()

for component_entry in "${components[@]}"; do
    IFS=':' read -r component_name component_dir <<< "$component_entry"
    score=${maturity_scores[$component_name]}

    if [ $score -ge 8 ]; then
        mature_components+=("$component_name")
    elif [ $score -ge 5 ]; then
        developing_components+=("$component_name")
    elif [ $score -ge 2 ]; then
        emerging_components+=("$component_name")
    else
        early_components+=("$component_name")
    fi
done

if [ ${#mature_components[@]} -gt 0 ]; then
    for comp in "${mature_components[@]}"; do
        echo "- ${comp}: Focus on optimization and advanced features" >> "$OUTPUT_FILE"
    done
else
    echo "- None yet" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" <<EOF

**Developing Components** (Score 5-7):
EOF

if [ ${#developing_components[@]} -gt 0 ]; then
    for comp in "${developing_components[@]}"; do
        echo "- ${comp}: Complete missing documentation and testing" >> "$OUTPUT_FILE"
    done
else
    echo "- None" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" <<EOF

**Emerging Components** (Score 2-4):
EOF

if [ ${#emerging_components[@]} -gt 0 ]; then
    for comp in "${emerging_components[@]}"; do
        echo "- ${comp}: Initialize BMAD and create planning artifacts" >> "$OUTPUT_FILE"
    done
else
    echo "- None" >> "$OUTPUT_FILE"
fi

cat >> "$OUTPUT_FILE" <<EOF

**Early Components** (Score 0-1):
EOF

if [ ${#early_components[@]} -gt 0 ]; then
    for comp in "${early_components[@]}"; do
        echo "- ${comp}: Start with \`/workflow-init\` to establish development process" >> "$OUTPUT_FILE"
    done
else
    echo "- None" >> "$OUTPUT_FILE"
fi

echo ""
echo "${GREEN}✓ Component inventory generated: ${OUTPUT_FILE}${NC}"
echo ""
echo "Summary:"
echo "- Mature: ${#mature_components[@]}"
echo "- Developing: ${#developing_components[@]}"
echo "- Emerging: ${#emerging_components[@]}"
echo "- Early: ${#early_components[@]}"
