#!/usr/bin/env python3
"""Offline CPU Whisper spot-check of generated audio (diagnostic, not certification).

    verify_audio.py --root chapters/01/audio --manifest chapters/01/chapter.json \\
        --phase all --max-chunks 24 --out chapters/01/audio/qa-chunks.json

Samples reference clips (expected = their design reference_text) and evenly spaced chapter
chunks (expected = the chunk text recorded by render_chapter.py), transcribes them with a
local faster-whisper model on CPU, and reports sample-scoped word error rate. WER of ~1% on
24/296 chunks was normal; look at the worst_wer_samples and LISTEN to those. ASR happily
normalizes mispronunciations, so a low WER is evidence of "no skipped/repeated/garbled words",
not of good prosody.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Defaults describe the pilot host: a faster-whisper-large-v3-turbo snapshot cached inside the
# `transcription-worker-1` container, run on CPU (int8) so it never competes with the TTS GPU.
# Override per host with env vars or flags; nothing else in this file is host-specific.
DEFAULT_CONTAINER = os.environ.get("ABK_ASR_CONTAINER", "transcription-worker-1")
MODEL_ID = os.environ.get("ABK_ASR_MODEL_ID", "mobiuslabsgmbh/faster-whisper-large-v3-turbo")
MODEL_REVISION = os.environ.get("ABK_ASR_MODEL_REVISION", "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf")
MODEL_PATH = os.environ.get(
    "ABK_ASR_MODEL_PATH",
    f"/app/models/models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/snapshots/{MODEL_REVISION}",
)
ASR_CODE = f"MODEL_PATH = {MODEL_PATH!r}\nMODEL_REVISION = {MODEL_REVISION!r}\n" + r'''
import base64
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from faster_whisper import WhisperModel

records = [json.loads(line) for line in sys.stdin if line.strip()]
load_started = time.perf_counter()
model = None
load_error = None
try:
    for name in ("model.bin", "config.json", "tokenizer.json", "preprocessor_config.json"):
        if not (Path(MODEL_PATH) / name).is_file():
            raise ValueError("Missing cached model file: " + name)
    model = WhisperModel(
        MODEL_PATH, device="cpu", compute_type="int8",
        cpu_threads=2, num_workers=1, local_files_only=True
    )
except Exception as exc:
    load_error = f"{type(exc).__name__}: {exc}"
load_seconds = time.perf_counter() - load_started
failed = False
for record in records:
    started = time.perf_counter()
    result = {
        "path": record["path"], "model_revision": MODEL_REVISION,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "model_load_seconds": load_seconds
    }
    try:
        if model is None:
            raise RuntimeError(load_error)
        audio = io.BytesIO(base64.b64decode(record["wav_b64"], validate=True))
        segments, info = model.transcribe(
            audio, language="en", task="transcribe", beam_size=5,
            temperature=0.0, condition_on_previous_text=False,
            vad_filter=False, repetition_penalty=1.0, no_repeat_ngram_size=0,
            word_timestamps=True
        )
        rows = [{
            "start": s.start, "end": s.end, "text": s.text,
            "words": [{
                "word": w.word, "start": w.start, "end": w.end,
                "probability": w.probability
            } for w in (s.words or [])]
        } for s in segments]
        result.update({
            "status": "ok", "transcript": " ".join(s["text"].strip() for s in rows),
            "audio_seconds": info.duration, "segments": rows
        })
    except Exception as exc:
        failed = True
        result.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
    result["wall_seconds"] = time.perf_counter() - started
    print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
if failed:
    raise SystemExit(1)
'''


class VerificationError(ValueError):
    pass


@dataclass(frozen=True)
class Sample:
    path: Path
    expected: str
    speaker: str
    kind: str


def normalized_words(text: str) -> list[str]:
    return re.sub(r"[^\w\s]|_", "", text.casefold()).split()


def ratio(errors: int, words: int) -> float | None:
    return errors / words if words else (0.0 if errors == 0 else None)


def word_errors(expected: str, actual: str) -> dict[str, Any]:
    reference, hypothesis = normalized_words(expected), normalized_words(actual)
    costs = [list(range(len(hypothesis) + 1))]
    for i, word in enumerate(reference, 1):
        row = [i]
        for j, other in enumerate(hypothesis, 1):
            row.append(min(
                costs[i - 1][j] + 1, row[j - 1] + 1,
                costs[i - 1][j - 1] + (word != other),
            ))
        costs.append(row)
    i, j = len(reference), len(hypothesis)
    edits = []
    counts = {"substitutions": 0, "deletions": 0, "insertions": 0}
    while i or j:
        if i and j and reference[i - 1] == hypothesis[j - 1] and costs[i][j] == costs[i - 1][j - 1]:
            i, j = i - 1, j - 1
            continue
        if i and j and costs[i][j] == costs[i - 1][j - 1] + 1:
            operation, wanted, heard = "substitution", reference[i - 1], hypothesis[j - 1]
            i, j = i - 1, j - 1
        elif i and costs[i][j] == costs[i - 1][j] + 1:
            operation, wanted, heard = "deletion", reference[i - 1], None
            i -= 1
        else:
            operation, wanted, heard = "insertion", None, hypothesis[j - 1]
            j -= 1
        counts[operation + "s"] += 1
        edits.append({"operation": operation, "expected": wanted, "actual": heard})
    distance = costs[-1][-1]
    return {
        "wer": ratio(distance, len(reference)), "edit_distance": distance,
        "expected_words": len(reference), "actual_words": len(hypothesis),
        **counts, "edits": list(reversed(edits)),
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def spaced(items: list[Any], limit: int) -> list[Any]:
    if limit < 1:
        raise VerificationError("max-chunks must be positive")
    if len(items) <= limit:
        return list(items)
    if limit == 1:
        return [items[len(items) // 2]]
    return [items[round(i * (len(items) - 1) / (limit - 1))] for i in range(limit)]


def sample_from_object(row: Any, root: Path) -> Sample:
    if not isinstance(row, dict):
        raise VerificationError("Each sample must be an object")
    if not isinstance(row.get("path"), str) or not row["path"].strip():
        raise VerificationError("Sample path must be a nonempty string")
    if not isinstance(row.get("expected"), str):
        raise VerificationError("Sample expected must be a string, including for silence")
    if not isinstance(row.get("speaker"), str) or not row["speaker"].strip():
        raise VerificationError("Sample speaker must be a nonempty string")
    if row.get("kind") not in ("ref", "chunk"):
        raise VerificationError("Sample kind must be ref or chunk")
    path = (root / row["path"]).resolve()
    if path.suffix.lower() != ".wav":
        raise VerificationError(f"Sample must be a WAV: {path}")
    return Sample(path, row["expected"], row["speaker"], row["kind"])


def reference_samples(manifest_path: Path, root: Path) -> list[Sample]:
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise VerificationError("Manifest must be an object")
    voices = manifest.get("voices")
    if isinstance(voices, dict):
        entries = list(voices.items())
    elif isinstance(voices, list):
        if any(not isinstance(voice, dict) for voice in voices):
            raise VerificationError("Manifest voices entries must be objects")
        entries = [(voice.get("id"), voice) for voice in voices]
    else:
        raise VerificationError("Manifest voices must be a mapping or list of voice objects")
    if not entries:
        raise VerificationError("Manifest has no voices")
    result: list[Sample] = []
    for speaker, voice in entries:
        if not isinstance(speaker, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", speaker):
            raise VerificationError("Manifest voice IDs must be safe filenames")
        if not isinstance(voice, dict):
            raise VerificationError(f"Invalid manifest voice: {speaker}")
        if voice.get("reference_audio") and not voice.get("reference_text"):
            continue  # pinned voice reused from an earlier chapter: no design clip to check here
        if not (root / "refs" / f"{speaker}.wav").is_file():
            continue  # voice not designed in this chapter's output (unused or pinned)
        result.append(sample_from_object({
            "path": f"refs/{speaker}.wav", "expected": voice.get("reference_text"),
            "speaker": speaker, "kind": "ref",
        }, root))
    return result


def select_samples(
    manifest_path: Path, root: Path, phase: str, samples_path: Path | None, max_chunks: int,
) -> tuple[list[Sample], dict[str, Any]]:
    if phase not in ("refs", "chunks", "all"):
        raise VerificationError("phase must be refs, chunks, or all")
    if max_chunks < 1:
        raise VerificationError("max-chunks must be positive")
    refs, chunks = [], []
    if samples_path is not None:
        rows = read_json(samples_path)
        if not isinstance(rows, list):
            raise VerificationError("Samples file must be a JSON array")
        candidates = [sample_from_object(row, root) for row in rows]
        if len({sample.path for sample in candidates}) != len(candidates):
            raise VerificationError("Duplicate sample paths")
        refs = [sample for sample in candidates if sample.kind == "ref"]
        chunks = [sample for sample in candidates if sample.kind == "chunk"]
        chunk_count = len(chunks)
        chunks = spaced(chunks, max_chunks)
        source = "explicit_samples"
    else:
        if phase in ("refs", "all"):
            refs = reference_samples(manifest_path, root)
        paths = sorted((root / "chunks").glob("*.wav")) if phase in ("chunks", "all") else []
        chunk_count = len(paths)
        for path in spaced(paths, max_chunks):
            metadata_path = path.with_suffix(".json")
            if not metadata_path.is_file():
                raise VerificationError(f"Missing {metadata_path}; supply --samples")
            metadata = read_json(metadata_path)
            request = metadata.get("request") if isinstance(metadata, dict) else None
            item = request.get("item") if isinstance(request, dict) else None
            if not isinstance(item, dict):
                raise VerificationError(f"Expected request.item in {metadata_path}; supply --samples")
            chunks.append(sample_from_object({
                "path": str(path.resolve()), "expected": item.get("text"),
                "speaker": item.get("speaker"), "kind": "chunk",
            }, root))
        source = "manifest_references_and_renderer_metadata"
    selected = (refs if phase in ("refs", "all") else []) + (chunks if phase in ("chunks", "all") else [])
    if not selected:
        raise VerificationError("No samples selected; provide existing WAVs or --samples")
    if len({sample.path for sample in selected}) != len(selected):
        raise VerificationError("Duplicate selected paths")
    return selected, {
        "source": source, "phase": phase, "max_chunks": max_chunks,
        "available_refs": len(refs) if phase in ("refs", "all") else 0,
        "available_chunks": chunk_count if phase in ("chunks", "all") else 0,
        "selected_refs": sum(sample.kind == "ref" for sample in selected),
        "selected_chunks": sum(sample.kind == "chunk" for sample in selected),
    }


def wav_record(sample: Sample) -> tuple[dict[str, str], dict[str, Any]]:
    data = sample.path.read_bytes()
    with wave.open(io.BytesIO(data), "rb") as reader:
        frames, rate = reader.getnframes(), reader.getframerate()
        frame_size = reader.getnchannels() * reader.getsampwidth()
        if frames < 1 or rate < 1 or reader.getcomptype() != "NONE":
            raise VerificationError("WAV must contain nonempty uncompressed PCM")
        if len(reader.readframes(frames)) != frames * frame_size:
            raise VerificationError("WAV PCM data is truncated")
        audio = {
            "duration_seconds": frames / rate, "sample_rate": rate,
            "channels": reader.getnchannels(), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    return {"path": str(sample.path), "wav_b64": base64.b64encode(data).decode("ascii")}, audio


def docker_command(timeout: float) -> list[str]:
    deadline = timeout - min(5.0, timeout / 2)
    grace = min(2.0, timeout / 4)
    return [
        "docker", "exec", "-i",
        "-e", "CUDA_VISIBLE_DEVICES=", "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "HF_HUB_OFFLINE=1", "-e", "TRANSFORMERS_OFFLINE=1",
        "-e", "HF_HUB_DISABLE_TELEMETRY=1", "-e", "TOKENIZERS_PARALLELISM=false",
        "-e", "OMP_NUM_THREADS=2", "-e", "OPENBLAS_NUM_THREADS=1",
        DEFAULT_CONTAINER, "/usr/bin/timeout", "--signal=TERM",
        f"--kill-after={grace}s", f"{deadline}s", "/usr/bin/nice", "-n", "15",
        "/usr/bin/python3", "-B", "-u", "-c", ASR_CODE,
    ]


def parse_records(stdout: bytes, identifiers: set[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    results: dict[str, dict[str, Any]] = {}
    errors = []
    for number, line in enumerate(stdout.decode("utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                raise VerificationError("Response must be an object with a path")
            path = row["path"]
            if path not in identifiers:
                raise VerificationError("Unexpected response path")
            if path in results:
                results[path] = {"status": "error", "error": "Duplicate ASR response"}
                raise VerificationError("Duplicate ASR response")
            if row.get("model_revision") != MODEL_REVISION:
                raise VerificationError("Unexpected model revision")
            if row.get("status") not in ("ok", "error"):
                raise VerificationError("Unexpected ASR status")
            if row["status"] == "ok" and not isinstance(row.get("transcript"), str):
                raise VerificationError("Missing ASR transcript")
            if row["status"] == "error" and not isinstance(row.get("error"), str):
                raise VerificationError("Missing ASR error")
            for field in ("wall_seconds", "model_load_seconds"):
                value = row.get(field)
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise VerificationError(f"Invalid ASR {field}")
            results[path] = row
        except (ValueError, VerificationError) as exc:
            errors.append(f"Output line {number}: {exc}")
    return results, errors


def transcribe_records(records: list[dict[str, str]], timeout: float) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not math.isfinite(timeout) or timeout <= 0:
        raise VerificationError("timeout must be finite and positive")
    started = time.perf_counter()
    payload = b"".join(json.dumps(row).encode("utf-8") + b"\n" for row in records)
    timed_out = False
    failure = None
    stdout, stderr = b"", b""
    returncode = None
    if records:
        try:
            process = subprocess.Popen(
                docker_command(timeout), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            try:
                stdout, stderr = process.communicate(input=payload, timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                stdout, stderr = process.communicate()
            returncode = process.returncode
            timed_out = timed_out or returncode in (124, 137)
        except (OSError, subprocess.SubprocessError) as exc:
            failure = f"{type(exc).__name__}: {exc}"
    identifiers = {row["path"] for row in records}
    results, protocol_errors = parse_records(stdout, identifiers)
    for path in identifiers - results.keys():
        results[path] = {
            "status": "timeout" if timed_out else "error",
            "error": failure or ("Batch deadline exceeded" if timed_out else "No valid ASR response"),
        }
    return results, {
        "wall_seconds": time.perf_counter() - started, "timeout_seconds": timeout,
        "timed_out": timed_out, "returncode": returncode,
        "error": failure, "protocol_errors": protocol_errors,
        "stderr": stderr.decode("utf-8", errors="replace")[-8000:],
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [row for row in rows if row["status"] == "ok"]
    totals = {
        field: sum(row[field] for row in scored)
        for field in ("edit_distance", "substitutions", "deletions", "insertions", "expected_words")
    }
    ranked = sorted(
        (row for row in scored if row["wer"] is not None), key=lambda row: row["wer"], reverse=True,
    )
    return {
        "scope": "selected_samples_only_not_whole_chapter", "samples": len(rows),
        "transcribed": len(scored), "unscored": len(rows) - len(scored),
        "statuses": {status: sum(row["status"] == status for row in rows) for status in ("ok", "error", "timeout")},
        "expected_words_selected": sum(row["expected_words"] for row in rows),
        "expected_words_scored": totals.pop("expected_words"), **totals,
        "micro_wer": ratio(totals["edit_distance"], sum(row["expected_words"] for row in scored)) if scored else None,
        "undefined_wer_samples": [row["path"] for row in scored if row["wer"] is None],
        "worst_wer_samples": [{
            key: row[key] for key in ("path", "speaker", "kind", "wer", "substitutions", "deletions", "insertions")
        } for row in ranked[:5]],
        "failed_samples_excluded_from_micro_wer": True,
    }


def verify(samples: list[Sample], timeout: float, selection: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    records, rows = [], []
    for sample in samples:
        row = {
            "path": str(sample.path), "speaker": sample.speaker, "kind": sample.kind,
            "expected_transcript": sample.expected, "actual_transcript": None,
            "model_revision": MODEL_REVISION, "status": "error", "error": None,
            "expected_words": len(normalized_words(sample.expected)), "wer": None,
            "edit_distance": None, "substitutions": None, "deletions": None, "insertions": None,
            "started_utc": None, "wall_seconds": None,
        }
        try:
            record, audio = wav_record(sample)
            records.append(record)
            row["audio"] = audio
        except (OSError, ValueError, wave.Error, EOFError) as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    results, batch = transcribe_records(records, timeout)
    for row in rows:
        if row["path"] not in results:
            continue
        result = results[row["path"]]
        for field in ("status", "error", "started_utc", "wall_seconds", "model_load_seconds", "segments"):
            if field in result:
                row[field] = result[field]
        if result["status"] == "ok":
            row["actual_transcript"] = result["transcript"]
            row.update(word_errors(row["expected_transcript"], result["transcript"]))
    summary = summarize(rows)
    complete = (
        summary["unscored"] == 0 and not batch["timed_out"] and not batch["error"]
        and not batch["protocol_errors"] and batch["returncode"] == 0
    )
    return {
        "version": 1, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if complete else "incomplete", "scope": summary["scope"],
        "assessment": (
            "ASR diagnostic, not certification of pronunciation or chapter completeness. "
            "Archaic compounds and names can be recognized differently; ASR may normalize mispronunciation."
        ),
        "normalization": "Casefold; strip punctuation with regex; split whitespace; no spelling substitutions.",
        "wer_policy": "WER is unbounded. Empty expected and actual: 0; empty expected with insertions: null.",
        "model": {
            "id": MODEL_ID, "revision": MODEL_REVISION, "path": MODEL_PATH,
            "device": "cpu", "compute_type": "int8", "cpu_threads": 2, "num_workers": 1,
            "offline": True, "reference_text_prompted": False,
        },
        "wall_seconds": time.perf_counter() - started, "selection": selection,
        "batch": batch, "summary": summary, "samples": rows,
    }


def validate_output(path: Path, samples: list[Sample], manifest: Path, samples_path: Path | None, root: Path) -> None:
    protected = {manifest.resolve(), Path(__file__).resolve()}
    if samples_path is not None:
        protected.add(samples_path.resolve())
    for sample in samples:
        protected.update((sample.path.resolve(), sample.path.with_suffix(".json").resolve()))
    protected.update((root / name).resolve() for name in (
        "plan.json", "prepared.json", "assembly.json", "metrics.json", "requests.jsonl",
    ))
    output = path.resolve()
    in_audio_directory = any(output.is_relative_to((root / name).resolve()) for name in ("refs", "chunks"))
    if output in protected or path.suffix.lower() != ".json" or in_audio_directory:
        raise VerificationError("Output must be a JSON report, not a source, manifest, sample, or renderer metadata file")
    if not path.parent.is_dir():
        raise VerificationError(f"Output parent directory must already exist: {path.parent}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sample-scoped offline CPU Whisper audiobook diagnostic")
    parser.add_argument("--manifest", type=Path, default=Path("chapter.json"))
    parser.add_argument("--root", type=Path, required=True, help="per-chapter audio dir (refs/, chunks/)")
    parser.add_argument("--phase", choices=("refs", "chunks", "all"), default="all")
    parser.add_argument("--samples", type=Path, help="JSON array of path, expected, speaker, kind; relative paths use --root")
    parser.add_argument("--out", type=Path, help="JSON report path (default: <root>/qa-<phase>.json)")
    parser.add_argument("--max-chunks", type=int, default=12)
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args(argv)
    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise VerificationError("timeout must be finite and positive")
        samples, selection = select_samples(args.manifest, args.root, args.phase, args.samples, args.max_chunks)
        args.out = args.out or args.root / f"qa-{args.phase}.json"
        validate_output(args.out, samples, args.manifest, args.samples, args.root)
        report = verify(samples, args.timeout, selection)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"out": str(args.out), "status": report["status"], "summary": report["summary"]}, ensure_ascii=False))
        return 0 if report["status"] == "complete" else 1
    except (OSError, ValueError, wave.Error, EOFError, subprocess.SubprocessError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
