"""Repair regressions: real owner API, upstream resolvers, and write boundaries."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from conftest import MODULE_ROOT, REPO_ROOT, clean_env, install
import g33lib as G
import g33_install as I
from test_followup_regressions import test_reference_only_fixture_activation as activate_fixture


def snapshot(root):
    """Hash tree entries without following symlink directories or dangling leaves."""
    entries = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(base) / name
            rel = str(path.relative_to(root))
            entries[rel] = ("link:" + os.readlink(path) if path.is_symlink()
                            else "dir" if path.is_dir()
                            else hashlib.sha256(path.read_bytes()).hexdigest())
    return entries


def stage_skill(root, skill="bmad-build"):
    dest = root / ".agents" / "skills" / skill
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(REPO_ROOT / "all-skills" / skill, target_is_directory=True)
    return dest


def bridge(root, operation, options=None, env=None):
    proc = subprocess.run([
        shutil.which("node") or "node", str(MODULE_ROOT / "scripts/g33_bridge_call.mjs"),
        json.dumps({"schemaVersion": 1, "moduleId": "g33", "operation": operation,
                    "projectRoot": str(root), "reason": "repair", "options": options or {}}),
    ], capture_output=True, text=True, env=env or clean_env())
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_R0_activation_ignores_poisoned_home(tmp_path, monkeypatch):
    poison = tmp_path / "poison-home"
    (poison / ".agents").mkdir(parents=True)
    (poison / ".agents/skills.json").write_text(json.dumps({
        "sets": ["intentionally-missing-g33-regression-set"], "skills": [],
        "inherit_global": False,
    }))
    monkeypatch.setenv("HOME", str(poison))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(poison / ".config"))
    activate_fixture(tmp_path)
    assert not (poison / ".agents/skills").exists()


@pytest.mark.parametrize("proof", [
    "3 passed\nexit_code=1\n", "3 passed\nexit_code=0\nexit_code=1\n",
    "3 passed\ncommand_exit_code=2\n", "3 passed\nexit_code=-1\n",
    "block A\n2 passed\nexit_code=0\nblock B\n1 passed\nexit_code=2\n",
])
def test_R1_nonzero_exit_never_certified(tmp_path, proof):
    assert G.parse_test_proof(proof)["clean_pass"] is False
    diff = tmp_path / "d.diff"
    diff.write_text("--- a/a\n+++ b/a\n@@ -1 +1 @@\n-old\n+new\n")
    tests = tmp_path / "tests.log"
    tests.write_text(proof)
    text = G.generate_handoff(MODULE_ROOT, {"diff_path": str(diff), "test_proof_path": str(tests)})
    tested = text.split("## Tested\n")[1].split("## Installed")[0]
    assert "VERIFIED" not in tested
    assert "exit codes" in tested


def test_R1_prose_exit_is_not_proof():
    assert G.parse_test_proof("The desired command should exit 0.")["clean_pass"] is False
    assert G.parse_test_proof("3 passed\nexit_code=0\n")["clean_pass"] is True


@pytest.mark.parametrize("proof", ["3 passed\n", "3 passed\nexit_code=oops\n",
    "block A\n3 passed\nexit_code=0\nblock B\n2 passed\n", "exit_code=0\n",
    "3 passed\nexit_code=0\ncommand_exit_code=not-known\n"])
def test_R1_missing_or_malformed_exit_uncertified(proof):
    assert G.parse_test_proof(proof)["clean_pass"] is False


@pytest.mark.parametrize("rel", [
    "_bmad", "_bmad/_config", "_bmad/custom", "_bmad/config.yaml",
    "_bmad/custom/config.toml", "_bmad/_config/bmad-help.csv",
    *[f"_bmad/custom/{s}.toml" for s in ("bmad-build", "bmad-code-review", "bmad-prd", "bmad-spec", "bmad-architecture")],
])
def test_R2_symlink_ancestors_and_leaves_zero_write(bmad_project, tmp_path, rel):
    for name in ("bmad-build", "bmad-code-review", "bmad-prd", "bmad-spec", "bmad-architecture"):
        stage_skill(bmad_project, name)
    target = bmad_project / rel
    outside = tmp_path / "outside"
    if target.is_dir():
        shutil.move(target, outside)
    else:
        outside.mkdir()
        if target.exists():
            shutil.move(target, outside / target.name)
        outside = outside / target.name
        if not outside.exists():
            outside.write_text("[workflow]\n" if target.suffix == ".toml" else "bystander\n")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(outside, target_is_directory=outside.is_dir())
    before = snapshot(bmad_project), snapshot(tmp_path / "outside")
    proc = install(bmad_project)
    payload = json.loads(proc.stdout)
    assert proc.returncode == 2 and payload["status"] == "conflict", proc.stdout + proc.stderr
    assert payload["conflicts"] and any("symlink" in c["detail"] for c in payload["conflicts"])
    assert before == (snapshot(bmad_project), snapshot(tmp_path / "outside"))


@pytest.mark.parametrize("link", ["../../outside/missing.toml", "/missing-g33-fixture-leaf"])
def test_R2_dangling_and_relative_link_refused(bmad_project, link):
    (bmad_project / "_bmad/custom/config.toml").symlink_to(link)
    before = snapshot(bmad_project)
    proc = install(bmad_project)
    assert proc.returncode == 2, proc.stdout
    assert snapshot(bmad_project) == before


def test_R2_project_root_alias_allowed(bmad_project, tmp_path):
    alias = tmp_path / "root-alias"
    alias.symlink_to(bmad_project, target_is_directory=True)
    assert install(alias).returncode == 0
    assert (bmad_project / "_bmad/custom/config.toml").is_file()


def test_R3_installed_deployed_require_separate_receipts(tmp_path):
    diff = tmp_path / "d.diff"
    diff.write_text("--- a/a\n+++ b/a\n@@ -1 +1 @@\n-a\n+b\n")
    tests = tmp_path / "t.log"
    tests.write_text("3 passed\nexit_code=0\n")
    bundle = {"diff_path": str(diff), "test_proof_path": str(tests),
              "installed": ["fixture installed"], "deployed": ["prod deployed"]}
    text = G.generate_handoff(MODULE_ROOT, bundle)
    assert "claimed-unverified: prod deployed" in text
    assert "claimed-unverified: fixture installed" in text
    for state, claim in (("installed", "fixture installed"), ("deployed", "prod deployed")):
        receipt = tmp_path / f"{state}.json"
        receipt.write_text(json.dumps({"state": state, "claims": [claim],
            "checks": [{"command": "fixture verification", "exit_code": 0, "observed": "expected fixture state"}]}))
        bundle[f"{state}_evidence_path"] = str(receipt)
    text = G.generate_handoff(MODULE_ROOT, bundle)
    assert "deployed receipt VERIFIED" in text and "installed receipt VERIFIED" in text
    bundle["deployed_evidence_path"] = str(tests)
    assert "claimed-unverified: prod deployed" in G.generate_handoff(MODULE_ROOT, bundle)


def test_R4_bridge_plan_answers_parity_and_cleanup(bmad_project, tmp_path):
    stage_skill(bmad_project)
    temp = tmp_path / "bridge-temp"
    temp.mkdir()
    env = {**clean_env(), "TMPDIR": str(temp)}
    options = {"answers": {"ecosystem_root": "custom/# ] ../root", "g33_output_folder": "/custom/output"}}
    before = snapshot(bmad_project)
    planned = bridge(bmad_project, "plan", options, env)
    assert planned["status"] == "planned", planned
    assert any("custom/# ] ../root" in e for e in planned["evidence"]), planned
    assert snapshot(bmad_project) == before and not list(temp.iterdir())
    applied = bridge(bmad_project, "apply", options, env)
    assert applied["status"] == "changed", applied
    actual = tomllib.loads((bmad_project / "_bmad/custom/config.toml").read_text())["modules"]["g33"]
    assert all(actual[k] == v for k, v in options["answers"].items())
    assert not list(temp.iterdir())
    failed = bridge(bmad_project, "plan", {"answers": {"unknown-answer": "bad"}}, env)
    assert failed["status"] == "error" and not list(temp.iterdir())


@pytest.mark.parametrize("options", [{"answers": []}, {"answers": "bad"}, {"moduleRoot": 3}, {"pythonExecutable": False}])
def test_R4_bad_option_values_error(bmad_project, options):
    assert bridge(bmad_project, "plan", options)["status"] == "error"


def test_R5_yaml_only_observe_unavailable(tmp_path):
    root = tmp_path / "yaml-only"
    (root / "_bmad").mkdir(parents=True)
    assert install(root).returncode == 0
    reply = bridge(root, "observe")
    assert reply["status"] == "unavailable", reply
    assert "inactive" in reply["summary"].lower() or "resolver absent" in reply["summary"].lower()


def test_R6_observe_real_customization_merge(bmad_project):
    stage_skill(bmad_project)
    assert install(bmad_project).returncode == 0
    before = snapshot(bmad_project)
    reply = bridge(bmad_project, "observe")
    assert reply["status"] == "installed", reply
    assert any("resolve_customization.py" in e and "g33" in e for e in reply["evidence"]), reply
    assert snapshot(bmad_project) == before
    (bmad_project / "_bmad/custom/bmad-build.toml").write_text("[workflow]\npersistent_facts = []\n")
    assert bridge(bmad_project, "observe")["status"] != "installed"


def test_R7_update_preservation_explicitly_unavailable(bmad_project):
    reply = bridge(bmad_project, "plan")
    assert any("update-preservation" in x and "unavailable" in x for x in reply["details"]), reply
    for rel in ("README.md", "SKILL.md", "assets/module-setup.md"):
        text = (MODULE_ROOT / rel).read_text()
        assert "update-preservation" in text and "unavailable" in text, rel


@pytest.mark.parametrize("value", ['quote"line\n[attack]\nkey = "oops" #', "..", "/absolute/path", "# ]", "tab\tvalue"])
def test_hidden_answers_roundtrip_without_injection(bmad_project, tmp_path, value):
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({"ecosystem_root": value}))
    proc = install(bmad_project, "--answers", str(answers))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    parsed = tomllib.loads((bmad_project / "_bmad/custom/config.toml").read_text())
    assert parsed["modules"]["g33"]["ecosystem_root"] == value
    assert set(parsed) == {"modules"}
    yaml = (bmad_project / "_bmad/config.yaml").read_text()
    line = next(l for l in yaml.splitlines() if l.startswith("  ecosystem_root:"))
    rendered = line.split(":", 1)[1].strip()
    assert (json.loads(rendered) if rendered.startswith('"') else rendered) == value
    assert install(bmad_project, "--answers", str(answers)).returncode == 0


def test_hidden_mid_apply_failure_rolls_back(bmad_project, monkeypatch):
    before = snapshot(bmad_project)
    plan = I.plan_install(bmad_project, False)
    real_replace = os.replace
    calls = 0
    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise PermissionError("injected Nth atomic write failure")
        return real_replace(*args, **kwargs)
    monkeypatch.setattr(os, "replace", fail_second)
    with pytest.raises((OSError, RuntimeError)):
        I.execute_plan(plan, False)
    assert snapshot(bmad_project) == before


def test_hidden_force_preserves_keys_comments_arrays(bmad_project):
    stage_skill(bmad_project)
    assert install(bmad_project).returncode == 0
    cfg = bmad_project / "_bmad/custom/config.toml"
    cfg.write_text(cfg.read_text() + '\n# operator comment\nextra = [\n  "one",\n  "two",\n]\n[modules.g33.nested]\nvalue = "keep"\n')
    override = bmad_project / "_bmad/custom/bmad-build.toml"
    override.write_text(override.read_text().replace("activation_steps_append = []", 'activation_steps_append = ["append-only"]') + '\n# operator note\nunknown = ["unknown-one", "unknown-two"]\n[other]\nkeep = true\n')
    assert install(bmad_project, "--force").returncode == 0
    assert "# operator comment" in cfg.read_text()
    assert tomllib.loads(cfg.read_text())["modules"]["g33"]["extra"] == ["one", "two"]
    assert tomllib.loads(cfg.read_text())["modules"]["g33"]["nested"]["value"] == "keep"
    data = tomllib.loads(override.read_text())
    assert data["workflow"]["unknown"] == ["unknown-one", "unknown-two"]
    assert data["workflow"]["activation_steps_append"] == ["append-only"]
    assert "append-only" not in data["workflow"]["persistent_facts"]
    assert data["other"]["keep"] is True and "# operator note" in override.read_text()
    before = snapshot(bmad_project)
    assert install(bmad_project, "--force").returncode == 0
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("value", [None, ["bad"], {"nested": "bad"}])
def test_hidden_invalid_answer_values_rejected(bmad_project, tmp_path, value):
    path = tmp_path / "invalid-answer.json"
    path.write_text(json.dumps({"ecosystem_root": value}))
    before = snapshot(bmad_project)
    proc = install(bmad_project, "--answers", str(path))
    assert proc.returncode != 0, proc.stdout
    assert snapshot(bmad_project) == before
    assert bridge(bmad_project, "plan", {"answers": {"ecosystem_root": value}})["status"] == "error"


def test_hidden_force_preserves_yaml_blank_sections_and_inline_comments(bmad_project):
    assert install(bmad_project).returncode == 0
    cfg = bmad_project / "_bmad/config.yaml"
    cfg.write_text(cfg.read_text() + '\n  # operator YAML comment\n  extra:\n    - one\n    - two\n')
    toml = bmad_project / "_bmad/custom/config.toml"
    toml.write_text(toml.read_text().replace('ecosystem_root = "."', 'ecosystem_root = "." # operator inline comment'))
    assert install(bmad_project, "--force").returncode == 0
    assert "# operator YAML comment" in cfg.read_text() and "    - two" in cfg.read_text()
    assert "# operator inline comment" in toml.read_text()
