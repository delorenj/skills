# Agent Token Efficiency Workflows

## Workflow 1: Unsupported agent optimizer

Command:

```bash
aeff optimize-unknown /path/to/agent-or-repo --docs-url URL --out ./reports
```

Purpose:

1. Inspect CLI help/version/config/docs.
2. Detect support for MCP/tools, skills, custom agents, profiles, compaction, approval/sandboxing, and usage metrics.
3. Map known strategies from Claude, Codex, Kimi, and Hermes to the unknown agent.
4. Produce a markdown report.
5. With `--apply`, add generic repo files: `AGENTS.md`, `.agent-efficiency/strategy.md`, and reusable scout/log/docs prompts.

Safe default: report-only. Unknown agent mutation is intentionally conservative.

## Workflow 2: Propagate updates across supported agents

Command examples:

```bash
aeff propagate-update --kind mcp --name context7 --source assets/mcp/context7.json --target all

aeff propagate-update --kind skill --name agent-token-efficiency --source . --target codex,claude

aeff propagate-update --kind instruction --name "Token Rules" --source assets/templates/AGENTS.md --target all
```

Rules:

- Dry-run by default.
- Codex skill target: `~/.codex/skills/<name>`.
- Claude skill target: `~/.claude/skills/<name>`.
- Kimi skill target: `~/.kimi/skills/<name>`.
- Hermes skill target: `~/.hermes/skills/<name>`.
- Codex MCP config: `~/.codex/config.toml`.
- Kimi MCP config: `~/.kimi/mcp.json`.
- Claude/Hermes MCP updates are emitted as reviewable install notes unless explicitly implemented by the team.

## Workflow 3: Usage analysis and provider rotation

Command:

```bash
aeff analyze-usage --providers assets/configs/providers.yml --desired-rpm 4 --desired-daily-requests 500
```

Outputs:

- usage report from `ccusage`, when available
- provider assumptions
- daily/RPM capacity calculation
- rotation allocation
- warnings about unknown quotas and free-tier instability

Important: this workflow must not recommend evading provider limits. It may recommend fallback/overflow providers, paid burst capacity, lower fan-out, longer inter-request delay, or moving cheap tasks to local models.
