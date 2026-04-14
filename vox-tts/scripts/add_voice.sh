#!/usr/bin/env bash
# Upload a new voice profile to vox. Auto-trimmed to 30s mono server-side.
#
# Usage: add_voice.sh <name> <display_name> <audio_path> [tags]
#   tags: comma-separated, optional
#
# Example:
#   add_voice.sh morty "Morty Smith" ~/samples/morty.ogg cartoon,male,rick-and-morty

set -euo pipefail

VOX_URL="${VOX_URL:-https://vox.delo.sh}"

if [[ $# -lt 3 ]]; then
    echo "usage: $0 <name> <display_name> <audio_path> [tags]" >&2
    echo "example: $0 morty \"Morty Smith\" morty.ogg cartoon,male" >&2
    exit 1
fi

name="$1"
display="$2"
audio="$3"
tags="${4:-}"

if [[ ! -f "$audio" ]]; then
    echo "audio file not found: $audio" >&2
    exit 2
fi

curl -fsS -X POST "${VOX_URL}/voices" \
    -F "name=${name}" \
    -F "display_name=${display}" \
    ${tags:+-F "tags=${tags}"} \
    -F "audio=@${audio}" \
    | python3 -m json.tool
