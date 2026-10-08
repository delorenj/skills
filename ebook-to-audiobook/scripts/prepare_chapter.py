#!/usr/bin/env python3
"""Turn page text into a speaker-attributed chapter manifest (chapter.json).

Three steps, each verifiable on its own:

  text    page-NNN.txt files  ->  chapter.txt   (paragraphs separated by blank lines)
  quotes  chapter.txt         ->  numbered list of quoted spans, for speaker attribution
  build   chapter.txt + speakers.json -> chapter.json (what render_chapter.py consumes)

`build` refuses unless every quoted span has a reviewed speaker and the segments
reconstruct the chapter text exactly (minus dialogue delimiters and whitespace).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from abk_common import AbkError, normalized, read_json, safe_id, write_json

DEFAULT_QUOTE = r"“([^“”]*)”"
OPEN_CLOSE = ("“", "”")
SENTENCE_END = ".!?”\"’:"


def words(text: str) -> int:
    return len(text.split())


# ------------------------------------------------------------------- text step


def page_files(pages_dir: Path, first: int, last: int) -> list[tuple[int, Path]]:
    rows = []
    for number in range(first, last + 1):
        path = pages_dir / f"page-{number:03d}.txt"
        if not path.is_file():
            raise AbkError(f"Missing page text: {path}")
        rows.append((number, path))
    return rows


def assemble_text(
    pages_dir: Path, first: int, last: int, *, start_marker: str | None = None,
    end_marker: str | None = None, strip_folio: bool = False,
    join_previous: set[int] | None = None, auto_join: bool = False,
    corrections: list[dict[str, Any]] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Return (paragraphs, report). Corrections must each match or the build is refused."""
    join_previous = join_previous or set()
    by_page: dict[int, list[dict[str, Any]]] = {}
    for item in corrections or []:
        by_page.setdefault(int(item["page"]), []).append(item)
    paragraphs: list[str] = []
    report: dict[str, Any] = {"corrections_applied": [], "joined_pages": [], "wrap_repairs": 0,
                              "end_marker_found": None if end_marker is None else False}
    for number, path in page_files(pages_dir, first, last):
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            raise AbkError(f"Empty page text: {path}")
        if strip_folio:
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if number == first and start_marker:
            index = text.find(start_marker)
            if index < 0:
                raise AbkError(f"start marker {start_marker!r} not found on page {number}")
            text = text[index + len(start_marker):].strip()
        ended = bool(end_marker) and end_marker in text  # checked on every page: --last may overshoot the chapter
        if ended:
            text = text.split(end_marker, 1)[0].strip()
            report["end_marker_found"] = number
            if not text:  # chapter ended exactly at the previous page boundary
                break
        for item in by_page.get(number, []):
            count = text.count(item["before"])
            if count == 0:
                raise AbkError(f"Reviewed correction no longer matches on page {number}: {item['before']!r}")
            text = text.replace(item["before"], item["after"])
            report["corrections_applied"].append({"page": number, "before": item["before"], "after": item["after"], "count": count})
        text, wraps = re.subn(r"([A-Za-z]+)-\n([a-z]+)", r"\1\2", text)  # soft-hyphen line wraps
        report["wrap_repairs"] += wraps
        text = re.sub(r"(?<=—)\n(?=\S)|(?<=\S)\n(?=—)", "", text)
        blocks = [normalized(block) for block in re.split(r"\n\s*\n", text) if block.strip()]
        if not blocks:
            raise AbkError(f"No chapter text on page {number}")
        joinable = number in join_previous or (
            auto_join and paragraphs and paragraphs[-1][-1] not in SENTENCE_END
        )
        if joinable and paragraphs and number != first:
            paragraphs[-1] += " " + blocks.pop(0)
            report["joined_pages"].append(number)
        paragraphs.extend(blocks)
        if ended:
            break
    if not paragraphs:
        raise AbkError("No paragraphs produced")
    return paragraphs, report


# ----------------------------------------------------------------- quotes step


def quote_spans(paragraphs: list[str], pattern: str = DEFAULT_QUOTE) -> list[dict[str, Any]]:
    rx = re.compile(pattern)
    spans = []
    for number, paragraph in enumerate(paragraphs, 1):
        for match in rx.finditer(paragraph):
            spans.append({
                "index": len(spans) + 1, "paragraph": number, "text": match.group(1),
                "before": paragraph[max(0, match.start() - 80):match.start()],
                "after": paragraph[match.end():match.end() + 80],
            })
    return spans


def check_delimiters(paragraphs: list[str], spans: list[dict[str, Any]], pattern: str) -> None:
    chapter = "\n\n".join(paragraphs)
    if pattern == DEFAULT_QUOTE and not (chapter.count(OPEN_CLOSE[0]) == chapter.count(OPEN_CLOSE[1]) == len(spans)):
        raise AbkError(
            f"Unbalanced dialogue quotes: {chapter.count(OPEN_CLOSE[0])} open, "
            f"{chapter.count(OPEN_CLOSE[1])} close, {len(spans)} matched spans. "
            "Fix the text (a quote crossing a paragraph break is the usual cause)."
        )


# ------------------------------------------------------------------ build step


def parse_turns(raw: list[Any]) -> list[tuple[str, str | None]]:
    turns = []
    for index, entry in enumerate(raw, 1):
        if isinstance(entry, str):
            turns.append((entry, None))
        elif isinstance(entry, list) and len(entry) == 2:
            turns.append((entry[0], entry[1]))
        elif isinstance(entry, dict) and "speaker" in entry:
            turns.append((entry["speaker"], entry.get("text")))
        else:
            raise AbkError(f"quotes[{index}] must be a speaker string, [speaker, text], or {{speaker, text}}")
    return turns


def split_segments(
    paragraphs: list[str], turns: list[tuple[str, str | None]], voices: dict[str, Any],
    default_speaker: str, pattern: str = DEFAULT_QUOTE,
) -> list[dict[str, Any]]:
    rx = re.compile(pattern)
    spans = quote_spans(paragraphs, pattern)
    check_delimiters(paragraphs, spans, pattern)
    if len(spans) != len(turns):
        raise AbkError(f"{len(spans)} quoted spans in the text but {len(turns)} speaker assignments")
    for span, (speaker, expected) in zip(spans, turns, strict=True):
        if speaker not in voices:
            raise AbkError(f"Quote {span['index']} assigned to unknown speaker {speaker!r}")
        if expected is not None and expected != span["text"]:
            raise AbkError(
                f"Quote {span['index']} ({speaker}) changed: {span['text']!r}; reviewed as {expected!r}. "
                "Re-review the attribution before rebuilding."
            )
    segments: list[dict[str, Any]] = []
    cursor_turn = 0
    for number, paragraph in enumerate(paragraphs, 1):
        cursor = 0
        for match in rx.finditer(paragraph):
            narration = paragraph[cursor:match.start()].strip()
            if narration:
                segments.append({"speaker": default_speaker, "text": narration, "paragraph": number})
            speaker, _ = turns[cursor_turn]
            if match.group(1).strip():
                segments.append({"speaker": speaker, "text": match.group(1), "paragraph": number})
            cursor_turn += 1
            cursor = match.end()
        tail = paragraph[cursor:].strip()
        if tail:
            segments.append({"speaker": default_speaker, "text": tail, "paragraph": number})
    verify_reconstruction(paragraphs, segments, pattern)
    return segments


def strip_quotes(text: str, pattern: str) -> str:
    return re.sub(pattern, lambda m: m.group(1), text)


def verify_reconstruction(paragraphs: list[str], segments: list[dict[str, Any]], pattern: str) -> None:
    if not segments:
        raise AbkError("No spoken segments")
    for number, paragraph in enumerate(paragraphs, 1):
        got = normalized(" ".join(s["text"] for s in segments if s["paragraph"] == number))
        want = normalized(strip_quotes(paragraph, pattern))
        if got != want:
            raise AbkError(f"Paragraph {number} lost or gained content during segmentation")
    whole = normalized(" ".join(s["text"] for s in segments))
    if whole != normalized(strip_quotes("\n\n".join(paragraphs), pattern)):
        raise AbkError("Chapter reconstruction differs from the source text")


def validate_voice_design(speaker: str, voice: dict[str, Any]) -> None:
    safe_id(speaker, "speaker id")
    if voice.get("reference_audio"):
        return  # pinned (already designed/selected); no design prompt needed
    description, reference = voice.get("description", ""), voice.get("reference_text", "")
    if not description or re.search(r"[()]", description):
        raise AbkError(f"{speaker}: description required, without parentheses")
    if words(description) >= 20:
        raise AbkError(f"{speaker}: description is {words(description)} words; keep it under 20 (longer degrades the voice)")
    if not 15 <= words(reference) <= 20:
        raise AbkError(f"{speaker}: reference_text is {words(reference)} words; use 15-20 (about 8 seconds, never chapter content)")


def build_manifest(
    paragraphs: list[str], spec: dict[str, Any], pinned: dict[str, str] | None = None,
) -> dict[str, Any]:
    voices = {key: dict(value) for key, value in spec.get("voices", {}).items()}
    if not voices:
        raise AbkError("speakers.json needs a non-empty `voices` object")
    for speaker, path in (pinned or {}).items():
        if speaker in voices:
            voices[speaker]["reference_audio"] = path
    for speaker, voice in voices.items():
        validate_voice_design(speaker, voice)
    default = spec.get("default_speaker", "narrator")
    if default not in voices:
        raise AbkError(f"default_speaker {default!r} is not in voices")
    pattern = spec.get("quote_pattern", DEFAULT_QUOTE)
    turns = parse_turns(spec.get("quotes", []))
    segments = split_segments(paragraphs, turns, voices, default, pattern)
    unused = sorted(set(voices) - {s["speaker"] for s in segments})
    return {
        "title": spec["title"], "chapter": spec["chapter"],
        "source": spec.get("source", {}),
        "settings": spec.get("settings", {"cfg": 2.0, "steps": 12}),
        "voices": voices, "casting": spec.get("casting", {}),
        "segments": segments, "unused_voices": unused,
    }


# ------------------------------------------------------------------------- CLI


def load_paragraphs(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    paragraphs = [normalized(block) for block in re.split(r"\n\s*\n", text) if block.strip()]
    if not paragraphs:
        raise AbkError(f"{path} has no text")
    return paragraphs


def cmd_text(args: argparse.Namespace) -> dict[str, Any]:
    corrections = read_json(args.corrections) if args.corrections else None
    join = {int(x) for x in args.join_previous.split(",") if x} if args.join_previous else set()
    paragraphs, report = assemble_text(
        args.pages_dir, args.first, args.last, start_marker=args.start_marker, end_marker=args.end_marker,
        strip_folio=args.strip_folio, join_previous=join, auto_join=args.auto_join, corrections=corrections,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n\n".join(paragraphs) + "\n", encoding="utf-8")
    if args.end_marker and not report["end_marker_found"]:
        print(f"warning: end marker {args.end_marker!r} not found on pages {args.first}-{args.last}; "
              "the chapter runs to the last page", file=sys.stderr)
    return {"out": str(args.out), "paragraphs": len(paragraphs), "words": sum(words(p) for p in paragraphs), **report}


def cmd_quotes(args: argparse.Namespace) -> Any:
    paragraphs = load_paragraphs(args.text)
    spans = quote_spans(paragraphs, args.quote_pattern)
    check_delimiters(paragraphs, spans, args.quote_pattern)
    return spans


def cmd_build(args: argparse.Namespace) -> dict[str, Any]:
    spec = read_json(args.speakers)
    paragraphs = load_paragraphs(args.text)
    pinned: dict[str, str] = {}
    out = args.out
    if args.book:
        import book as bookmod  # sibling module; imported lazily so `text`/`quotes` stay standalone

        data = bookmod.load(args.book)
        if args.chapter is None:
            raise AbkError("--chapter is required with --book")
        spec.setdefault("chapter", args.chapter)
        spec.setdefault("title", data["title"])
        out = out or bookmod.chapter_dir(args.book, args.chapter) / "chapter.json"
        for speaker, voice in data["voices"].items():
            audio = voice.get("reference_audio")
            if audio and speaker in spec.get("voices", {}):
                pinned[speaker] = str(Path(bookmod.absolute(args.book, audio["path"])).resolve())
    if out is None:
        raise AbkError("--out is required without --book")
    manifest = build_manifest(paragraphs, spec, pinned)
    base = out.resolve().parent
    for speaker, path in pinned.items():  # keep manifests relocatable: paths relative to the manifest
        manifest["voices"][speaker]["reference_audio"] = os.path.relpath(path, base)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, manifest)
    if args.book:  # record the chapter's files and move the marker to `prepared` (resume picks it up)
        bookmod.set_chapter(args.book, args.chapter, title=spec.get("chapter_title"), text=args.text, manifest=out)
        bookmod.set_progress(args.book, args.chapter, "prepared")
    counts: dict[str, int] = {}
    for segment in manifest["segments"]:
        counts[segment["speaker"]] = counts.get(segment["speaker"], 0) + 1
    return {
        "out": str(out), "paragraphs": len(paragraphs), "segments": len(manifest["segments"]),
        "characters": sum(len(s["text"]) for s in manifest["segments"]),
        "segments_by_speaker": counts, "pinned_voices": sorted(pinned),
        "unused_voices": manifest["unused_voices"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    text = sub.add_parser("text", help="assemble page-NNN.txt files into chapter.txt")
    text.add_argument("--pages-dir", type=Path, required=True)
    text.add_argument("--first", type=int, required=True)
    text.add_argument("--last", type=int, required=True)
    text.add_argument("--out", type=Path, required=True)
    text.add_argument("--start-marker", help="drop everything up to and including this heading on the first page")
    text.add_argument("--end-marker", help="drop this marker and everything after it on the last page")
    text.add_argument("--strip-folio", action="store_true", help="drop the last line of each page (page number)")
    text.add_argument("--join-previous", help="comma list of pages whose first block continues the previous paragraph")
    text.add_argument("--auto-join", action="store_true", help="also join when the previous paragraph lacks terminal punctuation")
    text.add_argument("--corrections", type=Path, help='JSON list of {"page","before","after"}; each must match')

    quotes = sub.add_parser("quotes", help="list numbered quoted spans for speaker attribution")
    quotes.add_argument("--text", type=Path, required=True)
    quotes.add_argument("--quote-pattern", default=DEFAULT_QUOTE)

    build = sub.add_parser("build", help="chapter.txt + speakers.json -> chapter.json")
    build.add_argument("--text", type=Path, required=True)
    build.add_argument("--speakers", type=Path, required=True)
    build.add_argument("--out", type=Path)
    build.add_argument("--book", type=Path, help="book dir: pin voices already registered in book.json")
    build.add_argument("--chapter", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = {"text": cmd_text, "quotes": cmd_quotes, "build": cmd_build}[args.command](args)
    except (AbkError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
