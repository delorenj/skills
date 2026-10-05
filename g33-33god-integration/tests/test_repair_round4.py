"""Tests-first S13 delimiter-family regressions against frozen round three."""
import pytest

from conftest import MODULE_ROOT as MODULE
from test_repair_round2 import VALID, bundle, implementation_section
import g33lib as G


def fence_cases():
    cases = []
    prefixes = ("", "   ", "    ", "\t", "> ", "> - ")
    for delimiter in (chr(96), "~"):
        for length in (3, 4, 32):
            for index, prefix in enumerate(prefixes):
                info = ("", "text", "python title=file")[index % 3]
                for closed in (False, True):
                    fence = delimiter * length
                    proof = prefix + fence + info + "\n=== 3 passed in 0.12s ===\ncommand_exit_code=0\n"
                    if closed:
                        proof += prefix + fence + "\n"
                    label = f"{ord(delimiter)}-{length}-{index}-{closed}"
                    cases.append(pytest.param(proof, id=label))
    return cases


@pytest.mark.parametrize("proof", fence_cases())
def test_S13_any_fence_family_length_context_never_certifies(tmp_path, proof):
    assert G.parse_test_proof(proof)["clean_pass"] is False
    data = bundle(tmp_path, VALID, proof, links=[{
        "claim": "implemented change", "acceptance_criteria": ["AC1"],
        "diff_paths": ["src/a.py"],
    }])
    handoff = G.generate_handoff(MODULE, data)
    assert "test proof VERIFIED" not in handoff
    assert "claimed-unverified: implemented change" in implementation_section(handoff)


@pytest.mark.parametrize("delimiter", [chr(96), "~"])
@pytest.mark.parametrize("prefix,suffix", [
    ("\x1b[0m", "\x1b[0m"),
    ("\x00", "\x00"),
    ("\x08", "\x08"),
    ("\r", "\r"),
    ("note: ", " inline"),
    ("- ", ""),
    ("  1. ", ""),
    ("\\", ""),
])
def test_S13_control_adjacent_or_embedded_fence_never_certifies(tmp_path, delimiter, prefix, suffix):
    proof = prefix + delimiter * 5 + suffix + "\n3 passed\nexit_code=0\n"
    assert G.parse_test_proof(proof)["clean_pass"] is False
    handoff = G.generate_handoff(MODULE, bundle(tmp_path, VALID, proof))
    assert "test proof VERIFIED" not in handoff


@pytest.mark.parametrize("proof", [
    "3 passed\nexit_code=0\n",
    "=== 3 passed, 1 skipped in 0.12s ===\ncommand_exit_code=0\n",
    "Command: pytest A\n2 passed\nexit_code=0\nCommand: pytest B\n1 passed\nexit_code=0\n",
    "raw output without delimiters\n3 passed\nexit_code=0\n",
    "note has ~~ two markers\n3 passed\nexit_code=0\n",
    "note has " + chr(96)*2 + " two markers\n3 passed\nexit_code=0\n",
    "note has ~ one marker\n3 passed\nexit_code=0\n",
    "note has " + chr(96) + " one marker\n3 passed\nexit_code=0\n",
    "$ pytest tests/a.py\n3 passed in 0.12s (0:00:01)\ncommand_exit_code=0\n",
])
def test_S13_plain_raw_positive_behavior_retained(proof):
    assert G.parse_test_proof(proof)["clean_pass"] is True
