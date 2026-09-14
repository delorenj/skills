#!/bin/bash

# Recall memories from the CoachingAgentFramework Hindsight bank.
#
# Usage:
#   recall.sh "<query>"
#   recall.sh "<query>" --json

set -euo pipefail

BANK="CoachingAgentFramework"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"<query>\" [extra hindsight args]" >&2
  exit 1
fi

query="$1"
shift

exec hindsight memory recall "$BANK" "$query" "$@"
