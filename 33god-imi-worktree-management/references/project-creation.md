# iMi Project Creation Reference

Comprehensive guide to iMi's project scaffolding system with stack detection, boilerplate generation, and GitHub integration.

## Overview

`imi project create` bootstraps complete projects with:
- GitHub repository creation
- Stack-specific boilerplate (Python/FastAPI, React/Vite, Generic)
- mise configuration and tasks
- Docker Compose setup
- Git initialization and remote push

## Stack Detection

### Detection Logic

iMi analyzes the project concept/PRD for stack indicators:

**Python/FastAPI Detection:**
- Keywords: "python", "fastapi", "uvicorn", "api", "backend", "rest"
- File patterns: `pyproject.toml`, `requirements.txt`
- Stack ID: `PythonFastAPI`

**React/Vite Detection:**
- Keywords: "react", "vite", "typescript", "frontend", "ui", "dashboard"
- File patterns: `package.json` with vite, `tsconfig.json`
- Stack ID: `ReactVite`

**Generic Fallback:**
- When no specific stack is detected
- Minimal boilerplate
- Stack ID: `Generic`

### Stack Selection Priority

1. Explicit stack in payload: `{"stack": "PythonFastAPI"}`
2. Keyword detection in concept/PRD
3. Generic fallback

## Boilerplate Templates

### Python/FastAPI Stack

**Generated Files:**
```
ProjectName/
├── pyproject.toml          # UV project config
├── mise.toml               # Tool version management
├── .mise/
│   └── tasks/
│       ├── dev             # Start FastAPI server
│       └── test            # Run pytest
├── compose.yml             # Docker Compose (empty, TODO)
├── src/
│   └── project_name/
│       ├── __init__.py
│       └── main.py         # FastAPI app with /health endpoint
├── tests/
│   └── __init__.py
├── README.md               # Project documentation
└── .gitignore              # Python-specific ignores
```

**pyproject.toml Template:**
```toml
[project]
name = "project-name"
version = "0.1.0"
description = "Project concept from user input"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]",
    "uvicorn[standard]",
    "pydantic",
    "pydantic-settings",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/project_name"]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
]
```

**mise.toml Template:**
```toml
[tools]
python = "3.12"

[env]
# Environment variables

[tasks.dev]
description = "Start development server"
run = "uv run uvicorn src.project_name.main:app --reload"

[tasks.test]
description = "Run tests"
run = "uv run pytest"
```

**main.py Template:**
```python
from fastapi import FastAPI

app = FastAPI(title="project-name")

@app.get("/")
async def root():
    return {"message": "Hello from project-name"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### React/Vite Stack

**Generated Files:**
```
ProjectName/
├── package.json            # Bun project config
├── mise.toml               # Tool version management
├── .mise/
│   └── tasks/
│       ├── dev             # Start Vite dev server
│       └── build           # Build for production
├── compose.yml             # Docker Compose (empty, TODO)
├── tsconfig.json           # TypeScript config
├── vite.config.ts          # Vite configuration
├── src/
│   ├── main.tsx           # React entry point
│   ├── App.tsx            # Main app component
│   └── index.css          # Tailwind CSS imports
├── public/
│   └── vite.svg
├── index.html              # HTML entry point
├── README.md               # Project documentation
└── .gitignore              # Node-specific ignores
```

**package.json Template:**
```json
{
  "name": "project-name",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.24",
    "tailwindcss": "^3.3.2",
    "typescript": "^5.0.0",
    "vite": "^4.3.9"
  }
}
```

**mise.toml Template:**
```toml
[tools]
node = "20"
bun = "latest"

[tasks.dev]
description = "Start development server"
run = "bun run dev"

[tasks.build]
description = "Build for production"
run = "bun run build"
```

### Generic Stack

**Generated Files:**
```
ProjectName/
├── mise.toml               # Tool version management
├── .mise/
│   └── tasks/
│       ├── dev             # Generic dev task
│       └── test            # Generic test task
├── src/                    # Empty directory
├── README.md               # Minimal documentation
└── .gitignore              # Basic ignores
```

**mise.toml Template:**
```toml
[tools]

[env]

[tasks.dev]
description = "Start development server"
run = "echo 'Development server starting...'"

[tasks.test]
description = "Run tests"
run = "echo 'Running tests...'"
```

## GitHub Integration

### Repository Creation

**API Endpoint:** `POST https://api.github.com/user/repos`

**Request Payload:**
```json
{
  "name": "ProjectName",
  "description": "Project concept from user input",
  "private": false,
  "auto_init": false,
  "has_issues": true,
  "has_projects": true,
  "has_wiki": false
}
```

**Authentication:**
- Requires `GITHUB_TOKEN` environment variable
- Or `gh` CLI authenticated session

**Checks:**
1. Verify token exists
2. Check if repository already exists
3. Create repository via REST API
4. Return GitHub URL

### Git Initialization

**Sequence:**
```bash
git init
git add .
git commit -m "Initial commit

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git remote add origin https://github.com/username/ProjectName.git
git push -u origin main
```

**Error Handling:**
- Repository creation failures → clean up local directory
- Push failures → warn user, leave local repository intact
- Authentication failures → provide setup instructions

## Input Modes

### 1. Concept Mode (Natural Language)

**Usage:**
```bash
imi project create --concept "FastAPI backend for task management with PostgreSQL" --name TaskMaster
```

**Processing:**
1. Extract project name (from `--name` or infer from concept)
2. Detect stack from keywords
3. Generate appropriate boilerplate
4. Use concept as project description

**Example Concepts:**
- "A dashboard to track my daily steps and exercise using React"
- "Python CLI tool for managing Docker containers"
- "REST API for blog platform with user authentication"

### 2. PRD Mode (Markdown File)

**Usage:**
```bash
imi project create --prd ./project-spec.md --name TaskMaster
```

**Processing:**
1. Read PRD markdown file
2. Extract project name from frontmatter or heading
3. Parse stack requirements from technical section
4. Use PRD content as project description

**Example PRD Structure:**
```markdown
# TaskMaster Project Specification

## Overview
A task management system with priority queues and deadline tracking.

## Technical Requirements
- **Backend:** FastAPI with PostgreSQL
- **Frontend:** React with TypeScript
- **Deployment:** Docker Compose

## Features
- User authentication
- Task CRUD operations
- Priority sorting
```

### 3. Payload Mode (Structured JSON)

**Usage:**
```bash
imi project create --payload '{
  "name": "TaskMaster",
  "stack": "PythonFastAPI",
  "database": "postgres",
  "description": "Task management system"
}'
```

**Processing:**
1. Parse JSON payload
2. Extract all fields directly
3. Override stack detection if `stack` provided
4. Apply field-specific configurations

**Payload Schema:**
```json
{
  "name": "string (required)",
  "stack": "PythonFastAPI | ReactVite | Generic",
  "database": "postgres | redis | qdrant",
  "description": "string",
  "visibility": "public | private"
}
```

## Service Integration (TODO)

### Native Service Configuration

**Planned:** Auto-configure `compose.yml` with native services:

**PostgreSQL:**
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_HOST: 192.168.1.12
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${DEFAULT_USERNAME}
      POSTGRES_PASSWORD: ${DEFAULT_PASSWORD}
```

**Redis:**
```yaml
services:
  redis:
    image: redis:7
    environment:
      REDIS_HOST: 192.168.1.12
      REDIS_PORT: 6379
```

**Qdrant:**
```yaml
services:
  qdrant:
    external: true
    environment:
      QDRANT_URL: https://qdrant.delo.sh
```

**Status:** Deferred - compose.yml currently empty

## README Generation

### Template Structure

```markdown
# {{project_name}}

{{project_description}}

## Stack

{{stack_details}}

## Getting Started

### Prerequisites

- [mise](https://mise.jdx.dev/) for tool version management
{{#if python}}
- Python {{python_version}}+
{{/if}}
{{#if node}}
- Node.js {{node_version}}+
{{/if}}

### Installation

```bash
# Install tools and dependencies
mise install
{{#if python}}
uv sync
{{/if}}
{{#if node}}
bun install
{{/if}}
```

### Development

```bash
# Start development server
mise run dev
```

### Available Tasks

{{#each mise_tasks}}
- `mise run {{name}}` - {{description}}
{{/each}}

## Project Structure

{{directory_tree}}

## License

MIT
```

**Stack Details by Type:**
- **PythonFastAPI:** "Python 3.12+ with FastAPI, UV package manager, and pytest"
- **ReactVite:** "TypeScript + React + Vite + Tailwind CSS + shadcn/ui"
- **Generic:** (Empty - to be filled by user)

## Workflow Integration

### Post-Creation Workflow

**Automatic:**
1. Project created in `/home/delorenj/code/ProjectName/`
2. Trunk worktree created: `trunk-main/`
3. Database entry for repository
4. GitHub repository created and pushed

**Next Steps (Manual):**
```bash
cd ProjectName/trunk-main
mise install              # Install tools
uv sync  # or bun install
mise run dev              # Start development

# Create first feature
cd ..
imi add feat initial-setup
cd feat-initial-setup
# ... develop ...
```

### Bloodbank Event

Published after successful project creation:
```json
{
  "event": "imi.project.created",
  "timestamp": "2025-12-30T00:00:00Z",
  "data": {
    "project_name": "TaskMaster",
    "project_path": "/home/delorenj/code/TaskMaster",
    "github_url": "https://github.com/delorenj/TaskMaster",
    "stack": "PythonFastAPI",
    "trunk_worktree": "/home/delorenj/code/TaskMaster/trunk-main"
  }
}
```

## Error Scenarios

### GitHub Authentication Failed

```
Error: GITHUB_TOKEN environment variable not set.

Solutions:
1. export GITHUB_TOKEN=<your-token>
2. gh auth login
```

### Repository Already Exists

```
Error: Repository 'ProjectName' already exists on GitHub.

Solutions:
1. Use different project name
2. Delete existing repository
3. Clone existing repository instead
```

### Stack Detection Ambiguous

```
Warning: Multiple stacks detected. Using PythonFastAPI.

Detected keywords:
- python, fastapi (→ PythonFastAPI)
- react, vite (→ ReactVite)

Use --payload '{"stack": "ReactVite"}' to override.
```

## Extension Points

### Custom Stack Templates

**Future:** Plugin system for custom stack templates:

```bash
imi project create --stack custom-django-htmx --concept "..."
```

**Template Location:** `~/.config/iMi/templates/custom-django-htmx/`

### Template Variables

All templates support Tera template syntax:

```toml
[project]
name = "{{ project_name }}"
description = "{{ project_description }}"
version = "{{ project_version | default(value='0.1.0') }}"
```

**Available Variables:**
- `project_name`: Sanitized project name
- `project_description`: From concept/PRD/payload
- `project_version`: Default "0.1.0"
- `python_version`: For Python projects
- `node_version`: For Node projects
- `github_url`: After repository creation

## Best Practices

**Project Naming:**
- PascalCase for project names (e.g., "TaskMaster", "ChoreScore")
- Hyphens for CLI tools (e.g., "my-cli-tool")
- Lowercase for libraries (e.g., "my-library")

**Stack Selection:**
- Be explicit in concept: "FastAPI backend" vs just "backend"
- Use payload mode for precise control
- Verify generated files match expectations

**Post-Creation:**
- Always run `mise install` first
- Commit generated boilerplate before making changes
- Create initial feature worktree for development

**33GOD Integration:**
- Use project name as Bloodbank routing key
- Coordinate with Jelmore for multi-agent workflows
- Integrate Flume tasks for project milestones
