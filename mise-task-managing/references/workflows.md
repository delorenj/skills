# Custom Workflows with Mise

This guide covers encapsulating multi-step custom workflows into mise tasks.

## When to Create Custom Workflows

Use mise workflows when you have:

- **Multi-step processes** requiring specific ordering
- **Conditional logic** based on environment or state
- **Error handling** across multiple operations
- **Repeated sequences** used by multiple team members
- **Complex orchestration** of tools and commands

## Workflow Design Principles

### 1. Single Responsibility

Each task should have one clear purpose:

```toml
# Good: Focused tasks
[tasks.lint]
run = "eslint ."

[tasks.format]
run = "prettier --write ."

[tasks.typecheck]
run = "tsc --noEmit"

[tasks.quality]
description = "Run all quality checks"
depends = ["lint", "format", "typecheck"]

# Bad: Kitchen sink task
[tasks.check-everything]
run = ["eslint .", "prettier --write .", "tsc --noEmit", "npm test"]
```

### 2. Composability

Build complex workflows from simple, reusable tasks:

```toml
[tasks.install]
run = "npm install"

[tasks.build]
depends = ["install"]
run = "npm run build"

[tasks.test]
depends = ["build"]
run = "npm test"

[tasks.deploy]
depends = ["test"]
run = "./deploy.sh"

# Compose into full pipeline
[tasks.ci]
depends = ["deploy"]
```

### 3. Idempotency

Tasks should be safe to run multiple times:

```bash
#!/usr/bin/env bash
#MISE description="Setup development environment"

set -euo pipefail

# Check before acting
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

if [ ! -f ".env" ]; then
  echo "Creating .env from template..."
  cp .env.example .env
fi
```

## Workflow Patterns

### Sequential Pipeline

Tasks run one after another, stopping on first failure:

```toml
[tasks.deploy]
description = "Full deployment pipeline"
depends = ["validate", "build", "test", "package", "upload"]

[tasks.validate]
run = "npm run validate"

[tasks.build]
run = "npm run build"

[tasks.test]
run = "npm test"

[tasks.package]
run = "./package.sh"

[tasks.upload]
run = "./upload.sh"
```

### Parallel Execution

Independent tasks run simultaneously:

```toml
[tasks.ci]
description = "Run CI checks in parallel"
depends = ["lint", "typecheck", "test-unit", "test-integration"]

[tasks.lint]
run = "eslint ."

[tasks.typecheck]
run = "tsc --noEmit"

[tasks."test-unit"]
run = "vitest run unit"

[tasks."test-integration"]
run = "vitest run integration"
```

Mise automatically parallelizes independent tasks in `depends`.

### Conditional Workflows

Use file-based tasks for complex logic:

```bash
#!/usr/bin/env bash
#MISE description="Deploy based on branch"

set -euo pipefail

BRANCH=$(git branch --show-current)

if [ "$BRANCH" = "main" ]; then
  echo "Deploying to production..."
  mise run deploy:prod
elif [ "$BRANCH" = "staging" ]; then
  echo "Deploying to staging..."
  mise run deploy:staging
else
  echo "Not a deployment branch. Running tests only..."
  mise run test
fi
```

### Cleanup Workflows

Use `depends_post` for guaranteed cleanup:

```toml
[tasks.integration-test]
description = "Run integration tests with cleanup"
depends = ["start-services"]
depends_post = ["stop-services"]
run = "npm run test:integration"

[tasks."start-services"]
run = "docker compose up -d"

[tasks."stop-services"]
run = "docker compose down"
```

### Watch and Rebuild

Create development loops:

```toml
[tasks.dev]
description = "Watch and rebuild on changes"
sources = ["src/**/*"]
run = "npm run build"

# Then: mise watch dev
```

Or with explicit watch command:

```bash
#!/usr/bin/env bash
#MISE description="Watch and run tests"

watchexec --clear --restart --exts rs,toml -- mise run test
```

## Real-World Workflow Examples

### Database Migration Workflow

```toml
[tasks."db:migrate"]
description = "Run database migrations"
depends = ["db:backup"]
run = "npm run migrate:up"

[tasks."db:backup"]
description = "Backup database before migration"
run = "./scripts/backup-db.sh"

[tasks."db:rollback"]
description = "Rollback last migration"
depends = ["db:backup"]
run = "npm run migrate:down"

[tasks."db:reset"]
description = "Reset database to clean state"
confirm = "This will destroy all data. Continue?"
run = ["npm run migrate:reset", "npm run seed"]
```

### Release Workflow

```bash
#!/usr/bin/env bash
#MISE description="Create and publish release"
#MISE depends=["test", "build"]
#MISE confirm="Create release and publish?"

set -euo pipefail

# Ensure clean working directory
if [ -n "$(git status --porcelain)" ]; then
  echo "Error: Working directory not clean"
  exit 1
fi

# Get version bump type
BUMP=${1:-patch}

# Update version
npm version "$BUMP"

# Get new version
VERSION=$(node -p "require('./package.json').version")

# Create git tag
git tag -a "v$VERSION" -m "Release v$VERSION"

# Build
mise run build

# Publish
npm publish

# Push to remote
git push origin main --tags

echo "Released v$VERSION"
```

### Multi-Environment Deployment

```toml
[tasks."deploy:staging"]
description = "Deploy to staging environment"
depends = ["build"]
env = { ENVIRONMENT = "staging", API_URL = "https://staging.api.example.com" }
run = "./deploy.sh"

[tasks."deploy:prod"]
description = "Deploy to production"
depends = ["build", "test"]
confirm = "Deploy to production?"
env = { ENVIRONMENT = "production", API_URL = "https://api.example.com" }
run = "./deploy.sh"

[tasks."deploy:rollback"]
description = "Rollback deployment"
confirm = "Rollback production deployment?"
run = "./rollback.sh"
```

### Docker-Based Development

```toml
[tasks."docker:up"]
description = "Start Docker services"
run = "docker compose up -d"

[tasks."docker:down"]
description = "Stop Docker services"
run = "docker compose down"

[tasks."docker:logs"]
description = "Show Docker logs"
raw = true
run = "docker compose logs -f"

[tasks."docker:reset"]
description = "Reset Docker environment"
confirm = "This will delete all volumes. Continue?"
run = ["docker compose down -v", "docker compose up -d"]

[tasks.dev]
description = "Start development with Docker"
depends = ["docker:up"]
depends_post = ["docker:down"]
run = "npm run dev"
```

### Monorepo Workflow

```toml
[tasks."lib:build"]
description = "Build shared library"
dir = "{{ config_root }}/packages/lib"
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks."app:build"]
description = "Build application"
dir = "{{ config_root }}/apps/web"
depends = ["lib:build"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks."api:build"]
description = "Build API server"
dir = "{{ config_root }}/apps/api"
depends = ["lib:build"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks.build]
description = "Build all packages"
depends = ["lib:build", "app:build", "api:build"]

[tasks.dev]
description = "Start all services"
depends = ["lib:build"]
run = ["concurrently 'mise run app:dev' 'mise run api:dev'"]
raw = true
```

## Advanced Patterns

### State Management

Track workflow state using files:

```bash
#!/usr/bin/env bash
#MISE description="Setup project with state tracking"

set -euo pipefail

STATE_FILE=".mise/state/setup-complete"

if [ -f "$STATE_FILE" ]; then
  echo "Setup already completed. Use --force to re-run."
  exit 0
fi

echo "Running first-time setup..."
mise run install
mise run db:migrate
mise run seed

mkdir -p "$(dirname "$STATE_FILE")"
touch "$STATE_FILE"

echo "Setup complete!"
```

### Dynamic Task Generation

Generate tasks based on project structure:

```bash
#!/usr/bin/env bash
#MISE description="Run tests for all packages"

set -euo pipefail

# Find all package directories
PACKAGES=$(find packages -maxdepth 1 -mindepth 1 -type d)

for pkg in $PACKAGES; do
  echo "Testing $pkg..."
  (cd "$pkg" && npm test)
done
```

### Workflow Orchestration with Arguments

```bash
#!/usr/bin/env bash
#MISE description="Deploy specific services"
#MISE usage="{usage} [OPTIONS] <services...>"

set -euo pipefail

SERVICES="${@:-all}"

if [ "$SERVICES" = "all" ]; then
  mise run deploy:frontend
  mise run deploy:backend
  mise run deploy:workers
else
  for service in $SERVICES; do
    echo "Deploying $service..."
    mise run "deploy:$service"
  done
fi
```

### Error Recovery

```bash
#!/usr/bin/env bash
#MISE description="Deploy with automatic rollback on failure"

set -euo pipefail

# Create checkpoint
CHECKPOINT=$(date +%s)
echo "Creating checkpoint: $CHECKPOINT"
./scripts/checkpoint-create.sh "$CHECKPOINT"

# Try deploy
if ! mise run deploy:apply; then
  echo "Deployment failed. Rolling back..."
  ./scripts/checkpoint-restore.sh "$CHECKPOINT"
  exit 1
fi

echo "Deployment successful"
./scripts/checkpoint-delete.sh "$CHECKPOINT"
```

### Notification Integration

```bash
#!/usr/bin/env bash
#MISE description="CI pipeline with notifications"

set -euo pipefail

notify() {
  local status=$1
  local message=$2
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"$status: $message\"}"
}

notify "⏳" "Starting CI pipeline..."

if ! mise run test; then
  notify "❌" "Tests failed"
  exit 1
fi

if ! mise run build; then
  notify "❌" "Build failed"
  exit 1
fi

notify "✅" "CI pipeline completed successfully"
```

## Performance Optimization

### Caching Strategy

```toml
[tasks.build]
description = "Build with aggressive caching"
sources = [
  "src/**/*",
  "package.json",
  "tsconfig.json"
]
outputs = [
  "dist/"
]
run = "npm run build"
```

### Incremental Builds

```toml
[tasks."build:lib"]
sources = ["lib/src/**/*"]
outputs = ["lib/dist/"]
run = "cd lib && npm run build"

[tasks."build:app"]
sources = ["app/src/**/*"]
outputs = ["app/dist/"]
depends = ["build:lib"]  # Only if lib changed
run = "cd app && npm run build"
```

### Parallel Execution Tuning

```bash
# Run with custom parallelism
mise run -j 8 task1 task2 task3

# Or set in mise.toml
[settings]
jobs = 8
```

## Testing Workflows

### Dry Run Mode

```bash
#!/usr/bin/env bash
#MISE description="Deploy (supports dry-run)"

set -euo pipefail

DRY_RUN=${DRY_RUN:-false}

if [ "$DRY_RUN" = "true" ]; then
  echo "[DRY RUN] Would deploy to production"
  exit 0
fi

echo "Deploying to production..."
./deploy.sh
```

Usage: `DRY_RUN=true mise run deploy`

### Validation Tasks

```toml
[tasks.validate]
description = "Validate deployment readiness"
run = [
  "test -f .env || (echo 'Missing .env' && exit 1)",
  "test -d dist || (echo 'Missing dist/' && exit 1)",
  "command -v docker || (echo 'Docker not installed' && exit 1)"
]
```

## Documentation

Document workflows in your mise.toml:

```toml
[tasks.ci]
description = """
Complete CI pipeline:
1. Lint code
2. Run type checks
3. Execute tests
4. Build artifacts
5. Generate coverage report

Required: Node.js 20+, Docker
"""
depends = ["lint", "typecheck", "test", "build", "coverage"]
```

## Troubleshooting

### Debugging Workflows

```bash
# Verbose output
mise run -v workflow-name

# Show task dependencies
mise tasks deps workflow-name

# Force run (ignore cache)
mise run --force workflow-name

# Dry run (if supported by task)
DRY_RUN=true mise run workflow-name
```

### Common Issues

**Tasks running in wrong order**
- Check `depends` configuration
- Verify task names are correct
- Use `mise tasks deps` to visualize

**Parallel execution conflicts**
- Add `raw = true` for interactive tasks
- Use `depends` to enforce ordering
- Reduce parallelism with `-j 1`

**Environment not propagating**
- Use `env` in task definition
- Check that child tasks don't override
- Verify `MISE_*` variables are available

## Resources

- [Common Workflows](./common-workflows.md) - Standard patterns
- [Wrapping Interfaces](./wrapping-an-interface.md) - Adapting existing tools
- [Mise Tasks Documentation](https://mise.jdx.dev/tasks/)
