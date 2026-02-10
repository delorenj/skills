#!/bin/bash
#
# Workspace Detector Library
#
# Automatically detects which Plane workspace to use based on:
# 1. Local .plane.json config (highest priority)
# 2. Git remote URL patterns
# 3. Current directory path
# 4. Environment variable
# 5. Default workspace (fallback)
#

set -euo pipefail

WORKSPACE_CONFIG_FILE="${HOME}/.claude/plane-workspaces.json"

# Function: Get current workspace
# Returns workspace name based on detection priority
get_current_workspace() {
  if [ ! -f "$WORKSPACE_CONFIG_FILE" ]; then
    echo "default"
    return
  fi

  # 1. Check for project-local .plane.json (highest priority)
  if [ -f ".plane.json" ]; then
    local ws=$(jq -r '.workspace // empty' .plane.json 2>/dev/null)
    if [ -n "$ws" ]; then
      echo "$ws"
      return
    fi
  fi

  # 2. Detect from git remote URL
  if git rev-parse --git-dir >/dev/null 2>&1; then
    local git_remote=$(git remote get-url origin 2>/dev/null || echo "")
    if [ -n "$git_remote" ]; then
      local ws=$(jq -r \
        --arg remote "$git_remote" \
        '.detection.git_remote_patterns | to_entries[] | select($remote | contains(.key)) | .value' \
        "$WORKSPACE_CONFIG_FILE" 2>/dev/null | head -1)
      if [ -n "$ws" ] && [ "$ws" != "null" ]; then
        echo "$ws"
        return
      fi
    fi
  fi

  # 3. Detect from current directory path
  local cwd=$(pwd)
  local ws=$(jq -r \
    --arg cwd "$cwd" \
    '.detection.directory_patterns | to_entries[] | select(.key as $pattern | $cwd | startswith($pattern)) | .value' \
    "$WORKSPACE_CONFIG_FILE" 2>/dev/null | head -1)
  if [ -n "$ws" ] && [ "$ws" != "null" ]; then
    echo "$ws"
    return
  fi

  # 4. Check environment variable
  if [ -n "${PLANE_WORKSPACE:-}" ]; then
    echo "$PLANE_WORKSPACE"
    return
  fi

  # 5. Fallback to default workspace
  local default_ws=$(jq -r '.default_workspace // "default"' "$WORKSPACE_CONFIG_FILE" 2>/dev/null)
  echo "$default_ws"
}

# Function: Get workspace configuration
# Args: workspace_name
# Returns: JSON object with workspace config
get_workspace_config() {
  local workspace="${1:-}"

  if [ -z "$workspace" ]; then
    workspace=$(get_current_workspace)
  fi

  if [ ! -f "$WORKSPACE_CONFIG_FILE" ]; then
    echo "{}"
    return 1
  fi

  jq -r --arg ws "$workspace" '.workspaces[$ws] // {}' "$WORKSPACE_CONFIG_FILE"
}

# Function: Get workspace API key
# Args: workspace_name (optional)
# Returns: API key value from environment
get_workspace_api_key() {
  local workspace="${1:-}"

  if [ -z "$workspace" ]; then
    workspace=$(get_current_workspace)
  fi

  local config=$(get_workspace_config "$workspace")
  local api_key_env=$(echo "$config" | jq -r '.api_key_env // "PLANE_API_KEY"')

  # Get value from environment (zsh-compatible indirect expansion)
  eval echo "\${$api_key_env:-}"
}

# Function: Get workspace base URL
# Args: workspace_name (optional)
# Returns: Base URL for Plane API
get_workspace_base_url() {
  local workspace="${1:-}"

  if [ -z "$workspace" ]; then
    workspace=$(get_current_workspace)
  fi

  local config=$(get_workspace_config "$workspace")
  echo "$config" | jq -r '.base_url // "plane.so"'
}

# Function: Get git repository name (not directory name)
# Returns: Repository name from git remote URL
get_git_repo_name() {
  if ! git rev-parse --git-dir >/dev/null 2>&1; then
    return 1
  fi

  local git_remote=$(git remote get-url origin 2>/dev/null || echo "")
  if [ -z "$git_remote" ]; then
    return 1
  fi

  # Extract repo name from URL (works for github.com/user/repo.git or git@github.com:user/repo.git)
  local repo_name=$(echo "$git_remote" | sed -E 's#.*/([^/]+)(\.git)?$#\1#' | sed 's/\.git$//')
  echo "$repo_name"
}

# Function: Get workspace project ID (with dynamic resolution)
# Args: workspace_name (optional), project_name (default: "default")
# Returns: Project UUID
get_workspace_project_id() {
  local workspace="${1:-}"
  local project="${2:-default}"

  if [ -z "$workspace" ]; then
    workspace=$(get_current_workspace)
  fi

  # Check local .plane.json first
  if [ -f ".plane.json" ]; then
    local local_project=$(jq -r '.project_id // empty' .plane.json 2>/dev/null)
    if [ -n "$local_project" ]; then
      echo "$local_project"
      return
    fi
  fi

  local config=$(get_workspace_config "$workspace")
  local is_dynamic=$(echo "$config" | jq -r '.projects.dynamic // false')

  # If dynamic project resolution is enabled and project is "default"
  if [ "$is_dynamic" = "true" ] && [ "$project" = "default" ]; then
    local repo_name=$(get_git_repo_name)

    if [ -n "$repo_name" ]; then
      # Check if repo name is in static config first
      local project_id=$(echo "$config" | jq -r --arg repo "$repo_name" '.projects[$repo] // empty')

      if [ -n "$project_id" ] && [ "$project_id" != "null" ] && [ "$project_id" != "true" ]; then
        echo "$project_id"
        return
      fi

      # If not in config, query API to find project by name
      local api_key=$(get_workspace_api_key "$workspace")
      local base_url=$(get_workspace_base_url "$workspace")

      if [ -n "$api_key" ] && [ -n "$base_url" ]; then
        project_id=$(curl -s -X GET \
          "https://${base_url}/api/v1/workspaces/${workspace}/projects/" \
          -H "X-Api-Key: ${api_key}" \
          -H "Content-Type: application/json" 2>/dev/null | \
          jq -r --arg name "$repo_name" '.results[] | select(.name == $name or (.identifier | ascii_downcase) == ($name | ascii_downcase)) | .id' | head -1)

        if [ -n "$project_id" ] && [ "$project_id" != "null" ]; then
          echo "$project_id"
          return
        fi
      fi
    fi
  fi

  # Static project resolution or fallback
  echo "$config" | jq -r --arg proj "$project" '.projects[$proj] // .projects.default // ""'
}

# Function: Get workspace WIP limits
# Args: workspace_name (optional)
# Returns: JSON with individual and team WIP limits
get_workspace_wip_limits() {
  local workspace="${1:-}"

  if [ -z "$workspace" ]; then
    workspace=$(get_current_workspace)
  fi

  local config=$(get_workspace_config "$workspace")
  local limits=$(echo "$config" | jq -r '.wip_limits // {"individual": 3, "team": 7}')
  echo "$limits"
}

# Function: Validate workspace exists
# Args: workspace_name
# Returns: 0 if exists, 1 if not
validate_workspace() {
  local workspace="$1"

  if [ ! -f "$WORKSPACE_CONFIG_FILE" ]; then
    return 1
  fi

  local exists=$(jq -r --arg ws "$workspace" '.workspaces | has($ws)' "$WORKSPACE_CONFIG_FILE")

  if [ "$exists" = "true" ]; then
    return 0
  else
    return 1
  fi
}

# Function: List available workspaces
# Returns: JSON array of workspace names
list_workspaces() {
  if [ ! -f "$WORKSPACE_CONFIG_FILE" ]; then
    echo "[]"
    return
  fi

  jq -r '.workspaces | keys' "$WORKSPACE_CONFIG_FILE"
}

# Function: Debug workspace detection
# Prints detection process for troubleshooting
debug_workspace_detection() {
  echo "Workspace Detection Debug"
  echo "========================="
  echo ""

  echo "Config file: $WORKSPACE_CONFIG_FILE"
  if [ -f "$WORKSPACE_CONFIG_FILE" ]; then
    echo "✓ Config file exists"
  else
    echo "✗ Config file not found"
    return 1
  fi
  echo ""

  echo "Detection Priority:"
  jq -r '.detection.priority[]' "$WORKSPACE_CONFIG_FILE" | sed 's/^/  - /'
  echo ""

  echo "1. Local .plane.json:"
  if [ -f ".plane.json" ]; then
    echo "  ✓ Found: $(jq -r '.workspace // "no workspace field"' .plane.json)"
  else
    echo "  ✗ Not found"
  fi
  echo ""

  echo "2. Git remote:"
  if git rev-parse --git-dir >/dev/null 2>&1; then
    local remote=$(git remote get-url origin 2>/dev/null || echo "no remote")
    echo "  Remote: $remote"
    local ws=$(jq -r --arg remote "$remote" \
      '.detection.git_remote_patterns | to_entries[] | select($remote | contains(.key)) | .value' \
      "$WORKSPACE_CONFIG_FILE" 2>/dev/null | head -1)
    if [ -n "$ws" ] && [ "$ws" != "null" ]; then
      echo "  ✓ Matched: $ws"
    else
      echo "  ✗ No match"
    fi
  else
    echo "  ✗ Not a git repository"
  fi
  echo ""

  echo "3. Directory path:"
  echo "  Current: $(pwd)"
  local ws=$(jq -r --arg cwd "$(pwd)" \
    '.detection.directory_patterns | to_entries[] | select($cwd | startswith(.key)) | .value' \
    "$WORKSPACE_CONFIG_FILE" 2>/dev/null | head -1)
  if [ -n "$ws" ] && [ "$ws" != "null" ]; then
    echo "  ✓ Matched: $ws"
  else
    echo "  ✗ No match"
  fi
  echo ""

  echo "4. Environment variable:"
  if [ -n "${PLANE_WORKSPACE:-}" ]; then
    echo "  ✓ PLANE_WORKSPACE=$PLANE_WORKSPACE"
  else
    echo "  ✗ Not set"
  fi
  echo ""

  echo "5. Default workspace:"
  local default=$(jq -r '.default_workspace // "default"' "$WORKSPACE_CONFIG_FILE")
  echo "  Default: $default"
  echo ""

  echo "========================="
  echo "Detected workspace: $(get_current_workspace)"
  echo "========================="
}

# Functions are available when script is sourced
# (export -f not supported in zsh, only bash)
