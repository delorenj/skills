"""Tests-first regressions for the completed round-one independent SPEC HOLD.
"""
import json
import sys
from pathlib import Path

import pytest

from conftest import MODULE_ROOT as MODULE, cli, install
from test_repair_round1 import snapshot, stage_skill, bridge
import g33_install as I
import yaml
import csv
import io
import g33lib as G

VALID = 'diff --git a/src/a.py b/src/a.py\nindex 1234567..2345678 100644\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@\n-old\n+new\n'


def bundle(tmp_path, diff_text, proof='1 passed\ncommand_exit_code=0\n', links=None):
    diff = tmp_path / 'proof.diff'
    diff.write_text(diff_text)
    tests = tmp_path / 'tests.log'
    tests.write_text(proof)
    data = {'acceptance_criteria': ['AC1'], 'worker_claims': ['implemented change'],
            'diff_path': str(diff), 'test_proof_path': str(tests),
            'implementer': 'worker', 'reviewer': 'external-reviewer'}
    if links is not None:
        data['claim_evidence'] = links
    return data


def implementation_section(text):
    return text.split('## Implemented\n', 1)[1].split('## Tested', 1)[0]


@pytest.mark.parametrize('diff', [
    'this is not a diff',
    '--- a/src/a.py\n+++ b/src/a.py\n',
    '--- a/src/a.py\n+++ b/src/a.py\n@@\n-old\n+new\n',
    '--- a/src/a.py\n+++ b/src/a.py\n@@ -1,2 +1 @@\n-old\n+new\n',
])
def test_S1_invalid_diff_does_not_certify_claims(tmp_path, diff):
    text = G.generate_handoff(MODULE, bundle(tmp_path, diff))
    assert 'claimed-unverified: implemented change' in implementation_section(text)
    assert 'diff VERIFIED' not in text
    assert 'overall: evidence verified' not in text


def test_S1_invalid_test_log_does_not_certify_claims(tmp_path):
    text = G.generate_handoff(MODULE, bundle(tmp_path, VALID, 'this is not test evidence'))
    assert 'claimed-unverified: implemented change' in implementation_section(text)
    assert 'overall: evidence verified' not in text


@pytest.mark.parametrize('links', [None,
    [{'claim': 'implemented change', 'acceptance_criteria': ['UNKNOWN'], 'diff_paths': ['src/a.py']}],
    [{'claim': 'implemented change', 'acceptance_criteria': ['AC1'], 'diff_paths': ['not-in-diff.py']}],
])
def test_S1_claim_requires_valid_ac_and_parsed_diff_link(tmp_path, links):
    text = G.generate_handoff(MODULE, bundle(tmp_path, VALID, links=links))
    assert 'claimed-unverified: implemented change' in implementation_section(text)


def test_S1_valid_link_is_visible_in_implementation_evidence(tmp_path):
    links = [{'claim': 'implemented change', 'acceptance_criteria': ['AC1'],
              'diff_paths': ['src/a.py']}]
    text = G.generate_handoff(MODULE, bundle(tmp_path, VALID, links=links))
    section = implementation_section(text)
    assert 'AC1' in section and 'src/a.py' in section
    assert 'linked recorded evidence' in section

@pytest.mark.parametrize("text", ['bmm: {unterminated\n', 'project_name: "unterminated\n',
    'bmm:\n  one: [unterminated\n', 'bmm:\n  duplicate: one\n  duplicate: two\n'])
def test_S2_malformed_yaml_refused_without_writes(bmad_project, text):
    (bmad_project / "_bmad/config.yaml").write_text(text)
    before = snapshot(bmad_project)
    proc = install(bmad_project)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "conflict" and payload["conflicts"]
    assert snapshot(bmad_project) == before


def test_S2_missing_yaml_parser_actionable_refusal(bmad_project, monkeypatch):
    monkeypatch.setattr(I, "yaml", None, raising=False)
    before = snapshot(bmad_project)
    plan = I.plan_install(bmad_project, False)
    assert plan["status"] == "conflict", plan
    assert any("PyYAML" in c["detail"] for c in plan["conflicts"])
    assert not plan["actions"] and snapshot(bmad_project) == before


def test_S3_force_preserves_nested_keys_and_inline_comments(bmad_project):
    assert install(bmad_project).returncode == 0
    path = bmad_project / "_bmad/config.yaml"
    text = path.read_text().replace('  ecosystem_root: .', '  ecosystem_root: "operator-root" # root inline')
    text += '  operator_nested:\n    ecosystem_root: keep-nested # nested comment\n    deeper:\n      name: "operator name"\n'
    path.write_text(text)
    assert install(bmad_project, "--force").returncode == 0
    after = path.read_text()
    data = yaml.safe_load(after)["g33"]
    assert data["ecosystem_root"] == "."
    assert data["operator_nested"] == {"ecosystem_root": "keep-nested", "deeper": {"name": "operator name"}}
    assert '# root inline' in after and '# nested comment' in after
    assert '    ecosystem_root: keep-nested # nested comment' in after
    snap = snapshot(bmad_project)
    assert install(bmad_project, "--force").returncode == 0
    assert snapshot(bmad_project) == snap


@pytest.mark.parametrize("tamper", ["remove-PF", "remove-ER", "remove-EH", "remove-SU", "args", "duplicate"])
def test_S4_observe_rejects_incomplete_owned_help(bmad_project, tamper):
    stage_skill(bmad_project)
    assert install(bmad_project).returncode == 0
    path = bmad_project / "_bmad/_config/bmad-help.csv"
    reader = csv.DictReader(io.StringIO(path.read_text()))
    rows, fields = list(reader), reader.fieldnames
    if tamper.startswith("remove-"):
        rows = [row for row in rows if row["menu-code"] != tamper[7:]]
    elif tamper == "args":
        for row in rows:
            if row["menu-code"] == "EH": row["args"] = "{--wrong-arg PATH}"
    else:
        rows.append(next(row for row in rows if row["menu-code"] == "EH"))
    stream = io.StringIO(); writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows); path.write_text(stream.getvalue())
    before = snapshot(bmad_project)
    reply = bridge(bmad_project, "observe")
    assert reply["status"] != "installed", reply
    assert snapshot(bmad_project) == before


def test_S5_self_authored_receipts_remain_unverified(tmp_path):
    data = bundle(tmp_path, VALID)
    data.update({"installed": ["installed on target"], "deployed": ["deployed to target"]})
    marker = tmp_path / "must-not-be-executed"
    for state, claim in (("installed", "installed on target"), ("deployed", "deployed to target")):
        path = tmp_path / f"{state}.json"
        path.write_text(json.dumps({"state": state, "claims": [claim], "checks": [
            {"command": f"touch {marker}", "exit_code": 0, "observed": "self assertion"}]}))
        data[f"{state}_evidence_path"] = str(path)
    text = G.generate_handoff(MODULE, data)
    assert "claimed-unverified: installed on target" in text
    assert "claimed-unverified: deployed to target" in text
    assert "installed receipt VERIFIED" not in text and "deployed receipt VERIFIED" not in text
    assert not marker.exists()


def test_S6_evidence_uses_installed_project_doctrine(bmad_project, tmp_path):
    assert install(bmad_project).returncode == 0
    cfg = bmad_project / "_bmad/custom/config.toml"
    cfg.write_text(cfg.read_text() + 'doctrine_pointer = "docs/my-doctrine.md"\n')
    path = tmp_path / "bundle.json"; path.write_text(json.dumps(bundle(tmp_path, VALID)))
    out = tmp_path / "handoff.md"
    proc = cli("evidence", "--project-root", str(bmad_project), "--bundle", str(path), "--out", str(out))
    assert proc.returncode == 0, proc.stdout
    assert "docs/my-doctrine.md" in out.read_text()
    assert "momo/PILLARS.md" not in out.read_text()


@pytest.mark.parametrize("proof", [
    "Block A\n2 passed\nexit_code=0\ncommand_exit_code=0\nBlock B\n1 passed\n",
    "exit_code=0\n2 passed\n",
    "Block A\n2 passed\nexit_code=0\n\nBlock B\nexit_code=0\n1 passed\n",
])
def test_S7_exit_markers_do_not_cross_blocks(proof):
    assert G.parse_test_proof(proof)["clean_pass"] is False


def test_S7_two_complete_blocks_certifiable():
    assert G.parse_test_proof("Block A\n2 passed\nexit_code=0\nBlock B\n1 passed\ncommand_exit_code=0\n")["clean_pass"] is True


@pytest.mark.parametrize("value", ["true", "123", "null", "yes", "on", "0xA", "2026-10-05", "~"])
def test_S8_answer_string_type_roundtrips(bmad_project, tmp_path, value):
    answers = tmp_path / "answers.json"; answers.write_text(json.dumps({"ecosystem_root": value}))
    proc = install(bmad_project, "--answers", str(answers))
    assert proc.returncode == 0, proc.stdout
    actual = yaml.safe_load((bmad_project / "_bmad/config.yaml").read_text())["g33"]["ecosystem_root"]
    assert type(actual) is str and actual == value


def test_S9_registry_owner_is_agent_registry():
    mapping = G.load_ecosystem_map(MODULE)
    notes = mapping["routes"]["project_provisioning"]["notes"]
    assert "agent-registry" in notes and "Flume-owned agents registry" not in notes
    routed = G.ecosystem_route(MODULE, "provision project and registry")
    assert any("agent-registry" in row["notes"] for row in routed["routes"])


@pytest.mark.parametrize("code", ["'other-owner'", '"other-owner"', "'''other-owner'''", "42"])
def test_S10_foreign_toml_ownership_from_parsed_value(bmad_project, code):
    path = bmad_project / "_bmad/custom/config.toml"
    path.write_text(f"[modules.g33]\ncode = {code}\n")
    before = snapshot(bmad_project)
    proc = install(bmad_project)
    assert proc.returncode == 2, proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["status"] == "conflict" and payload["conflicts"]
    assert snapshot(bmad_project) == before
