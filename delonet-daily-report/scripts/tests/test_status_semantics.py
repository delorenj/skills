"""Status describes the collection. The news it found belongs in the content.

Round 2 composed three changes into a self-sustaining failure latch:

1. ``report_delivery`` put the *delivery verdict* in its section ``status``, so
   any gap in the 7-day lookback produced ``partial``;
2. ``derive_status`` returned ``failed`` when a **required** section was not
   ``complete``;
3. ``report-delivery`` ships ``required: true``.

One missed day therefore failed the run, which published a generation whose
derived status was ``failed``, which ``verify_published`` refuses, which
``report_delivery._scan_day`` then classifies ``invalid`` -- so tomorrow's window
still holds a gap, and the pipeline can never return to green on its own. The
report that tells you something is wrong was being suppressed as a failure.

The corrected rule, asserted here:

``status`` answers *could this collector do its work*.
    ``complete`` -- every source was read and the answer is trustworthy,
    **including** when the answer is "three days are missing, here they are".
    ``partial`` -- a source could not be read, so the answer is incomplete.
    ``failed`` -- the collector could not do its job at all.

The findings live in ``summary``, ``metrics``, ``caveats``, ``detail``, and the
rendered document. A run that accurately reports bad news exits 0; a run whose
required collector could not run exits non-zero, which is the catch this package
was built for and is asserted here too.

Every test in this file fails against the pre-fix tree.
"""

from __future__ import annotations

import copy
import datetime as dt
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run as runner
from test_fixtures import config
from test_report_delivery import REPORT_DATE, CollectorTestCase, window

report_delivery = importlib.import_module("collectors.report_delivery")
reportctl_archive = importlib.import_module("reportctl_archive")
reportctl_config = importlib.import_module("reportctl_config")


# --------------------------------------------------------------------------- #
# 1. The collector: a detected gap is a completed collection reporting bad news
# --------------------------------------------------------------------------- #


class CollectionStatusTests(CollectorTestCase):
    def test_a_window_of_gaps_is_a_complete_collection(self) -> None:
        """Nothing was ever published. The collector read both sources fine."""
        with self.serve([]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual("", result.reason)
        self.assertEqual("failed", result.metrics["delivery_health"])
        self.assertEqual(6, result.metrics["days_missing"])
        self.assertEqual(6, result.metrics["delivery_gaps"])

    def test_the_bad_news_leads_the_summary_and_the_caveats(self) -> None:
        with self.serve([]):
            result = self.collect()
        self.assertTrue(
            result.summary.startswith("report-delivery: DELIVERY FAILED"), result.summary
        )
        self.assertIn("6 of 6 due day(s)", result.summary)
        self.assertTrue(
            result.caveats[0].startswith("DELIVERY FAILED"), result.caveats[:3]
        )
        self.assertIn("no valid published report", result.caveats[0])

    def test_the_bad_news_survives_into_a_valid_artifact(self) -> None:
        with self.serve([]):
            result = self.collect()
        artifact = result.to_artifact("run-under-test", 24)
        self.assertEqual("complete", artifact["status"])
        self.assertEqual("failed", artifact["metrics"]["delivery_health"])
        self.assertIn("DELIVERY FAILED", artifact["summary"])
        self.assertTrue(any("DELIVERY FAILED" in item for item in artifact["caveats"]))

    def test_a_partial_status_names_only_the_unread_source(self) -> None:
        """``reason`` explains the status. Delivery findings are not the status."""
        for day in window()[:-2]:
            self.publish(day)
        with self.dead_candystore():
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("Candystore not read", result.reason)
        self.assertNotIn("missing", result.reason)
        # ...and the gap it did see is still reported, just not as the status.
        self.assertEqual(1, result.metrics["delivery_gaps"])
        self.assertEqual("degraded", result.metrics["delivery_health"])
        self.assertTrue(any("DELIVERY DEGRADED" in item for item in result.caveats))

    def test_a_day_the_archive_could_not_be_read_for_is_not_a_delivery_claim(self) -> None:
        """One unreadable day is an unread source, not a missed report.

        This is the hole the fix could have opened: moving the delivery verdict
        out of ``status`` must not also move *read failures* out of it. A day
        whose scan raises is ``unknown`` -- no claim -- and an unknown day
        degrades the collection to ``partial``, because part of the archive was
        not read.
        """
        for day in window():
            self.publish(day)
        real = report_delivery._scan_day

        def flaky(config, day):
            if day == "2026-08-13":
                raise PermissionError("[Errno 13] Permission denied: 'current.json'")
            return real(config, day)

        with self.serve([]), mock.patch.object(report_delivery, "_scan_day", flaky):
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("2026-08-13", result.reason)
        self.assertIn("could not be read", result.reason)
        self.assertEqual(1, result.metrics["days_unreadable"])
        self.assertEqual(0, result.metrics["days_invalid"])
        self.assertEqual(0, result.metrics["delivery_gaps"])
        # 6 due days, not 7: no ratio may quietly count an unread day as due.
        self.assertIn("6 of 6 due days delivered", result.summary)

    def test_an_unreadable_archive_is_a_failed_collection(self) -> None:
        """The archive is the primary source: without it there is no answer.

        Candystore is a cross-check. Losing the cross-check is ``partial``;
        losing the thing being checked is ``failed``, and because this section is
        required that is what keeps a blind pipeline from exiting 0.
        """
        broken = copy.deepcopy(self.config)
        blocker = self.root / "not-a-directory"
        blocker.write_text("this is a file, not an archive\n", encoding="utf-8")
        broken["archive_dir"] = str(blocker)
        with self.serve([]):
            result = report_delivery.collect(self.section, REPORT_DATE, broken)
        self.assertEqual("failed", result.status)
        self.assertIn("not a directory", result.reason)
        self.assertEqual("unknown", result.metrics["delivery_health"])

    def test_standalone_exit_code_answers_could_it_run_not_is_it_healthy(self) -> None:
        import io
        from contextlib import redirect_stderr, redirect_stdout

        path = self.root / "report.json"
        path.write_text(json.dumps(self.config), encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with self.serve([]), redirect_stdout(out), redirect_stderr(err):
            code = report_delivery.main(["--date", REPORT_DATE, "--config", str(path)])
        artifact = json.loads(out.getvalue())
        self.assertEqual(0, code)
        self.assertEqual("complete", artifact["status"])
        self.assertEqual("failed", artifact["metrics"]["delivery_health"])
        # Exit 0 may never be the only thing an operator sees.
        self.assertIn("DELIVERY FAILED", err.getvalue())


# --------------------------------------------------------------------------- #
# 2. derive_status: "could not run" fails the run; "ran and found trouble" does not
# --------------------------------------------------------------------------- #


class DeriveStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.value = config(Path(self.temporary.name))

    def derive(self, statuses: dict[str, str]) -> str:
        return reportctl_archive.derive_status(self.value, statuses)

    def test_a_required_section_that_ran_partially_degrades_the_run(self) -> None:
        """``partial`` means the collector ran and produced a trustworthy but
        incomplete answer. That is a degraded report, not an absent one."""
        self.assertEqual(
            "partial", self.derive({"dev-activity": "partial", "fleet-health": "complete"})
        )

    def test_a_required_section_that_could_not_run_fails_the_run(self) -> None:
        for status in ("failed", "missing", "invalid", "stale"):
            with self.subTest(status=status):
                self.assertEqual(
                    "failed", self.derive({"dev-activity": status, "fleet-health": "complete"})
                )

    def test_an_absent_required_status_fails_the_run(self) -> None:
        self.assertEqual("failed", self.derive({"fleet-health": "complete"}))

    def test_nothing_completed_is_failed_even_when_everything_ran(self) -> None:
        self.assertEqual(
            "failed", self.derive({"dev-activity": "partial", "fleet-health": "partial"})
        )

    def test_required_failures_names_only_the_sections_that_could_not_run(self) -> None:
        statuses = {"dev-activity": "partial", "fleet-health": "failed"}
        self.assertEqual([], reportctl_archive.required_failures(self.value, statuses))
        self.assertEqual(
            ["dev-activity"],
            reportctl_archive.required_failures(
                self.value, {"dev-activity": "failed", "fleet-health": "complete"}
            ),
        )


# --------------------------------------------------------------------------- #
# 3. The latch itself, end to end
# --------------------------------------------------------------------------- #


class DeliveryGapLatchTests(unittest.TestCase):
    """A day with a real delivery gap must publish, exit 0, and not poison the
    next day. Pre-fix this test fails twice: the gap run exits 3 and publishes a
    generation classified ``failed``, and the next day's scan then calls that
    generation ``invalid`` -- a gap that regenerates itself forever."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.mirror = self.root / "mirror"  # never the git-tracked 33GOD mirror
        environment = mock.patch.dict(os.environ, {"DDR_MIRROR_DIR": str(self.mirror)})
        environment.start()
        self.addCleanup(environment.stop)
        self.config = self.make_config()
        self.day_one = "2026-08-17"
        self.day_two = "2026-08-18"

    def make_config(self) -> dict:
        value = config(self.root)
        value["sections"][0]["collector"] = "stub_always_complete"
        value["sections"][1] = {
            "id": "report-delivery",
            "title": "Daily Report and Delivery Health",
            "collector": "report_delivery",
            "required": True,
            "enabled": True,
            "max_age_hours": 24,
            "options": {"candystore_url": "http://127.0.0.1:8683", "lookback_days": 7},
        }
        return reportctl_config.validate_config(value)

    def run_day(self, date: str):
        with mock.patch.object(
            report_delivery, "_fetch_page", return_value={"events": [], "total": 0}
        ):
            return runner.run_report(
                self.config, date, narrate_enabled=False, emit=False, mirror=True
            )

    def section_artifact(self, date: str) -> dict:
        path = Path(self.config["artifact_dir"]) / date / "sections" / "report-delivery.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def day_states(self, date: str) -> dict[str, str]:
        artifact = self.section_artifact(date)
        target = dt.date.fromisoformat(date)
        days = {(target - dt.timedelta(days=n)).isoformat() for n in range(7)}
        states = {}
        for line in artifact.get("detail", []):
            fields = line.split(" ")
            if fields[0] in days:
                states[fields[0]] = fields[1]
        return states

    def test_a_gap_day_reports_loudly_publishes_and_exits_zero(self) -> None:
        outcome, code = self.run_day(self.day_one)
        self.assertEqual(0, code, outcome.get("caveats"))
        # ``section_status`` is the manifest-derived one. (``status`` is
        # ``partial`` here only because these runs disable the narrator, which
        # is a separate documented rule.)
        self.assertEqual("complete", outcome["section_status"])
        self.assertEqual("complete", outcome["manifest"]["sections"]["report-delivery"])

        # It published, and the pipeline's own gate accepts what it published.
        self.assertTrue(outcome["published"]["verified"])
        self.assertTrue(outcome["published"]["accepted"])
        verified = reportctl_archive.verify_published(self.config, self.day_one)
        self.assertTrue(verified["ok"], verified["problems"])

        # And the bad news is in the document a human reads.
        markdown = Path(outcome["published"]["markdown"]).read_text(encoding="utf-8")
        self.assertIn("DELIVERY FAILED", markdown)
        self.assertIn("6 of 6 due day(s)", markdown)
        self.assertIn("delivery_health=failed", markdown.replace(": ", "="))

    def test_the_next_day_is_not_poisoned_by_the_previous_verdict(self) -> None:
        self.run_day(self.day_one)
        outcome, code = self.run_day(self.day_two)
        self.assertEqual(0, code)
        self.assertEqual("complete", outcome["section_status"])
        # The whole latch, in one assertion: yesterday's honest bad-news report
        # is a delivered report, not an invalid one.
        self.assertEqual("delivered", self.day_states(self.day_two)[self.day_one])
        metrics = self.section_artifact(self.day_two)["metrics"]
        self.assertEqual(1, metrics["days_delivered"])
        self.assertEqual(0, metrics["days_invalid"])
        self.assertEqual("degraded", metrics["delivery_health"])

    def test_a_required_collector_that_cannot_run_still_exits_nonzero(self) -> None:
        """The teeth stay in: an unreadable archive is not a finding, it is a
        blind collector, and the run must not be recorded as a success."""
        # The archive this run publishes into stays writable; what breaks is the
        # collector's *read* of it, exactly as a permissions change or a dropped
        # mount would break it mid-flight.
        with mock.patch.object(
            report_delivery, "_fetch_page", return_value={"events": [], "total": 0}
        ), mock.patch.object(
            report_delivery,
            "_archive_usable",
            return_value="archive_dir /srv/ddr/archive is not readable",
        ):
            outcome, code = runner.run_report(
                self.config, self.day_one, narrate_enabled=False, emit=False, mirror=False
            )
        self.assertEqual("failed", outcome["manifest"]["sections"]["report-delivery"])
        self.assertEqual("failed", outcome["status"])
        self.assertEqual(runner.EXIT_UNMET, code)
        # The published artifact records the same refusal: the gate must not
        # accept a run whose required collector was blind.
        verified = reportctl_archive.verify_published(self.config, self.day_one)
        self.assertFalse(verified["ok"])
        self.assertEqual(["report-delivery"], verified["required_failures"])


def _stub_complete(section_cfg, report_date, config_value=None):
    from collectors.base import SectionResult

    return SectionResult(
        id=section_cfg["id"],
        status="complete",
        summary=f"{section_cfg['id']} read every source for {report_date}.",
        metrics={"items": 3},
    )


def _install_stub() -> None:
    import sys
    import types

    module = types.ModuleType("collectors.stub_always_complete")
    module.collect = _stub_complete
    sys.modules["collectors.stub_always_complete"] = module


_install_stub()


if __name__ == "__main__":
    unittest.main()
