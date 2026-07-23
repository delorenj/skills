#!/usr/bin/env python3
"""Emit a local lifecycle snapshot for BMAD-first CAF work."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


def main() -> None:
    root = Path.cwd()
    data: dict[str, Any] = {
        "project_root": str(root),
        "git": git_snapshot(root),
        "bmad": bmad_snapshot(root),
        "plane": plane_snapshot(root),
    }
    print(json.dumps(data, indent=2, sort_keys=True))


def git_snapshot(root: Path) -> dict[str, Any]:
    return {
        "branch": run(["git", "branch", "--show-current"], root),
        "status_short": run(["git", "status", "--short"], root).splitlines(),
        "remotes": run(["git", "remote", "-v"], root).splitlines(),
    }


def bmad_snapshot(root: Path) -> dict[str, Any]:
    manifest_path = root / "_bmad" / "_config" / "manifest.yaml"
    artifacts = root / "_bmad_output" / "planning-artifacts"
    manifest = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
    modules: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in manifest.splitlines():
        name_match = re.match(r"\s*-\s+name:\s+(.+)", line)
        if name_match:
            if current:
                modules.append(current)
            current = {"name": name_match.group(1).strip()}
            continue
        if current is None:
            continue
        for key in ("version", "source", "channel", "repoUrl", "npmPackage"):
            match = re.match(rf"\s+{key}:\s*(.*)", line)
            if match:
                current[key] = match.group(1).strip()
    if current:
        modules.append(current)

    return {
        "manifest_exists": manifest_path.exists(),
        "installation_version": first_yaml_value(manifest, "version"),
        "last_updated": first_yaml_value(manifest, "lastUpdated"),
        "modules": modules,
        "planning_artifact_count": len(list(artifacts.glob("*.md"))) if artifacts.exists() else 0,
        "story_count": len(list((artifacts / "stories").glob("*.md")))
        if (artifacts / "stories").exists()
        else 0,
    }


def plane_snapshot(root: Path) -> dict[str, Any]:
    env_path = root / ".env"
    keys = set(os.environ)
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                keys.add(line.split("=", 1)[0].strip())
    plane_keys = sorted(key for key in keys if "PLANE" in key.upper())
    return {
        "env_file_exists": env_path.exists(),
        "plane_key_names_present": plane_keys,
        "secrets_redacted": True,
    }


def first_yaml_value(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{key}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def run(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return f"ERROR: {exc}"
    if result.returncode != 0:
        return (result.stderr or result.stdout).strip()
    return result.stdout.strip()


if __name__ == "__main__":
    main()
