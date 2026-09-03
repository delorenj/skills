"""Token usage inside the window from Claude and Codex transcripts.

Claude: `~/.claude/projects/<slug>/**/*.jsonl` (subagent files live under
`<session>/subagents/`). The first line carrying `cwd` decides scope; each
assistant line with `message.usage` is one sample, deduplicated by
`message.id` (a message is written several times while it streams; the last
copy wins). Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`, scope from
`session_meta.payload.cwd`; `token_count` events carry a cumulative
`total_token_usage`, so the window's usage is the last total before the end
minus the last total before the start. Kimi has no transcript source yet and
stays null. An agent with no in-scope transcript is null, not zero.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timedelta

from .common import parse_iso

CLAUDE_ROOT = os.path.join(os.path.expanduser("~"), ".claude", "projects")
CODEX_ROOT = os.path.join(os.path.expanduser("~"), ".codex", "sessions")
MTIME_SLACK_SECONDS = 3600
HEAD_LINES = 200
BUCKET_KEYS = ("input", "output", "cache_read", "cache_write")
CODEX_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")


def _bucket(input_tokens: int, output: int, cache_read: int, cache_write: int) -> dict:
    return {"input": input_tokens, "output": output, "cache_read": cache_read, "cache_write": cache_write,
            "total": input_tokens + output + cache_read + cache_write}


def _int(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return max(0, int(value))


def _ts(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return parse_iso(value)
    except ValueError:
        return None


def _iter_jsonl(path: str):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict):
                    yield obj
    except OSError:
        return


def _first_cwd(path: str, key: str = "cwd", nested: tuple = ()) -> str | None:
    for n, obj in enumerate(_iter_jsonl(path)):
        if n >= HEAD_LINES:
            break
        container = obj
        for part in nested:
            container = container.get(part) if isinstance(container, dict) else None
        if isinstance(container, dict):
            value = container.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _recent(path: str, cutoff: float) -> bool:
    try:
        return os.stat(path).st_mtime >= cutoff
    except OSError:
        return False


# -- Claude ---------------------------------------------------------------------

def _claude(scope, window, root: str) -> tuple[dict | None, dict]:
    detail: dict = {"root_present": os.path.isdir(root), "files": 0, "sessions": 0, "messages": 0, "by_model": {}}
    if not detail["root_present"]:
        return None, detail
    cutoff = (window.start - timedelta(seconds=MTIME_SLACK_SECONDS)).timestamp()
    usage_by_id: dict[str, tuple[dict, str | None]] = {}
    sessions: set[tuple] = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            if not filename.endswith(".jsonl"):
                continue
            path = os.path.join(dirpath, filename)
            if not _recent(path, cutoff):
                continue
            if not scope.contains(_first_cwd(path)):
                continue
            detail["files"] += 1
            rel = os.path.relpath(path, root).split(os.sep)
            sessions.add((rel[0], rel[1][:-6] if len(rel) == 2 else rel[1]))
            for obj in _iter_jsonl(path):
                if obj.get("type") != "assistant":
                    continue
                message = obj.get("message")
                if not isinstance(message, dict) or not isinstance(message.get("usage"), dict):
                    continue
                at = _ts(obj.get("timestamp"))
                if at is None:
                    continue
                if at >= window.end:
                    break
                if at < window.start:
                    continue
                mid = message.get("id") or obj.get("requestId") or obj.get("uuid") or f"{path}:{len(usage_by_id)}"
                usage_by_id[str(mid)] = (message["usage"], message.get("model") if isinstance(message.get("model"), str) else None)
    if detail["files"] == 0:
        return None, detail
    detail["sessions"] = len(sessions)
    detail["messages"] = len(usage_by_id)
    by_model: Counter = Counter()
    input_tokens = output = cache_read = cache_write = 0
    for usage, model in usage_by_id.values():
        input_tokens += _int(usage.get("input_tokens"))
        output += _int(usage.get("output_tokens"))
        cache_read += _int(usage.get("cache_read_input_tokens"))
        cache_write += _int(usage.get("cache_creation_input_tokens"))
        by_model[model or "unknown"] += 1
    detail["by_model"] = dict(sorted(by_model.items(), key=lambda kv: (-kv[1], kv[0])))
    return _bucket(input_tokens, output, cache_read, cache_write), detail


# -- Codex ----------------------------------------------------------------------

def _codex_files(root: str, window) -> list[str]:
    local_tz = datetime.now().astimezone().tzinfo
    day = (window.start.astimezone(local_tz) - timedelta(days=1)).date()
    last = window.end.astimezone(local_tz).date()
    files: list[str] = []
    while day <= last:
        directory = os.path.join(root, f"{day:%Y}", f"{day:%m}", f"{day:%d}")
        if os.path.isdir(directory):
            for name in sorted(os.listdir(directory)):
                if name.startswith("rollout-") and name.endswith(".jsonl"):
                    files.append(os.path.join(directory, name))
        day += timedelta(days=1)
    return files


def _codex(scope, window, root: str) -> tuple[dict | None, dict]:
    detail: dict = {"root_present": os.path.isdir(root), "files": 0, "sessions_with_usage": 0, "reasoning_output": 0}
    if not detail["root_present"]:
        return None, detail
    cutoff = (window.start - timedelta(seconds=MTIME_SLACK_SECONDS)).timestamp()
    totals = {name: 0 for name in CODEX_FIELDS}
    for path in _codex_files(root, window):
        if not _recent(path, cutoff):
            continue
        if not scope.contains(_first_cwd(path, nested=("payload",))):
            continue
        detail["files"] += 1
        before: dict | None = None
        last_in: dict | None = None
        for obj in _iter_jsonl(path):
            if obj.get("type") != "event_msg":
                continue
            payload = obj.get("payload")
            if not isinstance(payload, dict) or payload.get("type") != "token_count":
                continue
            info = payload.get("info")
            total = info.get("total_token_usage") if isinstance(info, dict) else None
            if not isinstance(total, dict):
                continue
            at = _ts(obj.get("timestamp"))
            if at is None:
                continue
            if at < window.start:
                before = total
                continue
            if at >= window.end:
                break
            last_in = total
        if last_in is None:
            continue
        detail["sessions_with_usage"] += 1
        for name in CODEX_FIELDS:
            totals[name] += max(0, _int(last_in.get(name)) - _int((before or {}).get(name)))
    if detail["files"] == 0:
        return None, detail
    detail["reasoning_output"] = totals["reasoning_output_tokens"]
    cache_read = totals["cached_input_tokens"]
    return _bucket(max(0, totals["input_tokens"] - cache_read), totals["output_tokens"], cache_read,
                   totals["cache_write_input_tokens"]), detail


# -- entry ----------------------------------------------------------------------

def collect(scope, window, claude_root: str | None = None, codex_root: str | None = None) -> dict:
    """The digest "tokens" block (plus a caveats list digest.py hoists)."""
    caveats: list[str] = []
    claude, claude_detail = _claude(scope, window, claude_root or CLAUDE_ROOT)
    codex, codex_detail = _codex(scope, window, codex_root or CODEX_ROOT)
    if claude is None:
        caveats.append("no Claude transcript in scope for the window" if claude_detail["root_present"]
                       else "Claude transcript root is absent")
    if codex is None:
        caveats.append("no Codex rollout in scope for the window" if codex_detail["root_present"]
                       else "Codex session root is absent")
    total = sum(b["total"] for b in (claude, codex) if b)
    return {
        "total": total,
        "by_agent": {"claude": claude, "codex": codex, "kimi": None},
        "detail": {"claude": claude_detail, "codex": codex_detail, "kimi": {"status": "no transcript source"}},
        "caveats": caveats,
    }
