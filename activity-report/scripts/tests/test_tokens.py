"""Token usage from captured Claude and Codex transcripts."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import tokens  # noqa: E402
from ar.common import parse_iso  # noqa: E402
from ar.config import ScopeSet  # noqa: E402
from ar.window import Window  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "collect")
CLAUDE_ROOT = os.path.join(FIXTURES, "claude_home", "projects")
CODEX_ROOT = os.path.join(FIXTURES, "codex_home", "sessions")
ROOT = "/home/delorenj/code/james-brennan"
WORKTREE = "/home/delorenj/code/james-brennan-jimb169"

SESS_A = {"input": 159, "output": 6699, "cache_read": 144593, "cache_write": 41934, "total": 193385}
SUBAGENT = {"input": 2, "output": 214, "cache_read": 13719, "cache_write": 14958, "total": 28893}
OTHER_PROJECT_TOTAL = 2 + 291 + 0 + 75594
CODEX_SLICE = {"input": 5824, "output": 571, "cache_read": 82432, "cache_write": 0, "total": 88827}
CODEX_ALL = {"input": 53151, "output": 4230, "cache_read": 375552, "cache_write": 0, "total": 432933}


def window(start: str, end: str) -> Window:
    return Window(start=parse_iso(start), end=parse_iso(end), basis="explicit", previous_event_id=None, previous=None, caveats=[])


def scope(*extra_roots, worktrees=(WORKTREE,)) -> ScopeSet:
    return ScopeSet(roots=[ROOT, *extra_roots], worktrees=list(worktrees), missing=[])


def collect(win: Window, sc: ScopeSet | None = None) -> dict:
    return tokens.collect(sc or scope(), win, claude_root=CLAUDE_ROOT, codex_root=CODEX_ROOT)


class TokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for dirpath, _dirs, files in os.walk(FIXTURES):     # the mtime gate must not depend on checkout time
            for name in files:
                if name.endswith(".jsonl"):
                    os.utime(os.path.join(dirpath, name), None)

    def test_claude_dedups_streamed_copies_by_message_id(self):
        out = collect(window("2026-09-02T21:00:00Z", "2026-09-02T23:00:00Z"), scope(worktrees=()))
        self.assertEqual(out["by_agent"]["claude"], SESS_A)
        detail = out["detail"]["claude"]
        self.assertEqual((detail["root_present"], detail["files"], detail["sessions"], detail["messages"]), (True, 2, 1, 3))
        self.assertEqual(sum(detail["by_model"].values()), 3)
        self.assertIsNone(out["by_agent"]["codex"])                 # the rollout lives in the worktree, which is out of scope here
        self.assertIsNone(out["by_agent"]["kimi"])
        self.assertEqual(out["total"], SESS_A["total"])
        self.assertEqual(out["caveats"], ["no Codex rollout in scope for the window"])

    def test_subagent_transcripts_count_for_their_session(self):
        out = collect(window("2026-08-23T00:00:00Z", "2026-08-24T00:00:00Z"))
        self.assertEqual(out["by_agent"]["claude"], SUBAGENT)
        self.assertEqual(out["detail"]["claude"]["sessions"], 1)

    def test_other_projects_are_read_but_not_counted(self):
        wide = window("2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z")
        ours = collect(wide)["by_agent"]["claude"]["total"]
        both = collect(wide, scope("/home/delorenj/code/33GOD"))["by_agent"]["claude"]["total"]
        self.assertEqual(both - ours, OTHER_PROJECT_TOTAL)
        self.assertEqual(ours, SESS_A["total"] + SUBAGENT["total"])

    def test_window_with_no_usage_is_zero_not_null(self):
        out = collect(window("2026-08-25T00:00:00Z", "2026-08-26T00:00:00Z"))
        self.assertEqual(out["by_agent"]["claude"]["total"], 0)
        self.assertEqual(out["detail"]["claude"]["messages"], 0)

    def test_codex_uses_cumulative_totals(self):
        out = collect(window("2026-09-02T17:47:30Z", "2026-09-02T17:48:00Z"))
        self.assertEqual(out["by_agent"]["codex"], CODEX_SLICE)
        detail = out["detail"]["codex"]
        self.assertEqual((detail["files"], detail["sessions_with_usage"], detail["reasoning_output"]), (1, 1, 233))
        out = collect(window("2026-09-02T17:00:00Z", "2026-09-02T18:00:00Z"))
        self.assertEqual(out["by_agent"]["codex"], CODEX_ALL)
        self.assertEqual(out["total"], CODEX_ALL["total"] + out["by_agent"]["claude"]["total"])

    def test_codex_scope_comes_from_session_meta(self):
        out = collect(window("2026-09-02T17:00:00Z", "2026-09-02T18:00:00Z"), scope(worktrees=()))
        self.assertIsNone(out["by_agent"]["codex"])
        self.assertEqual(out["detail"]["codex"]["files"], 0)

    def test_absent_roots(self):
        out = tokens.collect(scope(), window("2026-09-02T17:00:00Z", "2026-09-02T18:00:00Z"),
                             claude_root=os.path.join(FIXTURES, "nope"), codex_root=os.path.join(FIXTURES, "nope"))
        self.assertEqual(out["by_agent"], {"claude": None, "codex": None, "kimi": None})
        self.assertEqual(out["total"], 0)
        self.assertEqual(out["caveats"], ["Claude transcript root is absent", "Codex session root is absent"])
        self.assertEqual(out["detail"]["kimi"], {"status": "no transcript source"})

    def test_bucket_totals_add_up(self):
        for bucket in (SESS_A, SUBAGENT, CODEX_SLICE, CODEX_ALL):
            self.assertEqual(bucket["total"], bucket["input"] + bucket["output"] + bucket["cache_read"] + bucket["cache_write"])


if __name__ == "__main__":
    unittest.main()
