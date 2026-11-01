"""Bounded applicability contract checks, not a model-routing evaluation.

Run: python3 -B -m unittest discover -s bmad-build/tests -v
"""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


class ApplicabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL.read_text()
        cls.commands = re.findall(r"```bash\n(.*?)\n```", cls.text, re.DOTALL)
        cls.gate = cls.commands[0]

    def test_description_limits_automatic_selection(self):
        description = self.text.split("description: ", 1)[1].splitlines()[0]
        self.assertIn("Automatically select only when", description)
        self.assertIn("_bmad/scripts/render_skill.py", description)
        self.assertIn("In non-BMAD projects, use the repo-native workflow instead", description)

    def test_missing_renderer_checks_without_running_build(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary:
            root = Path(temporary) / "Foundry content"
            root.mkdir()
            (root / "skills").mkdir()
            command = self.gate.replace("{project-root}", str(root))
            result = subprocess.run(["bash", "-c", command], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout + result.stderr, "")
            self.assertFalse((root / "_bmad").exists())

    def test_bmad_directory_alone_does_not_qualify(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary:
            root = Path(temporary)
            (root / "_bmad").mkdir()
            command = self.gate.replace("{project-root}", str(root))
            self.assertEqual(subprocess.run(["bash", "-c", command]).returncode, 1)

    def test_existing_renderer_passes_without_executing_it_or_changing_cwd(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary:
            root = Path(temporary) / "BMAD project"
            renderer = root / "_bmad/scripts/render_skill.py"
            renderer.parent.mkdir(parents=True)
            renderer.write_text("raise RuntimeError('preflight must not execute me')\n")
            command = self.gate.replace("{project-root}", str(root))
            before = Path.cwd()
            result = subprocess.run(["bash", "-c", command], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout + result.stderr, "")
            self.assertEqual(Path.cwd(), before)

    def test_ordinary_and_explicit_invocations_have_distinct_missing_paths(self):
        preflight = self.text.split("## Run in a BMAD-enabled project", 1)[0]
        self.assertIn("continue the already-authorized task with the repo-native workflow", preflight)
        self.assertIn("including `/bmad-build`", preflight)
        self.assertIn("report the exact missing prerequisite and stop this skill", preflight)
        self.assertIn("do not install BMAD", preflight)
        self.assertIn("for Foundry game content, `ltf-make-game`", preflight)

    def test_real_renderer_failure_still_halts(self):
        self.assertEqual(len(self.commands), 2)
        self.assertEqual(
            self.commands[1],
            'uv run --no-cache "{project-root}/_bmad/scripts/render_skill.py" '
            '--project-root "{project-root}" --skill "{skill-root}"',
        )
        self.assertIn("On failure (including `uv` being unavailable), report the command output and HALT", self.text)


if __name__ == "__main__":
    unittest.main()
