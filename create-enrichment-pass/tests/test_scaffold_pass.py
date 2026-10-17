"""Isolated stdlib tests for the pass scaffold.

Every test runs the real scaffold as a subprocess inside a temporary
directory; nothing here touches a live registry, pipeline, provider, or the
HeyMa checkout.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "scaffold_pass.py"
REASON_LINE = re.compile(r"^reason_code=([a-z_]+)$")

DOCUMENT_FIXTURE = (
    "---\ntitle: Existing\ncaptured: 2026-10-17T09:00:00Z\n---\n\n"
    "# Planning\n\nWe should ship the contract first.\n"
)
TRANSCRIPT_FIXTURE = (
    "---\ntitle: Standup\n---\n\n[00:01] Alice: queue is drained.\n"
    "[00:14] Bob: diarization held on CUDA.\n"
)


def run_scaffold(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def run_pass(executable: Path, document: Path, item_id: str = "opaque-id") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(executable), str(document), item_id],
        capture_output=True,
        text=True,
        check=False,
    )


def description_from_yaml(manifest: Path) -> str:
    """Recover the description without a YAML dependency.

    json.dumps output is a valid single-line YAML double-quoted scalar, so the
    remainder of the `description:` line is parseable as JSON.
    """
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.startswith("description: "):
            return json.loads(line[len("description: "):])
    raise AssertionError("no description line in " + str(manifest))


class RegistryGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.registry = Path(self._tmp.name) / "passes.d"
        self.addCleanup(self._tmp.cleanup)

    def scaffold(self, *extra: str, slug: str = "demo-pass") -> subprocess.CompletedProcess[str]:
        result = run_scaffold(slug, "--registry-dir", str(self.registry), *extra)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def manifest(self, slug: str = "demo-pass") -> Path:
        return self.registry / f"{slug}.yaml"

    def executable(self, slug: str = "demo-pass") -> Path:
        return self.registry / "bin" / slug

    def test_wax_defaults_to_document_capability(self) -> None:
        self.scaffold("--host", "wax")
        text = self.manifest().read_text(encoding="utf-8")
        self.assertIn("capabilities: [document]", text)
        self.assertIn("enabled: false", text)
        self.assertIn("auto: false", text)
        self.assertIn(
            'command: ["{component_root}/config/passes.d/bin/demo-pass", "{md_path}", "{item_id}"]',
            text,
        )
        self.assertTrue(self.executable().stat().st_mode & 0o111, "executable bit missing")

    def test_wax_optional_audio_capability(self) -> None:
        self.scaffold("--host", "wax", "--capability", "audio")
        self.assertIn(
            "capabilities: [audio]", self.manifest().read_text(encoding="utf-8")
        )

    def test_wax_both_capabilities(self) -> None:
        self.scaffold(
            "--host", "wax", "--capability", "audio", "--capability", "document"
        )
        self.assertIn(
            "capabilities: [document, audio]",
            self.manifest().read_text(encoding="utf-8"),
        )

    def test_generic_host_has_no_capabilities(self) -> None:
        self.scaffold()
        text = self.manifest().read_text(encoding="utf-8")
        self.assertNotIn("capabilities", text)
        self.assertIn(
            'command: ["bin/demo-pass", "{document_path}", "{item_id}"]', text
        )

    def test_capability_rejected_for_generic_host(self) -> None:
        result = run_scaffold(
            "demo-pass", "--registry-dir", str(self.registry), "--capability", "document"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.manifest().exists())

    def test_slug_starting_with_digit_rejected(self) -> None:
        for slug in ("1pass", "911", "0x"):
            result = run_scaffold(slug, "--registry-dir", str(self.registry))
            self.assertNotEqual(result.returncode, 0, slug)
        self.assertFalse(self.registry.exists())

    def test_malicious_slug_rejected(self) -> None:
        for slug in ("../evil", "evil;rm -rf", "has_underscore", "has space", "-lead", "UPPER", ""):
            result = run_scaffold(slug, "--registry-dir", str(self.registry))
            self.assertNotEqual(result.returncode, 0, repr(slug))
        self.assertFalse(self.registry.exists())

    def test_slug_with_digits_after_letter_accepted(self) -> None:
        self.scaffold(slug="x2-tldr")

    def test_descriptions_round_trip(self) -> None:
        cases = [
            "",
            'He said "ship it" twice',
            "line one\nline two\ttabbed",
            "ends with backslash \\ and \"quote\"",
            "placeholders {md_path} and {item_id} stay literal",
            "unicode — naïve café",
        ]
        for index, description in enumerate(cases):
            with self.subTest(description=description):
                slug = f"pass-{index}"
                self.scaffold(
                    "--host", "wax",
                    "--description", description,
                    slug=slug,
                )
                self.assertEqual(
                    description_from_yaml(self.manifest(slug)), description
                )

    def test_generated_executable_compiles_with_tricky_description(self) -> None:
        description = 'Quotes "here", \backslash, and """triple"""'
        self.scaffold("--host", "wax", "--description", description)
        generated = self.executable().read_text(encoding="utf-8")
        compile(generated, str(self.executable()), "exec")  # must be valid Python
        self.assertIn('"""' + description.replace("\\", "\\\\").replace('"', '\\"'), generated)

    def test_collision_refuses_and_preserves_existing(self) -> None:
        self.scaffold("--host", "wax")
        manifest_before = self.manifest().read_bytes()
        executable_before = self.executable().read_bytes()
        result = run_scaffold("demo-pass", "--registry-dir", str(self.registry), "--host", "wax")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to overwrite", result.stderr)
        self.assertEqual(self.manifest().read_bytes(), manifest_before)
        self.assertEqual(self.executable().read_bytes(), executable_before)

    def test_partial_collision_still_refuses(self) -> None:
        self.registry.mkdir(parents=True)
        sentinel = b"# operator-owned executable\n"
        (self.registry / "bin").mkdir()
        (self.executable()).write_bytes(sentinel)
        result = run_scaffold("demo-pass", "--registry-dir", str(self.registry), "--host", "wax")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.manifest().exists(), "manifest must not appear on collision")
        self.assertEqual(self.executable().read_bytes(), sentinel)


class GeneratedPassTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.registry = root / "passes.d"
        result = run_scaffold(
            "demo-pass", "--registry-dir", str(self.registry), "--host", "wax"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.executable = self.registry / "bin" / "demo-pass"
        self.document = root / "fixture.md"

    def write_document(self, text: str) -> None:
        self.document.write_text(text, encoding="utf-8")

    def test_document_fixture_purity(self) -> None:
        self.write_document(DOCUMENT_FIXTURE)
        before = self.document.read_bytes()
        result = run_pass(self.executable, self.document)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["wax_ep_version"], 1)
        self.assertIsInstance(payload["frontmatter"], dict)
        self.assertEqual(self.document.read_bytes(), before, "pass mutated its input")

    def test_transcript_fixture_and_idempotence(self) -> None:
        self.write_document(TRANSCRIPT_FIXTURE)
        before = self.document.read_bytes()
        first = run_pass(self.executable, self.document, item_id="20261017-090000")
        second = run_pass(self.executable, self.document, item_id="20261017-090000")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout, "rerun was not idempotent")
        self.assertEqual(self.document.read_bytes(), before)

    def test_nonexistent_input_reports_reason_code(self) -> None:
        result = run_pass(self.executable, self.document)  # never written
        self.assertNotEqual(result.returncode, 0)
        match = REASON_LINE.match(result.stderr.splitlines()[0])
        self.assertIsNotNone(match, result.stderr)
        self.assertEqual(match.group(1), "not_a_file")

    def test_bodyless_document_reports_empty_document(self) -> None:
        self.write_document("---\ntitle: Only frontmatter\n---\n")
        result = run_pass(self.executable, self.document)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(REASON_LINE.match(result.stderr.splitlines()[0]).group(1), "empty_document")

    def test_non_utf8_document_reports_undecodable(self) -> None:
        self.document.write_bytes(b"\xff\xfe\x00 not text \xff")
        result = run_pass(self.executable, self.document)
        self.assertNotEqual(result.returncode, 0)
        code = REASON_LINE.match(result.stderr.splitlines()[0]).group(1)
        self.assertEqual(code, "undecodable")
        self.assertNotIn("8", code, "runner reason codes reject digits")


if __name__ == "__main__":
    unittest.main()
