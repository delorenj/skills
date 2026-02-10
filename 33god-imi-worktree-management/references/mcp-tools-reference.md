# iMi MCP Tools Reference

Complete reference for the 10 MCP tools exposed by the iMi FastMCP server.

## Tool Categories

### Creation Tools

#### `create_worktree`
Create a new worktree of specified type.

**Parameters:**
- `name` (required): Descriptive name for worktree (e.g., "user-authentication")
- `worktree_type` (optional): Type of worktree (default: "feat")
  - Built-in: feat, fix, aiops, devops, review
  - Custom: Any user-defined type from `imi types list`
- `repo` (optional): Repository name (uses current repo if not specified)

**Returns:**
```json
{
  "success": true,
  "message": "Worktree 'user-auth' created successfully",
  "data": {
    "worktree_path": "/home/delorenj/code/myproject/feat-user-auth",
    "worktree_name": "feat-user-auth",
    "worktree_type": "feat"
  }
}
```

**Example Usage:**
```
User: "Create a feature worktree for user authentication"
Claude: [Uses create_worktree(name="user-authentication", worktree_type="feat")]

User: "Create an experimental worktree for neural network prototype"
Claude: [Uses create_worktree(name="neural-net", worktree_type="experiment")]
```

#### `create_review_worktree`
Create a worktree for reviewing a pull request.

**Parameters:**
- `pr_number` (required): Pull request number (integer > 0)
- `repo` (optional): Repository name (uses current repo if not specified)

**Returns:**
```json
{
  "success": true,
  "message": "Review worktree for PR #456 created successfully",
  "data": {
    "worktree_path": "/home/delorenj/code/myproject/pr-review-456",
    "pr_number": 456
  }
}
```

**Requirements:**
- GitHub CLI (`gh`) must be installed and authenticated
- PR must exist in the repository

**Example Usage:**
```
User: "Review PR #123"
Claude: [Uses create_review_worktree(pr_number=123)]
```

#### `create_project`
Bootstrap a new project with GitHub integration and boilerplate.

**Parameters:**
- `concept` (optional): Project concept description (natural language)
- `prd` (optional): Path to PRD markdown file
- `name` (optional): Explicit project name (inferred from concept/prd if not provided)
- `payload` (optional): JSON string for structured project definition

**Returns:**
```json
{
  "success": true,
  "message": "Project created successfully",
  "data": {
    "project_name": "TaskMaster",
    "project_path": "/home/delorenj/code/TaskMaster",
    "github_url": "https://github.com/delorenj/TaskMaster",
    "stack": "PythonFastAPI"
  }
}
```

**Example Usage:**
```
User: "Create a FastAPI project for task management called TaskMaster"
Claude: [Uses create_project(
  concept="FastAPI backend for task management with PostgreSQL",
  name="TaskMaster"
)]

User: "Bootstrap a React dashboard project"
Claude: [Uses create_project(
  concept="React dashboard with TypeScript and shadcn/ui",
  name="Dashboard"
)]
```

### Navigation Tools

#### `list_worktrees`
List all active worktrees and repositories.

**Parameters:**
- `repo` (optional): Repository name (shows all repos if not specified)
- `worktrees_only` (optional): List only worktrees (exclude projects)
- `projects_only` (optional): List only projects/repositories (exclude worktrees)

**Returns:**
```json
{
  "success": true,
  "message": "Worktrees listed successfully",
  "data": {
    "worktrees": [
      {
        "name": "feat-user-auth",
        "path": "/home/delorenj/code/myproject/feat-user-auth",
        "branch": "feat/user-auth",
        "type": "feat"
      }
    ]
  }
}
```

**Example Usage:**
```
User: "Show me all my worktrees"
Claude: [Uses list_worktrees()]

User: "List only feature worktrees in myproject"
Claude: [Uses list_worktrees(repo="myproject", worktrees_only=true)]
```

#### `navigate_worktree`
Find worktree path using fuzzy search.

**Parameters:**
- `query` (optional): Fuzzy search query (worktree name, branch name, or repo name)
- `repo` (optional): Exact repository name (skip fuzzy search within this repo)

**Returns:**
```json
{
  "success": true,
  "message": "Worktree located successfully",
  "data": {
    "target_path": "/home/delorenj/code/myproject/feat-user-auth"
  }
}
```

**Example Usage:**
```
User: "Navigate to the user authentication worktree"
Claude: [Uses navigate_worktree(query="user-auth")]
→ Returns path for use in subsequent file operations
```

#### `show_status`
Show status of all worktrees.

**Parameters:**
- `repo` (optional): Repository name (shows all repos if not specified)

**Returns:**
```json
{
  "success": true,
  "message": "Status retrieved successfully",
  "data": {
    "worktrees": [
      {
        "name": "feat-user-auth",
        "uncommitted_changes": 3,
        "branch_status": "ahead 2, behind 0"
      }
    ]
  }
}
```

**Example Usage:**
```
User: "Show me the status of all worktrees"
Claude: [Uses show_status()]
```

### Cleanup Tools

#### `remove_worktree`
Remove a worktree and optionally its branches.

**Parameters:**
- `name` (required): Name of worktree to remove
- `repo` (optional): Repository name (uses current repo if not specified)
- `keep_branch` (optional): Keep local branch after removing worktree (default: false)
- `keep_remote` (optional): Keep remote branch (requires keep_branch=true, default: false)

**Returns:**
```json
{
  "success": true,
  "message": "Worktree 'feat-user-auth' removed successfully",
  "data": {
    "removed_worktree": "feat-user-auth",
    "removed_branch": "feat/user-auth",
    "removed_remote": true
  }
}
```

**Example Usage:**
```
User: "Remove the user-auth worktree but keep the branch"
Claude: [Uses remove_worktree(name="user-auth", keep_branch=true)]
```

#### `sync_worktrees`
Sync database with actual Git worktree state.

**Parameters:**
- `repo` (optional): Repository name (syncs all repos if not specified)

**Returns:**
```json
{
  "success": true,
  "message": "Worktrees synced successfully",
  "data": {
    "added": 2,
    "removed": 1,
    "updated": 3
  }
}
```

**Example Usage:**
```
User: "Sync the database with git state"
Claude: [Uses sync_worktrees()]
```

#### `prune_worktrees`
Clean up stale worktree references from Git.

**Parameters:**
- `repo` (optional): Repository name (uses current repo if not specified)
- `dry_run` (optional): Show what would be removed without actually removing (default: false)

**Returns:**
```json
{
  "success": true,
  "message": "Prune completed successfully",
  "data": {
    "pruned": ["old-worktree-1", "old-worktree-2"]
  }
}
```

**Example Usage:**
```
User: "Clean up stale worktree references"
Claude: [Uses prune_worktrees()]

User: "Show what would be pruned without actually removing"
Claude: [Uses prune_worktrees(dry_run=true)]
```

### Discovery Tools

#### `list_types`
List all available worktree types.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "message": "Worktree types listed successfully",
  "data": {
    "count": 6,
    "types": [
      {
        "name": "feat",
        "branch_prefix": "feat/",
        "worktree_prefix": "feat-",
        "description": "Feature development",
        "is_builtin": true
      },
      {
        "name": "experiment",
        "branch_prefix": "experiment/",
        "worktree_prefix": "experiment-",
        "description": "Experimental features",
        "is_builtin": false
      }
    ]
  }
}
```

**Example Usage:**
```
User: "What worktree types are available?"
Claude: [Uses list_types()]

User: "Can I create a prototype worktree?"
Claude: [Uses list_types() to check if 'prototype' type exists]
```

## Error Responses

All tools return standardized error responses:

```json
{
  "success": false,
  "message": "Failed to create worktree 'user-auth'",
  "error": "Worktree directory already exists"
}
```

**Common Errors:**
- "GitHub token missing" - Set GITHUB_TOKEN env var
- "Type not found" - Use list_types to see available types
- "Worktree already exists" - Use list_worktrees to find existing
- "Binary not found" - iMi CLI not in PATH
- "Command timeout" - Operation exceeded 30s timeout

## Integration Patterns

### Sequential Workflow
```
1. list_types() - Discover available types
2. create_worktree(name="...", worktree_type="...") - Create worktree
3. navigate_worktree(query="...") - Get path
4. [User develops in worktree]
5. remove_worktree(name="...") - Clean up
```

### Project Bootstrapping
```
1. create_project(concept="...", name="...") - Bootstrap project
2. [Project created with GitHub repo + boilerplate]
3. navigate_worktree(query=project_name) - Navigate to trunk
4. create_worktree(name="initial-setup", worktree_type="feat") - Start work
```

### PR Review Workflow
```
1. list_worktrees() - See existing worktrees
2. create_review_worktree(pr_number=123) - Create review worktree
3. navigate_worktree(query="pr-review-123") - Get path
4. [User reviews code]
5. remove_worktree(name="pr-review-123") - Clean up
```
