---
pipeline-status:
  - new
---
# Integrating Mise into Existing Projects

This guide covers adding mise to projects with existing build tools, task runners, or package managers.

## Assessment Phase

Before integration, identify what you currently have:

### Existing Task Runners

- **Makefile**: Common in C/C++, Go, and legacy projects
- **package.json scripts**: Node.js/npm/pnpm/bun projects
- **Justfile**: Modern Make alternative
- **Taskfile.yml**: Task runner with YAML config
- **pyproject.toml scripts**: Python projects with PDM/Poetry
- **Cargo.toml**: Rust projects
- **shell scripts**: Ad-hoc bash/zsh scripts in `scripts/` or project root

### Tool Version Management

- **asdf**: Multi-language version manager
- **.nvmrc**: Node version
- **.ruby-version**: Ruby version
- **.python-version**: Python version
- **Dockerfile**: Container-based environments

## Integration Strategy

### Non-Destructive Approach

Mise can coexist with existing tools. Start by wrapping them:

```toml
# mise.toml
[tasks.make]
description = "Run legacy Makefile target"
run = "make ${@:-all}"

[tasks.npm]
description = "Run npm script"
run = "npm run ${@}"
```

This allows gradual migration without breaking existing workflows.

## Migration Patterns

### From package.json Scripts

**Before** (package.json):

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "test": "vitest",
    "lint": "eslint . --ext ts,tsx"
  }
}
```

**After** (mise.toml):

```toml
[tasks.dev]
description = "Start development server"
run = "vite"
raw = true

[tasks.lint]
description = "Lint code"
run = "eslint . --ext ts,tsx"

[tasks.test]
description = "Run tests"
depends = ["lint"]
run = "vitest"

[tasks.build]
description = "Build for production"
depends = ["test"]
sources = ["src/**/*", "tsconfig.json"]
outputs = ["dist/"]
run = ["tsc", "vite build"]
```

**Benefits gained:**
- Task dependencies (`depends`)
- Build caching (`sources`/`outputs`)
- Better parallelization
- Cross-project consistency

### From Makefile

**Before** (Makefile):

```makefile
.PHONY: build test clean

build: lint
	cargo build --release

test:
	cargo test

lint:
	cargo clippy

clean:
	rm -rf target/
```

**After** (mise.toml):

```toml
[tasks.lint]
description = "Lint Rust code"
run = "cargo clippy"

[tasks.build]
description = "Build release binary"
depends = ["lint"]
sources = ["src/**/*.rs", "Cargo.toml"]
outputs = ["target/release/"]
run = "cargo build --release"

[tasks.test]
description = "Run Rust tests"
run = "cargo test"

[tasks.clean]
description = "Clean build artifacts"
run = "rm -rf target/"
```

**Benefits gained:**
- Cross-platform compatibility (no Make required)
- Automatic parallel execution
- File watching support (`mise watch`)
- Better dependency visualization

### From Shell Scripts

**Before** (`scripts/deploy.sh`):

```bash
#!/bin/bash
set -e

echo "Running tests..."
npm test

echo "Building..."
npm run build

echo "Deploying..."
./deploy.sh
```

**After** (.mise/tasks/deploy):

```bash
#!/usr/bin/env bash
#MISE description="Deploy application"
#MISE depends=["test", "build"]
#MISE confirm="Deploy to production?"
#MISE env={ENVIRONMENT="production"}

set -euo pipefail

echo "Deploying to production..."
./deploy.sh "$@"
```

**And** (mise.toml):

```toml
[tasks.test]
run = "npm test"

[tasks.build]
run = "npm run build"
sources = ["src/**/*"]
outputs = ["dist/"]
```

**Benefits gained:**
- Dependency management
- Confirmation prompts
- Environment isolation
- Reusable task composition

## Tool Version Migration

### From asdf to Mise

Mise is a drop-in replacement for asdf with backward compatibility.

**Before** (.tool-versions):

```
nodejs 20.10.0
python 3.12.0
rust 1.75.0
```

**After** (mise.toml):

```toml
[tools]
node = "20.10.0"
python = "3.12.0"
rust = "1.75.0"
```

Or keep `.tool-versions` - mise reads it automatically!

### From nvm/rbenv/pyenv

**Before**:
- `.nvmrc`: `20.10.0`
- `.ruby-version`: `3.2.0`
- `.python-version`: `3.12.0`

**After** (mise.toml):

```toml
[tools]
node = "20.10.0"
ruby = "3.2.0"
python = "3.12.0"
```

Mise can also read these files automatically if they exist.

## Hybrid Configurations

### Keep package.json Scripts, Add Mise Tasks

Useful when existing scripts are used by CI/CD or team members:

```toml
# mise.toml - Enhanced orchestration
[tasks.ci]
description = "Run full CI pipeline"
depends = ["lint", "test", "build"]

[tasks.lint]
run = "npm run lint"

[tasks.test]
run = "npm test"

[tasks.build]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks.dev]
description = "Development with hot reload"
run = "npm run dev"
raw = true
```

**Result**: package.json scripts still work, but mise adds dependency management and caching.

### Keep Makefile for Legacy Targets

Some projects need Makefile for historical reasons (build systems, CI):

```toml
# mise.toml - Modern tasks
[tasks.dev]
description = "Start development"
run = "make dev"

[tasks.build]
description = "Build via Make"
run = "make build"

# New mise-native tasks
[tasks."build:watch"]
description = "Watch and rebuild"
run = "make build"
sources = ["src/**/*"]

[tasks.docker]
description = "Build Docker image"
depends = ["build"]
run = "docker build -t myapp ."
```

## Directory Structure Strategies

### Minimal Intrusion

Keep existing structure, add only mise.toml:

```
project-root/
├── mise.toml              # New
├── Makefile              # Existing
├── package.json          # Existing
├── scripts/              # Existing
│   └── deploy.sh
```

### Gradual Migration

Move complex scripts to `.mise/tasks/`:

```
project-root/
├── mise.toml              # New
├── .mise/                # New
│   └── tasks/
│       ├── deploy        # Migrated from scripts/
│       └── ci            # Migrated from CI config
├── Makefile              # Keep for now
├── package.json          # Keep for dependencies
```

### Full Adoption

Replace legacy tools entirely:

```
project-root/
├── mise.toml              # Primary orchestration
├── .mise/
│   └── tasks/            # All task scripts
│       ├── build
│       ├── test
│       ├── deploy
│       └── lint
```

## Team Adoption Strategy

### Phase 1: Coexistence (Week 1)

1. Add `mise.toml` with existing commands wrapped
2. Document in README
3. Make mise optional

```markdown
## Development

### With mise (recommended):
mise run dev

### Without mise (legacy):
npm run dev
```

### Phase 2: Enhancement (Week 2-3)

1. Add mise-specific features (caching, dependencies)
2. Update documentation to prefer mise
3. Train team members

### Phase 3: Migration (Week 4+)

1. Move complex scripts to `.mise/tasks/`
2. Add CI integration
3. Deprecate old tooling
4. Update onboarding docs

## Common Migration Challenges

### Challenge: Complex Makefile Logic

**Solution**: Start with file-based tasks in `.mise/tasks/` that preserve bash logic.

### Challenge: CI/CD Hardcoded Commands

**Solution**: Keep a hybrid approach where both systems work:

```yaml
# .github/workflows/ci.yml
- name: Run tests (mise)
  run: mise run test

# OR fallback to:
- name: Run tests (npm)
  run: npm test
```

### Challenge: Team Resistance

**Solution**:
1. Don't force migration
2. Show value through examples (caching, parallel execution)
3. Provide training and docs
4. Keep old system working alongside

### Challenge: Polyglot Projects

**Solution**: Mise excels here! Consolidate all languages:

```toml
[tools]
node = "20"
python = "3.12"
rust = "latest"
go = "1.21"

[tasks."backend:rs"]
dir = "{{ config_root }}/backend-rust"
run = "cargo run"

[tasks."api:py"]
dir = "{{ config_root }}/api-python"
run = "python main.py"

[tasks."frontend:js"]
dir = "{{ config_root }}/frontend"
run = "npm run dev"
```

## Testing the Migration

### Verification Checklist

```bash
# 1. All tasks listed
mise tasks

# 2. Each task runs
mise run lint
mise run test
mise run build

# 3. Dependencies work
mise tasks deps build

# 4. Caching works
mise run build          # First run
mise run build          # Should skip if cached

# 5. Parallel execution
mise run -j 4 lint test build
```

### Rollback Plan

Keep existing tooling functional during migration:

```bash
# mise.toml tasks just wrap existing commands
[tasks.build]
run = "npm run build"  # Still uses package.json

# If mise fails, fallback works
npm run build
```

## Post-Migration Cleanup

After successful migration (4-8 weeks):

1. Remove unused Makefile targets
2. Simplify package.json scripts
3. Archive old shell scripts
4. Update all documentation
5. Remove redundant CI steps

## Migration Examples by Ecosystem

### Node.js Project

1. Keep `package.json` for dependencies
2. Move scripts from `package.json` to `mise.toml`
3. Add sources/outputs for caching
4. Use mise for task orchestration

### Python Project

1. Keep `pyproject.toml` for dependencies
2. Replace Makefile/tox with mise tasks
3. Use file-based tasks for complex workflows
4. Leverage mise's Python version management

### Rust Project

1. Keep `Cargo.toml` for dependencies
2. Replace Makefile with mise tasks
3. Add caching for build artifacts
4. Use mise for cross-compilation tasks

### Monorepo

1. Root `mise.toml` for global tasks
2. Per-package `mise.toml` for local tasks
3. Use `dir` to run tasks in subprojects
4. Orchestrate with dependencies

## Resources

- [Common Workflows](./common-workflows.md) - Standard task patterns
- [Custom Workflows](./workflows.md) - Complex orchestration
- [Wrapping Interfaces](./wrapping-an-interface.md) - Adapting existing tools
