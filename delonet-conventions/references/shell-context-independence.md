---
pipeline-status:
  - new
---
# Shell Context Independence Pattern

## Problem Statement

Shell aliases and functions don't propagate to subprocess environments (cron jobs, systemd services, scripts executed via automation tools, etc.). Commands that work interactively fail with "command not found" when executed from automation contexts.

## Core Pattern: Self-Contained Scripts

### Architecture Principles

1. **No Shell Context Dependencies**: Scripts must not rely on user's interactive shell configuration
2. **Explicit PATH Management**: All required executables must be findable via explicit PATH configuration
3. **Absolute Paths**: Use absolute paths for all file operations and critical executables
4. **Detached Execution with Observability**: Long-running operations should spawn detached sessions with connection info returned immediately

### Basic Shell Script Structure

```bash
#!/bin/zsh
set -euo pipefail

# Explicit PATH configuration (no reliance on user's shell config)
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Configuration
PARAM1="${1:-}"
PARAM2="${2:-default-value}"

if [[ -z "$PARAM1" ]]; then
    echo "Error: Required parameter missing"
    echo "Usage: $(basename $0) <param1> [param2]"
    exit 1
fi

# Main logic using explicit commands, not aliases
some-explicit-command "$PARAM1"
```

### Key Rules

1. **Never use aliases**: They don't export to subprocesses
2. **Replace alias references with actual commands**: `dcu` becomes `docker compose up -d`, `mr` becomes `mise run`
3. **Export PATH explicitly**: Include all custom binary directories
4. **Use functions over aliases**: Functions can be exported (bash) or are available by default (zsh)

## Zellij Integration Pattern

**Problem:** Automation returns immediately but you need to observe long-running operations.

**Solution:** Detached Zellij sessions with unique identifiers.

### Implementation

```bash
#!/bin/zsh
set -euo pipefail

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

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

echo "Workflow: $TASK_ID"
echo "Session: $ZELLIJ_SESSION_NAME"

# Step 1: Navigate to target directory
cd "$HOME/code/$TASK_ID"

# Step 2: Run mise tasks (explicit, not alias)
mise run build

# Step 3: Execute main workflow
mise run test

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "Workflow completed"
else
    echo "Workflow failed: $EXIT_CODE"
fi
echo "Session: $ZELLIJ_SESSION_NAME"

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
    echo "Workflow launched in background"
    echo "Task: $TASK_ID"
    echo "Session: $SESSION_NAME"
    echo "To attach: zellij attach $SESSION_NAME"

    exit 0
fi

# Foreground mode - run directly
echo "Running in foreground..."
# ... direct execution logic
```

## Benefits

1. **Portability**: Works in any execution context (interactive, cron, systemd, automation)
2. **Observability**: Full terminal output available via Zellij attachment
3. **Non-blocking**: Automation workflows get immediate response
4. **Debuggable**: Can attach to live session to watch progress
5. **Persistent**: Session survives even if caller terminates
6. **Traceable**: Timestamped session names provide audit trail

## Real-World Example: Build and Deploy Workflow

### Before (Broken in automation)

```bash
# Relies on shell functions/aliases
cd $CODE/myapp && dcu && mr deploy
```

**Failures:**
- `$CODE`: environment variable not set in subprocess
- `dcu`: alias not found in subprocess
- `mr`: alias not found in subprocess
- No observability of long-running deploy process

### After (Works Everywhere)

```bash
#!/bin/zsh
# ~/.local/bin/deploy-app
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
export CODE="$HOME/code"

APP_NAME="${1:-myapp}"
SESSION_NAME="deploy-${APP_NAME}-$(date +%Y%m%d-%H%M%S)"

# Navigate using explicit path
cd "$CODE/$APP_NAME"

# Use explicit commands, not aliases
docker compose up -d
mise run deploy
```

**Wins:**
- Works in cron jobs
- Works in systemd services
- Works in any automation context
- Returns immediately with session name
- Full observability via Zellij

## Common Transformations

### Alias to Explicit Command

```bash
# Before (alias)
dcu

# After (explicit)
docker compose up -d
```

### Function Wrapper to Direct Invocation

```bash
# Before (function that wraps cd)
code myapp

# After (direct)
cd "$HOME/code/myapp"
```

### Mise Alias to Explicit

```bash
# Before
mr test

# After
mise run test
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

**Install location:** `~/.local/bin/` (already in most PATH configurations)

**Benefits:**
- Available to all users without shell config
- Standard location for user-installed scripts
- Automatically in PATH for most shells
- Consistent with FHS (Filesystem Hierarchy Standard)

## Testing Strategy

1. **Test in subprocess context** (mimics automation):
```bash
bash -c "deploy-app myapp"
```

2. **Test with empty environment**:
```bash
env -i HOME=$HOME PATH=/usr/bin:/bin deploy-app myapp
```

3. **Test detached mode**:
```bash
deploy-app myapp
zellij list-sessions  # Should show new session
zellij attach <session-name>  # Should attach successfully
```

## Anti-Patterns to Avoid

- Don't rely on `.zshrc` or `.bashrc` being sourced
- Don't use `alias` for commands that need to work in automation
- Don't assume parent shell context will be available
- Don't use relative paths for critical files
- Don't inline complex multi-line strings with nested quotes

Always:
- Export PATH explicitly in scripts
- Use functions instead of aliases (and export them if needed)
- Use absolute paths for files and executables
- Store complex prompts in files
- Spawn detached sessions for long-running operations
- Return connection info immediately for observability

## Related Patterns

- **Command Pattern**: Each script encapsulates a complete operation
- **Task Orchestration**: Mise tasks wrap scripts for consistent invocation
- **Detached Execution**: Background operations with observability hooks

## See Also

- `/home/delorenj/.config/zshyzsh/aliases.zsh` - Current alias definitions
- `/home/delorenj/.local/bin/` - Self-contained scripts directory
