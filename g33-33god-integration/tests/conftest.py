"""Shared fixtures: build a fresh BMAD project with the REAL upstream resolver."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]  # .../skillex
MODULE_ROOT = REPO_ROOT / "all-skills" / "g33-33god-integration"
UPSTREAM_SCRIPTS = REPO_ROOT / "_bmad" / "scripts"

sys.path.insert(0, str(MODULE_ROOT / "scripts"))


def clean_env() -> dict[str, str]:
    """Subprocess env without PYTHONSAFEPATH (which breaks the upstream
    resolver's sibling import of config_utils) and without bytecode writes."""
    env = dict(os.environ)
    env.pop("PYTHONSAFEPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


@pytest.fixture()
def bmad_project(tmp_path: Path) -> Path:
    """Fresh temp BMAD project with the REAL upstream resolver scripts and a
    base _bmad/config.toml install."""
    root = tmp_path / "proj"
    (root / "_bmad" / "scripts").mkdir(parents=True)
    (root / "_bmad" / "custom").mkdir(parents=True)
    for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
        shutil.copy2(UPSTREAM_SCRIPTS / name, root / "_bmad" / "scripts" / name)
    (root / "_bmad" / "config.toml").write_text(
        "# base install\n[core]\noutput_folder = \"{project-root}/_bmad-output\"\n",
        encoding="utf-8",
    )
    # authoring-layer YAML with an operator section that must survive
    (root / "_bmad" / "config.yaml").write_text(
        "# operator-authored config\n"
        "document_output_language: English\n"
        "output_folder: \"{project-root}/_bmad-output\"\n"
        "\n"
        "bmm:\n"
        "  # operator comment that must survive\n"
        "  planning_artifacts: \"{project-root}/_bmad-output/planning-artifacts\"\n",
        encoding="utf-8",
    )
    # existing help CSV with another module's rows (bmb header variant) on
    # the ACTIVE surface _bmad/_config/bmad-help.csv (real installed layout)
    (root / "_bmad" / "_config").mkdir(parents=True, exist_ok=True)
    (root / "_bmad" / "_config" / "bmad-help.csv").write_text(
        "module,skill,display-name,menu-code,description,action,args,phase,"
        "preceded-by,followed-by,required,output-location,outputs\n"
        "BMad Builder,bmad-bmb-setup,Setup Builder Module,SB,\"Install or update.\","
        "configure,\"{-H}\",anytime,,,false,{project-root}/_bmad,config.yaml\n",
        encoding="utf-8",
    )
    return root


def install(project_root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MODULE_ROOT / "scripts" / "g33_install.py"),
         "--project-root", str(project_root), *extra],
        capture_output=True, text=True, check=False, env=clean_env(),
    )


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MODULE_ROOT / "scripts" / "g33_cli.py"), *args],
        capture_output=True, text=True, check=False, env=clean_env(),
    )


def resolve_config(project_root: Path, *keys: str) -> dict:
    proc = subprocess.run(
        [sys.executable,
         str(project_root / "_bmad" / "scripts" / "resolve_config.py"),
         "--project-root", str(project_root), *sum((["--key", k] for k in keys), [])],
        capture_output=True, text=True, check=False, env=clean_env(),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def write_project_json(root: Path, doc: dict) -> None:
    (root / ".project.json").write_text(json.dumps(doc, indent=2), encoding="utf-8")
