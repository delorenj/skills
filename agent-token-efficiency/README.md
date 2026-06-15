# Agent Token Efficiency Skill

A Codex/Claude-compatible skill plus Typer CLI for optimizing a four-agent coding stack:

- Claude Code
- OpenAI Codex
- Kimi Code CLI
- Nous Hermes Agent

## Install locally

```bash
cd agent-token-efficiency-skill
python -m pip install -e .
aeff doctor --verbose
```

## Dry-run install bundle

```bash
aeff install-bundle
```

## Apply bundle

```bash
aeff install-bundle --apply
```

## Workflows

```bash
# 1. Research and optimize an unsupported agent
aeff optimize-unknown /path/to/agent-or-repo --docs-url https://example.com/docs

# 2. Propagate an update to supported agents
aeff propagate-update --kind mcp --name context7 --source assets/mcp/context7.json --target all

# 3. Analyze usage and calculate provider rotation
aeff analyze-usage --desired-rpm 4 --desired-daily-requests 500
```

Default mode is dry-run for mutating operations.
