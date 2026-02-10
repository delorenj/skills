#!/usr/bin/env bash
# Install Node CLI tool using bun
# Usage: ./install-node-cli.sh <package-name>

set -euo pipefail

PACKAGE="${1:-}"

if [[ -z "$PACKAGE" ]]; then
    echo "Usage: $0 <package-name>"
    echo "Example: $0 typescript"
    exit 1
fi

echo "Installing Node CLI tool: $PACKAGE"

# Ensure mise-managed bun is available
if ! command -v bun &> /dev/null; then
    echo "Error: bun not found. Installing with mise..."
    mise use bun@latest -g
fi

# Install the tool globally
echo "Running: bun install -g $PACKAGE"
bun install -g "$PACKAGE"

# Verify installation
TOOL_NAME="${PACKAGE##*/}"  # Extract tool name from package path
if command -v "$TOOL_NAME" &> /dev/null; then
    echo "✅ Successfully installed $TOOL_NAME"
    echo "Version: $("$TOOL_NAME" --version 2>/dev/null || echo 'N/A')"
    echo "Location: $(which "$TOOL_NAME")"
else
    echo "⚠️  Tool installed but not found in PATH"
    echo "Check bun global bin directory is in your PATH"
fi
