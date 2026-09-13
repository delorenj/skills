#!/usr/bin/env python3
"""Read-only audit of effective Git ignore policy and index parity."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


def git(
    repo: Path,
    *args: str,
    input_bytes: bytes | None = None,
    allowed: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in allowed:
        detail = os.fsdecode(result.stderr).strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result


def decode(value: bytes) -> str:
    return os.fsdecode(value)


def split_nul(value: bytes) -> list[bytes]:
    parts = value.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


def repo_root(subject: Path) -> Path:
    result = git(subject, "rev-parse", "--path-format=absolute", "--show-toplevel")
    return Path(decode(result.stdout).strip())


def global_ignore(repo: Path) -> tuple[Path, str]:
    configured = git(
        repo,
        "config",
        "--path",
        "--get",
        "core.excludesFile",
        allowed=(0, 1),
    )
    if configured.returncode == 0:
        path = Path(decode(configured.stdout).strip()).expanduser()
        shown = git(
            repo,
            "config",
            "--show-origin",
            "--path",
            "--get",
            "core.excludesFile",
        )
        return path, decode(shown.stdout).strip()

    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_home).expanduser() if xdg_home else Path.home() / ".config"
    path = base / "git" / "ignore"
    return path, "implicit XDG Git default"


def tracked_paths(repo: Path) -> list[bytes]:
    result = git(repo, "ls-files", "-z")
    return split_nul(result.stdout)


def tracked_ignored(repo: Path) -> list[dict[str, Any]]:
    result = git(
        repo,
        "ls-files",
        "--cached",
        "--ignored",
        "--exclude-standard",
        "-z",
    )
    paths = split_nul(result.stdout)
    if not paths:
        return []

    explained = git(
        repo,
        "check-ignore",
        "--verbose",
        "--no-index",
        "-z",
        "--stdin",
        input_bytes=b"\0".join(paths) + b"\0",
        allowed=(0, 1),
    )
    fields = split_nul(explained.stdout)
    if len(fields) % 4:
        raise RuntimeError("unexpected NUL record shape from git check-ignore")

    reasons: dict[bytes, tuple[bytes, bytes, bytes]] = {}
    for index in range(0, len(fields), 4):
        source, line, pattern, path = fields[index : index + 4]
        reasons[path] = (source, line, pattern)

    entries: list[dict[str, Any]] = []
    for raw_path in paths:
        source, line, pattern = reasons.get(raw_path, (b"", b"", b""))
        relative = decode(raw_path)
        entries.append(
            {
                "path": relative,
                "source": decode(source),
                "line": int(line) if line.isdigit() else None,
                "pattern": decode(pattern),
                "worktree_present": os.path.lexists(repo / relative),
            }
        )
    return entries


def active_patterns(path: Path) -> list[tuple[int, str]]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()
    return [
        (number, line)
        for number, line in enumerate(lines, start=1)
        if line and not line.startswith("#")
    ]


def ignore_files(repo: Path) -> list[Path]:
    found: list[Path] = []
    for raw_path in tracked_paths(repo):
        relative = decode(raw_path)
        if PurePosixPath(relative).name == ".gitignore":
            found.append(repo / relative)
    root_ignore = repo / ".gitignore"
    if root_ignore.is_file() and root_ignore not in found:
        found.append(root_ignore)
    return sorted(found)


def exact_overlaps(repo: Path, global_path: Path) -> list[dict[str, Any]]:
    global_lines: dict[str, list[int]] = {}
    for number, pattern in active_patterns(global_path):
        global_lines.setdefault(pattern, []).append(number)

    overlaps: list[dict[str, Any]] = []
    for ignore_file in ignore_files(repo):
        for number, pattern in active_patterns(ignore_file):
            if pattern in global_lines:
                overlaps.append(
                    {
                        "file": str(ignore_file.relative_to(repo)),
                        "line": number,
                        "pattern": pattern,
                        "global_lines": global_lines[pattern],
                    }
                )
    return overlaps


def build_report(subject: Path) -> dict[str, Any]:
    root = repo_root(subject)
    global_path, origin = global_ignore(root)
    return {
        "repo": str(root),
        "global_ignore": {
            "path": str(global_path),
            "origin": origin,
            "exists": global_path.is_file(),
        },
        "gitignore_files": [str(path.relative_to(root)) for path in ignore_files(root)],
        "exact_overlaps": exact_overlaps(root, global_path),
        "tracked_ignored": tracked_ignored(root),
    }


def print_human(report: dict[str, Any]) -> None:
    global_data = report["global_ignore"]
    print(f"repo: {report['repo']}")
    print(
        "global ignore: "
        f"{global_data['path']} ({global_data['origin']}; "
        f"{'present' if global_data['exists'] else 'missing'})"
    )

    print("\nexact repo/global pattern overlaps:")
    overlaps = report["exact_overlaps"]
    if not overlaps:
        print("  none")
    for entry in overlaps:
        global_lines = ",".join(str(line) for line in entry["global_lines"])
        print(
            f"  {entry['file']}:{entry['line']} {entry['pattern']} "
            f"(global line {global_lines})"
        )

    print("\ntracked paths matched by effective ignore rules:")
    ignored = report["tracked_ignored"]
    if not ignored:
        print("  none")
    for entry in ignored:
        location = entry["source"]
        if entry["line"] is not None:
            location += f":{entry['line']}"
        presence = "present" if entry["worktree_present"] else "missing"
        print(f"  {entry['path']} <- {location} {entry['pattern']} [{presence}]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository path")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args.repo.resolve())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
