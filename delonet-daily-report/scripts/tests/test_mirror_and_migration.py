"""Regressions for the git-tracked mirror and for the v1 -> v2 config migration.

Both defects here are the same defect wearing different clothes: a step that
reports success while quietly destroying, or quietly refusing to do, the work
the operator asked for.

MIRROR
    Round 2 replaced two in-place ``atomic_write`` calls with a directory swap
    (``rename(target -> .retired)`` then ``rename(.stage -> target)``). That
    made a torn *pair* impossible and made losing the whole *day* possible:

      * the swap replaces the entire day directory, so every file in it that the
        pipeline did not write is deleted. Measured on the live mirror:
        ``_bmad-output/daily-journals/2026-08-17/`` holds ``journal.txt``
        (17811 B) and ``report_event.json`` (1766 B), neither written by this
        pipeline, both destroyed by the swap;
      * a kill during staging strands ``.stage-<uuid>`` in a git-tracked
        directory forever;
      * a kill between the two renames leaves no day directory at all.

    The tests below pin the corrected contract: write in place, touch only the
    two files we own, never create/swap/remove the day directory, sweep our own
    debris, and *report* a torn pair rather than trading it for data loss.

MIGRATION
    The live v1 config has all three topics ``enabled: false`` -- the state
    delonet died in on 2026-07-25. Round 2's migration carried that forward
    faithfully, produced a config that validates and watches almost nothing,
    and printed ``"migrated": true``. Migration may not inherit a dead file's
    state by default; the operator has to say what they meant, and a disabled
    section has to be shouted, not filed in a notes array.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from test_fixtures import config as v2_config
from test_reportctl import reportctl  # noqa: F401  (module + sys.path setup)
from test_reportctl_config import LIVE_V1, ROOTS
from test_run_pipeline import PipelineCase, complete_collector, register_stub

import run as runner  # noqa: E402

reportctl_config = importlib.import_module("reportctl_config")
ConfigError = importlib.import_module("reportctl_contracts").ConfigError
MODULE_PATH = Path(reportctl_config.__file__).resolve()
SCRIPTS = Path(runner.__file__).resolve().parent

#: Bytes of a file the mirror did not write and must never touch. The real one
#: is the hand-committed developer journal that sits beside the report pair.
FOREIGN = {
    "journal.txt": "hand-written journal for the day; not ours to delete\n",
    "report_event.json": json.dumps({"type": "bloodbank.v1.reporting.report.completed"}) + "\n",
}


class MirrorNeighbourTests(PipelineCase):
    """The mirror is a well-behaved writer in a directory it does not own."""

    def seed_foreign(self) -> Path:
        target = self.mirror / self.date
        target.mkdir(parents=True, exist_ok=True)
        for name, text in FOREIGN.items():
            (target / name).write_text(text, encoding="utf-8")
        return target

    def collectors(self, tag: str) -> dict:
        return self.with_collectors(
            register_stub(f"{tag}_1", complete_collector),
            register_stub(f"{tag}_2", complete_collector),
        )

    def test_mirroring_never_deletes_a_file_it_did_not_write(self) -> None:
        target = self.seed_foreign()
        outcome, code = self.run_pipeline(self.collectors("neighbour_a"), mirror=True)
        self.assertTrue(outcome["mirror"]["ok"], outcome["mirror"])
        self.assertEqual(0, code)
        for name, text in FOREIGN.items():
            self.assertTrue((target / name).exists(), f"{name} was deleted by the mirror")
            self.assertEqual(text, (target / name).read_text(encoding="utf-8"), name)
        self.assertTrue((target / "report.md").exists())
        self.assertTrue((target / "report.json").exists())

    def test_the_day_directory_itself_is_never_replaced(self) -> None:
        target = self.seed_foreign()
        before = target.stat().st_ino
        self.run_pipeline(self.collectors("neighbour_b"), mirror=True)
        self.assertTrue(target.exists(), "the day directory disappeared")
        self.assertEqual(before, target.stat().st_ino, "the day directory was swapped, not written")

    def test_the_mirror_sweeps_its_own_debris_and_only_its_own(self) -> None:
        target = self.seed_foreign()
        debris = target / ".report.json.ab12cd34"
        debris.write_text("half-written wreckage from a killed run", encoding="utf-8")
        keeper = target / ".gitkeep"
        keeper.write_text("", encoding="utf-8")
        self.run_pipeline(self.collectors("neighbour_c"), mirror=True)
        self.assertFalse(debris.exists(), "a stale mirror temp file was left in a git-tracked dir")
        self.assertTrue(keeper.exists(), "the mirror deleted a dotfile that was not its temp")
        for name in FOREIGN:
            self.assertTrue((target / name).exists(), name)


class MirrorHonestyTests(PipelineCase):
    """What the mirror says about itself has to be what happened."""

    def collectors(self, tag: str) -> dict:
        return self.with_collectors(
            register_stub(f"{tag}_1", complete_collector),
            register_stub(f"{tag}_2", complete_collector),
        )

    def test_a_successful_mirror_does_not_report_a_failure_reason(self) -> None:
        outcome, _ = self.run_pipeline(self.collectors("honest_a"), mirror=True)
        mirrored = outcome["mirror"]
        self.assertTrue(mirrored["ok"], mirrored)
        self.assertNotEqual("mirror_failed", mirrored["reason"])
        self.assertIsNone(mirrored["reason"], mirrored)
        self.assertIsNone(mirrored["error"], mirrored)

    def test_a_torn_pair_is_named_in_the_error_rather_than_hidden(self) -> None:
        value = self.collectors("honest_b")
        first, _ = self.run_pipeline(value, mirror=True)
        target = self.mirror / self.date
        real_text = runner.atomic_write_text

        def fail_on_the_markdown(path, text):
            if Path(path).name == "report.md" and str(path).startswith(str(self.mirror)):
                raise OSError("forced failure after report.json landed")
            return real_text(path, text)

        with mock.patch.object(runner, "atomic_write_text", fail_on_the_markdown):
            second, code = self.run_pipeline(value, mirror=True)

        mirrored = second["mirror"]
        self.assertFalse(mirrored["ok"], mirrored)
        self.assertEqual(0, code)
        self.assertEqual("mirror_failed", mirrored["reason"])
        self.assertIn("torn", mirrored["error"])
        self.assertIn("report.json", mirrored["error"])
        # The caveat carries it to the reader too.
        self.assertTrue(
            any("torn" in caveat for caveat in second["caveats"]), second["caveats"]
        )
        # And the tear is the shape we documented: json new, markdown old.
        self.assertEqual(
            second["run_id"], json.loads((target / "report.json").read_text())["run_id"]
        )
        self.assertTrue((target / "report.md").exists())

    def test_a_failed_mirror_leaves_no_temp_file_behind(self) -> None:
        value = self.collectors("honest_c")
        self.run_pipeline(value, mirror=True)
        real_text = runner.atomic_write_text

        def fail_on_the_markdown(path, text):
            if Path(path).name == "report.md" and str(path).startswith(str(self.mirror)):
                raise OSError("forced")
            return real_text(path, text)

        with mock.patch.object(runner, "atomic_write_text", fail_on_the_markdown):
            self.run_pipeline(value, mirror=True)
        leftovers = sorted(
            item.name
            for item in (self.mirror / self.date).iterdir()
            if item.name.startswith(".report.")
        )
        self.assertEqual([], leftovers)
        self.assertEqual(
            [], [item.name for item in self.mirror.iterdir() if item.name.startswith(".")]
        )

    def test_the_installed_pair_is_group_and_world_readable(self) -> None:
        self.run_pipeline(self.collectors("honest_d"), mirror=True)
        for name in ("report.md", "report.json"):
            mode = stat.S_IMODE((self.mirror / self.date / name).stat().st_mode)
            self.assertEqual(0o644, mode, name)


CHILD = textwrap.dedent(
    """
    import sys, time
    sys.path.insert(0, {scripts!r})
    import run as runner

    generation, date = sys.argv[1], sys.argv[2]
    real = runner.atomic_write_text

    def slow(path, text):
        print("WINDOW-OPEN", flush=True)
        time.sleep(120)
        return real(path, text)

    runner.atomic_write_text = slow
    runner.mirror_generation(date, {{"ok": True, "generation": generation}})
    """
)


class MirrorCrashTests(unittest.TestCase):
    """SIGKILL mid-mirror: survivable, not catastrophic.

    A kill can leave a torn pair -- that is the accepted cost, because the
    archive is the source of truth and the next run repairs it. What it may
    never leave is a missing day directory, a deleted neighbour file, or a
    ``.stage-<uuid>`` corpse in a git-tracked tree.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.date = "2026-08-17"
        self.generation = self.root / "generation"
        self.generation.mkdir()
        (self.generation / "report.md").write_text("fresh markdown\n", encoding="utf-8")
        (self.generation / "report.json").write_text(
            json.dumps({"run_id": "ddr-2026-08-17-newnewnew"}) + "\n", encoding="utf-8"
        )
        self.mirror = self.root / "mirror"
        self.target = self.mirror / self.date
        self.target.mkdir(parents=True)
        for name, text in FOREIGN.items():
            (self.target / name).write_text(text, encoding="utf-8")
        (self.target / "report.md").write_text("stale markdown\n", encoding="utf-8")
        (self.target / "report.json").write_text(
            json.dumps({"run_id": "ddr-2026-08-17-oldoldold"}) + "\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_sigkill_mid_mirror_loses_no_neighbour_and_strands_no_staging_dir(self) -> None:
        script = self.root / "child.py"
        script.write_text(CHILD.format(scripts=str(SCRIPTS)), encoding="utf-8")
        environment = dict(os.environ, DDR_MIRROR_DIR=str(self.mirror))
        child = subprocess.Popen(
            [sys.executable, str(script), str(self.generation), self.date],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        try:
            deadline = time.monotonic() + 20
            line = ""
            while time.monotonic() < deadline:
                line = child.stdout.readline()
                if "WINDOW-OPEN" in line or not line:
                    break
            self.assertIn("WINDOW-OPEN", line, "the child never reached the mirror window")
            child.send_signal(signal.SIGKILL)
            child.wait(timeout=20)
        finally:
            if child.poll() is None:  # pragma: no cover - defensive
                child.kill()
                child.wait(timeout=10)
        self.assertEqual(-signal.SIGKILL, child.returncode)

        self.assertTrue(self.target.is_dir(), "SIGKILL left no day directory at all")
        for name, text in FOREIGN.items():
            self.assertEqual(text, (self.target / name).read_text(encoding="utf-8"), name)
        strays = sorted(item.name for item in self.mirror.iterdir() if item.name.startswith("."))
        self.assertEqual([], strays, "a staging/retired directory was stranded in the mirror")
        # The half that landed before the kill is the new one; the pair is torn
        # and that is acceptable and repairable.
        self.assertEqual(
            "ddr-2026-08-17-newnewnew",
            json.loads((self.target / "report.json").read_text())["run_id"],
        )

    def test_the_next_run_repairs_the_torn_pair_and_sweeps_the_debris(self) -> None:
        debris = self.target / ".report.md.zz99yy88"
        debris.write_text("wreckage", encoding="utf-8")
        with mock.patch.dict(os.environ, {"DDR_MIRROR_DIR": str(self.mirror)}):
            outcome = runner.mirror_generation(
                self.date, {"ok": True, "generation": str(self.generation)}
            )
        self.assertTrue(outcome["ok"], outcome)
        self.assertEqual("fresh markdown\n", (self.target / "report.md").read_text())
        self.assertEqual(
            "ddr-2026-08-17-newnewnew",
            json.loads((self.target / "report.json").read_text())["run_id"],
        )
        self.assertFalse(debris.exists())
        for name, text in FOREIGN.items():
            self.assertEqual(text, (self.target / name).read_text(encoding="utf-8"), name)


class MigrationIntentTests(unittest.TestCase):
    """A migration may not inherit a dead config's state by default."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.v1 = copy.deepcopy(LIVE_V1)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_disabled_topics_without_a_stated_intent_are_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            reportctl_config.migrate_v1_to_v2(self.v1, project_roots=ROOTS)
        message = str(caught.exception)
        for topic in ("nightly-pr-maintenance", "hermes-fleet-health", "report-delivery-health"):
            self.assertIn(topic, message)
        self.assertIn("--disabled-topics enable", message)
        self.assertIn("--disabled-topics preserve", message)
        self.assertIn("2026-07-25", message)

    def test_a_v1_config_with_nothing_disabled_needs_no_ceremony(self) -> None:
        for topic in self.v1["topics"]:
            topic["enabled"] = True
        migrated, notes = reportctl_config.migrate_v1_to_v2(self.v1, project_roots=ROOTS)
        self.assertTrue(all(section["enabled"] for section in migrated["sections"]))
        self.assertEqual([], [note for note in notes if note.startswith("WARNING")])

    def test_enable_is_a_stated_intent(self) -> None:
        migrated, _ = reportctl_config.migrate_v1_to_v2(
            self.v1, project_roots=ROOTS, disabled_topics="enable"
        )
        self.assertTrue(all(section["enabled"] for section in migrated["sections"]))

    def test_preserve_is_a_stated_intent_and_is_shouted(self) -> None:
        migrated, notes = reportctl_config.migrate_v1_to_v2(
            self.v1, project_roots=ROOTS, disabled_topics="preserve"
        )
        disabled = sorted(s["id"] for s in migrated["sections"] if not s["enabled"])
        self.assertEqual(["fleet-health", "pr-maintenance", "report-delivery"], disabled)
        self.assertEqual(3, len([note for note in notes if note.startswith("WARNING")]))

    def test_an_unknown_intent_is_rejected(self) -> None:
        with self.assertRaisesRegex(ConfigError, "disabled_topics"):
            reportctl_config.migrate_v1_to_v2(
                self.v1, project_roots=ROOTS, disabled_topics="whatever"
            )

    def test_the_result_states_what_the_report_will_not_cover(self) -> None:
        source = self.root / "v1.json"
        source.write_text(json.dumps(self.v1), encoding="utf-8")
        result = reportctl_config.migrate_config_file(
            source,
            self.root / "report.json",
            project_roots=ROOTS,
            disabled_topics="preserve",
        )
        self.assertEqual(
            ["fleet-health", "pr-maintenance", "report-delivery"],
            sorted(result["disabled_sections"]),
        )
        self.assertEqual(["dev-activity"], result["enabled_sections"])
        self.assertEqual(3, len(result["warnings"]))
        self.assertIn("will not be collected", result["coverage_warning"])

    def test_a_fully_enabled_migration_reports_no_coverage_warning(self) -> None:
        source = self.root / "v1.json"
        source.write_text(json.dumps(self.v1), encoding="utf-8")
        result = reportctl_config.migrate_config_file(
            source, self.root / "report.json", project_roots=ROOTS, disabled_topics="enable"
        )
        self.assertEqual([], result["disabled_sections"])
        self.assertEqual([], result["warnings"])
        self.assertIsNone(result["coverage_warning"])


class MigrationCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "v1.json"
        self.source.write_text(json.dumps(LIVE_V1), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_module(self, *argv: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(MODULE_PATH), *argv], capture_output=True, text=True
        )

    def test_the_cli_refuses_a_silent_inert_migration(self) -> None:
        destination = self.root / "report.json"
        completed = self.run_module(
            "migrate", "--config", str(self.source), "--out", str(destination),
            "--project-root", ROOTS[0],
        )
        self.assertEqual(2, completed.returncode, completed.stdout)
        self.assertIn("--disabled-topics", json.loads(completed.stderr)["error"])
        self.assertFalse(destination.exists(), "an unintended config was written anyway")

    def test_preserving_prints_the_warnings_where_an_operator_sees_them(self) -> None:
        destination = self.root / "report.json"
        completed = self.run_module(
            "migrate", "--config", str(self.source), "--out", str(destination),
            "--project-root", ROOTS[0], "--disabled-topics", "preserve",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(
            ["fleet-health", "pr-maintenance", "report-delivery"],
            sorted(payload["disabled_sections"]),
        )
        self.assertIn("WARNING", completed.stderr)
        self.assertIn("will not be collected", completed.stderr)

    def test_validate_surfaces_a_disabled_section_instead_of_a_bare_green(self) -> None:
        value = v2_config(self.root)
        value["sections"][1]["enabled"] = False
        value["sections"][1]["required"] = False
        path = self.root / "v2.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        completed = self.run_module("validate", "--config", str(path))
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(["fleet-health"], payload["disabled_sections"])
        self.assertEqual(["dev-activity"], payload["enabled_sections"])
        self.assertIn("fleet-health", completed.stderr)
        self.assertIn("WARNING", completed.stderr)


if __name__ == "__main__":
    unittest.main()
