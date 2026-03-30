# Task Levels Reference

# SSoT-OK

Comprehensive guide to mise task features, from basic definitions through advanced execution and watch mode.

## Level 1-2: Basic Tasks

### Minimal Task

```toml
[tasks.hello]
run = "echo 'Hello, World!'"
```

### With Description (AI-Agent Context Priming)

**CRITICAL**: The `description` field is the single most important field for AI coding agent discoverability. When an AI agent runs `mise tasks ls`, the description is the ONLY context it has to decide whether and how to use a task. Write descriptions that answer: **what does it do, what does it need, what are its side effects, and when should it be run?**

```toml
# BAD: Too minimal - AI agent has no context
[tasks.test]
description = "Run test suite"
run = "pytest tests/"

# GOOD: Rich context for AI agent decision-making
[tasks.test]
description = "Run pytest test suite against src/ with coverage reporting. Requires virtualenv activated or uv. Depends on build completing first. Exits non-zero on any test failure. Safe to run repeatedly."
run = "pytest tests/"
```

**Description checklist**:

- What it does (action + scope)
- What it requires (env vars, tools, prerequisites)
- What it produces or modifies (side effects, outputs)
- When to run it (phase context, safety notes)

```toml
# File-based task equivalent (in .mise/tasks/release/preflight):
#MISE description="Phase 1 of 4: Validate all release prerequisites before version bump. Checks: clean working directory, GH_TOKEN presence and format, GH_ACCOUNT target, plugin validation, and releasable conventional commits since last tag. Exits non-zero on any failure."
```

### With Alias

```toml
[tasks.test]
description = "Run pytest test suite with coverage. Requires virtualenv or uv. Exits non-zero on failure."
alias = "t"
run = "pytest tests/"
```

Now `mise run t` works.

### Working Directory

```toml
[tasks.frontend]
dir = "packages/frontend"
run = "npm run build"
```

### Task-Specific Environment

```toml
[tasks.test]
env = { RUST_BACKTRACE = "1", LOG_LEVEL = "debug" }
run = "cargo test"
```

**Note**: `env` values are NOT passed to dependency tasks.

### GitHub Token Verification Task

For multi-account GitHub setups, add a verification task:

```toml
[tasks._verify-gh-auth]
description = "Verify GitHub token matches expected account"
hide = true  # Hidden helper task
run = """
expected="${GH_ACCOUNT:-}"
if [ -z "$expected" ]; then
  echo "GH_ACCOUNT not set - skipping verification"
  exit 0
fi
actual=$(gh api user --jq '.login' 2>/dev/null || echo "")
if [ "$actual" != "$expected" ]; then
  echo "ERROR: GH_TOKEN authenticates as '$actual', expected '$expected'"
  exit 1
fi
echo "✓ GitHub auth verified: $actual"
"""

[tasks.release]
description = "Create semantic release"
depends = ["_verify-gh-auth"]  # Verify before release
run = "npx semantic-release --no-ci"
```

See [`mise-configuration` skill](../../mise-configuration/SKILL.md#github-token-multi-account-patterns) for GH_TOKEN setup.

> **SSH ControlMaster Warning**: If using multi-account SSH, ensure `ControlMaster no` is set for GitHub hosts in `~/.ssh/config`. Cached connections can authenticate with the wrong account.

### Multi-Command Tasks

```toml
[tasks.setup]
run = [
  "npm install",
  "npm run build",
  "npm run migrate"
]
```

---

## Level 3-4: Dependencies & Orchestration

### Pre-Execution Dependencies

```toml
[tasks.deploy]
depends = ["test", "build"]
run = "kubectl apply -f deployment.yaml"
```

Tasks `test` and `build` run BEFORE `deploy`.

### Post-Execution Tasks

```toml
[tasks.release]
depends = ["test"]
depends_post = ["notify", "cleanup"]
run = "npm publish"
```

After `release` succeeds, `notify` and `cleanup` run automatically.

### Soft Dependencies

```toml
[tasks.migrate]
wait_for = ["database"]
run = "./migrate.sh"
```

If `database` task is already running, wait for it. Otherwise, proceed.

### Task Chaining Pattern

```toml
[tasks.ci]
description = "Full CI pipeline"
depends = ["lint", "test", "build"]
depends_post = ["coverage-report"]
run = "echo 'CI passed'"
```

Single command: `mise run ci` executes entire chain.

### Parallel Dependencies

Dependencies without inter-dependencies run in parallel:

```toml
[tasks.validate]
depends = ["lint", "typecheck", "test"]  # These can run in parallel
run = "echo 'All validations passed'"
```

---

## Level 5: Hidden Tasks & Organization

### Hidden Tasks

```toml
[tasks._check-credentials]
description = "Verify credentials are set"
hide = true
run = '''
if [ -z "$API_KEY" ]; then
  echo "ERROR: API_KEY not set"
  exit 1
fi
'''

[tasks.deploy]
depends = ["_check-credentials"]
run = "deploy.sh"
```

Hidden tasks don't appear in `mise tasks` output but can be dependencies.

View hidden tasks: `mise tasks --hidden`

### Colon-Prefixed Namespacing

```toml
[tasks.test]
run = "pytest"

[tasks."test:unit"]
run = "pytest tests/unit/"

[tasks."test:integration"]
run = "pytest tests/integration/"

[tasks."test:e2e"]
run = "playwright test"
```

Run all test tasks: `mise run 'test:*'`

### Wildcard Patterns

```bash
mise run 'test:*'      # All tasks starting with test:
mise run 'db:**'       # Nested: db:migrate:up, db:seed:test
```

---

## Level 6: Task Arguments

### Usage Specification (Preferred Method)

```toml
[tasks.deploy]
description = "Deploy to environment"
usage = '''
arg "<environment>" help="Target environment" {
  choices "dev" "staging" "prod"
}
flag "-f --force" help="Skip confirmation"
flag "--region <region>" default="us-east-1" env="AWS_REGION"
'''
run = '''
echo "Deploying to ${usage_environment}"
[ "$usage_force" = "true" ] && echo "Force mode enabled"
echo "Region: ${usage_region}"
'''
```

### Argument Types

**Required positional**:

```toml
usage = 'arg "<file>" help="Input file"'
```

**Optional positional**:

```toml
usage = 'arg "[file]" default="config.toml"'
```

**Variadic (multiple values)**:

```toml
usage = 'arg "<files>" var=#true'
```

### Flag Types

**Boolean flag**:

```toml
usage = 'flag "-v --verbose"'
# Access: ${usage_verbose:-false}
```

**Flag with value**:

```toml
usage = 'flag "-o --output <file>" default="out.txt"'
# Access: ${usage_output}
```

**Environment-backed flag**:

```toml
usage = 'flag "--port <port>" env="PORT" default="8080"'
```

### Accessing Arguments

In `run` scripts, arguments become `usage_<name>` environment variables:

```bash
/usr/bin/env bash << 'SKILL_SCRIPT_EOF'
${usage_environment}      # Required arg value
${usage_verbose:-false}   # Boolean flag with default
${usage_output}           # Flag with value
SKILL_SCRIPT_EOF
```

**DEPRECATION WARNING**: The Tera template method (`{{arg(name="...")}}`) will be removed in mise 2026.11.0. Use `usage` spec instead.

For complete argument syntax, see: [arguments.md](./arguments.md)

---

## Level 7: File Tracking & Caching

### Source Files

```toml
[tasks.build]
sources = ["Cargo.toml", "src/**/*.rs"]
run = "cargo build"
```

Task re-runs only when source files change.

### Output Files

```toml
[tasks.build]
sources = ["Cargo.toml", "src/**/*.rs"]
outputs = ["target/release/myapp"]
run = "cargo build --release"
```

If outputs are newer than sources, task is **skipped**.

### Force Execution

```bash
mise run build --force  # Bypass caching
```

### Auto Output Detection

```toml
[tasks.compile]
outputs = { auto = true }  # Default behavior
run = "gcc -o app main.c"
```

---

## Level 8: Advanced Execution

### Confirmation Prompts

```toml
[tasks.drop-database]
confirm = "This will DELETE all data. Continue?"
run = "dropdb myapp"
```

### Output Control

```toml
[tasks.quiet-task]
quiet = true   # Suppress mise's output (not task output)
run = "echo 'This still prints'"

[tasks.silent-task]
silent = true  # Suppress ALL output
run = "background-job.sh"

[tasks.silent-stderr]
silent = "stderr"  # Only suppress stderr
run = "noisy-command"
```

### Raw Mode (Interactive)

```toml
[tasks.edit-config]
raw = true  # Direct stdin/stdout/stderr
run = "vim config.yaml"
```

**Warning**: `raw = true` disables parallel execution.

### Task-Specific Tools

```toml
[tasks.legacy-test]
tools = { python = "3.9", node = "18" }
run = "pytest && npm test"
```

Use specific tool versions for this task only.

### Custom Shell

```toml
[tasks.powershell-task]
shell = "pwsh -c"
run = "Get-Process | Select-Object -First 5"
```

---

## Level 9: Watch Mode

### Prefer Runtime-Native Watch

When the runtime has a built-in file watcher, use it instead of `mise watch` / `watchexec` -- zero extra memory, zero extra processes.

| Runtime     | Command                       | Notes                                                |
| ----------- | ----------------------------- | ---------------------------------------------------- |
| **Bun**     | `bun --watch run src/main.ts` | 0 MB overhead. Do NOT use `bun --hot` (stale state). |
| **Node.js** | `node --watch src/main.js`    | 0 MB overhead.                                       |
| **Python**  | `uvicorn app:main --reload`   | 0 MB overhead.                                       |

### External Watch (mise watch)

Use `mise watch` for runtimes without built-in watchers (Go, Rust, shell) or multi-language orchestration.

```bash
mise watch build  # Re-run on source changes
```

Requires `watchexec`: `mise use -g watchexec@latest`

### Watch Options

```bash
mise watch build --debounce 500ms  # Wait before re-run
mise watch build --restart          # Kill and restart on change
mise watch build --clear            # Clear screen before run
```

### On-Busy Behavior

```bash
mise watch build --on-busy-update=queue    # Queue changes
mise watch build --on-busy-update=restart  # Restart immediately
mise watch build --on-busy-update=do-nothing  # Ignore (default)
```
