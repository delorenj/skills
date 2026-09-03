import contextlib
import io
import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import verify  # noqa: E402
from ar.common import AcceptanceError, SourceUnavailable  # noqa: E402

RUN = "4c1f2e8a-3b5d-4e6f-9a7b-1c2d3e4f5a6b"


def event(eid, audience, run_id=RUN, dry_run=False):
    return {"id": eid, "type": "bloodbank.project.activity.recorded", "time": "2026-09-03T07:10:00Z",
            "data": {"audience": audience, "generator": {"run_id": run_id, "dry_run": dry_run}}}


class Url(unittest.TestCase):
    def test_query(self):
        url = verify.events_url()
        self.assertTrue(url.startswith(verify.CANDYSTORE_URL.rstrip("/") + "/events?"))
        self.assertIn("type=bloodbank.project.activity.recorded", url)
        self.assertIn("from=", url)
        self.assertIn("limit=50", url)


class Verify(unittest.TestCase):
    def test_found_first_poll(self):
        with mock.patch.object(verify, "fetch_events", return_value=[event("e1", "internal"), event("e2", "internal", run_id="other")]):
            result = verify.verify(RUN, timeout_seconds=5)
        self.assertEqual([f["id"] for f in result["found"]], ["e1"])
        self.assertEqual(result["polls"], 1)

    def test_audience_filter_and_expect(self):
        events = [event("e1", "internal"), event("e2", "external")]
        with mock.patch.object(verify, "fetch_events", return_value=events):
            self.assertEqual([f["id"] for f in verify.verify(RUN, 5, audience="external")["found"]], ["e2"])
            self.assertEqual(len(verify.verify(RUN, 5, expect=2)["found"]), 2)

    def test_polls_until_found(self):
        answers = [[], [], [event("e1", "internal")]]
        with mock.patch.object(verify, "fetch_events", side_effect=answers), mock.patch.object(verify, "POLL_SECONDS", 0.01):
            result = verify.verify(RUN, timeout_seconds=5)
        self.assertEqual(result["polls"], 3)

    def test_timeout_is_acceptance(self):
        with mock.patch.object(verify, "fetch_events", return_value=[]):
            with self.assertRaises(AcceptanceError):
                verify.verify(RUN, timeout_seconds=0)

    def test_unreachable_is_source_unavailable(self):
        with mock.patch.object(verify, "fetch_events", side_effect=OSError("refused")):
            with self.assertRaises(SourceUnavailable):
                verify.verify(RUN, timeout_seconds=0)

    def test_payload_shapes(self):
        payloads = [{"events": [event("e1", "internal")], "total": 1}, [event("e1", "internal")]]
        for payload in payloads:
            fake = io.BytesIO(__import__("json").dumps(payload).encode())
            with mock.patch("urllib.request.urlopen") as urlopen:
                urlopen.return_value.__enter__.return_value = fake
                self.assertEqual(verify.fetch_events()[0]["id"], "e1")


class VerifyCmd(unittest.TestCase):
    def test_prints(self):
        args = types.SimpleNamespace(run_id=RUN, timeout_seconds=5, audience="internal", expect=1, json=False, project=None)
        buf = io.StringIO()
        with mock.patch.object(verify, "fetch_events", return_value=[event("e1", "internal", dry_run=True)]), contextlib.redirect_stdout(buf):
            self.assertEqual(verify.verify_cmd(args), 0)
        self.assertIn("verified: event e1 (internal", buf.getvalue())
        self.assertIn("dry_run=True", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
