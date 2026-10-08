#!/usr/bin/env python3
"""Create one book voice with VoxCPM2 voice design, no chapter needed: design takes, audition, freeze one.

    design_voice.py design --book B --id o_lan \\
        --description "Twenty-year-old woman, grounded plain restrained middle-low register." \\
        --reference-text "The morning light falls across the room, and a gentle breeze moves the curtains beside the open window." \\
        [--takes 3] [--cfg 2.0] [--steps 12] [--retry-failed]
    design_voice.py list   --book B --id o_lan [--samples-out takes.samples.json]
    design_voice.py freeze --book B --id o_lan --take 2 --character "O-lan" [--chapter 1] [--replace]

Takes land in <book>/voices/takes/<id>/refs/take-NN.wav (+ .json receipt), and every synth call is
appended to <book>/voices/takes/<id>/requests.jsonl (started -> success|failure). This reuses
render_chapter.py's request path, so the same guarantees hold: the VoxCPM sidecar is called directly,
a response from any other engine is a hard failure, a failed/unfinished call blocks until you confirm
the engine is idle and pass --retry-failed, and a take is only trusted when fingerprint, WAV and
success receipt agree. `freeze` copies the chosen take to <book>/voices/<id>.wav and registers it in
book.json (mode designed); `prepare_chapter.py build --book` then pins it in every chapter.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import book as bookmod
import render_chapter as rc
from abk_common import AbkError, read_json, safe_id, write_json
from prepare_chapter import validate_voice_design

TAKE = re.compile(r"take-(\d{2,})")
PROMPT = re.compile(r"\((?P<description>[^()]*)\)(?P<reference_text>.*)", re.DOTALL)


def voice_root(book: Path, voice_id: str) -> Path:
    return book / "voices" / "takes" / safe_id(voice_id, "voice id")


def take_id(number: int) -> str:
    return f"take-{number:02d}"


def pseudo_plan(settings: dict[str, Any]) -> dict[str, Any]:
    """The slice of a render plan that render_chapter.request_spec reads."""
    return {"manifest": {"settings": settings}, "model_revision": "unversioned"}


def known_takes(root: Path) -> tuple[set[int], list[int]]:
    """(every take number in use, numbers whose last call failed or never finished and left no WAV)."""
    numbers = {int(m.group(1)) for p in (root / "refs").glob("take-*.wav") if (m := TAKE.fullmatch(p.stem))}
    last: dict[str, str] = {}
    for record in rc.request_records(root):  # a failed take keeps its number until it is retried
        if TAKE.fullmatch(record["item_id"]):
            last[record["item_id"]] = record["status"]
    numbers |= {int(TAKE.fullmatch(item).group(1)) for item in last}
    pending = sorted(int(TAKE.fullmatch(item).group(1)) for item, status in last.items()
                     if status != "success" and not (root / "refs" / f"{item}.wav").is_file())
    return numbers, pending


def settings_for(book: Path, cfg: float | None, steps: int | None) -> dict[str, Any]:
    defaults = bookmod.load(book).get("engine", {}).get("settings", {})
    cfg = float(cfg if cfg is not None else defaults.get("cfg", 2.0))
    steps = steps if steps is not None else defaults.get("steps", 12)
    if not 1 <= cfg <= 5 or type(steps) is not int or not 1 <= steps <= 50:  # the sidecar's own bounds
        raise AbkError("cfg must be 1-5 and steps an integer 1-50")
    return {"cfg": cfg, "steps": steps}


def design(
    book: Path, voice_id: str, description: str, reference_text: str, engine: rc.Engine, *,
    takes: int = 1, cfg: float | None = None, steps: int | None = None, retry_failed: bool = False,
) -> list[dict[str, Any]]:
    validate_voice_design(voice_id, {"description": description, "reference_text": reference_text})
    if not 1 <= takes <= 5:
        raise AbkError("--takes must be 1-5 (each take is one GPU call of a few seconds)")
    settings = settings_for(book, cfg, steps)
    root = voice_root(book, voice_id)
    root.mkdir(parents=True, exist_ok=True)
    plan = pseudo_plan(settings)
    prompt = f"({rc.normalized(description)}){rc.normalized(reference_text)}"
    results = []
    existing, pending = known_takes(root)
    # Retry an unfinished/failed take under its own number first (blocked without --retry-failed).
    numbers = (pending + [max(existing | {0}) + 1 + i for i in range(takes)])[:takes]
    for number in numbers:
        item = {"id": take_id(number), "speaker": voice_id, "text": prompt,
                "input_text_tokens": None, "characters": len(prompt)}
        spec = rc.request_spec(plan, engine, item, "design", None)
        if number in pending:
            previous = [r for r in rc.request_records(root) if r["item_id"] == item["id"]][-1]
            if previous["request_fingerprint"] != rc.digest(spec):
                raise AbkError(f"{item['id']} failed with a different prompt/settings; rerun with the same "
                               "description, reference text and settings, or delete its ledger lines deliberately")
        metadata = rc.generate_request(root, engine, spec, retry_failed=retry_failed)
        results.append({"take": number, "path": str(root / "refs" / f"{item['id']}.wav"),
                        **{k: metadata["wav"][k] for k in ("duration_seconds", "sample_rate", "sha256")}})
    return results


def list_takes(book: Path, voice_id: str) -> dict[str, Any]:
    root = voice_root(book, voice_id)
    rows = []
    for path in sorted((root / "refs").glob("take-*.wav")):
        metadata = read_json(path.with_suffix(".json"))
        prompt = PROMPT.fullmatch(metadata["request"]["item"]["text"])
        rows.append({
            "take": int(TAKE.fullmatch(path.stem).group(1)), "path": str(path),
            "duration_seconds": metadata["wav"]["duration_seconds"], "sha256": metadata["wav"]["sha256"],
            "description": prompt["description"] if prompt else None,
            "reference_text": prompt["reference_text"] if prompt else None,
            "settings": metadata["request"]["settings"],
        })
    records = rc.request_records(root) if root.is_dir() else []
    return {"voice": voice_id, "takes": rows,
            "unfinished_or_failed": [r["item_id"] for r in records if r["status"] != "success"
                                     and not (root / "refs" / f"{r['item_id']}.wav").is_file()]}


def freeze(
    book: Path, voice_id: str, take: int, character: str, *, chapter: int | None = None, replace: bool = False,
) -> dict[str, Any]:
    root = voice_root(book, voice_id)
    wav_path, metadata_path = rc.cache_paths(root, "design", take_id(take))
    if not metadata_path.is_file():
        raise AbkError(f"No take {take} for {voice_id} under {root / 'refs'}")
    metadata = rc.check_cache(root, read_json(metadata_path)["request"])  # fingerprint + WAV + success receipt
    prompt = PROMPT.fullmatch(metadata["request"]["item"]["text"])
    if prompt is None:
        raise AbkError(f"{metadata_path} is not a voice-design take")
    with bookmod.locked(book) as data:
        if voice_id in data["voices"] and not replace:
            raise AbkError(f"Voice {voice_id!r} is already in book.json; pass --replace to supersede it deliberately "
                           "(every later chapter will sound different)")
    target = book / "voices" / f"{voice_id}.wav"
    shutil.copyfile(wav_path, target)
    return bookmod.add_voice(
        book, voice_id, "designed", character, description=prompt["description"],
        reference_text=prompt["reference_text"], reference_audio=target, chapter=chapter,
        notes=f"design take {take}; receipts in {bookmod.rel(book, root)}", replace=replace,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("design", "list", "freeze"):
        command = sub.add_parser(name)
        command.add_argument("--book", type=Path, required=True)
        command.add_argument("--id", required=True, help="voice id (letters, digits, _ -); names files")
        if name == "design":
            command.add_argument("--description", required=True, help="under 20 words, no parentheses")
            command.add_argument("--reference-text", required=True, help="15-20 neutral words, never chapter content")
            command.add_argument("--takes", type=int, default=1)
            command.add_argument("--cfg", type=float)
            command.add_argument("--steps", type=int)
            command.add_argument("--retry-failed", action="store_true",
                                 help="authorize a new attempt only after confirming the engine is idle")
            command.add_argument("--engine-url", help=f"default {rc.DEFAULT_ENGINE_URL} (env VOXCPM_ENGINE_URL)")
            command.add_argument("--via-container", help="container to run curl in (env VOX_CORE_CONTAINER, default vox; '' = host)")
        if name == "list":
            command.add_argument("--samples-out", type=Path, help="write a verify_audio.py --samples file for the takes")
        if name == "freeze":
            command.add_argument("--take", type=int, required=True)
            command.add_argument("--character", required=True)
            command.add_argument("--chapter", type=int)
            command.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "design":
            engine = rc.Engine(args.engine_url, args.via_container, tokenizer="none")
            root = voice_root(args.book, args.id)
            root.mkdir(parents=True, exist_ok=True)
            with rc.output_lock(root):
                result: Any = design(args.book, args.id, args.description, args.reference_text, engine,
                                     takes=args.takes, cfg=args.cfg, steps=args.steps, retry_failed=args.retry_failed)
        elif args.command == "list":
            result = list_takes(args.book, args.id)
            if args.samples_out:
                write_json(args.samples_out, [
                    {"path": row["path"], "expected": row["reference_text"], "speaker": args.id, "kind": "ref"}
                    for row in result["takes"]
                ])
                result["samples_out"] = str(args.samples_out)
        else:
            result = freeze(args.book, args.id, args.take, args.character, chapter=args.chapter, replace=args.replace)
    except (AbkError, OSError, KeyError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
