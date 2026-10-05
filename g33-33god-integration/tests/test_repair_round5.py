"""QUALITY Q1–Q4 regressions against real owner and upstream resolver calls."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from conftest import MODULE_ROOT, REPO_ROOT, cli, install, write_project_json
from test_repair_round1 import bridge, snapshot, stage_skill
import g33_install as I
import g33lib as G

SKILLS = ("bmad-build", "bmad-code-review", "bmad-prd", "bmad-spec", "bmad-architecture")
LINKED = {"project_id": "fixture", "ticket_provider": {
    "type": "plane", "state": "linked", "workspace": "33god",
    "board_id": "fixture-board", "identifier": "FIXTURE"}}


def activate(root, module=MODULE_ROOT, surface=".agents/skills"):
    path = root / surface / "g33-33god-integration"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(module, target_is_directory=True)
    return path


def installed(root):
    for name in SKILLS:
        stage_skill(root, name)
    activate(root)
    assert install(root).returncode == 0
    assert bridge(root, "observe")["status"] == "installed"


@pytest.mark.parametrize("skill", SKILLS)
@pytest.mark.parametrize("field", ["activation_steps_prepend", "persistent_facts"])
@pytest.mark.parametrize("replacement", [[], ["g33"], ["g33 disabled by tamper"]])
def test_Q1_required_entries_not_substrings(bmad_project, skill, field, replacement):
    installed(bmad_project)
    path = bmad_project / "_bmad/custom" / f"{skill}.toml"
    required = tomllib.loads(I._override_content(skill))["workflow"]
    required[field] = replacement
    path.write_text("[workflow]\n" + "".join(
        f"{key} = {G.render_toml_value(values)}\n" for key, values in required.items()))
    before = snapshot(bmad_project)
    observed = bridge(bmad_project, "observe")
    assert observed["status"] == "conflict", observed
    assert skill in observed["summary"] and field in observed["summary"], observed
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("skill", SKILLS)
def test_Q1_operator_entries_remain_supported(bmad_project, skill):
    installed(bmad_project)
    path = bmad_project / "_bmad/custom" / f"{skill}.toml"
    expected = tomllib.loads(I._override_content(skill))["workflow"]
    # Reordering, unrelated entries and comments do not invalidate required content.
    path.write_text('# operator additions\n["workflow"] # quoted table\n' + "".join(
        f"{key} = {G.render_toml_value(['operator first', *values, 'operator last'])} # keep\n"
        for key, values in reversed(list(expected.items()))) + 'operator_notes = ["keep"]\n')
    before = snapshot(bmad_project)
    observed = bridge(bmad_project, "observe")
    assert observed["status"] == "installed", observed
    assert any(skill in evidence and "resolve_customization.py" in evidence
               for evidence in observed["evidence"])
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("tamper", ["missing", "foreign", "copied", "identical-copy", "body-only", "dangling"])
def test_Q3_canonical_activation_required(bmad_project, tmp_path, tamper):
    installed(bmad_project)
    binding = bmad_project / ".agents/skills/g33-33god-integration"
    binding.unlink()
    if tamper == "foreign":
        binding.symlink_to(REPO_ROOT / "all-skills/bmad-build", target_is_directory=True)
    elif tamper in ("copied", "identical-copy", "body-only"):
        binding.mkdir()
        if tamper == "body-only":
            (binding / "SKILL.md").symlink_to(MODULE_ROOT / "SKILL.md")
        else:
            (binding / "SKILL.md").write_text(
                (MODULE_ROOT / "SKILL.md").read_text() if tamper == "identical-copy"
                else "# irrelevant copied skill\n")
    elif tamper == "dangling":
        binding.symlink_to(tmp_path / "missing-source", target_is_directory=True)
    before = snapshot(bmad_project)
    observed = bridge(bmad_project, "observe")
    assert observed["status"] in ("missing", "conflict"), observed
    assert "activation" in observed["summary"].lower(), observed
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("surface", [".agents/skills", "skills", "_bmad/skills"])
def test_Q3_supported_activation_surfaces(bmad_project, surface):
    stage_skill(bmad_project)
    activate(bmad_project, surface=surface)
    assert install(bmad_project).returncode == 0
    before = snapshot(bmad_project)
    observed = bridge(bmad_project, "observe")
    assert observed["status"] == "installed", observed
    assert any("canonical" in evidence and "activation" in evidence
               and surface in evidence for evidence in observed["evidence"]), observed
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("earlier", [".agents/skills", "skills"])
def test_Q3_earlier_foreign_binding_not_hidden_by_fallback(bmad_project, earlier):
    stage_skill(bmad_project)
    activate(bmad_project, surface="_bmad/skills")
    activate(bmad_project, module=REPO_ROOT / "all-skills/bmad-build", surface=earlier)
    assert install(bmad_project).returncode == 0
    before = snapshot(bmad_project)
    observed = bridge(bmad_project, "observe")
    assert observed["status"] == "conflict", observed
    assert earlier in observed["summary"] or any(earlier in x for x in observed["details"])
    assert snapshot(bmad_project) == before


def test_Q3_relocated_source_and_relative_activation(bmad_project, tmp_path):
    moved = tmp_path / "relocated-module"
    shutil.copytree(MODULE_ROOT, moved, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    stage_skill(bmad_project)
    binding = bmad_project / ".agents/skills/g33-33god-integration"
    binding.symlink_to("../../../relocated-module", target_is_directory=True)
    options = {"moduleRoot": str(moved), "pythonExecutable": sys.executable}
    assert bridge(bmad_project, "apply", options)["status"] == "changed"
    before = snapshot(bmad_project)
    observed = bridge(bmad_project, "observe", options)
    assert observed["status"] == "installed", observed
    assert snapshot(bmad_project) == before


HEADERS = ['[modules."g33"]', '["modules".g33]', '["modules"."g33"]',
           "['modules'.'g33']", '["mod\\u0075les"."g\\u00333"]',
           '[ modules . "g33" ] # operator header']


@pytest.mark.parametrize("header", HEADERS)
@pytest.mark.parametrize("force", [False, True])
def test_Q2_equivalent_owned_tables_surgical_merge(bmad_project, header, force):
    path = bmad_project / "_bmad/custom/config.toml"
    prefix = '# foreign prefix\n[operator]\nvalue = "unchanged"\n\n'
    nested = '\n["modules"."g33".operator]\nvalue = "keep" # nested\n'
    path.write_text(prefix + header + '\ncode = "g33" # identity\n'
                    'name = "Operator module" # operator name\n# notes comment\n'
                    'notes = [\n "one",\n "two",\n]\n'
                    'message = """\n[modules.g33]\nlooks like a header\n"""\n' + nested)
    before = snapshot(bmad_project)
    args = ("--force",) if force else ()
    dry = install(bmad_project, "--dry-run", *args)
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert json.loads(dry.stdout)["status"] == "ok"
    assert snapshot(bmad_project) == before
    applied = install(bmad_project, *args)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    text = path.read_text()
    parsed = tomllib.loads(text)["modules"]["g33"]
    assert parsed["code"] == "g33" and parsed["notes"] == ["one", "two"]
    assert parsed["operator"] == {"value": "keep"}
    assert parsed["name"] == ("33GOD Integration" if force else "Operator module")
    assert text.startswith(prefix) and text.endswith(nested)
    assert header + "\n" in text and '# notes comment\nnotes = [\n "one",\n "two",\n]\n' in text
    assert '# operator name' in text and '# identity' in text
    converged = snapshot(bmad_project)
    assert install(bmad_project, *args).returncode == 0
    assert snapshot(bmad_project) == converged


@pytest.mark.parametrize("header", HEADERS)
def test_Q2_foreign_equivalent_tables_conflict(bmad_project, header):
    path = bmad_project / "_bmad/custom/config.toml"
    path.write_text(header + '\ncode = "foreign"\n')
    before = snapshot(bmad_project)
    for args in ((), ("--dry-run",), ("--force",)):
        proc = install(bmad_project, *args)
        data = json.loads(proc.stdout)
        assert proc.returncode == 2 and data["status"] == "conflict" and data["conflicts"], data
        assert any("foreign" in x["detail"] for x in data["conflicts"])
        assert snapshot(bmad_project) == before


def canonical_empty_errors():
    return ["execution.mode must be legacy, shadow or managed",
            "execution policy or skill pin missing",
            *[f"lane binding missing: {lane}" for lane in G.EXECUTION_LANES],
            "pilot_bundle_sha256 missing", "momo_bundle_sha256 missing",
            "working label binding missing", "PM actor enrollment missing",
            "controller repair actor enrollment missing", "legacy writers not fenced"]


@pytest.mark.parametrize("value", [{}, [], ["managed"], True, 7, "managed",
                                   {"mode": None}, {"mode": []}, {"mode": {}}])
def test_Q4_truthy_empty_and_malformed_readiness_matches_canonical(value):
    assert G.execution_readiness({**LINKED, "execution": value}) == canonical_empty_errors()


@pytest.mark.parametrize("value", [{}, [], ["managed"], True, False, 7, 0, "managed", "",
                                   {"mode": None}, {"mode": []}, {"mode": {}}])
def test_Q4_present_invalid_execution_never_legacy(bmad_project, value):
    manifest = {**LINKED, "execution": value}
    assert G.execution_mode_status(manifest) == "invalid"
    write_project_json(bmad_project, manifest)
    before = snapshot(bmad_project)
    proc = cli("preflight", "--project-root", str(bmad_project), "--json")
    result = json.loads(proc.stdout)
    enrollment = next(x for x in result["findings"] if x["check"] == "krebs-enrollment")
    assert proc.returncode == 1 and result["execution_mode"] == "invalid", result
    assert enrollment["status"] == "FAIL" and "absent" not in enrollment["evidence"], result
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("value", [None, False, 0, "", {"mode": "legacy"}])
def test_Q4_canonical_falsy_and_explicit_legacy_readiness(value):
    assert G.execution_readiness({**LINKED, "execution": value}) == []


@pytest.mark.parametrize("execution", [None, {"mode": "legacy"}])
def test_Q4_absent_null_and_explicit_legacy_preflight(bmad_project, execution):
    manifest = copy.deepcopy(LINKED)
    if execution is not None:
        manifest["execution"] = execution
    for null in (False, True):
        if null and execution is None:
            manifest["execution"] = None
        assert G.execution_mode_status(manifest) == "legacy"
        write_project_json(bmad_project, manifest)
        proc = cli("preflight", "--project-root", str(bmad_project), "--json")
        result = json.loads(proc.stdout)
        assert proc.returncode == 0 and result["execution_mode"] == "legacy", result
