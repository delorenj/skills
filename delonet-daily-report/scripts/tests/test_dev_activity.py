"""Tests for the dev-activity collector.

The point of every one of these is the same: the collector must never report
success it did not achieve. Happy path, dead source, and partial source each
get an assertion on the *status* as well as the data.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from collectors import dev_activity
from reportctl_contracts import validate_section_artifact
from test_fixtures import config as base_config

SCRIPTS = Path(__file__).resolve().parents[1]

# Hermetic git: no global or system config, so the machine's hooksPath, signing
# key, and identity never reach these repositories.
GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}
GIT_IDENTITY = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]
IN_WINDOW = "2026-08-17T12:00:00Z"
DATE = "2026-08-17"


def git(repo: Path, *args: str, when: str | None = None) -> subprocess.CompletedProcess:
    env = dict(GIT_ENV)
    if when:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )


def make_repo(path: Path, messages: list[str], when: str = IN_WINDOW) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main", ".")
    for index, message in enumerate(messages):
        (path / f"file{index}.txt").write_text(message, encoding="utf-8")
        git(path, *GIT_IDENTITY, "add", ".")
        git(path, *GIT_IDENTITY, "commit", "-q", "-m", message, when=when)
    return path


def event(
    event_type: str = "bloodbank.v1.agent.tool.completed",
    *,
    project: str = "widget",
    cli: str = "claude",
    time: str = "2026-08-17T15:30:00Z",
    correlationid: str = "corr-1",
    data: dict | None = None,
) -> dict:
    return {
        "id": "evt-1",
        "type": event_type,
        "time": time,
        "cli": cli,
        "project": project,
        "correlationid": correlationid,
        "producer": "claude-code",
        "data": data if data is not None else {},
    }


def heatmap(buckets: list[tuple[str, str, int]]) -> dict:
    return {
        "buckets": [
            {"hour": hour, "bucket": bucket, "project": bucket, "count": count}
            for hour, bucket, count in buckets
        ]
    }


class FakeCandystore:
    """Serves /events and /summary/heatmap; records every URL it was asked for."""

    def __init__(self, events: list[dict], summary: dict | None = None, *, fail: set | None = None):
        self.events = events
        self.summary = summary if summary is not None else {"buckets": []}
        self.fail = fail or set()
        self.urls: list[str] = []

    def __call__(self, url: str, timeout: int = 30):
        self.urls.append(url)
        if "/summary/heatmap" in url:
            if "heatmap" in self.fail:
                raise dev_activity.SourceUnavailable(f"cannot reach {url}: refused")
            return self.summary
        if "/events" in url:
            if "events" in self.fail:
                raise dev_activity.SourceUnavailable(f"cannot reach {url}: refused")
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            limit = int(query["limit"][0])
            offset = int(query["offset"][0])
            return {"events": self.events[offset : offset + limit]}
        raise AssertionError(f"collector fetched an unexpected URL: {url}")


class CollectorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        # Failure injection uses this variable; it must not leak into tests.
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("CANDYSTORE_URL", None)

    def config(self, roots: list[Path] | None = None) -> dict:
        config = base_config(self.root)
        config["project_roots"] = [str(path) for path in (roots or [])] or [str(self.root / "none")]
        return config

    def section(self, **options) -> dict:
        options.setdefault("candystore_url", "http://127.0.0.1:8683")
        return {
            "id": "dev-activity",
            "title": "Developer Activity",
            "collector": "dev_activity",
            "required": True,
            "enabled": True,
            "max_age_hours": 24,
            "options": options,
        }

    def collect(self, store: FakeCandystore, section: dict, config: dict):
        with mock.patch.object(dev_activity, "fetch_json", store):
            return dev_activity.collect(section, DATE, config)

    def artifact(self, result) -> dict:
        """Every result must survive the real contract validator."""
        return validate_section_artifact(result.to_artifact("run-test", 24), "dev-activity")


class HappyPathTests(CollectorTestCase):
    def test_complete_status_with_real_git_and_events(self) -> None:
        repo = make_repo(self.root / "code" / "widget", ["feat: add the widget", "fix: the widget"])
        store = FakeCandystore(
            [
                event(correlationid="corr-1"),
                event(correlationid="corr-2", cli="codex"),
                event(
                    "bloodbank.v1.repo.decision.recorded",
                    correlationid="corr-2",  # same session: sessions are de-duplicated
                    data={"issue": "WID-1", "repo": "widget", "title": "Ship it\nsecond line"},
                ),
                event(
                    "bloodbank.v1.agent.session.ended",
                    correlationid="corr-3",
                    data={"git_commits": ["abc123", "def456"], "total_turns": 12},
                ),
            ],
            heatmap([("2026-08-17T15:00:00Z", "widget", 3), ("2026-08-17T09:00:00Z", "widget", 1)]),
        )

        result = self.collect(store, self.section(), self.config([repo]))
        artifact = self.artifact(result)

        self.assertEqual("complete", artifact["status"])
        self.assertNotIn("reason", artifact)
        self.assertEqual(4, artifact["metrics"]["event_count"])
        self.assertEqual(3, artifact["metrics"]["session_count"])
        self.assertEqual(1, artifact["metrics"]["decision_count"])
        self.assertEqual(1, artifact["metrics"]["commit_count"])
        self.assertEqual(1, artifact["metrics"]["project_count"])
        self.assertEqual("2026-08-17T15:00:00Z", artifact["metrics"]["peak_hour"])
        self.assertEqual(2, artifact["metrics"]["git_commit_count"])
        self.assertTrue(artifact["metrics"]["candystore_reachable"])
        detail = "\n".join(artifact["detail"])
        self.assertIn("=== widget ===", detail)
        self.assertIn("feat: add the widget", detail)
        self.assertIn("[widget] WID-1: Ship it", detail)
        self.assertNotIn("second line", detail)
        self.assertIn("widget (claude, 12 turns): 2 commit(s)", detail)

    def test_dead_summary_endpoints_are_never_fetched(self) -> None:
        store = FakeCandystore([event()], heatmap([("2026-08-17T15:00:00Z", "widget", 1)]))
        self.collect(store, self.section(), self.config())
        fetched = " ".join(store.urls)
        for dead in ("/summary/daily", "/summary/by-project", "/summary/by-cli"):
            self.assertNotIn(dead, fetched)
        self.assertTrue(any("/summary/heatmap" in url for url in store.urls))

    def test_git_log_reads_branches_outside_head_and_marks_them(self) -> None:
        """A commit off HEAD is real work: counted, and marked as not landed.

        This test used to assert the opposite -- that a commit on a branch other
        than the checked-out one is ignored. That is what made the section claim
        coverage it did not have (see test_dev_activity_git_scope.py).
        """
        repo = make_repo(self.root / "code" / "widget", ["on main"])
        git(repo, "checkout", "-q", "-b", "stale")
        (repo / "stale.txt").write_text("stale", encoding="utf-8")
        git(repo, *GIT_IDENTITY, "add", ".")
        git(repo, *GIT_IDENTITY, "commit", "-q", "-m", "on a stale branch", when=IN_WINDOW)
        git(repo, "checkout", "-q", "main")

        store = FakeCandystore([event(project="widget")], heatmap([]))
        result = self.collect(store, self.section(), self.config([repo]))
        artifact = self.artifact(result)
        detail = "\n".join(artifact["detail"])

        self.assertIn("on main", detail)
        self.assertIn("on a stale branch  [not reachable from main]", detail)
        self.assertEqual(2, artifact["metrics"]["git_commit_count"])
        self.assertEqual(1, artifact["metrics"]["git_commits_off_head"])


class SourceUnreachableTests(CollectorTestCase):
    def test_dead_candystore_is_failed_not_an_exception(self) -> None:
        """A refused connection must degrade the section, never raise."""
        section = self.section(candystore_url="http://127.0.0.1:9", http_timeout_seconds=2)
        result = dev_activity.collect(section, DATE, self.config())
        artifact = self.artifact(result)

        self.assertEqual("failed", artifact["status"])
        self.assertIn("Candystore event history unavailable", artifact["reason"])
        self.assertIn("127.0.0.1:9", artifact["reason"])
        self.assertFalse(artifact["metrics"]["candystore_reachable"])
        self.assertNotIn("detail", artifact)

    def test_environment_override_is_honoured_and_recorded(self) -> None:
        os.environ["CANDYSTORE_URL"] = "http://127.0.0.1:9"
        result = dev_activity.collect(self.section(), DATE, self.config())
        artifact = self.artifact(result)

        self.assertEqual("failed", artifact["status"])
        self.assertIn("127.0.0.1:9", artifact["reason"])
        self.assertTrue(
            any("CANDYSTORE_URL environment variable" in item for item in artifact["caveats"])
        )

    def test_unexpected_exception_becomes_failed(self) -> None:
        def explode(url: str, timeout: int = 30):
            raise RuntimeError("something nobody anticipated")

        with mock.patch.object(dev_activity, "fetch_json", explode):
            result = dev_activity.collect(self.section(), DATE, self.config())
        artifact = self.artifact(result)

        self.assertEqual("failed", artifact["status"])
        self.assertIn("something nobody anticipated", artifact["reason"])

    def test_unusable_report_date_is_failed(self) -> None:
        result = dev_activity.collect(self.section(), "yesterday", self.config())
        artifact = self.artifact(result)

        self.assertEqual("failed", artifact["status"])
        self.assertIn("not an ISO", artifact["reason"])


class PartialDataTests(CollectorTestCase):
    def test_unreadable_heatmap_degrades_to_partial_with_events_fallback(self) -> None:
        store = FakeCandystore(
            [event(time="2026-08-17T15:30:00Z"), event(time="2026-08-17T15:31:00Z")],
            fail={"heatmap"},
        )
        result = self.collect(store, self.section(), self.config())
        artifact = self.artifact(result)

        self.assertEqual("partial", artifact["status"])
        self.assertIn("heatmap unavailable", artifact["reason"])
        self.assertEqual("2026-08-17T15:00:00Z", artifact["metrics"]["peak_hour"])
        self.assertFalse(artifact["metrics"]["heatmap_read"])

    def test_failing_git_log_degrades_to_partial(self) -> None:
        broken = self.root / "code" / "widget"
        broken.mkdir(parents=True)
        (broken / ".git").write_text("this is not a git directory", encoding="utf-8")

        store = FakeCandystore(
            [event(project="widget")], heatmap([("2026-08-17T15:00:00Z", "w", 1)])
        )
        result = self.collect(store, self.section(), self.config([broken]))
        artifact = self.artifact(result)

        self.assertEqual("partial", artifact["status"])
        self.assertIn("git log failed", artifact["reason"])
        self.assertIn("widget", artifact["reason"])
        self.assertEqual(1, artifact["metrics"]["git_repos_failed"])

    def test_missing_project_root_degrades_to_partial(self) -> None:
        """An absent path and a path that is not a repository read differently."""
        not_a_repo = self.root / "code" / "gadget"
        not_a_repo.mkdir(parents=True)
        store = FakeCandystore([event(project="widget")], heatmap([]))
        result = self.collect(
            store, self.section(), self.config([self.root / "code" / "widget", not_a_repo])
        )
        artifact = self.artifact(result)

        self.assertEqual("partial", artifact["status"])
        self.assertIn("could not be read as a git repository", artifact["reason"])
        self.assertIn("project root does not exist", artifact["reason"])
        self.assertIn("no .git", artifact["reason"])
        self.assertEqual(2, artifact["metrics"]["git_repos_missing"])

    def test_no_project_roots_degrades_to_partial(self) -> None:
        config = self.config()
        config["project_roots"] = []
        store = FakeCandystore([event()], heatmap([]))
        result = self.collect(store, self.section(), config)
        artifact = self.artifact(result)

        self.assertEqual("partial", artifact["status"])
        self.assertIn("no project_roots configured", artifact["reason"])

    def test_pagination_budget_exhaustion_degrades_to_partial(self) -> None:
        store = FakeCandystore(
            [event(correlationid=f"c{index}") for index in range(6)], heatmap([])
        )
        section = self.section(page_size=2, max_pages=2)
        result = self.collect(store, section, self.config())
        artifact = self.artifact(result)

        self.assertEqual("partial", artifact["status"])
        self.assertIn("page budget", artifact["reason"].replace("-page budget", " page budget"))
        self.assertEqual(4, artifact["metrics"]["event_count"])

    def test_unconfigured_active_projects_are_named(self) -> None:
        repo = make_repo(self.root / "code" / "widget", ["feat: widget"])
        store = FakeCandystore(
            [event(project="widget"), event(project="gadget"), event(project="gadget.git")],
            heatmap([]),
        )
        result = self.collect(store, self.section(), self.config([repo]))
        artifact = self.artifact(result)

        caveats = " ".join(artifact["caveats"])
        self.assertIn("have no configured project root", caveats)
        self.assertIn("gadget", caveats)
        self.assertEqual(1, artifact["metrics"]["projects_without_root"])


class ConfiguredCoverageTests(CollectorTestCase):
    """Coverage is the CONFIGURED roots, never the roots the day's events name.

    The collector's own docstring promises that ``complete`` means every source
    named here was read in full. Before this class existed, a configured root
    whose basename never appeared in a Candystore ``project`` field was dropped
    from the git sweep with no caveat and no metric -- on 2026-08-15 that hid 25
    of 39 commits under a ``complete``.
    """

    def test_configured_root_absent_from_events_is_still_logged(self) -> None:
        seen = make_repo(self.root / "code" / "widget", ["feat: the widget"])
        unseen = make_repo(
            self.root / "code" / "gadget", ["fix: the gadget", "chore: gadget again"]
        )
        store = FakeCandystore([event(project="widget")], heatmap([]))

        result = self.collect(store, self.section(), self.config([seen, unseen]))
        artifact = self.artifact(result)
        detail = "\n".join(artifact["detail"])

        self.assertIn("fix: the gadget", detail)
        self.assertIn("chore: gadget again", detail)
        self.assertEqual(3, artifact["metrics"]["git_commit_count"])
        self.assertEqual(2, artifact["metrics"]["git_roots_configured"])
        self.assertEqual(2, artifact["metrics"]["git_repos_logged"])
        self.assertEqual("complete", artifact["status"])

    def test_unreadable_root_absent_from_events_still_degrades_the_status(self) -> None:
        """The dropped root was also a dropped failure. Both come back."""
        seen = make_repo(self.root / "code" / "widget", ["feat: the widget"])
        store = FakeCandystore([event(project="widget")], heatmap([]))

        result = self.collect(
            store, self.section(), self.config([seen, self.root / "code" / "vanished"])
        )
        artifact = self.artifact(result)

        self.assertEqual("partial", artifact["status"])
        self.assertIn("vanished", artifact["reason"])
        self.assertEqual(1, artifact["metrics"]["git_repos_missing"])
        self.assertEqual(2, artifact["metrics"]["git_roots_configured"])

    def test_root_with_no_commits_is_recorded_as_read_not_omitted(self) -> None:
        busy = make_repo(self.root / "code" / "widget", ["feat: the widget"])
        quiet = make_repo(
            self.root / "code" / "quiet", ["ancient work"], when="2026-01-02T12:00:00Z"
        )
        store = FakeCandystore([event(project="widget")], heatmap([]))

        result = self.collect(store, self.section(), self.config([busy, quiet]))
        artifact = self.artifact(result)

        self.assertEqual("complete", artifact["status"])
        self.assertEqual(1, artifact["metrics"]["git_repos_no_commits"])
        self.assertEqual(2, artifact["metrics"]["git_roots_configured"])
        self.assertTrue(
            any("no commits" in item and "quiet" in item for item in artifact["caveats"]),
            artifact["caveats"],
        )
        self.assertIn("=== quiet ===", "\n".join(artifact["detail"]))

    def test_every_configured_root_lands_in_exactly_one_outcome_bucket(self) -> None:
        logged = make_repo(self.root / "code" / "widget", ["feat: the widget"])
        quiet = make_repo(
            self.root / "code" / "quiet", ["ancient work"], when="2026-01-02T12:00:00Z"
        )
        broken = self.root / "code" / "broken"
        broken.mkdir(parents=True)
        (broken / ".git").write_text("not a git directory", encoding="utf-8")
        gone = self.root / "code" / "vanished"

        store = FakeCandystore([event(project="widget")], heatmap([]))
        result = self.collect(store, self.section(), self.config([logged, quiet, broken, gone]))
        metrics = self.artifact(result)["metrics"]

        self.assertEqual(4, metrics["git_roots_configured"])
        self.assertEqual(
            metrics["git_roots_configured"],
            metrics["git_repos_logged"]
            + metrics["git_repos_no_commits"]
            + metrics["git_repos_failed"]
            + metrics["git_repos_missing"],
        )

    def test_basename_collision_keeps_both_roots_and_says_so(self) -> None:
        first = make_repo(self.root / "a" / "twin", ["feat: first twin"])
        second = make_repo(self.root / "b" / "twin", ["feat: second twin"])
        store = FakeCandystore([event(project="twin")], heatmap([]))

        result = self.collect(store, self.section(), self.config([first, second]))
        artifact = self.artifact(result)
        detail = "\n".join(artifact["detail"])

        self.assertIn("feat: first twin", detail)
        self.assertIn("feat: second twin", detail)
        self.assertEqual(2, artifact["metrics"]["git_commit_count"])
        self.assertEqual(2, artifact["metrics"]["git_roots_configured"])
        self.assertEqual(1, artifact["metrics"]["git_root_name_collisions"])
        caveats = " ".join(artifact["caveats"])
        self.assertIn("twin", caveats)
        self.assertIn(str(first), caveats)
        self.assertIn(str(second), caveats)

    def test_collision_resolution_never_silently_drops_a_root(self) -> None:
        """The old dict.setdefault kept the first root and forgot the second."""
        plan = dev_activity.resolve_project_dirs(
            [{"project": "candystore"}],
            ["/home/one/candystore", "/home/two/candystore"],
        )
        self.assertEqual(2, len(plan.selected))
        self.assertEqual(1, len(plan.collisions))
        self.assertEqual(
            {"/home/one/candystore", "/home/two/candystore"},
            {str(path) for _, path in plan.selected},
        )

    def test_duplicate_root_paths_are_deduped_out_loud(self) -> None:
        repo = make_repo(self.root / "code" / "widget", ["feat: the widget"])
        store = FakeCandystore([event(project="widget")], heatmap([]))

        result = self.collect(store, self.section(), self.config([repo, Path(f"{repo}/.")]))
        artifact = self.artifact(result)

        self.assertEqual(1, artifact["metrics"]["git_commit_count"])
        self.assertEqual(1, artifact["metrics"]["git_roots_duplicated"])
        self.assertTrue(
            any("logged once, not twice" in item for item in artifact["caveats"]),
            artifact["caveats"],
        )

    def test_unusable_root_entries_are_reported_not_skipped(self) -> None:
        repo = make_repo(self.root / "code" / "widget", ["feat: the widget"])
        config = self.config([repo])
        config["project_roots"] = [str(repo), 17, "   "]
        store = FakeCandystore([event(project="widget")], heatmap([]))

        result = self.collect(store, self.section(), config)
        artifact = self.artifact(result)

        self.assertEqual("partial", artifact["status"])
        self.assertIn("not usable paths", artifact["reason"])
        self.assertEqual(2, artifact["metrics"]["git_roots_unusable"])

    def test_summary_states_the_configured_denominator(self) -> None:
        seen = make_repo(self.root / "code" / "widget", ["feat: the widget"])
        unseen = make_repo(self.root / "code" / "gadget", ["fix: the gadget"])
        store = FakeCandystore([event(project="widget")], heatmap([]))

        result = self.collect(store, self.section(), self.config([seen, unseen]))
        artifact = self.artifact(result)

        self.assertIn("2 commit(s)", artifact["summary"])
        self.assertIn("2 configured repository(ies)", artifact["summary"])


class TruncationTests(CollectorTestCase):
    def test_decision_truncation_states_both_numbers(self) -> None:
        decisions = [
            event(
                "bloodbank.v1.repo.decision.recorded",
                data={"issue": f"WID-{index}", "repo": "widget", "title": f"Decision {index}"},
            )
            for index in range(43)
        ]
        store = FakeCandystore(decisions, heatmap([]))
        result = self.collect(store, self.section(), self.config())
        artifact = self.artifact(result)

        self.assertIn("decisions truncated: showing 30 of 43", artifact["caveats"])
        self.assertIn("  ... showing 30 of 43 decisions", artifact["detail"])
        self.assertEqual(43, artifact["metrics"]["decision_count"])

    def test_operational_note_truncation_states_both_numbers(self) -> None:
        notes = [
            event("bloodbank.v1.system.process.exited", data={"error": f"exit {index}"})
            for index in range(25)
        ]
        store = FakeCandystore(notes, heatmap([]))
        result = self.collect(store, self.section(), self.config())
        artifact = self.artifact(result)

        self.assertIn("operational events truncated: showing 20 of 25", artifact["caveats"])

    def test_commit_session_truncation_states_both_numbers(self) -> None:
        sessions = [
            event(
                "bloodbank.v1.agent.session.ended",
                correlationid=f"c{index}",
                data={"git_commits": ["abc"], "total_turns": index},
            )
            for index in range(31)
        ]
        store = FakeCandystore(sessions, heatmap([]))
        result = self.collect(store, self.section(), self.config())
        artifact = self.artifact(result)

        self.assertIn("committing sessions truncated: showing 30 of 31", artifact["caveats"])

    def test_detail_line_cap_is_recorded(self) -> None:
        store = FakeCandystore(
            [event(project=f"p{index}", correlationid=f"c{index}") for index in range(40)],
            heatmap([]),
        )
        result = self.collect(store, self.section(max_detail_lines=5), self.config())
        artifact = self.artifact(result)

        self.assertEqual(5, len(artifact["detail"]))
        self.assertTrue(
            any("detail truncated: showing 5 of" in item for item in artifact["caveats"])
        )


class AllowlistTests(CollectorTestCase):
    def test_raw_event_payload_never_reaches_the_artifact(self) -> None:
        """Only named keys survive; a tool payload cannot ride along."""
        secret = "unlisted-payload-marker-do-not-emit"
        store = FakeCandystore(
            [
                event(
                    data={
                        "arguments": {"command": f"export TOKEN={secret}"},
                        "working_directory": f"/home/{secret}",
                        "tool_name": "Bash",
                    }
                )
            ],
            heatmap([]),
        )
        result = self.collect(store, self.section(), self.config())
        artifact = self.artifact(result)

        self.assertNotIn(secret, json.dumps(artifact))
        self.assertNotIn("working_directory", json.dumps(artifact))

    def test_non_scalar_metrics_cannot_smuggle_structure(self) -> None:
        result = dev_activity._allowlisted(
            dev_activity.SectionResult(
                id="dev-activity",
                summary="x",
                metrics={"ok": 1, "nested": {"secret": "value"}},
            )
        )
        self.assertEqual({"ok": 1}, result.metrics)


class PeakHourTests(unittest.TestCase):
    def test_heatmap_peak_sums_project_buckets_instead_of_taking_the_first(self) -> None:
        """The journal read buckets[0] -- the newest hour's first project."""
        buckets = heatmap(
            [
                ("2026-08-17T23:00:00Z", "pjangler", 326),
                ("2026-08-17T23:00:00Z", "deckard", 150),
                ("2026-08-17T15:00:00Z", "pjangler", 400),
                ("2026-08-17T15:00:00Z", "deckard", 400),
            ]
        )
        peak = dev_activity.peak_hour_from_heatmap(buckets)
        self.assertEqual(dev_activity.PeakHour("2026-08-17T15:00:00Z", 800), peak)

    def test_events_fallback_when_heatmap_has_no_buckets(self) -> None:
        self.assertIsNone(dev_activity.peak_hour_from_heatmap({"buckets": []}))
        peak = dev_activity.build_heatmap_peak(
            [event(time="2026-08-17T09:05:00Z"), event(time="2026-08-17T09:45:00Z")]
        )
        self.assertEqual(dev_activity.PeakHour("2026-08-17T09:00:00Z", 2), peak)

    def test_no_timestamps_yields_no_peak(self) -> None:
        self.assertIsNone(dev_activity.build_heatmap_peak([]))


class CallStyleTests(CollectorTestCase):
    def test_keyword_call_style_used_by_reportctl_is_accepted(self) -> None:
        store = FakeCandystore([event()], heatmap([]))
        with mock.patch.object(dev_activity, "fetch_json", store):
            result = dev_activity.collect(self.section(), date=DATE, config=self.config())
        self.assertEqual("dev-activity", result.id)
        self.assertIn(result.status, {"complete", "partial"})

    def test_missing_report_date_is_failed_not_a_type_error(self) -> None:
        result = dev_activity.collect(self.section())
        self.assertEqual("failed", result.status)
        self.assertIn("without a report date", result.reason)


class StandaloneCliTests(CollectorTestCase):
    def test_cli_prints_an_artifact_and_exits_non_zero_when_the_source_is_dead(self) -> None:
        config = base_config(self.root)
        config["sections"][0]["options"] = {
            "candystore_url": "http://127.0.0.1:9",
            "http_timeout_seconds": 2,
        }
        config_path = self.root / "report.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        environment = {**os.environ}
        environment.pop("CANDYSTORE_URL", None)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "collectors.dev_activity",
                "--date",
                DATE,
                "--config",
                str(config_path),
                "--run-id",
                "run-cli",
            ],
            cwd=SCRIPTS,
            env=environment,
            capture_output=True,
            text=True,
            timeout=120,
        )

        self.assertEqual(1, completed.returncode, completed.stderr)
        artifact = validate_section_artifact(json.loads(completed.stdout), "dev-activity")
        self.assertEqual("failed", artifact["status"])
        self.assertEqual("run-cli", artifact["run_id"])


class EventNameEraTests(CollectorTestCase):
    """Both spellings of an event name must count as the same fact.

    Candystore's ``type`` column keeps two eras forever: the retired five-token
    ``bloodbank.v1.<domain>.<entity>.<action>`` on every row written before the
    version token was dropped, and the four-token name on everything published
    since. Nothing rewrites history, and nothing back-fills the new shape.

    This collector matched the ``v1`` spelling only, so it went quietly blind
    the day publishers stopped using it -- a day with seven version-free
    session-end events and zero ``v1`` ones rendered as a day with no sessions
    and no commits. Every other test in this file feeds the ``v1`` shape and so
    pins the other direction: dropping the old spelling would erase the archive.
    """

    def test_the_version_free_shape_is_counted(self) -> None:
        store = FakeCandystore(
            [
                event(
                    "bloodbank.repo.decision.recorded",
                    correlationid="corr-1",
                    data={"issue": "WID-9", "repo": "widget", "title": "Ship it"},
                ),
                event(
                    "bloodbank.agent.session.ended",
                    correlationid="corr-2",
                    data={"git_commits": ["abc123"], "total_turns": 4},
                ),
                event("bloodbank.system.process.exited", data={"error": "exit 1"}),
            ],
            heatmap([]),
        )
        artifact = self.artifact(self.collect(store, self.section(), self.config()))

        self.assertEqual(1, artifact["metrics"]["decision_count"])
        self.assertEqual(1, artifact["metrics"]["commit_count"])
        detail = "\n".join(artifact["detail"])
        self.assertIn("[widget] WID-9: Ship it", detail)
        self.assertIn("[widget] exited: exit 1", detail)

    def test_the_two_eras_of_one_name_add_up(self) -> None:
        """A window spanning the migration reads as one continuous history."""
        store = FakeCandystore(
            [
                event(
                    "bloodbank.v1.agent.session.ended",
                    correlationid="corr-old",
                    data={"git_commits": ["abc123"], "total_turns": 4},
                ),
                event(
                    "bloodbank.agent.session.ended",
                    correlationid="corr-new",
                    data={"git_commits": ["def456"], "total_turns": 6},
                ),
            ],
            heatmap([]),
        )
        artifact = self.artifact(self.collect(store, self.section(), self.config()))

        self.assertEqual(2, artifact["metrics"]["commit_count"])

    def test_a_non_string_type_matches_nothing(self) -> None:
        self.assertEqual("", dev_activity.canonical_type(None))
        self.assertEqual("", dev_activity.canonical_type({"type": "nope"}))


if __name__ == "__main__":
    unittest.main()
