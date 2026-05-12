# MCP Tools Configuration

How to register the n8n-mcp MCP server with Claude Code (or another agentic harness), the environment variables that control which tools are available, and how to verify the install. This is harness-level configuration, not skill-level: the skill assumes the MCP server is already running and the tools are exposed to the agent.

---

## What Gets Configured

The n8n-mcp MCP server provides the tools documented in [api.md](./api.md). The server runs as a separate process and the harness (Claude Code, Cursor, etc.) connects to it over the MCP protocol (stdio or HTTP, depending on harness).

Two pieces of configuration matter:

1. **MCP server registration**: how the harness finds and launches the server.
2. **n8n API credentials**: environment variables (`N8N_API_URL`, `N8N_API_KEY`) that determine whether API-requiring tools are available.

Without API credentials, you get a useful subset (search, get_node, validate_node, validate_workflow, templates, docs). With credentials, the full workflow management surface unlocks.

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `N8N_API_URL` | for API tools | Base URL of your n8n instance, e.g. `https://n8n.example.com` |
| `N8N_API_KEY` | for API tools | Personal API key issued by n8n (Settings then n8n API then Create API Key) |

If both are unset, the server still starts but API-requiring tools error out at call time. Use `n8n_health_check({ mode: "diagnostic" })` to confirm which env vars the server sees.

### Generating an API Key

In your n8n UI:

1. Click your profile then Settings.
2. Open the n8n API section.
3. Create an API key. Copy it.
4. Set `N8N_API_KEY` in the harness environment (not in checked-in config).

Keys grant the same access as the issuing user. Use a service account for agent automation.

### Pointing at the Right Instance

- Local dev: `N8N_API_URL=http://localhost:5678`.
- Self-hosted with reverse proxy: `N8N_API_URL=https://n8n.example.com` (HTTPS strongly recommended).
- n8n Cloud: the instance's hosted URL.

The MCP server appends API paths internally; do not include `/api/v1`.

---

## Tool Availability Matrix

Whether a tool can be called depends on whether the env vars are set:

| Always Available | Requires `N8N_API_URL` + `N8N_API_KEY` |
|---|---|
| `search_nodes`, `get_node`, `get_suggested_nodes` | `n8n_create_workflow`, `create_workflow_from_code` |
| `validate_node`, `validate_workflow` | `n8n_update_partial_workflow`, `n8n_update_full_workflow` |
| `search_templates`, `get_template` | `n8n_validate_workflow` (by ID), `n8n_autofix_workflow` |
| `tools_documentation`, `ai_agents_guide`, `get_sdk_reference` | `n8n_list_workflows`, `n8n_get_workflow`, `n8n_delete_workflow`, `archive_workflow` |
| `n8n_health_check` (basic) | `n8n_test_workflow`, `execute_workflow`, `n8n_executions` |
| | `n8n_deploy_template`, `n8n_workflow_versions` |
| | `n8n_manage_datatable`, `n8n_manage_credentials` |
| | `n8n_audit_instance` |
| | `n8n_generate_workflow` (hosted-only, even with env set) |

`n8n_generate_workflow` is additionally gated on instance type: only n8n Cloud (hosted) instances respond with workflows. Self-hosted gets `{ hosted_only: true, ... }` regardless of env. Fall back to `n8n_deploy_template` or `n8n_create_workflow` on self-hosted.

---

## Harness Registration

The specifics depend on the harness. Below are the common shapes.

### Claude Code (stdio MCP)

Add to `~/.claude/settings.json` or your project's `.claude/settings.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "@n8n/mcp"],
      "env": {
        "N8N_API_URL": "https://n8n.example.com",
        "N8N_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Code to pick up the new server. After restart, the n8n-mcp tools should appear in the available tools list.

For machine-local installs (avoid `npx` cold start), install once globally then reference the absolute path:

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "/usr/local/bin/n8n-mcp",
      "args": [],
      "env": {
        "N8N_API_URL": "https://n8n.example.com",
        "N8N_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Prefer reading the API key from the shell environment rather than committing it to settings:

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "n8n-mcp",
      "env": {
        "N8N_API_URL": "https://n8n.example.com",
        "N8N_API_KEY": "${env:N8N_API_KEY}"
      }
    }
  }
}
```

Then set `N8N_API_KEY` in your shell profile (or `~/.config/zshyzsh/secrets.zsh` in this environment), and Claude Code will inherit it.

### Other Harnesses

The general shape (command, args, env) is the same across MCP-compatible harnesses (Cursor, Cline, etc.). Consult the harness docs for the exact config file location and JSON schema. The two non-negotiables are:

1. The harness must launch the server with `N8N_API_URL` and `N8N_API_KEY` in env.
2. The harness must speak MCP over stdio (the n8n-mcp default).

---

## Secret Handling

Per global conventions for this environment:

1. Before asking the user for a credential, check these locations in order:
   - The project's `.env`.
   - `~/.config/zshyzsh/secrets.zsh` (exported to shell).
   - 1Password DeLoSecrets vault.
2. Never commit `N8N_API_KEY` to a checked-in settings file. Use the `${env:N8N_API_KEY}` shape and source the value from the shell.
3. Treat the API key as having the access of the issuing user. Use a dedicated service account where possible.

The MCP server itself redacts credential request bodies from debug logs and strips the `data` field from `get`/`create`/`update` responses for `n8n_manage_credentials`. The host side (your settings file) is the place secrets are most likely to leak.

---

## Tool Subset Selection

Some harnesses let you restrict which MCP tools are exposed to the agent. This is useful in security-sensitive setups (e.g., disable `n8n_delete_workflow`, `n8n_manage_credentials`, or `n8n_audit_instance` for non-admin agents).

The mechanism is harness-specific. Common shapes:

- An allowlist in the harness's permissions config.
- A wrapper that proxies MCP and filters tools at the protocol layer.
- A custom `mcpServers` entry that points at a subset server.

For Claude Code, see the permissions section of `~/.claude/settings.json`. For other harnesses, consult their docs. The n8n-mcp server itself does not support tool-list filtering via env vars; this is a harness concern.

---

## Verifying the Install

After registering the server and (re)starting the harness, verify:

```javascript
// 1. Basic health
n8n_health_check()
// → { status: "ok" } or an error

// 2. Diagnostic detail (env vars, tool status, API connectivity)
n8n_health_check({ mode: "diagnostic" })
// → { status, env, tools, apiConnectivity }

// 3. Quick search confirms the always-available tools
search_nodes({ query: "slack" })

// 4. If API tools should be available, confirm with a read-only call
n8n_list_workflows({ limit: 1 })
```

If `n8n_health_check` reports the env vars are not present, the server is running but the harness did not pass them through. Inspect the harness's settings file.

If the env vars are present but `apiConnectivity` is failing, check:

- The `N8N_API_URL` is reachable from the machine running the MCP server.
- The `N8N_API_KEY` belongs to the right user and has not been revoked.
- The n8n instance allows API calls from your IP (some n8n configurations restrict this).
- Any reverse proxy (Traefik, Nginx) is routing the API path through.

---

## Multiple n8n Instances

Different agents (or sessions) can talk to different n8n instances by registering multiple MCP server entries with different names and env vars:

```json
{
  "mcpServers": {
    "n8n-mcp-prod": {
      "command": "n8n-mcp",
      "env": {
        "N8N_API_URL": "https://n8n-prod.example.com",
        "N8N_API_KEY": "${env:N8N_PROD_API_KEY}"
      }
    },
    "n8n-mcp-staging": {
      "command": "n8n-mcp",
      "env": {
        "N8N_API_URL": "https://n8n-staging.example.com",
        "N8N_API_KEY": "${env:N8N_STAGING_API_KEY}"
      }
    }
  }
}
```

The harness exposes tools namespaced by server name (e.g., `n8n-mcp-prod__n8n_create_workflow`). Agents must consciously pick the right one.

---

## Upgrading the MCP Server

The server is versioned. New tool capabilities and bug fixes ship over time (notably, `patchNodeField`, `includeUsage`, `n8n_manage_datatable`, and `n8n_generate_workflow` are recent additions).

```bash
# If using npx (Claude Code default), it always pulls the latest on launch
# Force-refresh by clearing the npm cache or restarting the harness

# If installed globally
npm i -g @n8n/mcp@latest
```

After upgrading, restart the harness and re-run `n8n_health_check` to verify the new tool list is present.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Tools not appearing in harness | Server not registered, or harness not restarted | Check `mcpServers` entry, restart harness |
| `n8n_health_check` returns "API not configured" | Env vars not passed through | Set `N8N_API_URL`, `N8N_API_KEY` in harness env |
| `apiConnectivity: false` despite env vars | n8n unreachable from server's machine | Check URL, key, network, reverse proxy |
| `n8n_generate_workflow` returns `hosted_only` | Self-hosted instance | Use `n8n_deploy_template` or `n8n_create_workflow` |
| `n8n_manage_credentials` returns 403 on `get` | Endpoint not in this n8n version | Tool auto-falls-back to list+filter; no action needed |
| Wrong nodeType prefix errors | Mixed up short vs full prefix | See [gotchas.md](./gotchas.md), use `search_nodes` to get both |

---

## See Also

- [README.md](./README.md): Top-level overview and tool category summary.
- [api.md](./api.md): Per-tool reference, including which tools require API credentials.
- [patterns.md](./patterns.md): How tools chain together in real workflows.
- [gotchas.md](./gotchas.md): Common errors when the configuration is right but the calls are wrong.
- [../validation/](../validation/): Validation profiles and recovery for the validation tools enabled here.
