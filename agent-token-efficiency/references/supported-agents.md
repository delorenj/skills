---
pipeline-status: new
---
# Supported Agent Paths

## Claude Code

- Executable: `claude`
- Agents: `~/.claude/agents/*.md`
- Instructions: `~/.claude/CLAUDE.md`
- Skills: `~/.claude/skills/<skill>`
- MCP: prefer `claude mcp add ...` command; this CLI writes reviewable notes rather than blindly running it.

## Codex

- Executable: `codex`
- Config: `~/.codex/config.toml`
- Instructions: `~/.codex/AGENTS.md` plus repo `AGENTS.md`
- Agents: `~/.codex/agents/*.toml`
- Skills: `~/.codex/skills/<skill>`
- MCP: `[mcp_servers.<name>]` sections in `config.toml`

## Kimi Code CLI

- Executable: `kimi`
- Config: `~/.kimi/config.toml`
- MCP: `~/.kimi/mcp.json`
- Agents: `~/.kimi/agents/*.yaml` with prompt files
- Skills: `~/.kimi/skills/<skill>`

## Hermes Agent

- Executable: `hermes`
- Config: `~/.hermes/config.yaml`
- Secrets: `~/.hermes/.env`
- Skills: `~/.hermes/skills/<skill>`
- Provider selection: `hermes model` or config files
- Doctor: `hermes doctor`
