#!/usr/bin/env bash
# Auto-detect Hindsight bank ID from git repo name.
# Usage: hindsight memory recall "$(./scripts/hs-bank-id.sh)" "query"
# Or:    BANK=$(./scripts/hs-bank-id.sh) && hindsight memory recall "$BANK" "query"
set -euo pipefail
basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "general"
