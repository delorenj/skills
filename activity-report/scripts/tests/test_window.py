"""Window resolution against a mocked previous report."""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import window as window_mod  # noqa: E402
from ar.common import ConfigError, NothingToDo, SourceUnavailable  # noqa: E402
from ar.config import DEFAULTS, Project, deep_merge  # noqa: E402

NOW = datetime(2026, 9, 3, 7, 0, 0, tzinfo=timezone.utc)
PREV_ID = "0f6d4b2c-9a1e-4c3d-8b7a-2e5f1c9d0a11"


def project(cap_hours=24, min_minutes=60):
    config = deep_merge(DEFAULTS, {"window": {"cap_hours": cap_hours, "min_minutes": min_minutes}})
    return Project(slug="james-brennan", name="James Brennan", identifier="JIMB", workspace="automaticai",
                   board_id=None, provider_type="plane", repo_path="/tmp/x", extra_repo_paths=[], config=config,
                   tz="America/New_York", project_json_path="/tmp/x/.project.json")


def previous(end: datetime):
    return {"event_id": PREV_ID, "window_end": end.strftime("%Y-%m-%dT%H:%M:%SZ"), "title": "Yesterday", "raw": "body"}


class WindowTests(unittest.TestCase):
    def resolve(self, prev, **kw):
        with mock.patch.object(window_mod.candystore, "find_previous_report", return_value=prev) as finder:
            w = window_mod.resolve(project(**{k: kw.pop(k) for k in ("cap_hours", "min_minutes") if k in kw}),
                                   kw.pop("audience", "internal"), now=NOW, **kw)
            self.assertEqual(finder.call_args.args[:2], ("james-brennan", "internal"))
        return w

    def test_no_previous_is_the_24h_cap(self):
        w = self.resolve(None)
        self.assertEqual(w.basis, "cap_24h")
        self.assertEqual(w.duration_seconds, 86400)
        self.assertEqual(w.start, NOW - timedelta(hours=24))
        self.assertEqual(w.end, NOW)
        self.assertIsNone(w.previous_event_id)
        self.assertIsNone(w.previous)
        self.assertTrue(any("no previous internal report" in c for c in w.caveats))

    def test_previous_inside_the_cap_chains(self):
        prev_end = NOW - timedelta(hours=20)
        w = self.resolve(previous(prev_end))
        self.assertEqual(w.basis, "previous_report")
        self.assertEqual(w.start, prev_end)
        self.assertEqual(w.previous_event_id, PREV_ID)
        self.assertEqual(w.duration_seconds, 20 * 3600)
        self.assertEqual(w.caveats, [])

    def test_previous_older_than_the_cap_falls_back_with_a_caveat(self):
        w = self.resolve(previous(NOW - timedelta(hours=30)))
        self.assertEqual(w.basis, "cap_24h")
        self.assertEqual(w.duration_seconds, 86400)
        self.assertIsNone(w.previous_event_id)
        self.assertIsNotNone(w.previous)   # the digest still shows the previous report
        self.assertTrue(any("older than the 24 h cap" in c for c in w.caveats))

    def test_previous_in_the_future_is_clamped(self):
        with self.assertRaises(NothingToDo):
            self.resolve(previous(NOW + timedelta(hours=1)))
        w = self.resolve(previous(NOW + timedelta(hours=1)), force=True)
        self.assertEqual(w.basis, "previous_report")
        self.assertEqual(w.duration_seconds, 1)
        self.assertTrue(any("clamped" in c for c in w.caveats))

    def test_explicit_since_and_until(self):
        w = self.resolve(previous(NOW - timedelta(hours=5)), since="2026-09-01T03:00:00-04:00",
                         until="2026-09-02T03:00:00-04:00")
        self.assertEqual(w.basis, "explicit")
        self.assertEqual(w.start, datetime(2026, 9, 1, 7, tzinfo=timezone.utc))
        self.assertEqual(w.end, datetime(2026, 9, 2, 7, tzinfo=timezone.utc))
        self.assertEqual(w.previous_event_id, PREV_ID)
        self.assertEqual(w.label("America/New_York"), "2026-09-02T0300")

    def test_explicit_since_without_previous_has_no_previous_id(self):
        w = self.resolve(None, since="2026-09-02T00:00:00Z")
        self.assertEqual(w.basis, "explicit")
        self.assertEqual(w.end, NOW)
        self.assertIsNone(w.previous_event_id)

    def test_until_only_chains_from_previous_when_inside_the_cap(self):
        prev_end = NOW - timedelta(hours=10)
        w = self.resolve(previous(prev_end), until=(NOW - timedelta(hours=2)).isoformat())
        self.assertEqual(w.basis, "explicit")
        self.assertEqual(w.start, prev_end)
        self.assertEqual(w.previous_event_id, PREV_ID)

    def test_short_window_is_nothing_to_do_unless_forced(self):
        with self.assertRaises(NothingToDo):
            self.resolve(previous(NOW - timedelta(minutes=30)))
        w = self.resolve(previous(NOW - timedelta(minutes=30)), force=True)
        self.assertEqual(w.duration_seconds, 1800)
        self.assertTrue(any("forced" in c for c in w.caveats))

    def test_end_not_after_start_is_a_config_error(self):
        with self.assertRaises(ConfigError):
            self.resolve(None, since="2026-09-03T08:00:00Z", until="2026-09-03T07:00:00Z")
        with self.assertRaises(ConfigError):
            self.resolve(None, since="yesterday")

    def test_non_24h_cap_is_recorded_as_explicit(self):
        w = self.resolve(None, cap_hours=12)
        self.assertEqual(w.basis, "explicit")
        self.assertEqual(w.duration_seconds, 12 * 3600)
        self.assertTrue(any("cap_24h means exactly 24 h" in c for c in w.caveats))

    def test_as_dict_is_the_digest_window_block(self):
        w = self.resolve(previous(NOW - timedelta(hours=24)))
        self.assertEqual(w.as_dict(), {
            "start": "2026-09-02T07:00:00Z", "end": "2026-09-03T07:00:00Z", "duration_seconds": 86400,
            "basis": "previous_report", "previous_event_id": PREV_ID,
        })

    def test_candystore_down_propagates(self):
        with mock.patch.object(window_mod.candystore, "find_previous_report", side_effect=SourceUnavailable("down")):
            with self.assertRaises(SourceUnavailable):
                window_mod.resolve(project(), "internal", now=NOW)

    def test_bad_audience(self):
        with self.assertRaises(ConfigError):
            window_mod.resolve(project(), "client", now=NOW)

    def test_window_cmd_json(self):
        args = mock.Mock(project="james-brennan", audience="external", since=None, until=None, force=False, json=True)
        with mock.patch.object(window_mod, "load_project", return_value=project()), \
                mock.patch.object(window_mod.candystore, "find_previous_report", return_value=previous(NOW - timedelta(hours=24))), \
                mock.patch.object(window_mod, "utc_now", return_value=NOW), \
                mock.patch("sys.stdout") as out:
            self.assertEqual(window_mod.window_cmd(args), 0)
        text = "".join(call.args[0] for call in out.write.call_args_list)
        self.assertIn('"basis": "previous_report"', text)
        self.assertIn('"label": "2026-09-03T0300"', text)


if __name__ == "__main__":
    unittest.main()
