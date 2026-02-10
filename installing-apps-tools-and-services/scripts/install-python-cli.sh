#!/usr/bin/env bash
# Install Python CLI tool using uv
# Usage: ./install-python-cli.sh <package-name>

set -euo pipefail

PACKAGE="${1:-}"

if [[ -z "$PACKAGE" ]]; then
    echo "Usage: $0 <package-name>"
    echo "Example: $0 ruff"
    exit 1
fi

echo "Installing Python CLI tool: $PACKAGE"

# Ensure mise-managed uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv not found. Installing with mise..."
    mise use uv@latest -g
fi

# Install the tool globally
echo "Running: uv tool install $PACKAGE"
uv tool install "$PACKAGE"

# Verify installation
TOOL_NAME="${PACKAGE##*/}"  # Extract tool name from package path
if command -v "$TOOL_NAME" &> /dev/null; then
    echo "✅ Successfully installed $TOOL_NAME"
    echo "Version: $("$TOOL_NAME" --version 2>/dev/null || echo 'N/A')"
    echo "Location: $(which "$TOOL_NAME")"
else
    echo "⚠️  Tool installed but not found in PATH"
    echo "Check ~/.local/bin is in your PATH"
fi
