#!/usr/bin/env python3
"""Book manifest CLI: the durable memory of one audiobook project.

    book.py init --dir D --title T [--author A] [--source PATH]
    book.py voice add ID --mode designed|selected|cloned ...
    book.py voice list
    book.py chapter set N [--title T] [--status S] [--manifest P] [--output P]
    book.py progress set --chapter N --stage S [--chunk-id ID --chunks-done K --chunks-total T --char-offset O]
    book.py progress show
    book.py artifact add --kind K --path P [--chapter N] [--status partial|complete]
    book.py artifact verify
    book.py import-render --chapter N --output AUDIO_DIR
    book.py resume
    book.py show [--json]

All paths stored in book.json are relative to the book directory so the whole
directory can be moved. Writes are atomic and serialised with flock.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from abk_common import AbkError, atomic_write, file_hash, read_json, safe_id, utc_now, wav_metadata

SCHEMA = "ebook-to-audiobook/book/1"
VOICE_MODES = ("designed", "selected", "cloned")
STAGES = ("new", "researched", "prepared", "voices", "rendering", "assembled", "qa", "done")
ARTIFACT_STATUS = ("partial", "complete", "stale")
LAYOUT = (
    "source", "source/pages", "research", "voices", "chapters", "usage",
)


# ---------------------------------------------------------------- persistence


def book_file(directory: Path) -> Path:
    return directory / "book.json"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    if not slug:
        raise AbkError("Cannot derive a slug; pass --slug")
    return slug


def load(directory: Path) -> dict[str, Any]:
    path = book_file(directory)
    if not path.is_file():
        raise AbkError(f"No book.json in {directory}; run `book.py init` first")
    data = read_json(path)
    if data.get("schema") != SCHEMA:
        raise AbkError(f"Unsupported book.json schema: {data.get('schema')!r}")
    return data


def save(directory: Path, data: dict[str, Any]) -> None:
    data["updated_utc"] = utc_now()
    atomic_write(
        book_file(directory),
        (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode(),
    )


@contextmanager
def locked(directory: Path) -> Iterator[dict[str, Any]]:
    """Read-modify-write book.json under an exclusive lock; saves on clean exit."""
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".book.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            data = load(directory)
            yield data
            save(directory, data)
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def rel(directory: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(directory.resolve()))
    except ValueError:
        return str(resolved)


def absolute(directory: Path, stored: str) -> Path:
    path = Path(stored)
    return path if path.is_absolute() else directory / path


def chapter_dir(directory: Path, chapter: int) -> Path:
    return directory / "chapters" / f"{chapter:02d}"


# ------------------------------------------------------------------ operations


def init_book(
    directory: Path, title: str, author: str | None = None, slug: str | None = None,
    source: Path | None = None, language: str = "en", engine: str = "voxcpm2",
) -> dict[str, Any]:
    if book_file(directory).exists():
        raise AbkError(f"{book_file(directory)} already exists; refusing to overwrite")
    directory.mkdir(parents=True, exist_ok=True)
    for name in LAYOUT:
        (directory / name).mkdir(parents=True, exist_ok=True)
    source_info: dict[str, Any] = {"path": None, "kind": None, "sha256": None, "rights": None}
    if source is not None:
        if not source.is_file():
            raise AbkError(f"Source file does not exist: {source}")
        source_info.update({
            "path": rel(directory, source), "kind": source.suffix.lstrip(".").lower() or "unknown",
            "sha256": file_hash(source), "bytes": source.stat().st_size,
        })
    now = utc_now()
    data = {
        "schema": SCHEMA, "slug": slug or slugify(title), "title": title, "author": author,
        "language": language, "created_utc": now, "updated_utc": now,
        "source": source_info,
        "engine": {"name": engine, "settings": {"cfg": 2.0, "steps": 12}},
        "voices": {}, "chapters": {}, "artifacts": [], "usage": [],
        "progress": {"furthest": None, "current": None},
    }
    save(directory, data)
    return data


def add_voice(
    directory: Path, voice_id: str, mode: str, character: str, *, engine: str = "voxcpm2",
    description: str | None = None, reference_text: str | None = None,
    reference_audio: Path | None = None, voxxy_slug: str | None = None,
    chapter: int | None = None, notes: str | None = None, replace: bool = False,
) -> dict[str, Any]:
    safe_id(voice_id, "voice id")
    if mode not in VOICE_MODES:
        raise AbkError(f"mode must be one of {VOICE_MODES}")
    if mode == "designed" and (not description or not reference_text):
        raise AbkError("designed voices need --description and --reference-text (the design prompt)")
    if mode == "selected" and not (voxxy_slug or reference_audio):
        raise AbkError("selected voices need --voxxy-slug (an existing profile) or --reference-audio")
    if mode == "cloned" and reference_audio is None:
        raise AbkError("cloned voices need --reference-audio")
    if description and re.search(r"[()]", description):
        raise AbkError("description must not contain parentheses (the engine wraps it itself)")
    audio_info = None
    if reference_audio is not None:
        info = wav_metadata(reference_audio) if reference_audio.suffix.lower() == ".wav" else None
        target = reference_audio
        if not reference_audio.resolve().is_relative_to(directory.resolve()):
            target = directory / "voices" / f"{voice_id}{reference_audio.suffix.lower()}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(reference_audio, target)
        audio_info = {"path": rel(directory, target), "sha256": file_hash(target)}
        if info:
            audio_info.update(duration_seconds=info["duration_seconds"], sample_rate=info["sample_rate"])
    with locked(directory) as data:
        if voice_id in data["voices"] and not replace:
            raise AbkError(f"Voice {voice_id!r} exists; pass --replace to supersede it deliberately")
        previous = data["voices"].get(voice_id)
        chapters = sorted(set((previous or {}).get("chapters", []) + ([chapter] if chapter is not None else [])))
        data["voices"][voice_id] = {
            "character": character, "mode": mode, "engine": engine,
            "description": description, "reference_text": reference_text,
            "reference_audio": audio_info, "voxxy_slug": voxxy_slug,
            "chapters": chapters, "notes": notes,
            "added_utc": (previous or {}).get("added_utc", utc_now()), "updated_utc": utc_now(),
        }
        return data["voices"][voice_id]


def set_chapter(
    directory: Path, chapter: int, title: str | None = None, status: str | None = None,
    manifest: str | None = None, output: str | None = None, text: str | None = None,
) -> dict[str, Any]:
    if chapter < 0:
        raise AbkError("chapter must be >= 0 (0 = front matter)")
    with locked(directory) as data:
        row = data["chapters"].setdefault(str(chapter), {
            "title": None, "status": "new", "text": None, "manifest": None, "output": None,
        })
        for key, value in (("title", title), ("status", status), ("manifest", manifest),
                           ("output", output), ("text", text)):
            if value is not None:
                if key == "status" and value not in STAGES:
                    raise AbkError(f"status must be one of {STAGES}")
                row[key] = value
        row["updated_utc"] = utc_now()
        return row


def position(marker: dict[str, Any] | None) -> tuple[int, int, int, int]:
    """Order markers: chapter, then stage, then chunks done, then char offset."""
    if not marker:
        return (-1, -1, -1, -1)
    return (marker["chapter"], STAGES.index(marker["stage"]),
            marker.get("chunks_done") or 0, marker.get("char_offset") or 0)


def set_progress(
    directory: Path, chapter: int, stage: str, *, chunk_id: str | None = None,
    chunks_done: int | None = None, chunks_total: int | None = None,
    char_offset: int | None = None, note: str | None = None,
) -> dict[str, Any]:
    if stage not in STAGES:
        raise AbkError(f"stage must be one of {STAGES}")
    if chapter < 0:
        raise AbkError("chapter must be >= 0")
    if chunks_done is not None and chunks_total is not None and chunks_done > chunks_total:
        raise AbkError("chunks_done cannot exceed chunks_total")
    marker = {
        "chapter": chapter, "stage": stage, "chunk_id": chunk_id, "chunks_done": chunks_done,
        "chunks_total": chunks_total, "char_offset": char_offset, "note": note,
        "updated_utc": utc_now(),
    }
    with locked(directory) as data:
        progress = data["progress"]
        progress["current"] = marker
        # furthest = high-water mark; a re-render of an earlier chapter never drags it back.
        best = progress.get("furthest")
        stage_rank = STAGES.index(stage)
        if best is None or position(marker) > position(best):
            progress["furthest"] = marker
        chapter_row = data["chapters"].setdefault(str(chapter), {
            "title": None, "status": "new", "text": None, "manifest": None, "output": None,
        })
        if STAGES.index(chapter_row["status"]) < stage_rank:
            chapter_row["status"] = stage
        return progress


def sha_and_size(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": file_hash(path)}


def add_artifact(
    directory: Path, kind: str, path: Path, *, chapter: int | None = None,
    status: str = "complete", note: str | None = None,
) -> dict[str, Any]:
    if status not in ARTIFACT_STATUS:
        raise AbkError(f"status must be one of {ARTIFACT_STATUS}")
    target = path if path.is_absolute() else directory / path
    if not target.exists():
        raise AbkError(f"Artifact path does not exist: {target}")
    row: dict[str, Any] = {
        "kind": kind, "chapter": chapter, "path": rel(directory, target), "status": status,
        "note": note, "updated_utc": utc_now(),
    }
    if target.is_file():
        row.update(sha_and_size(target))
    else:  # directory artifact, e.g. a chunks/ cache: record a count, not a hash
        files = sorted(p for p in target.rglob("*") if p.is_file())
        row.update({"files": len(files), "bytes": sum(p.stat().st_size for p in files), "sha256": None})
    with locked(directory) as data:
        for index, existing in enumerate(data["artifacts"]):
            if existing["path"] == row["path"]:
                row["id"] = existing["id"]
                row["created_utc"] = existing.get("created_utc", row["updated_utc"])
                data["artifacts"][index] = row
                return row
        row["id"] = f"a{len(data['artifacts']) + 1:04d}"
        row["created_utc"] = row["updated_utc"]
        data["artifacts"].append(row)
        return row


def verify_artifacts(directory: Path, mark_stale: bool = True) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    with locked(directory) as data:
        for row in data["artifacts"]:
            target = absolute(directory, row["path"])
            issue = None
            if not target.exists():
                issue = "missing"
            elif target.is_file() and row.get("sha256") and file_hash(target) != row["sha256"]:
                issue = "checksum-mismatch"
            if issue:
                problems.append({"id": row["id"], "path": row["path"], "issue": issue})
                if mark_stale and row["status"] != "stale":
                    row["status"] = "stale"
                    row["note"] = f"{issue} at {utc_now()}"
    return problems


def import_render(directory: Path, chapter: int, output: Path) -> dict[str, Any]:
    """Register what render_chapter.py produced: designed voices + artifacts + progress."""
    prepared_path = output / "prepared.json"
    if not prepared_path.is_file():
        raise AbkError(f"{prepared_path} missing; run render_chapter.py prepare first")
    plan = read_json(prepared_path)
    manifest = plan["manifest"]
    summary: dict[str, Any] = {"voices": [], "artifacts": []}
    for item in plan["designs"]:
        ref = output / "refs" / f"{item['id']}.wav"
        if not ref.is_file():
            continue
        voice = manifest["voices"][item["id"]]
        with locked(directory) as data:
            already = item["id"] in data["voices"]
        if already:
            continue
        target = directory / "voices" / f"{item['id']}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ref, target)
        add_voice(
            directory, item["id"], "designed", voice.get("character") or item["id"],
            description=voice["description"], reference_text=voice["reference_text"],
            reference_audio=target, chapter=chapter,
        )
        summary["voices"].append(item["id"])
    with locked(directory) as data:  # pinned voices spoke in this chapter too
        for speaker in plan.get("pinned", {}):
            row = data["voices"].get(speaker)
            if row is not None and chapter not in row["chapters"]:
                row["chapters"] = sorted(row["chapters"] + [chapter])
    chunks_dir = output / "chunks"
    done = len(list(chunks_dir.glob("*.wav"))) if chunks_dir.is_dir() else 0
    total = len(plan["chunks"])
    final = output / "chapter.mp3"
    if chunks_dir.is_dir():
        add_artifact(directory, "chunk-cache", chunks_dir, chapter=chapter,
                     status="complete" if done == total else "partial")
        summary["artifacts"].append("chunk-cache")
    for kind, name in (("chapter-mp3", "chapter.mp3"), ("chapter-wav", "chapter.wav"),
                       ("requests-ledger", "requests.jsonl"), ("metrics", "metrics.json"),
                       ("assembly", "assembly.json")):
        if (output / name).is_file():
            add_artifact(directory, kind, output / name, chapter=chapter, status="complete")
            summary["artifacts"].append(kind)
    for qa in sorted(output.glob("qa-*.json")):
        add_artifact(directory, "asr-qa", qa, chapter=chapter, status="complete")
        summary["artifacts"].append(qa.name)
    stage = "assembled" if final.is_file() else ("rendering" if done else "voices")
    chars = 0
    for chunk in plan["chunks"][:done]:
        chars += len(chunk["text"]) + 1
    set_chapter(directory, chapter, manifest=None, output=rel(directory, output), status=stage)
    set_progress(
        directory, chapter, stage, chunk_id=plan["chunks"][done - 1]["id"] if done else None,
        chunks_done=done, chunks_total=total, char_offset=chars,
    )
    summary.update(stage=stage, chunks_done=done, chunks_total=total)
    return summary


def resume_hint(directory: Path) -> dict[str, Any]:
    data = load(directory)
    current = data["progress"].get("furthest")
    if current is None:
        return {"next": "Research the first chapter's cast, then run prepare_chapter.py", "marker": None}
    chapter, stage = current["chapter"], current["stage"]
    adir = f"chapters/{chapter:02d}"
    steps = {
        "new": f"research the cast of chapter {chapter} (references/character-research.md)",
        "researched": f"prepare_chapter.py --book {directory} --chapter {chapter} ...",
        "prepared": f"render_chapter.py prepare, then `voices`, in {adir}/audio",
        "voices": f"render_chapter.py render --output {adir}/audio",
        "rendering": f"render_chapter.py render --output {adir}/audio (cached chunks are skipped; add --retry-failed only if the engine is idle)",
        "assembled": f"verify_audio.py --root {adir}/audio, then record usage",
        "qa": f"record usage/accounting (optional), then book.py progress set --stage done",
        "done": f"start chapter {chapter + 1}",
    }
    return {"next": steps[stage], "marker": current}


# ------------------------------------------------------------------------ CLI


def render_show(data: dict[str, Any]) -> str:
    lines = [f"{data['title']} ({data['slug']})  schema={data['schema']}"]
    lines.append(f"engine: {data['engine']['name']}  settings: {json.dumps(data['engine']['settings'])}")
    furthest = data["progress"].get("furthest")
    if furthest:
        done = furthest.get("chunks_done")
        total = furthest.get("chunks_total")
        frac = f"  chunks {done}/{total}" if total else ""
        lines.append(f"furthest: chapter {furthest['chapter']} stage={furthest['stage']}{frac}")
    else:
        lines.append("furthest: (nothing yet)")
    lines.append(f"voices ({len(data['voices'])}):")
    for key, voice in sorted(data["voices"].items()):
        audio = voice["reference_audio"]["path"] if voice.get("reference_audio") else (voice.get("voxxy_slug") or "-")
        lines.append(f"  {key:<16} {voice['mode']:<9} {voice['character']}  [{audio}]")
    lines.append(f"chapters ({len(data['chapters'])}):")
    for key, row in sorted(data["chapters"].items(), key=lambda kv: int(kv[0])):
        lines.append(f"  {key:>3} {row['status']:<10} {row.get('title') or ''}")
    lines.append(f"artifacts ({len(data['artifacts'])}):")
    for row in data["artifacts"]:
        lines.append(f"  {row['id']} ch{row['chapter']} {row['kind']:<16} {row['status']:<8} {row['path']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=Path, default=Path("."), help="book directory (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--title", required=True)
    init.add_argument("--author")
    init.add_argument("--slug")
    init.add_argument("--source", type=Path, help="original ebook/pdf (hashed, not copied)")
    init.add_argument("--language", default="en")
    init.add_argument("--engine", default="voxcpm2")

    voice = sub.add_parser("voice").add_subparsers(dest="action", required=True)
    add = voice.add_parser("add")
    add.add_argument("id")
    add.add_argument("--mode", required=True, choices=VOICE_MODES)
    add.add_argument("--character", required=True)
    add.add_argument("--engine", default="voxcpm2")
    add.add_argument("--description")
    add.add_argument("--reference-text")
    add.add_argument("--reference-audio", type=Path)
    add.add_argument("--voxxy-slug")
    add.add_argument("--chapter", type=int)
    add.add_argument("--notes")
    add.add_argument("--replace", action="store_true")
    voice.add_parser("list")

    chapter = sub.add_parser("chapter").add_subparsers(dest="action", required=True)
    cset = chapter.add_parser("set")
    cset.add_argument("number", type=int)
    cset.add_argument("--title")
    cset.add_argument("--status", choices=STAGES)
    cset.add_argument("--manifest")
    cset.add_argument("--output")
    cset.add_argument("--text")

    progress = sub.add_parser("progress").add_subparsers(dest="action", required=True)
    pset = progress.add_parser("set")
    pset.add_argument("--chapter", type=int, required=True)
    pset.add_argument("--stage", required=True, choices=STAGES)
    pset.add_argument("--chunk-id")
    pset.add_argument("--chunks-done", type=int)
    pset.add_argument("--chunks-total", type=int)
    pset.add_argument("--char-offset", type=int)
    pset.add_argument("--note")
    progress.add_parser("show")

    artifact = sub.add_parser("artifact").add_subparsers(dest="action", required=True)
    aadd = artifact.add_parser("add")
    aadd.add_argument("--kind", required=True)
    aadd.add_argument("--path", type=Path, required=True)
    aadd.add_argument("--chapter", type=int)
    aadd.add_argument("--status", default="complete", choices=ARTIFACT_STATUS)
    aadd.add_argument("--note")
    averify = artifact.add_parser("verify")
    averify.add_argument("--no-mark", action="store_true", help="report only; do not mark stale")

    imp = sub.add_parser("import-render", help="register voices/artifacts/progress from a render output dir")
    imp.add_argument("--chapter", type=int, required=True)
    imp.add_argument("--output", type=Path, required=True)

    sub.add_parser("resume")
    show = sub.add_parser("show")
    show.add_argument("--json", action="store_true")
    return parser


def run(args: argparse.Namespace) -> Any:
    directory: Path = args.dir
    if args.command == "init":
        return init_book(directory, args.title, args.author, args.slug, args.source, args.language, args.engine)
    if args.command == "voice":
        if args.action == "list":
            return load(directory)["voices"]
        return add_voice(
            directory, args.id, args.mode, args.character, engine=args.engine,
            description=args.description, reference_text=args.reference_text,
            reference_audio=args.reference_audio, voxxy_slug=args.voxxy_slug,
            chapter=args.chapter, notes=args.notes, replace=args.replace,
        )
    if args.command == "chapter":
        return set_chapter(directory, args.number, args.title, args.status, args.manifest, args.output, args.text)
    if args.command == "progress":
        if args.action == "show":
            return load(directory)["progress"]
        return set_progress(
            directory, args.chapter, args.stage, chunk_id=args.chunk_id, chunks_done=args.chunks_done,
            chunks_total=args.chunks_total, char_offset=args.char_offset, note=args.note,
        )
    if args.command == "artifact":
        if args.action == "verify":
            return verify_artifacts(directory, mark_stale=not args.no_mark)
        return add_artifact(directory, args.kind, args.path, chapter=args.chapter, status=args.status, note=args.note)
    if args.command == "import-render":
        return import_render(directory, args.chapter, args.output)
    if args.command == "resume":
        return resume_hint(directory)
    return load(directory)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
    except (AbkError, OSError, KeyError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.command == "show" and not args.json:
        print(render_show(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "artifact" and args.action == "verify" and result:
        return 2  # problems found
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
