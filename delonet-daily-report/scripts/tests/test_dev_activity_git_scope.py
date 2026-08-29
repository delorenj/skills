"""The git sweep's scope: what it reads, and that it says so.

The defect these cover was proven on real data. On 2026-08-15 the published
report said "1 configured project root(s) were read and had no commits ...:
intelliforia" while that repository held commit 2096cdc2 "fix(staging): move to
stg.intelliforia.com" dated that day -- on a ref other than the checked-out
``design/admin-portal-overhaul``. On 2026-08-17 pjangler's HEAD was
``fix/PJAN-67-fleet-env-authority`` and eight commits, five of them already on
``main``, were missing from a section that claimed 9 of 9 repositories covered.
The scope of the read appeared in no artifact, metric, caveat or report line.

So every test here asserts one of two things: the commit is not lost, or the
scope of the number is stated. A count whose scope the reader cannot see is a
coverage claim the collector did not earn.
"""

#: RETIRED-SHAPE FIXTURES ARE DELIBERATE HERE. Every `bloodbank.v1.*` literal
#: below is test DATA, not a producer: it pins the dual-shape read in
#: collectors/dev_activity.py:175 (`canonical_type`) and the query widening in
#: collectors/report_delivery.py, which exist because ~713k Candystore rows
#: predate the version-drop and still carry the five-token spelling. Rewriting
#: these to the four-token grammar would delete the only coverage proving the
#: old rows still read. Grammar sweeps: stop here, this is not a violation.

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from collectors import dev_activity
from reportctl_contracts import validate_section_artifact
from test_fixtures import config as base_config

# Hermetic git: the machine's hooksPath, signing key and identity stay out.
GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}
IDENTITY = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]
IN_WINDOW = "2026-08-17T12:00:00Z"
DATE = "2026-08-17"


def git(repo: Path, *args: str, when: str | None = None) -> subprocess.CompletedProcess:
    env = dict(GIT_ENV)
    if when:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True, check=True, timeout=60
    )


def commit(repo: Path, message: str, *, when: str = IN_WINDOW, name: str | None = None) -> None:
    (repo / (name or f"{abs(hash(message)) % 10**8}.txt")).write_text(message, encoding="utf-8")
    git(repo, *IDENTITY, "add", ".")
    git(repo, *IDENTITY, "commit", "-q", "-m", message, when=when)


def make_repo(path: Path, messages: list[str], when: str = IN_WINDOW) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main", ".")
    for index, message in enumerate(messages):
        commit(path, message, when=when, name=f"file{index}.txt")
    return path


def event(project: str = "widget") -> dict:
    return {
        "id": "evt-1",
        "type": "bloodbank.v1.agent.tool.completed",  # retired shape on purpose: backward-compat fixture, see file header
        "time": "2026-08-17T15:30:00Z",
        "cli": "claude",
        "project": project,
        "correlationid": "corr-1",
        "data": {},
    }


class FakeCandystore:
    """Serves /events and an empty /summary/heatmap."""

    def __init__(self, events: list[dict]):
        self.events = events

    def __call__(self, url: str, timeout: int = 30):
        if "/summary/heatmap" in url:
            return {"buckets": []}
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        offset = int(query["offset"][0])
        limit = int(query["limit"][0])
        return {"events": self.events[offset : offset + limit]}


class GitScopeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("CANDYSTORE_URL", None)

    def run_collector(self, roots: list[Path], **options) -> dict:
        config = base_config(self.root)
        config["project_roots"] = [str(path) for path in roots]
        options.setdefault("candystore_url", "http://127.0.0.1:8683")
        section = {
            "id": "dev-activity",
            "title": "Developer Activity",
            "collector": "dev_activity",
            "required": True,
            "enabled": True,
            "max_age_hours": 24,
            "options": options,
        }
        with mock.patch.object(dev_activity, "fetch_json", FakeCandystore([event()])):
            result = dev_activity.collect(section, DATE, config)
        return validate_section_artifact(result.to_artifact("run-test", 24), "dev-activity")

    def caveats(self, artifact: dict) -> str:
        return "\n".join(artifact.get("caveats", []))

    def detail(self, artifact: dict) -> str:
        return "\n".join(artifact.get("detail", []))


class OffHeadCommitsTests(GitScopeTestCase):
    """The intelliforia case: the day's commit is not on the checked-out branch."""

    def repo_with_off_head_commit(self) -> Path:
        repo = make_repo(self.root / "code" / "intelliforia", ["chore: baseline"])
        commit(repo, "fix(staging): move to stg.intelliforia.com", name="staging.txt")
        git(repo, "checkout", "-q", "-b", "design/admin-portal-overhaul", "HEAD~1")
        return repo

    def test_a_commit_on_another_ref_is_counted_not_reported_as_no_commits(self) -> None:
        artifact = self.run_collector([self.repo_with_off_head_commit()])

        self.assertEqual(2, artifact["metrics"]["git_commit_count"])
        self.assertEqual(1, artifact["metrics"]["git_commits_off_head"])
        self.assertEqual(1, artifact["metrics"]["git_repos_logged"])
        self.assertEqual(0, artifact["metrics"]["git_repos_no_commits"])
        self.assertIn("fix(staging): move to stg.intelliforia.com", self.detail(artifact))
        self.assertNotIn("had no commits", self.caveats(artifact))

    def test_an_off_head_commit_is_marked_so_unmerged_work_cannot_look_landed(self) -> None:
        artifact = self.run_collector([self.repo_with_off_head_commit()])
        detail = self.detail(artifact)

        marked = [
            line
            for line in detail.splitlines()
            if "fix(staging)" in line and "not reachable from design/admin-portal-overhaul" in line
        ]
        self.assertEqual(1, len(marked), detail)
        self.assertIn("checked out: design/admin-portal-overhaul", detail)
        self.assertIn(
            "not reachable from their repository's checked-out branch", self.caveats(artifact)
        )

    def test_a_repository_read_at_head_only_never_claims_it_had_no_commits(self) -> None:
        """``git_scope: head`` is allowed -- silence about what it skips is not."""
        artifact = self.run_collector([self.repo_with_off_head_commit()], git_scope="head")

        self.assertEqual("head", artifact["metrics"]["git_scope"])
        self.assertEqual(1, artifact["metrics"]["git_commit_count"])
        self.assertNotIn("fix(staging)", self.detail(artifact))
        self.assertIn("the checked-out branch of each repository only", artifact["summary"])
        self.assertIn(
            "work on any branch not merged into it is absent from every git number",
            self.caveats(artifact),
        )


class ScopeIsAlwaysStatedTests(GitScopeTestCase):
    def test_the_summary_names_the_scope_of_its_commit_count(self) -> None:
        artifact = self.run_collector([make_repo(self.root / "code" / "widget", ["feat: one"])])

        self.assertIn("read across all refs of each repository", artifact["summary"])
        self.assertIn("1 on the checked-out branch, 0 only on other refs", artifact["summary"])

    def test_the_metrics_carry_the_scope_for_machine_consumers(self) -> None:
        artifact = self.run_collector([make_repo(self.root / "code" / "widget", ["feat: one"])])
        metrics = artifact["metrics"]

        self.assertEqual("all-refs", metrics["git_scope"])
        self.assertEqual(1, metrics["git_commits_on_head"])
        self.assertEqual(0, metrics["git_commits_off_head"])
        self.assertEqual(0, metrics["git_commit_replays_collapsed"])

    def test_the_scope_caveat_is_emitted_even_when_nothing_went_wrong(self) -> None:
        artifact = self.run_collector([make_repo(self.root / "code" / "widget", ["feat: one"])])

        self.assertEqual("complete", artifact["status"])
        self.assertIn("git scope is 'all-refs'", self.caveats(artifact))
        self.assertIn("refs/stash", self.caveats(artifact))

    def test_the_no_commits_caveat_states_what_was_searched(self) -> None:
        quiet = make_repo(self.root / "code" / "quiet", ["old work"], when="2026-01-02T09:00:00Z")
        artifact = self.run_collector([quiet])

        self.assertIn(
            "were read across all refs of each repository and had no commits",
            self.caveats(artifact),
        )

    def test_an_unusable_git_scope_is_reported_never_obeyed(self) -> None:
        artifact = self.run_collector(
            [make_repo(self.root / "code" / "widget", ["feat: one"])], git_scope="everything"
        )

        self.assertEqual("all-refs", artifact["metrics"]["git_scope"])
        self.assertIn("option git_scope='everything' is not one of", self.caveats(artifact))


class NoDoubleCountingTests(GitScopeTestCase):
    """Reading every ref must not make the day look busier than it was."""

    def test_a_commit_on_several_refs_is_counted_once(self) -> None:
        repo = make_repo(self.root / "code" / "widget", ["feat: shared"])
        git(repo, "branch", "release")
        git(repo, "branch", "backup")

        artifact = self.run_collector([repo])

        self.assertEqual(1, artifact["metrics"]["git_commit_count"])
        self.assertEqual(1, self.detail(artifact).count("feat: shared"))

    def test_the_same_sha_reached_from_two_refs_collapses_to_one_commit(self) -> None:
        """Directly, because git's own walk hides this end to end.

        ``git log --all`` already unifies a commit reachable from several refs,
        so an end-to-end test cannot tell whether this collector would. This one
        hands the renderer the duplicate git would hide.
        """
        duplicate = dev_activity.Commit(
            "sha1", "sha1abc", "2026-08-17T12:00:00Z", "feat: one", True
        )
        log = dev_activity._render_commits(
            [duplicate, duplicate._replace(on_head=False)], dev_activity.GIT_SCOPE_ALL, "main"
        )

        self.assertEqual(1, log.commits)
        self.assertEqual(1, log.on_head)
        self.assertEqual(0, log.off_head)
        self.assertEqual(1, log.text.count("feat: one"))

    def test_a_cherry_picked_copy_is_counted_once_and_the_collapse_is_recorded(self) -> None:
        # A same-day rebase: replayed onto a different base, so the copy gets a
        # new SHA while keeping the author date and the subject of the original.
        repo = make_repo(
            self.root / "code" / "widget", ["chore: base"], when="2026-01-02T09:00:00Z"
        )
        commit(repo, "feat: the work", name="work.txt")
        git(repo, "checkout", "-q", "-b", "rebased", "main~1")
        commit(repo, "chore: a different base", when="2026-01-03T09:00:00Z", name="other.txt")
        git(repo, *IDENTITY, "cherry-pick", "main", when=IN_WINDOW)
        git(repo, "checkout", "-q", "main")

        artifact = self.run_collector([repo])
        metrics = artifact["metrics"]

        self.assertEqual(1, metrics["git_commit_count"])
        self.assertEqual(1, metrics["git_commit_replays_collapsed"])
        self.assertIn("rebase or cherry-pick copies", self.caveats(artifact))
        self.assertIn("counted once, not twice", self.caveats(artifact))

    def test_a_stash_entry_is_not_a_commit_of_the_day(self) -> None:
        # Stashed inside the window: a stash entry IS a commit object, and it
        # lands on refs/stash, so only excluding that ref keeps it out.
        repo = make_repo(self.root / "code" / "widget", ["feat: the work"])
        (repo / "file0.txt").write_text("work in progress", encoding="utf-8")
        git(repo, *IDENTITY, "stash", "push", "-q", "-m", "wip: not a commit", when=IN_WINDOW)

        artifact = self.run_collector([repo])

        self.assertEqual(1, artifact["metrics"]["git_commit_count"])
        self.assertNotIn("wip: not a commit", self.detail(artifact))
        self.assertNotIn("WIP on main", self.detail(artifact))


class HeadEdgeCaseTests(GitScopeTestCase):
    def test_an_unborn_head_hides_no_commits_and_is_not_a_failure(self) -> None:
        """HEAD points at a branch with no commits; the refs still have the day."""
        repo = make_repo(self.root / "code" / "widget", ["feat: real work"])
        git(repo, "checkout", "-q", "--orphan", "fresh")
        git(repo, "reset", "-q", "--hard")

        artifact = self.run_collector([repo])

        self.assertEqual("complete", artifact["status"])
        self.assertEqual(1, artifact["metrics"]["git_commit_count"])
        self.assertEqual(1, artifact["metrics"]["git_commits_off_head"])
        self.assertIn("feat: real work", self.detail(artifact))

    def test_an_empty_repository_is_quiet_not_failed(self) -> None:
        repo = self.root / "code" / "empty"
        repo.mkdir(parents=True)
        git(repo, "init", "-q", "-b", "main", ".")

        artifact = self.run_collector([repo])

        self.assertEqual("complete", artifact["status"])
        self.assertEqual(1, artifact["metrics"]["git_repos_no_commits"])
        self.assertEqual(0, artifact["metrics"]["git_repos_failed"])


if __name__ == "__main__":
    unittest.main()
