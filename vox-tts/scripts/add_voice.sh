#!/usr/bin/env bash
# RAW-API FALLBACK. Prefer the CLI, which cuts a clean 10-15 s clip and sets prompt_text for you:
#   voxxy voice add FILE --auto -n <slug>
# Use this script only where the voxxy CLI is not installed. It uploads the file as given (the
# server keeps the first 30 s mono, which is NOT a clean cut) and only sets prompt_text if you pass it.
# Pass the exact words spoken in the clip as the 5th argument: it is the biggest quality lever.
#
# Usage: add_voice.sh <name> <display_name> <audio_path> [tags] [prompt_text]
#   tags: comma-separated, optional
#
# Example:
#   add_voice.sh morty "Morty Smith" ~/samples/morty.ogg cartoon,male "exact words spoken in the clip"

set -euo pipefail

VOX_URL="${VOX_URL:-https://vox.delo.sh}"

if [[ $# -lt 3 ]]; then
    echo "usage: $0 <name> <display_name> <audio_path> [tags] [prompt_text]" >&2
    echo "prefer: voxxy voice add <audio_path> --auto -n <name>" >&2
    exit 1
fi

name="$1"
display="$2"
audio="$3"
tags="${4:-}"
prompt_text="${5:-}"

if [[ ! -f "$audio" ]]; then
    echo "audio file not found: $audio" >&2
    exit 2
fi

if [[ -z "$prompt_text" ]]; then
    echo "warning: no prompt_text. voxcpm falls back to plain cloning (about 0.1 ecapa worse)." >&2
fi

curl -fsS -X POST "${VOX_URL}/voices" \
    -F "name=${name}" \
    -F "display_name=${display}" \
    ${tags:+-F "tags=${tags}"} \
    ${prompt_text:+-F "prompt_text=${prompt_text}"} \
    -F "audio=@${audio}" \
    | python3 -m json.tool
