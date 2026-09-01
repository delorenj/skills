# Starting Fresh with Mise

This guide covers setting up mise in a brand new project from scratch.

## Quick Start

1. **Copy the base configuration**

```bash
cp ~/.claude/skills/mise-task-managing/references/base-mise.toml mise.toml
```

2. **Trust the configuration**

```bash
mise trust
```

3. **Verify the setup**

```bash
mise tasks
```

## Project Structure

Create the standard mise directory structure:

```bash
mkdir -p .mise/tasks
```

Your project should now look like:

```
project-root/
├── mise.toml              # Primary config with tools and inline tasks
├── .mise/
│   └── tasks/            # Directory for file-based task scripts
```

## Adding Your First Tool

Define the tools your project needs in `mise.toml`:

```toml
[tools]
node = "20"
python = "3.12"
```

Install them:

```bash
mise install
```

## Creating Your First Task

### Simple TOML Task

Add directly to `mise.toml`:

```toml
[tasks.dev]
description = "Start development server"
run = "npm run dev"

[tasks.build]
description = "Build the project"
run = "npm run build"
depends = ["lint"]

[tasks.lint]
description = "Lint code"
run = "npm run lint"
```

### File-Based Task

For multi-line scripts, create `.mise/tasks/setup`:

```bash
#!/usr/bin/env bash
#MISE description="Setup project dependencies"

set -euo pipefail

echo "Installing dependencies..."
npm install

echo "Setting up git hooks..."
npx husky install

echo "Setup complete!"
```

Make it executable:

```bash
chmod +x .mise/tasks/setup
```

## Initial Task Organization

Organize tasks by domain using colon-separated names:

```toml
[tasks."dev:backend"]
description = "Start backend server"
dir = "{{ config_root }}/backend"
run = "cargo run"

[tasks."dev:frontend"]
description = "Start frontend dev server"
dir = "{{ config_root }}/frontend"
run = "npm run dev"

[tasks.dev]
description = "Start full development environment"
depends = ["dev:backend", "dev:frontend"]
```

## Essential Tasks Checklist

For most projects, start with these core tasks:

```toml
[tasks.install]
description = "Install dependencies"
run = "npm install"  # or pip install, cargo build, etc.

[tasks.lint]
description = "Lint code"
run = "npm run lint"

[tasks.test]
description = "Run tests"
depends = ["lint"]
run = "npm test"

[tasks.build]
description = "Build project"
depends = ["test"]
sources = ["src/**/*"]
outputs = ["dist/"]
run = "npm run build"

[tasks.dev]
description = "Start development server"
run = "npm run dev"
raw = true  # Interactive task

[tasks.clean]
description = "Clean build artifacts"
run = "rm -rf dist/ node_modules/"
```

## Environment Configuration

Set up environment-specific variables:

```toml
[env]
NODE_ENV = "development"
LOG_LEVEL = "debug"

[tasks.build]
description = "Build for development"
run = "npm run build"

[tasks."build:prod"]
description = "Build for production"
env = { NODE_ENV = "production" }
run = "npm run build"
```

## Git Integration

Add to `.gitignore`:

```
# Mise
.mise/cache/
```

Commit to version control:

```
mise.toml
.mise/tasks/
```

## Verification Workflow

After setup, verify everything works:

```bash
# List all tasks
mise tasks

# Test a simple task
mise run lint

# Test task dependencies
mise run build

# Watch for changes
mise watch test
```

## Next Steps

- Define `sources` and `outputs` for build caching
- Create environment-specific task variants
- Add parallel task execution with `depends`
- Set up CI integration (see [common-workflows.md](./common-workflows.md))
- Wrap existing scripts (see [wrapping-an-interface.md](./wrapping-an-interface.md))

## Common Patterns

### Monorepo Setup

```toml
[tasks."app:build"]
description = "Build application"
dir = "{{ config_root }}/apps/web"
run = "npm run build"

[tasks."lib:build"]
description = "Build library"
dir = "{{ config_root }}/packages/lib"
run = "npm run build"

[tasks.build]
description = "Build all packages"
depends = ["lib:build", "app:build"]
```

### Cross-Language Projects

```toml
[tools]
rust = "latest"
node = "20"
python = "3.12"

[tasks.backend]
dir = "{{ config_root }}/backend"
run = "cargo run"

[tasks.frontend]
dir = "{{ config_root }}/frontend"
run = "npm run dev"

[tasks.ml]
dir = "{{ config_root }}/ml"
tools = ["python@3.12"]
run = "python train.py"
```

## Troubleshooting

**Tasks not showing up?**

```bash
mise trust
mise tasks --verbose
```

**Wrong directory?**

Add explicit `dir` to tasks:

```toml
[tasks.task-name]
dir = "{{ config_root }}"
run = "command"
```

**Need interactive input?**

```toml
[tasks.interactive]
raw = true
run = "npm run dev"
```
