"""Atomic filesystem and subprocess primitives for reportctl.

Scope is deliberately small: archive path derivation, atomic writes, an advisory
file lock, the immutable archive-generation publish transaction, and a bounded
subprocess runner.

Everything that supported Hermes cron reconciliation (the profile YAML parser,
timezone/inference preflight, next-run checks, skill-install probing) was removed
in the merged pipeline: there is exactly one cron job now, and its correctness is
proven by ``reportctl verify``, not by inspecting scheduler state.
"""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from reportctl_contracts import ConfigError

COMMAND_TIMEOUT_SECONDS = 30
COMMAND_ERROR_TAIL = 500


def archive_paths(config: dict[str, Any], date: str) -> dict[str, Any]:
    try:
        parsed = dt.date.fromisoformat(date)
    except ValueError as exc:
        raise ConfigError("date must use YYYY-MM-DD") from exc
    base = Path(config["artifact_dir"]) / date
    archive = Path(config["archive_dir"]) / f"{parsed.year:04d}" / f"{parsed.month:02d}" / date
    return {
        "sections_dir": str(base / "sections"),
        "manifest": str(base / "run-manifest.json"),
        "archive_root": str(archive),
        "commit_marker": str(archive / "current.json"),
    }


def fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(
    path: Path, value: Any, *, after_replace: Callable[[], None] | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if after_replace:
            after_replace()
        fsync_dir(path.parent)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_dir(path.parent)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


@contextmanager
def file_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"lock failure at {path}: {exc}") from exc
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX)
        except OSError as exc:
            raise ConfigError(f"lock failure at {path}: {exc}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def run_command(
    command: list[str], *, env: dict[str, str] | None = None, timeout: int = COMMAND_TIMEOUT_SECONDS
) -> subprocess.CompletedProcess[str]:
    """Run a local command, failing loudly and never silently.

    Child diagnostics are bounded to the last ``COMMAND_ERROR_TAIL`` characters
    rather than filtered through a pattern denylist -- a bound cannot
    false-positive, and this runner is only ever pointed at local tools
    (git, systemctl) that do not print credentials.
    """
    try:
        return subprocess.run(
            command, check=True, text=True, capture_output=True, env=env, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise ConfigError(f"missing executable: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ConfigError(f"command timed out after {timeout}s: {command[0]}") from exc
    except OSError as exc:
        raise ConfigError(f"command failed to start: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()[-COMMAND_ERROR_TAIL:]
        raise ConfigError(
            f"command failed ({command[0]} exit {exc.returncode}): {message}"
        ) from exc


def publish_archive_pair(
    archive_root: Path,
    markdown: str,
    report: dict[str, Any],
    manifest: dict[str, Any],
    report_date: str,
) -> dict[str, Any]:
    marker_path = archive_root / "current.json"
    with file_lock(marker_path.with_suffix(".lock")):
        generations = archive_root / "generations"
        generations.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        staged = generations / f".stage-{token}"
        generation = generations / token
        pointer_replaced = False

        def record_pointer_replace() -> None:
            nonlocal pointer_replaced
            pointer_replaced = True

        staged.mkdir()
        try:
            atomic_write_text(staged / "report.md", markdown)
            atomic_write(staged / "report.json", report)
            atomic_write(staged / "run-manifest.json", manifest)
            fsync_dir(staged)
            os.replace(staged, generation)
            fsync_dir(generations)
            atomic_write(
                marker_path,
                {
                    "schema_version": 1,
                    "report_date": report_date,
                    "generation": token,
                },
                after_replace=record_pointer_replace,
            )
        except BaseException:
            if staged.exists():
                for path in staged.iterdir():
                    path.unlink(missing_ok=True)
                staged.rmdir()
            pointer_target = None
            try:
                pointer = json.loads(marker_path.read_text(encoding="utf-8"))
                pointer_target = pointer.get("generation") if isinstance(pointer, dict) else None
            except (OSError, json.JSONDecodeError):
                pass
            if generation.exists() and not (pointer_replaced or pointer_target == token):
                for path in generation.iterdir():
                    path.unlink(missing_ok=True)
                generation.rmdir()
            fsync_dir(generations)
            raise
    markdown_path, report_path, manifest_path = (
        generation / "report.md",
        generation / "report.json",
        generation / "run-manifest.json",
    )
    return {
        "archived": True,
        "markdown": str(markdown_path),
        "report_json": str(report_path),
        "manifest": str(manifest_path),
        "commit_marker": str(marker_path),
    }
