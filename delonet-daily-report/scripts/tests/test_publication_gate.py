"""Round 4, defect (C): a failed re-run is not a one-way door out of a good day.

``publish_archive_pair`` swapped ``current.json`` as the last step of *staging*,
so the pointer moved before anything had verified the generation it now named.
Measured on 2026-08-17: the day was published at generation ``b9102fee`` and
``verify`` exited 0; one re-run with the required source dead published
``49f3caea``, ``verify`` exited 3 -- and the pointer was already on it. The good
generation was still on disk, referenced by nothing. The next day's
``report-delivery`` then read 2026-08-17 as invalid and manufactured a delivery
gap that had not happened.

The fix is an ordering, expressed as a rule:

    A run may replace the day's published report with its own.
    It may never downgrade the day from a report that verifies to one that
    does not.

So the generation is materialised first, verified while nothing points at it, and
only then does the pointer move -- and when this run's generation is refused, the
pointer moves only if the incumbent is refused too. A first-ever failed run still
publishes itself, because there is nothing better to protect; a failed re-run over
a verified day does not, because there is.

None of that is allowed to soften the run's own account of itself, which is the
other half of these tests: the refused generation stays on disk for debugging, the
run still exits non-zero, its status is still ``failed``, and it says in its
caveats what it did and what survived.

Fail-first: run against the pre-fix ``publish``/``archive_report`` (pointer swap
inside ``publish_archive_pair``, verification afterwards) and every test in
``NoDowngradeTests`` fails.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from test_run_pipeline import (
    PipelineCase,
    complete_collector,
    failing_collector,
    register_stub,
)

import reportctl_archive  # noqa: E402
import run as runner  # noqa: E402


class GateCase(PipelineCase):
    def healthy(self, tag: str) -> dict:
        return self.with_collectors(
            register_stub(f"gate_ok_{tag}_a", complete_collector),
            register_stub(f"gate_ok_{tag}_b", complete_collector),
        )

    def required_source_dead(self, tag: str) -> dict:
        """dev-activity is required; its collector cannot reach its source."""
        return self.with_collectors(
            register_stub(f"gate_dead_{tag}", failing_collector),
            register_stub(f"gate_live_{tag}", complete_collector),
        )

    def marker_path(self, value: dict) -> Path:
        return Path(runner.archive_paths(value, self.date)["commit_marker"])

    def pointer(self, value: dict) -> str | None:
        path = self.marker_path(value)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))["generation"]

    def generations(self, value: dict) -> set[str]:
        root = Path(runner.archive_paths(value, self.date)["archive_root"]) / "generations"
        return {item.name for item in root.iterdir()} if root.exists() else set()


class NoDowngradeTests(GateCase):
    """The measured incident, and the rule that now refuses it."""

    def test_a_failed_rerun_does_not_take_the_published_day_with_it(self) -> None:
        good = self.healthy("keep")
        first, first_code = self.run_pipeline(good)
        self.assertEqual(0, first_code)
        published = self.pointer(good)
        self.assertEqual(first["published"]["generation"], published)
        self.assertTrue(reportctl_archive.verify_published(good, self.date)["ok"])

        dead = self.required_source_dead("keep")
        second, second_code = self.run_pipeline(dead)

        # The re-run failed, loudly and on its own behalf.
        self.assertEqual("failed", second["status"])
        self.assertEqual(runner.EXIT_UNMET, second_code)
        self.assertFalse(second["published"]["accepted"])
        self.assertFalse(second["published"]["current"])

        # And the day it could not improve is exactly as it was.
        self.assertEqual(published, self.pointer(good))
        still = reportctl_archive.verify_published(good, self.date)
        self.assertTrue(still["ok"], still["problems"])
        self.assertEqual("complete", still["status"])

    def test_the_refused_generation_is_retained_not_deleted(self) -> None:
        good = self.healthy("retain")
        first, _ = self.run_pipeline(good)
        dead = self.required_source_dead("retain")
        second, _ = self.run_pipeline(dead)
        names = self.generations(good)
        self.assertIn(first["published"]["generation"], names)
        self.assertIn(second["published"]["generation"], names, "evidence was destroyed")
        refused = Path(second["published"]["markdown"])
        self.assertTrue(refused.is_file())
        report = json.loads(Path(second["published"]["report_json"]).read_text())
        self.assertEqual(second["run_id"], report["run_id"])

    def test_the_run_says_which_report_survived_and_why_its_own_did_not(self) -> None:
        good = self.healthy("caveat")
        first, _ = self.run_pipeline(good)
        dead = self.required_source_dead("caveat")
        second, _ = self.run_pipeline(dead)
        joined = " ".join(second["caveats"])
        self.assertIn("current.json was not moved", joined)
        self.assertIn(second["published"]["generation"], joined)
        self.assertIn(first["published"]["generation"], joined)
        self.assertEqual(first["published"]["generation"],
                         second["published"]["previous_generation"])

    def test_the_next_days_delivery_scan_still_sees_a_delivered_day(self) -> None:
        # The consequence that made this a compounding defect rather than a
        # cosmetic one: an orphaned good generation reads as an undelivered day.
        good = self.healthy("scan")
        self.run_pipeline(good)
        dead = self.required_source_dead("scan")
        self.run_pipeline(dead)
        verified = reportctl_archive.verify_published(good, self.date)
        self.assertTrue(verified["ok"], verified["problems"])
        self.assertEqual([], verified["required_failures"])

    def test_nothing_was_mirrored_from_the_refused_generation(self) -> None:
        good = self.healthy("mirror")
        self.run_pipeline(good, mirror=True)
        before = (self.mirror / self.date / "report.json").read_text()
        dead = self.required_source_dead("mirror")
        second, _ = self.run_pipeline(dead, mirror=True)
        self.assertFalse(second["mirror"]["ok"])
        self.assertEqual(before, (self.mirror / self.date / "report.json").read_text())


class GateOrderingTests(GateCase):
    """The proof is applied while the pointer still names the old generation."""

    def test_the_gate_runs_before_current_json_is_written(self) -> None:
        good = self.healthy("order")
        first, _ = self.run_pipeline(good)
        published = first["published"]["generation"]
        seen: list[str | None] = []
        real = reportctl_archive.verify_generation

        def watching(config, date, generation):
            # What does current.json say at the moment the gate is consulted?
            seen.append(self.pointer(good))
            return real(config, date, generation)

        with mock.patch.object(runner, "verify_generation", watching):
            second, _ = self.run_pipeline(self.healthy("order2"))
        self.assertTrue(seen, "the gate was never consulted")
        # Every consultation happened while the PREVIOUS generation was current.
        self.assertEqual([published] * len(seen), seen)
        # ...and only afterwards did the pointer move to this run's generation.
        self.assertEqual(second["published"]["generation"], self.pointer(good))

    def test_a_generation_that_verifies_always_becomes_current(self) -> None:
        good = self.healthy("swap")
        first, _ = self.run_pipeline(good)
        second, code = self.run_pipeline(self.healthy("swap2"))
        self.assertEqual(0, code)
        self.assertTrue(second["published"]["current"])
        self.assertEqual(second["published"]["generation"], self.pointer(good))
        self.assertNotEqual(first["published"]["generation"], self.pointer(good))


class NothingToProtectTests(GateCase):
    """With no verified incumbent, a failed run publishes itself. Honestly."""

    def test_a_first_run_that_fails_still_publishes_its_own_record(self) -> None:
        dead = self.required_source_dead("first")
        outcome, code = self.run_pipeline(dead)
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)
        self.assertTrue(outcome["published"]["current"])
        self.assertEqual(outcome["published"]["generation"], self.pointer(dead))
        # Published, and refused by the gate that reads it back. Both are true
        # and both are visible; that is the point of publishing it.
        verified = reportctl_archive.verify_published(dead, self.date)
        self.assertFalse(verified["ok"])
        self.assertEqual("failed", verified["status"])
        self.assertEqual(["dev-activity"], verified["required_failures"])

    def test_a_failed_run_replaces_an_earlier_failed_run(self) -> None:
        first, _ = self.run_pipeline(self.required_source_dead("f1"))
        second, _ = self.run_pipeline(self.required_source_dead("f2"))
        self.assertEqual(second["published"]["generation"], self.pointer(self.value))
        self.assertNotEqual(first["published"]["generation"], self.pointer(self.value))

    def test_a_corrupt_incumbent_does_not_protect_itself(self) -> None:
        good = self.healthy("corrupt")
        first, _ = self.run_pipeline(good)
        Path(first["published"]["report_json"]).write_text("{not json", encoding="utf-8")
        second, _ = self.run_pipeline(self.required_source_dead("corrupt2"))
        # The incumbent no longer verifies, so it is not a report this run is
        # making worse. The new one, failed but readable, becomes the record.
        self.assertTrue(second["published"]["current"])
        self.assertEqual(second["published"]["generation"], self.pointer(good))


class ArchiveCommandIsUnchangedTests(unittest.TestCase):
    """``reportctl archive`` is the low-level command and keeps its contract."""

    def test_archive_report_without_a_gate_always_swaps_the_pointer(self) -> None:
        # ``verify`` is what refuses a bad generation for this command; the gate
        # belongs to the run path alone. Changing that would silently alter what
        # a hand-run `reportctl archive` does.
        import inspect

        signature = inspect.signature(reportctl_archive.archive_report)
        self.assertIs(signature.parameters["gate"].default, None)
        self.assertEqual(
            inspect.Parameter.KEYWORD_ONLY, signature.parameters["gate"].kind
        )


if __name__ == "__main__":
    unittest.main()
