"""Shared vocabulary for every activity-report module.

Exit codes, the error hierarchy that maps onto them, time helpers, and the
on-disk layout of a run. Nothing here touches the network.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

EXIT_OK = 0
EXIT_CONFIG = 2        # configuration, contract, I/O, or a required source unreachable
EXIT_ACCEPTANCE = 3    # lint violation, event not projected, files missing
EXIT_NOTHING = 4       # window shorter than window.min_minutes (pass --force)
EXIT_LOCKED = 5        # another run holds the project lock

AUDIENCES = ("internal", "external")
AGENT_NAMES = ("claude", "codex", "kimi", "hermes", "copilot", "antigravity", "opencode")
TOKEN_AGENTS = ("claude", "codex", "kimi")   # the buckets the event carries
SKILL_NAME = "activity-report"
EVENT_TYPE = "bloodbank.project.activity.recorded"
CANDYSTORE_URL = os.environ.get("CANDYSTORE_URL", "http://127.0.0.1:8683")


class SkillError(Exception):
    """Base of every failure the CLI turns into an exit code."""
    exit_code = EXIT_CONFIG


class ConfigError(SkillError):
    exit_code = EXIT_CONFIG


class SourceUnavailable(SkillError):
    """A required source (Candystore) cannot be reached. Never degrade to git-only."""
    exit_code = EXIT_CONFIG


class ContractError(SkillError):
    """A digest or event does not have the shape the contract requires."""
    exit_code = EXIT_CONFIG


class AcceptanceError(SkillError):
    exit_code = EXIT_ACCEPTANCE


class NothingToDo(SkillError):
    exit_code = EXIT_NOTHING


class Locked(SkillError):
    exit_code = EXIT_LOCKED


# -- time -------------------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_iso_z(dt: datetime) -> str:
    """RFC 3339 in UTC with a Z suffix and whole seconds: 2026-09-03T07:00:00Z."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 / RFC 3339 string into an aware UTC datetime.

    Accepts a trailing Z, a numeric offset, or a naive value (taken as UTC).
    """
    text = value.strip()
    if text.endswith("Z") or text.endswith("z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def label_for(dt: datetime, tz: str) -> str:
    """The run label: the window end in the project timezone as YYYY-MM-DDTHHMM."""
    return dt.astimezone(ZoneInfo(tz)).strftime("%Y-%m-%dT%H%M")


# -- files ------------------------------------------------------------------

def read_json(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str, obj) -> None:
    """Atomic write: tmp file in the same directory, then os.replace."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ar-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, sort_keys=False, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_text(path: str, text: str) -> None:
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ar-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def runtime_dir(project) -> str:
    """<repo_path>/<output.runtime_dir>/<slug> — gitignored per-run files."""
    return os.path.join(project.repo_path, project.config["output"]["runtime_dir"], project.slug)


def runtime_paths(project, label: str, audience: str) -> dict:
    """Every file a run touches, keyed by role. `lint_json` exists only for external."""
    base = os.path.join(runtime_dir(project), f"{label}-{audience}")
    return {
        "dir": runtime_dir(project),
        "lock": os.path.join(runtime_dir(project), ".lock"),
        "digest": base + ".digest.json",
        "raw": base + ".raw.txt",
        "markdown": base + ".md",
        "html": base + ".html",
        "event": base + ".event.json",
        "compose": base + ".compose.json",
        "emit": base + ".emit.json",
        "lint_json": os.path.join(runtime_dir(project), f"{label}-external.lint.json"),
    }


def state_dir(slug: str) -> str:
    root = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(root, SKILL_NAME, slug)


def cache_dir(*parts: str) -> str:
    root = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    path = os.path.join(root, SKILL_NAME, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def eprint(*args) -> None:
    print(*args, file=sys.stderr, flush=True)
