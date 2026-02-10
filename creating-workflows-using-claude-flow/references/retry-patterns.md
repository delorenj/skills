# Retry Loop Patterns for Workflows

**Problem**: Phase 2 verification failures often indicate issues in Phase 1 implementation that can be fixed with additional context.

**Solution**: Implement intelligent retry loops that feed failure information back to Phase 1.

---

## Core Retry Pattern

### Basic Structure

```bash
ATTEMPT=1
MAX_RETRIES=2  # Total attempts = 1 initial + 2 retries = 3
RETRY_ENABLED=true

while [[ $ATTEMPT -le $((MAX_RETRIES + 1)) ]]; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Workflow Attempt ${ATTEMPT}/$((MAX_RETRIES + 1))"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Phase 1 (with context injection on retry)
  if ! run_phase1 $ATTEMPT; then
    handle_phase1_failure
    continue
  fi

  # Phase 2
  if ! run_phase2; then
    if [[ $ATTEMPT -ge $((MAX_RETRIES + 1)) ]]; then
      handle_exhausted_retries
      exit 1
    fi

    echo "Phase 2 failed - Looping back to Phase 1 with failure context"
    ATTEMPT=$((ATTEMPT + 1))
    sleep 2  # Brief pause before retry
    continue
  fi

  # Success
  echo "✅ Workflow completed successfully"
  break
done
```

---

## Context Injection

### Pattern 1: Append Failure Details

**Problem**: Retries repeat identical failures without additional information.

**Solution**: Inject failure details into Phase 1 context.

```bash
run_phase1() {
  local attempt=$1
  local context_override="${2:-$CONTEXT}"

  # Build context for retry
  if [[ $attempt -gt 1 ]]; then
    context_override="$context_override | RETRY ATTEMPT $((attempt - 1)): Previous Phase 2 verification failed. Review verification logs at /tmp/phase2.log and address these failures."
  fi

  # Pass enhanced context to implementation
  npx claude-flow@alpha swarm "$task_content\n\nContext: $context_override" \
    --strategy development \
    --claude
}
```

### Pattern 2: Structured Failure Context

**Advanced**: Create structured failure information.

```bash
run_phase1() {
  local attempt=$1

  if [[ $attempt -gt 1 ]]; then
    local failure_context=$(cat <<EOF
━━━ RETRY CONTEXT ━━━
Attempt: $((attempt - 1))/$MAX_RETRIES
Previous Failure: Phase 2 verification
Failed At: $(date -Iseconds)

Specific Issues:
$PHASE2_FAILURE_DETAILS

Logs:
- Backend: /tmp/backend.log
- Extension Build: /tmp/extension-build.log
- Verification: /tmp/verification.log

Action Required:
Review the above logs and address the specific issues identified.
━━━━━━━━━━━━━━━━━━━━━
EOF
)

    context_override="$CONTEXT\n\n$failure_context"
  fi

  # Pass to swarm
  npx claude-flow@alpha swarm "$task_content\n\n$context_override" --claude
}
```

### Pattern 3: Capture Specific Failures

**Best**: Extract specific error messages from Phase 2.

```bash
run_phase2() {
  # Clear previous failure details
  PHASE2_FAILURE_DETAILS=""

  # Backend startup check
  if ! start_backend; then
    PHASE2_FAILURE_DETAILS+="- Backend failed to start: $(tail -5 /tmp/backend.log | head -3)\n"
    return 1
  fi

  # Extension build check
  if ! build_extension; then
    PHASE2_FAILURE_DETAILS+="- Extension build failed: $(tail -5 /tmp/extension-build.log | head -3)\n"
    return 1
  fi

  # Smoke tests
  if ! run_smoke_tests; then
    PHASE2_FAILURE_DETAILS+="- Smoke tests failed: $(tail -5 /tmp/smoke-tests.log | head -3)\n"
    return 1
  fi

  return 0
}

# In retry context injection:
if [[ -n "$PHASE2_FAILURE_DETAILS" ]]; then
  context_override="$CONTEXT\n\nPhase 2 Failures:\n$PHASE2_FAILURE_DETAILS"
fi
```

---

## Retry Limits

### Pattern 1: Configurable Max Retries

```bash
# CLI flag parsing
while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--max-retries)
      MAX_RETRIES="$2"
      shift 2
      ;;
    --no-retry)
      RETRY_ENABLED=false
      shift
      ;;
  esac
done

# In retry loop
if [[ "$RETRY_ENABLED" == "false" ]]; then
  echo "Retry disabled - exiting on first failure"
  exit 1
fi

if [[ $ATTEMPT -gt $MAX_RETRIES ]]; then
  echo "Max retry attempts ($MAX_RETRIES) reached"
  exit 1
fi
```

### Pattern 2: Progressive Timeouts

**Advanced**: Increase timeout on each retry.

```bash
get_timeout_for_attempt() {
  local attempt=$1
  local base_timeout=30

  # Increase timeout by 50% on each retry
  echo $((base_timeout + (attempt - 1) * 15))
}

# In Phase 2
timeout=$(get_timeout_for_attempt $ATTEMPT)
echo "Using timeout: ${timeout}s for attempt $ATTEMPT"
```

### Pattern 3: Exponential Backoff

**Production**: Add increasing delays between retries.

```bash
get_backoff_delay() {
  local attempt=$1

  # 2^attempt seconds (2s, 4s, 8s, 16s, ...)
  # Capped at 30s
  local delay=$((2 ** attempt))
  if [[ $delay -gt 30 ]]; then
    delay=30
  fi

  echo $delay
}

# Before retry
delay=$(get_backoff_delay $ATTEMPT)
echo "Waiting ${delay}s before retry..."
sleep $delay
```

---

## Failure Summary

### Pattern 1: Basic Summary

```bash
handle_exhausted_retries() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Retry Summary:"
  echo "  Total attempts: $ATTEMPT"
  echo "  Phase 1 status: ✓ Success"
  echo "  Phase 2 status: ✗ Failed"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}
```

### Pattern 2: Actionable Next Steps

```bash
handle_exhausted_retries() {
  cat <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 Max Retry Attempts Exhausted
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Attempts: $ATTEMPT
Phase 1: ✓ Implementation succeeded
Phase 2: ✗ Verification failed

━━━ Next Steps ━━━

1. 🔍 Review Logs
   - Backend: tail -f /tmp/backend.log
   - Extension: tail -f /tmp/extension-build.log
   - Verification: cat /tmp/verification.log

2. 🧪 Manual Investigation
   - Check backend status: ps aux | grep backend
   - Verify extension: ls -la extensions/chrome/dist/
   - Test manually: open chrome://extensions

3. 🔄 Retry Options
   - Run Phase 2 only: $0 --phase 2
   - Increase retries: $0 --max-retries 5
   - Disable retry: $0 --no-retry

4. 📞 Get Help
   - File issue: https://github.com/org/repo/issues
   - Slack channel: #dev-support
   - On-call: Check PagerDuty rotation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
}
```

### Pattern 3: Detailed Failure History

```bash
# Track failures throughout workflow
declare -a FAILURE_HISTORY=()

record_failure() {
  local phase=$1
  local attempt=$2
  local reason=$3

  FAILURE_HISTORY+=("Attempt $attempt - Phase $phase: $reason")
}

# Usage in phases
run_phase2() {
  if ! start_backend; then
    record_failure 2 $ATTEMPT "Backend failed to start"
    return 1
  fi
  # ...
}

# In summary
handle_exhausted_retries() {
  echo "Failure History:"
  for failure in "${FAILURE_HISTORY[@]}"; do
    echo "  - $failure"
  done
}
```

---

## Phase-Specific Retry Strategies

### Strategy 1: Only Retry Phase 2 Failures

```bash
# Phase 1 failures don't retry
run_phase1() {
  if ! execute_phase1; then
    echo "✗ Phase 1 failed - implementation error"
    exit 1  # Don't retry Phase 1 failures
  fi
}

# Phase 2 failures trigger Phase 1 retry
run_phase2() {
  if ! execute_phase2; then
    if [[ $ATTEMPT -lt $((MAX_RETRIES + 1)) ]]; then
      echo "Phase 2 failed - will retry Phase 1 with failure context"
      return 1  # Trigger retry loop
    else
      echo "Max retries exhausted"
      exit 1
    fi
  fi
}
```

### Strategy 2: Selective Retry Based on Failure Type

```bash
run_phase2() {
  local failure_type=""

  if ! start_backend; then
    failure_type="backend_startup"
  elif ! build_extension; then
    failure_type="extension_build"
  elif ! run_tests; then
    failure_type="test_failure"
  fi

  # Only retry for specific failure types
  case "$failure_type" in
    backend_startup|extension_build)
      echo "Retryable failure: $failure_type"
      return 1  # Trigger retry
      ;;
    test_failure)
      echo "Non-retryable failure: $failure_type"
      echo "Fix tests manually before proceeding"
      exit 1  # Don't retry
      ;;
  esac
}
```

### Strategy 3: Checkpoint Recovery

```bash
# Save state between phases
save_checkpoint() {
  local phase=$1
  cat > /tmp/workflow-checkpoint.json <<EOF
{
  "phase": $phase,
  "attempt": $ATTEMPT,
  "timestamp": "$(date -Iseconds)",
  "context": "$CONTEXT"
}
EOF
}

# Restore from checkpoint
restore_checkpoint() {
  if [[ -f /tmp/workflow-checkpoint.json ]]; then
    local last_phase=$(jq -r '.phase' /tmp/workflow-checkpoint.json)
    local last_attempt=$(jq -r '.attempt' /tmp/workflow-checkpoint.json)

    echo "Found checkpoint: Phase $last_phase, Attempt $last_attempt"
    echo "Resume from here? (y/n)"
    read -r resume

    if [[ "$resume" == "y" ]]; then
      ATTEMPT=$last_attempt
      # Skip to failed phase
    fi
  fi
}

# Usage
run_phase1() {
  # ... execute phase 1 ...
  save_checkpoint 1
}

run_phase2() {
  # ... execute phase 2 ...
  save_checkpoint 2
}
```

---

## Testing Retry Behavior

### Test 1: Verify Context Injection

```bash
# In Phase 1, log the context received
run_phase1() {
  echo "Phase 1 Context:" >> /tmp/phase1-contexts.log
  echo "$context_override" >> /tmp/phase1-contexts.log
  echo "---" >> /tmp/phase1-contexts.log
}

# After workflow with failures
cat /tmp/phase1-contexts.log

# Expected: First attempt has base context only
# Expected: Second attempt includes "RETRY: Previous Phase 2..."
# Expected: Third attempt includes more details
```

### Test 2: Verify Retry Count

```bash
# Intentionally fail Phase 2
run_phase2() {
  return 1  # Always fail
}

# Run workflow
./workflow.sh --max-retries 2

# Expected: Exactly 3 total attempts
# Expected: "Max retry attempts (2) reached" message
# Expected: Exit code 1
```

### Test 3: Verify No-Retry Flag

```bash
# Run with --no-retry
./workflow.sh --no-retry

# Expected: Single attempt only
# Expected: Immediate exit on Phase 2 failure
# Expected: No "Looping back to Phase 1" message
```

---

## Best Practices

1. **Always Inject Context**
   - Never retry blindly
   - Provide specific failure information
   - Include log paths and error excerpts

2. **Reasonable Retry Limits**
   - Default: 2 retries (3 total attempts)
   - Max: 5 retries for production
   - Allow users to disable retry

3. **Progressive Delays**
   - Add 2-5 second delays between retries
   - Prevents overwhelming systems
   - Gives transient failures time to resolve

4. **Comprehensive Summaries**
   - Show total attempts made
   - List specific failures
   - Provide actionable next steps
   - Include support contact info

5. **Test Retry Behavior**
   - Intentionally fail phases
   - Verify context injection works
   - Ensure retry limits are enforced
   - Check delay timing

---

## Common Pitfalls

### Pitfall 1: Infinite Loops

**Problem**: Missing max retry check

**Solution**:
```bash
# Always enforce max retries
if [[ $ATTEMPT -gt $((MAX_RETRIES + 1)) ]]; then
  echo "Max retries exhausted"
  exit 1
fi
```

### Pitfall 2: No Context Injection

**Problem**: Retries repeat identical failures

**Solution**: Always inject failure context (see patterns above)

### Pitfall 3: Unclear Failure Messages

**Problem**: User doesn't know what to do next

**Solution**: Provide specific next steps and log locations

### Pitfall 4: Phase 1 Retry on Phase 1 Failure

**Problem**: Retrying Phase 1 when Phase 1 itself failed

**Solution**: Only retry Phase 1 when Phase 2 fails

```bash
if ! run_phase1; then
  # Phase 1 failed - don't retry
  echo "Phase 1 failed - fix implementation"
  exit 1
fi

if ! run_phase2; then
  # Phase 2 failed - retry Phase 1
  ATTEMPT=$((ATTEMPT + 1))
  continue
fi
```

---

**Reference Version**: 1.0.0
**Maintainer**: Jarad DeLorenzo
**Last Updated**: 2025-10-28
