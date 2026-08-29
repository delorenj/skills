"""Tests for the report-delivery self-check collector.

The property under test is not "does it produce a section" -- it is "can it be
made to claim a delivery that did not happen". Every test below either proves a
real gap becomes visible, or proves an unreadable source becomes ``partial`` /
``failed`` instead of an exception or a fabricated ``complete``.

``DeliveryVerdictTests`` is the regression suite for the defect that made this
section useless: it detected every gap and every archive/event disagreement
perfectly and then dropped the detection, so six undelivered days reached every
consumer as an unremarkable ``complete``. A detection nothing acts on is not a
detection -- so the verdict is now carried loudly in ``summary``, ``caveats``,
``metrics.delivery_health`` and ``detail``.

It is *not* carried in ``status``. Status answers "could this collector do its
work"; the round-2 attempt to answer "was the news good" there latched the whole
pipeline into a permanent failure, and ``test_status_semantics.py`` holds that
latch open.
"""

from __future__ import annotations

import copy
import datetime as dt
import importlib
import io
import json
import os
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from test_fixtures import config, manifest, report

report_delivery = importlib.import_module("collectors.report_delivery")
reportctl_archive = importlib.import_module("reportctl_archive")
reportctl_config = importlib.import_module("reportctl_config")
reportctl_runtime = importlib.import_module("reportctl_runtime")
validate_section_artifact = importlib.import_module(
    "reportctl_contracts"
).validate_section_artifact

REPORT_DATE = "2026-08-17"
EVENT_TYPE = report_delivery.DEFAULT_EVENT_TYPE
SECTION_STATUSES = {
    "dev-activity": "complete",
    "fleet-health": "complete",
    "report-delivery": "complete",
}


def window(report_date: str = REPORT_DATE, lookback: int = 7) -> list[str]:
    target = dt.date.fromisoformat(report_date)
    return [(target - dt.timedelta(days=n)).isoformat() for n in range(lookback - 1, -1, -1)]


def event(report_date: str, status: str = "complete", run_id: str = "dev-journal") -> dict:
    """A realistic completion envelope, noise included.

    The actor, producer, artifact paths, and delivery block exist here on purpose:
    the allowlist has to drop them, and a test proves it does.
    """
    return {
        "id": f"evt-{report_date}-{run_id}",
        "type": EVENT_TYPE,
        "time": f"{report_date}T16:04:47Z",
        "producer": "33god-pm",
        "service": "33god-pm",
        "cli": "hermes",
        "actor": {
            "type": "agent_cli",
            "agent_id": "bloodbank.agent.33god-pm",
            "provider": "nous_research",
        },
        "data": {
            "schema_version": 1,
            "run_id": run_id,
            "report_date": report_date,
            "outcome": {"status": status, "sections": {"overview": "complete"}},
            "artifacts": {"report_artifact_id": "/home/delorenj/private/journal.txt"},
            "delivery": {"status": "delivered", "destination_alias": "daily-journals"},
        },
    }


def page(events: list[dict]) -> dict:
    return {"events": events, "total": len(events), "limit": report_delivery.PAGE_SIZE, "offset": 0}


class CollectorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = self.make_config()
        environment = mock.patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("CANDYSTORE_URL", None)
        os.environ.pop("DELONET_REPORT_CONFIG", None)
        self.requested_urls: list[str] = []

    def make_config(self) -> dict:
        value = config(self.root)
        value["sections"].append(
            {
                "id": "report-delivery",
                "title": "Daily Report and Delivery Health",
                "collector": "report_delivery",
                "required": True,
                "enabled": True,
                "max_age_hours": 24,
                "options": {"candystore_url": "http://127.0.0.1:8683", "lookback_days": 7},
            }
        )
        return reportctl_config.validate_config(value)

    @property
    def section(self) -> dict:
        return copy.deepcopy(self.config["sections"][-1])

    def section_with(self, **options) -> dict:
        section = self.section
        section["options"].update(options)
        return section

    # -- fake sources ------------------------------------------------------- #

    def serve(self, events: list[dict]):
        def fetch(url: str, timeout: int):
            self.requested_urls.append(url)
            return page(events)

        return mock.patch.object(report_delivery, "_fetch_page", side_effect=fetch)

    def dead_candystore(self):
        def fetch(url: str, timeout: int):
            self.requested_urls.append(url)
            raise urllib.error.URLError("Connection refused")

        return mock.patch.object(report_delivery, "_fetch_page", side_effect=fetch)

    # -- archive helpers ---------------------------------------------------- #

    def publish(self, day: str, statuses: dict | None = None) -> None:
        """Publish a real generation through the real archive transaction."""
        value = report(self.config)
        value["report_date"] = day
        value["run_id"] = f"run-{day}"
        entries = manifest(statuses or SECTION_STATUSES)
        entries["report_date"] = day
        entries["run_id"] = f"run-{day}"
        entries["started_at"] = f"{day}T10:00:00Z"
        entries["completed_at"] = f"{day}T10:01:00Z"
        staging = self.root / "staging" / day
        staging.mkdir(parents=True, exist_ok=True)
        (staging / "report.json").write_text(json.dumps(value), encoding="utf-8")
        (staging / "run-manifest.json").write_text(json.dumps(entries), encoding="utf-8")
        (staging / "report.md").write_text(f"# Daily report {day}\n", encoding="utf-8")
        reportctl_archive.archive_report(
            self.config,
            str(staging / "report.json"),
            str(staging / "report.md"),
            str(staging / "run-manifest.json"),
        )

    def archive_root(self, day: str) -> Path:
        return Path(reportctl_runtime.archive_paths(self.config, day)["archive_root"])

    def stage_without_pointer(self, day: str) -> None:
        """A generation that landed but whose current.json swap never happened."""
        generation = self.archive_root(day) / "generations" / "abcdef123456"
        generation.mkdir(parents=True)
        (generation / "report.md").write_text("# interrupted\n", encoding="utf-8")
        (generation / "report.json").write_text("{}", encoding="utf-8")
        (generation / "run-manifest.json").write_text("{}", encoding="utf-8")

    def corrupt_published_report(self, day: str) -> None:
        marker = json.loads((self.archive_root(day) / "current.json").read_text(encoding="utf-8"))
        generation = self.archive_root(day) / "generations" / marker["generation"]
        (generation / "report.json").write_text('{"schema_version": 1}', encoding="utf-8")

    # -- invocation --------------------------------------------------------- #

    def collect(self, section: dict | None = None, report_date: str = REPORT_DATE):
        return report_delivery.collect(section or self.section, report_date, self.config)

    def days(self, result) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for line in result.detail:
            fields = line.split(" ")
            if len(fields) >= 2 and fields[0] in set(window()):
                parsed[fields[0]] = fields[1]
        return parsed


class HappyPathTests(CollectorTestCase):
    def test_every_day_delivered_and_evented_is_complete(self) -> None:
        days = window()
        for day in days:
            self.publish(day)
        with self.serve([event(day) for day in days]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual(7, result.metrics["days_checked"])
        self.assertEqual(7, result.metrics["days_delivered"])
        self.assertEqual(0, result.metrics["days_missing"])
        self.assertEqual(0, result.metrics["days_invalid"])
        self.assertEqual(7, result.metrics["events_found"])
        self.assertEqual(0, result.metrics["archive_event_disagreements"])
        self.assertEqual(7, result.metrics["consecutive_delivered_streak"])
        self.assertTrue(result.metrics["archive_readable"])
        self.assertTrue(result.metrics["candystore_reachable"])
        self.assertEqual({day: "delivered" for day in days}, self.days(result))

    def test_artifact_validates_against_the_contract(self) -> None:
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        artifact = result.to_artifact("run-under-test", 24)
        self.assertEqual(artifact, validate_section_artifact(artifact, "report-delivery"))
        self.assertEqual("complete", artifact["status"])

    def test_candystore_is_queried_for_the_window_and_type(self) -> None:
        with self.serve([]):
            self.collect()
        self.assertTrue(self.requested_urls)
        url = self.requested_urls[0]
        # Both eras of the name ride one comma-separated `type` filter. The
        # ~713k rows written before the version token was retired keep the
        # five-token spelling forever, so a query for either shape alone turns
        # the other era's days into fabricated delivery gaps.
        self.assertIn(
            "type=bloodbank.reporting.report.completed"
            "%2Cbloodbank.v1.reporting.report.completed",
            url,
        )
        self.assertIn("from=2026-08-10T00%3A00%3A00Z", url)
        self.assertIn("to=2026-08-19T00%3A00%3A00Z", url)

    def test_a_config_naming_the_retired_shape_still_reads_the_new_rows(self) -> None:
        """An operator's `event_type` override must not re-narrow the query.

        Config written before the migration names `bloodbank.v1.*`. Honouring
        it literally would hide every event published since.
        """
        self.assertEqual(
            "bloodbank.reporting.report.completed"
            ",bloodbank.v1.reporting.report.completed",
            report_delivery.query_types("bloodbank.v1.reporting.report.completed"),
        )
        self.assertEqual(
            report_delivery.query_types("bloodbank.reporting.report.completed"),
            report_delivery.query_types("bloodbank.v1.reporting.report.completed"),
        )

    def test_history_written_under_the_retired_shape_still_agrees_with_the_archive(
        self,
    ) -> None:
        """Pre-migration completion events must not read as delivery gaps.

        Every archived day here also published a completion event -- just under
        the retired five-token name, the way all 713k rows older than the
        migration did. Matching only the current shape would report seven
        ``archived-but-never-published`` disagreements that never happened.
        """
        legacy = [event(day) for day in window()]
        for envelope in legacy:
            envelope["type"] = "bloodbank.v1.reporting.report.completed"
        for day in window():
            self.publish(day)
        with self.serve(legacy):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual("ok", result.metrics["delivery_health"])
        self.assertEqual(0, result.metrics["days_archive_without_event"])

    def test_lookback_days_option_is_honoured(self) -> None:
        with self.serve([]):
            result = self.collect(self.section_with(lookback_days=3))
        self.assertEqual(3, result.metrics["days_checked"])
        self.assertEqual(3, result.metrics["lookback_days"])
        self.assertEqual(set(window(lookback=3)), set(self.days(result)))

    def test_nonsense_lookback_falls_back_and_says_so(self) -> None:
        with self.serve([]):
            result = self.collect(self.section_with(lookback_days=0))
        self.assertEqual(7, result.metrics["days_checked"])
        self.assertTrue(any("lookback_days" in item for item in result.caveats))


class UnreachableSourceTests(CollectorTestCase):
    def test_candystore_down_is_partial_never_complete(self) -> None:
        for day in window():
            self.publish(day)
        with self.dead_candystore():
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("Candystore", result.reason)
        self.assertIn("Connection refused", result.reason)
        self.assertEqual(7, result.metrics["days_delivered"])
        self.assertEqual("unknown", result.metrics["events_found"])
        self.assertEqual("unknown", result.metrics["archive_event_disagreements"])
        self.assertFalse(result.metrics["candystore_reachable"])

    def test_both_sources_unreadable_is_failed_not_an_exception(self) -> None:
        broken = copy.deepcopy(self.config)
        blocker = self.root / "not-a-directory"
        blocker.write_text("this is a file, not an archive\n", encoding="utf-8")
        broken["archive_dir"] = str(blocker)
        with self.dead_candystore():
            result = report_delivery.collect(self.section, REPORT_DATE, broken)
        self.assertEqual("failed", result.status)
        self.assertIn("not a directory", result.reason)
        self.assertIn("unreachable", result.reason)
        self.assertEqual("unknown", result.metrics["days_delivered"])
        self.assertEqual("unknown", result.metrics["consecutive_delivered_streak"])

    def test_http_error_is_failed_text_not_a_traceback(self) -> None:
        error = urllib.error.HTTPError("http://127.0.0.1:8683/events", 503, "no", None, None)
        with mock.patch.object(report_delivery, "_fetch_page", side_effect=error):
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("HTTP 503", result.reason)

    def test_garbage_json_from_candystore_is_partial(self) -> None:
        with mock.patch.object(report_delivery, "_fetch_page", return_value=["not", "a", "page"]):
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("events array", result.reason)

    def test_an_unexpected_transport_error_is_partial_not_a_traceback(self) -> None:
        import http.client

        error = http.client.IncompleteRead(b"half")
        with mock.patch.object(report_delivery, "_fetch_page", side_effect=error):
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("IncompleteRead", result.reason)

    def test_an_exhausted_page_budget_is_partial_not_a_silent_truncation(self) -> None:
        full = page([event("2026-08-16") for _ in range(report_delivery.PAGE_SIZE)])
        full["events"] = full["events"][: report_delivery.PAGE_SIZE]
        with mock.patch.object(report_delivery, "_fetch_page", return_value=full):
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("page budget was exhausted", result.reason)
        self.assertEqual("unknown", result.metrics["events_found"])

    def test_empty_config_is_failed_with_a_named_reason(self) -> None:
        with self.dead_candystore():
            result = report_delivery.collect(self.section, REPORT_DATE, {})
        self.assertEqual("failed", result.status)
        self.assertIn("archive_dir", result.reason)

    def test_bad_report_date_is_failed(self) -> None:
        result = self.collect(report_date="yesterday")
        self.assertEqual("failed", result.status)
        self.assertIn("ISO", result.reason)

    def test_collect_never_raises_on_garbage_input(self) -> None:
        result = report_delivery.collect(None, None, None)  # type: ignore[arg-type]
        self.assertEqual("failed", result.status)
        self.assertTrue(result.reason)

    def test_a_crash_inside_the_collector_becomes_failed(self) -> None:
        with mock.patch.object(report_delivery, "_scan_archive", side_effect=RuntimeError("boom")):
            result = self.collect()
        self.assertEqual("failed", result.status)
        self.assertIn("RuntimeError: boom", result.reason)


class PartialDataTests(CollectorTestCase):
    def test_a_missing_day_is_recorded_not_dropped(self) -> None:
        days = window()
        for day in days:
            if day != "2026-08-14":
                self.publish(day)
        with self.serve([event(day) for day in days if day != "2026-08-14"]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertIn("2026-08-11..2026-08-17", result.summary)
        self.assertIn("1 missing", result.summary)
        self.assertEqual("degraded", result.metrics["delivery_health"])
        self.assertEqual(6, result.metrics["days_delivered"])
        self.assertEqual(1, result.metrics["days_missing"])
        self.assertEqual("missing", self.days(result)["2026-08-14"])
        self.assertEqual(7, len(self.days(result)))

    def test_an_invalid_generation_is_invalid_not_delivered(self) -> None:
        for day in window():
            self.publish(day)
        self.corrupt_published_report("2026-08-13")
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        self.assertEqual(1, result.metrics["days_invalid"])
        self.assertEqual(6, result.metrics["days_delivered"])
        self.assertEqual("invalid", self.days(result)["2026-08-13"])

    def test_a_staged_generation_without_a_pointer_is_unpublished(self) -> None:
        self.stage_without_pointer("2026-08-12")
        with self.serve([]):
            result = self.collect()
        self.assertEqual("unpublished-but-archived", self.days(result)["2026-08-12"])
        self.assertEqual(1, result.metrics["days_unpublished_but_archived"])
        self.assertEqual(0, result.metrics["days_delivered"])

    def test_streak_counts_back_from_the_newest_due_day(self) -> None:
        for day in window()[-4:-1]:
            self.publish(day)
        with self.serve([]):
            result = self.collect()
        self.assertEqual(3, result.metrics["consecutive_delivered_streak"])

    def test_partial_metrics_never_claim_a_clean_window(self) -> None:
        with self.serve([]):
            result = self.collect()
        self.assertEqual(6, result.metrics["days_missing"])
        self.assertEqual(1, result.metrics["days_in_progress"])
        self.assertEqual(0, result.metrics["consecutive_delivered_streak"])
        self.assertIn("0 of 6 due days delivered", result.summary)


class InProgressTests(CollectorTestCase):
    def test_the_day_this_run_produces_is_not_counted_missing(self) -> None:
        for day in window()[:-1]:
            self.publish(day)
        with self.serve([event(day) for day in window()[:-1]]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual(0, result.metrics["days_missing"])
        self.assertEqual(1, result.metrics["days_in_progress"])
        self.assertEqual(6, result.metrics["days_delivered"])
        self.assertEqual("in-progress", self.days(result)[REPORT_DATE])
        self.assertEqual(0, result.metrics["archive_event_disagreements"])

    def test_an_already_published_report_date_stays_delivered(self) -> None:
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        self.assertEqual("delivered", self.days(result)[REPORT_DATE])
        self.assertEqual(0, result.metrics["days_in_progress"])

    def test_an_event_for_the_in_progress_day_is_still_a_disagreement(self) -> None:
        for day in window()[:-1]:
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        self.assertEqual(1, result.metrics["archive_event_disagreements"])
        self.assertTrue(
            any(
                line.startswith(
                    f"DISAGREEMENT {REPORT_DATE} published-but-never-archived "
                    "(event-without-archive)"
                )
                for line in result.detail
            )
        )


class DisagreementTests(CollectorTestCase):
    def test_event_without_archive_is_named(self) -> None:
        for day in window()[:-2]:
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        lines = [line for line in result.detail if line.startswith("DISAGREEMENT")]
        self.assertEqual(2, len(lines))
        self.assertIn("event-without-archive", lines[0])
        self.assertIn("reported success it did not achieve", lines[0])
        self.assertEqual(2, result.metrics["archive_event_disagreements"])
        self.assertTrue(any("DISAGREEMENT" in item for item in result.caveats))

    def test_archive_without_event_is_named(self) -> None:
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()[:-1]]):
            result = self.collect()
        lines = [line for line in result.detail if "archive-without-event" in line]
        self.assertEqual(1, len(lines))
        self.assertIn(REPORT_DATE, lines[0])
        self.assertIn("event publication failed", lines[0])
        self.assertEqual(1, result.metrics["archive_event_disagreements"])

    def test_agreement_produces_no_disagreements(self) -> None:
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        self.assertEqual([], [line for line in result.detail if "DISAGREEMENT" in line])

    def test_duplicate_events_for_one_day_are_flagged(self) -> None:
        for day in window():
            self.publish(day)
        events = [event(day) for day in window()]
        events.append(event("2026-08-16", run_id="dev-journal-second"))
        with self.serve(events):
            result = self.collect()
        self.assertEqual(8, result.metrics["events_found"])
        self.assertTrue(any("duplicate completion events" in item for item in result.caveats))

    def test_events_outside_the_window_are_ignored(self) -> None:
        with self.serve([event("2020-01-01"), event("2026-08-16")]):
            result = self.collect()
        self.assertEqual(1, result.metrics["events_found"])

    def test_events_without_a_report_date_are_counted_as_unattributed(self) -> None:
        orphan = event("2026-08-16")
        orphan["data"].pop("report_date")
        with self.serve([orphan]):
            result = self.collect()
        self.assertEqual(0, result.metrics["events_found"])
        self.assertTrue(any("no data.report_date" in item for item in result.caveats))


class DeliveryVerdictTests(CollectorTestCase):
    """A detected delivery failure must reach every consumer -- as content.

    The verdict belongs in ``summary``, ``metrics.delivery_health``, ``caveats``
    and ``detail``. It must NOT reach ``status``, which answers a different
    question: could this collector do its work? A gap it found cleanly is a
    finished job, and calling that ``partial`` latched the pipeline into a
    failure it could never leave (see ``test_status_semantics.py``).

    So each test here asserts both halves: the finding is loud, and the status
    is the collection's, not the finding's.
    """

    def verdicts(self, result) -> dict[str, str]:
        """The per-day cross-check verdict, parsed back out of detail."""
        parsed: dict[str, str] = {}
        for line in result.detail:
            fields = line.split(" ")
            if fields[0] not in set(window()):
                continue
            marked = [f for f in fields if f.startswith("cross_check=")]
            parsed[fields[0]] = marked[0].split("=", 1)[1] if marked else "agreed"
        return parsed

    def assertLoud(self, result, *fragments: str) -> None:
        """The verdict is in the summary AND in a caveat, so it survives both the
        narrated path (which renders caveats) and any consumer reading summaries."""
        for fragment in fragments:
            self.assertIn(fragment, result.summary)
        joined = " ".join(result.caveats)
        for fragment in fragments:
            self.assertIn(fragment, joined)

    def test_a_day_with_no_archive_and_no_event_is_a_complete_collection(self) -> None:
        """The 2026-08-18 shape: the run simply never happened.

        Nothing archived, nothing in Candystore, no evidence anywhere that a
        report was produced. Six due days of pure absence -- and a collector that
        read both of its sources and answered correctly.
        """
        with self.serve([]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual("", result.reason)
        self.assertEqual("missing", self.days(result)["2026-08-14"])
        self.assertEqual(6, result.metrics["days_missing"])
        self.assertEqual(6, result.metrics["delivery_gaps"])
        self.assertEqual("failed", result.metrics["delivery_health"])
        self.assertLoud(result, "6 of 6 due day(s)", "no valid published report")
        self.assertTrue(result.summary.startswith("report-delivery: DELIVERY FAILED"))

    def test_one_missing_day_among_six_delivered_is_degraded_not_failed(self) -> None:
        days = window()
        for day in days:
            if day != "2026-08-13":
                self.publish(day)
        with self.serve([event(day) for day in days if day != "2026-08-13"]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual("degraded", result.metrics["delivery_health"])
        self.assertEqual(1, result.metrics["delivery_gaps"])
        self.assertLoud(result, "1 missing")

    def test_phantom_completion_events_are_reported(self) -> None:
        """Events claim seven delivered days; the archive holds none of them."""
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual(7, result.metrics["days_event_without_archive"])
        self.assertEqual(0, result.metrics["days_archive_without_event"])
        self.assertEqual("failed", result.metrics["delivery_health"])
        self.assertLoud(result, "reported success it did not achieve")
        self.assertEqual(
            {day: "published-but-never-archived" for day in window()},
            self.verdicts(result),
        )

    def test_an_archived_day_with_no_event_is_reported(self) -> None:
        """Publication failed: the report exists, nothing downstream can see it."""
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()[:-1]]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual(1, result.metrics["days_archive_without_event"])
        self.assertEqual(0, result.metrics["days_event_without_archive"])
        self.assertEqual(0, result.metrics["delivery_gaps"])
        self.assertEqual("degraded", result.metrics["delivery_health"])
        self.assertLoud(result, "event publication failed")
        self.assertEqual(
            "archived-but-never-published", self.verdicts(result)[REPORT_DATE]
        )

    def test_an_invalid_generation_is_reported(self) -> None:
        for day in window():
            self.publish(day)
        self.corrupt_published_report("2026-08-13")
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual(1, result.metrics["days_invalid"])
        self.assertEqual(1, result.metrics["delivery_gaps"])
        self.assertLoud(result, "1 invalid")

    def test_a_generation_staged_without_a_pointer_is_reported(self) -> None:
        published = [day for day in window()[:-1] if day != "2026-08-12"]
        for day in published:
            self.publish(day)
        self.stage_without_pointer("2026-08-12")
        with self.serve([event(day) for day in published]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual(1, result.metrics["days_unpublished_but_archived"])
        self.assertLoud(result, "archived but never published")

    def test_every_day_delivered_and_evented_is_still_complete(self) -> None:
        """The fix must not make a healthy window look broken."""
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual("", result.reason)
        self.assertEqual("ok", result.metrics["delivery_health"])
        self.assertEqual(0, result.metrics["delivery_gaps"])
        self.assertNotIn("DELIVERY", result.summary)
        self.assertEqual([], [item for item in result.caveats if "DELIVERY" in item])
        self.assertEqual({day: "agreed" for day in window()}, self.verdicts(result))

    def test_the_in_progress_run_is_never_counted_as_a_delivery_failure(self) -> None:
        """Today's run publishes after collection; it is not a gap."""
        for day in window()[:-1]:
            self.publish(day)
        with self.serve([event(day) for day in window()[:-1]]):
            result = self.collect()
        self.assertEqual("complete", result.status)
        self.assertEqual("ok", result.metrics["delivery_health"])
        self.assertEqual(0, result.metrics["delivery_gaps"])
        self.assertEqual(1, result.metrics["days_in_progress"])
        self.assertEqual(0, result.metrics["days_missing"])
        self.assertEqual("in-progress", self.days(result)[REPORT_DATE])
        self.assertEqual("agreed", self.verdicts(result)[REPORT_DATE])

    def test_a_gap_survives_an_unreadable_second_source(self) -> None:
        """Candystore down does not excuse the archive gaps we can see.

        The status becomes ``partial`` because a source could not be read -- and
        ``reason`` says exactly that and nothing else. The gap is content.
        """
        for day in window()[:-2]:
            self.publish(day)
        with self.dead_candystore():
            result = self.collect()
        self.assertEqual("partial", result.status)
        self.assertIn("Candystore not read", result.reason)
        self.assertNotIn("missing", result.reason)
        self.assertLoud(result, "1 missing")
        self.assertEqual(1, result.metrics["delivery_gaps"])
        self.assertEqual("degraded", result.metrics["delivery_health"])
        self.assertEqual("unknown", result.metrics["days_event_without_archive"])
        self.assertEqual("unknown", result.metrics["days_archive_without_event"])

    def test_an_unreadable_archive_is_a_failed_collection(self) -> None:
        """The archive is the source of the claim, not a cross-check of it.

        Without it the collector cannot answer its question for any day, which
        is ``failed`` -- and because this section is required, that is what keeps
        a blind pipeline from exiting 0.
        """
        broken = copy.deepcopy(self.config)
        blocker = self.root / "not-a-directory"
        blocker.write_text("this is a file, not an archive\n", encoding="utf-8")
        broken["archive_dir"] = str(blocker)
        with self.serve([]):
            result = report_delivery.collect(self.section, REPORT_DATE, broken)
        self.assertEqual("failed", result.status)
        self.assertIn("no claim about any day is possible", result.reason)
        self.assertEqual("unknown", result.metrics["delivery_health"])
        self.assertEqual("unknown", result.metrics["delivery_gaps"])

    def test_the_verdict_reaches_a_valid_artifact(self) -> None:
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        artifact = result.to_artifact("run-under-test", 24)
        self.assertEqual(artifact, validate_section_artifact(artifact, "report-delivery"))
        self.assertEqual("complete", artifact["status"])
        self.assertNotIn("reason", artifact)
        self.assertIn("reported success it did not achieve", artifact["summary"])
        self.assertTrue(
            any("reported success it did not achieve" in item for item in artifact["caveats"])
        )
        self.assertEqual("failed", artifact["metrics"]["delivery_health"])

    def test_standalone_exits_zero_on_an_undelivered_window_but_says_so(self) -> None:
        """Exit code answers "could the check run". The verdict goes to stderr,
        so exit 0 is never the only thing an operator is shown."""
        path = self.root / "report.json"
        path.write_text(json.dumps(self.config), encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with self.serve([]), redirect_stdout(out), redirect_stderr(err):
            code = report_delivery.main(["--date", REPORT_DATE, "--config", str(path)])
        artifact = json.loads(out.getvalue())
        self.assertEqual(0, code)
        self.assertEqual("complete", artifact["status"])
        self.assertEqual("failed", artifact["metrics"]["delivery_health"])
        self.assertIn("delivery health failed", err.getvalue())
        self.assertIn("DELIVERY FAILED", err.getvalue())


class AllowlistTests(CollectorTestCase):
    def test_no_raw_event_payload_reaches_the_artifact(self) -> None:
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            result = self.collect()
        rendered = json.dumps(result.to_artifact("run-under-test", 24))
        for leaked in (
            "bloodbank.agent.33god-pm",
            "nous_research",
            "/home/delorenj/private/journal.txt",
            "destination_alias",
            "agent_cli",
        ):
            self.assertNotIn(leaked, rendered)

    def test_the_event_allowlist_keeps_only_named_keys(self) -> None:
        filtered = report_delivery.allowlist(
            event("2026-08-16"),
            report_delivery.EVENT_FIELDS,
            opaque_keys=report_delivery.EVENT_OPAQUE,
        )
        self.assertEqual({"id", "type", "time", "data"}, set(filtered))
        self.assertEqual(
            {"run_id", "report_date", "outcome"},
            set(filtered["data"]),
        )
        self.assertEqual({"status", "sections"}, set(filtered["data"]["outcome"]))
        self.assertEqual({"overview": "complete"}, filtered["data"]["outcome"]["sections"])


class StandaloneTests(CollectorTestCase):
    def config_file(self) -> Path:
        path = self.root / "report.json"
        path.write_text(json.dumps(self.config), encoding="utf-8")
        return path

    def run_main(self, *argv: str) -> tuple[int, dict]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = report_delivery.main(list(argv))
        return code, json.loads(buffer.getvalue())

    def test_standalone_prints_a_valid_artifact_and_exits_zero_when_complete(self) -> None:
        for day in window():
            self.publish(day)
        with self.serve([event(day) for day in window()]):
            code, artifact = self.run_main(
                "--date", REPORT_DATE, "--config", str(self.config_file())
            )
        self.assertEqual(0, code)
        self.assertEqual(artifact, validate_section_artifact(artifact, "report-delivery"))
        self.assertEqual("complete", artifact["status"])

    def test_standalone_exits_nonzero_when_a_source_is_unreadable(self) -> None:
        with self.dead_candystore():
            code, artifact = self.run_main(
                "--date", REPORT_DATE, "--config", str(self.config_file())
            )
        self.assertEqual(1, code)
        self.assertEqual("partial", artifact["status"])
        self.assertEqual(artifact, validate_section_artifact(artifact, "report-delivery"))

    def test_an_unloadable_config_still_prints_a_valid_failed_artifact(self) -> None:
        broken = self.root / "broken.json"
        broken.write_text("{ not json", encoding="utf-8")
        with self.dead_candystore():
            code, artifact = self.run_main("--date", REPORT_DATE, "--config", str(broken))
        self.assertEqual(1, code)
        self.assertEqual("failed", artifact["status"])
        self.assertEqual(artifact, validate_section_artifact(artifact, "report-delivery"))
        self.assertTrue(any("no usable config" in item for item in artifact["caveats"]))


if __name__ == "__main__":
    unittest.main()
