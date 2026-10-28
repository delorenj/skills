#!/usr/bin/env bash
# RAW-API FALLBACK. Prefer the CLI:
#   voxxy voice clone "<who>"              (from a description)
#   voxxy voice add FILE --auto -n <slug>  (from a recording; clean cut + transcript)
# This script uploads the audio as given (no clean cut; the server keeps the first 30 s) and only
# sets prompt_text if you pass it. Use it where the voxxy CLI is not installed.
#
# Uploads to POST /voices, verifies, synthesizes a confirmation in the new voice and FAILS if the
# engine that answered was not a real clone (elevenlabs ignores reference audio).
#
# Usage:
#   clone_voice.sh <name> <display_name> <audio_path> [tags] [prompt_text]
#   prompt_text: the exact words spoken in the clip (the biggest quality lever)
#
# Example:
#   clone_voice.sh jarad "Jarad" ~/downloads/voice_message.ogg clone,male
#
# What it does:
#   1. Slugifies the name (lowercase, hyphenated)
#   2. Uploads the audio to POST /voices (with prompt_text when given)
#   3. Verifies with GET /voices/<name>
#   4. Synthesizes a confirmation message using POST /synthesize-url
#   5. Prints the confirmation audio URL to stdout

set -euo pipefail

VOX_URL="${VOX_URL:-https://vox.delo.sh}"

if [[ $# -lt 3 ]]; then
    echo "usage: $0 <name> <display_name> <audio_path> [tags] [prompt_text]" >&2
    echo "prefer: voxxy voice add <audio_path> --auto -n <name>" >&2
    echo "example: $0 jarad \"Jarad\" ~/voice_message.ogg clone,male" >&2
    exit 1
fi

raw_name="$1"
display="$2"
audio="$3"
tags="${4:-}"
prompt_text="${5:-}"

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

# Step 1: Upload to POST /voices
upload_result="$(
    curl -fsS -X POST "${VOX_URL}/voices" \
        -F "name=${name}" \
        -F "display_name=${display}" \
        ${tags:+-F "tags=${tags}"} \
        ${prompt_text:+-F "prompt_text=${prompt_text}"} \
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

engine="$(echo "${synth_result}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('engine','?'))")"
if [[ "$engine" != "voxcpm" && "$engine" != "vibevoice" ]]; then
    echo "NOT A CLONE: synthesis was served by engine '${engine}', which ignores the reference audio." >&2
    echo "Check 'voxxy daemon status' and stop ollama models holding VRAM, then retry." >&2
    exit 4
fi

echo "✓ Confirmation synthesized (engine: ${engine}):"
echo "${synth_result}" | python3 -m json.tool
echo ""
echo "🎧 Confirmation audio URL: ${audio_url}"
echo ""
echo "Voice '${name}' is ready. Use voice=\"${name}\" in speak_url or /synthesize-url."
