"""Candystore client and derived counts, on captured event shapes."""
import copy
import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import candystore  # noqa: E402
from ar.common import SourceUnavailable  # noqa: E402
from ar.config import ScopeSet  # noqa: E402
from ar.window import Window  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "collect")
ROOT = "/home/delorenj/code/james-brennan"
WORKTREE = "/home/delorenj/code/james-brennan-jimb169"
OTHER = "/home/delorenj/code/james-brennan-other"


def fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


def window(start="2026-09-02T00:00:00Z", end="2026-09-03T00:00:00Z") -> Window:
    return Window(start=candystore.parse_iso(start), end=candystore.parse_iso(end), basis="explicit",
                  previous_event_id=None, previous=None, caveats=[])


def with_cwd(event: dict, cwd: str) -> dict:
    """A copy of a captured event with every working-directory field pointed at `cwd`."""
    e = copy.deepcopy(event)
    data = e["data"]
    if "working_directory" in data:
        data["working_directory"] = cwd
    if isinstance(data.get("payload"), dict) and "cwd" in data["payload"]:
        data["payload"]["cwd"] = cwd
    return e


class ScopeTests(unittest.TestCase):
    """The worktree is in scope only through the worktree list; a sibling directory never is."""

    def test_claude_event_in_root_is_in_scope(self):
        scope = ScopeSet(roots=[ROOT], worktrees=[WORKTREE], missing=[])
        event = fixture("tool_completed_claude.json")
        self.assertEqual(candystore.cwd_of(event), ROOT)
        self.assertTrue(scope.contains(candystore.cwd_of(event)))

    def test_codex_event_in_worktree_needs_the_worktree_list(self):
        event = fixture("tool_completed_codex.json")
        self.assertEqual(candystore.cwd_of(event), WORKTREE)
        self.assertTrue(ScopeSet(roots=[ROOT], worktrees=[WORKTREE], missing=[]).contains(candystore.cwd_of(event)))
        self.assertFalse(ScopeSet(roots=[ROOT], worktrees=[], missing=[]).contains(candystore.cwd_of(event)))
        deeper = with_cwd(event, WORKTREE + "/apps/relay")
        self.assertTrue(ScopeSet(roots=[ROOT], worktrees=[WORKTREE], missing=[]).contains(candystore.cwd_of(deeper)))

    def test_sibling_directory_is_never_in_scope(self):
        scope = ScopeSet(roots=[ROOT], worktrees=[WORKTREE], missing=[])
        for name in ("tool_completed_claude.json", "tool_completed_hermes.json", "tool_completed_codex.json"):
            event = with_cwd(fixture(name), OTHER)
            self.assertEqual(candystore.cwd_of(event), OTHER)
            self.assertFalse(scope.contains(candystore.cwd_of(event)), name)
            self.assertFalse(scope.contains(OTHER + "/apps"), name)
        self.assertFalse(scope.contains("/home/delorenj/code/james-brennan-tmp"))
        self.assertFalse(scope.contains(None))

    def test_hermes_cwd_comes_from_payload(self):
        event = fixture("tool_completed_hermes.json")
        self.assertNotIn("working_directory", event["data"])
        self.assertEqual(candystore.cwd_of(event), ROOT)

    def test_cwd_falls_back_to_payload_raw(self):
        event = fixture("tool_completed_hermes.json")
        del event["data"]["payload"]["cwd"]
        self.assertIsNone(candystore.cwd_of(event))
        event["data"]["payload"]["raw"] = json.dumps({"cwd": WORKTREE, "tool_name": "terminal"})
        self.assertEqual(candystore.cwd_of(event), WORKTREE)


class TypeTests(unittest.TestCase):
    def test_canonical_type_folds_namespaces_and_renames(self):
        self.assertEqual(candystore.canonical_type("bloodbank.v1.agent.tool.completed"), "bloodbank.agent.tool.completed")
        self.assertEqual(candystore.canonical_type("bloodbank.tool.tool_call.completed"), "bloodbank.agent.tool.completed")
        self.assertEqual(candystore.canonical_type("bloodbank.v1.tool.tool_call.failed"), "bloodbank.agent.tool.failed")
        self.assertEqual(candystore.canonical_type("bloodbank.repo.task.updated"), "bloodbank.repo.task.updated")
        self.assertEqual(candystore.canonical_type(None), "")

    def test_type_lists_cover_both_namespaces(self):
        for types in (candystore.TOOL_TYPES, candystore.SESSION_TYPES, candystore.TASK_TYPES, candystore.REPORT_TYPES):
            self.assertTrue(any(t.startswith("bloodbank.v1.") for t in types))
            self.assertTrue(any(not t.startswith("bloodbank.v1.") for t in types))
        self.assertIn("bloodbank.tool.tool_call.completed", candystore.TOOL_TYPES)

    def test_outcome_missing_is_unknown_not_success(self):
        event = fixture("tool_completed_claude.json")
        self.assertEqual(candystore.outcome_class(event), "success")
        del event["data"]["outcome"]
        self.assertEqual(candystore.outcome_class(event), "unknown")
        self.assertEqual(candystore.outcome_class(fixture("tool_completed_hermes_error.json")), "failed")

    def test_field_finds_command_for_every_producer(self):
        self.assertIn("claude --help", candystore.field(fixture("tool_completed_claude.json"), "command"))
        self.assertIn("hermes cron runs", candystore.field(fixture("tool_completed_hermes.json"), "command"))
        self.assertEqual(candystore.field(fixture("tool_completed_hermes.json"), "tool_name"), "terminal")
        self.assertTrue(candystore.field(fixture("tool_completed_codex.json"), "command").startswith("*** Begin Patch"))

    def test_agent_key_normalises(self):
        self.assertEqual(candystore.agent_key("Claude Code"), "claude-code")
        self.assertEqual(candystore.agent_key(None), "unknown")
        self.assertEqual(candystore.agent_key("33god"), "cli-33god")
        self.assertEqual(candystore.cli_of(fixture("tool_completed_hermes.json")), "hermes")

    def test_deploy_detection(self):
        for cmd in ("mise run relay:deploy", "cd ~/code/x && mise run deploy:relay", "bash scripts/relay-ecs-build-push.sh",
                    "cd apps/relay && sudo ./deploy.sh --env prod", "wrangler deploy --env prod", "pnpm run deploy",
                    "gh workflow run deploy-relay.yml", "unset AWS_PROFILE; aws ecs update-service --cluster x", "  mise run relay:deploy\n"):
            self.assertTrue(candystore.is_deploy_command(cmd), cmd)
        for cmd in ("pytest tests/test_deploy_gate.py", "python3 tests/test_deploy_gate.py", "sed -n 1,80p scripts/relay-ecs-build-push.sh",
                    "cd ~/code/james-brennan && cat apps/project-room/deploy/.env", "gh run list --workflow 'deploy relay' --limit 8",
                    "git diff origin/main -- devops/ecs/taskdefs/deploy.json", "cat > notes.md <<'EOF'\nmise run deploy tomorrow\nEOF",
                    "*** Begin Patch\n*** Update File: tests/test_deploy_gate.py", "mise tasks --hidden --json | grep deploy", "", None):
            self.assertFalse(candystore.is_deploy_command(cmd), cmd)


class FakeStore:
    """Serves /events from a list, newest first, honouring type/from/to/limit/offset like Candystore."""

    def __init__(self, events, limit_cap=1000):
        self.events = sorted(events, key=lambda e: e["time"], reverse=True)
        self.limit_cap = limit_cap
        self.urls = []

    def __call__(self, url, timeout=30):
        self.urls.append(url)
        q = parse_qs(urlparse(url).query)
        assert "project" not in q, "never pass project= (the store's project column is the cwd basename)"
        types = set(q["type"][0].split(","))
        start = candystore.parse_iso(q["from"][0])
        end = candystore.parse_iso(q["to"][0]) if q.get("to") else None
        rows = [e for e in self.events if e["type"] in types and candystore.parse_iso(e["time"]) >= start
                and (end is None or candystore.parse_iso(e["time"]) <= end)]
        limit = min(int(q.get("limit", ["1000"])[0]), self.limit_cap)
        offset = int(q.get("offset", ["0"])[0])
        return {"events": rows[offset:offset + limit], "total": len(rows), "limit": limit, "offset": offset}


def stamped(event, time, **data):
    e = copy.deepcopy(event)
    e["time"] = time
    e["data"].update(data)
    return e


class FetchTests(unittest.TestCase):
    def test_paging_and_inclusive_to(self):
        base = fixture("tool_completed_claude.json")
        events = [stamped(base, f"2026-09-02T00:00:{i:02d}.000000Z", invocation_id=str(i)) for i in range(7)]
        events.append(stamped(base, "2026-09-03T00:00:00.000000Z", invocation_id="edge"))  # == end, must be dropped
        store = FakeStore(events, limit_cap=3)
        with mock.patch.object(candystore, "fetch_json", store):
            got, total, truncated = candystore.fetch_events(candystore.TOOL_TYPES, window().start, window().end, page_size=3)
        self.assertEqual(total, 8)
        self.assertEqual(len(got), 7)
        self.assertFalse(truncated)
        self.assertFalse(any(e["data"]["invocation_id"] == "edge" for e in got))
        self.assertEqual(len(store.urls), 3)
        self.assertIn("to=2026-09-03T00:00:00Z", store.urls[0])
        self.assertIn("type=bloodbank.agent.tool.completed,bloodbank.v1.agent.tool.completed", store.urls[0])

    def test_max_pages_marks_truncated(self):
        base = fixture("tool_completed_claude.json")
        store = FakeStore([stamped(base, f"2026-09-02T00:00:{i:02d}.000000Z") for i in range(10)], limit_cap=2)
        with mock.patch.object(candystore, "fetch_json", store):
            got, total, truncated = candystore.fetch_events(candystore.TOOL_TYPES, window().start, window().end,
                                                            page_size=2, max_pages=2)
        self.assertEqual((len(got), total, truncated), (4, 10, True))

    def test_unreachable_store_is_source_unavailable(self):
        with self.assertRaises(SourceUnavailable):
            candystore.fetch_json("http://127.0.0.1:1/events")
        with mock.patch.object(candystore, "fetch_json", side_effect=SourceUnavailable("down")):
            with self.assertRaises(SourceUnavailable):
                candystore.collect_tools(ScopeSet(roots=[ROOT], worktrees=[], missing=[]), window())


class CollectToolsTests(unittest.TestCase):
    def setUp(self):
        claude = fixture("tool_completed_claude.json")
        hermes = fixture("tool_completed_hermes.json")
        hermes_error = fixture("tool_completed_hermes_error.json")
        codex = fixture("tool_completed_codex.json")
        self.events = [
            stamped(claude, "2026-09-02T10:00:00.000000Z"),
            stamped(claude, "2026-09-02T10:01:00.000000Z", arguments={"command": "mise run relay:deploy"}),
            stamped(claude, "2026-09-02T10:02:00.000000Z", invocation_id="second-claude-session", git_branch="feat/x"),
            stamped(claude, "2026-09-02T10:03:00.000000Z", arguments={"command": "cat > notes.md <<'EOF'\ncd x && mise run deploy\nEOF"}),
            stamped(hermes, "2026-09-02T11:00:00.000000Z"),
            stamped(hermes_error, "2026-09-02T11:01:00.000000Z"),
            stamped(codex, "2026-09-02T12:00:00.000000Z"),                       # worktree: in scope
            with_cwd(stamped(codex, "2026-09-02T12:01:00.000000Z"), OTHER),      # sibling: never
            stamped(claude, "2026-09-02T13:00:00.000000Z", outcome=None),        # unknown outcome
        ]
        self.store = FakeStore(self.events)

    def collect(self, scope):
        with mock.patch.object(candystore, "fetch_json", self.store):
            return candystore.collect_tools(scope, window())

    def test_counts(self):
        block = self.collect(ScopeSet(roots=[ROOT], worktrees=[WORKTREE], missing=[]))
        self.assertEqual(block["tool_calls_total"], 8)
        self.assertEqual(block["by_cli"], {"claude": 5, "hermes": 2, "codex": 1})
        self.assertEqual(block["failed"], 1)
        self.assertEqual(block["unknown_outcome"], 1)
        self.assertEqual(block["sessions"], 4)   # claude x2, hermes, codex: distinct invocation_id, not volume
        self.assertEqual(block["sessions_by_cli"], {"claude": 2, "codex": 1, "hermes": 1})
        self.assertEqual(block["branches_touched"], ["codex/jimb-169-prod-incident-20260901", "feat/x", "main"])
        self.assertEqual(block["by_tool"]["Bash"], 5)
        self.assertEqual([d["command"] for d in block["deploy_commands"]], ["mise run relay:deploy"])   # the heredoc body is not a deploy
        self.assertEqual(len(block["failures"]), 1)
        self.assertEqual(block["failures"][0]["tool"], "mcp__plane__workitem_relation")
        self.assertEqual(block["failures"][0]["at"], "2026-09-02T11:01:00Z")
        self.assertEqual(block["coverage"], {"total": 9, "fetched": 9, "pages": 1, "truncated": False})
        self.assertTrue(block["reachable"])

    def test_worktree_scope_changes_the_count(self):
        block = self.collect(ScopeSet(roots=[ROOT], worktrees=[], missing=[]))
        self.assertEqual(block["tool_calls_total"], 7)
        self.assertNotIn("codex", block["by_cli"])


class SessionsEndedTests(unittest.TestCase):
    def test_sums(self):
        claude = with_cwd(fixture("session_ended_claude.json"), ROOT)
        hermes = fixture("session_ended_hermes.json")                       # cwd 33GOD/bloodbank: out
        hermes_in = with_cwd(hermes, WORKTREE + "/apps")
        store = FakeStore([stamped(claude, "2026-09-02T10:00:00.000000Z"), stamped(hermes, "2026-09-02T10:00:01.000000Z"),
                           stamped(hermes_in, "2026-09-02T10:00:02.000000Z")])
        with mock.patch.object(candystore, "fetch_json", store):
            block = candystore.collect_sessions_ended(ScopeSet(roots=[ROOT], worktrees=[WORKTREE], missing=[]), window())
        self.assertEqual(block, {"count": 2, "turns": 8, "duration_seconds": 51, "by_cli": {"claude": 1, "hermes": 1}})


class TicketTests(unittest.TestCase):
    def records(self, events, slug="james-brennan"):
        with mock.patch.object(candystore, "fetch_json", FakeStore(events)):
            return {r["key"] or r["ticket_id"]: r for r in candystore.collect_tickets(slug, window(), identifier="JIMB")}

    def test_title_edit_is_not_a_transition(self):
        rec = self.records([stamped(fixture("task_updated_title.json"), "2026-09-02T10:00:00.000000Z")])["JIMB-230"]
        self.assertEqual(rec["transitions"], [])
        self.assertFalse(rec["closed"] or rec["started"] or rec["opened"])
        self.assertEqual(rec["phase"], "Todo")
        self.assertEqual(rec["kinds"], ["updated"])

    def test_state_change_marks_started_and_done_marks_closed(self):
        recs = self.records([
            stamped(fixture("task_updated_state.json"), "2026-09-02T10:00:00.000000Z"),
            stamped(fixture("task_updated_done.json"), "2026-09-02T11:00:00.000000Z"),
            stamped(fixture("task_created.json"), "2026-09-02T12:00:00.000000Z"),
        ])
        self.assertTrue(recs["JIMB-169"]["started"])
        self.assertFalse(recs["JIMB-169"]["closed"])
        self.assertEqual(recs["JIMB-169"]["transitions"][0]["from_state_id"], "5c475e29-3255-4e80-b536-82ccec365000")
        self.assertTrue(recs["JIMB-229"]["closed"])
        self.assertEqual(recs["JIMB-229"]["last_transition"]["to_phase"], "Done")
        self.assertTrue(recs["JIMB-251"]["opened"])
        self.assertEqual(recs["JIMB-251"]["labels"][0]["name"], "xp:external")
        self.assertEqual(recs["JIMB-251"]["first_seen"], "2026-09-02T12:00:00Z")

    def test_last_transition_wins_on_reopen(self):
        done = stamped(fixture("task_updated_done.json"), "2026-09-02T10:00:00.000000Z")
        reopened = copy.deepcopy(fixture("task_updated_state.json"))
        reopened["data"]["ticket_key"] = "JIMB-229"
        reopened["data"]["ticket_id"] = done["data"]["ticket_id"]
        reopened = stamped(reopened, "2026-09-02T11:00:00.000000Z")
        rec = self.records([done, reopened])["JIMB-229"]
        self.assertFalse(rec["closed"])
        self.assertTrue(rec["started"])
        self.assertEqual(len(rec["transitions"]), 2)

    def test_comment_merges_by_ticket_id_and_key_is_derived(self):
        appended = fixture("task_appended.json")
        update = copy.deepcopy(fixture("task_updated_state.json"))
        update["data"]["ticket_id"] = appended["data"]["ticket_id"]
        update["data"]["ticket"]["id"] = appended["data"]["ticket_id"]
        recs = self.records([stamped(appended, "2026-09-02T09:00:00.000000Z"), stamped(update, "2026-09-02T10:00:00.000000Z")])
        self.assertEqual(list(recs), ["JIMB-169"])
        rec = recs["JIMB-169"]
        self.assertTrue(rec["commented"])
        self.assertEqual(rec["kinds"], ["appended", "updated"])
        self.assertEqual(rec["events"], 2)
        orphan = self.records([stamped(appended, "2026-09-02T09:00:00.000000Z")])
        self.assertEqual(list(orphan), [appended["data"]["ticket_id"]])   # key unknown; board.py resolves or drops it

    def test_other_slug_is_ignored(self):
        self.assertEqual(self.records([stamped(fixture("task_created.json"), "2026-09-02T12:00:00.000000Z")], slug="33god"), {})

    def test_key_from_identifier_and_sequence(self):
        created = fixture("task_created.json")
        del created["data"]["ticket_key"]
        recs = self.records([stamped(created, "2026-09-02T12:00:00.000000Z")])
        self.assertEqual(list(recs), ["JIMB-251"])


class DecisionTests(unittest.TestCase):
    def test_decision_fields(self):
        event = stamped(fixture("decision_recorded.json"), "2026-09-02T12:00:00.000000Z")
        with mock.patch.object(candystore, "fetch_json", FakeStore([event])):
            self.assertEqual(candystore.collect_decisions("james-brennan", window()), [])
            out = candystore.collect_decisions("33god", window())
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["at"], "2026-09-02T12:00:00Z")
        self.assertTrue(out[0]["title"].startswith("Hold Board Cranker"))
        self.assertTrue(out[0]["note"].startswith("33GOD-42: "))


class PreviousReportTests(unittest.TestCase):
    def test_newest_matching_non_dry_run(self):
        internal = fixture("activity_recorded_internal.json")
        real = copy.deepcopy(internal)
        real["data"]["generator"]["dry_run"] = False
        real["data"]["project"]["slug"] = "james-brennan"
        real["id"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        older = copy.deepcopy(real)
        older["id"] = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        older["data"]["window"]["end"] = "2026-09-01T07:00:00Z"
        external = copy.deepcopy(real)
        external["id"] = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        external["data"]["audience"] = "external"
        external["data"]["window"]["end"] = "2026-09-02T09:00:00Z"
        events = [stamped(internal, "2026-09-02T23:00:00.000000Z"),          # dry run: skipped
                  stamped(real, "2026-09-02T08:00:00.000000Z"), stamped(older, "2026-09-01T08:00:00.000000Z"),
                  stamped(external, "2026-09-02T10:00:00.000000Z")]
        store = FakeStore(events)
        now = datetime(2026, 9, 3, 7, tzinfo=timezone.utc)
        with mock.patch.object(candystore, "fetch_json", store):
            found = candystore.find_previous_report("james-brennan", "internal", now)
            self.assertIsNone(candystore.find_previous_report("nobody", "internal", now))
        self.assertEqual(found["event_id"], "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.assertEqual(found["window_end"], "2026-09-02T07:00:00Z")
        self.assertEqual(found["title"], real["data"]["report"]["title"])
        self.assertIn("from=2026-07-20T07:00:00Z", store.urls[0])

    def test_find_events_by_run_id(self):
        event = stamped(fixture("activity_recorded_internal.json"), "2026-09-02T23:00:00.000000Z")
        event["correlationid"] = "11111111-1111-4111-8111-111111111111"
        with mock.patch.object(candystore, "fetch_json", FakeStore([event])):
            since = datetime(2026, 9, 2, tzinfo=timezone.utc)
            self.assertEqual(len(candystore.find_events_by_run_id("11111111-1111-4111-8111-111111111111", since)), 1)
            self.assertEqual(candystore.find_events_by_run_id("nope", since), [])


if __name__ == "__main__":
    unittest.main()
