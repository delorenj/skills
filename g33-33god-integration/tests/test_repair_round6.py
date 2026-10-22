"""Round 6: pre-6.12 BMAD customization resolvers (no --project-root).

Found in the PJAN-177 fleet sweep (bloodbank, candystore, srvls on BMAD
6.10.x): the bridge passed --project-root to a resolver whose argparse
rejected it, and the old resolver finds the project from the skill's REAL
path, so a catalog-linked skill resolves in the wrong project. Observation
must say so truthfully instead of failing with a usage error.
"""
from __future__ import annotations

import re

from conftest import install
from test_repair_round1 import bridge, snapshot, stage_skill


def downgrade_resolver(root):
    """Strip --project-root from the real resolver, as BMAD < 6.12 shipped it."""
    path = root / "_bmad" / "scripts" / "resolve_customization.py"
    text = path.read_text()
    old, count = re.subn(r'\n\s*parser\.add_argument\(\s*"--project-root".*?\n\s*\)\n', "\n", text, flags=re.S)
    assert count == 1, "fixture resolver no longer declares --project-root"
    path.write_text(old)
    return path


def test_R6_pre_612_resolver_is_unavailable_not_an_error(bmad_project):
    for name in ("bmad-build", "bmad-code-review", "bmad-prd", "bmad-spec", "bmad-architecture"):
        stage_skill(bmad_project, name)
    assert install(bmad_project).returncode == 0
    assert bridge(bmad_project, "observe")["status"] == "installed"
    downgrade_resolver(bmad_project)
    before = snapshot(bmad_project)
    reply = bridge(bmad_project, "observe")
    assert reply["status"] == "unavailable", reply
    assert "predates --project-root" in reply["summary"]
    assert "upgrade BMAD" in reply["summary"]
    assert reply["evidence"], "evidence gathered before the resolver check is kept"
    assert snapshot(bmad_project) == before
