"""Shared stdlib helpers for the ebook-to-audiobook scripts.

Everything here is book-agnostic: hashing, atomic JSON writes, WAV validation.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AbkError(ValueError):
    """A refusal the caller should surface verbatim (exit 1, no traceback)."""


SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            sha.update(block)
    return sha.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode())


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()


def safe_id(value: Any, what: str = "id") -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise AbkError(f"{what} must be a safe filename: letters, digits, underscore, hyphen (got {value!r})")
    return value


def wav_metadata(source: bytes | Path) -> dict[str, Any]:
    """Validate an uncompressed PCM RIFF WAV end to end and describe it."""
    if isinstance(source, bytes):
        stream: Any = io.BytesIO(source)
        size = len(source)
        sha256 = hashlib.sha256(source).hexdigest()
    else:
        stream = source.open("rb")
        size = source.stat().st_size
        sha256 = file_hash(source)
    try:
        header = stream.read(12)
        if len(header) != 12 or header[:4] != b"RIFF" or header[8:] != b"WAVE":
            raise AbkError("Audio is not a RIFF WAV")
        if int.from_bytes(header[4:8], "little") + 8 != size:
            raise AbkError("WAV RIFF size does not match its bytes")
        stream.seek(0)
        with wave.open(stream, "rb") as reader:
            rate, channels, width, frames = (
                reader.getframerate(), reader.getnchannels(),
                reader.getsampwidth(), reader.getnframes(),
            )
            if reader.getcomptype() != "NONE" or width not in (1, 2, 3, 4):
                raise AbkError("WAV must contain uncompressed integer PCM")
            if rate <= 0 or channels < 1 or frames < 1:
                raise AbkError("WAV sample metadata is invalid or empty")
            frame_bytes = channels * width
            seen = 0
            while block := reader.readframes(8192):
                if len(block) % frame_bytes:
                    raise AbkError("WAV has an incomplete PCM frame")
                seen += len(block) // frame_bytes
            if seen != frames:
                raise AbkError("WAV PCM data is truncated")
        return {
            "duration_seconds": frames / rate, "sample_rate": rate, "channels": channels,
            "sample_width": width, "frames": frames, "bytes": size, "sha256": sha256,
        }
    except (wave.Error, EOFError) as exc:
        raise AbkError(f"Invalid WAV: {exc}") from exc
    finally:
        stream.close()
