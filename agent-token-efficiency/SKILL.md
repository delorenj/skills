---
name: agent-token-efficiency
version: 0.1.0
description: Optimize multi-agent coding CLI stacks for lower token burn across Claude Code, Codex, Kimi Code CLI, and Hermes; includes workflows for unknown agents, cross-agent updates, MCP/profile propagation, and usage/provider rotation analysis.
---

# Agent Token Efficiency Skill

Use this skill when the user wants to save tokens, reduce context bloat, configure coding agents, propagate skills/tools/profiles/MCP servers, analyze usage, or design provider/model rotation for continuous agentic coding.

This skill codifies a layered strategy:

1. Premium models make architecture and final tradeoff decisions.
2. Cheap subagents gather evidence, summarize logs, research docs, and map impact.
3. MCP servers are enabled sparingly because every exposed tool adds context overhead.
4. Skills and profiles are preferred over giant global instructions.
5. Usage metrics drive the next optimization pass.
6. Provider rotation uses measured quotas, not vibes wearing a lab coat.

## Included CLI

Run the bundled Typer CLI:

```bash
python scripts/agent_efficiency.py --help
```

Recommended install from this skill directory:

```bash
python -m pip install -e .
aeff --help
```

## Core workflows

### 1. Optimize an unsupported agent

Given the path to an unknown agent CLI or repository, inspect its capabilities, discover docs hints, map supported strategies from Claude/Codex/Kimi/Hermes, and produce/apply a token-efficiency optimization plan.

```bash
aeff optimize-unknown /path/to/agent-or-executable --docs-url https://example.com/docs --out ./reports
```

Use `--apply` only after reviewing the report:

```bash
aeff optimize-unknown /path/to/agent-or-executable --apply
```

The workflow looks for:

- config files
- model/provider settings
- MCP or tool registration
- custom agents/subagents
- skills/prompts/profiles
- compaction/summarization settings
- approval/sandbox controls
- usage accounting hooks

It then applies equivalent strategies where safe:

- add scout/research/log-compression workers
- add profiles for deep/cheap modes
- reduce always-loaded instructions
- add docs/code-search MCP only when useful
- add usage-reporting hooks
- disable unsafe auto-approval by default

### 2. Propagate a new tool, skill, profile, MCP server, or general update

Apply one update across the supported CLI fleet.

```bash
aeff propagate-update --kind mcp --name context7 --source assets/mcp/context7.json --target all
```

Supported `--kind` values:

- `mcp`
- `skill`
- `profile`
- `agent`
- `instruction`
- `config`

Dry-run is default. Add `--apply` to mutate files or run agent CLI commands.

### 3. Analyze token usage and propose improvements

Read local usage metrics, inspect configured agents/providers, compare provider free/throttled capacity, and calculate a rotation plan.

```bash
aeff analyze-usage --providers assets/configs/providers.yml --desired-rpm 4 --desired-daily-requests 500
```

With web refresh of provider notes:

```bash
aeff analyze-usage --allow-web --providers assets/configs/providers.yml
```

This workflow should produce:

- detected usage hotspots
- agents/models likely overused
- MCP/tool bloat warnings
- suggested model/profile changes
- free/throttled provider rotation plan
- explicit quota assumptions

## Safety rules

- Default to dry-run.
- Do not commit secrets.
- Do not enable YOLO/auto-approval globally.
- Do not install large MCP suites by default.
- Prefer official docs for provider/rate-limit facts.
- If a rate limit cannot be verified, mark it unknown and require manual input.
- Never recommend violating provider ToS by creating throwaway accounts or evading limits.

## Files

- `scripts/agent_efficiency.py` — Typer CLI implementation.
- `assets/configs/providers.yml` — provider quota and rotation assumptions.
- `assets/mcp/*.json` — bundled MCP server definitions.
- `assets/agents/*` — reusable scout/reviewer/research agents.
- `assets/templates/*` — AGENTS.md, CLAUDE.md, and reports.
- `references/*.md` — implementation playbooks.

## Invocation guidance for agents

When this skill is active:

1. Use `aef doctor` or `python scripts/agent_efficiency.py doctor` before modifying a machine.
2. Use dry-run reports first.
3. Apply changes only after confirming file paths and generated diffs.
4. After changes, run smoke checks.
5. Store reports under `~/.agent-token-efficiency/reports` or the requested output directory.
