#!/usr/bin/env bash
# Auto-detect Hindsight bank ID from the git repo name.
# Worktree-safe: uses --git-common-dir (the shared .git of the canonical
# repo) so every git worktree resolves to the SAME bank — the repo name,
# not the worktree folder name. --show-toplevel would give the worktree dir.
# Usage: hindsight memory recall "$(./scripts/hs-bank-id.sh)" "query"
# Or:    BANK=$(./scripts/hs-bank-id.sh) && hindsight memory recall "$BANK" "query"
set -euo pipefail
{ d=$(git rev-parse --git-common-dir 2>/dev/null) && basename "$(dirname "$(readlink -f "$d")")"; } || echo "general"
