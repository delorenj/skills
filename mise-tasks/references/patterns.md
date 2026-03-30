# mise Tasks Patterns

## Table of Contents

- [Hidden Helper Tasks](#hidden-helper-tasks)
  - [Credential Check](#credential-check)
  - [Destructive Operation Confirmation](#destructive-operation-confirmation)
  - [Environment Validation](#environment-validation)
- [Database Migration Pattern](#database-migration-pattern)
- [CI/CD Pipeline Pattern](#cicd-pipeline-pattern)
- [Release Workflow Pattern](#release-workflow-pattern)
- [Development Server Pattern](#development-server-pattern)
  - [Runtime-Native Watch (Preferred)](#runtime-native-watch-preferred)
  - [External Watch (Polyglot / Non-Runtime)](#external-watch-polyglot--non-runtime)
  - [Watch Method Decision Table](#watch-method-decision-table)
- [Parameterized Deployment Pattern](#parameterized-deployment-pattern)
- [File Tracking Pattern](#file-tracking-pattern)
- [Pueue Pipeline Orchestration Pattern](#pueue-pipeline-orchestration-pattern)
  - [mise Entry Points](#mise-entry-points)
  - [Shell Script DAG Builder](#shell-script-dag-builder)
  - [Key Principles](#key-principles)
  - [Anti-Pattern: mise `depends` for Long-Running Remote Jobs](#anti-pattern-mise-depends-for-long-running-remote-jobs)
  - [When to Use](#when-to-use)
- [Complete Project Template](#complete-project-template)

Real-world task patterns for common workflows.

## Hidden Helper Tasks

Internal utilities that support other tasks but shouldn't appear in `mise tasks` output.

### Credential Check

```toml
[tasks._check-credentials]
description = "Verify required credentials are set"
hide = true
run = '''
#!/usr/bin/env bash
set -euo pipefail

missing=()
[ -z "${DATABASE_URL:-}" ] && missing+=("DATABASE_URL")
[ -z "${API_KEY:-}" ] && missing+=("API_KEY")

if [ ${#missing[@]} -gt 0 ]; then
  echo "Missing required credentials:"
  printf '  - %s\n' "${missing[@]}"
  echo ""
  echo "Copy .env.example to .env and fill in values"
  exit 1
fi
echo "Credentials configured"
'''
```

### Destructive Operation Confirmation

```toml
[tasks._confirm-destructive]
description = "Confirm destructive operation"
hide = true
run = '''
echo ""
echo "This will DELETE existing data."
echo "Press Enter to continue or Ctrl+C to cancel..."
read
'''
```

### Environment Validation

```toml
[tasks._validate-env]
description = "Validate environment is ready"
hide = true
run = '''
#!/usr/bin/env bash
set -euo pipefail

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required="3.11"
if [ "$(printf '%s\n' "$required" "$python_version" | sort -V | head -n1)" != "$required" ]; then
  echo "Python >= $required required (found $python_version)"
  exit 1
fi

# Check database connection
if ! pg_isready -q 2>/dev/null; then
  echo "Database not available"
  exit 1
fi

echo "Environment validated"
'''
```

---

## Database Migration Pattern

Complete database migration workflow with safety checks.

```toml
[env]
_.file = ".env"
CLICKHOUSE_DATABASE = "myapp"

[tasks._check-credentials]
hide = true
run = '[ -n "$CLICKHOUSE_HOST" ] || { echo "Set CLICKHOUSE_HOST in .env"; exit 1; }'

[tasks._confirm-destructive]
hide = true
run = 'echo "Press Enter to continue or Ctrl+C to cancel..." && read'

[tasks.db-drop]
description = "Drop legacy database (destructive!)"
depends = ["_check-credentials", "_confirm-destructive"]
run = "clickhouse-client --query 'DROP DATABASE IF EXISTS legacy_db'"

[tasks.db-init]
description = "Create database and tables from schema"
depends = ["_check-credentials"]
depends_post = ["db-validate"]
usage = 'opt "--schema" default="main" help="Schema name"'
run = "uv run python -m schema.cli init --schema ${usage_schema}"

[tasks.db-validate]
description = "Validate schema against live database"
depends = ["_check-credentials"]
run = "uv run python -m schema.cli validate"

[tasks.db-migrate]
description = "Full migration: drop legacy + create new + validate"
depends = ["db-drop", "db-init"]
depends_post = ["test-e2e"]
run = "echo 'Migration complete'"
```

**Usage**:

```bash
mise run db-migrate
# Executes: _check-credentials → _confirm-destructive → db-drop → db-init → db-validate → test-e2e
```

---

## CI/CD Pipeline Pattern

Comprehensive CI pipeline with parallel stages.

```toml
[tasks.lint]
description = "Run linters"
run = "ruff check . && ruff format --check ."

[tasks.typecheck]
description = "Run type checker"
run = "mypy src/"

[tasks.test]
description = "Run test suite"
alias = "t"
run = "pytest tests/ -v"

[tasks."test:unit"]
description = "Run unit tests only"
run = "pytest tests/unit/ -v"

[tasks."test:integration"]
description = "Run integration tests"
depends = ["_check-credentials"]
run = "pytest tests/integration/ -v"

[tasks.build]
description = "Build distribution"
depends = ["lint", "typecheck", "test"]
run = "uv build"

[tasks.ci]
description = "Full CI pipeline"
depends = ["lint", "typecheck", "test", "build"]
run = "echo 'CI passed'"
```

**Parallel execution**:

```bash
# Run lint and typecheck in parallel
mise run lint ::: typecheck

# Then run tests
mise run test
```

---

## Release Workflow Pattern

Safe release workflow with pre-checks.

```toml
[tasks._check-clean]
description = "Verify working directory is clean"
hide = true
run = '''
if [ -n "$(git status --porcelain)" ]; then
  echo "Working directory not clean. Commit or stash changes."
  exit 1
fi
'''

[tasks._check-main]
description = "Verify on main branch"
hide = true
run = '''
branch=$(git branch --show-current)
if [ "$branch" != "main" ] && [ "$branch" != "master" ]; then
  echo "Must be on main/master branch (on: $branch)"
  exit 1
fi
'''

[tasks.release-dry]
description = "Dry-run release (no changes)"
depends = ["_check-clean", "_check-main", "test"]
run = '/usr/bin/env bash -c '\''GITHUB_TOKEN=$(gh auth token) npx semantic-release --no-ci --dry-run'\'''

[tasks.release]
description = "Create release"
depends = ["_check-clean", "_check-main", "test"]
confirm = "This will create a new release. Continue?"
run = '/usr/bin/env bash -c '\''GITHUB_TOKEN=$(gh auth token) npx semantic-release --no-ci'\'''
```

---

## Development Server Pattern

Development workflow with file watching.

### Runtime-Native Watch (Preferred)

Use the runtime's built-in file watcher when available — zero extra processes, zero extra memory.

**Bun/TypeScript** (preferred for all Bun services):

```toml
[tasks.start]
description = "Start service (auto-restarts on file changes)"
run = "bun --watch run src/main.ts"

[tasks.start-plain]
description = "Start without file watching"
run = "bun run src/main.ts"
```

> **Anti-pattern**: Do NOT use `bun --hot`, `nodemon`, `ts-node-dev`, `tsx watch`, or
> `watchexec` for Bun/TypeScript projects. `bun --watch` uses the same kqueue/inotify
> primitives built into the Bun runtime with zero overhead (tested: +0 MB RSS vs plain
> `bun run`). `bun --hot` preserves module state across reloads which causes stale state
> bugs in long-running services.

**Python** (uvicorn built-in reload):

```toml
[tasks.dev]
description = "Start development server"
run = "uvicorn app:main --reload --port 8000"

[tasks.dev-db]
description = "Start database in Docker"
run = "docker compose up -d postgres"

[tasks.dev-full]
description = "Start full dev environment"
depends = ["dev-db"]
run = "mise run dev"
```

### External Watch (Polyglot / Non-Runtime)

Use `mise watch` or `watchexec` only when the runtime lacks a built-in watcher (Go, Rust, shell scripts, multi-language orchestration).

```bash
mise watch dev  # Auto-restart on file changes (requires watchexec)
```

### Watch Method Decision Table

| Runtime            | Method             | Command                         | Extra overhead          |
| ------------------ | ------------------ | ------------------------------- | ----------------------- |
| **Bun**            | Built-in `--watch` | `bun --watch run src/main.ts`   | 0 MB, 0 processes       |
| **Python**         | uvicorn reload     | `uvicorn app:main --reload`     | 0 MB, 0 processes       |
| **Node.js**        | Built-in `--watch` | `node --watch src/main.js`      | 0 MB, 0 processes       |
| **Go/Rust/other**  | watchexec          | `watchexec -w src -- cargo run` | +10 MB, 1 process       |
| **Multi-language** | mise watch         | `mise watch dev`                | +10 MB (uses watchexec) |

---

## Parameterized Deployment Pattern

Environment-aware deployment with arguments.

```toml
[tasks.deploy]
description = "Deploy to environment"
depends = ["_check-credentials", "build"]
usage = '''
arg "<environment>" help="Target environment" {
  choices "dev" "staging" "prod"
}
flag "-f --force" help="Skip confirmation"
flag "--dry-run" help="Show what would be deployed"
'''
run = '''
#!/usr/bin/env bash
set -euo pipefail

ENV="${usage_environment}"
FORCE="${usage_force:-false}"
DRY="${usage_dry_run:-false}"

echo "Deploying to: $ENV"

if [ "$DRY" = "true" ]; then
  echo "[DRY RUN] Would deploy to $ENV"
  exit 0
fi

if [ "$ENV" = "prod" ] && [ "$FORCE" != "true" ]; then
  echo "Production deployment requires --force flag"
  exit 1
fi

kubectl config use-context "$ENV"
kubectl apply -f "k8s/$ENV/"
'''
```

**Usage**:

```bash
mise run deploy dev           # Deploy to dev
mise run deploy staging       # Deploy to staging
mise run deploy prod --force  # Deploy to production
mise run deploy prod --dry-run  # Preview production deploy
```

---

## File Tracking Pattern

Efficient builds with source/output tracking.

```toml
[tasks.compile]
description = "Compile TypeScript"
sources = ["src/**/*.ts", "tsconfig.json"]
outputs = ["dist/**/*.js"]
run = "tsc"

[tasks.bundle]
description = "Bundle for production"
depends = ["compile"]
sources = ["dist/**/*.js", "package.json"]
outputs = ["build/bundle.js"]
run = "esbuild dist/index.js --bundle --outfile=build/bundle.js"
```

**Behavior**:

- First run: Both tasks execute
- Second run (no changes): Both tasks skip
- After editing `src/`: Only `compile` and `bundle` run
- Force rebuild: `mise run bundle --force`

---

## Pueue Pipeline Orchestration Pattern

Delegate long-running, multi-step pipelines to [pueue](https://github.com/Nukesor/pueue) for SSH-safe persistence and dependency chaining. Battle-tested during rangebar-py Issue #88 production deployment (batch repopulation -> OPTIMIZE TABLE -> validation).

### mise Entry Points

```toml
# .mise/tasks/cache.toml

# Individual steps (can run standalone)
["cache:detect-overflow"]
description = "Detect volume overflow (negative volumes) in ClickHouse cache"
run = "python scripts/detect_volume_overflow.py"

["cache:optimize"]
description = "Run OPTIMIZE TABLE FINAL on range_bars"
run = "./scripts/pueue-populate.sh optimize"

# Fully-chained pueue pipeline (recommended for production)
["cache:postprocess-all"]
description = "Full post-fix pipeline via pueue: repopulate → optimize → detect (auto-chained)"
run = "./scripts/pueue-populate.sh postprocess-all"
```

### Shell Script DAG Builder

The shell script captures pueue job IDs with `--print-task-id` and chains steps with `--after`:

```bash
postprocess_all() {
    # Step 1: Queue batch jobs, capture IDs
    JOB_IDS=()
    for threshold in 250 500 750 1000; do
        local job_id
        job_id=$(pueue add --print-task-id --group postfix \
            --label "SYMBOL@${threshold}" \
            --working-directory "$PROJECT_DIR" \
            -- uv run python scripts/populate.py --threshold "$threshold" --force-refresh)
        JOB_IDS+=("$job_id")
    done

    # Step 2: Chain OPTIMIZE TABLE --after all batch jobs
    local optimize_id
    optimize_id=$(pueue add --print-task-id --group postfix \
        --label "optimize-table" \
        --after "${JOB_IDS[@]}" \
        --working-directory "$PROJECT_DIR" \
        -- clickhouse-client --query "OPTIMIZE TABLE mydb.mytable FINAL")

    # Step 3: Chain validation --after optimize
    pueue add --group postfix \
        --label "detect-overflow" \
        --after "$optimize_id" \
        --working-directory "$PROJECT_DIR" \
        -- uv run python scripts/detect_overflow.py

    echo "Pipeline: ${#JOB_IDS[@]} batch jobs → optimize → detect"
}
```

### Key Principles

- **mise provides the entry point**: `mise run cache:postprocess-all` — human-friendly, discoverable via `mise tasks`
- **Pueue provides the execution engine**: Dependency resolution, SSH-safe persistence, group-based parallelism
- **Shell script is the glue**: Captures pueue job IDs with `--print-task-id`, chains with `--after`
- **Each step also standalone**: `mise run cache:optimize` works independently for ad-hoc use

### Anti-Pattern: mise `depends` for Long-Running Remote Jobs

```toml
# BAD: mise blocks waiting for each step
["cache:postprocess-all"]
depends = ["cache:repopulate", "cache:optimize", "cache:detect"]
# This runs synchronously — if SSH disconnects, everything dies

# GOOD: Delegate to pueue for persistence
["cache:postprocess-all"]
run = "./scripts/pueue-populate.sh postprocess-all"
# This queues everything in pueue and returns immediately
```

### When to Use

| Scenario                                       | Use This Pattern | Use Plain mise `depends`     |
| ---------------------------------------------- | ---------------- | ---------------------------- |
| Long-running jobs (hours/days) on remote hosts | Yes              | No                           |
| Multi-step pipelines with dependencies         | Yes              | No                           |
| Jobs that must survive SSH disconnects         | Yes              | No                           |
| Group-based parallelism limits needed          | Yes              | No                           |
| Fast local tasks (< 5 minutes)                 | No               | Yes                          |
| CI/CD pipelines                                | No               | Yes (with parallel operator) |
| Single-step operations                         | No               | Yes                          |

---

## Complete Project Template

Full `.mise.toml` template combining all patterns.

```toml
# .mise.toml - Complete project configuration
min_version = "2024.9.5"

[settings]
experimental = true

[tools]
python = "3.11"
node = "22"
uv = "latest"

[env]
_.python.venv = { path = ".venv", create = true }
_.file = [".env", { path = ".env.local", redact = true }]
_.path = ["{{config_root}}/bin", "node_modules/.bin"]

PROJECT_ROOT = "{{config_root}}"
PYTHONUNBUFFERED = "1"

# Hidden helpers
[tasks._check-env]
hide = true
run = '[ -f .env ] || { echo "Copy .env.example to .env"; exit 1; }'

[tasks._check-clean]
hide = true
run = '[ -z "$(git status --porcelain)" ] || { echo "Uncommitted changes"; exit 1; }'

# Development
[tasks.dev]
description = "Start development server"
depends = ["_check-env"]
run = "uvicorn app:main --reload"

# Testing
[tasks.test]
description = "Run tests"
alias = "t"
run = "pytest tests/ -v"

[tasks."test:cov"]
description = "Run tests with coverage"
run = "pytest tests/ --cov=src --cov-report=html"

# Code quality
[tasks.lint]
description = "Run linters"
run = "ruff check . && ruff format --check ."

[tasks.fix]
description = "Fix linting issues"
run = "ruff check --fix . && ruff format ."

# Build
[tasks.build]
description = "Build package"
depends = ["lint", "test"]
run = "uv build"

# Release
[tasks.release]
description = "Create release"
depends = ["_check-clean", "build"]
confirm = "Create new release?"
run = '/usr/bin/env bash -c '\''GITHUB_TOKEN=$(gh auth token) npx semantic-release --no-ci'\'''
```
