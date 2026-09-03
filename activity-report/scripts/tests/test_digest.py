"""Digest assembly, path scrubbing and the contract validator."""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import digest as digest_mod  # noqa: E402
from ar.common import ConfigError, ContractError, parse_iso  # noqa: E402
from ar.config import DEFAULTS, Project, ScopeSet  # noqa: E402
from ar.window import Window  # noqa: E402

RUN_ID = "11111111-1111-4111-8111-111111111111"
PREV_ID = "0f6d4b2c-9a1e-4c3d-8b7a-2e5f1c9d0a11"
BOARD_ID = "a8a12be1-b3ab-44f4-ab24-abe8829aeb72"
ROOT = "/home/delorenj/code/james-brennan"
WORKTREE = "/home/delorenj/code/james-brennan-jimb169"


def ticket(audience="internal", **over):
    t = {"key": "JIMB-251", "title": "Client-facing win", "from_state": None, "to_state": "Backlog", "event_kinds": ["created"],
         "labels": ["xp:external"], "exposure": "external", "surface": None if audience == "internal" else "always",
         "description_excerpt": None, "url": None, "first_seen": "2026-09-02T12:00:00Z", "last_seen": "2026-09-02T12:00:00Z"}
    t.update(over)
    return t


def commit(**over):
    c = {"sha": "a" * 40, "short": "aaaaaaa", "at": "2026-09-02T12:00:00Z", "author": "Jarad", "subject": "feat: x", "on_default": True}
    c.update(over)
    return c


def repo(**over):
    r = {"name": "james-brennan", "state": "ok", "default_branch": "main", "commit_count": 1, "on_default": 1, "off_default": 0,
         "replays": 0, "truncated": False, "commits": [commit()], "branches": ["main"],
         "worktrees": [{"path": WORKTREE, "branch": "codex/x", "head": "abcdef0", "uncommitted_files": 0}],
         "uncommitted_files": 0, "files_changed": 1, "insertions": 1, "deletions": 0}
    r.update(over)
    return r


def minimal(audience="internal"):
    return {
        "schema_version": 1, "run_id": RUN_ID, "generated_at": "2026-09-03T07:00:05Z", "audience": audience, "label": "2026-09-03T0300",
        "project": {"slug": "james-brennan", "name": "James Brennan", "identifier": "JIMB", "workspace": "automaticai",
                    "board_id": BOARD_ID, "repos": ["james-brennan"], "timezone": "America/New_York"},
        "window": {"start": "2026-09-02T07:00:00Z", "end": "2026-09-03T07:00:00Z", "duration_seconds": 86400, "basis": "cap_24h",
                   "previous_event_id": None},
        "previous_report": None,
        "scope": {"roots": [ROOT], "worktrees": [WORKTREE]},
        "candystore": {"reachable": True, "base_url": "http://127.0.0.1:8683", "tool_calls_total": 1, "failed": 0, "unknown_outcome": 0,
                       "by_cli": {"claude": 1}, "by_tool": {"Bash": 1}, "sessions": 1, "sessions_by_cli": {"claude": 1},
                       "branches_touched": ["main"], "deploy_commands": [], "failures": [],
                       "sessions_ended": {"count": 0, "turns": 0, "duration_seconds": 0, "by_cli": {}},
                       "coverage": {"total": 1, "fetched": 1, "pages": 1, "truncated": False}},
        "git": {"commit_count": 1, "repos": [repo()]},
        "board": {"provider": "plane", "status": "ok", "labels_resolved": True,
                  "exposure_labels": {"external": "xp:external", "internal": "xp:internal"},
                  "tickets": [ticket(audience)], "opened": ["JIMB-251"], "closed": [], "started": [], "commented": [], "decisions": []},
        "hindsight": {"bank": "james-brennan", "status": "ok", "items": [], "recall": {"query": "q", "items": []}},
        "tokens": {"total": 10, "by_agent": {"claude": {"input": 1, "output": 2, "cache_read": 3, "cache_write": 4, "total": 10},
                                             "codex": None, "kimi": None}, "detail": {}},
        "caveats": [],
    }


class ScrubTests(unittest.TestCase):
    def test_scrub_paths(self):
        cases = {
            "/home/delorenj/code/x": "~/code/x",
            "see /Users/bob/y now": "see ~/y now",
            "/root/z": "~/z",
            "/tmp/a/b": "tmp/a/b",
            "/home/delorenj": "~/",
            "cd /home/delorenj && ls": "cd ~/ && ls",
            "https://x.io/home/y": "https://x.io/home/y",
            "foo.com/tmp/": "foo.com/tmp/",
            "'/var/log/x'": "'var/log/x'",
        }
        for text, want in cases.items():
            self.assertEqual(digest_mod.scrub_paths(text), want, text)
        self.assertEqual(digest_mod.scrub({"a": ["/home/u/x", 1, None, {"b": "/etc/hosts"}]}), {"a": ["~/x", 1, None, {"b": "etc/hosts"}]})

    def test_run_id(self):
        self.assertEqual(digest_mod.normalise_run_id(RUN_ID), RUN_ID)
        self.assertEqual(digest_mod.normalise_run_id(RUN_ID.upper()), RUN_ID)
        self.assertRegex(digest_mod.normalise_run_id(None), digest_mod.UUID_RE)
        with self.assertRaises(ConfigError):
            digest_mod.normalise_run_id("nope")

    def test_lint_json_path_sits_next_to_out(self):
        proj = mock.Mock(repo_path="/tmp/jb", slug="james-brennan", config={"output": {"runtime_dir": "runtime/activity-report"}})
        self.assertEqual(digest_mod.lint_json_path(proj, "2026-09-03T0300", "/x/y/foo.digest.json"), "/x/y/2026-09-03T0300-external.lint.json")
        self.assertEqual(digest_mod.lint_json_path(proj, "2026-09-03T0300"),
                         "/tmp/jb/runtime/activity-report/james-brennan/2026-09-03T0300-external.lint.json")
        self.assertEqual(digest_mod.digest_path(proj, "2026-09-03T0300", "internal"),
                         "/tmp/jb/runtime/activity-report/james-brennan/2026-09-03T0300-internal.digest.json")


class ValidateTests(unittest.TestCase):
    def assert_rejects(self, mutate, needle: str, audience="internal"):
        d = minimal(audience)
        mutate(d)
        with self.assertRaises(ContractError) as ctx:
            digest_mod.validate_digest(d)
        self.assertIn(needle, str(ctx.exception), str(ctx.exception))

    def test_minimal_digests_pass(self):
        digest_mod.validate_digest(minimal("internal"))
        digest_mod.validate_digest(minimal("external"))

    def test_window_rules(self):
        def short_cap(d):
            d["window"].update({"start": "2026-09-03T06:00:00Z", "duration_seconds": 3600})
        self.assertRejects = self.assert_rejects
        self.assert_rejects(short_cap, "cap_24h requires exactly 86400")
        self.assert_rejects(lambda d: d["window"].update({"basis": "previous_report"}), "previous_event_id")
        self.assert_rejects(lambda d: d["window"].update({"duration_seconds": 100}), "must equal end - start")
        self.assert_rejects(lambda d: d["window"].update({"basis": "yesterday"}), "window.basis")
        self.assert_rejects(lambda d: d["window"].update({"end": "2026-09-03T07:00:00+00:00"}), "ending in Z")
        d = minimal()
        d["window"].update({"basis": "previous_report", "previous_event_id": PREV_ID})
        d["previous_report"] = {"event_id": PREV_ID, "window_end": "2026-09-02T07:00:00Z", "title": "T", "raw_excerpt": "x" * 600}
        digest_mod.validate_digest(d)
        d["previous_report"]["raw_excerpt"] = "x" * 601
        with self.assertRaises(ContractError):
            digest_mod.validate_digest(d)

    def test_audience_rules(self):
        self.assert_rejects(lambda d: d["board"]["tickets"][0].update({"surface": "always"}), "must be null in an internal digest")
        self.assert_rejects(lambda d: d["board"]["tickets"][0].update({"exposure": "internal", "surface": "judgment"}),
                            "never appear in an external digest", audience="external")
        self.assert_rejects(lambda d: d["board"]["tickets"][0].update({"surface": "judgment"}), "must be 'always'", audience="external")
        self.assert_rejects(lambda d: d["board"]["tickets"][0].update({"exposure": "unlabeled"}), "must be 'judgment'", audience="external")
        self.assert_rejects(lambda d: d.update({"audience": "client"}), "audience")

    def test_caps_and_shapes(self):
        self.assert_rejects(lambda d: d["board"].update({"opened": ["JIMB-999"]}), "not in board.tickets")
        self.assert_rejects(lambda d: d["board"]["tickets"].append(ticket()), "duplicate ticket key")
        self.assert_rejects(lambda d: d["board"]["tickets"][0].update({"key": "jimb-1"}), "does not match")
        self.assert_rejects(lambda d: d["board"]["tickets"][0].update({"labels": ["l"] * 9}), "more than 8 items")
        self.assert_rejects(lambda d: d["git"]["repos"][0].update({"name": "code/james-brennan"}), "does not match")
        self.assert_rejects(lambda d: d["git"]["repos"][0].update({"truncated": True}), "truncated")
        self.assert_rejects(lambda d: d["git"]["repos"][0].update({"commits": [commit(sha=f"{i:040x}") for i in range(101)],
                                                                    "commit_count": 101}), "more than 100 items")
        self.assert_rejects(lambda d: d["git"]["repos"][0]["commits"][0].update({"subject": "s" * 121}), "longer than 120")
        self.assert_rejects(lambda d: d["git"]["repos"][0]["commits"][0].update({"sha": "xyz"}), "sha")
        self.assert_rejects(lambda d: d["git"]["repos"].append(repo()), "duplicate repo name")
        self.assert_rejects(lambda d: d["candystore"].update({"reachable": False}), "exit 2")
        self.assert_rejects(lambda d: d["candystore"].update({"by_cli": {"Claude Code": 1}}), "by_cli key")
        self.assert_rejects(lambda d: d["candystore"].update({"failures": [{"at": "x", "cli": "claude", "tool": "Bash", "detail": "d"}] * 41}),
                            "more than 40 items")
        self.assert_rejects(lambda d: d["candystore"].update({"by_tool": {f"t{i}": 1 for i in range(13)}}), "more than 12 tools")
        self.assert_rejects(lambda d: d["candystore"].update({"branches_touched": [f"b{i}" for i in range(65)]}), "more than 64 items")
        self.assert_rejects(lambda d: d["candystore"]["sessions_ended"].pop("turns"), "sessions_ended")
        self.assert_rejects(lambda d: d["hindsight"].update({"status": "meh"}), "hindsight.status")
        self.assert_rejects(lambda d: d.update({"label": "2026-09-03"}), "label")
        self.assert_rejects(lambda d: d.update({"run_id": "abc"}), "run_id")
        self.assert_rejects(lambda d: d.update({"schema_version": 2}), "schema_version")
        self.assert_rejects(lambda d: d.pop("tokens"), "missing key 'tokens'")

    def test_token_rules(self):
        self.assert_rejects(lambda d: d["tokens"].update({"total": 11}), "sum of the non-null buckets")
        self.assert_rejects(lambda d: d["tokens"]["by_agent"]["claude"].update({"input": 5}), "not the sum of its parts")
        self.assert_rejects(lambda d: d["tokens"]["by_agent"].update({"kimi": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "total": 0}}),
                            "kimi")
        self.assert_rejects(lambda d: d["tokens"]["by_agent"].pop("codex"), "tokens.by_agent")
        self.assert_rejects(lambda d: d["tokens"]["by_agent"]["claude"].update({"input": -1}), "non-negative")
        d = minimal()
        d["tokens"] = {"total": 0, "by_agent": {"claude": None, "codex": None, "kimi": None}, "detail": {}}
        digest_mod.validate_digest(d)

    def test_absolute_paths_are_refused_everywhere_but_scope_and_worktrees(self):
        self.assert_rejects(lambda d: d["caveats"].append("see /home/delorenj/x"), "caveats[0]: carries an absolute path")
        self.assert_rejects(lambda d: d["git"]["repos"][0]["commits"][0].update({"subject": "fix /tmp/thing"}), "commits[0].subject")
        self.assert_rejects(lambda d: d["git"]["repos"][0]["worktrees"][0].update({"branch": "/var/x"}), "worktrees[0].branch")
        self.assert_rejects(lambda d: d["git"]["repos"][0]["worktrees"][0].update({"path": "relative/x"}), "must be an absolute path")
        self.assert_rejects(lambda d: d["board"]["tickets"][0].update({"description_excerpt": "at /Users/me/x"}), "description_excerpt")
        self.assert_rejects(lambda d: d["scope"]["roots"].append("code/x"), "scope.roots[1]")
        d = minimal()
        d["board"]["tickets"][0]["title"] = "https://example.com/home/page and /opt without a slash after"
        digest_mod.validate_digest(d)


class CollectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ar-digest-")
        self.repo = os.path.join(self.tmp, "james-brennan")
        os.makedirs(self.repo)
        self.project = Project(slug="james-brennan", name="James Brennan", identifier="JIMB", workspace="automaticai", board_id=BOARD_ID,
                               provider_type="plane", repo_path=self.repo, extra_repo_paths=[], config=DEFAULTS, tz="America/New_York",
                               project_json_path=os.path.join(self.repo, ".project.json"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def window(self, previous=True):
        prev = {"event_id": PREV_ID, "window_end": "2026-09-02T07:00:00Z", "title": "Yesterday", "raw": "r" * 1000} if previous else None
        return Window(start=parse_iso("2026-09-02T07:00:00Z"), end=parse_iso("2026-09-03T07:00:00Z"),
                      basis="previous_report" if previous else "cap_24h", previous_event_id=PREV_ID if previous else None,
                      previous=prev, caveats=["previous end clamped"] if previous else [])

    def patches(self, audience):
        tools = {"reachable": True, "base_url": "http://127.0.0.1:8683", "tool_calls_total": 3, "failed": 1, "unknown_outcome": 0,
                 "by_cli": {"claude": 2, "hermes": 1}, "by_tool": {"Bash": 3}, "sessions": 2, "sessions_by_cli": {"claude": 1, "hermes": 1},
                 "branches_touched": ["main"], "deploy_commands": [{"at": "2026-09-02T12:00:00Z", "cli": "claude", "command": "mise run deploy"}],
                 "failures": [{"at": "2026-09-02T12:00:00Z", "cli": "hermes", "tool": "terminal", "detail": f"ls {ROOT}/apps: boom"}],
                 "coverage": {"total": 3, "fetched": 3, "pages": 1, "truncated": False}, "caveats": ["failures list capped at 40 of 41"]}
        ended = {"count": 1, "turns": 4, "duration_seconds": 30, "by_cli": {"claude": 1}}
        records = [{"key": "JIMB-251", "ticket_id": "t1"}]
        decisions = [{"at": "2026-09-02T13:00:00Z", "title": "Hold", "note": "JIMB-1: because"}]
        git = {"commit_count": 1, "repos": [repo(commits=[commit(subject=f"fix: read {ROOT}/boards")])],
               "caveats": [f"repo james-brennan: worktree jimb169 skipped: boom at {WORKTREE}"]}
        board_block = {"provider": "plane", "status": "ok", "labels_resolved": True,
                       "exposure_labels": {"external": "xp:external", "internal": "xp:internal"},
                       "tickets": [ticket(audience, description_excerpt=f"see {ROOT}/docs")], "opened": ["JIMB-251"], "closed": [],
                       "started": [], "commented": [], "decisions": [], "caveats": ["xp:internal missing"]}
        lint = {"identifiers": ["JIMB"], "denied_titles": [f"Secret at {ROOT}/x"], "surface_always": [{"key": "JIMB-251", "title": "Client-facing win"}]} \
            if audience == "external" else None
        hs = {"bank": "james-brennan", "status": "ok", "items": [{"at": "2026-09-02T10:00:00Z", "fact_type": "world", "text": f"note {ROOT}"}],
              "recall": {"query": "q", "items": []}, "caveats": []}
        tok = {"total": 10, "by_agent": {"claude": {"input": 1, "output": 2, "cache_read": 3, "cache_write": 4, "total": 10}, "codex": None, "kimi": None},
               "detail": {"claude": {"files": 1}, "codex": {}, "kimi": {}}, "caveats": ["no Codex rollout in scope for the window"]}
        scope = ScopeSet(roots=[ROOT], worktrees=[WORKTREE], missing=["/home/delorenj/code/missing"])
        return [
            mock.patch.object(digest_mod, "scope_set", return_value=scope),
            mock.patch.object(digest_mod.candystore, "collect_tools", return_value=copy.deepcopy(tools)),
            mock.patch.object(digest_mod.candystore, "collect_sessions_ended", return_value=ended),
            mock.patch.object(digest_mod.candystore, "collect_tickets", return_value=records),
            mock.patch.object(digest_mod.candystore, "collect_decisions", return_value=decisions),
            mock.patch.object(digest_mod.gitscan, "scan", return_value=copy.deepcopy(git)),
            mock.patch.object(digest_mod.board, "enrich", return_value=(copy.deepcopy(board_block), lint)),
            mock.patch.object(digest_mod.hindsight, "collect", return_value=copy.deepcopy(hs)),
            mock.patch.object(digest_mod.tokens, "collect", return_value=copy.deepcopy(tok)),
        ]

    def collect(self, audience, out=None, previous=True):
        patches = self.patches(audience)
        for p in patches:
            p.start()
        try:
            return digest_mod.collect(self.project, audience, self.window(previous), RUN_ID, out_path=out)
        finally:
            for p in patches:
                p.stop()

    def test_internal_digest(self):
        out = os.path.join(self.tmp, "out", "x-internal.digest.json")
        d = self.collect("internal", out)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), d)
        self.assertEqual(list(d), list(digest_mod.TOP_KEYS))
        self.assertEqual((d["run_id"], d["audience"], d["label"]), (RUN_ID, "internal", "2026-09-03T0300"))
        self.assertEqual(d["project"]["repos"], ["james-brennan"])
        self.assertEqual(d["window"], {"start": "2026-09-02T07:00:00Z", "end": "2026-09-03T07:00:00Z", "duration_seconds": 86400,
                                       "basis": "previous_report", "previous_event_id": PREV_ID})
        self.assertEqual(d["previous_report"], {"event_id": PREV_ID, "window_end": "2026-09-02T07:00:00Z", "title": "Yesterday",
                                                "raw_excerpt": "r" * 600})
        self.assertEqual(d["scope"], {"roots": [ROOT], "worktrees": [WORKTREE]})
        self.assertEqual(d["caveats"], [
            "window: previous end clamped",
            "scope: configured root ~/code/missing is not a git checkout",
            "candystore: failures list capped at 40 of 41",
            "git: repo james-brennan: worktree jimb169 skipped: boom at ~/code/james-brennan-jimb169",
            "board: xp:internal missing",
            "tokens: no Codex rollout in scope for the window",
        ])
        self.assertEqual(d["candystore"]["failures"][0]["detail"], "ls ~/code/james-brennan/apps: boom")
        self.assertEqual(d["candystore"]["sessions_ended"]["turns"], 4)
        self.assertNotIn("caveats", d["candystore"])
        self.assertEqual(d["git"]["repos"][0]["commits"][0]["subject"], "fix: read ~/code/james-brennan/boards")
        self.assertEqual(d["git"]["repos"][0]["worktrees"][0]["path"], WORKTREE)
        self.assertEqual(d["board"]["tickets"][0]["description_excerpt"], "see ~/code/james-brennan/docs")
        self.assertEqual(d["board"]["decisions"], [{"at": "2026-09-02T13:00:00Z", "title": "Hold", "note": "JIMB-1: because"}])
        self.assertEqual(d["hindsight"]["items"][0]["text"], "note ~/code/james-brennan")
        self.assertEqual(d["tokens"]["total"], 10)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out", "2026-09-03T0300-external.lint.json")))
        digest_mod.validate_digest(d)

    def test_external_digest_writes_lint_json(self):
        out = os.path.join(self.tmp, "out", "x-external.digest.json")
        d = self.collect("external", out)
        self.assertEqual(d["board"]["tickets"][0]["surface"], "always")
        lint_path = os.path.join(self.tmp, "out", "2026-09-03T0300-external.lint.json")
        with open(lint_path, encoding="utf-8") as fh:
            lint = json.load(fh)
        self.assertEqual(lint, {"identifiers": ["JIMB"], "denied_titles": ["Secret at ~/code/james-brennan/x"],
                                "surface_always": [{"key": "JIMB-251", "title": "Client-facing win"}]})

    def test_default_paths_follow_runtime_layout(self):
        d = self.collect("internal", previous=False)
        self.assertIsNone(d["previous_report"])
        self.assertEqual(d["window"]["basis"], "cap_24h")
        expected = os.path.join(self.repo, "runtime", "activity-report", "james-brennan", "2026-09-03T0300-internal.digest.json")
        self.assertTrue(os.path.isfile(expected))

    def test_bad_audience_and_run_id(self):
        with self.assertRaises(ConfigError):
            self.collect("client")
        with self.assertRaises(ConfigError):
            digest_mod.collect(self.project, "internal", self.window(), "not-a-uuid")

    def test_collect_cmd_prints_a_summary(self):
        out = os.path.join(self.tmp, "cmd.digest.json")
        args = mock.Mock(project=None, audience="internal", since=None, until=None, force=False, run_id=RUN_ID, out=out, json=False)
        with mock.patch.object(digest_mod, "load_project", return_value=self.project), \
                mock.patch.object(digest_mod.window_mod, "resolve", return_value=self.window()), \
                mock.patch.object(digest_mod, "collect", return_value=minimal()), mock.patch("sys.stdout") as stdout:
            self.assertEqual(digest_mod.collect_cmd(args), 0)
        text = "".join(c.args[0] for c in stdout.write.call_args_list)
        self.assertIn(f"digest    {out}", text)
        self.assertIn("by_cli claude=1", text)
        self.assertIn("tokens    total 10; claude=10, codex=null, kimi=null", text)


if __name__ == "__main__":
    unittest.main()
