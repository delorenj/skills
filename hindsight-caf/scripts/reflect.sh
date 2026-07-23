#!/bin/bash

# Reflect on memories in the CoachingAgentFramework Hindsight bank.
#
# Usage:
#   reflect.sh "<question>"
#   reflect.sh "<question>" --context "architecture review" --budget high

set -euo pipefail

BANK="CoachingAgentFramework"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"<question>\" [extra hindsight args]" >&2
  exit 1
fi

question="$1"
shift

exec hindsight memory reflect "$BANK" "$question" "$@"
