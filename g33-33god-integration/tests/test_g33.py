"""g33 module: unit + installer + CLI tests (real upstream resolver fixtures)."""

from __future__ import annotations

import csv
import io
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from conftest import MODULE_ROOT, REPO_ROOT, cli, install, resolve_config, write_project_json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import g33lib as G  # noqa: E402


LINKED_BINDING = {
    "project_id": "demo",
    "ticket_provider": {"type": "plane", "state": "linked",
                        "workspace": "w", "board_id": "b"},
}


# ------------------------------------------------------------- structure/identity

def test_module_yaml_identity():
    module = G.load_module_yaml(MODULE_ROOT / "assets" / "module.yaml")
    assert module["code"] == "g33"
    assert module["name"] == "33GOD Integration"
    assert str(module["module_version"]) == "1.1.0"
    assert module.get("default_selected") is False
    assert "description" in module and module["description"]


def test_skill_md_name_matches_dir():
    text = (MODULE_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\nname: g33-33god-integration\n")


def test_validate_module_script():
    validator = REPO_ROOT / "all-skills" / "bmad-module-builder" / "scripts" / "validate-module.py"
    proc = subprocess.run([sys.executable, str(validator), str(MODULE_ROOT)],
                          capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload.get("status") in ("pass", "success"), payload
    assert not [i for i in payload.get("issues", []) if i.get("severity") == "high"]


def test_ecosystem_map_portable():
    with (MODULE_ROOT / "assets" / "ecosystem-map.toml").open("rb") as f:
        cmap = tomllib.load(f)
    routes = cmap["routes"]
    assert routes, "owner map has no routes"
    for name, node in routes.items():
        assert node.get("owner"), f"route {name} missing owner"
        assert node.get("entrypoint"), f"route {name} missing entrypoint"
        for value in (str(node.get("entrypoint")), str(node.get("notes", "")),
                      str(node.get("owner"))):
            assert "/home/" not in value, f"route {name} is not portable: {value}"


def test_help_and_version_exit_zero():
    for script in ("g33_install.py", "g33_cli.py"):
        proc = subprocess.run(
            [sys.executable, str(MODULE_ROOT / "scripts" / script), "--help"],
            capture_output=True, text=True, check=False)
        assert proc.returncode == 0, script
    proc = cli("--version")
    assert proc.returncode == 0
    assert G.MODULE_VERSION in proc.stdout


# ------------------------------------------------------------------- installer

def test_dry_run_writes_nothing(bmad_project):
    before = {p: p.read_bytes() for p in bmad_project.rglob("*") if p.is_file()}
    proc = install(bmad_project, "--dry-run")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    plan = json.loads(proc.stdout)
    assert plan["dry_run"] is True
    targets = {Path(a["path"]).name for a in plan["actions"]}
    assert {"config.yaml", "bmad-help.csv", "config.toml"} <= targets
    after = {p: p.read_bytes() for p in bmad_project.rglob("*") if p.is_file()}
    assert before == after, "dry-run mutated files"


def test_fresh_install_and_real_resolver(bmad_project):
    for skill in ("bmad-build", "bmad-code-review"):
        d = bmad_project / ".agents" / "skills" / skill
        d.mkdir(parents=True)
        shutil.copy2(REPO_ROOT / "all-skills" / skill / "customize.toml",
                     d / "customize.toml")
    proc = install(bmad_project)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)
    assert result["status"] == "ok"
    assert result["module"] == "g33"

    # YAML layer: g33 section added, operator section byte-preserved
    cfg = (bmad_project / "_bmad" / "config.yaml").read_text(encoding="utf-8")
    assert "\ng33:\n" in cfg
    assert "bmm:" in cfg
    assert "# operator comment that must survive" in cfg
    assert 'planning_artifacts: "{project-root}/_bmad-output/planning-artifacts"' in cfg
    # core keys not duplicated
    assert cfg.count("document_output_language:") == 1

    # CSV layer: ACTIVE surface _bmad/_config/bmad-help.csv (resolver layout)
    csv_text = (bmad_project / "_bmad" / "_config" / "bmad-help.csv").read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert any(r["module"] == "BMad Builder" for r in rows)
    g33_rows = [r for r in rows if r["module"] == "33GOD Integration"]
    assert len(g33_rows) == 4
    assert {r["menu-code"] for r in g33_rows} == {"PF", "ER", "EH", "SU"}

    # TOML team layer + REAL upstream resolver activation
    merged = resolve_config(bmad_project, "modules.g33")
    assert merged["modules.g33"]["code"] == "g33"
    assert merged["modules.g33"]["name"] == "33GOD Integration"
    # base config survives the merge
    merged_all = resolve_config(bmad_project, "core")
    assert merged_all["core"]["output_folder"] == "{project-root}/_bmad-output"

    # override files exist
    for name in ("bmad-build.toml", "bmad-code-review.toml"):
        p = bmad_project / "_bmad" / "custom" / name
        assert p.is_file()
        with p.open("rb") as f:
            tomllib.load(f)  # parses


def test_idempotent_rerun(bmad_project):
    assert install(bmad_project).returncode == 0
    snap = {p: p.read_bytes() for p in bmad_project.rglob("*") if p.is_file()}
    proc = install(bmad_project)
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert all(a["action"] == "already-present" for a in result["actions"]), result
    snap2 = {p: p.read_bytes() for p in bmad_project.rglob("*") if p.is_file()}
    assert snap == snap2


def test_operator_edits_preserved_then_force(bmad_project):
    assert install(bmad_project).returncode == 0
    custom = bmad_project / "_bmad" / "custom" / "config.toml"
    text = custom.read_text(encoding="utf-8").replace(
        'ecosystem_root = "."', 'ecosystem_root = "vendor/33GOD"')
    custom.write_text(text, encoding="utf-8")
    cfg = bmad_project / "_bmad" / "config.yaml"
    cfg_text = cfg.read_text(encoding="utf-8").replace(
        "ecosystem_root: .", 'ecosystem_root: "my/ecosystem"')
    cfg.write_text(cfg_text, encoding="utf-8")

    proc = install(bmad_project)
    assert proc.returncode == 0
    # operator-edited managed value survives non-force rerun (convergent merge
    # keeps operator value; only absent managed keys are re-emitted)
    assert 'ecosystem_root = "vendor/33GOD"' in custom.read_text(encoding="utf-8")
    assert 'ecosystem_root: "my/ecosystem"' in cfg.read_text(encoding="utf-8")

    # operator-added unknown key (F5)
    custom.write_text(
        custom.read_text(encoding="utf-8") + 'operator_extra = "keep-me"\n',
        encoding="utf-8")

    proc = install(bmad_project, "--force")
    assert proc.returncode == 0
    text = custom.read_text(encoding="utf-8")
    assert 'ecosystem_root = "."' in text
    # --force re-emits managed keys but operator EXTRA keys survive (F5)
    assert "operator_extra" in text


def test_operator_edited_override_preserved(bmad_project):
    d = bmad_project / ".agents" / "skills" / "bmad-build"
    d.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "all-skills" / "bmad-build" / "customize.toml",
                 d / "customize.toml")
    assert install(bmad_project).returncode == 0
    override = bmad_project / "_bmad" / "custom" / "bmad-build.toml"
    edited = override.read_text(encoding="utf-8").replace(
        ',\n]\n\nactivation_steps_append',
        ',\n  "OPERATOR EXTRA FACT"\n]\n\nactivation_steps_append')
    override.write_text(edited, encoding="utf-8")
    proc = install(bmad_project)
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert any("bmad-build.toml" in p["path"] and "preserved" in p["reason"]
               for p in result["preserved"]), result
    assert override.read_text(encoding="utf-8") == edited


def test_resolver_roundtrip_stable(bmad_project):
    assert install(bmad_project).returncode == 0
    first = resolve_config(bmad_project)
    second = resolve_config(bmad_project)
    assert first == second


def test_missing_resolver_refuses_toml(tmp_path):
    root = tmp_path / "proj2"
    (root / "_bmad").mkdir(parents=True)
    (root / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
    proc = install(root)
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert any("UNSUPPORTED/INACTIVE" in w for w in result["warnings"])
    assert not (root / "_bmad" / "custom" / "config.toml").exists()
    assert not (root / "_bmad" / "custom" / "bmad-build.toml").exists()


def test_rejects_non_bmad_target(tmp_path):
    root = tmp_path / "plain"
    root.mkdir()
    proc = install(root)
    assert proc.returncode == 1
    result = json.loads(proc.stdout)
    assert result["status"] == "error"


# --------------------------------------------------------------------- preflight

def test_preflight_missing_binding(bmad_project):
    proc = cli("preflight", "--project-root", str(bmad_project))
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["status"] == "FAIL"
    assert any(f["check"] == "project-binding" and f["status"] == "FAIL"
               for f in result["findings"])


def test_preflight_legacy_mode_is_warn_not_fail(bmad_project):
    write_project_json(bmad_project, LINKED_BINDING)
    proc = cli("preflight", "--project-root", str(bmad_project))
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["execution_mode"] == "legacy"
    krebs = [f for f in result["findings"] if f["check"] == "krebs-enrollment"]
    assert krebs and krebs[0]["status"] == "WARN"


def test_preflight_managed_without_actors_fails(bmad_project):
    write_project_json(bmad_project, {
        **LINKED_BINDING,
        "execution": {"mode": "managed", "actors": {}},
    })
    proc = cli("preflight", "--project-root", str(bmad_project))
    result = json.loads(proc.stdout)
    assert result["status"] == "FAIL"
    krebs = [f for f in result["findings"] if f["check"] == "krebs-enrollment"]
    assert krebs and krebs[0]["status"] == "FAIL"
    assert "canonical executionReadiness" in krebs[0]["evidence"]


def test_preflight_managed_enrolled_passes(bmad_project):
    write_project_json(bmad_project, {
        **LINKED_BINDING,
        "execution": {
            "mode": "shadow",
            "actors": {
                "worker": {"native_user_id": "u1", "runtime_id": "r1"},
                "pm": {"native_user_id": "u2", "runtime_id": "r2"},
            },
        },
    })
    proc = cli("preflight", "--project-root", str(bmad_project))
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS", result
    assert result["execution_mode"] == "shadow"


def test_preflight_scrubs_secrets(bmad_project):
    write_project_json(bmad_project, {
        **LINKED_BINDING,
        "api_token": "SUPERSECRET",
    })
    proc = cli("preflight", "--project-root", str(bmad_project))
    assert "SUPERSECRET" not in proc.stdout


# -------------------------------------------------------------- route/evidence

def test_route_event_request(bmad_project):
    proc = cli("route", "--project-root", str(bmad_project),
               "--request", "add a new bloodbank event type")
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["routes"], result
    assert result["routes"][0]["route"] == "event_naming"
    assert result["routes"][0]["owner"] == "Bloodbank"
    assert "/home/" not in proc.stdout


def test_evidence_to_handoff(bmad_project, tmp_path):
    diff = tmp_path / "d.diff"
    diff.write_text("--- a\n+++ b\n", encoding="utf-8")
    tests = tmp_path / "t.log"
    tests.write_text("3 passed\n", encoding="utf-8")
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps({
        "acceptance_criteria": ["AC1 module installs", "AC2 resolver active"],
        "worker_claims": ["implemented installer", "implemented CLI"],
        "diff_path": str(diff),
        "test_proof_path": str(tests),
        "outstanding": ["live install pending"],
    }), encoding="utf-8")
    out = tmp_path / "handoff.md"
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(bundle), "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = out.read_text(encoding="utf-8")
    for section in ("## Implemented", "## Tested", "## Installed",
                    "## Deployed", "## Outstanding", "## Attestation",
                    "Decision compass"):
        assert section in text, section
    assert "momo/PILLARS.md" in text
    assert "independence" in text.lower()
    # separate states, not conflated
    assert "- none reported" in text  # installed/deployed default
    assert str(tests) in text


def test_evidence_rejects_incomplete_bundle(bmad_project, tmp_path):
    bundle = tmp_path / "bad.json"
    bundle.write_text(json.dumps({"acceptance_criteria": []}), encoding="utf-8")
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(bundle))
    assert proc.returncode == 1
    result = json.loads(proc.stdout)
    assert result["status"] == "error"
    assert any("worker_claims" in e for e in result["errors"])


# ------------------------------------------------------------- unit: editors

def test_yaml_section_editor_preserves_other_bytes():
    text = ("# top\nfoo: 1\n\nbmm:\n  x: 1\n  # keep me\n")
    new, changed = G.replace_yaml_section(text, "g33", ["  a: 2"])
    assert changed
    assert "# top" in new and "foo: 1" in new
    assert "bmm:" in new and "  # keep me" in new
    assert "g33:" in new and "  a: 2" in new


def test_toml_table_editor_preserves_other_bytes():
    text = "# c\n[core]\nx = 1\n\n[modules.other]\ny = 2\n"
    new, changed = G.replace_toml_table(text, "[modules.g33]", ["code = \"g33\""])
    assert changed
    assert "[core]" in new and "y = 2" in new and "# c" in new
    assert "[modules.g33]" in new
    with io.StringIO() as _:
        import tomllib as _t
        parsed = _t.loads(new)
    assert parsed["modules"]["g33"]["code"] == "g33"
    assert parsed["modules"]["other"]["y"] == 2


def test_csv_merge_variants():
    target = (
        "module,skill,display-name,menu-code,description,action,args,phase,"
        "after,before,required,output-location,outputs\n"
        "M,s,d,c,desc,act,args,anytime,,,false,loc,outs\n"
    )
    (tmp := __import__("tempfile").mkdtemp())
    src = Path(tmp) / "src.csv"
    src.write_text((MODULE_ROOT / "assets" / "module-help.csv").read_text("utf-8"),
                   encoding="utf-8")
    merged, appended = G.merge_help_csv(target, src)
    assert len(appended) == 4
    assert "M,s,d" in merged  # other module preserved
    rows = list(csv.DictReader(io.StringIO(merged)))
    assert len(rows) == 5


def test_secret_scrub():
    dirty = {"api_token": "x", "nested": {"PASSWORD": "y", "ok": 1},
             "plain": "key value text"}
    clean = G.secret_free(dirty)
    assert clean["api_token"] == "[REDACTED]"
    assert clean["nested"]["PASSWORD"] == "[REDACTED]"
    assert clean["nested"]["ok"] == 1
    assert clean["plain"] == "key value text"
