#!/usr/bin/env bash
# Register vox as an MCP server in the target agent.
#
# Usage: register_mcp.sh <target>
#   target: openclaw | claude-code
#   (hermes is refused: the fleet uses the native tts/vox plugin instead.)

set -euo pipefail

TARGET="${1:-}"
VOX_MCP_URL="${VOX_MCP_URL:-https://vox.delo.sh/mcp/}"  # trailing slash required

if [[ -z "$TARGET" ]]; then
    echo "usage: $0 <openclaw|claude-code>" >&2
    exit 1
fi

case "$TARGET" in
    hermes)
        # The Hermes fleet speaks through the native tts/vox plugin
        # (tts.provider: vox), not the MCP, and ~/.hermes/config.yaml is the
        # hand-maintained fleet base: a yaml dump would strip its comments.
        echo "refusing: the Hermes fleet uses tts.provider: vox, not the vox MCP (removed 2026-10-01)" >&2
        exit 4
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
        echo "unknown target: $TARGET (expected openclaw|claude-code)" >&2
        exit 2
        ;;
esac
