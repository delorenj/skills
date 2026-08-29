#!/usr/bin/env bash
# Clone a voice: upload raw audio to POST /voices, verify, and synthesize a
# confirmation message in the new voice.
#
# This script is the lower-level building block. The interactive agent workflow
# (present passage → receive Telegram voice message → upload → verify) is
# documented in SKILL.md under "Interactive voice cloning workflow".
#
# Usage:
#   clone_voice.sh <name> <display_name> <audio_path> [tags]
#
# Example:
#   clone_voice.sh jarad "Jarad" ~/downloads/voice_message.ogg clone,male
#
# What it does:
#   1. Slugifies the name (lowercase, hyphenated)
#   2. Uploads raw audio to POST /voices (no STT — raw file only)
#   3. Verifies with GET /voices/<name>
#   4. Synthesizes a confirmation message using POST /synthesize-url
#   5. Prints the confirmation audio URL to stdout

set -euo pipefail

VOX_URL="${VOX_URL:-https://vox.delo.sh}"

if [[ $# -lt 3 ]]; then
    echo "usage: $0 <name> <display_name> <audio_path> [tags]" >&2
    echo "example: $0 jarad \"Jarad\" ~/voice_message.ogg clone,male" >&2
    exit 1
fi

raw_name="$1"
display="$2"
audio="$3"
tags="${4:-}"

# Slugify: lowercase, spaces → hyphens, strip non-alphanumeric (keep hyphens)
name="$(echo "${raw_name}" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g; s/[^a-z0-9-]//g; s/--*/-/g; s/^-//; s/-$//')"

if [[ -z "$name" ]]; then
    echo "error: slugified name is empty — provide a valid name" >&2
    exit 2
fi

if [[ ! -f "$audio" ]]; then
    echo "audio file not found: $audio" >&2
    exit 3
fi

echo "→ Uploading voice '${name}' (display: '${display}') from ${audio}..."

# Step 1: Upload raw audio to POST /voices (no STT — raw file only)
upload_result="$(
    curl -fsS -X POST "${VOX_URL}/voices" \
        -F "name=${name}" \
        -F "display_name=${display}" \
        ${tags:+-F "tags=${tags}"} \
        -F "audio=@${audio}"
)"

echo "✓ Voice uploaded:"
echo "${upload_result}" | python3 -m json.tool

# Step 2: Verify the voice was registered
echo "→ Verifying voice '${name}'..."
verify_result="$(curl -fsS "${VOX_URL}/voices/${name}")"
echo "✓ Voice verified:"
echo "${verify_result}" | python3 -m json.tool

# Step 3: Synthesize a confirmation message in the new voice
confirm_text="Voice cloning complete. I'm now speaking in the ${display} voice. How do I sound?"
echo "→ Synthesizing confirmation message..."

synth_result="$(
    curl -fsS -X POST "${VOX_URL}/synthesize-url" \
        -H 'content-type: application/json' \
        -d "$(python3 -c "import json; print(json.dumps({'text': '''${confirm_text}''', 'voice': '${name}'}))")"
)"

audio_url="$(echo "${synth_result}" | python3 -c "import json,sys; print(json.load(sys.stdin)['audio_url'])")"

echo "✓ Confirmation synthesized:"
echo "${synth_result}" | python3 -m json.tool
echo ""
echo "🎧 Confirmation audio URL: ${audio_url}"
echo ""
echo "Voice '${name}' is ready. Use voice=\"${name}\" in speak_url or /synthesize-url."
