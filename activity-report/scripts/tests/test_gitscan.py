"""gitscan against a throwaway repository: window, excludes, replays, worktrees, stats."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ar import gitscan  # noqa: E402
from ar.common import parse_iso  # noqa: E402
from ar.config import DEFAULTS, Project, ScopeSet  # noqa: E402
from ar.window import Window  # noqa: E402

GIT_ENV = {
    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
    "GIT_AUTHOR_NAME": "Test Author", "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test Author", "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(cwd: str, *args: str, date: str | None = None) -> str:
    env = {**os.environ, **GIT_ENV}
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    proc = subprocess.run(["git", "-C", cwd, *args], env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)}: {proc.stderr}")
    return proc.stdout.strip()


def write(repo: str, name: str, text: str) -> None:
    with open(os.path.join(repo, name), "w", encoding="utf-8") as fh:
        fh.write(text)


def commit(repo: str, name: str, subject: str, date: str) -> str:
    write(repo, name, f"{subject}\n")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", subject, date=date)
    return git(repo, "rev-parse", "HEAD")


def window() -> Window:
    return Window(start=parse_iso("2026-09-02T00:00:00Z"), end=parse_iso("2026-09-03T00:00:00Z"), basis="explicit",
                  previous_event_id=None, previous=None, caveats=[])


class GitScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="ar-gitscan-")
        cls.repo = os.path.join(cls.tmp, "repo")
        cls.wt = os.path.join(cls.tmp, "wt")
        cls.missing = os.path.join(cls.tmp, "missing")
        os.makedirs(cls.repo)
        git(cls.repo, "init", "-q", "-b", "main")
        cls.A = commit(cls.repo, "a.txt", "old commit", "2026-09-01T10:00:00Z")          # before the window
        cls.B = commit(cls.repo, "b.txt", "on main", "2026-09-02T10:00:00Z")
        git(cls.repo, "checkout", "-q", "-b", "feature")
        cls.C = commit(cls.repo, "c.txt", "feature work", "2026-09-02T11:00:00Z")
        git(cls.repo, "checkout", "-q", "main")
        cls.D = commit(cls.repo, "d.txt", "main again", "2026-09-02T12:00:00Z")
        git(cls.repo, "checkout", "-q", "-b", "replay", cls.A)
        git(cls.repo, "cherry-pick", cls.C, date="2026-09-02T13:00:00Z")                # same author date + subject
        cls.C_replay = git(cls.repo, "rev-parse", "HEAD")
        git(cls.repo, "checkout", "-q", "main")
        git(cls.repo, "worktree", "add", "-q", "--detach", cls.wt, "main")
        cls.E = commit(cls.wt, "e.txt", "worktree commit", "2026-09-02T14:00:00Z")       # reachable only from the worktree HEAD
        write(cls.repo, "b.txt", "stashed change\n")
        git(cls.repo, "stash", "push", "-q", date="2026-09-02T15:00:00Z")                # refs/stash: excluded
        write(cls.repo, "untracked.txt", "not committed\n")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def project(self, extra=()):
        return Project(slug="repo", name="Repo", identifier=None, workspace=None, board_id=None, provider_type="plane",
                       repo_path=self.repo, extra_repo_paths=list(extra), config=DEFAULTS, tz="UTC",
                       project_json_path=os.path.join(self.repo, ".project.json"))

    def scope(self, missing=()):
        return ScopeSet(roots=[self.repo], worktrees=[self.wt], missing=list(missing))

    def test_scan(self):
        block = gitscan.scan(self.project(), self.scope(), window())
        self.assertEqual(block["caveats"], [])
        self.assertEqual(block["commit_count"], 4)
        repo = block["repos"][0]
        self.assertEqual((repo["name"], repo["state"], repo["default_branch"]), ("repo", "ok", "main"))
        subjects = [c["subject"] for c in repo["commits"]]
        self.assertEqual(subjects, ["worktree commit", "feature work", "main again", "on main"])
        self.assertEqual(repo["commits"][1]["sha"], self.C_replay)          # the newer copy of a replayed commit wins
        self.assertEqual([c["on_default"] for c in repo["commits"]], [False, False, True, True])
        self.assertEqual((repo["on_default"], repo["off_default"], repo["replays"]), (2, 2, 1))
        self.assertEqual(repo["commits"][0]["at"], "2026-09-02T14:00:00Z")
        self.assertEqual(repo["commits"][0]["author"], "Test Author")
        self.assertTrue(repo["commits"][0]["sha"].startswith(repo["commits"][0]["short"]))
        self.assertFalse(any(s.startswith(("index on", "WIP on", "On main")) for s in subjects), "stash commits leaked")
        self.assertNotIn("old commit", subjects)
        self.assertEqual(repo["branches"], ["main", "feature", "replay"])
        self.assertEqual(len(repo["worktrees"]), 1)
        wt = repo["worktrees"][0]
        self.assertEqual(os.path.realpath(wt["path"]), os.path.realpath(self.wt))
        self.assertIsNone(wt["branch"])
        self.assertTrue(self.E.startswith(wt["head"]))
        self.assertEqual(wt["uncommitted_files"], 0)
        self.assertEqual(repo["uncommitted_files"], 1)
        self.assertEqual((repo["files_changed"], repo["insertions"], repo["deletions"]), (4, 4, 0))
        self.assertFalse(repo["truncated"])

    def test_window_bounds_are_half_open(self):
        w = Window(start=parse_iso("2026-09-02T11:00:00Z"), end=parse_iso("2026-09-02T12:00:00Z"), basis="explicit",
                   previous_event_id=None, previous=None, caveats=[])
        repo = gitscan.scan(self.project(), self.scope(), w)["repos"][0]
        self.assertEqual([c["subject"] for c in repo["commits"]], ["feature work"])
        self.assertEqual(repo["commits"][0]["sha"], self.C)                 # the replay is outside this window
        self.assertEqual(repo["branches"], ["feature"])

    def test_commit_cap_marks_truncated(self):
        with mock.patch.object(gitscan, "COMMIT_CAP", 2):
            block = gitscan.scan(self.project(), self.scope(), window())
        repo = block["repos"][0]
        self.assertTrue(repo["truncated"])
        self.assertEqual((repo["commit_count"], len(repo["commits"])), (4, 2))
        self.assertIn("repo repo: commits capped at 2 of 4", block["caveats"])

    def test_missing_root_is_reported_not_fatal(self):
        block = gitscan.scan(self.project(extra=[self.missing]), self.scope(missing=[self.missing]), window())
        self.assertEqual([r["name"] for r in block["repos"]], ["repo", "missing"])
        self.assertEqual(block["repos"][1]["state"], "missing")
        self.assertEqual(block["repos"][1]["commit_count"], 0)
        self.assertEqual(block["commit_count"], 4)
        self.assertTrue(any("missing" in c and "not a git checkout" in c for c in block["caveats"]))

    def test_log_does_not_split_on_record_separators(self):
        revs = [f"--exclude={glob}" for glob in gitscan.EXCLUDED_REF_GLOBS] + ["--all"]   # --all also walks every worktree HEAD
        entries = gitscan._log(self.repo, revs, window().start, window().end)
        self.assertEqual(sorted(e["sha"] for e in entries), sorted([self.B, self.C, self.D, self.C_replay, self.E]))
        stats = gitscan._numstat(self.repo, revs, window().start, window().end)
        self.assertEqual(stats[self.B], [{"b.txt"}, 1, 0])


if __name__ == "__main__":
    unittest.main()
