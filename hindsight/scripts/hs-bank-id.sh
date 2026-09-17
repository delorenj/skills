#!/usr/bin/env bash
# Resolve the task bank through the canonical machine hook implementation.
# Run from the task working directory, including linked worktrees.
set -euo pipefail
resolver="${HOME}/.agents/hooks/lib/hindsight-bank.sh"
if [[ ! -r "$resolver" ]]; then
  printf 'Hindsight bank resolver is unavailable: %s\n' "$resolver" >&2
  exit 1
fi
source "$resolver"
resolve_bank
