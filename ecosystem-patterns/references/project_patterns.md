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
# Feature branch (default)
iMi add feature-name
iMi add -f feature-name
iMi add --feature feature-name

# Pull request worktree (no branch creation)
iMi add --pr 123
iMi add -p 123

# PR review worktree
iMi add --review 123
iMi add -r 123

# PR suggestion branch (from PR)
iMi add --suggestion 123
iMi add -s 123

# Bug fix
iMi add --fix bug-name

# Hotfix (from trunk)
iMi add --hotfix critical-bug

# Custom label
iMi add --custom label-name branch-name

# Experiment (temporary, not for merging)
iMi add --experiment idea-name
```

### Naming Conventions

**Prefixes:**
- `trunk-` - Main branch (e.g., `trunk-main`, `trunk-master`)
- `feature-` - Feature development
- `pr-{number}-` - Pull request worktrees
- `pr-review-{number}-` - Review worktrees
- `pr-suggestion-{number}-` - Suggestion branches from PRs
- `fix-` - Bug fixes
- `hotfix-` - Critical production fixes
- `experiment-` - Temporary experimental work

**Branch Names:**
- Features: `feature/{descriptive-name}`
- Fixes: `fix/{issue-description}`
- Hotfixes: `hotfix/{critical-issue}`
- Experiments: `experiment/{idea-name}`

## Multi-Component Projects

### Umbrella Project Structure

For projects with multiple repositories (like ChoreScore):

```
ChoreScore/                     # Umbrella project
├── chorescore-web/             # Web application repo
│   ├── trunk-main/
│   ├── feature-mvp/
│   └── feature-auth/
├── chorescore-mobile/          # Mobile application repo
│   ├── trunk-main/
│   └── feature-flutter-setup/
├── chorescore-api/             # Backend API repo
│   ├── trunk-main/
│   └── feature-endpoints/
└── chorescore-docs/            # Documentation repo
    └── trunk-main/
```

### Project Initialization Script

```bash
#!/bin/bash
# setup-chorescore.sh

PROJECT_ROOT="$HOME/code/ChoreScore"
ORG="delorenj"

# Create umbrella directory
mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Initialize each component
components=("chorescore-web" "chorescore-mobile" "chorescore-api" "chorescore-docs")

for comp in "${components[@]}"; do
  mkdir -p "$comp"
  cd "$comp"
  gh repo clone "$ORG/$comp" trunk-main
  cd ..
done

echo "✅ All repositories initialized!"
```

## Repository Organization Patterns

### Monorepo vs Multi-Repo

**Use Monorepo When:**
- Shared dependencies between components
- Coordinated releases required
- Small to medium project size
- Team works across all components

**Use Multi-Repo (with iMi umbrella) When:**
- Independent deployment cycles
- Different teams/ownership
- Large, complex projects
- Clear service boundaries

### Standard Repository Structure

**Full-Stack Application:**
```
project-name/
├── trunk-main/
│   ├── src/
│   │   ├── app/              # Next.js app directory
│   │   ├── components/       # React components
│   │   ├── lib/              # Utilities
│   │   └── types/            # TypeScript types
│   ├── public/               # Static assets
│   ├── tests/                # Test files
│   ├── docker/               # Docker configs
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   ├── supabase/             # Backend config
│   │   ├── migrations/
│   │   └── functions/
│   ├── .env.example          # Environment template
│   ├── .mise.toml            # Tool versions
│   ├── package.json          # Dependencies
│   └── README.md             # Documentation
```

**API Service:**
```
api-service/
├── trunk-main/
│   ├── app/                  # FastAPI application
│   │   ├── api/              # API routes
│   │   │   ├── v1/
│   │   │   └── v2/
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── core/             # Configuration
│   ├── tests/                # Test suite
│   ├── alembic/              # Database migrations
│   ├── docker/               # Container configs
│   ├── requirements.txt      # Python dependencies
│   ├── pyproject.toml        # Project metadata
│   └── README.md
```

**Mobile Application (Flutter):**
```
mobile-app/
├── trunk-main/
│   ├── lib/
│   │   ├── main.dart         # Entry point
│   │   ├── screens/          # UI screens
│   │   ├── widgets/          # Reusable widgets
│   │   ├── models/           # Data models
│   │   ├── services/         # API clients
│   │   └── utils/            # Utilities
│   ├── android/              # Android config
│   ├── ios/                  # iOS config
│   ├── test/                 # Tests
│   ├── pubspec.yaml          # Dependencies
│   └── README.md
```

## Obsidian Vault Integration

### Project Documentation Structure

**Location:** `/home/delorenj/code/DeLoDocs/Projects/`

```
DeLoDocs/
├── Projects/
│   ├── 33GOD/                # Agentic workflow project
│   │   ├── PRD.md
│   │   ├── Architecture.md
│   │   ├── iMi/              # iMi tool documentation
│   │   │   └── PRD.md
│   │   └── Components/
│   ├── ChoreScore/           # Household gamification
│   │   ├── PRD.md
│   │   ├── Technical-Architecture.md
│   │   ├── Quick-Start.md
│   │   └── Roadmap.md
│   └── Concierge/            # API gateway
│       └── PRD.md
├── Daily-Notes/              # Daily work logs
│   └── 2025-10-25.md
└── Prompts/                  # AI prompt library
    ├── Code-Review.md
    └── Documentation.md
```

### Project Link Pattern

**Cross-Reference Pattern:**
```markdown
# ChoreScore

Related Projects:
- [[33GOD]] - Agentic workflow system
- [[iMi]] - Worktree management tool
- Component: [[chorescore-web]]
```

## Development Workflow Patterns

### Feature Development Flow

```bash
# 1. Create feature worktree
cd project-name
iMi add feature-new-endpoint

# 2. Develop in worktree
cd feature-new-endpoint
# ... make changes ...

# 3. Commit and push
git add .
git commit -m "feat: add new endpoint"
git push -u origin feature/new-endpoint

# 4. Create pull request
gh pr create --title "Add new endpoint" --body "Description"

# 5. Code review
cd ../trunk-main
iMi add --review 123

# 6. Merge and cleanup
gh pr merge 123
git worktree remove feature-new-endpoint
```

### Hotfix Workflow

```bash
# 1. Create hotfix from trunk
iMi add --hotfix critical-bug

# 2. Fix and test
cd hotfix-critical-bug
# ... fix issue ...

# 3. Fast-track PR
git push -u origin hotfix/critical-bug
gh pr create --title "HOTFIX: Critical bug" --body "Fix description"

# 4. Immediate merge and deploy
gh pr merge --merge
# ... deploy ...
```

### Multi-Agent Parallel Development

```bash
# Multiple features in parallel
iMi add feature-auth        # Agent 1
iMi add feature-database    # Agent 2
iMi add feature-ui          # Agent 3

# Each agent works independently in their worktree
# Real-time visibility via iMi status dashboard
```

## Project Template System

### Template Repository Structure

```
project-template/
├── .github/
│   ├── workflows/           # CI/CD templates
│   └── ISSUE_TEMPLATE/      # Issue templates
├── docker/
│   ├── Dockerfile.dev       # Development image
│   └── Dockerfile.prod      # Production image
├── docker-compose.yml       # Local development
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── .mise.toml               # Tool versions
├── README.template.md       # README template
└── scripts/
    ├── setup.sh             # Project setup
    └── deploy.sh            # Deployment script
```

### Project Initialization from Template

```bash
# Using GitHub template
gh repo create new-project --template org/project-template --private

# Clone with iMi structure
mkdir new-project && cd new-project
gh repo clone org/new-project trunk-main

# Initialize from template script
cd trunk-main
./scripts/setup.sh
```

## Configuration Management

### Tool Version Management (.mise.toml)

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
5. **Use experiments** for throwaway code

### Project Organization
1. **Consistent structure** across all projects
2. **Document everything** in Obsidian vault
3. **Version all dependencies** explicitly
4. **Keep secrets** out of version control
5. **Automate setup** with scripts

### Multi-Component Projects
1. **Clear component boundaries**
2. **Independent deployment** where possible
3. **Shared documentation** in umbrella project
4. **Consistent naming** across components
5. **Cross-reference** in project docs

## Troubleshooting

### Worktree Issues

**Worktree locked:**
```bash
# Remove lock file
rm .git/worktrees/feature-name/locked

# Or force remove
git worktree remove --force feature-name
```

**Branch not tracking:**
```bash
cd feature-name
git branch --set-upstream-to=origin/feature/name
```

**Stale worktrees:**
```bash
# List all worktrees
git worktree list

# Prune deleted worktrees
git worktree prune
```

### Project Setup Issues

**Missing dependencies:**
```bash
# Install all tool versions
mise install

# Verify installation
mise list
```

**Docker network issues:**
```bash
# Recreate networks
docker-compose down
docker network prune -f
docker-compose up -d
```

## Migration Checklist

When starting a new project:

- [ ] Create project directory structure
- [ ] Initialize with iMi workflow
- [ ] Set up .mise.toml for tool versions
- [ ] Create .env.example template
- [ ] Add docker-compose.yml if needed
- [ ] Create README.md with setup instructions
- [ ] Initialize git and push to remote
- [ ] Create Obsidian project documentation
- [ ] Set up CI/CD workflows
- [ ] Configure pre-commit hooks
- [ ] Document architecture decisions
- [ ] Add to project portfolio

## Real-World Examples

### ChoreScore Project
```bash
# Umbrella structure
~/code/ChoreScore/
├── chorescore-web/trunk-main/      # Next.js frontend
├── chorescore-mobile/trunk-main/   # Flutter app
├── chorescore-api/trunk-main/      # FastAPI backend
└── chorescore-sb/trunk-main/       # Supabase config
```

### 33GOD Project
```bash
# Monorepo with iMi
~/code/33GOD/trunk-main/
├── api/                    # FastAPI backend
├── frontend/               # React frontend
├── agents/                 # Agent implementations
└── tools/
    └── iMi/               # iMi tool itself
```

### Concierge API Gateway
```bash
# Simple service
~/code/concierge/
├── trunk-main/            # Main API
├── feature-auth/          # Auth feature
└── pr-review-45/          # Active PR review
```
