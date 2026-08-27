#!/usr/bin/env bash
# Set the active Hermes profile's Voxxy TTS voice.
# Usage: set_voice.sh <voice-slug>
set -euo pipefail

VOICE="${1:-carlin}"
BASE_URL="${VOX_BASE_URL:-https://vox.delo.sh}"

# Verify the voice exists on the Voxxy service.
if ! curl -sf "${BASE_URL}/voices/${VOICE}" >/dev/null 2>&1; then
    echo "Voice '${VOICE}' not found at ${BASE_URL}. Available voices:" >&2
    curl -sf "${BASE_URL}/voices" 2>/dev/null | \
        python3 -c 'import json,sys; data=json.load(sys.stdin); print("\n".join(v["name"] for v in data))' >&2 || true
    exit 1
fi

# Resolve the active Hermes TTS provider.
PROVIDER=$(hermes config get tts.provider 2>/dev/null || echo "voxxy")

case "${PROVIDER}" in
    voxxy|vox)
        hermes config set --force tts.vox.voice "${VOICE}"
        hermes config set --force tts.voice "${VOICE}"
        ;;
    *)
        echo "Unsupported TTS provider: ${PROVIDER}. This script only configures Voxxy." >&2
        exit 1
        ;;
esac

echo "Hermes TTS voice set to '${VOICE}' for provider '${PROVIDER}'."
echo "Restart Hermes or run /reset for the change to take effect."
