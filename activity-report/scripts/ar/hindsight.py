"""Hindsight: list/recall for the digest, retain for the finished report.

Hindsight is colour, never truth. Nothing here decides a count; everything it
returns is an aside for the compose agent, and every failure degrades to
`status: unavailable` with a caveat instead of stopping the run. Memories the
skill wrote itself (context `activity-report:<audience>`) are excluded from
the listing so a report never quotes the previous report back as a fact.
"""
from __future__ import annotations

import json
import os
import subprocess

from .common import ConfigError, eprint, parse_iso, read_json, to_iso_z
from .config import hindsight_bank, load_project

HINDSIGHT_BIN = os.environ.get("HINDSIGHT_BIN", "hindsight")
CONTEXT_PREFIX = "activity-report:"
LIST_PAGE = 200
LIST_MAX_PAGES = 5
ITEM_CAP = 40
RECALL_CAP = 20
TEXT_CHARS = 500
LIST_TIMEOUT = 60
RECALL_TIMEOUT = 120
RETAIN_TIMEOUT = 120


class HindsightFailed(Exception):
    pass


def _run(args: list[str], timeout: int) -> str:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise HindsightFailed(f"{args[0]} is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise HindsightFailed(f"{' '.join(args[:3])} timed out after {timeout}s") from exc
    except OSError as exc:
        raise HindsightFailed(f"{' '.join(args[:3])}: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        raise HindsightFailed(f"{' '.join(args[:3])} exited {proc.returncode}: {detail[-1][:200] if detail else 'no output'}")
    return proc.stdout


def _json(text: str):
    try:
        return json.loads(text)
    except ValueError as exc:
        raise HindsightFailed("hindsight returned non-JSON output") from exc


def _text_of(item: dict) -> str | None:
    for name in ("text", "content", "fact", "memory"):
        value = item.get(name)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return None


def _when(item: dict):
    for name in ("date", "occurred_start", "mentioned_at", "created_at"):
        value = item.get(name)
        if isinstance(value, str) and value:
            try:
                return parse_iso(value)
            except ValueError:
                continue
    return None


def _list(bank: str, window) -> tuple[list[dict], int]:
    """Memories recorded inside the window, newest first; (items, scanned)."""
    items: list[dict] = []
    offset = scanned = 0
    for _ in range(LIST_MAX_PAGES):
        out = _run([HINDSIGHT_BIN, "memory", "list", bank, "-o", "json", "-l", str(LIST_PAGE), "-s", str(offset)], LIST_TIMEOUT)
        body = _json(out)
        batch = body.get("items") if isinstance(body, dict) else body
        if not isinstance(batch, list):
            raise HindsightFailed("hindsight memory list returned no items list")
        for item in batch:
            if not isinstance(item, dict):
                continue
            scanned += 1
            if item.get("invalidated_at"):
                continue
            context = item.get("context")
            if isinstance(context, str) and context.startswith(CONTEXT_PREFIX):
                continue
            at = _when(item)
            text = _text_of(item)
            if at is None or text is None or not (window.start <= at < window.end):
                continue
            items.append({"at": to_iso_z(at), "fact_type": item.get("fact_type") if isinstance(item.get("fact_type"), str) else None,
                          "text": text[:TEXT_CHARS]})
        offset += len(batch)
        total = body.get("total") if isinstance(body, dict) else None
        if not batch or len(batch) < LIST_PAGE or (isinstance(total, int) and offset >= total):
            break
        dates = [d for d in (_when(i) for i in batch if isinstance(i, dict)) if d is not None]
        if dates and dates == sorted(dates, reverse=True) and dates[-1] < window.start:
            break   # the listing is newest-first and this page already passed the window
    items.sort(key=lambda i: i["at"], reverse=True)
    return items, scanned


def _recall(bank: str, query: str) -> list[str]:
    out = _run([HINDSIGHT_BIN, "memory", "recall", bank, query, "-o", "json", "--budget", "high", "--max-tokens", "2048"],
               RECALL_TIMEOUT)
    body = _json(out)
    results = body.get("results") if isinstance(body, dict) else body
    if not isinstance(results, list):
        return []
    texts: list[str] = []
    for item in results:
        text = _text_of(item) if isinstance(item, dict) else (item if isinstance(item, str) else None)
        if text and text[:TEXT_CHARS] not in texts:
            texts.append(text[:TEXT_CHARS])
        if len(texts) >= RECALL_CAP:
            break
    return texts


def collect(project, window) -> dict:
    """The digest "hindsight" block. Never raises."""
    cfg = project.config.get("hindsight") or {}
    caveats: list[str] = []
    try:
        bank = hindsight_bank(project)
    except ConfigError as exc:
        return {"bank": None, "status": "unavailable", "items": [], "recall": {"query": None, "items": []},
                "caveats": [f"hindsight: {exc}"]}
    block = {"bank": bank, "status": "ok", "items": [], "recall": {"query": None, "items": []}, "caveats": caveats}
    if cfg.get("recall") is False:
        block["status"] = "disabled"
        return block
    list_ok = recall_ok = False
    try:
        items, _scanned = _list(bank, window)
        if len(items) > ITEM_CAP:
            caveats.append(f"hindsight items capped at {ITEM_CAP} of {len(items)}")
        block["items"] = items[:ITEM_CAP]
        list_ok = True
    except (HindsightFailed, Exception) as exc:  # noqa: BLE001 - colour never stops the run
        caveats.append(f"hindsight list failed: {exc}")
    query = (f"what changed for {project.name} between {to_iso_z(window.start)} and {to_iso_z(window.end)}: "
             "wins, blockers, decisions")
    block["recall"]["query"] = query
    try:
        block["recall"]["items"] = _recall(bank, query)
        recall_ok = True
    except (HindsightFailed, Exception) as exc:  # noqa: BLE001
        caveats.append(f"hindsight recall failed: {exc}")
    if not list_ok and not recall_ok:
        block["status"] = "unavailable"
    return block


def retain(project, audience: str, raw_text: str, window_end, label: str) -> bool:
    """Store the report body in the project's bank. False (with a warning) on any failure; never raises."""
    cfg = project.config.get("hindsight") or {}
    if cfg.get("retain") is False:
        eprint(f"activity-report: retain disabled for {project.slug} (hindsight.retain=false)")
        return False
    if not isinstance(raw_text, str) or not raw_text.strip():
        eprint("activity-report: retain skipped: empty report text")
        return False
    try:
        bank = hindsight_bank(project)
    except ConfigError as exc:
        eprint(f"activity-report: retain skipped: {exc}")
        return False
    timestamp = window_end if isinstance(window_end, str) else to_iso_z(window_end)
    args = [HINDSIGHT_BIN, "memory", "retain", bank, raw_text,
            "--context", f"{CONTEXT_PREFIX}{audience}",
            "--doc-id", f"{CONTEXT_PREFIX}{project.slug}:{audience}:{label}",
            "--timestamp", timestamp]
    try:
        _run(args, RETAIN_TIMEOUT)
    except (HindsightFailed, Exception) as exc:  # noqa: BLE001
        eprint(f"activity-report: retain failed (warning): {exc}")
        return False
    return True


def retain_cmd(args) -> int:
    project = load_project(args.project)
    try:
        with open(args.raw, encoding="utf-8") as fh:
            raw_text = fh.read()
    except OSError as exc:
        raise ConfigError(f"cannot read {args.raw}: {exc}") from exc
    try:
        digest = read_json(args.digest)
    except (OSError, ValueError) as exc:
        raise ConfigError(f"cannot read digest {args.digest}: {exc}") from exc
    if not isinstance(digest, dict) or not isinstance(digest.get("window"), dict) or not digest.get("label"):
        raise ConfigError(f"{args.digest} is not a digest (no window/label)")
    if digest.get("audience") != args.audience:
        raise ConfigError(f"{args.digest} is a {digest.get('audience')} digest, not {args.audience}")
    ok = retain(project, args.audience, raw_text, digest["window"]["end"], digest["label"])
    doc_id = f"{CONTEXT_PREFIX}{project.slug}:{args.audience}:{digest['label']}"
    if args.json:
        print(json.dumps({"retained": ok, "bank": hindsight_bank(project), "doc_id": doc_id}))
    elif ok:
        print(f"retained  {hindsight_bank(project)}  {doc_id}")
    else:
        print(f"retain    skipped or failed for {doc_id} (see stderr)")
    return 0
