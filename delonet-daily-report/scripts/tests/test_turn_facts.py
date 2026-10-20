"""Tests for the turn_facts collector.

The point of every one of these is the same: the collector must never claim a
completeness it did not achieve. Happy path, dead source, truncated
pagination, the signal floor, and an empty day each get an assertion on the
*status* as well as the data.
"""

from __future__ import annotations

import os
import unittest
import urllib.parse
from unittest import mock

from collectors import turn_facts
from collectors.base import run_collector
from reportctl_contracts import validate_section_artifact

DATE = "2026-10-20"
# America/New_York (EDT, UTC-4): the local day 2026-10-20 is the UTC window
# 2026-10-20T04:00:00Z .. 2026-10-21T04:00:00Z.
IN_WINDOW = "2026-10-20T15:30:00Z"
BEFORE_WINDOW = "2026-10-20T03:59:59Z"  # still 2026-10-19 in New York
AFTER_WINDOW = "2026-10-21T04:00:01Z"  # already 2026-10-21 in New York
CONFIG = {"timezone": "America/New_York", "max_age_hours": 24}


def turn(
    *,
    time: str = IN_WINDOW,
    project: str | None = "33god",
    signal: float = 0.9,
    action: str = "code",
    blocker: str | None = None,
    outcome: str = "completed",
) -> dict:
    return {
        "id": "evt-1",
        "type": "bloodbank.conversation.turn.annotated",
        "time": time,
        "project": project,
        "cli": "hermes",
        "actor": {"cli": "hermes", "type": "agent_cli"},
        "data": {
            "signal": signal,
            "action": action,
            "artifacts": ["README.md"],
            "blocker": blocker,
            "outcome": outcome,
            "thread_id": "thread-1",
            "target_event_id": "evt-0",
        },
    }


class FakeCandystore:
    """Serves /events for turn.annotated; records every URL it was asked for."""

    def __init__(self, events: list[dict], *, fail: bool = False):
        self.events = events
        self.fail = fail
        self.urls: list[str] = []

    def __call__(self, url: str, timeout: int = 30):
        self.urls.append(url)
        if "/events" in url:
            if self.fail:
                raise turn_facts.SourceUnavailable(f"cannot reach {url}: refused")
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            limit = int(query["limit"][0])
            offset = int(query["offset"][0])
            return {"events": self.events[offset : offset + limit]}
        raise AssertionError(f"collector fetched an unexpected URL: {url}")


def section(**options) -> dict:
    options.setdefault("candystore_url", "http://127.0.0.1:8683")
    return {
        "id": "turn-facts",
        "title": "Agent Turn Facts",
        "collector": "turn_facts",
        "required": False,
        "enabled": True,
        "max_age_hours": 24,
        "options": options,
    }


def collect(store: FakeCandystore, sec: dict | None = None, config: dict | None = None):
    with mock.patch.object(turn_facts, "fetch_json", store):
        return turn_facts.collect(sec or section(), DATE, config or CONFIG)


def artifact(result) -> dict:
    """Every result must survive the real contract validator."""
    return validate_section_artifact(result.to_artifact("run-test", 24), "turn-facts")


class HappyPathTests(unittest.TestCase):
    def test_complete_status_with_real_counts(self) -> None:
        store = FakeCandystore(
            [
                turn(project="33god", action="code", time="2026-10-20T15:30:00Z"),
                turn(project="33god", action="code", time="2026-10-20T14:00:00Z"),
                turn(project="33god", action="review", time="2026-10-20T13:00:00Z"),
                turn(project="bloodbank", action="deploy", time="2026-10-20T12:00:00Z"),
                turn(
                    project="bloodbank",
                    action="triage",
                    blocker="TOWE-7 grooming",
                    time="2026-10-20T11:00:00Z",
                ),
                # One event clearly older than the day start ends pagination.
                turn(project="bloodbank", action="old", time=BEFORE_WINDOW),
            ]
        )
        result = collect(store)
        doc = artifact(result)

        self.assertEqual("complete", doc["status"])
        self.assertNotIn("reason", doc)
        self.assertEqual(5, doc["metrics"]["annotated_turns"])
        self.assertEqual(2, doc["metrics"]["projects"])
        self.assertEqual(1, doc["metrics"]["turns_with_blockers"])
        self.assertEqual(0.9, doc["metrics"]["avg_signal"])
        self.assertTrue(doc["metrics"]["candystore_reachable"])
        detail = doc["detail"]
        self.assertIn("33god: 3 turns, top actions: code, review", detail)
        self.assertIn("bloodbank: 2 turns, top actions: deploy, triage", detail)
        self.assertIn("bloodbank: BLOCKED - TOWE-7 grooming", detail)
        self.assertIn("busiest: 33god (3), bloodbank (2)", doc["summary"])
        self.assertIn("1 turn(s) reported a blocker", doc["summary"])
        # Events outside the local-day window are excluded.
        self.assertNotIn("old", "\n".join(detail))

    def test_local_day_bounds_follow_config_timezone(self) -> None:
        store = FakeCandystore(
            [
                turn(time=BEFORE_WINDOW, action="yesterday"),
                turn(time=IN_WINDOW, action="today"),
                turn(time=AFTER_WINDOW, action="tomorrow"),
            ]
        )
        result = collect(store)
        self.assertEqual("complete", result.status)
        self.assertEqual(1, result.metrics["annotated_turns"])
        self.assertEqual(["33god: 1 turns, top actions: today"], result.detail)

    def test_missing_project_renders_as_unknown(self) -> None:
        store = FakeCandystore([turn(project=None), turn(project="  ")])
        result = collect(store)
        self.assertEqual(1, result.metrics["projects"])
        self.assertTrue(result.detail[0].startswith("unknown: 2 turns"))

    def test_literal_none_blocker_is_not_a_blocker(self) -> None:
        # The enricher writes the literal string "none" when a turn has no
        # blocker; rendering it as BLOCKED would invent blockers.
        store = FakeCandystore([turn(blocker="none"), turn(blocker="None")])
        result = collect(store)
        self.assertEqual(0, result.metrics["turns_with_blockers"])
        self.assertFalse(any("BLOCKED" in line for line in result.detail))
        self.assertIn("0 turn(s) reported a blocker", result.summary)


class SignalFloorTests(unittest.TestCase):
    def test_low_signal_turns_excluded_but_counted_in_a_caveat(self) -> None:
        store = FakeCandystore(
            [
                turn(signal=0.9),
                turn(signal=0.2, action="noise"),
                turn(signal=0.1, action="noise"),
            ]
        )
        result = collect(store)
        doc = artifact(result)
        self.assertEqual(1, doc["metrics"]["annotated_turns"])
        self.assertEqual(2, doc["metrics"]["low_signal_turns"])
        caveat_text = "\n".join(doc["caveats"])
        self.assertIn("2 annotated turn(s)", caveat_text)
        self.assertIn("excluded from", caveat_text)
        self.assertNotIn("noise", "\n".join(doc["detail"]))

    def test_missing_signal_is_below_the_floor(self) -> None:
        event = turn(signal=0.9)
        del event["data"]["signal"]
        store = FakeCandystore([event, turn()])
        result = collect(store)
        self.assertEqual(1, result.metrics["annotated_turns"])
        self.assertEqual(1, result.metrics["low_signal_turns"])

    def test_all_turns_below_floor_is_empty_with_reason(self) -> None:
        store = FakeCandystore([turn(signal=0.1), turn(signal=0.4)])
        result = collect(store)
        doc = artifact(result)
        self.assertEqual("empty", doc["status"])
        self.assertIn("signal floor", doc["reason"])
        self.assertEqual(0, doc["metrics"]["annotated_turns"])
        self.assertEqual(2, doc["metrics"]["low_signal_turns"])


class EmptyAndFailureTests(unittest.TestCase):
    def test_empty_day_is_empty_not_failed(self) -> None:
        store = FakeCandystore([turn(time=BEFORE_WINDOW)])
        result = collect(store)
        doc = artifact(result)
        self.assertEqual("empty", doc["status"])
        self.assertIn(f"no {turn_facts.TURN_TYPE} events on {DATE}", doc["reason"])
        self.assertEqual(0, doc["metrics"]["annotated_turns"])
        self.assertTrue(doc["metrics"]["candystore_reachable"])

    def test_candystore_down_is_failed_with_url(self) -> None:
        store = FakeCandystore([], fail=True)
        result = collect(store)
        doc = artifact(result)
        self.assertEqual("failed", doc["status"])
        self.assertIn("Candystore turn-event history unavailable", doc["reason"])
        self.assertIn("127.0.0.1:8683", doc["reason"])
        self.assertFalse(doc["metrics"]["candystore_reachable"])

    def test_bad_date_is_failed(self) -> None:
        with mock.patch.object(turn_facts, "fetch_json", FakeCandystore([])):
            result = turn_facts.collect(section(), "not-a-date", CONFIG)
        self.assertEqual("failed", result.status)
        self.assertIn("not an ISO YYYY-MM-DD date", result.reason)

    def test_missing_date_is_failed(self) -> None:
        result = turn_facts.collect(section(), None, CONFIG)
        self.assertEqual("failed", result.status)
        self.assertIn("without a report date", result.reason)

    def test_bad_timezone_falls_back_with_a_caveat(self) -> None:
        store = FakeCandystore([turn()])
        result = collect(store, config={"timezone": "Not/AZone"})
        caveat_text = "\n".join(result.caveats)
        self.assertIn("not a known IANA zone", caveat_text)


class PaginationTests(unittest.TestCase):
    def test_pages_until_an_event_predates_the_day(self) -> None:
        # page_size=2: two full in-window pages, then a page whose oldest
        # event predates the day start, which ends the walk.
        events = [
            turn(time="2026-10-20T20:00:00Z"),
            turn(time="2026-10-20T19:00:00Z"),
            turn(time="2026-10-20T18:00:00Z"),
            turn(time="2026-10-20T17:00:00Z"),
            turn(time="2026-10-20T16:00:00Z"),
            turn(time=BEFORE_WINDOW),
        ]
        store = FakeCandystore(events)
        result = collect(store, section(page_size=2))
        self.assertEqual("complete", result.status)
        self.assertEqual(5, result.metrics["annotated_turns"])
        self.assertEqual(3, len(store.urls))

    def test_page_budget_exhausted_is_partial(self) -> None:
        # Every page is full and every event is inside the window, so the walk
        # never reaches the day boundary within the page budget.
        events = [turn(time="2026-10-20T12:00:00Z") for _ in range(6)]
        store = FakeCandystore(events)
        result = collect(store, section(page_size=2, max_pages=3))
        doc = artifact(result)
        self.assertEqual("partial", doc["status"])
        self.assertIn("page budget", doc["reason"])
        self.assertEqual(6, doc["metrics"]["annotated_turns"])


class RunnerContractTests(unittest.TestCase):
    def test_run_collector_returns_the_result(self) -> None:
        store = FakeCandystore([turn()])
        with mock.patch.object(turn_facts, "fetch_json", store):
            result = run_collector(
                lambda cfg: turn_facts.collect(cfg, DATE, CONFIG), section()
            )
        self.assertEqual("complete", result.status)
        self.assertEqual("turn-facts", result.id)

    def test_run_collector_converts_crashes(self) -> None:
        def boom(cfg):
            raise RuntimeError("boom")

        result = run_collector(boom, section())
        self.assertEqual("failed", result.status)
        self.assertIn("RuntimeError", result.reason)

    def test_env_var_overrides_configured_url(self) -> None:
        store = FakeCandystore([turn()])
        with mock.patch.dict(os.environ, {"CANDYSTORE_URL": "http://10.0.0.9:9999/"}):
            with mock.patch.object(turn_facts, "fetch_json", store):
                result = turn_facts.collect(section(), DATE, CONFIG)
        self.assertEqual("http://10.0.0.9:9999", result.metrics["candystore_url"])
        self.assertIn("CANDYSTORE_URL", "\n".join(result.caveats))
        self.assertTrue(store.urls[0].startswith("http://10.0.0.9:9999/events"))


if __name__ == "__main__":
    unittest.main()
