#!/usr/bin/env bash
# log-run.sh — record a disk-space-maintenance run in the machine profile.
#
#   log-run.sh <machine> "<free before>" "<free after>" "<one-line summary>"
#   log-run.sh carries-macbook-air "16G" "71G" "tier A: DerivedData, sim runtimes, caches; bounded ~/.cache via launchd"
#
# Prepends a dated line under "## Run log" and sets "**Last verified:**" to
# today. A machine without a profile gets one from _template.md, so a new
# machine is never cleaned without leaving a map behind.
set -euo pipefail

[ $# -eq 4 ] || { sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }
machine=$1 before=$2 after=$3 summary=$4

here=$(cd "$(dirname "$0")/.." && pwd)
dir="$here/references/machines"
profile="$dir/$machine.md"
today=$(date +%Y-%m-%d)

if [ ! -f "$profile" ]; then
  sed "s/<machine>/$machine/" "$dir/_template.md" > "$profile"
  echo "created $profile from template: fill in Identity, Space map and Accumulators" >&2
fi

grep -q '^## Run log' "$profile" || printf '\n## Run log\n' >> "$profile"

entry="- $today — free $before → $after. $summary"
tmp=$(mktemp)
awk -v entry="$entry" -v today="$today" '
  skip_blank { skip_blank = 0; if ($0 == "") next }
  /^\*\*Last verified:\*\*/ { sub(/\*\*Last verified:\*\* [^—]*/, "**Last verified:** " today " "); }
  { print }
  /^## Run log/ && !done { print ""; print entry; done = 1; skip_blank = 1 }
' "$profile" > "$tmp"
mv "$tmp" "$profile"

echo "logged: $entry"
echo "now update the profile's Space map / Known accumulators / Gotchas, then commit + push the skills repo"
