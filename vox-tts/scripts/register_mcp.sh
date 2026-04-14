#!/usr/bin/env bash
# Register vox as an MCP server in the target agent.
#
# Usage: register_mcp.sh <target>
#   target: hermes | openclaw | claude-code
#
# Works around Hermes v0.8.0 CLI bug where `hermes mcp add` drops to chat mode
# when invoked non-interactively — writes to ~/.hermes/config.yaml directly.

set -euo pipefail

TARGET="${1:-}"
VOX_MCP_URL="${VOX_MCP_URL:-https://vox.delo.sh/mcp/}"  # trailing slash required

if [[ -z "$TARGET" ]]; then
    echo "usage: $0 <hermes|openclaw|claude-code>" >&2
    exit 1
fi

case "$TARGET" in
    hermes)
        python3 - <<EOF
import yaml, pathlib
p = pathlib.Path.home() / '.hermes/config.yaml'
cfg = yaml.safe_load(p.read_text()) or {}
cfg.setdefault('mcp_servers', {})['vox'] = {'url': '${VOX_MCP_URL}'}
p.write_text(yaml.safe_dump(cfg, sort_keys=False))
print(f'registered vox in {p}')
EOF
        hermes mcp test vox
        ;;

    openclaw)
        # OpenClaw shares MCP semantics with Hermes. Check its CLI for the
        # exact invocation (may differ by version):
        openclaw mcp add vox --url "$VOX_MCP_URL" || {
            echo "openclaw CLI failed; fall back to editing its config by hand" >&2
            exit 3
        }
        ;;

    claude-code)
        # Claude Code reads MCP servers from ~/.claude/settings.json (mcpServers key).
        python3 - <<EOF
import json, pathlib
p = pathlib.Path.home() / '.claude/settings.json'
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg.setdefault('mcpServers', {})['vox'] = {
    'type': 'http',
    'url': '${VOX_MCP_URL}'
}
p.write_text(json.dumps(cfg, indent=2))
print(f'registered vox in {p}')
print('restart claude code to pick up the change')
EOF
        ;;

    *)
        echo "unknown target: $TARGET (expected hermes|openclaw|claude-code)" >&2
        exit 2
        ;;
esac
