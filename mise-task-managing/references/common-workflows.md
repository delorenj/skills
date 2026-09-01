# Common Workflows

Standard mise task patterns for Database, Build, CI, Test, Deploy, and Lint operations.

## Database Workflows

### Basic Database Operations

```toml
[tasks."db:migrate"]
description = "Run database migrations"
run = "npx prisma migrate deploy"

[tasks."db:rollback"]
description = "Rollback last migration"
run = "npx prisma migrate down"

[tasks."db:seed"]
description = "Seed database with initial data"
depends = ["db:migrate"]
run = "npx prisma db seed"

[tasks."db:reset"]
description = "Reset database to clean state"
confirm = "This will destroy all data. Continue?"
run = "npx prisma migrate reset --force"

[tasks."db:studio"]
description = "Open database GUI"
raw = true
run = "npx prisma studio"
```

### Database with Backup

```toml
[tasks."db:backup"]
description = "Backup database"
run = "./scripts/db-backup.sh"

[tasks."db:restore"]
description = "Restore database from backup"
confirm = "Restore database from backup?"
run = "./scripts/db-restore.sh ${@}"

[tasks."db:migrate"]
description = "Migrate with automatic backup"
depends = ["db:backup"]
run = "npx prisma migrate deploy"
```

### Multi-Environment Database

```toml
[env]
DATABASE_URL = "postgresql://localhost/dev"

[tasks."db:migrate:staging"]
description = "Migrate staging database"
env = { DATABASE_URL = "postgresql://staging.db/mydb" }
run = "npx prisma migrate deploy"

[tasks."db:migrate:prod"]
description = "Migrate production database"
env = { DATABASE_URL = "postgresql://prod.db/mydb" }
confirm = "Migrate PRODUCTION database?"
depends = ["test"]
run = "npx prisma migrate deploy"
```

### Database Connection Pooling

```bash
#!/usr/bin/env bash
#MISE description="Setup database connection pool"

set -euo pipefail

# Start pgbouncer
docker compose up -d pgbouncer

# Wait for readiness
echo "Waiting for pgbouncer..."
timeout 30 bash -c 'until nc -z localhost 6432; do sleep 1; done'

echo "Database pool ready"
```

## Build Workflows

### Simple Build

```toml
[tasks.build]
description = "Build the project"
sources = ["src/**/*", "package.json", "tsconfig.json"]
outputs = ["dist/"]
run = "npm run build"
```

### Multi-Stage Build

```toml
[tasks."build:clean"]
description = "Clean build artifacts"
run = "rm -rf dist/"

[tasks."build:compile"]
description = "Compile TypeScript"
depends = ["build:clean"]
sources = ["src/**/*.ts"]
outputs = ["dist/**/*.js"]
run = "tsc"

[tasks."build:bundle"]
description = "Bundle assets"
depends = ["build:compile"]
sources = ["dist/**/*.js"]
outputs = ["dist/bundle.js"]
run = "esbuild dist/index.js --bundle --outfile=dist/bundle.js"

[tasks.build]
description = "Full build pipeline"
depends = ["build:bundle"]
```

### Build with Assets

```toml
[tasks."build:assets"]
description = "Process static assets"
sources = ["assets/**/*"]
outputs = ["public/assets/"]
run = "npm run process-assets"

[tasks."build:code"]
description = "Build application code"
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks.build]
description = "Build code and assets"
depends = ["build:assets", "build:code"]
```

### Environment-Specific Builds

```toml
[tasks."build:dev"]
description = "Development build (fast, unoptimized)"
env = { NODE_ENV = "development" }
run = "vite build --mode development"

[tasks."build:prod"]
description = "Production build (optimized)"
env = { NODE_ENV = "production" }
depends = ["lint", "test"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "vite build --mode production"

[tasks.build]
description = "Default build (production)"
depends = ["build:prod"]
```

### Monorepo Build

```toml
[tasks."build:shared"]
description = "Build shared library"
dir = "{{ config_root }}/packages/shared"
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks."build:api"]
description = "Build API service"
dir = "{{ config_root }}/apps/api"
depends = ["build:shared"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks."build:web"]
description = "Build web application"
dir = "{{ config_root }}/apps/web"
depends = ["build:shared"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks.build]
description = "Build all packages"
depends = ["build:shared", "build:api", "build:web"]
```

## CI Workflows

### Basic CI Pipeline

```toml
[tasks.ci]
description = "Run CI pipeline"
depends = ["lint", "typecheck", "test", "build"]

[tasks.lint]
description = "Lint code"
run = "eslint ."

[tasks.typecheck]
description = "Type check"
run = "tsc --noEmit"

[tasks.test]
description = "Run tests"
run = "vitest run"

[tasks.build]
description = "Build project"
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"
```

### CI with Parallel Checks

```toml
[tasks.ci]
description = "Run CI with parallel checks"
depends = ["checks", "test", "build"]

# These run in parallel
[tasks.checks]
depends = ["lint", "typecheck", "format-check", "security-audit"]

[tasks.lint]
run = "eslint ."

[tasks.typecheck]
run = "tsc --noEmit"

[tasks."format-check"]
run = "prettier --check ."

[tasks."security-audit"]
run = "npm audit --audit-level=moderate"

[tasks.test]
run = "vitest run --coverage"

[tasks.build]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"
```

### CI with Coverage

```toml
[tasks."test:coverage"]
description = "Run tests with coverage"
run = "vitest run --coverage"

[tasks."coverage:report"]
description = "Generate coverage report"
depends = ["test:coverage"]
run = "npx nyc report --reporter=html"

[tasks."coverage:check"]
description = "Enforce coverage thresholds"
depends = ["test:coverage"]
run = "npx nyc check-coverage --lines 80 --functions 80"

[tasks.ci]
depends = ["lint", "coverage:check", "build"]
```

### CI with Artifacts

```bash
#!/usr/bin/env bash
#MISE description="CI pipeline with artifact upload"
#MISE depends=["lint", "test", "build"]

set -euo pipefail

# Run checks
echo "All checks passed"

# Create artifact
echo "Creating artifact..."
tar -czf dist.tar.gz dist/

# Upload (example)
if [ -n "${CI:-}" ]; then
  echo "Uploading artifact..."
  aws s3 cp dist.tar.gz "s3://artifacts/build-$BUILD_NUMBER.tar.gz"
fi
```

## Test Workflows

### Basic Testing

```toml
[tasks.test]
description = "Run all tests"
run = "npm test"

[tasks."test:watch"]
description = "Run tests in watch mode"
raw = true
run = "npm test -- --watch"

[tasks."test:coverage"]
description = "Run tests with coverage"
run = "npm test -- --coverage"
```

### Test Suites

```toml
[tasks."test:unit"]
description = "Run unit tests"
run = "vitest run unit"

[tasks."test:integration"]
description = "Run integration tests"
depends = ["db:migrate"]
run = "vitest run integration"

[tasks."test:e2e"]
description = "Run end-to-end tests"
depends = ["build", "db:seed"]
raw = true
run = "playwright test"

[tasks.test]
description = "Run all test suites"
depends = ["test:unit", "test:integration", "test:e2e"]
```

### Test with Services

```toml
[tasks."test:services:up"]
description = "Start test services"
run = "docker compose -f docker-compose.test.yml up -d"

[tasks."test:services:down"]
description = "Stop test services"
run = "docker compose -f docker-compose.test.yml down"

[tasks.test]
description = "Run tests with services"
depends = ["test:services:up"]
depends_post = ["test:services:down"]
run = "npm test"
```

### Smoke Tests

```toml
[tasks."test:smoke"]
description = "Run smoke tests against deployment"
env = { API_URL = "${TARGET_URL}" }
run = "./scripts/smoke-tests.sh"

[tasks.deploy]
depends = ["build"]
depends_post = ["test:smoke"]
run = "./deploy.sh"
```

## Deploy Workflows

### Simple Deployment

```toml
[tasks.deploy]
description = "Deploy application"
depends = ["test", "build"]
confirm = "Deploy to production?"
run = "./scripts/deploy.sh"
```

### Multi-Stage Deployment

```toml
[tasks."deploy:staging"]
description = "Deploy to staging"
depends = ["build"]
env = { ENVIRONMENT = "staging" }
run = "./scripts/deploy.sh"

[tasks."deploy:smoke"]
description = "Run smoke tests"
depends = ["deploy:staging"]
run = "./scripts/smoke-test.sh"

[tasks."deploy:prod"]
description = "Deploy to production"
depends = ["deploy:smoke"]
confirm = "Deploy to PRODUCTION?"
env = { ENVIRONMENT = "production" }
run = "./scripts/deploy.sh"
```

### Blue-Green Deployment

```bash
#!/usr/bin/env bash
#MISE description="Blue-green deployment"
#MISE depends=["build"]

set -euo pipefail

CURRENT=$(./scripts/get-active-slot.sh)
NEXT=$([[ "$CURRENT" == "blue" ]] && echo "green" || echo "blue")

echo "Current: $CURRENT, Deploying to: $NEXT"

# Deploy to inactive slot
./scripts/deploy-to-slot.sh "$NEXT"

# Run health checks
./scripts/health-check.sh "$NEXT"

# Switch traffic
echo "Switching traffic to $NEXT"
./scripts/switch-traffic.sh "$NEXT"

echo "Deployment complete. Old slot ($CURRENT) still running for rollback"
```

### Deployment with Rollback

```toml
[tasks."deploy:checkpoint"]
description = "Create deployment checkpoint"
run = "./scripts/checkpoint.sh create"

[tasks."deploy:apply"]
description = "Apply deployment"
run = "./scripts/deploy.sh"

[tasks."deploy:rollback"]
description = "Rollback deployment"
confirm = "Rollback to previous version?"
run = "./scripts/checkpoint.sh restore"

[tasks.deploy]
description = "Deploy with rollback capability"
depends = ["deploy:checkpoint", "deploy:apply"]
```

### Kubernetes Deployment

```toml
[tasks."k8s:build"]
description = "Build Docker image"
sources = ["Dockerfile", "src/**/*"]
run = "docker build -t myapp:${VERSION} ."

[tasks."k8s:push"]
description = "Push to container registry"
depends = ["k8s:build"]
run = "docker push myapp:${VERSION}"

[tasks."k8s:deploy"]
description = "Deploy to Kubernetes"
depends = ["k8s:push"]
confirm = "Deploy to Kubernetes?"
run = "kubectl apply -f k8s/"

[tasks."k8s:rollout"]
description = "Wait for rollout"
depends = ["k8s:deploy"]
run = "kubectl rollout status deployment/myapp"

[tasks.deploy]
depends = ["k8s:rollout"]
```

## Lint Workflows

### Basic Linting

```toml
[tasks.lint]
description = "Lint code"
run = "eslint ."

[tasks."lint:fix"]
description = "Fix linting issues"
run = "eslint . --fix"
```

### Multi-Tool Linting

```toml
[tasks."lint:eslint"]
description = "Lint JavaScript/TypeScript"
run = "eslint ."

[tasks."lint:prettier"]
description = "Check code formatting"
run = "prettier --check ."

[tasks."lint:stylelint"]
description = "Lint CSS/SCSS"
run = "stylelint '**/*.{css,scss}'"

[tasks."lint:markdown"]
description = "Lint markdown files"
run = "markdownlint '**/*.md'"

[tasks.lint]
description = "Run all linters"
depends = ["lint:eslint", "lint:prettier", "lint:stylelint", "lint:markdown"]
```

### Lint with Auto-Fix

```toml
[tasks.lint]
description = "Check code quality"
depends = ["lint:check", "format:check"]

[tasks."lint:check"]
run = "eslint ."

[tasks."format:check"]
run = "prettier --check ."

[tasks."lint:fix"]
description = "Fix linting issues"
run = "eslint . --fix"

[tasks."format:fix"]
description = "Format code"
run = "prettier --write ."

[tasks.fix]
description = "Fix all issues"
depends = ["lint:fix", "format:fix"]
```

### Language-Specific Linting

**Rust:**

```toml
[tasks.lint]
description = "Lint Rust code"
run = "cargo clippy -- -D warnings"

[tasks.format]
description = "Format Rust code"
run = "cargo fmt"

[tasks."format:check"]
run = "cargo fmt -- --check"
```

**Python:**

```toml
[tasks.lint]
description = "Lint Python code"
depends = ["lint:ruff", "lint:mypy"]

[tasks."lint:ruff"]
run = "ruff check ."

[tasks."lint:mypy"]
run = "mypy ."

[tasks.format]
description = "Format Python code"
run = "ruff format ."
```

**Go:**

```toml
[tasks.lint]
description = "Lint Go code"
run = "golangci-lint run"

[tasks.format]
description = "Format Go code"
run = "go fmt ./..."
```

## Combined Workflow Patterns

### Full Development Workflow

```toml
[tasks.setup]
description = "Initial project setup"
depends = ["install", "db:migrate", "db:seed"]

[tasks.install]
run = "npm install"

[tasks.dev]
description = "Start development server"
depends = ["install"]
raw = true
run = "npm run dev"

[tasks.lint]
run = "eslint ."

[tasks.test]
depends = ["lint"]
run = "npm test"

[tasks.build]
depends = ["test"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks.deploy]
depends = ["build"]
confirm = "Deploy to production?"
run = "./scripts/deploy.sh"
```

### Pre-Commit Workflow

```toml
[tasks.precommit]
description = "Run pre-commit checks"
depends = ["format:fix", "lint:fix", "test:quick"]

[tasks."format:fix"]
run = "prettier --write ."

[tasks."lint:fix"]
run = "eslint . --fix"

[tasks."test:quick"]
run = "vitest run --changed"
```

### Release Workflow

```toml
[tasks."release:check"]
description = "Pre-release checks"
depends = ["lint", "test", "build"]

[tasks."release:bump"]
description = "Bump version"
run = "npm version ${@:-patch}"

[tasks."release:changelog"]
description = "Generate changelog"
run = "conventional-changelog -p angular -i CHANGELOG.md -s"

[tasks."release:tag"]
description = "Create git tag"
run = "git tag -a v$(node -p require('./package.json').version)"

[tasks."release:publish"]
description = "Publish package"
confirm = "Publish to npm?"
run = "npm publish"

[tasks.release]
description = "Full release process"
depends = ["release:check", "release:bump", "release:changelog", "release:tag", "release:publish"]
```

## Best Practices

### 1. Use Semantic Task Names

```toml
# Good
[tasks."db:migrate"]
[tasks."test:e2e"]
[tasks."deploy:staging"]

# Avoid
[tasks.dbmigrate]
[tasks.teste2e]
[tasks.deploystaging]
```

### 2. Document Complex Workflows

```toml
[tasks.deploy]
description = """
Deploy application to production

Prerequisites:
- All tests passing
- Clean git working directory
- AWS credentials configured

Steps:
1. Build production assets
2. Run smoke tests
3. Create deployment checkpoint
4. Apply deployment
5. Run post-deployment checks
"""
depends = ["build", "test"]
run = "./scripts/deploy.sh"
```

### 3. Make Destructive Actions Explicit

```toml
[tasks."db:reset"]
confirm = "This will DESTROY all data. Continue?"
run = "prisma migrate reset --force"

[tasks."deploy:prod"]
confirm = "Deploy to PRODUCTION?"
depends = ["test"]
run = "./deploy.sh production"
```

### 4. Use Dependencies for Safety

```toml
[tasks.deploy]
depends = ["lint", "test", "build"]  # Must pass first
run = "./deploy.sh"
```

### 5. Cache When Possible

```toml
[tasks.build]
sources = ["src/**/*", "package.json"]
outputs = ["dist/"]
run = "npm run build"
```

## Resources

- [Workflows](./workflows.md) - Complex orchestration patterns
- [Wrapping Interfaces](./wrapping-an-interface.md) - Adapting existing tools
- [Starting Fresh](./starting-fresh.md) - New project setup
- [Brownfield Integration](./brownfield.md) - Existing project integration
