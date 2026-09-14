#!/bin/bash

# Retain a memory into the CoachingAgentFramework Hindsight bank.
#
# Usage:
#   retain.sh "<fact>"
#   retain.sh "<fact>" <context>
#   retain.sh "<fact>" <context> --doc-id <id>
#   retain.sh "<fact>" --doc-id <id>
#
# Context categories: architecture, conventions, debugging, deployment,
# dependencies, preferences, session-summary, code-edit

set -euo pipefail

BANK="CoachingAgentFramework"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"<fact to retain>\" [context] [extra hindsight args]" >&2
  exit 1
fi

fact="$1"
shift

context="conventions"
if [ $# -ge 1 ] && [[ "$1" != --* ]]; then
  context="$1"
  shift
fi

exec hindsight memory retain "$BANK" "$fact" --context "$context" "$@"
