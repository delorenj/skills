# iMi Worktree Conventions

Deep dive into iMi's opinionated structure, naming rules, and workflow patterns.

## Directory Structure Philosophy

iMi enforces a strict directory layout that enables predictable navigation, tooling integration, and 33GOD ecosystem coordination.

### Standard Layout

```
/home/delorenj/code/
├── iMi/                          # Example project
│   ├── trunk-main/               # Main branch worktree (source of truth)
│   ├── feat-mcp-server/          # Feature: MCP server implementation
│   ├── feat-create-project/      # Feature: Project creation command
│   ├── fix-json-collision/       # Fix: Bug fix for JSON parameter
│   ├── aiops-custom-types/       # AI Ops: Custom type system
│   ├── devops-ci-pipeline/       # DevOps: CI/CD setup
│   └── pr-review-456/            # PR Review: Review of PR #456
```

### Key Principles

**1. Trunk Isolation**
- Main branch worktree is always `trunk-<branch-name>`
- Never commit directly to trunk - use feature worktrees
- Trunk is for merging, pulling, and baseline reference

**2. Type-Based Naming**
- Worktree directory: `<type-prefix><name>` (e.g., `feat-user-auth`)
- Git branch: `<type-prefix>/<name>` (e.g., `feat/user-auth`)
- Prefix consistency enforced by database types

**3. Database-Driven Metadata**
- SQLite database tracks all worktrees, types, and activity
- Database location: `~/.local/share/iMi/imi.db`
- Automatic sync with `git worktree list`

## Naming Rules

### Worktree Directory Names

**Pattern:** `<worktree-prefix><name>`

Examples:
- `feat-user-authentication` - Feature worktree
- `fix-login-bug` - Fix worktree
- `aiops-claude-skill` - AI operations worktree
- `devops-docker-setup` - DevOps worktree
- `pr-review-123` - PR review worktree
- `experiment-neural-net` - Custom type worktree

**Rules:**
- Lowercase only
- Hyphens separate words
- No underscores or spaces
- Descriptive, not abbreviated

### Git Branch Names

**Pattern:** `<branch-prefix>/<name>`

Examples:
- `feat/user-authentication`
- `fix/login-bug`
- `aiops/claude-skill`
- `devops/docker-setup`
- `pr-review/123`
- `experiment/neural-net`

**Rules:**
- Forward slash separator (Git convention)
- Name matches worktree directory (minus prefix)
- Type prefix must match database definition

### Trunk Worktree

**Pattern:** `trunk-<default-branch>`

Examples:
- `trunk-main` - For repos with `main` as default
- `trunk-master` - For repos with `master` as default
- `trunk-develop` - For repos with `develop` as default

**Rules:**
- Always lowercase
- Always `trunk-` prefix
- Never commit directly
- Source of truth for merges

## Workflow Patterns

### Feature Development (Standard)

```bash
# 1. Create feature worktree from trunk
cd /home/delorenj/code/iMi/trunk-main
imi add feat user-authentication

# 2. Navigate and develop
cd ../feat-user-authentication
# ... develop, commit, push ...

# 3. Create PR
gh pr create --title "Add user authentication" --body "..."

# 4. Merge and cleanup
cd ../trunk-main
git pull  # Get merged changes
imi remove feat-user-authentication  # Remove worktree + branches
```

### Bug Fix (Hotfix)

```bash
# 1. Create fix worktree
imi add fix critical-security-bug

# 2. Fix and test
cd ../fix-critical-security-bug
# ... fix, test, commit ...

# 3. Create PR with urgency label
gh pr create --title "Fix critical security bug" --label "urgent"

# 4. Merge and cleanup
cd ../trunk-main
git pull
imi remove fix-critical-security-bug
```

### PR Review

```bash
# 1. Create review worktree (fetches PR branch automatically)
imi review 456

# 2. Review code
cd pr-review-456
# ... read code, test locally, verify changes ...

# 3. Comment on GitHub
gh pr review 456 --comment --body "Looks good, approved!"

# 4. Cleanup
imi remove pr-review-456
```

### AI Operations (33GOD-specific)

```bash
# 1. Create AI ops worktree
imi add aiops custom-agent-skill

# 2. Develop agent/skill/workflow
cd ../aiops-custom-agent-skill
# ... write skill, test with Claude Code ...

# 3. Integrate with Bloodbank
# Publish event: imi.worktree.created → triggers Jelmore coordination

# 4. Merge and deploy
gh pr create
# ... PR merged ...
cd ../trunk-main && git pull
imi remove aiops-custom-agent-skill
```

### DevOps Tasks

```bash
# 1. Create devops worktree
imi add devops github-actions-ci

# 2. Configure CI/CD
cd ../devops-github-actions-ci
# ... write .github/workflows/, update mise tasks ...

# 3. Test CI pipeline
git push
gh run watch  # Watch GitHub Actions run

# 4. Merge and cleanup
gh pr create
cd ../trunk-main && git pull
imi remove devops-github-actions-ci
```

### Custom Type Workflow

```bash
# 1. Define custom type
imi types add prototype --description "Prototype features for testing"

# 2. Create custom worktree
imi add prototype voice-interface

# 3. Develop experimental feature
cd ../prototype-voice-interface
# ... experiment with risky/exploratory work ...

# 4. Decide: Keep or discard
# Keep: gh pr create
# Discard: imi remove prototype-voice-interface --keep-remote=false
```

## Database Schema

### worktree_types Table

```sql
CREATE TABLE worktree_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    branch_prefix TEXT NOT NULL,
    worktree_prefix TEXT NOT NULL,
    description TEXT,
    is_builtin BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
```

**Built-in Types (is_builtin=true):**
- Cannot be removed
- Seeded on first database init
- Core to 33GOD workflows

**Custom Types (is_builtin=false):**
- User-defined via `imi types add`
- Can be removed with `imi types remove`
- Extend iMi for project-specific needs

### worktrees Table

```sql
CREATE TABLE worktrees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    branch TEXT NOT NULL,
    worktree_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_activity TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id),
    FOREIGN KEY (worktree_type) REFERENCES worktree_types(name)
);
```

**Key Fields:**
- `worktree_type`: References worktree_types.name
- `last_activity`: Updated on navigation, commits, etc.
- `path`: Absolute path to worktree directory

## 33GOD Ecosystem Integration

### Bloodbank Events

**Published Events:**
```json
{
  "event": "imi.worktree.created",
  "data": {
    "worktree_name": "feat-user-auth",
    "worktree_type": "feat",
    "repo": "iMi",
    "branch": "feat/user-auth"
  }
}
```

```json
{
  "event": "imi.project.created",
  "data": {
    "project_name": "TaskMaster",
    "github_url": "https://github.com/delorenj/TaskMaster",
    "stack": "PythonFastAPI"
  }
}
```

**Consumed Events:**
```json
{
  "event": "bloodbank.orchestration.create_worktree",
  "data": {
    "worktree_type": "aiops",
    "name": "auto-generated-skill",
    "repo": "33GOD"
  }
}
```

### Jelmore Session Context

iMi provides session-aware context to Jelmore:
- Current active worktree
- Worktree type for task categorization
- Branch status for coordination

### Flume Task Lifecycle

Automatic task creation when worktrees are created:
```json
{
  "task_id": "task-123",
  "title": "Complete feat-user-auth implementation",
  "worktree": "feat-user-auth",
  "status": "in_progress"
}
```

Task completion triggers cleanup workflow.

## Navigation Shortcuts

### Using iMi Go

```bash
# Fuzzy search navigation
cd $(imi go user-auth --json | jq -r '.data.target_path')

# Exact repo navigation
cd $(imi go --repo iMi trunk --json | jq -r '.data.target_path')
```

### Shell Aliases (Recommended)

Add to `.zshrc`:
```zsh
# Navigate to worktree
alias ig='cd $(imi go "$1" --json | jq -r ".data.target_path")'

# Quick worktree creation
alias ifa='imi add feat'
alias ixa='imi add fix'
alias iaa='imi add aiops'
alias ida='imi add devops'

# List worktrees
alias il='imi list'
alias ilt='imi types list'
```

Usage:
```bash
ig user-auth       # cd to feat-user-auth
ifa my-feature     # imi add feat my-feature
il                 # List all worktrees
```

## Common Pitfalls

### Anti-Pattern: Committing to Trunk

**Wrong:**
```bash
cd trunk-main
git commit -m "Quick fix"  # ❌ Never do this
```

**Right:**
```bash
imi add fix quick-fix
cd ../fix-quick-fix
# ... make changes ...
git commit -m "Quick fix"
gh pr create
```

### Anti-Pattern: Manual Worktree Creation

**Wrong:**
```bash
git worktree add ../my-feature  # ❌ Bypasses iMi database
```

**Right:**
```bash
imi add feat my-feature  # ✅ Tracked in database
```

### Anti-Pattern: Inconsistent Naming

**Wrong:**
```bash
imi add feat "User Auth Feature"  # ❌ Spaces, caps
```

**Right:**
```bash
imi add feat user-auth-feature  # ✅ Lowercase, hyphens
```

## Migration from Manual Worktrees

If you have existing manual git worktrees:

```bash
# 1. Sync database with git state
imi sync

# 2. Verify all worktrees are tracked
imi list

# 3. For untracked worktrees, either:
# a) Remove and recreate with iMi
imi remove <name>
imi add <type> <name>

# b) Or manually insert into database (advanced)
sqlite3 ~/.local/share/iMi/imi.db "INSERT INTO worktrees ..."
```

## Advanced: Multi-Repository Workflows

iMi supports managing multiple repositories:

```bash
# List all projects
imi list --projects

# Create worktree in specific repo
imi add feat user-auth --repo TaskMaster

# Navigate across repos
imi go user-auth --repo TaskMaster
```

**Directory structure with multiple repos:**
```
/home/delorenj/code/
├── iMi/
│   ├── trunk-main/
│   └── feat-mcp-server/
├── TaskMaster/
│   ├── trunk-main/
│   └── feat-user-auth/
└── ChoreScore/
    ├── trunk-main/
    └── fix-points-bug/
```
