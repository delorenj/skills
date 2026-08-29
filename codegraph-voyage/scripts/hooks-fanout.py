#!/usr/bin/env python3
"""Render and surgically install CodeGraph Voyage hooks for supported clients."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
MASTER = SKILL_ROOT / "hooks" / "hooks.master.json"
GENERATED = SKILL_ROOT / "hooks" / "generated"
OWNER_ENV = "CODEGRAPH_VOYAGE_HOOK_OWNER"
GENERATED_NAMES = {
    "claude": "claude.settings.json",
    "codex": "codex.hooks.json",
    "hermes": "hermes.hooks.json",
    "hermes_allowlist": "hermes.shell-hooks-allowlist.json",
}


class FanoutError(RuntimeError):
    pass


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _load(path: Path, *, missing: Any = None) -> Any:
    if not path.exists():
        return copy.deepcopy(missing)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FanoutError(f"invalid JSON at {path}: {exc}") from exc


def _master() -> dict[str, Any]:
    value = _load(MASTER)
    if not isinstance(value, dict) or set(value.get("roles", {})) != {
        "session_start", "post_tool", "session_end"
    }:
        raise FanoutError("hooks.master.json has an invalid normalized role set")
    if value.get("owner") != "codegraph-voyage.hooks.v1":
        raise FanoutError("hooks.master.json has an unexpected owner")
    return value


def _command(master: dict[str, Any], role: str) -> str:
    return f'{OWNER_ENV}={master["owner"]} "{master["command"]}" {role}'


def _grouped_fragment(master: dict[str, Any], client: str) -> dict[str, Any]:
    hooks: dict[str, list[dict[str, Any]]] = {}
    mapping = master["clients"][client]["events"]
    for role, event in mapping.items():
        hook = {
            "type": "command",
            "command": _command(master, role),
            "timeout": master["roles"][role]["timeout_seconds"],
        }
        group: dict[str, Any] = {"hooks": [hook]}
        if role == "post_tool":
            group["matcher"] = master["roles"][role]["mutating_tool_matcher"]
        hooks[event] = [group]
    return {"hooks": hooks}


def _hermes_fragments(master: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    hooks: dict[str, list[dict[str, Any]]] = {}
    approvals: list[dict[str, str]] = []
    for role, event in master["clients"]["hermes"]["events"].items():
        command = _command(master, role)
        hooks[event] = [{
            "command": command,
            "timeout": master["roles"][role]["timeout_seconds"],
        }]
        approvals.append({
            "approved_by": master["owner"],
            "command": command,
            "event": event,
        })
    return {"hooks": hooks}, {"approvals": approvals}


def projections(master: dict[str, Any]) -> dict[str, bytes]:
    hermes, allowlist = _hermes_fragments(master)
    return {
        GENERATED_NAMES["claude"]: _json_bytes(_grouped_fragment(master, "claude")),
        GENERATED_NAMES["codex"]: _json_bytes(_grouped_fragment(master, "codex")),
        GENERATED_NAMES["hermes"]: _json_bytes(hermes),
        GENERATED_NAMES["hermes_allowlist"]: _json_bytes(allowlist),
    }


def _reject_symlinks(path: Path, *, include_leaf: bool = True) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    parts = absolute.parts[1:] if absolute.anchor else absolute.parts
    for index, part in enumerate(parts):
        current = current / part
        if not include_leaf and index == len(parts) - 1:
            break
        try:
            information = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(information.st_mode):
            raise FanoutError(f"unsafe symlink in destination path: {current}")
        if index < len(parts) - 1 and not stat.S_ISDIR(information.st_mode):
            raise FanoutError(f"destination parent is not a directory: {current}")


def _write_if_changed(path: Path, data: bytes, *, backup: bool = False) -> bool:
    old = path.read_bytes() if path.is_file() else None
    if old == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and old is not None:
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
    return True


def render() -> int:
    _reject_symlinks(GENERATED)
    expected = projections(_master())
    changed = 0
    for name, data in expected.items():
        changed += _write_if_changed(GENERATED / name, data)
    print(f"render: {'changed' if changed else 'up to date'} ({changed} files)")
    return 0


def _owned(command: Any, owner: str) -> bool:
    return isinstance(command, str) and command.startswith(f"{OWNER_ENV}={owner} ")


def _merge_grouped(live: dict[str, Any], fragment: dict[str, Any], owner: str, uninstall: bool) -> dict[str, Any]:
    result = copy.deepcopy(live)
    hooks = result.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise FanoutError("existing hooks must be an object")
    for event, canonical_groups in fragment["hooks"].items():
        groups = hooks.get(event, [])
        if not isinstance(groups, list):
            raise FanoutError(f"existing hook event {event} must be an array")
        cleaned: list[dict[str, Any]] = []
        for group in groups:
            if not isinstance(group, dict):
                raise FanoutError(f"existing hook group {event} must be an object")
            clone = copy.deepcopy(group)
            entries = clone.get("hooks")
            if isinstance(entries, list):
                clone["hooks"] = [entry for entry in entries if not (
                    isinstance(entry, dict) and _owned(entry.get("command"), owner)
                )]
                if not clone["hooks"] and set(clone) <= {"hooks", "matcher"}:
                    continue
            cleaned.append(clone)
        if not uninstall:
            cleaned.extend(copy.deepcopy(canonical_groups))
        if cleaned:
            hooks[event] = cleaned
        else:
            hooks.pop(event, None)
    if uninstall and not hooks:
        result.pop("hooks", None)
    return result


def _merge_hermes(live: dict[str, Any], fragment: dict[str, Any], owner: str, uninstall: bool) -> dict[str, Any]:
    result = copy.deepcopy(live)
    hooks = result.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise FanoutError("existing Hermes hooks must be an object")
    for event, canonical in fragment["hooks"].items():
        entries = hooks.get(event, [])
        if not isinstance(entries, list):
            raise FanoutError(f"existing Hermes hook event {event} must be an array")
        entries = [entry for entry in entries if not (
            isinstance(entry, dict) and (
                entry.get("owner") == owner or _owned(entry.get("command"), owner)
            )
        )]
        if not uninstall:
            entries.extend(copy.deepcopy(canonical))
        if entries:
            hooks[event] = entries
        else:
            hooks.pop(event, None)
    if uninstall and not hooks:
        result.pop("hooks", None)
    return result


def _merge_allowlist(live: dict[str, Any], fragment: dict[str, Any], owner: str, uninstall: bool) -> dict[str, Any]:
    result = copy.deepcopy(live)
    approvals = result.setdefault("approvals", [])
    if not isinstance(approvals, list):
        raise FanoutError("existing Hermes approvals must be an array")
    approvals = [entry for entry in approvals if not (
        isinstance(entry, dict) and (
            entry.get("owner") == owner or entry.get("approved_by") == owner
            or _owned(entry.get("command"), owner)
        )
    )]
    if not uninstall:
        approvals.extend(copy.deepcopy(fragment["approvals"]))
    if approvals:
        result["approvals"] = approvals
    else:
        result.pop("approvals", None)
    return result


def _destinations(root: Path, master: dict[str, Any]) -> dict[str, Path]:
    return {
        "claude": root / master["clients"]["claude"]["destination"],
        "codex": root / master["clients"]["codex"]["destination"],
        "hermes": root / master["clients"]["hermes"]["destination"],
        "hermes_allowlist": root / master["clients"]["hermes"]["allowlist_destination"],
    }


def _preflight(root: Path, destinations: dict[str, Path]) -> None:
    if not root.is_absolute():
        raise FanoutError("--project-root must be absolute")
    _reject_symlinks(root)
    if not root.is_dir():
        raise FanoutError("--project-root must name an existing real directory")
    for destination in destinations.values():
        try:
            destination.relative_to(root)
        except ValueError as exc:
            raise FanoutError(f"destination escapes project root: {destination}") from exc
        _reject_symlinks(destination)
        backup = destination.with_name(destination.name + ".bak")
        _reject_symlinks(backup)


def mutate(root: Path, *, uninstall: bool) -> int:
    master = _master()
    generated = projections(master)
    destinations = _destinations(root, master)
    _preflight(root, destinations)  # Complete safety pass before any mkdir/write/backup.
    fragments = {key: json.loads(generated[GENERATED_NAMES[key]]) for key in destinations}
    current = {key: _load(path, missing={}) for key, path in destinations.items()}
    merged = {
        "claude": _merge_grouped(current["claude"], fragments["claude"], master["owner"], uninstall),
        "codex": _merge_grouped(current["codex"], fragments["codex"], master["owner"], uninstall),
        "hermes": _merge_hermes(current["hermes"], fragments["hermes"], master["owner"], uninstall),
        "hermes_allowlist": _merge_allowlist(current["hermes_allowlist"], fragments["hermes_allowlist"], master["owner"], uninstall),
    }
    changed = 0
    for key, path in destinations.items():
        value = merged[key]
        # Keep an existing empty object; remove an owned-only file on uninstall.
        if uninstall and not value and path.exists():
            shutil.copy2(path, path.with_name(path.name + ".bak"))
            path.unlink()
            changed += 1
        elif not (uninstall and not value and not path.exists()):
            changed += _write_if_changed(path, _json_bytes(value), backup=True)
    print(f"{'uninstall' if uninstall else 'install'}: {'changed' if changed else 'up to date'} ({changed} files)")
    return 0


def check(root: Path | None) -> int:
    master = _master()
    expected = projections(master)
    findings: list[str] = []
    for name, data in expected.items():
        path = GENERATED / name
        try:
            _reject_symlinks(path)
            actual = path.read_bytes()
        except (OSError, FanoutError):
            actual = None
        if actual != data:
            findings.append(f"generated drift: {path}")
    if root is not None:
        destinations = _destinations(root, master)
        try:
            _preflight(root, destinations)
            current = {key: _load(path, missing={}) for key, path in destinations.items()}
            desired = {
                "claude": _merge_grouped(current["claude"], json.loads(expected[GENERATED_NAMES["claude"]]), master["owner"], False),
                "codex": _merge_grouped(current["codex"], json.loads(expected[GENERATED_NAMES["codex"]]), master["owner"], False),
                "hermes": _merge_hermes(current["hermes"], json.loads(expected[GENERATED_NAMES["hermes"]]), master["owner"], False),
                "hermes_allowlist": _merge_allowlist(current["hermes_allowlist"], json.loads(expected[GENERATED_NAMES["hermes_allowlist"]]), master["owner"], False),
            }
            for key, path in destinations.items():
                if current[key] != desired[key]:
                    findings.append(f"installed drift: {path}")
        except FanoutError as exc:
            findings.append(str(exc))
    if findings:
        print("\n".join(findings))
        return 1
    print("check: clean")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("render", "check", "install", "uninstall"))
    parser.add_argument("--project-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            return render()
        if args.command == "check":
            return check(args.project_root)
        if args.project_root is None:
            raise FanoutError(f"{args.command} requires --project-root")
        return mutate(args.project_root, uninstall=args.command == "uninstall")
    except FanoutError as exc:
        print(f"hooks-fanout: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
