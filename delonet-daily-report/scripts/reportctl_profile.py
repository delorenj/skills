"""Fail-closed resolution of Hermes skill directories and pointer files."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from reportctl_security import contains_secret

MAX_POINTER_BYTES = 4096


def _resolved_directory(path: Path) -> Path | None:
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return resolved if resolved.is_dir() else None


def _lexically_trusted(path: Path, home: Path, name: str) -> bool:
    profile_entry = home / "skills" / name
    canonical_entry = Path.home() / ".agents" / "skills" / name
    return path == profile_entry or path == canonical_entry or path.is_relative_to(canonical_entry)


def _canonical_entry_trusted(path: Path, name: str) -> bool:
    canonical_entry = Path.home() / ".agents" / "skills" / name
    return path == canonical_entry or path.is_relative_to(canonical_entry)


def _trusted_symlink(entry: Path, name: str) -> bool:
    try:
        raw_target = entry.readlink()
    except OSError:
        return False
    if contains_secret(str(raw_target)):
        return False
    destination = raw_target if raw_target.is_absolute() else entry.parent / raw_target
    normalized = Path(os.path.normpath(destination))
    return _canonical_entry_trusted(normalized, name)


def _pointer_target(entry: Path, home: Path, name: str) -> Path | None:
    try:
        metadata = entry.lstat()
        if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= MAX_POINTER_BYTES:
            return None
        raw = entry.read_bytes()
    except OSError:
        return None
    if len(raw) > MAX_POINTER_BYTES or b"\x00" in raw:
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        return None
    lines = text.splitlines()
    if len(lines) != 1 or not lines[0].strip() or contains_secret(text):
        return None
    value = lines[0].strip()
    target = Path(value)
    if (
        not target.is_absolute()
        or ".." in target.parts
        or not _lexically_trusted(target, home, name)
    ):
        return None
    return _resolved_directory(target)


def _valid_skill_marker(target: Path) -> bool:
    try:
        marker = (target / "SKILL.md").resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return marker.is_relative_to(target) and marker.is_file()


def skill_entry_installed(home: Path, name: str) -> bool:
    """Return whether a profile skill entry resolves to an approved skill directory."""
    entry = home / "skills" / name
    try:
        metadata = entry.lstat()
    except OSError:
        return False
    if stat.S_ISREG(metadata.st_mode):
        target = _pointer_target(entry, home, name)
    elif stat.S_ISDIR(metadata.st_mode):
        target = _resolved_directory(entry)
    elif stat.S_ISLNK(metadata.st_mode):
        if not _trusted_symlink(entry, name):
            return False
        target = _resolved_directory(entry)
    else:
        return False
    return bool(target and target.name == name and _valid_skill_marker(target))
