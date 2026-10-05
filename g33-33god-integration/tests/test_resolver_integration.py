"""Real-BMAD-project integration: g33 install + REAL upstream override resolver.

Builds a fresh fixture BMAD project containing the REAL upstream scripts
(resolve_config.py / resolve_customization.py / config_utils.py copied from the
skillex repo install), installs g33, then proves:
- the module config is active through the real 4-layer TOML merge
- the per-skill customization resolver (resolve_customization.py) merges the
  g33-written team override over the real bmad-build customize.toml defaults
- operator edits to the team override survive an installer rerun
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import MODULE_ROOT, REPO_ROOT, bmad_project, clean_env, install, write_project_json  # noqa: F401


def resolve_customization(project_root: Path, skill_dir: Path, *keys: str) -> dict:
    proc = subprocess.run(
        [sys.executable,
         str(project_root / "_bmad" / "scripts" / "resolve_customization.py"),
         "--skill", str(skill_dir),
         "--project-root", str(project_root),
         *sum((["--key", k] for k in keys), [])],
        capture_output=True, text=True, check=False, env=clean_env(),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture()
def bmad_build_skill(bmad_project: Path) -> Path:
    """Real bmad-build skill (customize.toml + SKILL.md) staged into the fixture
    project's activation root."""
    skill_dir = bmad_project / ".agents" / "skills" / "bmad-build"
    skill_dir.mkdir(parents=True)
    src = REPO_ROOT / "all-skills" / "bmad-build"
    shutil.copy2(src / "customize.toml", skill_dir / "customize.toml")
    shutil.copy2(src / "SKILL.md", skill_dir / "SKILL.md")
    return skill_dir


def test_customization_resolver_merges_g33_override(bmad_project, bmad_build_skill):
    proc = install(bmad_project)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    merged = resolve_customization(
        bmad_project, bmad_build_skill, "workflow.persistent_facts")
    facts = merged["workflow.persistent_facts"]
    assert any("g33 preflight" in f for f in facts), facts
    prep = resolve_customization(
        bmad_project, bmad_build_skill, "workflow.activation_steps_prepend")
    assert any("g33" in s for s in prep["workflow.activation_steps_prepend"])
    # review layers from the base customize.toml survive the merge
    layers = resolve_customization(
        bmad_project, bmad_build_skill, "workflow.review_layers")
    ids = [l["id"] for l in layers["workflow.review_layers"]]
    assert "blind-hunter" in ids and "edge-case-hunter" in ids


def test_operator_override_edit_survives_rerun(bmad_project, bmad_build_skill):
    assert install(bmad_project).returncode == 0
    override = bmad_project / "_bmad" / "custom" / "bmad-build.toml"
    text = override.read_text(encoding="utf-8")
    # well-formed operator edit: add an entry INSIDE the prepend array
    text = text.replace(
        ',\n]\n\nactivation_steps_append',
        ',\n  "file:{project-root}/docs/team-conventions.md"\n]\n\nactivation_steps_append')
    override.write_text(text, encoding="utf-8")

    proc = install(bmad_project)
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert any("bmad-build.toml" in p["path"] and "preserved" in p["reason"]
               for p in result["preserved"]), result

    # the REAL resolver now shows base defaults + g33 + operator fact, appended
    facts = resolve_customization(
        bmad_project, bmad_build_skill, "workflow.activation_steps_prepend")
    steps = facts["workflow.activation_steps_prepend"]
    assert any("g33" in s for s in steps)
    assert any("team-conventions.md" in s for s in steps)


def test_central_config_four_layer_merge(bmad_project):
    """Full real-resolver dump: base + custom team layer merged, stable."""
    assert install(bmad_project).returncode == 0
    # operator user layer on top must not clobber the team g33 table
    user = bmad_project / "_bmad" / "custom" / "config.user.toml"
    user.write_text("[core]\nuser_name = \"Jarad\"\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(bmad_project / "_bmad" / "scripts" / "resolve_config.py"),
         "--project-root", str(bmad_project)],
        capture_output=True, text=True, check=False, env=clean_env())
    assert proc.returncode == 0, proc.stderr
    merged = json.loads(proc.stdout)
    assert merged["modules"]["g33"]["code"] == "g33"
    assert merged["core"]["user_name"] == "Jarad"
    assert merged["core"]["output_folder"] == "{project-root}/_bmad-output"

    proc2 = subprocess.run(
        [sys.executable, str(bmad_project / "_bmad" / "scripts" / "resolve_config.py"),
         "--project-root", str(bmad_project)],
        capture_output=True, text=True, check=False, env=clean_env())
    assert json.loads(proc2.stdout) == merged  # deterministic roundtrip
