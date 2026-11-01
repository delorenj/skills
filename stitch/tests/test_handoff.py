"""Offline contracts for the Stitch/BMAD handoff; never contacts Google."""
from pathlib import Path
import re
import tomllib
import unittest


SKILL = Path(__file__).resolve().parents[1]
CATALOG = SKILL.parent


class StitchHandoffTests(unittest.TestCase):
    def test_portable_metadata(self):
        text = (SKILL / "SKILL.md").read_text()
        metadata = text.split("---", 2)[1]
        self.assertEqual(re.findall(r"^(\w+):", metadata, re.M), ["name", "description"])
        self.assertIn("name: stitch", metadata)

    def test_relative_markdown_targets_exist(self):
        paths = [SKILL / "SKILL.md", SKILL / "references/33god-handoff.md",
                 CATALOG / "bmad-ux/references/stitch-handoff.md"]
        for path in paths:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in target and not target.startswith("#"):
                    with self.subTest(path=path, target=target):
                        self.assertTrue((path.parent / target.split("#")[0]).exists())

    def test_bmad_registry_delegates_to_skill(self):
        config = tomllib.loads((CATALOG / "bmad-ux/customize.toml").read_text())
        entries = config["workflow"]["design_handoffs"]
        self.assertTrue(any("skill:stitch" in entry for entry in entries))
        self.assertTrue(any("references/stitch-handoff.md" in entry for entry in entries))

    def test_bmad_entrypoint_has_concrete_handoff(self):
        text = (CATALOG / "bmad-ux/SKILL.md").read_text()
        self.assertIn("references/stitch-handoff.md", text)
        self.assertIn("Resume Update/Finalize", text)

    def test_hub_routes_to_canonical_skill(self):
        self.assertIn("../stitch/SKILL.md", (CATALOG / "33god-hub/SKILL.md").read_text())

    def test_handoff_preserves_authority_and_pending_choice(self):
        text = (SKILL / "references/33god-handoff.md").read_text()
        for expected in ["selection pending", "EXPERIENCE.md", "DESIGN.md",
                         ".working/stitch/handoff.md", "Both spines", "win"]:
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_cli_examples_preview_remote_generation(self):
        text = (SKILL / "SKILL.md").read_text()
        for command in ["stitch generate screen", "stitch generate variant"]:
            example = text.split(command, 1)[1].split("\n\n", 1)[0]
            self.assertIn("--dry-run", example)
        self.assertIn("stitch download screen", text)
        self.assertNotIn("stitch config set apiKey", text)

    def test_private_delivery_and_manual_provenance_are_explicit(self):
        skill = (SKILL / "SKILL.md").read_text()
        handoff = (SKILL / "references/33god-handoff.md").read_text()
        self.assertIn("separate approval", skill)
        self.assertIn("user-supplied Canvas links", handoff)
        self.assertIn("promote copies", handoff)
        self.assertIn("Keep original Stitch exports", handoff)

    def test_no_skill_installer_or_workspace_loop(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertIn("Never run", text)
        self.assertIn("stitch agent-skills add", text)
        self.assertIn("enable workspace `loop`", text)


if __name__ == "__main__":
    unittest.main()
