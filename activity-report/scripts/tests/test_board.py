"""Plane enrichment with the API mocked on captured response shapes."""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import board, candystore  # noqa: E402
from ar.common import ConfigError, parse_iso  # noqa: E402
from ar.config import DEFAULTS, Project, deep_merge  # noqa: E402
from ar.window import Window  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "collect")
BOARD_ID = "a8a12be1-b3ab-44f4-ab24-abe8829aeb72"
INT_ID = "11111111-2222-4333-8444-555555555555"
NEW_ID = "99999999-8888-4777-8666-555555555555"


def fixture(name: str):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


LABELS = fixture("plane_labels.json")["results"]
STATES = fixture("plane_states.json")["results"]
ISSUE = fixture("plane_issue.json")
EXT_ID = next(l["id"] for l in LABELS if l["name"] == "xp:external")
CREATED = fixture("task_created.json")
UPDATED = fixture("task_updated_state.json")
APPENDED = fixture("task_appended.json")
ID_251 = CREATED["data"]["ticket_id"]
ID_169 = UPDATED["data"]["ticket_id"]


def window() -> Window:
    return Window(start=parse_iso("2026-09-02T00:00:00Z"), end=parse_iso("2026-09-03T00:00:00Z"), basis="explicit",
                  previous_event_id=None, previous=None, caveats=[])


def project(**over) -> Project:
    config = deep_merge(DEFAULTS, over.pop("config", {}))
    fields = dict(slug="james-brennan", name="James Brennan", identifier="JIMB", workspace="automaticai", board_id=BOARD_ID,
                  provider_type="plane", repo_path="/tmp/james-brennan", extra_repo_paths=[], config=config,
                  tz="America/New_York", project_json_path="/tmp/james-brennan/.project.json")
    fields.update(over)
    return Project(**fields)


def stamped(event: dict, time: str) -> dict:
    e = copy.deepcopy(event)
    e["time"] = time
    return e


def records(events=None) -> list[dict]:
    events = events if events is not None else [stamped(CREATED, "2026-09-02T12:00:00.000000Z"),
                                                stamped(UPDATED, "2026-09-02T10:00:00.000000Z")]
    newest_first = sorted(events, key=lambda e: e["time"], reverse=True)
    fake = lambda url, timeout=30: {"events": newest_first, "total": len(events), "limit": 1000, "offset": 0}  # noqa: E731
    with mock.patch.object(candystore, "fetch_json", fake):
        return candystore.collect_tickets("james-brennan", window(), identifier="JIMB")


def issue(issue_id: str, sequence: int, name: str, labels: list[str], html: str = "<p>Hello &amp; <b>world</b></p>") -> dict:
    return {**ISSUE, "id": issue_id, "sequence_id": sequence, "name": name, "labels": labels, "description_html": html}


class FakePlane:
    """Routes PlaneApi.request by path; remembers every call."""

    def __init__(self, labels=None, states=None, issues=None, fail: tuple | None = None):
        self.labels = copy.deepcopy(labels if labels is not None else LABELS)
        self.states = copy.deepcopy(states if states is not None else STATES)
        self.issues = issues or {}
        self.fail = fail          # (path prefix, http status)
        self.calls: list[tuple] = []

    def request(self, api, method, path, params=None, body=None):
        self.calls.append((method, path, params, body))
        if self.fail and path.startswith(self.fail[0]):
            raise board.BoardUnavailable(f"Plane {method} {path}: HTTP {self.fail[1]}", self.fail[1])
        if method == "POST" and path == "labels":
            made = {"id": NEW_ID, "name": body["name"], "color": body["color"], "description": body["description"]}
            self.labels.append(made)
            return made
        if path == "labels":
            return {"results": list(self.labels), "next_page_results": False, "next_cursor": None}
        if path == "states":
            return {"results": list(self.states), "next_page_results": False, "next_cursor": None}
        if path.startswith("issues/"):
            found = self.issues.get(path.split("/", 1)[1])
            if found is None:
                raise board.BoardUnavailable("Plane GET issue: HTTP 404 not found", 404)
            if isinstance(found, int):
                raise board.BoardUnavailable(f"Plane GET issue: HTTP {found}", found)
            return found
        raise AssertionError(f"unexpected request {method} {path}")

    def issue_calls(self):
        return [c[1] for c in self.calls if c[1].startswith("issues/")]


class BoardCase(unittest.TestCase):
    def setUp(self):
        self.cache = tempfile.mkdtemp(prefix="ar-board-")
        self.env = mock.patch.dict(os.environ, {"XDG_CACHE_HOME": self.cache})
        self.env.start()
        self.key = mock.patch.object(board, "resolve_api_key", return_value=("test-key-value", "env PLANE_API_KEY", []))
        self.key.start()

    def tearDown(self):
        self.key.stop()
        self.env.stop()
        shutil.rmtree(self.cache, ignore_errors=True)

    def enrich(self, fake: FakePlane, audience="internal", recs=None, **over):
        with mock.patch.object(board.PlaneApi, "request", lambda api, method, path, params=None, body=None:
                               fake.request(api, method, path, params, body)):
            return board.enrich(project(**over), recs if recs is not None else records(), window(), audience)

    def cache_files(self):
        out = {}
        for dirpath, _dirs, files in os.walk(self.cache):
            for name in files:
                with open(os.path.join(dirpath, name), encoding="utf-8") as fh:
                    out[os.path.relpath(os.path.join(dirpath, name), self.cache)] = fh.read()
        return out


class EnrichTests(BoardCase):
    def fake(self, **kw):
        issues = {ID_251: issue(ID_251, 251, "Client-facing win", [EXT_ID]),
                  ID_169: issue(ID_169, 169, "Prod incident follow-up", [])}
        return FakePlane(issues=issues, **kw)

    def test_internal_digest_reads_live_labels(self):
        fake = self.fake()
        block, lint = self.enrich(fake)
        self.assertIsNone(lint)
        self.assertEqual((block["status"], block["labels_resolved"]), ("ok", True))
        self.assertEqual(block["exposure_labels"], {"external": "xp:external", "internal": "xp:internal"})
        self.assertEqual([t["key"] for t in block["tickets"]], ["JIMB-251", "JIMB-169"])   # newest last_seen first
        t251, t169 = block["tickets"]
        self.assertEqual((t251["title"], t251["labels"], t251["exposure"], t251["surface"]),
                         ("Client-facing win", ["xp:external"], "external", None))
        self.assertEqual(t251["description_excerpt"], "Hello & world")
        self.assertEqual(t251["url"], f"https://plane.delo.sh/automaticai/projects/{BOARD_ID}/issues/{ID_251}")
        self.assertEqual((t251["from_state"], t251["to_state"], t251["event_kinds"]), (None, "Todo", ["created"]))
        self.assertEqual((t169["from_state"], t169["to_state"], t169["exposure"]), ("Todo", "In Progress", "unlabeled"))
        self.assertEqual(t169["event_kinds"], ["updated"])
        self.assertEqual((block["opened"], block["closed"], block["started"], block["commented"]),
                         (["JIMB-251"], [], ["JIMB-169"], []))
        self.assertEqual(fake.issue_calls(), [f"issues/{ID_251}", f"issues/{ID_169}"])
        self.assertTrue(any("xp:internal do not exist on the board" in c for c in block["caveats"]))
        self.assertFalse(any("snapshot" in c for c in block["caveats"]))

    def test_external_digest_denies_internal_and_surfaces_external(self):
        fake = self.fake(labels=LABELS + [{"id": INT_ID, "name": "xp:internal", "color": "#586a7a"}])
        fake.issues[ID_169]["labels"] = [INT_ID, EXT_ID]        # both labels: internal wins
        block, lint = self.enrich(fake, audience="external")
        self.assertEqual([t["key"] for t in block["tickets"]], ["JIMB-251"])
        self.assertEqual(block["tickets"][0]["surface"], "always")
        self.assertEqual(block["tickets"][0]["description_excerpt"], "Hello & world")
        self.assertEqual(lint["identifiers"], ["JIMB"])
        self.assertEqual(lint["denied_titles"], ["Prod incident follow-up"])
        self.assertEqual(lint["surface_always"], [{"key": "JIMB-251", "title": "Client-facing win"}])
        self.assertEqual((block["started"], block["opened"]), ([], ["JIMB-251"]))    # a denied ticket is not flagged either
        self.assertEqual(block["caveats"], [])

    def test_external_unlabeled_is_judgment_without_excerpt(self):
        fake = self.fake()
        block, lint = self.enrich(fake, audience="external")
        t169 = next(t for t in block["tickets"] if t["key"] == "JIMB-169")
        self.assertEqual((t169["exposure"], t169["surface"], t169["description_excerpt"]), ("unlabeled", "judgment", None))
        self.assertEqual(lint["denied_titles"], [])

    def test_no_key_internal_marks_unlabeled_external_withholds(self):
        self.key.stop()
        try:
            with mock.patch.object(board, "resolve_api_key", return_value=(None, "none", ["env PLANE_API_KEY (unset)"])):
                fake = self.fake()
                block, _ = self.enrich(fake)
                self.assertEqual(block["status"], "unavailable")
                self.assertFalse(block["labels_resolved"])
                self.assertEqual([t["exposure"] for t in block["tickets"]], ["unlabeled", "unlabeled"])
                self.assertEqual(block["started"], ["JIMB-169"])
                self.assertTrue(any("Plane API key not found: env PLANE_API_KEY (unset)" in c for c in block["caveats"]))
                self.assertTrue(any("exposure is unlabeled for every ticket" in c for c in block["caveats"]))
                block, lint = self.enrich(fake, audience="external")
                self.assertEqual(block["tickets"], [])
                self.assertEqual(len(lint["denied_titles"]), 2)
                self.assertTrue(any("withheld from the external digest" in c for c in block["caveats"]))
                self.assertEqual(fake.calls, [])
        finally:
            self.key.start()

    def test_board_down_without_cache_is_unavailable(self):
        fake = self.fake(fail=("labels", 403))
        block, lint = self.enrich(fake, audience="external")
        self.assertEqual(block["status"], "unavailable")
        self.assertEqual(block["tickets"], [])
        self.assertTrue(any("HTTP 403" in c for c in block["caveats"]))
        self.assertEqual(fake.issue_calls(), [])

    def test_stale_cache_stands_in_when_the_list_fails(self):
        good = self.fake()
        self.enrich(good)
        files = self.cache_files()
        self.assertEqual(sorted(files), [os.path.join("activity-report", "plane", "automaticai", BOARD_ID, "labels.json"),
                                         os.path.join("activity-report", "plane", "automaticai", BOARD_ID, "states.json")])
        self.assertFalse(any("test-key-value" in body for body in files.values()), "a key reached the cache")
        for name in ("labels", "states"):
            path = os.path.join(self.cache, "activity-report", "plane", "automaticai", BOARD_ID, f"{name}.json")
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            data["fetched_at_epoch"] = 1.0
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
        down = self.fake(fail=("labels", 500))
        block, _ = self.enrich(down)
        self.assertEqual(block["status"], "ok")
        self.assertTrue(block["labels_resolved"])
        self.assertTrue(any("using the cached labels" in c for c in block["caveats"]))
        self.assertEqual([t["exposure"] for t in block["tickets"]], ["external", "unlabeled"])

    def test_fresh_cache_skips_the_lists(self):
        first = self.fake()
        self.enrich(first)
        second = self.fake()
        self.enrich(second)
        self.assertEqual([c[1] for c in first.calls][:2], ["labels", "states"])
        self.assertEqual([c[1] for c in second.calls], [f"issues/{ID_251}", f"issues/{ID_169}"])

    def test_live_budget_then_snapshot(self):
        fake = self.fake()
        block, _ = self.enrich(fake, config={"board": {"max_live_fetches": 1}})
        self.assertEqual(fake.issue_calls(), [f"issues/{ID_251}"])
        t251, t169 = block["tickets"]
        self.assertEqual(t251["labels"], ["xp:external"])
        self.assertEqual(t169["labels"], [])
        self.assertTrue(any("labels for 1 ticket(s) come from the event snapshot" in c for c in block["caveats"]))
        block, _ = self.enrich(self.fake(), config={"board": {"max_live_fetches": 0}})
        t251 = block["tickets"][0]
        self.assertEqual((t251["labels"], t251["exposure"]), (["xp:external"], "external"))   # snapshot labels are dicts with names

    def test_live_404_falls_back_to_the_snapshot(self):
        fake = self.fake()
        del fake.issues[ID_169]
        block, _ = self.enrich(fake)
        self.assertEqual([t["key"] for t in block["tickets"]], ["JIMB-251", "JIMB-169"])
        self.assertTrue(any("404" in c for c in block["caveats"]))

    def test_live_error_stops_further_reads(self):
        fake = self.fake()
        fake.issues[ID_251] = 500
        block, _ = self.enrich(fake)
        self.assertEqual(fake.issue_calls(), [f"issues/{ID_251}"])
        self.assertEqual(len(block["tickets"]), 2)
        self.assertTrue(any("live ticket reads stopped" in c for c in block["caveats"]))

    def test_comment_only_ticket_needs_a_live_read_for_its_key(self):
        recs = records([stamped(APPENDED, "2026-09-02T09:00:00.000000Z")])
        self.assertIsNone(recs[0]["key"])
        fake = FakePlane(issues={APPENDED["data"]["ticket_id"]: issue(APPENDED["data"]["ticket_id"], 169, "Named by the board", [])})
        block, _ = self.enrich(fake, recs=recs)
        self.assertEqual([t["key"] for t in block["tickets"]], ["JIMB-169"])
        self.assertEqual(block["commented"], ["JIMB-169"])
        self.assertEqual(block["tickets"][0]["title"], "Named by the board")
        block, _ = self.enrich(FakePlane(), recs=recs, config={"board": {"max_live_fetches": 0}})
        self.assertEqual(block["tickets"], [])
        self.assertTrue(any("no resolvable key" in c for c in block["caveats"]))

    def test_unsupported_provider(self):
        block, lint = self.enrich(FakePlane(), audience="external", provider_type="linear")
        self.assertEqual((block["status"], block["tickets"]), ("unsupported", []))
        self.assertEqual(lint["denied_titles"], [])
        self.assertTrue(any("not supported" in c for c in block["caveats"]))


class EnsureLabelsTests(BoardCase):
    def run_ensure(self, fake: FakePlane, confirm: bool, **over):
        with mock.patch.object(board.PlaneApi, "request", lambda api, method, path, params=None, body=None:
                               fake.request(api, method, path, params, body)):
            return board.ensure_labels(project(**over), confirm)

    def test_plan_creates_nothing(self):
        fake = FakePlane()
        result = self.run_ensure(fake, confirm=False)
        self.assertEqual(result["present"], [{"role": "external", "name": "xp:external", "id": EXT_ID, "color": "#0693E3"}])
        self.assertEqual(result["missing"], [{"role": "internal", "name": "xp:internal", "color": "#586a7a",
                                             "description": "Never surface to the client"}])
        self.assertEqual((result["created"], result["confirmed"], result["key_source"]), ([], False, "env PLANE_API_KEY"))
        self.assertEqual([c[0] for c in fake.calls], ["GET"])

    def test_confirm_creates_only_the_missing_label(self):
        fake = FakePlane()
        result = self.run_ensure(fake, confirm=True)
        posts = [c for c in fake.calls if c[0] == "POST"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][3], {"name": "xp:internal", "color": "#586a7a", "description": "Never surface to the client"})
        self.assertEqual(result["created"], [{"role": "internal", "name": "xp:internal", "id": NEW_ID, "color": "#586a7a"}])
        files = self.cache_files()
        self.assertTrue(any("xp:internal" in body for body in files.values()), "labels cache not refreshed")
        self.assertFalse(any("test-key-value" in body for body in files.values()))
        again = self.run_ensure(fake, confirm=True)
        self.assertEqual((again["missing"], again["created"]), ([], []))

    def test_errors_are_config_errors(self):
        with self.assertRaises(ConfigError):
            self.run_ensure(FakePlane(), confirm=False, provider_type="linear")
        with self.assertRaises(ConfigError):
            self.run_ensure(FakePlane(fail=("labels", 401)), confirm=False)
        self.key.stop()
        try:
            with mock.patch.object(board, "resolve_api_key", return_value=(None, "none", ["env PLANE_API_KEY (unset)"])):
                with self.assertRaises(ConfigError):
                    self.run_ensure(FakePlane(), confirm=False)
        finally:
            self.key.start()

    def test_cmd_prints_the_plan(self):
        fake = FakePlane()
        args = mock.Mock(project="james-brennan", confirm=False, json=False)
        with mock.patch.object(board, "load_project", return_value=project()), \
                mock.patch.object(board.PlaneApi, "request", lambda api, method, path, params=None, body=None:
                                  fake.request(api, method, path, params, body)), \
                mock.patch("sys.stdout") as out:
            self.assertEqual(board.ensure_labels_cmd(args), 0)
        text = "".join(call.args[0] for call in out.write.call_args_list)
        self.assertIn("present   xp:external", text)
        self.assertIn("missing   xp:internal", text)
        self.assertIn("1 label(s) would be created; re-run with --confirm", text)


class KeyResolutionTests(unittest.TestCase):
    """`_op_read` is always patched here: a real `op read` would print a live key into a failure message."""

    def setUp(self):
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        for name in ("PLANE_API_KEY", "PLANE_AUTOMATICAI_API_KEY", "MY_PLANE_KEY"):
            os.environ.pop(name, None)
        self.op = mock.patch.object(board, "_op_read", return_value=None)
        self.op.start()

    def tearDown(self):
        self.op.stop()
        self.env.stop()

    def test_chain(self):
        with mock.patch.object(board, "_op_read", return_value=None):
            key, source, tried = board.resolve_api_key(project())
        self.assertEqual((key, source), (None, "none"))
        self.assertEqual(tried[:2], ["env PLANE_API_KEY (unset)", "env PLANE_AUTOMATICAI_API_KEY (unset)"])
        self.assertIn("builtin ref op://DeLoSecrets/Plane/AutomaticAI API Token (op read failed)", tried)

        with mock.patch.object(board, "_op_read", return_value="from-op") as op:
            self.assertEqual(board.resolve_api_key(project())[:2], ("from-op", "builtin ref for workspace automaticai"))
            op.assert_called_once_with("op://DeLoSecrets/Plane/AutomaticAI API Token")

        os.environ["PLANE_AUTOMATICAI_API_KEY"] = "ws-key"
        self.assertEqual(board.resolve_api_key(project())[:2], ("ws-key", "env PLANE_AUTOMATICAI_API_KEY"))
        os.environ["PLANE_API_KEY"] = "generic"
        self.assertEqual(board.resolve_api_key(project())[:2], ("generic", "env PLANE_API_KEY"))

        os.environ["MY_PLANE_KEY"] = "named"
        self.assertEqual(board.resolve_api_key(project(config={"board": {"api_key_ref": "env:MY_PLANE_KEY"}}))[:2],
                         ("named", "env MY_PLANE_KEY"))
        with mock.patch.object(board, "_op_read", return_value="cfg-op") as op:
            key, source, _ = board.resolve_api_key(project(config={"board": {"api_key_ref": "op://Vault/Item/field"}}))
            self.assertEqual((key, source), ("cfg-op", "board.api_key_ref op://Vault/Item/field"))
            op.assert_called_once_with("op://Vault/Item/field")

    def test_a_literal_key_in_config_is_never_used(self):
        key, source, tried = board.resolve_api_key(project(config={"board": {"api_key_ref": "plane_api_1234567890"}}))
        self.assertEqual((key, source), (None, "none"))
        self.assertTrue(tried[0].startswith("board.api_key_ref is neither op://"))
        self.assertNotIn("plane_api_1234567890", " ".join(tried))


class FakeResponse:
    def __init__(self, raw: bytes):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.raw


class PlaneApiTests(unittest.TestCase):
    def test_headers_and_url(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["req"] = req
            return FakeResponse(b'{"results": [{"id": "x", "name": "y"}], "next_page_results": false}')

        api = board.PlaneApi("automaticai", BOARD_ID, "secret-key")
        with mock.patch.object(board.urllib.request, "urlopen", fake_urlopen):
            self.assertEqual(api.labels(), [{"id": "x", "name": "y"}])
        req = captured["req"]
        self.assertEqual(req.full_url, f"https://plane.delo.sh/api/v1/workspaces/automaticai/projects/{BOARD_ID}/labels/?per_page=100")
        self.assertEqual(req.get_header("X-api-key"), "secret-key")
        self.assertEqual(req.get_header("User-agent"), board.USER_AGENT)
        self.assertTrue(board.USER_AGENT.startswith("activity-report/"))

    def test_pagination_follows_the_cursor(self):
        pages = iter([b'{"results": [{"id": "1"}], "next_page_results": true, "next_cursor": "100:1:0"}',
                      b'{"results": [{"id": "2"}], "next_page_results": false, "next_cursor": null}'])
        urls = []

        def fake_urlopen(req, timeout=None):
            urls.append(req.full_url)
            return FakeResponse(next(pages))

        with mock.patch.object(board.urllib.request, "urlopen", fake_urlopen):
            self.assertEqual([x["id"] for x in board.PlaneApi("automaticai", BOARD_ID, "k").states()], ["1", "2"])
        self.assertIn("cursor=100%3A1%3A0", urls[1])

    def test_http_errors_become_board_unavailable(self):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)

        with mock.patch.object(board.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(board.BoardUnavailable) as ctx:
                board.PlaneApi("automaticai", BOARD_ID, "k").issue("abc")
        self.assertEqual(ctx.exception.status, 403)
        self.assertIn("User-Agent", str(ctx.exception))

    def test_strip_html(self):
        self.assertEqual(board.strip_html("<ul><li>One</li><li>Two &amp; three</li></ul><p>Done</p>"), "One Two & three Done")


if __name__ == "__main__":
    unittest.main()
