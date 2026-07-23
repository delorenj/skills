from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config
from test_reportctl import reportctl, reportctl_runtime


class ProfileConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "hermes"
        self.home.mkdir()
        skill = self.home / "skills" / "delonet-daily-report" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("skill", encoding="utf-8")
        self.value = config(self.root)
        self.environment = mock.patch.dict(
            os.environ,
            {"HOME": str(self.root), "HERMES_HOME": str(self.home), "HERMES_TIMEZONE": ""},
            clear=False,
        )
        self.environment.start()

    def tearDown(self) -> None:
        self.environment.stop()
        self.temporary.cleanup()

    def write_profile(self, value: str) -> None:
        (self.home / "config.yaml").write_text(value, encoding="utf-8")

    def test_real_nested_profile_passes_preflight(self) -> None:
        self.write_profile(
            "timezone: America/New_York\nmodel:\n  provider: openai-codex\n  default: gpt-5.4\n"
        )
        reportctl.timezone_preflight(self.value)

    def test_canonical_skill_pointer_passes_preflight(self) -> None:
        skill_root = self.root / "code" / "skillex" / "all-skills" / "delonet-daily-report"
        skill_root.mkdir(parents=True)
        (skill_root / "SKILL.md").write_text("skill", encoding="utf-8")
        canonical = self.root / ".agents" / "skills" / "delonet-daily-report"
        canonical.parent.mkdir(parents=True)
        canonical.symlink_to(skill_root, target_is_directory=True)
        profile_skill = self.home / "skills" / "delonet-daily-report"
        (profile_skill / "SKILL.md").unlink()
        profile_skill.rmdir()
        profile_skill.write_text(str(canonical), encoding="utf-8")
        self.write_profile(
            "timezone: America/New_York\nmodel:\n  provider: openai-codex\n  default: gpt-5.4\n"
        )
        reportctl.timezone_preflight(self.value)

    def test_symlinked_skill_under_canonical_root_passes(self) -> None:
        skill_root = self.root / ".agents" / "skills" / "delonet-daily-report"
        skill_root.mkdir(parents=True)
        (skill_root / "SKILL.md").write_text("skill", encoding="utf-8")
        profile_skill = self.home / "skills" / "delonet-daily-report"
        (profile_skill / "SKILL.md").unlink()
        profile_skill.rmdir()
        relative = os.path.relpath(skill_root, profile_skill.parent)
        profile_skill.symlink_to(relative, target_is_directory=True)
        self.assertTrue(reportctl_runtime.profile_skill_installed("delonet-daily-report"))

    def test_direct_profile_symlink_to_untrusted_directory_is_rejected(self) -> None:
        untrusted = self.root / "untrusted" / "delonet-daily-report"
        untrusted.mkdir(parents=True)
        (untrusted / "SKILL.md").write_text("skill", encoding="utf-8")
        profile_skill = self.home / "skills" / "delonet-daily-report"
        (profile_skill / "SKILL.md").unlink()
        profile_skill.rmdir()
        profile_skill.symlink_to(untrusted, target_is_directory=True)
        self.assertFalse(reportctl_runtime.profile_skill_installed("delonet-daily-report"))

    def test_canonical_pointer_follows_multiple_symlinks(self) -> None:
        physical = self.root / "physical" / "delonet-daily-report"
        physical.mkdir(parents=True)
        (physical / "SKILL.md").write_text("skill", encoding="utf-8")
        hop = self.root / "hop"
        hop.symlink_to(physical, target_is_directory=True)
        canonical = self.root / ".agents" / "skills" / "delonet-daily-report"
        canonical.parent.mkdir(parents=True)
        canonical.symlink_to(hop, target_is_directory=True)
        profile_skill = self.home / "skills" / "delonet-daily-report"
        (profile_skill / "SKILL.md").unlink()
        profile_skill.rmdir()
        profile_skill.write_text(str(canonical), encoding="utf-8")
        self.assertTrue(reportctl_runtime.profile_skill_installed("delonet-daily-report"))

    def test_unsafe_or_broken_skill_pointers_fail_closed(self) -> None:
        profile_skill = self.home / "skills" / "delonet-daily-report"
        (profile_skill / "SKILL.md").unlink()
        profile_skill.rmdir()
        self.write_profile(
            "timezone: America/New_York\nmodel:\n  provider: openai-codex\n  default: gpt-5.4\n"
        )
        secret = "github_pat_abcdefghijklmnopqrstuvwxyz123456"
        unapproved = self.root / "unapproved" / "delonet-daily-report"
        unapproved.mkdir(parents=True)
        (unapproved / "SKILL.md").write_text("skill", encoding="utf-8")
        approved = self.root / ".agents" / "skills" / "delonet-daily-report"
        approved.mkdir(parents=True)
        (approved / "SKILL.md").write_text("skill", encoding="utf-8")
        for pointer in (
            "relative/path",
            "/missing/skill",
            "/first/path\n/second/path\n",
            str(unapproved),
            str(approved.parent / ".." / "skills" / "delonet-daily-report"),
            f"/tmp/{secret}",
            f"{approved}\x00suffix",
            "/" + ("x" * 4097),
        ):
            with self.subTest(pointer=pointer.splitlines()[0]):
                profile_skill.write_text(pointer, encoding="utf-8")
                with self.assertRaisesRegex(reportctl.ConfigError, "must be installed"):
                    reportctl.timezone_preflight(self.value)

    def test_looping_and_dangling_symlinks_fail_closed(self) -> None:
        profile_skill = self.home / "skills" / "delonet-daily-report"
        (profile_skill / "SKILL.md").unlink()
        profile_skill.rmdir()
        for target in (profile_skill, self.root / "missing"):
            with self.subTest(target=target.name):
                profile_skill.symlink_to(target, target_is_directory=True)
                self.assertFalse(reportctl_runtime.profile_skill_installed("delonet-daily-report"))
                profile_skill.unlink()

    def test_skill_marker_symlink_cannot_escape_final_directory(self) -> None:
        physical = self.root / "physical" / "delonet-daily-report"
        physical.mkdir(parents=True)
        outside = self.root / "outside-SKILL.md"
        outside.write_text("skill", encoding="utf-8")
        (physical / "SKILL.md").symlink_to(outside)
        canonical = self.root / ".agents" / "skills" / "delonet-daily-report"
        canonical.parent.mkdir(parents=True)
        canonical.symlink_to(physical, target_is_directory=True)
        profile_skill = self.home / "skills" / "delonet-daily-report"
        (profile_skill / "SKILL.md").unlink()
        profile_skill.rmdir()
        profile_skill.write_text(str(canonical), encoding="utf-8")
        self.assertFalse(reportctl_runtime.profile_skill_installed("delonet-daily-report"))

    def test_profile_subset_rejects_unsupported_yaml_constructs(self) -> None:
        probes = {
            "top-level sequences": "- timezone: America/New_York\n",
            "directives": "%YAML 1.2\n---\ntimezone: America/New_York\n",
            "end markers": "timezone: America/New_York\n...\n",
            "nested values": "model: gpt-5.4\n  provider: openai-codex\n",
            "flow nesting": "model: {provider: openai-codex, default: gpt-5.4}\n  extra: value\n",
            "block scalars": "model: |\n  gpt-5.4\n",
            "folded scalars": "model: >-\n  gpt-5.4\n",
        }
        for message, profile in probes.items():
            with self.subTest(message=message):
                self.write_profile(profile)
                with self.assertRaises(reportctl.ConfigError):
                    reportctl_runtime.profile_config()

    def test_plain_hash_and_unrelated_sections_are_supported(self) -> None:
        self.write_profile(
            "unrelated:\n"
            "  items:\n"
            "    - one\n"
            "timezone: America/New_York # comment\n"
            "provider: openai-codex\n"
            "model: gpt#5.4\n"
        )
        profile = reportctl_runtime.profile_config()
        self.assertEqual("gpt#5.4", profile["model"])

    def test_live_shaped_quotes_and_escapes_are_supported(self) -> None:
        self.write_profile(
            "unrelated:\n"
            "  plain: it's valid YAML\n"
            '  double: "say \\"hello\\" # still quoted" # comment\n'
            "  single: 'it''s quoted'\n"
            "timezone: America/New_York\n"
            "model: {provider: openai-codex, default: gpt#5.4}\n"
        )
        profile = reportctl_runtime.profile_config()
        self.assertEqual("gpt#5.4", profile["model"]["default"])

    def test_unterminated_quotes_are_rejected_globally(self) -> None:
        for profile in (
            'unrelated: "unterminated\n',
            "unrelated:\n  nested: 'unterminated\n",
            'unrelated: {nested: "unterminated}\n',
        ):
            with self.subTest(profile=profile[:12]):
                self.write_profile(profile)
                with self.assertRaisesRegex(reportctl.ConfigError, "unterminated quoted"):
                    reportctl_runtime.profile_config()

    def test_flow_nested_profile_passes_preflight(self) -> None:
        self.write_profile(
            "timezone: America/New_York\nmodel: { provider: openai-codex, default: gpt-5.4 }\n"
        )
        reportctl.timezone_preflight(self.value)

    def test_flat_profile_remains_compatible(self) -> None:
        self.write_profile("timezone: America/New_York\nprovider: openai-codex\nmodel: gpt-5.4\n")
        reportctl.timezone_preflight(self.value)

    def test_flat_and_nested_inference_is_rejected_as_ambiguous(self) -> None:
        self.write_profile(
            "timezone: America/New_York\n"
            "provider: openai-codex\n"
            "model:\n"
            "  provider: openai-codex\n"
            "  default: gpt-5.4\n"
        )
        with self.assertRaisesRegex(reportctl.ConfigError, "ambiguous"):
            reportctl_runtime.profile_config()

    def test_duplicate_nested_setting_is_rejected(self) -> None:
        self.write_profile(
            "model:\n  provider: openai-codex\n  provider: openrouter\n  default: gpt-5.4\n"
        )
        with self.assertRaisesRegex(reportctl.ConfigError, "duplicate model.provider"):
            reportctl_runtime.profile_config()

    def test_aliases_and_tags_are_rejected_without_echoing_values(self) -> None:
        secret = "github_pat_abcdefghijklmnopqrstuvwxyz123456"
        for profile in (
            f"model:\n  provider: !secret {secret}\n  default: gpt-5.4\n",
            "model:\n  provider: &provider openai-codex\n  default: *provider\n",
            "defaults: &defaults\n  provider: openai-codex\nmodel:\n  <<: *defaults\n",
        ):
            with self.subTest(profile=profile[:6]):
                self.write_profile(profile)
                with self.assertRaises(reportctl.ConfigError) as raised:
                    reportctl_runtime.profile_config()
                self.assertNotIn(secret, str(raised.exception))
                self.assertRegex(str(raised.exception), "unsupported YAML")


if __name__ == "__main__":
    unittest.main()
