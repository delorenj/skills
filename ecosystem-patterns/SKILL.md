---
name: ecosystem-patterns
description: "Learns and applies Jarad's unique development patterns by mining conversation history, PRDs, code structures, and workflow preferences. Use when: creating new projects, generating documentation, suggesting architecture, naming files/folders, or when the user references 'my ecosystem', 'my patterns', or 'how I do things'. Extracts naming conventions, stack preferences, project organization (iMi worktrees), Docker patterns, shell configs, and PRD structures from past conversations."
---

# Ecosystem Patterns

## Overview

This skill transforms Claude into an ecosystem-aware assistant by learning from YOUR specific development patterns rather than generic best practices. It mines conversation history, PRD structures, code examples, and workflow preferences to provide personalized guidance that matches YOUR naming conventions, tech stack choices, project organization, and architectural patterns.

## Core Concept

**Question:** What would you know if you had access to every prompt given over a month for a project?

**Answer:** A detailed list of every wish granted, trajectory headed, naming conventions used, file locations chosen, stack information, and task patterns preferred.

**Result:** A self-learning system that captures YOUR patterns, not generic ones.

## Universal Paths

**Environment Variables:**
- `$CODE` = `~/code/` - All project repositories
- `$VAULT` = `~/code/DeLoDocs` - Obsidian vault
- `$CONTAINERS` = `~/docker` - DeLoContainers ecosystem
- `$ZSHYZSH` = `~/.config/zshyzsh` - Shell configuration

**Critical Pattern:** Every repo in `$CODE` has a matching folder in `$VAULT/Projects/` for non-tracked brainstorming and iteration documents.

## Pattern Categories

### 1. Project Structure Patterns (iMi Workflow)

**Key Pattern:** Opinionated git worktree management

**Location:** `$CODE/{project-name}/`

```bash
$CODE/project-name/
├── trunk-main/              # Main repository branch
├── feature-{name}/          # Feature branches
├── pr-{number}-{name}/      # PR worktrees
├── pr-review-{number}/      # Review worktrees
├── experiment-{name}/       # Experimental branches
└── fix-{name}/              # Bug fixes
```

**Vault Documentation:** `$VAULT/Projects/{project-name}/`

```bash
$VAULT/Projects/project-name/
├── PRD.md                   # Product requirements
├── Architecture.md          # Technical architecture
├── Brainstorming.md         # Ideas and iteration
├── Meeting-Notes.md         # Discussion notes
└── Research/                # Background research
```

**Critical Pattern:** Every project in `$CODE` has corresponding documentation in `$VAULT/Projects/` for non-tracked brainstorming and iteration.

**Detection Signals:**
- User mentions "iMi," "worktree," or "trunk-main"
- Project setup questions
- Repository organization discussions

**Application:**
- Always suggest iMi structure for new projects
- Reference existing worktree conventions
- Generate appropriate branch names
- Create matching vault documentation folder

### 2. Docker & Container Patterns (DeLoContainers)

**Key Patterns:**
- Docker Compose for orchestration
- Stack-based organization by domain in `~/docker`
- Portainer for management
- Service naming: `{service}-{environment}`

**Detection Signals:**
- Docker, docker-compose, container mentions
- Service architecture questions
- Deployment discussions

**DeLoContainers Organization:**
```
~/docker/
├── stacks/
│   ├── ai/                    # AI/ML services
│   ├── monitoring/            # Grafana, Prometheus, Loki
│   ├── databases/             # Postgres, Redis, Neo4j
│   └── utilities/             # Portainer, Traefik
└── compose-files/             # Reusable compose configs
```

**Application:**
- Suggest compose file structures matching past patterns
- Reference common service configurations
- Apply consistent naming conventions
- Default to DeLoContainers organization

### 3. Shell Configuration Patterns (zshyzsh)

**Key Patterns:**
- Modular zsh config in `~/.config/zshyzsh/`
- Platform-specific initialization files
- Zellij terminal multiplexing
- Custom aliases and functions
- Terminal logging system

**Structure:**
```
~/.config/zshyzsh/
├── aliases.zsh            # Custom aliases
├── functions.zsh          # Shell functions
├── platforms/             # OS-specific configs
│   ├── macos-init.zsh
│   └── linux-init.zsh
├── zellij/               # Multiplexer configs
└── terminal_logger.sh    # Logging system
```

**Detection Signals:**
- Shell, zsh, terminal, dotfiles mentions
- Alias or function requests
- Cross-platform compatibility questions

**Application:**
- Reference existing aliases before creating new ones
- Maintain cross-platform compatibility
- Follow modular organization pattern

### 4. Tech Stack Preferences

**Backend:**
- FastAPI (Python) for APIs
- PostgreSQL for databases
- FastMCP for Model Context Protocol servers
- Redis for caching and message queues
- UV for Python package management

**Frontend:**
- React with Vite (not Next.js!)
- Tailwind CSS for styling
- ShadCN/UI for components
- TypeScript for type safety

**Runtime:**
- Node.js or Bun for JavaScript
- Python 3.11+ managed with UV

**DevOps:**
- Docker Compose for orchestration
- Mise for tool version management
- n8n for workflow automation
- DeLoContainers ecosystem in `~/docker`

**AI/Agentic:**
- Agno agents (not generic LangChain)
- FastMCP for tool integration
- Custom agent frameworks (33GOD, AgentForge)
- Multi-agent coordination patterns
- Context management systems

**Detection Signals:**
- Stack selection questions
- Framework recommendations
- Architecture discussions

**Application:**
- Default to these technologies unless explicitly requested otherwise
- Reference integration patterns between these tools
- Suggest configurations that match existing setups
- Never assume Supabase/Next.js unless explicitly mentioned

### 5. Documentation Patterns (Obsidian Vault)

**Key Patterns:**
- Complexity/effort metrics instead of time estimates
- Obsidian vault at `$VAULT` (`~/code/DeLoDocs`)
- Project-based folder structure
- Daily notes with templates
- **Every repo has matching vault folder**

**Critical Relationship:**
```
$CODE/project-name/          → $VAULT/Projects/project-name/
$CODE/33GOD/                 → $VAULT/Projects/33GOD/
$CODE/ChoreScore/            → $VAULT/Projects/ChoreScore/
```

**Vault Structure:**
```
$VAULT/
├── Projects/
│   ├── {project-name}/      # Matches $CODE/{project-name}
│   │   ├── PRD.md
│   │   ├── Architecture.md
│   │   ├── Brainstorming.md
│   │   └── Research/
│   ├── 33GOD/
│   └── ChoreScore/
├── Daily-Notes/
│   └── YYYY-MM-DD.md
└── Prompts/                 # AI prompt library
    └── {category}/
```

**PRD Structure:**
```markdown
# Product Name

## Executive Summary
## Problem Statement
## User Personas
## Core Features
## Tech Stack
## Complexity Assessment (not dates!)
## Success Metrics
```

**Detection Signals:**
- Documentation requests
- PRD creation
- Project planning
- "Document this" requests

**Application:**
- Use effort/complexity metrics (Small/Medium/Large/XL)
- Always create matching vault folder for new projects
- Organize in `$VAULT/Projects/{ProjectName}/` folders
- Reference existing PRD patterns
- Apply consistent formatting
- Link project docs with `[[project-name]]` syntax

### 6. Naming Conventions

**Files & Directories:**
- Kebab-case for directories: `my-project-name`
- Snake_case for Python: `my_module.py`
- PascalCase for React: `MyComponent.tsx`
- Uppercase for env files: `.ENV.local`

**Git Branches:**
- `feature/{descriptive-name}`
- `fix/{issue-description}`
- `experiment/{idea-name}`
- `pr-{number}-{description}`

**Database Tables:**
- Lowercase with underscores: `user_profiles`
- Plural for collections: `tasks`, `projects`
- Timestamp fields: `created_at`, `updated_at`

**API Endpoints:**
- RESTful conventions: `/api/v1/resources`
- Plural nouns: `/users`, `/projects`
- Nested resources: `/projects/{id}/tasks`

**Detection Signals:**
- "What should I name this?"
- File/folder creation
- Database design
- API design

**Application:**
- Apply appropriate convention based on context
- Reference existing patterns in codebase
- Suggest names that match established style

## Usage Workflow

### When Creating New Projects

1. **Check for existing project patterns:**
   - Search conversations for similar projects
   - Extract naming conventions from matches
   - Reference tech stack choices

2. **Apply iMi structure:**
   - Suggest worktree organization
   - Provide setup commands
   - Reference existing worktree conventions

3. **Generate PRD using pattern:**
   - Use complexity metrics, not dates
   - Include user personas from past PRDs
   - Apply consistent structure

### When Suggesting Architecture

1. **Reference existing stack patterns:**
   - Default to FastAPI + Supabase + Next.js
   - Suggest Docker Compose configuration
   - Apply layered abstraction principles

2. **Check for integration patterns:**
   - Look for past integrations of similar services
   - Reference existing configurations
   - Suggest tested patterns

3. **Apply naming conventions:**
   - Match file/folder structures
   - Use established branch naming
   - Follow API conventions

### When Generating Code

1. **Extract code style from history:**
   - Search for similar implementations
   - Copy import patterns
   - Match comment styles

2. **Reference existing utilities:**
   - Check for helper functions
   - Look for custom hooks/components
   - Find configuration patterns

3. **Apply architectural patterns:**
   - Layered abstraction (data/logic/presentation)
   - API-first design
   - Modular microservices

## Pattern Mining Process

### What to Look For in Conversations

**Project Requests:**
- What tech stacks are chosen?
- How are projects structured?
- What naming conventions emerge?

**Problem-Solving Patterns:**
- What approaches are preferred?
- Which tools are frequently mentioned?
- What trade-offs are discussed?

**Code Reviews:**
- What feedback is given repeatedly?
- What patterns are praised?
- What anti-patterns are corrected?

**Documentation Style:**
- How are features described?
- What level of detail is preferred?
- How are complexities communicated?

### Pattern Confidence Levels

**HIGH CONFIDENCE (3+ occurrences):**
- Apply automatically
- Reference explicitly
- Use as defaults

**MEDIUM CONFIDENCE (2 occurrences):**
- Suggest as option
- Confirm before applying
- Mention alternative exists

**LOW CONFIDENCE (1 occurrence):**
- Don't apply automatically
- Ask for clarification
- Learn from response

## Critical Reminders

**Universal Paths:**
- All projects: `$CODE` = `~/code/`
- Documentation: `$VAULT` = `~/code/DeLoDocs`
- Containers: `~/docker` (DeLoContainers)
- Shell config: `~/.config/zshyzsh`
- ALWAYS use absolute paths: `/home/delorenj/code/project`
- NEVER use relative paths unless explicitly requested
- Every repo in `$CODE` has matching folder in `$VAULT/Projects/`

**Stack Awareness:**
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: React + Vite + Tailwind + ShadCN
- Python: UV for package management
- Runtime: Node/Bun
- AI: Agno agents, FastMCP
- MCP: FastMCP for tool servers
- Never assume Next.js or Supabase unless explicitly mentioned

**Workflow Patterns:**
- iMi worktrees for all project organization
- Mise for tool versioning
- Modular zsh configs in `~/.config/zshyzsh`
- Docker Compose for services in `~/docker`
- Vault docs in `$VAULT/Projects/` for every project

**Communication Style:**
- Direct, concise, technical authority
- No em dashes
- Medium-depth explanations (~200 words)
- Speak as peer, not explainer

## Resources

### scripts/
- `pattern_miner.py` - Analyzes conversation history for patterns
- `prd_extractor.py` - Extracts PRD structure patterns
- `naming_analyzer.py` - Identifies naming convention patterns

### references/
- `docker_patterns.md` - Comprehensive Docker/compose patterns
- `zshyzsh_patterns.md` - Shell configuration patterns
- `project_patterns.md` - iMi workflow and project structures
- `code_patterns.md` - Language-specific style guides
- `prd_template.md` - Standard PRD structure with examples

### assets/
- `prd_template.md` - Reusable PRD template
- `docker-compose.yml` - Standard compose file template
- `worktree_setup.sh` - iMi initialization script
