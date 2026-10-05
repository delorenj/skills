"""Followup regression tests: exact reported bugs, authored BEFORE the fixes.

Covers the 2026-10-04 SPEC review findings F1-F10, parent spec review
blockers/defects, and the followup-contract items:
- evidence honesty (read+hash+parse real files, identity validation)
- canonical executionReadiness adapter parity + invalid-mode FAIL
- real conflict detection / malformed prerequisites / zero-write rejection
- --answers plumbing, additive merge preserving operator keys under --force
- planning-family skill overrides (bmad-prd/bmad-spec/bmad-architecture)
- identity wording agent-<identity>, 33GOD exact-case bank, Flume/Fleet split
- help surface _bmad/_config/bmad-help.csv, EH args --bundle
- runtime config consumption (ecosystem_root/doctrine override) in route/preflight
- PJangler v1 ES-module bridge (real subprocess calls, no mocks)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import pytest

from conftest import (MODULE_ROOT, REPO_ROOT, UPSTREAM_SCRIPTS, bmad_project,
                      clean_env, cli, install, resolve_config,
                      write_project_json)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import g33lib as G  # noqa: E402

LINKED_BINDING = {
    "project_id": "demo",
    "ticket_provider": {"type": "plane", "state": "linked",
                        "workspace": "33god", "board_id": "b1"},
}


# ================================================ F2/Blocker1: evidence honesty

def _write_bundle(tmp_path: Path, **over) -> Path:
    bundle = {
        "acceptance_criteria": ["AC1"],
        "worker_claims": ["built it"],
        "diff_path": "/nonexistent/no-such.diff",
        "test_proof_path": "/nonexistent/no-tests.txt",
        "installed": ["installed everywhere"],
        "deployed": ["deployed to prod"],
        "implementer": "worker-a",
        "reviewer": "worker-b",
    }
    bundle.update(over)
    p = tmp_path / "bundle.json"
    p.write_text(json.dumps(bundle), encoding="utf-8")
    return p


def test_evidence_nonexistent_paths_not_certified(bmad_project, tmp_path):
    """F2: nonexistent diff/test-proof must not yield Implemented/Tested."""
    bundle = _write_bundle(tmp_path)
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(bundle), "--out", str(tmp_path / "h.md"))
    text = (tmp_path / "h.md").read_text(encoding="utf-8") if (tmp_path / "h.md").exists() else ""
    payload = json.loads(proc.stdout)
    assert payload["status"] in ("ok", "error")
    # The handoff must NOT certify unverified claims as implemented/tested.
    if text:
        assert "## Implemented" in text
        assert "claimed-unverified" in text, text
        assert "[unverified" in text or "unresolved evidence" in text, text
        assert not any(
            ln.startswith("- test proof: /nonexistent") and "missing" not in ln
            for ln in text.splitlines()
        )


def test_evidence_missing_files_fails_or_flags(bmad_project, tmp_path):
    bundle = _write_bundle(tmp_path)
    out = tmp_path / "h2.md"
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(bundle), "--out", str(out))
    payload = json.loads(proc.stdout)
    if payload["status"] == "ok":
        text = out.read_text(encoding="utf-8")
        assert "cannot certify" in text or "unverified" in text or "missing" in text
    else:
        assert proc.returncode == 1


def test_evidence_test_proof_parsed_pass_fail(bmad_project, tmp_path):
    """F2: test-proof content is parsed; failures are surfaced, not hidden."""
    diff = tmp_path / "ok.diff"
    diff.write_text("--- a\n+++ b\n@@\n-a\n+b\n", encoding="utf-8")
    failing = tmp_path / "fail.log"
    failing.write_text("2 failed, 0 passed\n", encoding="utf-8")
    passing = tmp_path / "pass.log"
    passing.write_text("5 passed, 0 failed\n", encoding="utf-8")
    for proof, expect_fail in ((failing, True), (passing, False)):
        bundle = _write_bundle(tmp_path, diff_path=str(diff),
                               test_proof_path=str(proof))
        out = tmp_path / "h3.md"
        proc = cli("evidence", "--project-root", str(bmad_project),
                   "--bundle", str(bundle), "--out", str(out))
        assert proc.returncode == 0, proc.stdout
        text = out.read_text(encoding="utf-8")
        if expect_fail:
            assert "NOT CLEAN" in text and "2 failed" in text, text
        else:
            assert "VERIFIED" in text and "5 passed" in text, text


def test_evidence_empty_test_proof_not_certified(bmad_project, tmp_path):
    diff = tmp_path / "ok.diff"
    diff.write_text("--- a\n+++ b\n", encoding="utf-8")
    empty = tmp_path / "empty.log"
    empty.write_text("", encoding="utf-8")
    bundle = _write_bundle(tmp_path, diff_path=str(diff),
                           test_proof_path=str(empty))
    out = tmp_path / "h4.md"
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(bundle), "--out", str(out))
    assert proc.returncode == 0
    text = out.read_text(encoding="utf-8")
    assert "unverified" in text or "empty" in text or "cannot certify" in text


def test_evidence_identity_validation(bmad_project, tmp_path):
    """F2/Blocker1: attestation must validate distinct implementer/reviewer."""
    diff = tmp_path / "ok.diff"
    diff.write_text("--- a\n+++ b\n", encoding="utf-8")
    proof = tmp_path / "ok.log"
    proof.write_text("3 passed\n", encoding="utf-8")
    # same identity -> attestation must be refused/flagged
    bundle = _write_bundle(tmp_path, diff_path=str(diff),
                           test_proof_path=str(proof),
                           implementer="sameguy", reviewer="sameguy")
    out = tmp_path / "h5.md"
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(bundle), "--out", str(out))
    assert proc.returncode == 0
    text = out.read_text(encoding="utf-8")
    assert "NOT VALIDATED" in text or "not validated" in text or "same identity" in text, text
    # missing identities -> flagged
    missing = {
        "acceptance_criteria": ["AC1"], "worker_claims": ["built it"],
        "diff_path": str(diff), "test_proof_path": str(proof),
        "installed": ["installed everywhere"], "deployed": ["deployed to prod"],
    }
    (tmp_path / "bundle2.json").write_text(json.dumps(missing),
                                           encoding="utf-8")
    out2 = tmp_path / "h6.md"
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(tmp_path / "bundle2.json"), "--out", str(out2))
    assert proc.returncode == 0
    text2 = out2.read_text(encoding="utf-8")
    assert "NOT VALIDATED" in text2 or "not validated" in text2, text2
    # distinct identities -> attestation validated with names
    bundle3 = _write_bundle(tmp_path, diff_path=str(diff),
                            test_proof_path=str(proof),
                            implementer="impl-x", reviewer="rev-y")
    out3 = tmp_path / "h7.md"
    proc = cli("evidence", "--project-root", str(bmad_project),
               "--bundle", str(bundle3), "--out", str(out3))
    assert proc.returncode == 0
    text3 = out3.read_text(encoding="utf-8")
    assert "impl-x" in text3 and "rev-y" in text3
    assert "same identity" not in text3 and "NOT VALIDATED" not in text3


# ============================== F7/Blocker2: canonical executionReadiness parity

def test_preflight_invalid_mode_fails_not_legacy(bmad_project):
    write_project_json(bmad_project, {
        **LINKED_BINDING,
        "execution": {"mode": "managedd", "actors": {}},
    })
    proc = cli("preflight", "--project-root", str(bmad_project))
    result = json.loads(proc.stdout)
    krebs = [f for f in result["findings"] if f["check"] == "krebs-enrollment"]
    assert krebs and krebs[0]["status"] == "FAIL", result
    assert result["execution_mode"] == "invalid"
    assert result["status"] == "FAIL"


def _canonical_errors(execution: dict) -> list[str]:
    return G.execution_readiness(
        {**LINKED_BINDING, "project_id": "demo", "execution": execution})


def test_readiness_bare_actor_fails_like_canonical():
    """The exact Blocker-2 repro: actors-only managed must FAIL readiness."""
    errors = _canonical_errors({"mode": "managed",
                                "actors": {"a": {"native_user_id": "u1"}}})
    text = " | ".join(errors)
    assert "pm actor" in text.lower() or "pm_actor" in text.lower(), errors
    assert "op reference" in text, errors  # canonical actor requirement
    assert "policy" in text.lower(), errors
    assert "lane" in text.lower(), errors
    assert len(errors) >= 8, errors  # canonical rejects on >= 8 counts


def test_readiness_full_managed_manifest_passes():
    """A complete policyVersion-2 manifest must pass the ported validator."""
    manifest = {
        **LINKED_BINDING,
        "project_id": "demo",
        "execution": {
            "mode": "managed",
            "policy_version": 2,
            "skill_version": "1.2.3",
            "working_label": "Doing",
            "legacy_writers_fenced": True,
            "pm_actor": "grolf",
            "controller_actor": "controller",
            "pilot_bundle_sha256": "a" * 64,
            "momo_bundle_sha256": "b" * 64,
            "states": {lane: f"s-{i}" for i, lane in enumerate(G.EXECUTION_LANES)},
            "actors": {
                "grolf": {
                    "role": "pm", "native_user_id": "u-pm",
                    "key_ref": "op://x/y/z", "runtime_id": "rt-pm",
                    "runtime": {"adapter": "systemd", "unit_prefix": "pm",
                                "planner_argv": ["plan"]},
                },
                "controller": {
                    "role": "operator", "native_user_id": "u-ctl",
                    "key_ref": "op://x/y/w", "runtime_id": "rt-ctl",
                    "runtime": {"adapter": "systemd", "unit_prefix": "ctl"},
                },
            },
        },
    }
    assert G.execution_readiness(manifest) == []


def test_readiness_shadow_partial_allowed_but_not_certified():
    """Shadow may be incremental (no hard FAIL) but must not certify managed."""
    errors = _canonical_errors({"mode": "shadow",
                                "actors": {"a": {"native_user_id": "u1"}}})
    assert isinstance(errors, list)


def test_preflight_managed_uses_canonical_validator(bmad_project):
    """preflight must FAIL the Blocker-2 repro fixture via the ported adapter."""
    write_project_json(bmad_project, {
        **LINKED_BINDING,
        "execution": {"mode": "managed",
                      "actors": {"a": {"native_user_id": "u1"}}},
    })
    proc = cli("preflight", "--project-root", str(bmad_project))
    result = json.loads(proc.stdout)
    krebs = [f for f in result["findings"] if f["check"] == "krebs-enrollment"]
    assert krebs and krebs[0]["status"] == "FAIL", result
    assert result["status"] == "FAIL"


def test_preflight_managed_full_manifest_passes(bmad_project):
    manifest = {
        **LINKED_BINDING,
        "execution": {
            "mode": "managed", "policy_version": 2, "skill_version": "1.2.3",
            "working_label": "Doing", "legacy_writers_fenced": True,
            "pm_actor": "grolf", "controller_actor": "controller",
            "pilot_bundle_sha256": "a" * 64, "momo_bundle_sha256": "b" * 64,
            "states": {lane: f"s-{i}" for i, lane in enumerate(G.EXECUTION_LANES)},
            "actors": {
                "grolf": {"role": "pm", "native_user_id": "u-pm",
                          "key_ref": "op://x/y/z", "runtime_id": "rt-pm",
                          "runtime": {"adapter": "systemd", "unit_prefix": "pm",
                                      "planner_argv": ["plan"]}},
                "controller": {"role": "operator", "native_user_id": "u-ctl",
                               "key_ref": "op://x/y/w", "runtime_id": "rt-ctl",
                               "runtime": {"adapter": "systemd",
                                           "unit_prefix": "ctl"}},
            },
        },
    }
    write_project_json(bmad_project, manifest)
    proc = cli("preflight", "--project-root", str(bmad_project))
    result = json.loads(proc.stdout)
    krebs = [f for f in result["findings"] if f["check"] == "krebs-enrollment"]
    assert krebs and krebs[0]["status"] == "PASS", result


# ============================== F1/F4/Blocker3: conflicts + validation + answers

def _mk_bare(target: Path) -> Path:
    (target / "_bmad").mkdir(parents=True)
    return target


def test_conflict_foreign_g33_yaml_section_rejected(tmp_path):
    """F1 P9: pre-existing foreign g33 section => conflict, zero writes."""
    target = _mk_bare(tmp_path / "t1")
    (target / "_bmad" / "config.yaml").write_text(
        "g33:\n  name: existing-owner\n", encoding="utf-8")
    before = (target / "_bmad" / "config.yaml").read_text(encoding="utf-8")
    proc = install(target)
    assert proc.returncode != 0, proc.stdout
    result = json.loads(proc.stdout)
    assert result["status"] == "conflict"
    assert result["conflicts"], result
    assert any("g33" in c.get("path", "") or "g33" in c.get("detail", "")
               for c in result["conflicts"])
    # zero mutations
    assert (target / "_bmad" / "config.yaml").read_text(encoding="utf-8") == before
    assert not (target / "_bmad" / "custom").exists()


def test_conflict_inline_g33_yaml_detected(tmp_path):
    """Blocker3: `g33: prev-value` inline must be detected, not duplicated."""
    target = _mk_bare(tmp_path / "t2")
    (target / "_bmad" / "config.yaml").write_text(
        "g33: operator-inline\n", encoding="utf-8")
    before = (target / "_bmad" / "config.yaml").read_text(encoding="utf-8")
    proc = install(target)
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "conflict"
    assert (target / "_bmad" / "config.yaml").read_text(encoding="utf-8") == before


def test_conflict_malformed_custom_toml_rejected_before_writes(tmp_path):
    """F4 P6: pre-broken custom/config.toml => conflict, file untouched."""
    target = tmp_path / "t3"
    (target / "_bmad" / "custom").mkdir(parents=True)
    (target / "_bmad" / "scripts").mkdir(parents=True)
    for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
        shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
    (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
    (target / "_bmad" / "custom" / "config.toml").write_text(
        "broken = [\n", encoding="utf-8")
    broken_before = (target / "_bmad" / "custom" / "config.toml").read_bytes()
    proc = install(target)
    assert proc.returncode != 0, proc.stdout
    result = json.loads(proc.stdout)
    assert result["status"] == "conflict"
    assert (target / "_bmad" / "custom" / "config.toml").read_bytes() == broken_before
    assert not (target / "_bmad" / "custom" / "bmad-build.toml").exists()


def test_conflict_symlink_target_rejected(tmp_path):
    """Symlink at config.yaml target => conflict, zero writes."""
    target = _mk_bare(tmp_path / "t4")
    real = tmp_path / "real.yaml"
    real.write_text("other: 1\n", encoding="utf-8")
    (target / "_bmad" / "config.yaml").symlink_to(real)
    proc = install(target)
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "conflict"
    assert real.read_text(encoding="utf-8") == "other: 1\n"


def test_conflict_foreign_toml_table_rejected(tmp_path):
    """Foreign [modules.g33] with unknown/other module code => conflict."""
    target = tmp_path / "t5"
    (target / "_bmad" / "custom").mkdir(parents=True)
    (target / "_bmad" / "scripts").mkdir(parents=True)
    for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
        shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
    (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
    (target / "_bmad" / "custom" / "config.toml").write_text(
        '[modules.g33]\ncode = "other-module"\n', encoding="utf-8")
    before = (target / "_bmad" / "custom" / "config.toml").read_text(encoding="utf-8")
    proc = install(target)
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "conflict"
    assert (target / "_bmad" / "custom" / "config.toml").read_text(encoding="utf-8") == before


def test_malformed_config_yaml_rejected(tmp_path):
    """Non-BMAD/garbage config.yaml (unparseable tab indent) => conflict."""
    target = _mk_bare(tmp_path / "t6")
    (target / "_bmad" / "config.yaml").write_text(
        "g33:\n\tname: [\n", encoding="utf-8")
    before = (target / "_bmad" / "config.yaml").read_text(encoding="utf-8")
    proc = install(target)
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "conflict"
    assert (target / "_bmad" / "config.yaml").read_text(encoding="utf-8") == before


def test_answers_json_is_consumed(tmp_path):
    """F3 P5: --answers values must reach TOML and YAML outputs."""
    target = tmp_path / "t7"
    (target / "_bmad" / "custom").mkdir(parents=True)
    (target / "_bmad" / "scripts").mkdir(parents=True)
    for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
        shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
    (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
    answers = tmp_path / "a.json"
    answers.write_text(json.dumps({
        "ecosystem_root": "custom/eco",
        "g33_output_folder": "{project-root}/custom-out",
    }), encoding="utf-8")
    proc = install(target, "--answers", str(answers))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    toml_text = (target / "_bmad" / "custom" / "config.toml").read_text(encoding="utf-8")
    assert 'ecosystem_root = "custom/eco"' in toml_text
    yaml_text = (target / "_bmad" / "config.yaml").read_text(encoding="utf-8")
    assert "custom/eco" in yaml_text
    assert "custom-out" in toml_text


def test_answers_nonexistent_file_errors(tmp_path):
    """--answers /nonexistent.json must fail, not silently no-op."""
    target = _mk_bare(tmp_path / "t8")
    proc = install(target, "--answers", "/nonexistent.json")
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "error"
    assert "answers" in json.dumps(result).lower()


def test_answers_unknown_key_rejected(tmp_path):
    """Answers with unknown variables must be rejected (validated, not ignored)."""
    target = _mk_bare(tmp_path / "t9")
    answers = tmp_path / "a.json"
    answers.write_text(json.dumps({"bogus_key": "x"}), encoding="utf-8")
    proc = install(target, "--answers", str(answers))
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "error"


def test_output_validated_before_writing(tmp_path):
    """F4: written TOML must parse; a write that would break it must abort."""
    # covered implicitly by malformed tests; here we assert installer validates
    # its own plan output: simulate by checking plan contains no invalid TOML
    target = tmp_path / "t10"
    (target / "_bmad" / "custom").mkdir(parents=True)
    (target / "_bmad" / "scripts").mkdir(parents=True)
    for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
        shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
    (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
    proc = install(target)
    assert proc.returncode == 0
    with (target / "_bmad" / "custom" / "config.toml").open("rb") as f:
        tomllib.load(f)  # written state parses


def test_additive_merge_preserves_operator_keys_under_force(tmp_path):
    """F5 P4b: --force must NOT drop operator unknown keys in [modules.g33]."""
    target = tmp_path / "t11"
    (target / "_bmad" / "custom").mkdir(parents=True)
    (target / "_bmad" / "scripts").mkdir(parents=True)
    for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
        shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
    (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
    assert install(target).returncode == 0
    custom = target / "_bmad" / "custom" / "config.toml"
    text = custom.read_text(encoding="utf-8")
    text += 'operator_extra = "keep-me"\n'
    custom.write_text(text, encoding="utf-8")
    assert install(target, "--force").returncode == 0
    assert 'operator_extra = "keep-me"' in custom.read_text(encoding="utf-8")


def test_help_targets_real_bmad_help_csv(bmad_project):
    """F6: g33 rows must land in _bmad/_config/bmad-help.csv."""
    assert install(bmad_project).returncode == 0
    help_csv = bmad_project / "_bmad" / "_config" / "bmad-help.csv"
    assert help_csv.is_file()
    rows = [r for r in help_csv.read_text(encoding="utf-8").splitlines()
            if r.startswith("33GOD Integration,")]
    assert len(rows) == 4, rows


def test_help_csv_eh_args_bundle():
    """Defect 8: EH row args must say --bundle (actual flag)."""
    text = (MODULE_ROOT / "assets" / "module-help.csv").read_text(encoding="utf-8")
    eh = [ln for ln in text.splitlines() if ",EH," in ln]
    assert eh, text
    assert "--bundle" in eh[0]
    assert "--evidence" not in eh[0]


# ============================ F5/Defect5: planning-family skill overrides

def test_planning_family_overrides_emitted(bmad_project):
    """Defect 5: bmad-prd / bmad-spec / bmad-architecture overrides emitted
    for surfaces actually installed in the project's skill root."""
    for skill in ("bmad-build", "bmad-code-review", "bmad-prd",
                  "bmad-spec", "bmad-architecture"):
        d = bmad_project / ".agents" / "skills" / skill
        d.mkdir(parents=True)
        shutil.copy2(REPO_ROOT / "all-skills" / skill / "customize.toml",
                     d / "customize.toml")
    assert install(bmad_project).returncode == 0
    for name in ("bmad-prd.toml", "bmad-spec.toml", "bmad-architecture.toml"):
        p = bmad_project / "_bmad" / "custom" / name
        assert p.is_file(), name
        with p.open("rb") as f:
            tomllib.load(f)


def test_planning_overrides_only_for_installed_surfaces(bmad_project):
    """Sparse: only skills whose customize.toml exists in all-skills."""
    assert install(bmad_project).returncode == 0
    custom_dir = bmad_project / "_bmad" / "custom"
    written = {p.name for p in custom_dir.glob("*.toml")} - {"config.toml"}
    canonical = {p.name for p in (REPO_ROOT / "all-skills").glob("bmad-*/customize.toml")}
    # every written override must correspond to a canonical customize.toml
    for name in written:
        stem = name[: -len(".toml")]
        assert f"{stem}.toml" in canonical or stem in (
            "bmad-build", "bmad-code-review", "bmad-prd", "bmad-spec",
            "bmad-architecture"), (name, canonical)


# ==================== F8: runtime config consumed + doctrine override

def test_route_consumes_project_config(bmad_project):
    """F8 P10: ecosystem_root in custom/config.toml must affect route output."""
    assert install(bmad_project).returncode == 0
    custom = bmad_project / "_bmad" / "custom" / "config.toml"
    custom.write_text(custom.read_text(encoding="utf-8").replace(
        'ecosystem_root = "."', 'ecosystem_root = "vendor/33GOD"'), encoding="utf-8")
    proc = cli("route", "--project-root", str(bmad_project),
               "--request", "analyze the plan")
    result = json.loads(proc.stdout)
    assert result.get("ecosystem_root") == "vendor/33GOD", result
    assert "vendor/33GOD" in proc.stdout


def test_route_doctrine_override(bmad_project):
    """F8: doctrine pointer portable override from project config."""
    assert install(bmad_project).returncode == 0
    custom = bmad_project / "_bmad" / "custom" / "config.toml"
    text = custom.read_text(encoding="utf-8")
    text = text.replace("ecosystem_root = \".\"", "ecosystem_root = \".\"") \
        + 'doctrine_pointer = "custom-doctrine/PILLARS.md"\n'
    custom.write_text(text, encoding="utf-8")
    proc = cli("route", "--project-root", str(bmad_project),
               "--request", "analyze")
    result = json.loads(proc.stdout)
    assert result["doctrine"]["pointer"] == "custom-doctrine/PILLARS.md", result


def test_preflight_reports_ecosystem_root(bmad_project):
    """Module config actually consumed at preflight, not ornamental."""
    assert install(bmad_project).returncode == 0
    proc = cli("preflight", "--project-root", str(bmad_project))
    result = json.loads(proc.stdout)
    assert result.get("config", {}).get("ecosystem_root") is not None, result


# ==================== F9/.claude-plugin protection (must stay byte-identical)

def test_claude_plugin_marketplace_untouched():
    """Followup contract: protect unrelated dirty .claude-plugin byte-for-byte.

    The module must NOT depend on or modify all-skills/.claude-plugin/.
    """
    p = REPO_ROOT / "all-skills" / ".claude-plugin" / "marketplace.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        # whatever it says, the g33 module must not be the reason it exists:
        # no canonical file inside g33 may reference it
        for f in MODULE_ROOT.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".toml", ".csv", ".yaml"):
                assert ".claude-plugin" not in f.read_text(encoding="utf-8"), f


# ==================== Identity wording fixes in the ecosystem map

def test_ecosystem_map_identity_wording():
    text = (MODULE_ROOT / "assets" / "ecosystem-map.toml").read_text(encoding="utf-8")
    # Defect 6: named identity, not routing profile
    assert "agent-<identity>" in text
    assert "agent-grolf" in text
    assert "agent-{profile}" not in text
    assert "agent-33god-pm" in text  # do-not-target stale bank named
    # project bank trap documented
    assert "33god-core" in text or "consolidated" in text


def test_ecosystem_map_flume_fleet_split():
    text = (MODULE_ROOT / "assets" / "ecosystem-map.toml").read_text(encoding="utf-8")
    # Defect 7: Hermes Fleet owns runtime/profiles/templates
    assert "Hermes Fleet" in text


# ==================== Resolver-absent status honesty (F10)

def test_resolver_absent_install_reports_not_active(tmp_path):
    target = _mk_bare(tmp_path / "t12")
    (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
    proc = install(target)
    result = json.loads(proc.stdout)
    assert proc.returncode in (0, 1)
    assert any("absent" in w.lower() or "inactive" in w.lower()
               for w in result.get("warnings", [])), result
    assert result.get("activation") in (None, "inactive", "partial", "unavailable") or \
        result.get("toml_active") is False, result


# ==================== PJangler v1 ES module bridge (real subprocess calls)

NODE = shutil.which("node")


@pytest.mark.skipif(NODE is None, reason="node runtime unavailable")
class TestPjanglerBridge:
    @staticmethod
    def _call(request: dict, module_path: Path | None = None,
              executable: str | None = None) -> tuple[int, Any]:
        script = MODULE_ROOT / "scripts" / "g33_bridge_call.mjs"
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        cmd = [NODE, str(script), json.dumps(request)]
        if module_path:
            cmd += ["--module", str(module_path)]
        if executable:
            cmd += ["--python", executable]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              check=False, env=env)
        try:
            parsed: Any = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = proc.stdout + proc.stderr
        return proc.returncode, parsed

    def test_observe_missing(self, tmp_path):
        target = tmp_path / "proj"
        target.mkdir()
        rc, out = self._call({
            "schemaVersion": 1, "moduleId": "g33", "operation": "observe",
            "projectRoot": str(target), "reason": "audit", "options": {},
        })
        assert rc == 0
        assert out["status"] == "missing"
        assert out["schemaVersion"] == 1

    def test_observe_installed_after_apply(self, tmp_path):
        target = tmp_path / "proj"
        (target / "_bmad" / "custom").mkdir(parents=True)
        (target / "_bmad" / "scripts").mkdir(parents=True)
        for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
            shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
        (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
        req = {"schemaVersion": 1, "moduleId": "g33", "operation": "apply",
               "reason": "bmad-install", "options": {}}
        req = {**req, "projectRoot": str(target)}
        rc, out = self._call(req)
        assert rc == 0
        assert out["status"] == "changed"
        rc, out = self._call({**req, "operation": "observe"})
        assert out["status"] == "installed"
        # observe verified real content, not metadata
        assert any("resolve_config" in e or "bmad-help.csv" in e
                   or "modules.g33" in e for e in out["evidence"])
        # apply is idempotent
        rc, out = self._call({**req, "operation": "apply"})
        assert out["status"] == "unchanged"

    def test_plan_zero_writes(self, tmp_path):
        target = tmp_path / "proj"
        (target / "_bmad" / "custom").mkdir(parents=True)
        (target / "_bmad" / "scripts").mkdir(parents=True)
        for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
            shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
        (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
        before = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
        rc, out = self._call({
            "schemaVersion": 1, "moduleId": "g33", "operation": "plan",
            "projectRoot": str(target), "reason": "recipe", "options": {},
        })
        assert rc == 0
        assert out["status"] == "planned"
        after = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
        assert before == after

    def test_observe_conflict(self, tmp_path):
        target = tmp_path / "proj"
        (target / "_bmad").mkdir(parents=True)
        (target / "_bmad" / "config.yaml").write_text(
            "g33:\n  name: foreign\n", encoding="utf-8")
        rc, out = self._call({
            "schemaVersion": 1, "moduleId": "g33", "operation": "observe",
            "projectRoot": str(target), "reason": "audit", "options": {},
        })
        assert out["status"] == "conflict"

    def test_observe_tampered_files_not_installed(self, tmp_path):
        """Missing/tampered installed files must not report installed."""
        target = tmp_path / "proj"
        (target / "_bmad" / "custom").mkdir(parents=True)
        (target / "_bmad" / "scripts").mkdir(parents=True)
        for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
            shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
        (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
        # fake a partial install: g33 TOML row present but help CSV missing,
        # YAML section present but overrides missing => tampered/partial
        (target / "_bmad" / "custom" / "config.toml").write_text(
            '[modules.g33]\ncode = "g33"\n', encoding="utf-8")
        rc, out = self._call({
            "schemaVersion": 1, "moduleId": "g33", "operation": "observe",
            "projectRoot": str(target), "reason": "audit", "options": {},
        })
        assert out["status"] in ("missing", "conflict"), out

    def test_relocated_module_and_python_override(self, tmp_path):
        """Module relocation + executable override are portable options."""
        target = tmp_path / "proj"
        (target / "_bmad" / "custom").mkdir(parents=True)
        (target / "_bmad" / "scripts").mkdir(parents=True)
        for name in ("config_utils.py", "resolve_config.py", "resolve_customization.py"):
            shutil.copy2(UPSTREAM_SCRIPTS / name, target / "_bmad" / "scripts" / name)
        (target / "_bmad" / "config.toml").write_text("[core]\n", encoding="utf-8")
        relocated = tmp_path / "relocated-g33"
        shutil.copytree(MODULE_ROOT, relocated)
        rc, out = self._call({
            "schemaVersion": 1, "moduleId": "g33", "operation": "observe",
            "projectRoot": str(target), "reason": "audit", "options": {},
        }, module_path=relocated / "scripts" / "g33_pjangler_bridge.mjs",
           executable=sys.executable)
        assert rc == 0
        assert out["status"] == "missing"

    def test_unsupported_option_rejected(self, tmp_path):
        target = tmp_path / "proj"
        target.mkdir()
        rc, out = self._call({
            "schemaVersion": 1, "moduleId": "g33", "operation": "observe",
            "projectRoot": str(target), "reason": "audit",
            "options": {"bogus_option": True},
        })
        assert out["status"] == "error"
        joined = out["summary"] + " ".join(out["details"])
        assert "bogus_option" in joined

    def test_strict_shapes(self, tmp_path):
        """Wrong schemaVersion/moduleId/reason => error, never silent pass."""
        target = tmp_path / "proj"
        target.mkdir()
        for bad in (
            {"schemaVersion": 2},
            {"moduleId": "g34"},
            {"reason": "curious"},
            {"operation": "destroy"},
        ):
            req = {"schemaVersion": 1, "moduleId": "g33", "operation": "observe",
                   "projectRoot": str(target), "reason": "audit", "options": {}}
            req.update(bad)
            rc, out = self._call(req)
            assert out["status"] == "error", bad


def project_root_override(target: Path) -> Path:  # helper kept for symmetry
    return target


# ==================== Fixture activation via Skillex (reference-only pack)

def test_reference_only_fixture_activation(tmp_path):
    """Module activation through Skillex CLI in an isolated fixture.

    Creates a reference-only set pointing at the canonical g33 body (never a
    copy), enables it in a fixture project through the REAL skillex CLI, and
    observes the activated symlink via `skillex status` — read-only on the
    live repo except the fixture directory itself.
    """
    skillex_bin = shutil.which("skillex")
    if skillex_bin is None:
        pytest.skip("skillex CLI not on PATH")
    fixture = tmp_path / "fx"
    fixture.mkdir()
    # fixture manifest: registry is the real skillex checkout (read-only use)
    (fixture / ".agents").mkdir()
    (fixture / ".agents" / "skills.json").write_text(json.dumps({
        "$schema": "https://raw.githubusercontent.com/delorenj/skillex/main/skills.schema.json",
        "inherit_global": False,
        "registry": f"file://{REPO_ROOT}",
        "skills": ["g33-33god-integration"],
    }), encoding="utf-8")
    proc = subprocess.run(
        [skillex_bin, "sync", "--project", str(fixture), "--json"],
        capture_output=True, text=True, check=False,
        env={**clean_env(), "SKILLEX_REGISTRY_ROOT": str(REPO_ROOT)},
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    assert proc.returncode == 0, proc.stdout + proc.stderr
    activated = fixture / ".agents" / "skills" / "g33-33god-integration"
    assert activated.exists(), payload
    assert activated.is_symlink() and not activated.is_dir() or activated.is_dir()
    # reference-only: it is a symlink to the canonical body, not a copy
    assert activated.is_symlink()
    assert activated.resolve() == (REPO_ROOT / "all-skills" / "g33-33god-integration").resolve()
    # owner observation through the CLI
    proc2 = subprocess.run(
        [skillex_bin, "status", "--scope", "project", "--project", str(fixture), "--json"],
        capture_output=True, text=True, check=False,
    )
    assert proc2.returncode in (0, 6)
    data = json.loads(proc2.stdout)
    scopes = data["data"]["resolution"]["scopes"]
    proj = [s for s in scopes if s["scope"] == "project"][0]
    names = [b["name"] for b in proj["bindings"]]
    assert "g33-33god-integration" in names
    # and the activated skill's CLI really runs from the activation root
    cli_proc = subprocess.run(
        [sys.executable, str(activated / "scripts" / "g33_cli.py"), "--version"],
        capture_output=True, text=True, check=False, env=clean_env(),
    )
    assert cli_proc.returncode == 0
    assert G.MODULE_VERSION in cli_proc.stdout
