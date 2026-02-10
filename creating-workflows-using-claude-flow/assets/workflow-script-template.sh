#!/usr/bin/env bash
# IntelliForia Iterate Workflow Runner
# Executes the two-phase development workflow using claude-flow

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_FILE="${SCRIPT_DIR}/intelliforia-iterate.json"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage
usage() {
  cat <<EOF
Usage: $0 [options]

Execute the intelliForia-iterate workflow using claude-flow swarm orchestration

Phases:
  Phase 1: Implementation Kickoff
    - Uses 'claude-flow swarm' with development strategy
    - Spawns up to 5 parallel agents
    - Opens Claude Code CLI for implementation

  Phase 2: System Verification
    - Starts Tauri backend (watches for 'Accepted new IPC')
    - Builds Chrome extension from ./extensions/chrome
    - Prompts for manual verification steps

Options:
  -t, --task FILE         Task specification file (default: TASK.md)
  -c, --context STRING    Additional context for requirements
  -p, --phase PHASE       Run specific phase only (1 or 2)
  -s, --skip-verification Skip Phase 2 verification
  -r, --max-retries N     Max retry attempts on Phase 2 failure (default: 2)
  --no-retry              Disable retry loop (fail immediately)
  -d, --dry-run          Show what would be executed
  -h, --help             Show this help message

Examples:
  # Run full workflow with retry on Phase 2 failure
  $0 --task TASK.md

  # Run with max 3 retries
  $0 --task TASK.md --max-retries 3

  # Disable retry loop
  $0 --task TASK.md --no-retry

  # Run Phase 1 only (implementation)
  $0 --task TASK.md --phase 1

  # Run Phase 2 only (verification)
  $0 --phase 2

  # Dry run to preview workflow
  $0 --task TASK.md --dry-run

EOF
  exit 1
}

# Parse arguments
TASK_FILE="${PROJECT_ROOT}/TASK.md"
CONTEXT=""
PHASE="all"
SKIP_VERIFICATION=false
MAX_RETRIES=2
RETRY_ENABLED=true
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -t|--task)
      TASK_FILE="$2"
      shift 2
      ;;
    -c|--context)
      CONTEXT="$2"
      shift 2
      ;;
    -p|--phase)
      PHASE="$2"
      shift 2
      ;;
    -s|--skip-verification)
      SKIP_VERIFICATION=true
      shift
      ;;
    -r|--max-retries)
      MAX_RETRIES="$2"
      shift 2
      ;;
    --no-retry)
      RETRY_ENABLED=false
      shift
      ;;
    -d|--dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      usage
      ;;
  esac
done

# Validate task file
if [[ ! -f "$TASK_FILE" ]]; then
  echo -e "${RED}Error: Task file not found: $TASK_FILE${NC}"
  exit 1
fi

# Display workflow info
echo -e "${GREEN}=== IntelliForia Iterate Workflow ===${NC}"
echo "Task File: $TASK_FILE"
echo "Phase: $PHASE"
echo "Method: claude-flow swarm (development strategy, max 5 agents)"
if [[ "$RETRY_ENABLED" == "true" && "$PHASE" == "all" ]]; then
  echo "Max Retries: $MAX_RETRIES"
fi
echo ""

# Dry run mode
if [[ "$DRY_RUN" == "true" ]]; then
  echo -e "${YELLOW}DRY RUN MODE${NC}"
  echo "Would execute Phase 1:"
  echo "  npx claude-flow@alpha swarm \"\$(cat $TASK_FILE)\" \\"
  echo "    --strategy development \\"
  echo "    --parallel \\"
  echo "    --max-agents 5 \\"
  echo "    --claude"
  echo ""
  echo "Would execute Phase 2:"
  echo "  1. mise start (with log monitoring)"
  echo "  2. cd extensions/chrome && bun run build"
  echo "  3. Manual verification prompt"
  if [[ "$RETRY_ENABLED" == "true" && "$PHASE" == "all" ]]; then
    echo ""
    echo "Retry loop enabled: Phase 2 failures will retry Phase 1 (max $MAX_RETRIES attempts)"
  fi
  exit 0
fi

# Check if claude-flow is available
if ! command -v npx &> /dev/null; then
  echo -e "${RED}Error: npx not found. Please install Node.js${NC}"
  exit 1
fi

# Function to run Phase 1
run_phase1() {
  local attempt=$1
  local context_override="${2:-$CONTEXT}"

  echo -e "${GREEN}Running Phase 1: Implementation Kickoff${NC}"
  if [[ $attempt -gt 1 ]]; then
    echo -e "${BLUE}Retry attempt $((attempt - 1))/${MAX_RETRIES} - Incorporating Phase 2 feedback${NC}"
  fi

  # Read task file content
  local task_content
  if [[ -f "$TASK_FILE" ]]; then
    task_content=$(cat "$TASK_FILE")
  else
    echo -e "${RED}Error: Task file not found: $TASK_FILE${NC}"
    return 1
  fi

  # Build objective with context
  local objective="$task_content"
  if [[ -n "$context_override" ]]; then
    objective="$objective\n\nAdditional Context: $context_override"
  fi

  # Execute swarm with development strategy and parallel execution
  npx claude-flow@alpha swarm "$objective" \
    --strategy development \
    --parallel \
    --max-agents 5 \
    --claude

  return $?
}

# Function to run Phase 2
run_phase2() {
  echo -e "${GREEN}Running Phase 2: System Verification${NC}"
  echo ""

  local phase2_failed=false

  # Step 1: Backend startup check
  echo -e "${BLUE}[Step 1/3] Starting Tauri backend...${NC}"
  echo -e "${YELLOW}Running: mise start${NC}"
  echo -e "${YELLOW}Watching for 'Accepted new IPC connection' message...${NC}"

  # Start backend in background
  mise start > /tmp/intelliforia-backend.log 2>&1 &
  local backend_pid=$!

  # Watch logs for success indicator (timeout after 30 seconds)
  local timeout=30
  local elapsed=0
  local backend_started=false

  while [[ $elapsed -lt $timeout ]]; do
    if grep -q "Accepted new IPC connection" /tmp/intelliforia-backend.log 2>/dev/null; then
      backend_started=true
      echo -e "${GREEN}✓ Backend started successfully${NC}"
      break
    fi

    if grep -qi "error\|compilation failed" /tmp/intelliforia-backend.log 2>/dev/null; then
      echo -e "${RED}✗ Backend compilation errors detected${NC}"
      cat /tmp/intelliforia-backend.log
      phase2_failed=true
      break
    fi

    sleep 1
    elapsed=$((elapsed + 1))
  done

  if [[ "$backend_started" == "false" && "$phase2_failed" == "false" ]]; then
    echo -e "${RED}✗ Backend startup timed out (no 'Accepted IPC' message within ${timeout}s)${NC}"
    echo -e "${YELLOW}Backend logs:${NC}"
    cat /tmp/intelliforia-backend.log
    phase2_failed=true
  fi

  if [[ "$phase2_failed" == "true" ]]; then
    return 1
  fi

  echo ""

  # Step 2: Extension build check
  echo -e "${BLUE}[Step 2/3] Building Chrome extension...${NC}"
  echo -e "${YELLOW}Running: cd extensions/chrome && bun run build${NC}"

  cd extensions/chrome
  if ! bun run build; then
    echo -e "${RED}✗ Extension build failed${NC}"
    cd ../..
    return 1
  fi
  cd ../..

  # Verify dist files exist
  local required_files=(
    "extensions/chrome/dist/manifest.json"
    "extensions/chrome/dist/background.js"
    "extensions/chrome/dist/content/session-notes-bundle.js"
  )

  for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
      echo -e "${RED}✗ Required file missing: $file${NC}"
      return 1
    fi
  done

  echo -e "${GREEN}✓ Extension built successfully${NC}"
  echo ""

  # Step 3: Manual verification reminder
  echo -e "${BLUE}[Step 3/3] Manual Verification Required${NC}"
  echo -e "${YELLOW}Please complete these steps:${NC}"
  echo "  1. Open chrome://extensions in Chrome"
  echo "  2. Enable 'Developer mode' (top right)"
  echo "  3. Find 'IntelliForia' extension"
  echo "  4. Click 'Reload' button"
  echo "  5. Test on target page (Salesforce/EMR)"
  echo ""
  echo -e "${YELLOW}Press Enter when verification is complete, or Ctrl+C to abort...${NC}"
  read -r

  echo -e "${GREEN}✓ Phase 2 verification complete${NC}"
  return 0
}

# Execute workflow based on phase
case "$PHASE" in
  1)
    run_phase1 1
    ;;

  2)
    run_phase2
    ;;

  all|*)
    echo -e "${GREEN}Running Full Workflow (Phase 1 + Phase 2)${NC}"

    # Retry loop
    ATTEMPT=1
    PHASE1_SUCCESS=false
    PHASE2_SUCCESS=false

    while [[ $ATTEMPT -le $((MAX_RETRIES + 1)) ]]; do
      echo ""
      echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
      echo -e "${YELLOW}Workflow Attempt ${ATTEMPT}/$((MAX_RETRIES + 1))${NC}"
      echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

      # Phase 1
      echo ""
      echo -e "${YELLOW}[Phase 1/2] Implementation Kickoff${NC}"

      # On retry, add Phase 2 failure context
      RETRY_CONTEXT="$CONTEXT"
      if [[ $ATTEMPT -gt 1 ]]; then
        RETRY_CONTEXT="$CONTEXT | RETRY: Previous Phase 2 verification failed. Review verification logs and address failures."
      fi

      run_phase1 $ATTEMPT "$RETRY_CONTEXT"
      PHASE1_EXIT=$?

      if [[ $PHASE1_EXIT -ne 0 ]]; then
        echo -e "${RED}Phase 1 failed with exit code $PHASE1_EXIT${NC}"

        if [[ "$RETRY_ENABLED" == "false" || $ATTEMPT -gt $MAX_RETRIES ]]; then
          echo -e "${RED}No more retries available. Exiting.${NC}"
          exit $PHASE1_EXIT
        fi

        echo -e "${YELLOW}Retrying Phase 1...${NC}"
        ATTEMPT=$((ATTEMPT + 1))
        continue
      fi

      PHASE1_SUCCESS=true
      echo -e "${GREEN}✓ Phase 1 completed successfully${NC}"

      # Check if verification should be skipped
      if [[ "$SKIP_VERIFICATION" == "true" ]]; then
        echo -e "${YELLOW}Skipping Phase 2 (verification) as requested${NC}"
        exit 0
      fi

      # Phase 2
      echo ""
      echo -e "${YELLOW}[Phase 2/2] System Verification${NC}"

      run_phase2
      PHASE2_EXIT=$?

      if [[ $PHASE2_EXIT -ne 0 ]]; then
        echo -e "${RED}Phase 2 failed with exit code $PHASE2_EXIT${NC}"

        if [[ "$RETRY_ENABLED" == "false" ]]; then
          echo -e "${RED}Retry disabled. Exiting.${NC}"
          exit $PHASE2_EXIT
        fi

        if [[ $ATTEMPT -ge $((MAX_RETRIES + 1)) ]]; then
          echo -e "${RED}Max retry attempts (${MAX_RETRIES}) reached. Exiting.${NC}"
          echo ""
          echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
          echo -e "${YELLOW}Retry Summary:${NC}"
          echo -e "  Total attempts: $ATTEMPT"
          echo -e "  Phase 1 status: ${GREEN}✓ Success${NC}"
          echo -e "  Phase 2 status: ${RED}✗ Failed${NC}"
          echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
          echo ""
          echo -e "${BLUE}Next steps:${NC}"
          echo "  1. Review Phase 2 verification logs in docs/threads/"
          echo "  2. Manually investigate backend/extension failures"
          echo "  3. Run Phase 2 only: $0 --phase 2"
          echo "  4. Or increase retries: $0 --task TASK.md --max-retries 5"
          exit $PHASE2_EXIT
        fi

        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}Phase 2 Verification Failed - Triggering Retry${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${YELLOW}Looping back to Phase 1 with failure context...${NC}"
        echo -e "${YELLOW}Will incorporate Phase 2 feedback in next implementation${NC}"

        ATTEMPT=$((ATTEMPT + 1))
        sleep 2  # Brief pause before retry
        continue
      fi

      # Both phases succeeded
      PHASE2_SUCCESS=true
      echo -e "${GREEN}✓ Phase 2 completed successfully${NC}"
      break
    done

    # Final status
    if [[ "$PHASE1_SUCCESS" == "true" && "$PHASE2_SUCCESS" == "true" ]]; then
      echo ""
      echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
      echo -e "${GREEN}✅ Workflow completed successfully${NC}"
      echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
      echo ""
      echo "Reports generated in: ${PROJECT_ROOT}/docs/threads/"

      if [[ $ATTEMPT -gt 1 ]]; then
        echo ""
        echo -e "${BLUE}Note: Success achieved after $((ATTEMPT - 1)) retry attempt(s)${NC}"
      fi

      exit 0
    fi
    ;;
esac

echo ""
echo -e "${GREEN}✅ Workflow completed successfully${NC}"
echo "Reports generated in: ${PROJECT_ROOT}/docs/threads/"
