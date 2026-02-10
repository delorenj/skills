# Project Structure & iMi Workflow Patterns

## iMi Philosophy

**Opinionated Git Worktree Management:** A Rust-based tool designed for asynchronous, parallel multi-agent workflows with real-time visibility into worktree activities.

**Core Principle:** Convention over configuration for simplified, productive development.

## Universal Paths

**Environment:**

- `$CODE` = `~/code/` - All project repositories
- `$VAULT` = `~/code/DeLoDocs` - Obsidian documentation vault
- `$CONTAINERS` = `~/docker` - DeLoContainers ecosystem
- `$ZSHYZSH` = `~/.config/zshyzsh` - Shell configuration

**Critical Pattern:** Every repo in `$CODE` has a matching folder in `$VAULT/Projects/` for non-tracked brainstorming and iteration documents.

## Standard Project Structure

### Top-Level Organization

```
$CODE/project-name/
├── trunk-main/              # Main repository branch (always present)
├── feature-{name}/          # Feature development branches
├── pr-{number}-{name}/      # Pull request worktrees
├── pr-review-{number}/      # PR review worktrees
├── pr-suggestion-{number}/  # PR suggestion branches
├── fix-{name}/              # Bug fix branches
├── hotfix-{name}/           # Critical fix branches
└── experiment-{name}/       # Experimental branches (not for merging)
```

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

## iMi Workflow Commands

### Core Operations

**Initialize Project:**

```bash
# Create project directory
mkdir project-name && cd project-name

# Clone trunk branch
gh repo clone org/project-name trunk-main
```

**Add Worktrees:**

```bash
# Create a Feature branch
iMi feat feature-name

# Pull request worktree (no branch creation)
iMi pr 123 [org/repo]

# Bug fix
iMi fix bug-name

```

### Naming Conventions

**Prefixes:**

- `trunk-` - Main branch (e.g., `trunk-main`, `trunk-master`)
- `feat-` - Feature development
- `pr-{number}` - Pull request worktrees
- `fix-` - Bug fixes

**Branch Names:**

- Features: `feat/{descriptive-name}`
- Fixes: `fix/{issue-description}`

## Obsidian Vault Integration

### Project Documentation Structure

**Location:** `/home/delorenj/code/DeLoDocs/Projects/`

```
DeLoDocs/
├── Projects/
│   ├── SomeRepo/
```

## Development Workflow Patterns

### Feature Development Flow

```bash
# 1. Create feature worktree
iMi feat some-repo-name feature-new-endpoint

# 2. Develop in worktree
igo some-repo-name feature-new-endpoint #cd into dir
# ... make changes ...

# 3. Commit and push
iMi sync
# git add .
# git commit -m "feat: add new endpoint"
# git push -u origin feature/new-endpoint

# 4. Create pull request
iMi submit
#gh pr create --title "Add new endpoint" --body "Description"

# 5. Code review
iMi pr 123 some-repo-name

# 6. Merge and cleanup
iMi merge
#gh pr merge 123
#git worktree remove feature-new-endpoint
```

## Configuration Management

### Tool Version Management (mise.toml)

```toml
[tools]
node = "20"
python = "3.11"
go = "1.21"

[env]
_.file = ".env"

[tasks.dev]
description = "Start development server"
run = "docker-compose up -d"

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
SUPABASE_URL=your-project-url
SUPABASE_ANON_KEY=your-anon-key
OPENAI_API_KEY=your-api-key

# Feature Flags
FEATURE_NEW_UI=true
FEATURE_BETA_API=false
```

## Best Practices

### iMi Workflow

1. **Always work in worktrees**, never directly in trunk
2. **Keep trunk-main pristine** and always up to date
3. **Name worktrees descriptively** for clarity
4. **Remove worktrees** after merging PRs

### Project Organization

1. **Consistent structure** across all projects
2. **Document everything** in Obsidian vault
3. **Version all dependencies** explicitly
4. **Keep secrets** out of version control
5. **Automate setup** with `mise tasks`

## Troubleshooting

### Worktree Issues

**First try `iMi repair`**

```bash
iMi repair
```
