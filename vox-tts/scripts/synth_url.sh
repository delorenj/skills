#!/usr/bin/env bash
# Synthesize speech via vox and print a Telegram-ready OGG/Opus URL.
#
# Usage: synth_url.sh "<text>" [voice]
#
# Prints the audio_url to stdout. The URL lives for VOX_AUDIO_TTL_SECONDS
# (default 3600) and is consumable by:
#   - Telegram sendVoice (voice=<url>)
#   - Discord webhook embeds
#   - Home Assistant media_player.play_media (media_content_id=<url>)
#   - HTML5 <audio src="...">
#
# Examples:
#   synth_url.sh "System online"
#   synth_url.sh "(cheerful young woman)Welcome back!"
#   synth_url.sh "Wubba lubba dub dub" rick
#
# Pipe-friendly:
#   url=$(synth_url.sh "Deployment finished")
#   curl -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendVoice" \
#        -d "chat_id=${TG_CHAT_ID}" -d "voice=${url}"

set -euo pipefail

VOX_URL="${VOX_URL:-https://vox.delo.sh}"
CFG="${VOX_CFG:-2.0}"
STEPS="${VOX_STEPS:-10}"

if [[ $# -lt 1 ]]; then
    echo "usage: $0 \"<text>\" [voice]" >&2
    exit 1
fi

text="$1"
voice="${2:-}"

payload=$(python3 -c "
import json, os, sys
d = {'text': sys.argv[1], 'cfg': float(os.environ['CFG']), 'steps': int(os.environ['STEPS'])}
if sys.argv[2]:
    d['voice'] = sys.argv[2]
print(json.dumps(d))
" "$text" "$voice")

response=$(
    curl -fsS -X POST "${VOX_URL}/synthesize-url" \
        -H 'content-type: application/json' \
        -d "$payload"
)

# Extract audio_url; bail loudly if it's missing so callers notice the contract changed.
url=$(echo "$response" | python3 -c "import json,sys; print(json.load(sys.stdin)['audio_url'])")
engine=$(echo "$response" | python3 -c "import json,sys; print(json.load(sys.stdin).get('engine','?'))")

# Emit engine to stderr for observability without polluting stdout.
echo "engine=${engine}" >&2
echo "$url"
