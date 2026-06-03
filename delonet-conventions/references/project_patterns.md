---
pipeline-status:
  - new
---
# Project Structure & Vault Integration Patterns

## Universal Paths

**Environment:**

- `$CODE` = `~/code/` - All project repositories
- `$VAULT` = `~/code/DeLoDocs` - Obsidian documentation vault
- `$CONTAINERS` = `~/docker` - DeLoContainers ecosystem
- `$ZSHYZSH` = `~/.config/zshyzsh` - Shell configuration

**Critical Convention:** `exported` paths are ALWAYS in caps. `aliases` and `functions` are ALWAYS lowercase. For every exported path, there should be an alias to navigate to it quickly.

```bash
export CODE="$HOME/code"
export VAULT="$HOME/code/DeLoDocs"
export CONTAINERS="$HOME/docker"

alias code='cd $CODE'
alias vault='cd $VAULT'
alias containers='cd $CONTAINERS'
```

## $CODE and $VAULT Relationship

**Critical Pattern:** Every repo in `$CODE` (ideally) has a matching folder in `$VAULT/Projects/` for non-tracked brainstorming and iteration documents. There is a `helper.zsh` script function `syncDocs` that ensures this relationship is maintained.

This works because I write code in the terminal but view docs in Obsidian.

**Limitation:** There's no single source of truth since the docs are duplicated. Symlinking causes rendering issues in Obsidian and conflicts.

### Vault Documentation Structure

```
$VAULT/Projects/project-name/
├── PRD.md                   # Product requirements document
├── Architecture.md          # Technical architecture
├── Brainstorming.md         # Ideas and iteration
├── Meeting-Notes.md         # Discussion notes
├── Research/                # Background research
│   ├── competitor-analysis.md
│   └── tech-evaluation.md
└── Decisions/               # Architecture decision records
    └── 001-tech-stack.md
```

## Standard Project Structure

### Top-Level Organization

```
$CODE/project-name/
├── trunk-main/              # Main repository branch (always present)
├── feat-{name}/             # Feature development branches
├── fix-{name}/              # Bug fix branches
├── pr-{number}/             # Pull request worktrees
└── experiment-{name}/       # Experimental branches (not for merging)
```

## Configuration Management

### Tool Version Management (mise.toml)

Mise is the primary tooling and package versioning utility. EVERYTHING that CAN be managed with Mise should be managed with Mise. If you find something managed by another tool, migrate it to Mise and remove the old tooling.

```toml
[tools]
node = "20"
python = "3.11"
go = "1.21"

[env]
_.file = ".env"

[tasks.dev]
description = "Start development server"
run = "docker compose up -d"

[tasks.test]
description = "Run test suite"
run = "pytest tests/"

[tasks.deploy]
description = "Deploy to production"
run = "./scripts/deploy.sh"
```

### Environment Configuration (.env pattern)

```bash
# .env.example (committed to repo)
# Copy to .env and fill in values

# Application
NODE_ENV=development
PORT=3000
LOG_LEVEL=info

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379

# External Services
OPENAI_API_KEY=your-api-key
```

## Document Pruning Rule

After each large task, prune and refactor docs to keep them minimal and useful. Rule of thumb: If you created 10 docs in a session, delete 9 of them and keep only the best one.

NEVER put documents randomly in the root of a repo. Use the vault for that.

## Best Practices

1. **Consistent structure** across all projects
2. **Document everything** in Obsidian vault (not in repo root)
3. **Version all dependencies** explicitly via mise.toml
4. **Keep secrets** out of version control
5. **Automate setup** with `mise tasks`
