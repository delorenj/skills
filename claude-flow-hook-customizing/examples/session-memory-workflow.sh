#!/bin/bash
# Intelligent Session Memory Workflow for Claude Code
# This orchestrates memory management across development sessions

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MEMORY_NAMESPACE="intelliforia-dev"
PROJECT_ROOT="/home/delorenj/code/intelliForia-desktop"
MAX_RECALL_SESSIONS=3
RELEVANCE_THRESHOLD=0.7

# Helper function to log with timestamp
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

# ============================================
# SESSION START: Intelligent Memory Recall
# ============================================
session_start() {
    log "${GREEN}🧠 Initializing Intelligent Memory Workflow${NC}"

    # 1. Recall recent session summaries
    log "📚 Recalling last ${MAX_RECALL_SESSIONS} sessions..."

    npx claude-flow@alpha hooks memory-recall \
        --namespace "${MEMORY_NAMESPACE}" \
        --pattern "session-summary-*" \
        --limit ${MAX_RECALL_SESSIONS} \
        --format "chronological" \
        --output-format "summary" > /tmp/session-recall.txt

    # 2. Analyze current git state for context
    log "🔍 Analyzing current project state..."

    CURRENT_BRANCH=$(git branch --show-current)
    MODIFIED_FILES=$(git diff --name-only)
    RECENT_COMMITS=$(git log --oneline -5)

    # 3. Identify relevant memories based on current context
    log "🎯 Finding relevant memories for current context..."

    npx claude-flow@alpha hooks memory-search \
        --namespace "${MEMORY_NAMESPACE}" \
        --query "branch:${CURRENT_BRANCH} OR files:${MODIFIED_FILES}" \
        --relevance-threshold ${RELEVANCE_THRESHOLD} \
        --include-metadata true > /tmp/relevant-memories.txt

    # 4. Load critical project knowledge
    log "💡 Loading project-specific knowledge..."

    npx claude-flow@alpha hooks memory-retrieve \
        --namespace "${MEMORY_NAMESPACE}" \
        --keys "critical-patterns,known-issues,architecture-decisions" \
        --merge-results true > /tmp/project-knowledge.txt

    # 5. Create session context prompt
    cat > /tmp/session-context.txt << EOF
## Session Context Loaded

### Recent Sessions Summary
$(cat /tmp/session-recall.txt)

### Current Working Context
- Branch: ${CURRENT_BRANCH}
- Modified Files: ${MODIFIED_FILES}
- Recent Work: ${RECENT_COMMITS}

### Relevant Memories
$(cat /tmp/relevant-memories.txt)

### Project Knowledge
$(cat /tmp/project-knowledge.txt)

### Session Started: $(date)
EOF

    # 6. Initialize new session with smart defaults
    SESSION_ID="session-$(date +%Y%m%d-%H%M%S)"

    npx claude-flow@alpha hooks session-init \
        --session-id "${SESSION_ID}" \
        --context-file "/tmp/session-context.txt" \
        --enable-auto-memory true \
        --memory-strategy "adaptive"

    log "${GREEN}✅ Session ${SESSION_ID} initialized with intelligent context${NC}"

    # Store session start metadata
    npx claude-flow@alpha hooks memory-store \
        --namespace "${MEMORY_NAMESPACE}" \
        --key "session-active" \
        --value "{\"id\":\"${SESSION_ID}\",\"started\":\"$(date)\",\"branch\":\"${CURRENT_BRANCH}\"}" \
        --ttl 86400
}

# ============================================
# QUERY PROCESSING: Smart Memory Storage
# ============================================
after_query() {
    local QUERY="$1"
    local RESPONSE_FILE="$2"

    log "💭 Analyzing query for memory storage..."

    # 1. Classify query importance
    IMPORTANCE=$(npx claude-flow@alpha hooks analyze-importance \
        --query "${QUERY}" \
        --context-file "${RESPONSE_FILE}" \
        --factors "complexity,impact,reusability")

    # 2. Extract key information based on importance
    if [[ "${IMPORTANCE}" == "high" ]] || [[ "${IMPORTANCE}" == "critical" ]]; then
        log "📝 Storing high-importance information..."

        # Extract different types of knowledge
        npx claude-flow@alpha hooks extract-knowledge \
            --input "${RESPONSE_FILE}" \
            --types "decisions,patterns,solutions,issues" \
            --format "structured" > /tmp/extracted-knowledge.json

        # Store with intelligent categorization
        while IFS= read -r knowledge_item; do
            TYPE=$(echo "$knowledge_item" | jq -r '.type')
            KEY=$(echo "$knowledge_item" | jq -r '.key')
            VALUE=$(echo "$knowledge_item" | jq -r '.value')

            npx claude-flow@alpha hooks memory-store \
                --namespace "${MEMORY_NAMESPACE}" \
                --key "${TYPE}/${KEY}" \
                --value "${VALUE}" \
                --tags "auto-extracted,${TYPE}" \
                --ttl $([[ "${TYPE}" == "decisions" ]] && echo "2592000" || echo "604800")
        done < <(jq -c '.[]' /tmp/extracted-knowledge.json)
    fi

    # 3. Update session working memory
    log "🔄 Updating session working memory..."

    SESSION_ID=$(npx claude-flow@alpha hooks memory-retrieve \
        --namespace "${MEMORY_NAMESPACE}" \
        --key "session-active" | jq -r '.id')

    npx claude-flow@alpha hooks memory-append \
        --namespace "${MEMORY_NAMESPACE}" \
        --key "session-${SESSION_ID}/queries" \
        --value "{\"time\":\"$(date)\",\"query\":\"${QUERY}\",\"importance\":\"${IMPORTANCE}\"}"

    # 4. Identify and store reusable patterns
    if [[ "${RESPONSE_FILE}" == *".ts"* ]] || [[ "${RESPONSE_FILE}" == *".rs"* ]]; then
        log "🎨 Extracting reusable patterns..."

        npx claude-flow@alpha hooks pattern-extract \
            --file "${RESPONSE_FILE}" \
            --language "auto-detect" \
            --min-complexity 3 | while read -r pattern; do

            npx claude-flow@alpha hooks memory-store \
                --namespace "${MEMORY_NAMESPACE}" \
                --key "patterns/$(echo "$pattern" | sha256sum | cut -c1-8)" \
                --value "${pattern}" \
                --tags "code-pattern,reusable" \
                --ttl 1209600
        done
    fi
}

# ============================================
# SESSION END: Intelligent Summarization
# ============================================
session_end() {
    log "📊 Creating intelligent session summary..."

    SESSION_ID=$(npx claude-flow@alpha hooks memory-retrieve \
        --namespace "${MEMORY_NAMESPACE}" \
        --key "session-active" | jq -r '.id')

    # 1. Analyze session activity
    QUERIES=$(npx claude-flow@alpha hooks memory-retrieve \
        --namespace "${MEMORY_NAMESPACE}" \
        --key "session-${SESSION_ID}/queries")

    FILES_CHANGED=$(git diff --name-only)
    COMMITS_MADE=$(git log --oneline --since="1 day ago" | wc -l)

    # 2. Generate smart summary
    SUMMARY=$(npx claude-flow@alpha hooks generate-summary \
        --session-id "${SESSION_ID}" \
        --include "achievements,decisions,blockers,next-steps" \
        --analyze-patterns true \
        --identify-themes true)

    # 3. Store session summary with metadata
    npx claude-flow@alpha hooks memory-store \
        --namespace "${MEMORY_NAMESPACE}" \
        --key "session-summary-${SESSION_ID}" \
        --value "${SUMMARY}" \
        --metadata "{\"files_changed\":\"${FILES_CHANGED}\",\"commits\":${COMMITS_MADE}}" \
        --ttl 2592000

    # 4. Update long-term project knowledge
    log "🧬 Updating long-term project knowledge..."

    npx claude-flow@alpha hooks knowledge-synthesis \
        --session-id "${SESSION_ID}" \
        --update-types "architecture,patterns,issues" \
        --merge-strategy "intelligent"

    # 5. Prune old/irrelevant memories
    log "🧹 Pruning outdated memories..."

    npx claude-flow@alpha hooks memory-prune \
        --namespace "${MEMORY_NAMESPACE}" \
        --strategy "relevance-decay" \
        --keep-critical true \
        --max-age-days 30

    log "${GREEN}✅ Session ${SESSION_ID} completed and indexed${NC}"
}

# ============================================
# CONTEXT SWITCH: Smart Memory Adaptation
# ============================================
context_switch() {
    local NEW_CONTEXT="$1"

    log "🔄 Adapting memory for context: ${NEW_CONTEXT}"

    # Load context-specific memories
    npx claude-flow@alpha hooks memory-adapt \
        --namespace "${MEMORY_NAMESPACE}" \
        --context "${NEW_CONTEXT}" \
        --strategy "similarity-based" \
        --include-related true
}

# ============================================
# MEMORY OPTIMIZATION: Learning from Usage
# ============================================
optimize_memory() {
    log "⚡ Optimizing memory based on usage patterns..."

    # Analyze memory access patterns
    npx claude-flow@alpha hooks memory-analyze \
        --namespace "${MEMORY_NAMESPACE}" \
        --metrics "access-frequency,relevance-score,age" \
        --output "/tmp/memory-analysis.json"

    # Reorganize based on patterns
    npx claude-flow@alpha hooks memory-reorganize \
        --namespace "${MEMORY_NAMESPACE}" \
        --strategy "frequency-weighted" \
        --promote-threshold 0.8 \
        --demote-threshold 0.3

    # Create memory index for faster retrieval
    npx claude-flow@alpha hooks memory-index \
        --namespace "${MEMORY_NAMESPACE}" \
        --index-types "semantic,temporal,structural" \
        --output "/tmp/memory-index.json"
}

# Main workflow orchestration
case "${1:-start}" in
    start)
        session_start
        ;;
    query)
        after_query "$2" "$3"
        ;;
    end)
        session_end
        ;;
    switch)
        context_switch "$2"
        ;;
    optimize)
        optimize_memory
        ;;
    *)
        echo "Usage: $0 {start|query|end|switch|optimize}"
        exit 1
        ;;
esac