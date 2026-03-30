# mise Tasks Advanced Features

Advanced features for watch mode, monorepo support, and experimental functionality.

## Watch Mode

### Overview

`mise watch` re-runs tasks automatically when source files change. Requires `watchexec` to be installed.

**Install watchexec**:

```bash
mise use -g watchexec@latest
```

### Basic Watch

```bash
mise watch build      # Re-run build on changes
mise watch test       # Re-run tests on changes
```

Watch uses `sources` from task definition to determine which files to monitor:

```toml
[tasks.build]
sources = ["src/**/*.rs", "Cargo.toml"]
run = "cargo build"
```

### Watch Options

- `--debounce` - Wait before re-running (e.g., `--debounce 500ms`)
- `--restart` - Kill running task and restart
- `--clear` - Clear screen before each run
- `--on-busy-update` - Behavior when task is running (e.g., `--on-busy-update=queue`)

### On-Busy Behavior

Controls what happens when files change while a task is running:

```bash
# Queue changes and run after current execution
mise watch build --on-busy-update=queue

# Immediately restart (kill current)
mise watch build --on-busy-update=restart

# Ignore changes during execution (default)
mise watch build --on-busy-update=do-nothing
```

### Interruptible Tasks

For tasks that should be restartable mid-execution:

```toml
[tasks.dev-server]
run = "uvicorn app:main --reload"
```

Use `--restart` with long-running processes:

```bash
mise watch dev-server --restart
```

### Watch with Multiple Tasks

```bash
mise watch 'test lint'     # Watch and run both
mise watch 'test ::: lint' # Watch and run in parallel
```

---

## Monorepo Support (Experimental)

**Requires**: `MISE_EXPERIMENTAL=1` environment variable.

### Enable Monorepo Mode

```toml
# Root .mise.toml
[settings]
experimental_monorepo_root = true
```

### Path Syntax

Monorepo mode introduces path-prefixed task names:

- `//projects/frontend:build` - Task in specific subproject
- `:build` - Task in current `config_root`
- `//...:test` - Run `test` in all projects
- `//projects/...:lint` - Run `lint` in all under `projects/`
- `//projects/frontend:*` - All tasks in `frontend`

### Project Discovery

Tasks in subdirectories are auto-discovered with path prefixes:

```
project-root/
  .mise.toml                    # Root config
  packages/
    api/
      .mise.toml               # Tasks become packages/api:*
    web/
      .mise.toml               # Tasks become packages/web:*
    shared/
      .mise.toml               # Tasks become packages/shared:*
```

### Running Monorepo Tasks

```bash
# Run specific project task
mise run //packages/api:test

# Run test in all packages
mise run '//packages/...:test'

# Run all tasks in one package
mise run '//packages/web:*'

# Run from package directory
cd packages/api
mise run :test        # Runs packages/api:test
mise run build        # Also runs local build
```

### Cross-Project Dependencies

```toml
# packages/web/.mise.toml
[tasks.build]
depends = ["//packages/shared:build"]  # Depend on shared lib
run = "npm run build"
```

### Monorepo Patterns

**Root orchestration task**:

```toml
# Root .mise.toml
[tasks.test-all]
description = "Run all package tests"
run = "mise run '//packages/...:test'"

[tasks.build-all]
description = "Build all packages"
run = "mise run '//packages/...:build'"
```

**Selective execution**:

```bash
# Test only changed packages (requires git integration)
git diff --name-only main | xargs -I{} mise run '//{}:test'
```

---

## Experimental Features

Features requiring `MISE_EXPERIMENTAL=1`:

### Task Hierarchy

Nested task inheritance (experimental):

```toml
[tasks.base-test]
env = { LOG_LEVEL = "debug" }
run = "pytest"

[tasks."test:unit"]
inherits = "base-test"
run = "pytest tests/unit/"
```

### Remote Tasks

Import tasks from remote sources (experimental):

```toml
[tasks]
include = ["https://example.com/tasks.toml"]
```

### Task Aliases with Arguments

```bash
mise alias test "run test -v"
mise test  # Runs: mise run test -v
```

---

## Shell Integration

### Custom Shell per Task

```toml
[tasks.powershell-task]
shell = "pwsh -c"
run = "Get-Process | Select-Object -First 5"

[tasks.python-task]
shell = "python -c"
run = '''
import json
print(json.dumps({"status": "ok"}))
'''

[tasks.zsh-task]
shell = "zsh -c"
run = "setopt extended_glob && ls **/*.md"
```

### Default Shell Configuration

```toml
[settings]
task_default_shell = "bash -c"
```

---

## Parallel Execution

### Parallel Operator

```bash
# Run tasks in parallel with :::
mise run lint ::: typecheck ::: test

# Sequential (default)
mise run lint test typecheck
```

### Jobs Control

```bash
mise run --jobs 4 'test:*'   # Limit concurrent tasks
mise run --jobs 0 'test:*'   # Unlimited parallelism
```

### Parallel in Task Definition

```toml
[tasks.validate]
# These run in parallel (no dependencies between them)
depends = ["lint", "typecheck", "format-check"]
run = "echo 'All validations passed'"
```

Dependencies without inter-dependencies run in parallel automatically.

---

## Environment Integration

### Global vs Task Environment

```toml
[env]
# Global - available to all tasks
DATABASE_URL = "postgresql://localhost/dev"

[tasks.test]
# Task-specific - overrides global, not passed to depends
env = { DATABASE_URL = "postgresql://localhost/test" }
run = "pytest"
```

**Important**: Task `env` is NOT inherited by dependency tasks.

### Environment from File

```toml
[env]
_.file = ".env"

[tasks.deploy]
# Additional env file for deploy
env_file = ".env.deploy"
run = "deploy.sh"
```

### Conditional Environment

```toml
[env]
{% if env.CI %}
LOG_LEVEL = "error"
{% else %}
LOG_LEVEL = "debug"
{% endif %}
```

---

## Debugging Tasks

### Verbose Output

```bash
mise run --verbose build     # Show task execution details
mise run -v build            # Short form
```

### Dry Run

```bash
mise run --dry-run ci        # Show what would run
```

### Task Information

```bash
mise tasks                   # List all tasks
mise tasks --hidden          # Include hidden tasks
mise task info build         # Show task details
```

### Environment Inspection

```bash
mise env                     # Show all env vars
mise env --json              # JSON format
```

---

## Best Practices

### Performance

1. **Use `sources`/`outputs`** - Skip unchanged builds
2. **Parallel where possible** - Use `:::` operator
3. **Limit watch scope** - Specific globs in `sources`
4. **Cache dependencies** - Use `depends` to avoid redundant work

### Organization

1. **Namespace with colons** - `test:unit`, `test:e2e`
2. **Hide internal tasks** - `hide = true` for helpers
3. **Document with descriptions** - Every task gets `description`
4. **Keep tasks focused** - Single responsibility

### Monorepo Specific

1. **Root orchestration** - Global tasks in root `.mise.toml`
2. **Explicit dependencies** - Cross-project with `//path:task`
3. **Consistent naming** - Same task names across packages
4. **Selective execution** - Use wildcards for efficiency
