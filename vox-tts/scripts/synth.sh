#!/usr/bin/env bash
# Synthesize speech via vox. Writes WAV to the output path (default ./out.wav).
#
# Usage: synth.sh "<text>" [voice] [output_path]
#
# Examples:
#   synth.sh "Hello world"                           # voice design mode
#   synth.sh "(cheerful young woman)Hi there!"       # inline description
#   synth.sh "Wubba lubba dub dub" rick /tmp/r.wav   # clone mode

set -euo pipefail

VOX_URL="${VOX_URL:-https://vox.delo.sh}"
CFG="${VOX_CFG:-2.0}"
STEPS="${VOX_STEPS:-10}"

if [[ $# -lt 1 ]]; then
    echo "usage: $0 \"<text>\" [voice] [output_path]" >&2
    exit 1
fi

text="$1"
voice="${2:-}"
output="${3:-./out.wav}"

payload=$(python3 -c "
import json, os, sys
d = {'text': sys.argv[1], 'cfg': float(os.environ['CFG']), 'steps': int(os.environ['STEPS'])}
if sys.argv[2]:
    d['voice'] = sys.argv[2]
print(json.dumps(d))
" "$text" "$voice")

curl -fsS -X POST "${VOX_URL}/synthesize" \
    -H 'content-type: application/json' \
    -d "$payload" \
    -o "$output"

echo "wrote $output ($(stat -c%s "$output" 2>/dev/null || stat -f%z "$output") bytes)"
