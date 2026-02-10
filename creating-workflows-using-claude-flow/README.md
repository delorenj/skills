# Creating Workflows Skill

**Version**: 1.0.0
**Created**: 2025-10-28
**Maintainer**: Jarad DeLorenzo

Comprehensive skill for building automated multi-phase development workflows using claude-flow orchestration, multi-agent coordination, and intelligent verification systems.

---

## Quick Start

### 1. Copy Template

```bash
cp ~/.claude/skills/creating-workflows/assets/workflow-script-template.sh ./my-workflow.sh
chmod +x ./my-workflow.sh
```

### 2. Customize Phases

Edit `my-workflow.sh`:
- Modify `run_phase1()` with your implementation logic
- Modify `run_phase2()` with your verification steps
- Update CLI help text and workflow name

### 3. Test Dry-Run

```bash
./my-workflow.sh --dry-run
```

### 4. Run Workflow

```bash
./my-workflow.sh --task TASK.md
```

---

## What's Included

### SKILL.md
Comprehensive patterns, best practices, and examples for:
- Multi-phase workflow architecture
- Retry loops with context injection
- Silent failure detection
- Claude-flow integration
- Documentation patterns
- Testing strategies

### Reference Documentation

**references/**:
- `claude-flow-commands.md` - Complete CLI reference for claude-flow v2.7.26+
- `silent-failure-detection.md` - Patterns for detecting false-positive successes
- `retry-patterns.md` - Intelligent retry loop implementations

### Templates

**assets/**:
- `workflow-script-template.sh` - Complete working example from intelliForia-iterate

---

## Core Concepts

### Multi-Phase Workflows

**Phase 1 (Kickoff)**: Implementation via multi-agent orchestration
- Uses `claude-flow swarm` with development strategy
- Spawns up to 5 parallel agents
- Opens Claude Code CLI for implementation
- Reads TASK.md for requirements

**Phase 2 (Verification)**: System state validation
- Backend/service startup monitoring
- Artifact building and validation
- Manual verification prompts
- Log pattern matching for silent failures

**Phase N**: Add additional phases as needed
- Testing, deployment, rollback, etc.

### Retry Loops

When Phase 2 fails, automatically retry Phase 1 with enhanced context:
- Appends specific failure details
- Includes log paths and error excerpts
- Enforces configurable max retry limit (default: 2)
- Provides comprehensive failure summary on exhaustion

### Silent Failure Detection

Process managers often return success despite actual failures:
- **Problem**: `mise start`, `docker-compose up`, etc. exit 0 on failure
- **Solution**: Monitor logs for explicit success patterns
- **Example**: Wait for "Accepted new IPC connection" message

---

## Common Use Cases

### 1. Feature Implementation Workflow

```bash
# Phase 1: Multi-agent implementation
# Phase 2: Backend start + Extension build + Manual testing
./feature-workflow.sh --task FEATURE.md
```

### 2. Refactoring Workflow

```bash
# Phase 1: Research + Design + Refactor
# Phase 2: Test suite + Smoke tests + Performance checks
./refactor-workflow.sh --task REFACTOR.md
```

### 3. Deployment Workflow

```bash
# Phase 1: Build artifacts + Run tests
# Phase 2: Deploy to staging + Health checks + Smoke tests
./deploy-workflow.sh --environment staging
```

---

## Key Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Complete patterns and best practices |
| `references/claude-flow-commands.md` | CLI command reference |
| `references/silent-failure-detection.md` | Failure detection patterns |
| `references/retry-patterns.md` | Retry loop implementations |
| `assets/workflow-script-template.sh` | Working example script |

---

## Prerequisites

### Required

- **claude-flow@alpha** v2.7.26+
  ```bash
  npm install -g claude-flow@alpha
  npx claude-flow@alpha --version
  ```

- **Bash** 4.0+ with `set -euo pipefail`

- **jq** (for JSON parsing in advanced patterns)
  ```bash
  brew install jq  # macOS
  apt install jq   # Linux
  ```

### Optional

- **mise** (if using mise task runner patterns)
- **Docker** (if using container patterns)
- **PostgreSQL** (if using database patterns)

---

## Workflow Structure

### Minimal Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Phase 1
run_phase1() {
  echo -e "${GREEN}Phase 1: Implementation${NC}"
  npx claude-flow@alpha swarm "$(cat TASK.md)" \
    --strategy development \
    --claude
}

# Phase 2
run_phase2() {
  echo -e "${GREEN}Phase 2: Verification${NC}"
  # Add your verification steps
}

# Execute
run_phase1 && run_phase2
```

### Full-Featured Script

See `assets/workflow-script-template.sh` for complete example with:
- CLI argument parsing
- Retry loop with context injection
- Silent failure detection
- Dry-run mode
- Comprehensive error handling
- Actionable failure summaries

---

## Documentation Standards

Every workflow should include:

### 1. Overview Document (`workflow-name.md`)
- Purpose and use cases
- Phase descriptions
- Trigger instructions
- Input/output specifications
- Failure recovery patterns

### 2. Quick Reference (`QUICK-REFERENCE.md`)
- Common commands
- CLI flags
- Output locations
- Troubleshooting commands

### 3. README (if in workflows directory)
- List all available workflows
- Quick start for each
- Links to detailed docs

---

## Testing Workflows

### 1. Dry-Run

```bash
./workflow.sh --dry-run
# Should show commands without executing
```

### 2. Individual Phases

```bash
./workflow.sh --phase 1  # Test Phase 1 only
./workflow.sh --phase 2  # Test Phase 2 only
```

### 3. Retry Behavior

```bash
# Intentionally fail Phase 2
# Verify:
# - Phase 1 re-executes with failure context
# - Max retries enforced
# - Failure summary appears
```

### 4. Failure Detection

```bash
# Introduce compilation error
# Verify workflow detects it within timeout
# Verify error logs are shown
```

---

## Integration with Claude-Flow

### Available Commands (v2.7.26+)

**DO NOT USE**: `workflow execute` (doesn't exist)

**USE INSTEAD**:
- `swarm <objective>` - Multi-agent coordination
- `sparc <mode>` - SPARC methodology phases
- `stream-chain` - Sequential context preservation

See `references/claude-flow-commands.md` for complete reference.

---

## Best Practices

1. **Always Include Dry-Run Mode**
   - Users should preview execution
   - Shows exact commands without running

2. **Test Failure Scenarios**
   - Intentionally break builds/services
   - Verify detection works
   - Ensure error messages are helpful

3. **Provide Actionable Next Steps**
   - Include log paths
   - Show troubleshooting commands
   - Link to support channels

4. **Document Everything**
   - Overview document
   - Quick reference
   - Inline script comments

5. **Use Retry Loops Wisely**
   - Default: 2 retries (3 total attempts)
   - Always inject failure context
   - Allow users to disable with --no-retry

---

## Support

### Questions?

- Open issue: https://github.com/ruvnet/claude-flow/issues
- Review skill documentation: `~/.claude/skills/creating-workflows/SKILL.md`
- Check reference docs: `~/.claude/skills/creating-workflows/references/`

### Contributing

Found a better pattern? Discovered a new pitfall?

Submit improvements to the skill maintainer.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-28 | Initial skill creation from intelliForia-iterate workflow |

---

## License

This skill is provided as-is for use in Claude Code development workflows.

---

**Last Updated**: 2025-10-28
**Maintainer**: Jarad DeLorenzo
