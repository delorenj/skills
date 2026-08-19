#!/usr/bin/env python3
"""Project the canonical Project Notebook hooks into Claude settings safely."""

from __future__ import annotations

import argparse
import contextlib
import copy
import fcntl
import hashlib
import json
import os
import posixpath
import secrets
import shlex
import stat
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MASTER = SKILL_ROOT / "hooks" / "hooks.master.json"
DEFAULT_FRAGMENT = SKILL_ROOT / "hooks" / "claude.settings.json"
OWNER_PREFIX = "PJ_HOOK_OWNER=project-notebook.v1 "
EVENT_WRAPPERS = {
    "SessionStart": "$HOME/.agents/skills/project-notebook/hooks/session-start.sh",
    "SessionEnd": "$HOME/.agents/skills/project-notebook/hooks/session-end.sh",
}
EVENT_ORDER = tuple(EVENT_WRAPPERS)
MAX_JSON_BYTES = 8 * 1024 * 1024


class ProjectorError(RuntimeError):
    """A bounded validation or projection failure."""


@dataclass(frozen=True)
class Generation:
    exists: bool
    device: int | None
    inode: int | None
    size: int
    modified_ns: int | None
    digest: str


@dataclass(frozen=True)
class LockedState:
    hook_install_fd: int
    snapshots_fd: int


def _canonical_command(event: str) -> str:
    return f'{OWNER_PREFIX}"{EVENT_WRAPPERS[event]}"'


def _absolute_path(raw: str | os.PathLike[str], label: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ProjectorError(f"{label} must be an absolute path")
    if any(component in (".", "..") for component in path.parts[1:]):
        raise ProjectorError(f"{label} must not contain dot path components")
    return path


def _directory_flags() -> int:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise ProjectorError("platform lacks required no-follow directory APIs")
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _regular_read_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        raise ProjectorError("platform lacks required no-follow file APIs")
    return os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _leaf_name(name: str, label: str) -> str:
    if not name or name in (".", "..") or "/" in name or "\0" in name:
        raise ProjectorError(f"{label} has an unsafe leaf name")
    return name


def _open_absolute_directory(
    path: Path,
    label: str,
    *,
    create_missing: bool,
    require_final_owner: bool = False,
) -> int | None:
    if not path.is_absolute():
        raise ProjectorError(f"{label} must be an absolute path")
    components = path.parts[1:]
    if any(component in ("", ".", "..") for component in components):
        raise ProjectorError(f"{label} contains an unsafe path component")
    try:
        current_fd = os.open("/", _directory_flags())
    except OSError as exc:
        raise ProjectorError(f"cannot open filesystem root for {label}: {exc.strerror}") from exc
    try:
        for component in components:
            created = False
            try:
                child_fd = os.open(component, _directory_flags(), dir_fd=current_fd)
            except FileNotFoundError:
                if not create_missing:
                    os.close(current_fd)
                    return None
                try:
                    os.mkdir(component, 0o700, dir_fd=current_fd)
                    created = True
                except FileExistsError:
                    pass
                except (OSError, TypeError) as exc:
                    detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
                    raise ProjectorError(
                        f"cannot create descriptor-relative {label}: {detail}"
                    ) from exc
                try:
                    child_fd = os.open(component, _directory_flags(), dir_fd=current_fd)
                except (OSError, TypeError) as exc:
                    detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
                    raise ProjectorError(
                        f"cannot open descriptor-relative {label}: {detail}"
                    ) from exc
            except (OSError, TypeError) as exc:
                detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
                raise ProjectorError(f"cannot open descriptor-relative {label}: {detail}") from exc
            os.close(current_fd)
            current_fd = child_fd
            information = os.fstat(current_fd)
            if not stat.S_ISDIR(information.st_mode):
                raise ProjectorError(f"{label} must contain only real directories")
            if created and (
                information.st_uid != os.getuid() or stat.S_IMODE(information.st_mode) != 0o700
            ):
                raise ProjectorError(f"new {label} directory must be current-user mode 0700")
        information = os.fstat(current_fd)
        if require_final_owner and information.st_uid != os.getuid():
            raise ProjectorError(f"{label} must be owned by the current user")
        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def _open_private_directory_at(parent_fd: int, name: str, label: str) -> int:
    name = _leaf_name(name, label)
    try:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
    except FileExistsError:
        pass
    except (OSError, TypeError) as exc:
        detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
        raise ProjectorError(f"cannot create descriptor-relative {label}: {detail}") from exc
    try:
        descriptor = os.open(name, _directory_flags(), dir_fd=parent_fd)
    except (OSError, TypeError) as exc:
        detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
        raise ProjectorError(f"cannot open descriptor-relative {label}: {detail}") from exc
    try:
        information = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(information.st_mode)
            or information.st_uid != os.getuid()
            or stat.S_IMODE(information.st_mode) != 0o700
        ):
            raise ProjectorError(f"{label} must be a current-user mode 0700 directory")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectorError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json_object(raw: bytes, label: str) -> dict[str, Any]:
    if len(raw) > MAX_JSON_BYTES:
        raise ProjectorError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProjectorError(f"{label} is not UTF-8") from exc
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except ProjectorError:
        raise
    except json.JSONDecodeError as exc:
        raise ProjectorError(
            f"{label} is invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise ProjectorError(f"{label} must contain one JSON object")
    return value


def _open_regular_at(parent_fd: int, name: str, label: str) -> tuple[int, os.stat_result]:
    name = _leaf_name(name, label)
    try:
        descriptor = os.open(name, _regular_read_flags(), dir_fd=parent_fd)
    except FileNotFoundError:
        raise
    except (OSError, TypeError) as exc:
        if isinstance(exc, TypeError):
            raise ProjectorError(f"platform cannot safely open {label}") from exc
        raise ProjectorError(f"cannot open {label}: {exc.strerror}") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ProjectorError(f"{label} must be a regular file")
        if info.st_uid != os.getuid():
            raise ProjectorError(f"{label} must be owned by the current user")
        if info.st_size > MAX_JSON_BYTES:
            raise ProjectorError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
        return descriptor, info
    except Exception:
        os.close(descriptor)
        raise


def _read_descriptor(descriptor: int, expected_size: int, label: str) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(descriptor, min(65536, MAX_JSON_BYTES + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_JSON_BYTES:
            raise ProjectorError(f"{label} exceeds {MAX_JSON_BYTES} bytes")
    raw = b"".join(chunks)
    if len(raw) != expected_size:
        raise ProjectorError(f"{label} changed while it was being read")
    return raw


def _read_regular_at_bytes(parent_fd: int, name: str, label: str) -> bytes:
    descriptor, information = _open_regular_at(parent_fd, name, label)
    try:
        return _read_descriptor(descriptor, information.st_size, label)
    finally:
        os.close(descriptor)


def _read_regular_bytes(path: Path, label: str) -> bytes:
    parent_fd = _open_absolute_directory(path.parent, f"{label} parent", create_missing=False)
    if parent_fd is None:
        raise ProjectorError(f"{label} does not exist")
    try:
        try:
            return _read_regular_at_bytes(parent_fd, path.name, label)
        except FileNotFoundError as exc:
            raise ProjectorError(f"{label} does not exist") from exc
    finally:
        os.close(parent_fd)


def _absent_target() -> tuple[bytes, dict[str, Any], Generation]:
    return (
        b"",
        {},
        Generation(False, None, None, 0, None, hashlib.sha256(b"").hexdigest()),
    )


def _read_target_at(parent_fd: int, name: str) -> tuple[bytes, dict[str, Any], Generation]:
    try:
        descriptor, info = _open_regular_at(parent_fd, name, "Claude settings target")
    except FileNotFoundError:
        return _absent_target()
    try:
        raw = _read_descriptor(descriptor, info.st_size, "Claude settings target")
    finally:
        os.close(descriptor)
    value = _parse_json_object(raw, "Claude settings target")
    _validate_live_shape(value)
    generation = Generation(
        True,
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        hashlib.sha256(raw).hexdigest(),
    )
    return raw, value, generation


def _read_target(path: Path) -> tuple[bytes, dict[str, Any], Generation]:
    parent_fd = _open_absolute_directory(
        path.parent,
        "Claude settings parent",
        create_missing=False,
        require_final_owner=True,
    )
    if parent_fd is None:
        return _absent_target()
    try:
        return _read_target_at(parent_fd, path.name)
    finally:
        os.close(parent_fd)


def _validate_master(master: dict[str, Any]) -> None:
    if list(master) != ["hooks"]:
        raise ProjectorError("hook master must contain only the hooks key")
    hooks = master.get("hooks")
    if not isinstance(hooks, dict) or list(hooks) != list(EVENT_ORDER):
        raise ProjectorError("hook master events must be SessionStart then SessionEnd")
    if "Stop" in hooks:
        raise ProjectorError("hook master must never contain Stop")
    for event in EVENT_ORDER:
        groups = hooks[event]
        if not isinstance(groups, list) or len(groups) != 1:
            raise ProjectorError(f"hook master {event} must contain one group")
        group = groups[0]
        if not isinstance(group, dict) or list(group) != ["hooks"]:
            raise ProjectorError(f"hook master {event} group must contain only hooks")
        entries = group["hooks"]
        if not isinstance(entries, list) or len(entries) != 1:
            raise ProjectorError(f"hook master {event} must contain one hook")
        hook = entries[0]
        if not isinstance(hook, dict) or list(hook) != ["type", "command", "timeout"]:
            raise ProjectorError(f"hook master {event} hook keys must be type, command, timeout")
        if hook["type"] != "command":
            raise ProjectorError(f"hook master {event} type must be command")
        if hook["command"] != _canonical_command(event):
            raise ProjectorError(f"hook master {event} command is not canonical")
        timeout = hook["timeout"]
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 60:
            raise ProjectorError(f"hook master {event} timeout must be an integer 1..60")


def _deterministic_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _load_master(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular_bytes(path, "hook master")
    master = _parse_json_object(raw, "hook master")
    _validate_master(master)
    return master, _deterministic_bytes(master)


def _load_fragment(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular_bytes(path, "Claude generated fragment")
    fragment = _parse_json_object(raw, "Claude generated fragment")
    return fragment, raw


def _load_assets(master_path: Path, fragment_path: Path) -> dict[str, Any]:
    master, expected = _load_master(master_path)
    fragment, raw = _load_fragment(fragment_path)
    if fragment != master or raw != expected:
        raise ProjectorError("Claude generated fragment is stale; run project-hooks.py render")
    return master


def _validate_live_shape(value: dict[str, Any]) -> None:
    if "hooks" not in value:
        return
    hooks = value["hooks"]
    if not isinstance(hooks, dict):
        raise ProjectorError("Claude settings hooks must be an object")
    for event, groups in hooks.items():
        if not isinstance(event, str) or not isinstance(groups, list):
            raise ProjectorError("each Claude hook event must contain a group array")
        for group in groups:
            if not isinstance(group, dict):
                raise ProjectorError(f"Claude hook group for {event} must be an object")
            if "hooks" not in group:
                continue
            entries = group["hooks"]
            if not isinstance(entries, list):
                raise ProjectorError(f"Claude hook group hooks for {event} must be an array")
            if not all(isinstance(entry, dict) for entry in entries):
                raise ProjectorError(f"Claude hook entries for {event} must be objects")


def _normalized_wrapper(token: str) -> str | None:
    if token.startswith("${HOME}/"):
        token = "$HOME/" + token[len("${HOME}/") :]
    elif token.startswith("~/"):
        token = "$HOME/" + token[2:]
    if not token.startswith("$HOME/"):
        return None
    suffix = posixpath.normpath(token[len("$HOME/") :])
    if suffix == "." or suffix.startswith("../") or suffix == "..":
        return None
    return "$HOME/" + suffix


def _marked_wrapper(command: Any) -> tuple[bool, str | None]:
    if not isinstance(command, str) or not command.startswith(OWNER_PREFIX):
        return False, None
    tail = command[len(OWNER_PREFIX) :]
    try:
        tokens = shlex.split(tail, posix=True)
    except ValueError:
        return True, None
    if len(tokens) != 1:
        return True, None
    normalized = _normalized_wrapper(tokens[0])
    if normalized is None:
        return True, None
    for event, wrapper in EVENT_WRAPPERS.items():
        if normalized == wrapper:
            return True, event
    return True, None


def _is_owned(hook: dict[str, Any], event: str) -> bool:
    marked, wrapper_event = _marked_wrapper(hook.get("command"))
    return marked and wrapper_event == event


def _dedicated_owned_group(group: dict[str, Any], event: str) -> bool:
    entries = group.get("hooks")
    return (
        set(group) == {"hooks"}
        and isinstance(entries, list)
        and bool(entries)
        and all(_is_owned(entry, event) for entry in entries)
    )


def _install_projection(live: dict[str, Any], fragment: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(live)
    hooks = merged.setdefault("hooks", {})
    for event in EVENT_ORDER:
        canonical_group = fragment["hooks"][event][0]
        canonical_hook = canonical_group["hooks"][0]
        groups = hooks.setdefault(event, [])
        seen = False
        next_groups: list[dict[str, Any]] = []
        for group in groups:
            entries = group.get("hooks")
            if entries is None:
                next_groups.append(group)
                continue
            was_dedicated = _dedicated_owned_group(group, event)
            next_entries: list[dict[str, Any]] = []
            removed = False
            for hook in entries:
                if not _is_owned(hook, event):
                    next_entries.append(hook)
                    continue
                if not seen:
                    next_entries.append(copy.deepcopy(canonical_hook))
                    seen = True
                else:
                    removed = True
            group["hooks"] = next_entries
            if removed and not next_entries and was_dedicated:
                continue
            next_groups.append(group)
        if not seen:
            next_groups.append(copy.deepcopy(canonical_group))
        hooks[event] = next_groups
    return merged


def _uninstall_projection(live: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(live)
    hooks = merged.get("hooks")
    if not isinstance(hooks, dict):
        return merged
    for event in EVENT_ORDER:
        groups = hooks.get(event)
        if not isinstance(groups, list):
            continue
        event_removed = False
        next_groups: list[dict[str, Any]] = []
        for group in groups:
            entries = group.get("hooks")
            if entries is None:
                next_groups.append(group)
                continue
            was_dedicated = _dedicated_owned_group(group, event)
            next_entries = [entry for entry in entries if not _is_owned(entry, event)]
            removed = len(next_entries) != len(entries)
            event_removed = event_removed or removed
            group["hooks"] = next_entries
            if removed and not next_entries and was_dedicated:
                continue
            next_groups.append(group)
        if event_removed and not next_groups:
            del hooks[event]
        else:
            hooks[event] = next_groups
    return merged


def _check_findings(live: dict[str, Any], fragment: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    hooks = live.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}

    owned: dict[str, list[dict[str, Any]]] = {event: [] for event in EVENT_ORDER}
    for actual_event, groups in hooks.items():
        for group_index, group in enumerate(groups):
            for hook_index, hook in enumerate(group.get("hooks", [])):
                marked, wrapper_event = _marked_wrapper(hook.get("command"))
                if not marked:
                    continue
                if wrapper_event != actual_event or actual_event not in EVENT_ORDER:
                    findings.append(
                        {
                            "kind": "foreign-conflict",
                            "event": actual_event,
                            "group": group_index,
                            "hook": hook_index,
                            "message": "owner marker has an unknown or event-mismatched wrapper",
                        }
                    )
                    continue
                owned[actual_event].append(hook)

    for event in EVENT_ORDER:
        entries = owned[event]
        if not entries:
            findings.append(
                {"kind": "missing", "event": event, "message": "canonical hook is absent"}
            )
            continue
        if len(entries) > 1:
            findings.append(
                {
                    "kind": "duplicate",
                    "event": event,
                    "count": len(entries),
                    "message": "multiple owned hooks are installed",
                }
            )
        canonical = fragment["hooks"][event][0]["hooks"][0]
        if entries[0] != canonical:
            findings.append(
                {"kind": "stale", "event": event, "message": "owned hook differs from master"}
            )
    return findings


def _state_home(raw: str | None) -> Path:
    if raw:
        return _absolute_path(raw, "state home")
    configured = os.environ.get("XDG_STATE_HOME")
    if configured:
        return _absolute_path(configured, "XDG_STATE_HOME")
    home = os.environ.get("HOME")
    if not home:
        raise ProjectorError("HOME or XDG_STATE_HOME is required for mutation")
    return _absolute_path(str(Path(home) / ".local" / "state"), "state home")


@contextlib.contextmanager
def _projector_lock(state_home: Path) -> Iterator[LockedState]:
    state_fd = _open_absolute_directory(state_home, "state home", create_missing=True)
    if state_fd is None:
        raise AssertionError("create_missing directory traversal returned no descriptor")
    current_fd = state_fd
    hook_install_fd = -1
    snapshots_fd = -1
    lock_fd = -1
    try:
        for name in ("pjangler", "notebook", "v1", "hook-install"):
            child_fd = _open_private_directory_at(current_fd, name, "state directory")
            os.close(current_fd)
            current_fd = child_fd
        hook_install_fd = current_fd
        current_fd = -1
        snapshots_fd = _open_private_directory_at(
            hook_install_fd, "snapshots", "snapshot directory"
        )
        flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        try:
            lock_fd = os.open("lock", flags, 0o600, dir_fd=hook_install_fd)
        except (OSError, TypeError) as exc:
            detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
            raise ProjectorError(
                f"cannot open descriptor-relative projector lock: {detail}"
            ) from exc
        info = os.fstat(lock_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise ProjectorError("projector lock must be a current-user regular file")
        os.fchmod(lock_fd, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield LockedState(hook_install_fd, snapshots_fd)
    finally:
        if lock_fd >= 0:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)
        if snapshots_fd >= 0:
            os.close(snapshots_fd)
        if hook_install_fd >= 0:
            os.close(hook_install_fd)
        if current_fd >= 0:
            os.close(current_fd)


def _atomic_write_at(parent_fd: int, name: str, raw: bytes, mode: int) -> None:
    name = _leaf_name(name, "atomic write target")
    temporary_name = ""
    descriptor = -1
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    for _ in range(16):
        candidate = f".{name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
        try:
            descriptor = os.open(candidate, flags, mode, dir_fd=parent_fd)
        except FileExistsError:
            continue
        except (OSError, TypeError) as exc:
            detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
            raise ProjectorError(
                f"cannot create descriptor-relative temporary file: {detail}"
            ) from exc
        temporary_name = candidate
        break
    if descriptor < 0:
        raise ProjectorError("cannot allocate a unique descriptor-relative temporary file")
    try:
        os.fchmod(descriptor, mode)
        written = 0
        while written < len(raw):
            count = os.write(descriptor, raw[written:])
            if count <= 0:
                raise ProjectorError("short write to descriptor-relative temporary file")
            written += count
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        try:
            os.replace(
                temporary_name,
                name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
        except (OSError, TypeError) as exc:
            detail = exc.strerror if isinstance(exc, OSError) else "unsupported API"
            raise ProjectorError(f"descriptor-relative atomic replace failed: {detail}") from exc
        temporary_name = ""
        os.fsync(parent_fd)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_name:
            try:
                os.unlink(temporary_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass


def _same_generation_at(parent_fd: int, name: str, expected: Generation) -> bool:
    raw, _, actual = _read_target_at(parent_fd, name)
    del raw
    return actual == expected


def _write_snapshot(snapshots_fd: int, raw: bytes) -> str:
    digest = hashlib.sha256(raw).hexdigest()
    name = f"{digest}.json"
    try:
        descriptor, information = _open_regular_at(snapshots_fd, name, "recovery snapshot")
    except FileNotFoundError:
        _atomic_write_at(snapshots_fd, name, raw, 0o600)
    else:
        try:
            existing = _read_descriptor(descriptor, information.st_size, "recovery snapshot")
        finally:
            os.close(descriptor)
        if existing != raw:
            raise ProjectorError("content-addressed recovery snapshot collision")
        if stat.S_IMODE(information.st_mode) != 0o600:
            raise ProjectorError("recovery snapshot must be mode 0600")
    return name


def _mutate(
    operation: str,
    master_path: Path,
    fragment_path: Path,
    target: Path,
    state_home: Path,
) -> bool:
    fragment = _load_assets(master_path, fragment_path)
    _read_target(target)  # Preflight JSON before creating lock or recovery state.
    with _projector_lock(state_home) as locked:
        target_parent_fd = _open_absolute_directory(
            target.parent,
            "Claude settings parent",
            create_missing=True,
            require_final_owner=True,
        )
        if target_parent_fd is None:
            raise AssertionError("create_missing target traversal returned no descriptor")
        try:
            raw, live, generation = _read_target_at(
                target_parent_fd, target.name
            )  # Required under-lock re-read.
            if operation == "install":
                desired = _install_projection(live, fragment)
            elif operation == "uninstall":
                desired = _uninstall_projection(live)
            else:
                raise AssertionError(operation)
            if desired == live:
                return False
            if not _same_generation_at(target_parent_fd, target.name, generation):
                raise ProjectorError("Claude settings changed concurrently; retry")
            snapshot_raw = raw if generation.exists else b"{}\n"
            _write_snapshot(locked.snapshots_fd, snapshot_raw)
            if not _same_generation_at(target_parent_fd, target.name, generation):
                raise ProjectorError("Claude settings changed concurrently; retry")
            _atomic_write_at(
                target_parent_fd,
                target.name,
                _deterministic_bytes(desired),
                0o600,
            )
            return True
        finally:
            os.close(target_parent_fd)


def _render(master_path: Path, fragment_path: Path) -> bool:
    _, expected = _load_master(master_path)
    parent_fd = _open_absolute_directory(
        fragment_path.parent,
        "generated fragment parent",
        create_missing=False,
        require_final_owner=True,
    )
    if parent_fd is None:
        raise ProjectorError("generated fragment parent does not exist")
    try:
        try:
            current = _read_regular_at_bytes(
                parent_fd, fragment_path.name, "Claude generated fragment"
            )
        except FileNotFoundError:
            current = None
        if current is not None:
            _parse_json_object(current, "Claude generated fragment")
            if current == expected:
                return False
        _atomic_write_at(parent_fd, fragment_path.name, expected, 0o644)
        return True
    finally:
        os.close(parent_fd)


def _check(master_path: Path, fragment_path: Path, target: Path) -> list[dict[str, Any]]:
    master, expected = _load_master(master_path)
    fragment, fragment_raw = _load_fragment(fragment_path)
    findings: list[dict[str, Any]] = []
    if fragment != master or fragment_raw != expected:
        findings.append(
            {
                "kind": "stale",
                "event": "generated-fragment",
                "message": "generated fragment differs from hook master",
            }
        )
    _, live, _ = _read_target(target)
    findings.extend(_check_findings(live, master))
    return findings


def _add_asset_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--master", default=str(DEFAULT_MASTER), help="absolute hook master")
    parser.add_argument(
        "--fragment", default=str(DEFAULT_FRAGMENT), help="absolute generated fragment"
    )


def _add_target_argument(parser: argparse.ArgumentParser) -> None:
    default = os.environ.get(
        "PJ_PROJECT_NOTEBOOK_CLAUDE_SETTINGS", str(Path.home() / ".claude" / "settings.json")
    )
    parser.add_argument("--target", default=default, help="absolute Claude settings target")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    render = commands.add_parser("render", help="render the deterministic Claude fragment")
    _add_asset_arguments(render)

    check = commands.add_parser("check", help="report hook projection drift without writes")
    _add_asset_arguments(check)
    _add_target_argument(check)
    check.add_argument("--json", action="store_true", help="emit a machine-readable result")

    for name in ("install", "uninstall"):
        command = commands.add_parser(name, help=f"{name} only recognized Project Notebook hooks")
        _add_asset_arguments(command)
        _add_target_argument(command)
        command.add_argument(
            "--state-home",
            help="absolute XDG state home override (tests and packaged installers)",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        master_path = _absolute_path(args.master, "hook master")
        fragment_path = _absolute_path(args.fragment, "generated fragment")
        if master_path == fragment_path:
            raise ProjectorError("hook master and generated fragment must be distinct")

        if args.command == "render":
            changed = _render(master_path, fragment_path)
            print(f"project-hooks: render {'changed' if changed else 'up to date'}")
            return 0

        target = _absolute_path(args.target, "Claude settings target")
        if target in (master_path, fragment_path):
            raise ProjectorError("Claude settings target must be distinct from skill assets")
        if args.command == "check":
            findings = _check(master_path, fragment_path, target)
            if args.json:
                print(
                    json.dumps(
                        {"ok": not findings, "findings": findings},
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                )
            elif findings:
                for finding in findings:
                    print(
                        f"project-hooks: {finding['kind']}: {finding['event']}: "
                        f"{finding['message']}"
                    )
            else:
                print("project-hooks: check clean")
            return 0 if not findings else 1

        state_home = _state_home(args.state_home)
        changed = _mutate(args.command, master_path, fragment_path, target, state_home)
        print(f"project-hooks: {args.command} {'changed' if changed else 'up to date'}")
        return 0
    except (OSError, ProjectorError) as exc:
        message = exc.strerror if isinstance(exc, OSError) and exc.strerror else str(exc)
        print(f"project-hooks: error: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
