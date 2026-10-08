"""Shared test fixtures: a fake VoxCPM sidecar and tiny WAV builder (no GPU, docker or ffmpeg)."""
from __future__ import annotations

import base64
import io
import json
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def make_wav(seconds: float = 0.1, rate: int = 8000, value: int = 1000) -> bytes:
    frames = max(1, int(seconds * rate))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes(struct.pack("<h", value) * frames)
    return buffer.getvalue()


class FakeEngine:
    """Replaces subprocess.run for tokenizer + synth commands; records every synth payload."""

    def __init__(self, engine_name: str = "voxcpm", fail_on: set[str] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.engine_name = engine_name
        self.fail_on = fail_on or set()

    def __call__(self, command, input=None, **kwargs):  # noqa: A002
        if "-c" in command:  # tokenizer
            texts = json.loads(input)
            body = {"model_revision": "a" * 40, "input_text_tokens": [max(1, len(t) // 4) for t in texts]}
            return subprocess.CompletedProcess(command, 0, json.dumps(body).encode(), b"")
        payload = json.loads(input)
        self.calls.append(payload)
        if any(marker in payload["text"] for marker in self.fail_on):
            raise subprocess.CalledProcessError(22, command, b"", b"engine exploded")
        wav = make_wav(0.05 + 0.001 * len(payload["text"]))
        body = {"engine": self.engine_name, "wav_b64": base64.b64encode(wav).decode(),
                "bytes": len(wav), "sample_rate": 8000, "duration_s": None}
        return subprocess.CompletedProcess(command, 0, json.dumps(body).encode(), b"")
