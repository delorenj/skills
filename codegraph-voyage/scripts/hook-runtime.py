#!/usr/bin/env python3
"""Fail-open, project-scoped runtime for CodeGraph Voyage lifecycle hooks."""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

DIRTY_NAME = "codegraph-voyage.dirty"
LOCK_NAME = "codegraph-voyage.lock"
LOG_NAME = "codegraph-voyage-hooks.log"
MAX_PAYLOAD_BYTES = 1_048_576
MAX_LOG_BYTES = 65_536
DEFAULT_INDEX_TIMEOUT = 30.0
DEFAULT_STATUS_TIMEOUT = 2.0
MUTATION_WORDS = (
    "write", "edit", "patch", "create", "replace", "rename", "move", "delete",
    "apply_patch", "multi_edit", "str_replace",
)
READ_ONLY_WORDS = (
    "read", "search", "grep", "find", "list", "status", "describe", "get", "view",
)
ROOT_KEYS = (
    "project_root", "projectRoot", "project_path", "projectPath", "workspace_root",
    "workspaceRoot", "workspace", "cwd", "working_directory", "workingDirectory",
)
TOOL_KEYS = ("tool_name", "toolName", "tool", "name", "function_name", "functionName")


def _payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.buffer.read(MAX_PAYLOAD_BYTES + 1)
        if len(raw) > MAX_PAYLOAD_BYTES or not raw.strip():
            return {}
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _string_at(value: Any, keys: tuple[str, ...], depth: int = 0) -> str | None:
    if depth > 3 or not isinstance(value, dict):
        return None
    for key in keys:
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    for key in (
        "context", "request", "input", "tool", "function", "tool_input", "toolInput", "metadata"
    ):
        found = _string_at(value.get(key), keys, depth + 1)
        if found:
            return found
    return None


def _project_root(payload: dict[str, Any]) -> Path | None:
    raw = _string_at(payload, ROOT_KEYS) or os.getcwd()
    try:
        start = Path(raw).expanduser()
        if not start.is_absolute():
            start = Path.cwd() / start
        start = start.resolve(strict=False)
        if start.is_file():
            start = start.parent
        for candidate in (start, *start.parents):
            if (candidate / ".codegraph" / "codegraph.db").is_file() and (
                candidate / "tools" / "codegraph_voyage"
            ).is_dir():
                return candidate
    except Exception:
        pass
    return None


def _tool_name(payload: dict[str, Any]) -> str:
    return (_string_at(payload, TOOL_KEYS) or "").strip().lower()


def _is_mutation(payload: dict[str, Any]) -> bool:
    name = _tool_name(payload)
    if not name:
        return False
    if any(word in name for word in MUTATION_WORDS):
        return True
    if any(word in name for word in READ_ONLY_WORDS):
        return False
    # Tolerate clients that expose a generic file tool with an operation/action field.
    operation = _string_at(payload, ("operation", "action", "op", "mode"))
    operation = operation.lower() if operation else ""
    return any(word in operation for word in MUTATION_WORDS)


def _append_log(root: Path, message: str) -> None:
    try:
        path = root / ".codegraph" / LOG_NAME
        old = path.read_bytes()[-(MAX_LOG_BYTES // 2) :] if path.is_file() else b""
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {message}\n".encode(
            "utf-8", "replace"
        )
        data = (old + line)[-MAX_LOG_BYTES:]
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, path)
    except Exception:
        pass


def _provider(root: Path) -> str:
    value = os.environ.get("CODEGRAPH_VOYAGE_HOOK_PROVIDER", "").strip().lower()
    if not value:
        try:
            local = json.loads((root / ".agents" / "local.json").read_text(encoding="utf-8"))
            value = str(
                local.get("codegraph_voyage_hook_provider")
                or local.get("codegraph-voyage", {}).get("hook_provider")
                or local.get("codegraph_voyage", {}).get("hook_provider")
                or "fake"
            ).strip().lower()
        except Exception:
            value = "fake"
    return value if value in {"fake", "voyage", "off"} else "fake"


def _timeout(variable: str, default: float, maximum: float) -> float:
    try:
        return max(0.1, min(float(os.environ.get(variable, default)), maximum))
    except (TypeError, ValueError):
        return default


async def _run(root: Path, arguments: list[str], timeout: float) -> bool:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root) + os.pathsep + environment.get("PYTHONPATH", "")
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "tools.codegraph_voyage",
        *arguments,
        cwd=root,
        env=environment,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        _append_log(root, f"subprocess timed out after {timeout:.1f}s")
        return False
    if process.returncode != 0:
        detail = (stderr or b"").decode("utf-8", "replace").strip().replace("\n", " ")[-1000:]
        _append_log(root, f"subprocess failed ({process.returncode}): {detail}")
        return False
    return True


def _status(root: Path) -> None:
    try:
        asyncio.run(_run(root, ["status"], _timeout("CODEGRAPH_VOYAGE_HOOK_STATUS_TIMEOUT", DEFAULT_STATUS_TIMEOUT, 5.0)))
    except Exception as exc:
        _append_log(root, f"status probe failed: {type(exc).__name__}: {exc}")


def _mark_dirty(root: Path) -> None:
    try:
        path = root / ".codegraph" / DIRTY_NAME
        temporary = path.with_suffix(f".tmp.{os.getpid()}")
        temporary.write_text(f"{time.time_ns()}\n", encoding="ascii")
        os.replace(temporary, path)
    except Exception as exc:
        _append_log(root, f"could not mark dirty: {type(exc).__name__}: {exc}")


def _refresh(root: Path) -> None:
    dirty = root / ".codegraph" / DIRTY_NAME
    if not dirty.is_file():
        return
    provider = _provider(root)
    if provider == "off":
        return
    lock_path = root / ".codegraph" / LOCK_NAME
    try:
        with lock_path.open("a+b") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return
            if not dirty.is_file():
                return
            timeout = _timeout("CODEGRAPH_VOYAGE_HOOK_TIMEOUT", DEFAULT_INDEX_TIMEOUT, 60.0)
            succeeded = asyncio.run(_run(root, ["index", "--provider", provider], timeout))
            if succeeded:
                dirty.unlink(missing_ok=True)
    except Exception as exc:
        _append_log(root, f"refresh failed open: {type(exc).__name__}: {exc}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("session_start", "post_tool", "session_end"))
    args = parser.parse_args(argv)
    try:
        payload = _payload()
        root = _project_root(payload)
        if root is None:
            return 0
        if args.role == "session_start":
            _status(root)
        elif args.role == "post_tool":
            if _is_mutation(payload):
                _mark_dirty(root)
        else:
            _refresh(root)
    except Exception:
        # Lifecycle hooks must never break the client workflow.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
