# Running DeLoHome as an MCP server

Use this only when an agent session wants the tools resident. For one-shot actions the CLI
is better: it is generated from the same `DomainRegistry`, so the two surfaces cannot
drift, and it needs no registration.

## Register it

DeLoHome speaks stdio. Add to the relevant `.mcp.json` (project) or via `claude mcp add`:

```json
{
  "mcpServers": {
    "delohome": {
      "command": "delohome",
      "args": ["serve", "stdio"]
    }
  }
}
```

Or, if it is not on `PATH`:

```json
{
  "mcpServers": {
    "delohome": {
      "command": "python",
      "args": ["-m", "delohome", "serve", "stdio"],
      "cwd": "/home/delorenj/code/DeLoHome"
    }
  }
}
```

Credentials resolve from the environment first, then 1Password. In a session where `op` is
authenticated, nothing else is needed.

## The tool surface

A client sees exactly five tools. Domain tools are deliberately *not* loaded into context
until asked for — that is the whole point of the hub.

| Tool | Purpose |
|---|---|
| `list_domains()` | Start here. Returns each domain's name, title, description, tool count and status. A domain whose hardware is unreachable reports `status: "error"` with the reason, rather than taking the hub down. |
| `list_domain_tools(domain)` | Loads that domain's schemas into context. Call it only for a domain you intend to use. |
| `call_domain_tool(domain, tool, arguments)` | Dispatch. `arguments` must match the tool's `input_schema`. |
| `list_rooms()` | Every room, its aliases and what it can do. The disambiguator. |
| `reload_domains()` | Re-initialise every domain after fixing hardware, without restarting. |

Behind them: `media` (8 tools), `lights` (7), `displays` (11).

```
call_domain_tool("lights", "set_lights", {"room": "bedroom", "brightness": 40, "kelvin": 2200})
call_domain_tool("media", "play", {"title": "The Big Lebowski", "room": "dommy"})
```

## Result shape

FastMCP wraps a tool that returns a list as `{"result": [...]}`. Unwrap before iterating —
a tool annotated `-> Any` gets no structured schema at all and comes back as a JSON
**string**, which a caller will then iterate character by character. That shipped once:
`list_display_apps` reported 3140 installed apps, the character count of the JSON, when
there were 67. Every tool now carries a concrete return annotation and a test enforces it.

## HTTP mode

For the container. Host-networked, port 8091, no Traefik route — it is LAN-only.

```bash
delohome serve http            # DELOHOME_HOST / DELOHOME_PORT
mise run up                    # hub + zwave-js sidecar, creds via `op run`
```

Note `serve` must `await hub.run_async(...)`. `hub.run()` calls `asyncio.run()` internally
and the CLI is already inside a loop, so it dies with "Already running asyncio in this
thread" and the server never starts at all.

The Docker image installs `.[media,lights]` only — the `displays` extra is missing, so in
the container that domain will fail on import and report as unavailable.
