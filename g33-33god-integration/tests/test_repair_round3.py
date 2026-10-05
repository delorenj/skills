"""Tests-first regressions for round-two independent SPEC S11 and S12."""
import json

import pytest
import yaml

from conftest import MODULE_ROOT as MODULE, install
from test_repair_round1 import bridge, snapshot, stage_skill
from test_repair_round2 import VALID, bundle, implementation_section
import g33lib as G


@pytest.mark.parametrize("text", [
    "This note expects 3 passed, but no tests were executed.",
    "Expected output: 3 passed",
    "prefix 3 passed",
    "3 passed suffix",
    "3 passed but not executed",
    "3 passed # sample only",
    "[expected] 3 passed",
    "3 passed in 0.12s expected",
    "=== 3 passed in 0.12s === expected",
    "=== 3 passed",
    "3 passed ===",
    "3 passed, 2 passed",
    "3 passed, 0 failed, 1 failed",
    "3 passed, 0 errors, 1 error",
    "3 passed, 4 unsupported",
    "-3 passed",
    "1.5 passed",
    "Expected output:\n3 passed",
    "# Expected output\n3 passed",
    "Example summary:\n=== 3 passed in 0.12s ===",
    chr(96)*3+"text\n3 passed",
    "prose expects 2 passed\n3 passed",
])
def test_S11_unsupported_summary_never_certifies(tmp_path, text):
    proof = text + "\ncommand_exit_code=0\n"
    parsed = G.parse_test_proof(proof)
    assert parsed["clean_pass"] is False, parsed
    data = bundle(tmp_path, VALID, proof, links=[{
        "claim": "implemented change", "acceptance_criteria": ["AC1"],
        "diff_paths": ["src/a.py"],
    }])
    handoff = G.generate_handoff(MODULE, data)
    assert "test proof VERIFIED" not in handoff
    assert "claimed-unverified: implemented change" in implementation_section(handoff)


@pytest.mark.parametrize("summary", [
    "3 passed",
    " \t3 passed \t",
    "3 passed, 0 failed",
    "3 passed, 1 skipped, 2 deselected",
    "3 passed, 1 warning in 0.12s",
    "3 passed, 1 xfailed, 1 xpassed in 1s",
    "3 passed in 0.12s (0:00:01)",
    "================ 3 passed in 0.12s ================",
    "=== 3 passed, 1 skipped, 2 warnings in 0.12s ===",
])
def test_S11_complete_supported_summary_valid(summary):
    parsed = G.parse_test_proof(summary + "\nexit_code=0\n")
    assert parsed["clean_pass"] is True, parsed
    assert parsed["passed"] == 3 and len(parsed["blocks"]) == 1


def test_S11_counts_only_from_supported_summary_and_per_block_exits():
    valid = G.parse_test_proof(
        "Command: pytest A\n=== 2 passed in 0.1s ===\nexit_code=0\n"
        "Command: pytest B\n1 passed, 1 skipped in 0.2s\ncommand_exit_code=0\n")
    assert valid["clean_pass"] is True and valid["passed"] == 3
    invalid = G.parse_test_proof(
        "Command: pytest A\n2 passed\nexit_code=0\ncommand_exit_code=0\n"
        "Command: pytest B\n1 passed\n")
    assert invalid["clean_pass"] is False
    assert G.parse_test_proof("3 passed, 1 failed in 0.2s\nexit_code=0\n")["clean_pass"] is False


FOREIGN = [
    "g33:\n  ecosystem_root: foreign-owner\n",
    "'g33':\n  ecosystem_root: foreign-owner\n",
    '"g33":\n  ecosystem_root: foreign-owner\n',
    '"g\\u0033\\u0033":\n  ecosystem_root: foreign-owner\n',
    '? "g33"\n:\n  ecosystem_root: foreign-owner\n',
    "? |-\n  g33\n:\n  ecosystem_root: foreign-owner\n",
    "? >-\n  g33\n:\n  ecosystem_root: foreign-owner\n",
    "'g33': {ecosystem_root: foreign-owner}\n",
    "{'g33': {ecosystem_root: foreign-owner}}\n",
    "'g33': foreign-owner\n",
]


@pytest.mark.parametrize("foreign", FOREIGN)
@pytest.mark.parametrize("force", [False, True])
def test_S12_foreign_equivalent_namespace_refused_zero_writes(bmad_project, tmp_path, foreign, force):
    (bmad_project / "_bmad/config.yaml").write_text(foreign)
    outside = tmp_path / "outside"; outside.mkdir()
    (outside / "sentinel").write_text("preserve")
    before = snapshot(bmad_project), snapshot(outside)
    proc = install(bmad_project, *(["--force"] if force else []))
    assert proc.returncode == 2, proc.stdout
    result = json.loads(proc.stdout)
    assert result["status"] == "conflict" and result["conflicts"]
    assert any("g33" in c["detail"] for c in result["conflicts"])
    assert (snapshot(bmad_project), snapshot(outside)) == before
    assert bridge(bmad_project, "apply")["status"] == "conflict"
    assert (snapshot(bmad_project), snapshot(outside)) == before


@pytest.mark.parametrize("text", [
    '# managed by g33 installer\n"g33":\n  name: foreign\n',
    'other:\n  # managed by g33 installer\n  name: unrelated\n"g33":\n  name: foreign\n',
    '"g33":\n  name: foreign\nother:\n  # managed by g33 installer\n  name: unrelated\n',
    '"g33":\n  note: "# managed by g33 installer"\n',
    '"g33":\n  note: |\n    # managed by g33 installer\n',
    '"g33":\n  nested:\n    # managed by g33 installer\n    name: foreign\n',
    '"g33":\n  # managed by g33 installer-lookalike\n  name: foreign\n',
    '"g33": # managed by g33 installer\n  name: foreign\n',
    'template: &foreign\n  # managed by g33 installer\n  name: foreign\n"g33": *foreign\n',
    'template: &foreign\n  name: foreign\n<<: {g33: *foreign}\n',
])
def test_S12_foreign_marker_elsewhere_or_scalar_never_authorizes(bmad_project, text):
    (bmad_project / "_bmad/config.yaml").write_text(text)
    before = snapshot(bmad_project)
    proc = install(bmad_project, "--force")
    assert proc.returncode == 2, proc.stdout
    result = json.loads(proc.stdout)
    assert result["conflicts"] and any("g33" in c["detail"] for c in result["conflicts"])
    assert snapshot(bmad_project) == before
    assert bridge(bmad_project, "apply")["status"] == "conflict"
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("duplicate", [
    'g33:\n  name: one\n"g33":\n  name: two\n',
    "'g33': {}\n\"g\\u0033\\u0033\": {}\n",
    '? "g33"\n: {}\n? |-\n  g33\n: {}\n',
    '{"g33": {}, g33: {}}\n',
])
def test_S12_equivalent_duplicate_namespace_refused(bmad_project, duplicate):
    (bmad_project / "_bmad/config.yaml").write_text(duplicate)
    before = snapshot(bmad_project)
    proc = install(bmad_project)
    assert proc.returncode == 2, proc.stdout
    assert "duplicate" in proc.stdout
    assert snapshot(bmad_project) == before


@pytest.mark.parametrize("header", ["'g33':", '"g33":', '"g\\u0033\\u0033":',
                                  '? "g33"\n:', "? |-\n  g33\n:", "? >-\n  g33\n:", "g33: &owned", '"g33": &owned'])
@pytest.mark.parametrize("force", [False, True])
def test_S12_managed_equivalent_block_preserved_observed(bmad_project, header, force):
    stage_skill(bmad_project)
    assert install(bmad_project).returncode == 0
    path = bmad_project / "_bmad/config.yaml"
    text = path.read_text().replace("\ng33:\n", "\n" + header + "\n")
    text = text.replace('  ecosystem_root: "."', '  ecosystem_root: "operator-root" # inline')
    text += '  nested:\n    ecosystem_root: keep-nested # child comment\n'
    path.write_text(text)
    proc = install(bmad_project, *(["--force"] if force else []))
    assert proc.returncode == 0, proc.stdout
    after = path.read_text()
    assert header + "\n" in after and "# inline" in after and "# child comment" in after
    data = yaml.safe_load(after)["g33"]
    assert data["ecosystem_root"] == ("." if force else "operator-root")
    assert data["nested"] == {"ecosystem_root": "keep-nested"}
    before = snapshot(bmad_project)
    assert bridge(bmad_project, "observe")["status"] == "installed"
    assert snapshot(bmad_project) == before
    assert install(bmad_project, *(["--force"] if force else [])).returncode == 0
    assert snapshot(bmad_project) == before
