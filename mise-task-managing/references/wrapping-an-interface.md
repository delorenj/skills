# Wrapping Existing Interfaces with Mise

This guide covers exposing scripts, CLI commands, and tools as convenient mise tasks.

## Why Wrap Existing Tools?

Wrapping provides:

- **Consistent interface** - Same command pattern across all tools
- **Context awareness** - Leverage mise's environment and tool management
- **Documentation** - Built-in help via task descriptions
- **Dependency management** - Ensure prerequisites run first
- **Team onboarding** - Simpler commands for new team members
- **Environment isolation** - Tool versions managed by mise

## Pattern: Wrapping Shell Scripts

### Simple Script Wrapper

**Before** - Direct script execution:

```bash
./scripts/deploy.sh production --verbose
```

**After** - Mise task wrapper:

```toml
[tasks.deploy]
description = "Deploy application to specified environment"
run = "./scripts/deploy.sh ${@}"
```

Usage: `mise run deploy production --verbose`

### Script with Environment Setup

```toml
[tasks.deploy]
description = "Deploy with proper environment"
env = {
  AWS_REGION = "us-east-1",
  LOG_LEVEL = "info"
}
run = "./scripts/deploy.sh ${@}"
```

### Script with Prerequisites

```toml
[tasks.deploy]
description = "Deploy after running checks"
depends = ["test", "build"]
confirm = "Deploy to production?"
run = "./scripts/deploy.sh ${@}"
```

## Pattern: Wrapping Package Manager Scripts

### npm/pnpm/bun Scripts

**Before** (package.json):

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  }
}
```

**After** (mise.toml) - Enhanced wrappers:

```toml
[tasks.dev]
description = "Start development server"
run = "npm run dev"
raw = true  # Allow interactive input

[tasks.build]
description = "Build for production"
depends = ["lint", "test"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks.test]
description = "Run tests"
run = "npm test -- ${@}"  # Pass arguments through
```

Benefits:
- Add caching with `sources`/`outputs`
- Add dependencies with `depends`
- Uniform interface: `mise run build` instead of `npm run build`

### Python Script Wrapper

**Before**:

```bash
python scripts/process_data.py --input data.csv --output results.json
```

**After**:

```toml
[tasks."data:process"]
description = "Process data file"
tools = ["python@3.12"]  # Ensure correct Python version
dir = "{{ config_root }}"
run = "python scripts/process_data.py ${@}"
```

Usage: `mise run data:process --input data.csv --output results.json`

## Pattern: Wrapping Docker Commands

### Docker Compose Wrapper

```toml
[tasks."docker:up"]
description = "Start all Docker services"
run = "docker compose up -d"

[tasks."docker:down"]
description = "Stop all Docker services"
run = "docker compose down"

[tasks."docker:logs"]
description = "Show Docker logs (follow mode)"
raw = true
run = "docker compose logs -f ${@}"

[tasks."docker:exec"]
description = "Execute command in container"
run = "docker compose exec ${@}"

[tasks."docker:rebuild"]
description = "Rebuild and restart services"
confirm = "Rebuild all services?"
run = ["docker compose down", "docker compose build", "docker compose up -d"]
```

Usage:
```bash
mise run docker:up
mise run docker:logs backend
mise run docker:exec backend bash
```

### Docker Build Wrapper

```toml
[tasks."docker:build"]
description = "Build Docker image"
sources = ["Dockerfile", "src/**/*"]
run = "docker build -t myapp:${VERSION:-latest} ."

[tasks."docker:push"]
description = "Push Docker image to registry"
depends = ["docker:build"]
confirm = "Push image to registry?"
run = "docker push myapp:${VERSION:-latest}"
```

## Pattern: Wrapping CLI Tools

### Git Operations

```toml
[tasks."git:sync"]
description = "Sync with remote (pull & push)"
run = ["git pull --rebase", "git push"]

[tasks."git:clean"]
description = "Clean untracked files"
confirm = "Delete all untracked files?"
run = "git clean -fd"

[tasks."git:status"]
description = "Show git status with additional info"
run = ["git status", "git log --oneline -5"]
```

### Database CLI Wrapper

```toml
[tasks."db:connect"]
description = "Connect to database"
raw = true
env = { DATABASE_URL = "postgresql://localhost/mydb" }
run = "psql $DATABASE_URL"

[tasks."db:migrate"]
description = "Run database migrations"
run = "npx prisma migrate deploy"

[tasks."db:seed"]
description = "Seed database"
depends = ["db:migrate"]
run = "npx prisma db seed"

[tasks."db:reset"]
description = "Reset database"
confirm = "This will destroy all data. Continue?"
run = ["npx prisma migrate reset --force"]
```

### Terraform Wrapper

```toml
[tasks."tf:init"]
description = "Initialize Terraform"
dir = "{{ config_root }}/terraform"
run = "terraform init"

[tasks."tf:plan"]
description = "Show Terraform plan"
depends = ["tf:init"]
dir = "{{ config_root }}/terraform"
run = "terraform plan"

[tasks."tf:apply"]
description = "Apply Terraform changes"
depends = ["tf:plan"]
confirm = "Apply infrastructure changes?"
dir = "{{ config_root }}/terraform"
run = "terraform apply"

[tasks."tf:destroy"]
description = "Destroy infrastructure"
confirm = "DESTROY all infrastructure?"
dir = "{{ config_root }}/terraform"
run = "terraform destroy"
```

## Pattern: Wrapping Make Targets

```toml
[tasks.make]
description = "Run Make target with arguments"
run = "make ${@}"

# Or wrap specific targets
[tasks.build]
description = "Build via Make"
run = "make build"

[tasks.clean]
description = "Clean via Make"
run = "make clean"

[tasks.install]
description = "Install via Make"
run = "make install"
```

## Pattern: Complex Multi-Tool Wrappers

### File-Based Wrapper Script

When simple TOML isn't enough, use file-based tasks:

```bash
#!/usr/bin/env bash
#MISE description="Deploy with pre-flight checks"
#MISE depends=["test", "build"]
#MISE confirm="Deploy to production?"

set -euo pipefail

# Pre-flight checks
echo "Running pre-flight checks..."
if ! command -v aws &> /dev/null; then
  echo "Error: AWS CLI not installed"
  exit 1
fi

if [ -z "${AWS_ACCESS_KEY_ID:-}" ]; then
  echo "Error: AWS credentials not configured"
  exit 1
fi

# Main deployment
echo "Deploying to production..."
./scripts/deploy.sh "$@"

# Post-deployment
echo "Running smoke tests..."
./scripts/smoke-test.sh

echo "Deployment complete!"
```

Save as `.mise/tasks/deploy`, make executable: `chmod +x .mise/tasks/deploy`

## Pattern: Argument Forwarding

### Pass-Through Arguments

```toml
[tasks.test]
description = "Run tests with custom arguments"
run = "npm test -- ${@}"
```

Usage: `mise run test --coverage --watch`

### Named Arguments with Defaults

```bash
#!/usr/bin/env bash
#MISE description="Deploy to environment"

set -euo pipefail

ENVIRONMENT=${1:-staging}
REGION=${2:-us-east-1}

echo "Deploying to $ENVIRONMENT in $REGION..."
./scripts/deploy.sh "$ENVIRONMENT" "$REGION"
```

Usage:
```bash
mise run deploy              # staging, us-east-1
mise run deploy production   # production, us-east-1
mise run deploy production eu-west-1  # production, eu-west-1
```

### Flag Parsing

```bash
#!/usr/bin/env bash
#MISE description="Build with options"
#MISE usage="{usage} [OPTIONS]"

set -euo pipefail

VERBOSE=false
CLEAN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

[ "$CLEAN" = true ] && echo "Cleaning..." && make clean
[ "$VERBOSE" = true ] && echo "Building (verbose)..." || echo "Building..."

make build
```

## Pattern: Environment-Specific Wrappers

```toml
[tasks."deploy:staging"]
description = "Deploy to staging"
env = {
  ENVIRONMENT = "staging",
  API_URL = "https://staging.api.example.com"
}
run = "./scripts/deploy.sh"

[tasks."deploy:prod"]
description = "Deploy to production"
env = {
  ENVIRONMENT = "production",
  API_URL = "https://api.example.com"
}
confirm = "Deploy to PRODUCTION?"
depends = ["test"]
run = "./scripts/deploy.sh"
```

## Pattern: Interactive Tool Wrappers

For tools requiring stdin/stdout interaction:

```toml
[tasks.shell]
description = "Interactive shell in container"
raw = true
run = "docker compose exec backend bash"

[tasks.repl]
description = "Start Python REPL with project context"
raw = true
tools = ["python@3.12"]
run = "python -i -c 'from app import *'"

[tasks.psql]
description = "Interactive PostgreSQL shell"
raw = true
run = "psql $DATABASE_URL"
```

The `raw = true` setting connects the task directly to terminal stdin/stdout.

## Pattern: Caching Wrapper

Wrap expensive operations with caching:

```toml
[tasks.download]
description = "Download dependencies (cached)"
sources = ["requirements.txt"]
outputs = [".venv/"]
run = "pip install -r requirements.txt"

[tasks."assets:download"]
description = "Download static assets (cached)"
sources = ["assets.lock"]
outputs = ["public/assets/"]
run = "./scripts/download-assets.sh"
```

Mise skips execution if outputs are newer than sources.

## Pattern: Credential-Aware Wrappers

```bash
#!/usr/bin/env bash
#MISE description="Deploy with 1Password secrets"

set -euo pipefail

# Inject secrets from 1Password
export AWS_ACCESS_KEY_ID=$(op read "op://vault/aws/access-key")
export AWS_SECRET_ACCESS_KEY=$(op read "op://vault/aws/secret-key")

# Run deployment
./scripts/deploy.sh "$@"
```

## Pattern: Notification Wrappers

```bash
#!/usr/bin/env bash
#MISE description="Run tests with Slack notification"

set -euo pipefail

notify() {
  local message=$1
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"$message\"}"
}

notify "Tests starting..."

if mise run test:ci; then
  notify "✅ Tests passed"
else
  notify "❌ Tests failed"
  exit 1
fi
```

## Best Practices

### 1. Keep Wrappers Thin

Wrappers should orchestrate, not reimplement:

```toml
# Good: Thin wrapper
[tasks.deploy]
run = "./scripts/deploy.sh ${@}"

# Bad: Logic in wrapper
[tasks.deploy]
run = [
  "docker build -t app .",
  "docker tag app:latest app:v1",
  "docker push app:v1",
  # ... 20 more lines
]
```

Move complex logic to scripts, use mise for orchestration.

### 2. Document Arguments

```toml
[tasks.deploy]
description = """
Deploy application to environment

Usage: mise run deploy <environment> [options]

Arguments:
  <environment>  Target environment (staging|production)

Options:
  --verbose      Show detailed output
  --dry-run      Simulate deployment
"""
run = "./scripts/deploy.sh ${@}"
```

### 3. Add Safety Rails

```toml
[tasks.prod-deploy]
confirm = "Deploy to PRODUCTION?"
depends = ["test", "security-scan"]
run = "./deploy.sh production"
```

### 4. Version Control Requirements

```toml
[tasks.deploy]
tools = ["node@20", "docker@24"]  # Ensure correct versions
run = "./deploy.sh"
```

### 5. Provide Defaults

```bash
#!/usr/bin/env bash
#MISE description="Build with defaults"

ENVIRONMENT=${ENVIRONMENT:-development}
NODE_ENV=${NODE_ENV:-development}

npm run build
```

## Troubleshooting

### Arguments Not Passing Through

Use `${@}` in TOML or `"$@"` in bash:

```toml
# Correct
[tasks.test]
run = "npm test -- ${@}"

# Wrong
[tasks.test]
run = "npm test"  # Ignores arguments
```

### Interactive Commands Not Working

Add `raw = true`:

```toml
[tasks.shell]
raw = true
run = "bash"
```

### Environment Not Available

Check `env` propagation:

```toml
[env]
DATABASE_URL = "postgresql://localhost/db"

[tasks.migrate]
# DATABASE_URL is available
run = "prisma migrate deploy"
```

### Wrong Working Directory

Set explicit `dir`:

```toml
[tasks.build]
dir = "{{ config_root }}/backend"
run = "cargo build"
```

## Examples by Tool Category

### CI/CD Tools

```toml
[tasks."gh:pr"]
description = "Create GitHub pull request"
run = "gh pr create ${@}"

[tasks."gh:deploy"]
description = "Trigger GitHub Actions deployment"
run = "gh workflow run deploy.yml"
```

### Kubernetes

```toml
[tasks."k8s:apply"]
description = "Apply Kubernetes manifests"
dir = "{{ config_root }}/k8s"
run = "kubectl apply -f ${@:-.}"

[tasks."k8s:logs"]
description = "Show pod logs"
raw = true
run = "kubectl logs -f ${@}"
```

### Testing Tools

```toml
[tasks."test:unit"]
run = "pytest tests/unit ${@}"

[tasks."test:e2e"]
raw = true
run = "playwright test ${@}"

[tasks."test:load"]
run = "k6 run ${@:-load-test.js}"
```

## Resources

- [Workflows](./workflows.md) - Complex orchestration patterns
- [Common Workflows](./common-workflows.md) - Standard task patterns
- [Mise Task Configuration](https://mise.jdx.dev/tasks/task-configuration.html)
