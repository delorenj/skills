# Shell Context Independence Pattern

## Problem Statement

**Root Cause**: Shell aliases and functions don't propagate to subprocess environments (n8n workflows, cron jobs, systemd services, scripts executed via Bash tool, etc.)

**Failure Mode**: Commands that work interactively fail with "command not found" when executed from automation contexts.

## Core Pattern: Self-Contained Scripts

### Architecture Principles

1. **No Shell Context Dependencies**: Scripts must not rely on user's interactive shell configuration
2. **Explicit PATH Management**: All required executables must be findable via explicit PATH configuration
3. **Absolute Paths**: Use absolute paths for all file operations and critical executables
4. **Detached Execution with Observability**: Long-running operations should spawn detached sessions with connection info returned immediately

## Implementation Pattern

### Basic Shell Script Structure

```bash
#!/bin/zsh
# self-contained-script.sh
set -euo pipefail

# Explicit PATH configuration (no reliance on user's shell config)
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Configuration
PARAM1="${1:-}"
PARAM2="${2:-default-value}"

if [[ -z "$PARAM1" ]]; then
    echo "❌ Error: Required parameter missing"
    echo "Usage: $(basename $0) <param1> [param2]"
    exit 1
fi

# Main logic using explicit commands, not aliases
some-explicit-command "$PARAM1"
```

### Key Rules

1. **Never use aliases**: They don't export to subprocesses
2. **Replace alias references with actual commands**: `imi` becomes `iMi`, `cfi` becomes the actual `npx claude-flow@alpha init` invocation
3. **Export PATH explicitly**: Include all custom binary directories
4. **Use functions over aliases**: Functions can be exported (bash) or are available by default (zsh)

## Zellij Integration Pattern

**Problem**: Automation returns immediately but you need to observe long-running operations.

**Solution**: Detached Zellij sessions with unique identifiers.

### Implementation

```bash
#!/bin/zsh
# workflow-with-observability.sh
set -euo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Configuration
TASK_ID="${1:-}"
RUN_MODE="${2:-detached}"  # detached or foreground

# Generate unique session name with timestamp
SESSION_NAME="workflow-${TASK_ID}-$(date +%Y%m%d-%H%M%S)"

if [[ "$RUN_MODE" == "detached" ]]; then
    # Create temp script with workflow logic
    TEMP_SCRIPT=$(mktemp)
    cat > "$TEMP_SCRIPT" << 'WORKFLOW'
#!/bin/zsh
set -euo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

TASK_ID="$1"

echo "🔍 Workflow: $TASK_ID"
echo "🖥️  Session: $ZELLIJ_SESSION_NAME"
echo ""

# Step 1: Navigate to target directory
TARGET_DIR=$(iMi go "$TASK_ID")
cd "$TARGET_DIR"

# Step 2: Initialize environment
npx claude-flow@alpha init --sparc --force

# Step 3: Execute main workflow
npx claude-flow@alpha swarm \
    "Execute task: $TASK_ID" \
    --strategy development \
    --parallel \
    --claude

EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ Workflow completed"
else
    echo "❌ Workflow failed: $EXIT_CODE"
fi
echo "Session: $ZELLIJ_SESSION_NAME"
echo "Press any key to close, or Ctrl+C to keep open..."
read -k1

exit $EXIT_CODE
WORKFLOW

    chmod +x "$TEMP_SCRIPT"

    # Launch detached Zellij session
    zellij --session "$SESSION_NAME" \
           options --default-shell zsh \
           -- "$TEMP_SCRIPT" "$TASK_ID" &

    sleep 0.5
    (sleep 2 && rm -f "$TEMP_SCRIPT") &

    # Return session info immediately
    echo "🚀 Workflow launched in background"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Task: $TASK_ID"
    echo "🖥️  Session: $SESSION_NAME"
    echo ""
    echo "To attach: zellij attach $SESSION_NAME"
    echo "To list: zellij list-sessions"

    exit 0
fi

# Foreground mode - run directly
echo "Running in foreground..."
# ... direct execution logic
```

## Benefits

1. **Portability**: Works in any execution context (interactive, n8n, cron, systemd)
2. **Observability**: Full terminal output available via Zellij attachment
3. **Non-blocking**: Automation workflows get immediate response
4. **Debuggable**: Can attach to live session to watch progress
5. **Persistent**: Session survives even if caller terminates
6. **Traceable**: Timestamped session names provide audit trail

## Real-World Example: PR Review Workflow

### Before (Broken in n8n)

```bash
# Relies on shell functions/aliases
igo pr-458 && cfi && npx claude-flow@alpha swarm "Review PR..." --claude
```

**Failures**:
- `igo`: function not found in subprocess
- `cfi`: function not found in subprocess
- No observability of long-running review process
- Quote escaping nightmare with complex prompts

### After (Works Everywhere)

```bash
# /home/delorenj/.local/bin/review-pr
#!/bin/zsh
set -euo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

PR_ID="${1:-}"
PROMPT_FILE="${2:-$HOME/code/DeLoDocs/AI/Agents/Generic/My Personal PR Review Representative.md}"

SESSION_NAME="pr-review-${PR_ID}-$(date +%Y%m%d-%H%M%S)"

# ... (Zellij detached session creation)

# Navigation: Direct iMi command (not alias)
TARGET_DIR=$(iMi go "$PR_ID")
cd "$TARGET_DIR"

# Init: Explicit npx command (not cfi alias)
npx claude-flow@alpha init --sparc --force

# Execute: Prompt from file (no quote escaping)
PROMPT_CONTENT=$(cat "$PROMPT_FILE")
npx claude-flow@alpha swarm \
    "Review this PR: $PROMPT_CONTENT" \
    --strategy development \
    --claude
```

**Wins**:
- ✅ Works in n8n Execute Command nodes
- ✅ Works in cron jobs
- ✅ Works in systemd services
- ✅ Returns immediately with session name
- ✅ Full observability via Zellij
- ✅ No quote escaping issues (prompt from file)

## Integration with n8n Workflows

### Execute Command Node

```javascript
{
  "command": "review-pr pr-458",
  "timeout": 5000  // Returns in ~1 second
}
```

### Parse Output Node

```javascript
const output = $('Execute Command').json.stdout;
const sessionMatch = output.match(/Session: ([\w-]+)/);
const sessionName = sessionMatch[1];

return {
  sessionName,
  attachCommand: `zellij attach ${sessionName}`,
  timestamp: new Date().toISOString()
};
```

### Follow-up Monitoring (Optional)

```javascript
// Check if session still exists
{
  "command": "zellij list-sessions | grep {{ $json.sessionName }}",
  "continueOnFail": true
}

// Attach to watch (blocks until complete)
{
  "command": "zellij attach {{ $json.sessionName }}"
}

// Kill if needed
{
  "command": "zellij kill-session {{ $json.sessionName }}"
}
```

## Common Transformations

### Alias to Explicit Command

```bash
# Before
cfi

# After
npx claude-flow@alpha init --sparc --force
npx claude mcp remove flow-nexus 2>/dev/null || true
npx claude mcp remove agentic-payments 2>/dev/null || true
```

### Function Wrapper to Direct Invocation

```bash
# Before
igo pr-458  # Function that calls iMi and cd's

# After
TARGET_DIR=$(iMi go pr-458)
cd "$TARGET_DIR"
```

### Complex Piped Commands

```bash
# Before (quote hell)
command "$(cat <<'EOF'
Complex
Multi-line
Prompt
EOF
)"

# After (file-based)
PROMPT=$(cat /path/to/prompt.md)
command "$PROMPT"
```

## File Location Pattern

**Install location**: `~/.local/bin/` (already in most PATH configurations)

**Benefits**:
- Available to all users without shell config
- Standard location for user-installed scripts
- Automatically in PATH for most shells
- Consistent with FHS (Filesystem Hierarchy Standard)

## Testing Strategy

1. **Test in subprocess context** (mimics n8n):
```bash
bash -c "review-pr pr-458"
```

2. **Test with empty environment**:
```bash
env -i HOME=$HOME PATH=/usr/bin:/bin review-pr pr-458
```

3. **Test detached mode**:
```bash
review-pr pr-458
zellij list-sessions  # Should show new session
zellij attach <session-name>  # Should attach successfully
```

## Anti-Patterns to Avoid

❌ **Don't**: Rely on `.zshrc` or `.bashrc` being sourced
❌ **Don't**: Use `alias` for commands that need to work in automation
❌ **Don't**: Assume parent shell context will be available
❌ **Don't**: Use relative paths for critical files
❌ **Don't**: Inline complex multi-line strings with nested quotes

✅ **Do**: Export PATH explicitly in scripts
✅ **Do**: Use functions instead of aliases (and export them if needed)
✅ **Do**: Use absolute paths for files and executables
✅ **Do**: Store complex prompts in files
✅ **Do**: Spawn detached sessions for long-running operations
✅ **Do**: Return connection info immediately for observability

## Related Patterns

- **Command Pattern**: Each script encapsulates a complete operation
- **Event-Driven Architecture**: Scripts publish events via Bloodbank when complete
- **Task Orchestration**: Mise tasks wrap scripts for consistent invocation
- **Detached Execution**: Background operations with observability hooks

## See Also

- `/home/delorenj/.config/zshyzsh/aliases.zsh` - Current alias definitions
- `/home/delorenj/.config/zshyzsh/claude-flow-helpers.zsh` - Shell functions
- `/home/delorenj/.local/bin/` - Self-contained scripts directory
- `ecosystem-patterns/SKILL.md` - General ecosystem patterns
- `creating-workflows/SKILL.md` - Multi-phase workflow automation
