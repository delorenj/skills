#!/usr/bin/env python3
"""Frozen-reference VoxCPM2 chapter renderer: prepare -> voices -> render -> report.

    render_chapter.py prepare --manifest chapter.json --output audio/
    render_chapter.py voices  --manifest chapter.json --output audio/     # design one reference clip per voice
    render_chapter.py preview --manifest chapter.json --output audio/     # voice-preview.mp3: audition the cast
    render_chapter.py render  --manifest chapter.json --output audio/     # chunks + assemble + master + mp3
    render_chapter.py redo    --manifest chapter.json --output audio/ --chunk 000116 --reason "ASR: opening mangled"
    render_chapter.py status  --manifest chapter.json --output audio/
    render_chapter.py report  --manifest chapter.json --output audio/ [--llm-usage-snapshot usage.json]

Design rules baked in (each one cost the pilot run something to learn):
  * Talks to the VoxCPM sidecar directly. The public vox API and `voxxy speak` cannot pin an
    engine, so a down engine silently answers in another engine's (or ElevenLabs') voice. A
    response whose engine is not "voxcpm" is a hard failure here.
  * One voice = one frozen reference clip, designed once with "(description)reference_text".
    Every chunk is then conditioned on reference audio only; descriptions never reach chapter text.
  * Every request is appended to requests.jsonl (started -> success|failure) before and after the
    call. Caches are only trusted when fingerprint, WAV bytes, and a success receipt all agree.
  * A failed/unfinished request is never retried implicitly: a client timeout does not prove the
    GPU stopped. Confirm the engine is idle, then pass --retry-failed.
  * Resumable: rerunning render skips every cached chunk and costs ~0 synth calls.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid
import wave
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from abk_common import (
    AbkError, atomic_write, canonical, digest, file_hash, normalized, read_json, safe_id,
    utc_now, wav_metadata, write_json,
)

ChapterError = AbkError  # historical name used in the pilot run's tests/logs

TOKEN_LABEL = "Exact VoxCPM2 input text tokens; not billable, audio, or LLM tokens"
DEFAULT_ENGINE_URL = "http://voxxy-engine-voxcpm:8000/v1/synthesize"
CHUNK_TARGET, CHUNK_MAX = 450, 650  # characters; the pilot used these with 0 truncations in 296 chunks
TURN_PAUSE_MS, PARAGRAPH_PAUSE_MS, FADE_MS = 120, 280, 8
LOUDNESS = {"I": -20, "TP": -3, "LRA": 7}
MP3_KBPS = 128

TOKENIZER_CODE = r'''
import importlib.metadata, json, os, re, runpy, sys
from pathlib import Path
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from transformers import LlamaTokenizerFast
root = Path("/cache/huggingface/hub/models--openbmb--VoxCPM2")
revision = (root / "refs/main").read_text().strip()
if not re.fullmatch(r"[0-9a-f]{40}", revision):
    raise ValueError("Invalid VoxCPM2 model revision")
snapshot = root / "snapshots" / revision
utils = importlib.metadata.distribution("voxcpm").locate_file("voxcpm/model/utils.py")
mask = runpy.run_path(str(utils))["mask_multichar_chinese_tokens"]
tokenizer = mask(LlamaTokenizerFast.from_pretrained(str(snapshot), local_files_only=True))
counts = []
for text in json.load(sys.stdin):
    ids = tokenizer(re.sub(r"\s+", " ", text.replace("\n", " ")))
    if not isinstance(ids, list) or any(type(i) is not int for i in ids):
        raise TypeError("VoxCPM2 tokenizer must return a list of integer IDs")
    counts.append(len(ids))
print(json.dumps({"model_revision": revision, "input_text_tokens": counts}))
'''


class Engine:
    """Where the VoxCPM sidecar lives. All fields overridable by env or CLI flag."""

    def __init__(
        self, url: str | None = None, core_container: str | None = None,
        engine_container: str | None = None, tokenizer: str = "voxcpm-docker", timeout: int = 240,
    ) -> None:
        self.url = url or os.environ.get("VOXCPM_ENGINE_URL", DEFAULT_ENGINE_URL)
        # curl runs inside this container so the docker-network hostname resolves; "" = run curl on the host.
        self.core_container = os.environ.get("VOX_CORE_CONTAINER", "vox") if core_container is None else core_container
        self.engine_container = engine_container or os.environ.get("VOXCPM_ENGINE_CONTAINER", "voxxy-engine-voxcpm")
        if tokenizer not in ("voxcpm-docker", "none"):
            raise ChapterError("tokenizer must be voxcpm-docker or none")
        self.tokenizer = tokenizer
        self.timeout = timeout

    def synth_command(self) -> list[str]:
        curl = ["curl", "-fsS", "--connect-timeout", "5", "--max-time", str(self.timeout),
                "-H", "content-type:application/json", "--data-binary", "@-", self.url]
        return ["docker", "exec", "-i", self.core_container, *curl] if self.core_container else curl

    def tokenizer_command(self) -> list[str]:
        return ["docker", "exec", "-i", self.engine_container, "/opt/venv/bin/python", "-B", "-c", TOKENIZER_CODE]


# ---------------------------------------------------------------- manifest/plan


def positive_int(value: Any, field: str) -> int:
    if type(value) is not int or value < 1:
        raise ChapterError(f"{field} must be a positive integer")
    return value


def nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not normalized(value):
        raise ChapterError(f"{field} must be a nonempty string")
    return normalized(value)


def validate_manifest(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ChapterError("Manifest must be an object")
    result = dict(data)
    result["title"] = nonempty(data.get("title"), "title")
    chapter = data.get("chapter")
    if type(chapter) is int:
        if chapter < 0:
            raise ChapterError("chapter must be >= 0")
    else:
        nonempty(chapter, "chapter")
    settings = data.get("settings", {})
    if not isinstance(settings, dict) or set(settings) - {"cfg", "steps"}:
        raise ChapterError("settings supports only cfg and steps")
    cfg, steps = settings.get("cfg", 2.0), settings.get("steps", 12)
    if type(cfg) not in (int, float) or not math.isfinite(cfg) or not 1 <= cfg <= 5:
        raise ChapterError("settings.cfg must be finite and between 1 and 5")
    if type(steps) is not int or not 1 <= steps <= 50:
        raise ChapterError("settings.steps must be an integer between 1 and 50")
    result["settings"] = {"cfg": float(cfg), "steps": steps}
    voices = data.get("voices")
    if not isinstance(voices, dict) or not voices:
        raise ChapterError("voices must be a nonempty object")
    result["voices"] = {}
    for speaker, voice in voices.items():
        safe_id(speaker, "voice id")
        if not isinstance(voice, dict):
            raise ChapterError(f"voices.{speaker} must be an object")
        if voice.get("reference_audio"):
            nonempty(voice["reference_audio"], f"voices.{speaker}.reference_audio")
            result["voices"][speaker] = dict(voice)
            continue
        description = nonempty(voice.get("description"), f"voices.{speaker}.description")
        reference_text = nonempty(voice.get("reference_text"), f"voices.{speaker}.reference_text")
        if "(" in description or ")" in description:
            raise ChapterError("Voice descriptions must not contain parentheses")
        result["voices"][speaker] = {**voice, "description": description, "reference_text": reference_text}
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ChapterError("segments must be a nonempty list")
    result["segments"] = []
    previous = -1
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ChapterError(f"segments[{index}] must be an object")
        if segment.get("speaker") not in voices:
            raise ChapterError(f"segments[{index}] has an unknown speaker")
        paragraph = segment.get("paragraph")
        if type(paragraph) is not int or paragraph < 0 or paragraph < previous:
            raise ChapterError("paragraph must be a nonnegative, nondecreasing integer")
        previous = paragraph
        result["segments"].append({**segment, "text": nonempty(segment.get("text"), f"segments[{index}].text")})
    return result


def chunk_text(text: str, target: int = CHUNK_TARGET, sentence_max: int = CHUNK_MAX) -> list[str]:
    """Split on sentence boundaries into chunks of ~target chars, never above sentence_max.

    Invariant (checked): ' '.join(chunks) == normalized(text). Nothing is dropped or reworded.
    """
    if not 1 <= target <= sentence_max:
        raise ChapterError("Invalid chunk limits")
    text = normalized(text)
    if not text:
        raise ChapterError("Cannot chunk empty text")
    if any(len(word) > sentence_max for word in text.split()):
        raise ChapterError(f"A word exceeds the {sentence_max}-character hard limit")
    sentences = re.split(r'(?<=[.!?。！？])\s+|(?<=[.!?]["”’])\s+', text)
    units: list[str] = []
    for sentence in sentences:
        remaining = sentence
        limit = target if len(sentence) > sentence_max else sentence_max
        while len(remaining) > limit:
            breaks = [m.start() for m in re.finditer(r"\s+", remaining) if m.start() <= target]
            if not breaks:
                breaks = [m.start() for m in re.finditer(r"\s+", remaining) if m.start() <= sentence_max]
            if not breaks:
                if len(remaining) <= sentence_max:
                    break
                raise ChapterError("Cannot split text without breaking a word")
            punctuation = [pos for pos in breaks if remaining[pos - 1] in ",;:—–"]
            end = punctuation[-1] if punctuation else breaks[-1]
            units.append(remaining[:end])
            remaining = remaining[end:].lstrip()
        units.append(remaining)
    chunks: list[str] = []
    current = ""
    for unit in units:
        joined = f"{current} {unit}" if current else unit
        if current and len(joined) > target:
            chunks.append(current)
            current = unit
        else:
            current = joined
    if current:
        chunks.append(current)
    if " ".join(chunks) != text or any(len(chunk) > sentence_max for chunk in chunks):
        raise ChapterError("Chunk coverage invariant failed")
    return chunks


def tokenize_texts(engine: Engine, texts: list[str]) -> dict[str, Any]:
    if engine.tokenizer == "none":
        return {"model_revision": "unversioned", "input_text_tokens": [None] * len(texts)}
    done = subprocess.run(engine.tokenizer_command(), input=canonical(texts), capture_output=True, check=True, timeout=120)
    result = json.loads(done.stdout)
    counts = result.get("input_text_tokens")
    if not re.fullmatch(r"[0-9a-f]{40}", str(result.get("model_revision", ""))):
        raise ChapterError("Tokenizer returned an invalid model revision")
    if not isinstance(counts, list) or len(counts) != len(texts) or any(type(c) is not int or c < 1 for c in counts):
        raise ChapterError("Tokenizer returned invalid exact input text token counts")
    return result


def build_plan(manifest_path: Path, engine: Engine) -> dict[str, Any]:
    manifest = validate_manifest(read_json(manifest_path))
    base = manifest_path.resolve().parent
    pinned: dict[str, dict[str, Any]] = {}
    designs: list[dict[str, Any]] = []
    for speaker, voice in sorted(manifest["voices"].items()):
        if voice.get("reference_audio"):
            path = (base / voice["reference_audio"]).resolve() if not Path(voice["reference_audio"]).is_absolute() else Path(voice["reference_audio"])
            if not path.is_file():
                raise ChapterError(f"voices.{speaker}.reference_audio not found: {path}")
            info = wav_metadata(path)
            pinned[speaker] = {"path": str(path), "sha256": info["sha256"], "duration_seconds": info["duration_seconds"]}
        else:
            designs.append({"id": speaker, "speaker": speaker, "text": f"({voice['description']}){voice['reference_text']}"})
    used = {segment["speaker"] for segment in manifest["segments"]}
    chunks: list[dict[str, Any]] = []
    for segment_index, segment in enumerate(manifest["segments"]):
        for part, text in enumerate(chunk_text(segment["text"])):
            chunks.append({
                "id": f"{len(chunks) + 1:06d}", "speaker": segment["speaker"], "text": text,
                "paragraph": segment["paragraph"], "segment": segment_index, "part": part,
            })
    designs = [item for item in designs if item["speaker"] in used]  # never pay to design a silent voice
    tokenization = tokenize_texts(engine, [item["text"] for item in designs + chunks])
    for item, count in zip(designs + chunks, tokenization["input_text_tokens"], strict=True):
        item["input_text_tokens"] = count
        item["characters"] = len(item["text"])
    plan = {
        "version": 1, "manifest": manifest, "manifest_sha256": digest(manifest),
        "model_revision": tokenization["model_revision"], "token_label": TOKEN_LABEL,
        "tokenizer": engine.tokenizer, "pinned": pinned, "designs": designs, "chunks": chunks,
        "planned_input_text_tokens": {
            "design": sum(i["input_text_tokens"] or 0 for i in designs),
            "chapter": sum(i["input_text_tokens"] or 0 for i in chunks),
        },
    }
    plan["plan_sha256"] = digest(plan)
    return plan


def prepare(manifest_path: Path, root: Path, engine: Engine) -> dict[str, Any]:
    plan = build_plan(manifest_path, engine)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "prepared.json"
    if path.exists() and read_json(path) != plan:
        raise ChapterError("Prepared manifest/model changed; use a fresh output directory")
    write_json(path, plan)
    return plan


def load_plan(manifest_path: Path, root: Path, engine: Engine) -> dict[str, Any]:
    path = root / "prepared.json"
    if not path.is_file():
        raise ChapterError("Run prepare first")
    stored = read_json(path)
    if stored != build_plan(manifest_path, engine):
        raise ChapterError("Prepared manifest, tokens, or model revision changed; use a fresh output directory")
    return stored


# ------------------------------------------------------------- request ledger


def decode_response(response: Any) -> tuple[bytes, dict[str, Any]]:
    if not isinstance(response, dict) or response.get("engine") != "voxcpm":
        raise ChapterError("Synthesis response engine must be voxcpm; fallback is forbidden")
    encoded = response.get("wav_b64")
    if not isinstance(encoded, str):
        raise ChapterError("Synthesis response has no WAV base64 string")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ChapterError("Invalid WAV base64") from exc
    metadata = wav_metadata(data)
    for field, expected in (("bytes", metadata["bytes"]), ("sample_rate", metadata["sample_rate"])):
        if type(response.get(field)) is not int or response[field] != expected:
            raise ChapterError(f"Synthesis {field} disagrees with the WAV")
    duration = response.get("duration_s")
    if duration is not None and (
        type(duration) not in (int, float) or not math.isfinite(duration)
        or abs(duration - metadata["duration_seconds"]) > 1 / metadata["sample_rate"]
    ):
        raise ChapterError("Synthesis duration disagrees with the WAV")
    return data, metadata


def request_spec(
    plan: dict[str, Any], engine: Engine, item: dict[str, Any], phase: str, reference_sha256: str | None,
) -> dict[str, Any]:
    return {
        "version": 1, "engine": "voxcpm", "endpoint": engine.url, "phase": phase, "item": item,
        "reference_sha256": reference_sha256, "settings": plan["manifest"]["settings"],
        "model_revision": plan["model_revision"],
        "conditioning": "reference_audio_only" if reference_sha256 else "voice_design",
    }


def append_request(root: Path, record: dict[str, Any]) -> None:
    with (root / "requests.jsonl").open("ab") as handle:
        handle.write(canonical(record) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def request_records(root: Path) -> list[dict[str, Any]]:
    path = root / "requests.jsonl"
    if not path.exists():
        return []
    records: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                record = json.loads(line)
                request_id, status = record["request_id"], record["status"]
                if status not in ("started", "success", "failure"):
                    raise ChapterError("Unknown request status")
                previous = records.get(request_id)
                if previous is not None:
                    if previous["status"] != "started" or status == "started":
                        raise ChapterError("Duplicate request lifecycle event")
                    for field in ("request_fingerprint", "phase", "speaker", "input_text_tokens"):
                        if previous[field] != record[field]:
                            raise ChapterError("Request lifecycle identity changed")
                elif status != "started":
                    raise ChapterError("Request completion has no start record")
                records[request_id] = record
            except (KeyError, TypeError, json.JSONDecodeError, ChapterError) as exc:
                raise ChapterError(f"Invalid requests.jsonl line {line_number}: {exc}") from exc
    return list(records.values())


def cache_paths(root: Path, phase: str, item_id: str) -> tuple[Path, Path]:
    directory = root / ("refs" if phase == "design" else "chunks")
    return directory / f"{item_id}.wav", directory / f"{item_id}.json"


def check_cache(root: Path, spec: dict[str, Any]) -> dict[str, Any] | None:
    wav_path, metadata_path = cache_paths(root, spec["phase"], spec["item"]["id"])
    if not wav_path.exists() and not metadata_path.exists():
        return None
    if not wav_path.is_file() or not metadata_path.is_file():
        raise ChapterError(f"Incomplete/unknown cache: {wav_path}")
    metadata = read_json(metadata_path)
    if metadata.get("request_fingerprint") != digest(spec) or metadata.get("request") != spec:
        raise ChapterError(f"Stale request fingerprint/reference/settings: {wav_path}")
    actual = wav_metadata(wav_path)
    if metadata.get("wav") != actual:
        raise ChapterError(f"Corrupted cached audio or metadata: {wav_path}")
    receipt = next((r for r in request_records(root) if r["request_id"] == metadata.get("request_id")), None)
    if not receipt or receipt["status"] != "success" or receipt["wav"] != actual or receipt["request_fingerprint"] != digest(spec):
        raise ChapterError(f"Cache has no matching successful request receipt: {wav_path}")
    return metadata


def check_inventory(root: Path, phase: str, items: list[dict[str, Any]]) -> None:
    directory = root / ("refs" if phase == "design" else "chunks")
    expected = {f"{item['id']}{suffix}" for item in items for suffix in (".wav", ".json")}
    if directory.exists():
        unknown = [p.name for p in directory.iterdir() if p.name not in expected]
        if unknown:
            raise ChapterError(f"Unknown cache files in {directory}: {', '.join(sorted(unknown))}")


def superseded_request_ids(root: Path) -> set[str]:
    path = root / "superseded.jsonl"
    if not path.exists():
        return set()
    return {json.loads(line)["request_id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def check_previous_attempts(root: Path, spec: dict[str, Any], retry_failed: bool) -> None:
    superseded = superseded_request_ids(root)
    for record in request_records(root):
        if record["phase"] != spec["phase"] or record["item_id"] != spec["item"]["id"]:
            continue
        if record["request_id"] in superseded:
            continue  # a deliberately retired take; its GPU time stays in the ledger
        if record["request_fingerprint"] != digest(spec):
            raise ChapterError("Historical request is stale; use a fresh output directory")
        if record["status"] == "success":
            raise ChapterError("Successful request has lost its frozen cache; refusing to regenerate")
        if not retry_failed:
            raise ChapterError(
                "Prior failed/unfinished request; confirm the engine is idle (nvidia-smi / engine logs), "
                "then explicitly use --retry-failed. A timeout does not prove cancellation."
            )


def generate_request(
    root: Path, engine: Engine, spec: dict[str, Any], reference: bytes | None = None, retry_failed: bool = False,
) -> dict[str, Any]:
    if (hashlib.sha256(reference).hexdigest() if reference is not None else None) != spec["reference_sha256"]:
        raise ChapterError("Reference bytes do not match the frozen reference hash")
    cached = check_cache(root, spec)
    if cached is not None:
        return cached
    check_previous_attempts(root, spec, retry_failed)
    wav_path, metadata_path = cache_paths(root, spec["phase"], spec["item"]["id"])
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"text": spec["item"]["text"], **spec["settings"]}
    if reference is not None:
        payload["reference_audio_b64"] = base64.b64encode(reference).decode("ascii")
    record: dict[str, Any] = {
        "request_id": uuid.uuid4().hex, "timestamp_utc": utc_now(), "phase": spec["phase"],
        "speaker": spec["item"]["speaker"], "item_id": spec["item"]["id"],
        "request_fingerprint": digest(spec), "reference_sha256": spec["reference_sha256"],
        "settings": spec["settings"], "model_revision": spec["model_revision"],
        "input_text_tokens": spec["item"]["input_text_tokens"], "token_label": TOKEN_LABEL,
        "engine": "voxcpm", "status": "started", "success": None,
        "wall_seconds": None, "wav": None, "error": None,
    }
    append_request(root, record)
    start = time.perf_counter()
    try:
        done = subprocess.run(engine.synth_command(), input=canonical(payload), capture_output=True,
                              check=True, timeout=engine.timeout + 10)
        audio, wav = decode_response(json.loads(done.stdout))
        record["wav"] = wav
        record["wall_seconds"] = time.perf_counter() - start
        metadata = {"request_id": record["request_id"], "request_fingerprint": digest(spec), "request": spec, "wav": wav}
        atomic_write(wav_path, audio)
        write_json(metadata_path, metadata)
    except BaseException as exc:
        record.update({"status": "failure", "success": False, "wall_seconds": time.perf_counter() - start,
                       "completed_utc": utc_now(), "error": f"{type(exc).__name__}: {exc}"})
        append_request(root, record)
        raise
    record.update({"status": "success", "success": True, "completed_utc": utc_now()})
    append_request(root, record)
    return metadata


# ------------------------------------------------------------ voices / render


def voices(plan: dict[str, Any], root: Path, engine: Engine, retry_failed: bool = False) -> dict[str, Any]:
    check_inventory(root, "design", plan["designs"])
    specs = [request_spec(plan, engine, item, "design", None) for item in plan["designs"]]
    for spec in specs:
        if check_cache(root, spec) is None:
            check_previous_attempts(root, spec, retry_failed)
    return {s["item"]["id"]: generate_request(root, engine, s, retry_failed=retry_failed) for s in specs}


def load_references(plan: dict[str, Any], root: Path, engine: Engine) -> dict[str, bytes]:
    refs: dict[str, bytes] = {}
    for item in plan["designs"]:
        metadata = check_cache(root, request_spec(plan, engine, item, "design", None))
        if metadata is None:
            raise ChapterError(f"Missing frozen reference for {item['id']}; run voices first")
        path, _ = cache_paths(root, "design", item["id"])
        refs[item["id"]] = path.read_bytes()
        if hashlib.sha256(refs[item["id"]]).hexdigest() != metadata["wav"]["sha256"]:
            raise ChapterError("Frozen reference changed while loading")
    for speaker, info in plan["pinned"].items():
        data = Path(info["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != info["sha256"]:
            raise ChapterError(f"Pinned reference for {speaker} changed since prepare; rerun prepare in a fresh output dir")
        refs[speaker] = data
    return refs


def pause_frames(previous: dict[str, Any], current: dict[str, Any], rate: int) -> int:
    if previous["paragraph"] != current["paragraph"]:
        return round(rate * PARAGRAPH_PAUSE_MS / 1000)
    if previous["segment"] != current["segment"]:
        return round(rate * TURN_PAUSE_MS / 1000)
    return 0


def fade_pcm(block: bytes, offset: int, total: int, width: int, channels: int, fade: int) -> bytes:
    if fade <= 1 or (offset >= fade and offset + len(block) // (width * channels) <= total - fade):
        return block
    result = bytearray(block)
    frame_size = width * channels
    for local in range(len(block) // frame_size):
        frame = offset + local
        gain = min(1.0, frame / (fade - 1), (total - 1 - frame) / (fade - 1))
        if gain == 1:
            continue
        for channel in range(channels):
            position = local * frame_size + channel * width
            sample = int.from_bytes(block[position:position + width], "little", signed=width != 1)
            if width == 1:
                sample -= 128
            sample = round(sample * gain) + (128 if width == 1 else 0)
            result[position:position + width] = sample.to_bytes(width, "little", signed=width != 1)
    return bytes(result)


def assemble_wav(chunks: list[tuple[dict[str, Any], Path]], destination: Path) -> dict[str, Any]:
    if not chunks:
        raise ChapterError("No chapter chunks to assemble")
    metadata = [wav_metadata(path) for _, path in chunks]
    first = metadata[0]
    fields = ("sample_rate", "channels", "sample_width")
    if any(any(item[f] != first[f] for f in fields) for item in metadata):
        raise ChapterError("Chunk WAV rates/channels/sample widths do not match")
    rate, channels, width = (first[f] for f in fields)
    temporary = destination.with_name(destination.stem + ".part.wav")
    pauses = 0
    with wave.open(str(temporary), "wb") as writer:
        writer.setparams((channels, width, rate, 0, "NONE", "not compressed"))
        for index, ((item, path), info) in enumerate(zip(chunks, metadata, strict=True)):
            if index:
                silence_frames = pause_frames(chunks[index - 1][0], item, rate)
                silence = (b"\x80" if width == 1 else b"\x00" * width) * channels
                writer.writeframesraw(silence * silence_frames)
                pauses += silence_frames
            fade = min(round(rate * FADE_MS / 1000), info["frames"] // 2)
            with wave.open(str(path), "rb") as reader:
                offset = 0
                while block := reader.readframes(8192):
                    writer.writeframesraw(fade_pcm(block, offset, info["frames"], width, channels, fade))
                    offset += len(block) // (width * channels)
    temporary.replace(destination)
    result = wav_metadata(destination)
    if result["frames"] != sum(item["frames"] for item in metadata) + pauses:
        raise ChapterError("Assembly frame count does not match audio plus pauses")
    return {"wav": result, "pause_frames": pauses, "pause_seconds": pauses / rate, "fade_ms": FADE_MS}


def master_audio(raw: Path, mastered: Path, mp3: Path, rate: int) -> None:
    """Two-pass loudnorm over the WHOLE chapter (per-chunk loudnorm makes voices pump)."""
    base = ["ffmpeg", "-nostdin", "-hide_banner", "-y"]
    target = f"loudnorm=I={LOUDNESS['I']}:TP={LOUDNESS['TP']}:LRA={LOUDNESS['LRA']}"
    measure = subprocess.run(base + ["-i", str(raw.resolve()), "-af", target + ":print_format=json", "-f", "null", "-"],
                             capture_output=True, check=True, timeout=1800)
    match = re.search(r'\{\s*"input_i".*?\}', measure.stderr.decode("utf-8", errors="replace"), re.DOTALL)
    if match is None:
        raise ChapterError("ffmpeg loudnorm did not return whole-chapter measurements")
    measured = json.loads(match.group())
    mapping = {"measured_I": "input_i", "measured_TP": "input_tp", "measured_LRA": "input_lra",
               "measured_thresh": "input_thresh", "offset": "target_offset"}
    values = {}
    for key, field in mapping.items():
        value = float(measured[field])
        if not math.isfinite(value):
            raise ChapterError("Nonfinite loudness measurement (possibly silent audio)")
        values[key] = value
    filter_text = target + ":linear=true:" + ":".join(f"{k}={v}" for k, v in values.items())
    part_wav = mastered.with_name(mastered.stem + ".part.wav")
    part_mp3 = mp3.with_name(mp3.stem + ".part.mp3")
    subprocess.run(base + ["-i", str(raw.resolve()), "-af", filter_text, "-ar", str(rate), "-c:a", "pcm_s16le", str(part_wav.resolve())],
                   capture_output=True, check=True, timeout=1800)
    wav_metadata(part_wav)
    part_wav.replace(mastered)
    subprocess.run(base + ["-i", str(mastered.resolve()), "-c:a", "libmp3lame", "-b:a", f"{MP3_KBPS}k", str(part_mp3.resolve())],
                   capture_output=True, check=True, timeout=1800)
    if not part_mp3.is_file() or not part_mp3.stat().st_size:
        raise ChapterError("ffmpeg produced an empty MP3")
    part_mp3.replace(mp3)


def redo(plan: dict[str, Any], root: Path, chunk_ids: list[str], reason: str) -> dict[str, Any]:
    """Retire specific successful chunks (and the assembled outputs) so the next `render` re-rolls only those.

    Old takes move to superseded/<stamp>/ and stay in requests.jsonl, so metrics still count the GPU time.
    """
    if not reason.strip():
        raise ChapterError("redo needs a --reason (it is recorded in superseded.jsonl)")
    known = {c["id"] for c in plan["chunks"]}
    unknown = sorted(set(chunk_ids) - known)
    if unknown:
        raise ChapterError(f"Unknown chunk ids: {', '.join(unknown)}")
    archive = root / "superseded" / utc_now().replace(":", "").replace("+", "_")
    moved: list[str] = []
    entries = []
    for chunk_id in sorted(set(chunk_ids)):
        wav_path, metadata_path = cache_paths(root, "chapter", chunk_id)
        if not (wav_path.is_file() and metadata_path.is_file()):
            raise ChapterError(f"Chunk {chunk_id} has no complete cache to retire")
        entries.append({"request_id": read_json(metadata_path)["request_id"], "item_id": chunk_id,
                        "timestamp_utc": utc_now(), "reason": reason})
    archive.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        for path in cache_paths(root, "chapter", entry["item_id"]):
            path.replace(archive / path.name)
            moved.append(path.name)
    for name in ("assembly.json", "chapter.raw.wav", "chapter.wav", "chapter.mp3"):
        if (root / name).exists():
            (root / name).replace(archive / name)
            moved.append(name)
    with (root / "superseded.jsonl").open("ab") as handle:
        for entry in entries:
            handle.write(canonical(entry) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    return {"retired_chunks": [e["item_id"] for e in entries], "archive": str(archive), "moved": moved}


def encode_mp3(wav: Path, mp3: Path) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-y", "-i", str(wav.resolve()), "-c:a", "libmp3lame",
                    "-b:a", f"{MP3_KBPS}k", str(mp3.resolve())], capture_output=True, check=True, timeout=600)


def preview(plan: dict[str, Any], root: Path, engine: Engine) -> dict[str, Any]:
    """Concatenate every voice's frozen reference (cast order) into voice-preview.wav/.mp3 for auditioning."""
    load_references(plan, root, engine)  # validates designed refs and pinned hashes first
    rows: list[tuple[dict[str, Any], Path]] = []
    order = [d["id"] for d in plan["designs"]] + sorted(plan["pinned"])
    for index, speaker in enumerate(order):
        path = Path(plan["pinned"][speaker]["path"]) if speaker in plan["pinned"] else cache_paths(root, "design", speaker)[0]
        rows.append(({"paragraph": index, "segment": index}, path))
    wav, mp3 = root / "voice-preview.wav", root / "voice-preview.mp3"
    info = assemble_wav(rows, wav)
    encode_mp3(wav, mp3)
    return {"order": order, "seconds": info["wav"]["duration_seconds"], "wav": str(wav), "mp3": str(mp3)}


def render(
    plan: dict[str, Any], root: Path, engine: Engine, retry_failed: bool = False,
    limit: int | None = None, assemble: bool = True,
) -> dict[str, Any]:
    """Synthesize every missing chunk (at most `limit` new calls), then assemble if all exist."""
    check_inventory(root, "design", plan["designs"])
    check_inventory(root, "chapter", plan["chunks"])
    refs = load_references(plan, root, engine)
    specs = [
        request_spec(plan, engine, item, "chapter", hashlib.sha256(refs[item["speaker"]]).hexdigest())
        for item in plan["chunks"]
    ]
    for spec in specs:
        if check_cache(root, spec) is None:
            check_previous_attempts(root, spec, retry_failed)
    chunks, hashes, new_calls = [], [], 0
    for spec in specs:
        cached = check_cache(root, spec)
        if cached is None:
            if limit is not None and new_calls >= limit:
                break
            new_calls += 1
        metadata = generate_request(root, engine, spec, refs[spec["item"]["speaker"]], retry_failed)
        path, _ = cache_paths(root, "chapter", spec["item"]["id"])
        chunks.append((spec["item"], path))
        hashes.append({"request_fingerprint": digest(spec), "wav_sha256": metadata["wav"]["sha256"]})
    if len(chunks) < len(specs) or not assemble:
        return {"status": "partial" if len(chunks) < len(specs) else "chunks-complete",
                "chunks_done": len(chunks), "chunks_total": len(specs), "new_calls": new_calls}
    assembly_spec = {
        "chunks": hashes, "plan_sha256": plan["plan_sha256"], "turn_pause_ms": TURN_PAUSE_MS,
        "paragraph_pause_ms": PARAGRAPH_PAUSE_MS, "fade_ms": FADE_MS,
        "mastering": {**LOUDNESS, "mp3_kbps": MP3_KBPS, "two_pass": True},
    }
    assembly_path = root / "assembly.json"
    raw, mastered, mp3 = (root / name for name in ("chapter.raw.wav", "chapter.wav", "chapter.mp3"))
    if assembly_path.exists():
        saved = read_json(assembly_path)
        if saved["fingerprint"] != digest(assembly_spec):
            raise ChapterError("Stale chapter assembly fingerprint")
        if wav_metadata(raw) != saved["raw"]["wav"] or wav_metadata(mastered) != saved["mastered_wav"]:
            raise ChapterError("Corrupted chapter WAV export")
        if file_hash(mp3) != saved["mp3"]["sha256"] or mp3.stat().st_size != saved["mp3"]["bytes"]:
            raise ChapterError("Corrupted chapter MP3 export")
        return {**saved, "status": "assembled", "new_calls": new_calls}
    raw_info = assemble_wav(chunks, raw)
    master_audio(raw, mastered, mp3, raw_info["wav"]["sample_rate"])
    result = {
        "fingerprint": digest(assembly_spec), "spec": assembly_spec, "raw": raw_info,
        "mastered_wav": wav_metadata(mastered),
        "mp3": {"bytes": mp3.stat().st_size, "sha256": file_hash(mp3), "bitrate_kbps": MP3_KBPS},
        "timestamp_utc": utc_now(),
    }
    write_json(assembly_path, result)
    return {**result, "status": "assembled", "new_calls": new_calls}


# ------------------------------------------------------------ status / report


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "requests": len(records),
        "successful_calls": sum(r["status"] == "success" for r in records),
        "failed_calls": sum(r["status"] == "failure" for r in records),
        "unfinished_calls": sum(r["status"] == "started" for r in records),
        "input_text_tokens": sum(r["input_text_tokens"] or 0 for r in records),
        "wall_seconds": sum(r["wall_seconds"] or 0 for r in records),
        "successful_audio_seconds": sum(r["wav"]["duration_seconds"] for r in records if r["status"] == "success"),
        "wall_time_complete": all(r["wall_seconds"] is not None for r in records),
    }


def status(plan: dict[str, Any], root: Path) -> dict[str, Any]:
    chunks_dir = root / "chunks"
    done = {p.stem for p in chunks_dir.glob("*.wav")} if chunks_dir.is_dir() else set()
    ids = [c["id"] for c in plan["chunks"]]
    next_id = next((i for i in ids if i not in done), None)
    records = request_records(root)
    return {
        "chunks_done": sum(i in done for i in ids), "chunks_total": len(ids), "next_chunk": next_id,
        "designs_done": sum((root / "refs" / f"{d['id']}.wav").is_file() for d in plan["designs"]),
        "designs_total": len(plan["designs"]),
        "unfinished_requests": [r["item_id"] for r in records if r["status"] == "started"],
        "failed_requests": [r["item_id"] for r in records if r["status"] == "failure"],
        "assembled": (root / "chapter.mp3").is_file(),
    }


def llm_metrics(snapshot: Any = None) -> dict[str, Any]:
    if snapshot is None:
        return {"input_tokens": None, "output_tokens": None, "total_tokens": None, "cost_usd": None,
                "reason": "No actual LLM usage snapshot supplied; TTS text tokens are not LLM usage and nothing is estimated."}
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("totals"), dict):
        raise ChapterError("LLM usage snapshot must be the usage.py capture format (has `totals`)")
    if not isinstance(snapshot.get("source"), str) or not snapshot["source"].strip():
        raise ChapterError("LLM usage snapshot requires an actual usage source")
    totals = snapshot["totals"]
    for key in ("input_tokens", "output_tokens", "reasoning_tokens", "cache_read_tokens", "cache_write_tokens",
                "reported_total_tokens", "messages_missing_usage"):
        if type(totals.get(key)) is not int or totals[key] < 0:
            raise ChapterError(f"LLM snapshot totals.{key} must be a nonnegative integer")
    complete = totals["messages_missing_usage"] == 0
    pick = lambda key: totals[key] if complete else None  # noqa: E731
    return {
        "input_tokens": pick("input_tokens"), "output_tokens": pick("output_tokens"),
        "reasoning_tokens": pick("reasoning_tokens"), "cache_read_tokens": pick("cache_read_tokens"),
        "cache_write_tokens": pick("cache_write_tokens"), "total_tokens": pick("reported_total_tokens"),
        "cost_usd": snapshot.get("actual_llm_charge_usd"), "source": snapshot["source"], "snapshot": snapshot,
        "reason": "Supplied cumulative snapshot; reported cost is not proof of a paid charge.",
    }


def report(root: Path, snapshot: Any = None) -> dict[str, Any]:
    if (root / "llm-usage.json").is_file() and snapshot is None:
        snapshot = read_json(root / "llm-usage.json")
    llm = llm_metrics(snapshot)
    records = request_records(root)
    result: dict[str, Any] = {
        "timestamp_utc": utc_now(), "token_label": TOKEN_LABEL, "totals": summarize(records),
        "by_phase": {p: summarize([r for r in records if r["phase"] == p]) for p in ("design", "chapter")},
        "failed_calls": summarize([r for r in records if r["status"] == "failure"]),
        "by_speaker": {
            s: {"totals": summarize([r for r in records if r["speaker"] == s]),
                **{p: summarize([r for r in records if r["speaker"] == s and r["phase"] == p]) for p in ("design", "chapter")}}
            for s in sorted({r["speaker"] for r in records})
        },
        "costs": {
            "observed_paid_provider_charge_usd": 0,
            "basis": "Only the self-hosted VoxCPM2 sidecar is invoked; engine!=voxcpm is a hard failure, so no paid fallback.",
            "energy_usd": None, "tools_usd": None, "llm_usd": llm["cost_usd"],
            "exclusions": "Energy, tools, and LLM costs are excluded from the observed synthesis provider charge.",
        },
        "llm_metrics": llm,
        "assembly": read_json(root / "assembly.json") if (root / "assembly.json").is_file() else None,
    }
    if (root / "prepared.json").is_file():
        plan = read_json(root / "prepared.json")
        result.update(title=plan["manifest"]["title"], chapter=plan["manifest"]["chapter"],
                      planned_input_text_tokens=plan["planned_input_text_tokens"], planned_chunks=len(plan["chunks"]))
    if snapshot is not None:
        write_json(root / "llm-usage.json", snapshot)
    write_json(root / "metrics.json", result)
    return result


@contextmanager
def output_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ChapterError("Another chapter command owns this output directory") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def sync_book(book_dir: Path | None, chapter: int | None, output: Path) -> None:
    """Best-effort: mirror disk state into book.json. Never masks the real result."""
    if book_dir is None:
        return
    try:
        import book as bookmod

        bookmod.import_render(book_dir, chapter if chapter is not None else 0, output)
    except Exception as exc:  # noqa: BLE001
        print(f"book.json sync skipped: {type(exc).__name__}: {exc}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "voices", "preview", "render", "redo", "status", "report"):
        command = sub.add_parser(name)
        command.add_argument("--manifest", type=Path, default=Path("chapter.json"))
        command.add_argument("--output", type=Path, required=True, help="per-chapter audio directory")
        command.add_argument("--engine-url", help=f"default {DEFAULT_ENGINE_URL} (env VOXCPM_ENGINE_URL)")
        command.add_argument("--via-container", help="container to run curl in (env VOX_CORE_CONTAINER, default vox; '' = host)")
        command.add_argument("--engine-container", help="container with the voxcpm venv, for exact token counts")
        command.add_argument("--tokenizer", choices=("voxcpm-docker", "none"), default="voxcpm-docker")
        command.add_argument("--book", type=Path, help="book dir: mirror voices/artifacts/progress into book.json")
        command.add_argument("--book-chapter", type=int, help="chapter number for --book (default: manifest chapter)")
        if name in ("voices", "render"):
            command.add_argument("--retry-failed", action="store_true",
                                 help="authorize a new attempt only after confirming the engine is idle")
        if name == "render":
            command.add_argument("--limit", type=int, help="synthesize at most N new chunks, then stop (audition/partial)")
            command.add_argument("--no-assemble", action="store_true")
        if name == "redo":
            command.add_argument("--chunk", action="append", required=True, help="chunk id to re-roll (repeatable)")
            command.add_argument("--reason", required=True)
        if name == "report":
            command.add_argument("--llm-usage-snapshot", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = Engine(args.engine_url, args.via_container, args.engine_container, args.tokenizer)
    chapter = args.book_chapter
    try:
        with output_lock(args.output):
            if chapter is None and args.book:
                chapter = validate_manifest(read_json(args.manifest))["chapter"]
                chapter = chapter if isinstance(chapter, int) else None
            if args.command == "prepare":
                plan = prepare(args.manifest, args.output, engine)
                result = {"chunks": len(plan["chunks"]), "voices_to_design": len(plan["designs"]),
                          "voices_pinned": sorted(plan["pinned"]),
                          "planned_input_text_tokens": plan["planned_input_text_tokens"],
                          "model_revision": plan["model_revision"], "token_label": TOKEN_LABEL}
                sync_book(args.book, chapter, args.output)
            elif args.command == "report":
                snapshot = read_json(args.llm_usage_snapshot) if args.llm_usage_snapshot else None
                result = report(args.output, snapshot)
            else:
                plan = load_plan(args.manifest, args.output, engine)
                if args.command == "status":
                    result = status(plan, args.output)
                elif args.command == "preview":
                    result = preview(plan, args.output, engine)
                elif args.command == "redo":
                    result = redo(plan, args.output, args.chunk, args.reason)
                else:
                    try:
                        if args.command == "voices":
                            result = {
                                speaker: {"path": f"refs/{speaker}.wav", **{k: meta["wav"][k] for k in ("duration_seconds", "sample_rate", "sha256")}}
                                for speaker, meta in voices(plan, args.output, engine, args.retry_failed).items()
                            }
                        else:
                            result = render(plan, args.output, engine, args.retry_failed, args.limit, not args.no_assemble)
                    except BaseException:
                        try:
                            report(args.output)
                        except Exception as report_error:  # noqa: BLE001
                            print(f"Metrics update failed: {report_error}", file=sys.stderr)
                        sync_book(args.book, chapter, args.output)
                        raise
                    report(args.output)
                    sync_book(args.book, chapter, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ChapterError, OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
