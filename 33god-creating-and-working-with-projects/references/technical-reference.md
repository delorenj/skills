# Technical Reference

This skill focuses on workflow patterns and when to use iMi. For detailed technical documentation, see:

## Reference Materials from Deprecated Skill

The `33god-imi-worktree-management` skill (now deprecated) contains detailed technical references:

- **MCP Tools Reference**: `/home/delorenj/.claude/skills/33god-imi-worktree-management/references/mcp-tools-reference.md`
  - Complete MCP tool schemas
  - Parameter specifications
  - Usage examples for Claude Desktop integration

- **Worktree Conventions**: `/home/delorenj/.claude/skills/33god-imi-worktree-management/references/worktree-conventions.md`
  - Deep dive on directory structure
  - Naming convention rationale
  - Advanced workflow patterns

- **Project Creation**: `/home/delorenj/.claude/skills/33god-imi-worktree-management/references/project-creation.md`
  - Stack detection logic
  - Boilerplate template system
  - GitHub integration details

## Source Code Documentation

- **Architecture**: `/home/delorenj/code/iMi/trunk-main/docs/architecture-imi-project-registry.md`
  - Complete architectural decisions
  - Schema design rationale
  - Integration patterns

- **PostgreSQL Schema**: `/home/delorenj/code/iMi/trunk-main/migrations/001_create_schema.sql`
  - Complete table definitions
  - Constraints and indexes
  - Triggers and views

- **Helper Functions**: `/home/delorenj/code/iMi/trunk-main/migrations/002_functions_and_helpers.sql`
  - 20+ PostgreSQL functions
  - Usage examples in comments
  - Performance considerations

## Database Connection

```bash
# Interactive psql session
/home/delorenj/code/iMi/trunk-main/scripts/psql-imi.sh

# Query example
/home/delorenj/code/iMi/trunk-main/scripts/psql-imi.sh -c "SELECT * FROM v_inflight_work"
```

**Connection Details**:
- Host: 192.168.1.12:5432
- Database: imi
- User: imi
- Connection string: `postgresql://imi:imi_dev_password_2026@192.168.1.12:5432/imi`

## Quick Reference

### Worktree Types (Built-in)
- `feat` - Feature development
- `fix` - Bug fixes
- `aiops` - AI operations (agents, MCP, workflows)
- `devops` - DevOps tasks (CI, deploys, repo org)
- `review` - PR reviews
- `trunk` - Main branch (never commit directly)

### Directory Structure
```
/home/delorenj/code/ProjectName/
├── .iMi/                    # Cluster hub (shared by all worktrees)
│   ├── project.json         # Project UUID and metadata
│   ├── presence/            # Agent lock files
│   └── links/               # Shared environment files
├── trunk-main/              # Main branch worktree
├── feat-<name>/             # Feature worktrees
├── fix-<name>/              # Fix worktrees
├── aiops-<name>/            # AI ops worktrees
└── devops-<name>/           # DevOps worktrees
```

### Naming Conventions
- Worktree directory: `<type-prefix><name>` (e.g., `feat-user-auth`)
- Git branch: `<type-prefix>/<name>` (e.g., `feat/user-auth`)
- Trunk worktree: `trunk-<default-branch>` (e.g., `trunk-main`)

### JSON Output
All commands support `--json` flag:
```bash
imi list --json | jq '.data[] | select(.agent_id != null)'
imi show feat-user-auth --json | jq '.data.metadata.plane_ticket_id'
```
