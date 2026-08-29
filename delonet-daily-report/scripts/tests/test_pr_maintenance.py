"""Tests for the pr_maintenance collector.

The point of every one of these is the same: the collector must never claim a
completeness it did not achieve, and must keep "did not run", "ran and found
nothing", and "state unreadable" as three distinguishable facts.
"""

from __future__ import annotations

import json
from pathlib import Path

from collectors import pr_maintenance
from collectors.base import run_collector
from reportctl_contracts import validate_section_artifact
from test_fixtures import config as fixture_config

DATE = "2026-08-17"
CONFIG = {"timezone": "America/New_York", "max_age_hours": 24}
SLUG = "git-github.com-delorenj-mcp-server-trello.git-7bef4efbe7ba8cc5"
REMOTE = "git@github.com:delorenj/mcp-server-trello.git"


def section(state_dir: Path, **options) -> dict:
    return {
        "id": "pr-maintenance",
        "title": "Nightly PR Maintenance",
        "collector": "pr_maintenance",
        "required": False,
        "enabled": True,
        "max_age_hours": 24,
        "options": {"state_dir": str(state_dir), **options},
    }


def tick_doc(
    tick: int,
    completed_at: str,
    *,
    status: str = "complete",
    success: bool = True,
    candidates: list[dict] | None = None,
    outcomes: list[dict] | None = None,
    noop_streak: int = 0,
    version: int = 1,
    lifecycle: list[dict] | None = None,
    extra: dict | None = None,
) -> dict:
    """One tick summary.json, shaped exactly like the verified live files."""
    doc = {
        "version": version,
        "tick": tick,
        "run_id": f"tick-{tick:06d}-{completed_at.replace('-', '').replace(':', '')}",
        "started_at": completed_at,
        "completed_at": completed_at,
        "success": success,
        "repository": REMOTE,
        "automerge": False,
        "provider": "opencode",
        "provider_status": status,
        "provider_returncode": 0,
        "attempts": [{"kind": "provider_attempt", "phase": "invoke", "returncode": 0}],
        "action_outcomes": [],
        "merge_outcomes": outcomes if outcomes is not None else [],
        "lifecycle": lifecycle
        if lifecycle is not None
        else [
            {
                "type": "bloodbank.v1.repo.maintenance.completed",
                "event_id": "0dbcc4f6-7f15-596e-b6bf-754221910645",
                "publish_status": "skipped",
                "detail": "publisher disabled",
            }
        ],
        "result": {
            "schema_version": 1,
            "status": status,
            "summary": f"tick {tick} analysis",
            "actions": [],
            "merge_candidates": candidates if candidates is not None else [],
        },
        "resume": {
            "version": 1,
            "tick": tick,
            "status": status,
            "noop_streak": noop_streak,
            "marker": "a" * 64,
            "repository": REMOTE,
            "updated_at": completed_at,
        },
    }
    if extra:
        doc.update(extra)
    return doc


def candidate(number: int, **overrides) -> dict:
    base = {
        "number": number,
        "ci": "green",
        "coverage": "unknown",
        "disposition": "keep",
        "grade": "good",
        "draft": False,
        "mergeable": True,
        "threads_resolved": True,
        "head_sha": "e2e916a115af8f738009e398c94ced7d895ffa82",
    }
    base.update(overrides)
    return base


def build_state(
    root: Path,
    ticks: list[dict],
    *,
    slug: str = SLUG,
    journal_runs: list[dict] | None = None,
    latest: dict | None = None,
    skip_run_dirs: set[int] | None = None,
) -> Path:
    """Write a pr-crusher state tree; return the state directory."""
    repo = root / "repos" / slug
    (repo / "runs").mkdir(parents=True, exist_ok=True)
    skip = skip_run_dirs or set()
    for doc in ticks:
        if doc["tick"] in skip:
            continue
        run_dir = repo / "runs" / doc["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "summary.json").write_text(json.dumps(doc), encoding="utf-8")
    newest = latest if latest is not None else (ticks[-1] if ticks else tick_doc(1, "2026-01-01T00:00:00Z"))
    (repo / "summary.json").write_text(json.dumps(newest), encoding="utf-8")
    runs = journal_runs
    if runs is None:
        runs = [
            {"at": doc["completed_at"], "phase": "completed", "run_id": doc["run_id"], "tick": doc["tick"], "success": doc["success"]}
            for doc in ticks
        ]
    (repo / "journal.json").write_text(
        json.dumps(
            {
                "version": 1,
                "repository": REMOTE,
                "github_repository": "delorenj/mcp-server-trello",
                "runs": runs,
                "actions": [{"kind": "provider_attempt", "at": "2026-08-17T07:10:18Z"}],
            }
        ),
        encoding="utf-8",
    )
    return root


def run(state_dir: Path, date: str = DATE, config: dict | None = None, **options):
    return pr_maintenance.collect(section(state_dir, **options), date, config or CONFIG)


# --------------------------------------------------------------------------- #
# happy path
# --------------------------------------------------------------------------- #


def test_happy_path_reports_complete_with_real_counts(tmp_path):
    state = build_state(
        tmp_path,
        [
            tick_doc(19, "2026-08-16T07:14:50Z", candidates=[candidate(111)]),
            tick_doc(
                20,
                "2026-08-17T07:10:55Z",
                status="noop",
                noop_streak=1,
                candidates=[candidate(111), candidate(115)],
                outcomes=[
                    {"number": 111, "allowed": False, "attempted": False, "reasons": ["automerge disabled"]},
                    {"number": 115, "allowed": False, "attempted": False, "reasons": ["automerge disabled"]},
                ],
            ),
            tick_doc(21, "2026-08-18T07:09:08Z", candidates=[candidate(111)]),
        ],
    )
    result = run(state)

    assert result.status == "complete"
    assert result.reason == ""
    assert result.metrics["repos_tracked"] == 1
    assert result.metrics["ticks_in_window"] == 1, "only the 2026-08-17 tick is in the window"
    assert result.metrics["prs_triaged"] == 2
    assert result.metrics["merge_candidates"] == 2
    assert result.metrics["merges_attempted"] == 0
    assert result.metrics["merges_completed"] == 0
    assert result.metrics["noop_streak"] == 1, "streak comes from the last in-window tick"
    assert result.metrics["ticks_noop"] == 1
    assert result.metrics["bloodbank_events_skipped"] == 1
    assert any("PR #115" in line for line in result.detail)
    assert any("delorenj/mcp-server-trello" in line for line in result.detail)


def test_artifact_validates_against_the_section_contract(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z", candidates=[candidate(111)])])
    artifact = run(state).to_artifact("run-test", 24)
    assert validate_section_artifact(artifact, "pr-maintenance") == artifact
    assert artifact["status"] == "complete"
    assert artifact["schema_version"] == 2


def test_disabled_bloodbank_publisher_is_always_visible(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z")])
    caveats = " ".join(run(state).caveats)
    assert "publisher disabled" in caveats
    assert "Candystore" in caveats


def test_missing_publication_evidence_still_warns_about_candystore(tmp_path):
    """A day with no tick must still say why Candystore is silent."""
    state = build_state(tmp_path, [tick_doc(21, "2026-08-18T07:09:08Z")])
    caveats = " ".join(run(state).caveats)
    assert "Candystore" in caveats


def test_collect_accepts_the_keyword_aliases(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z")])
    result = pr_maintenance.collect(section=section(state), date=DATE, config=CONFIG)
    assert result.status == "complete"


def test_window_follows_the_configured_timezone(tmp_path):
    """03:00Z on the 18th is still the 17th in America/New_York."""
    state = build_state(tmp_path, [tick_doc(20, "2026-08-18T03:30:00Z")])
    assert run(state).metrics["ticks_in_window"] == 1
    utc = run(state, config={"timezone": "UTC"})
    assert utc.metrics["ticks_in_window"] == 0
    assert "did not run" in utc.summary


# --------------------------------------------------------------------------- #
# the three facts that must stay apart
# --------------------------------------------------------------------------- #


def test_did_not_run_is_complete_not_failed(tmp_path):
    state = build_state(tmp_path, [tick_doc(21, "2026-08-18T07:09:08Z")])
    result = run(state)
    assert result.status == "complete"
    assert "did not run" in result.summary
    assert result.metrics["ticks_in_window"] == 0
    assert result.metrics["prs_triaged"] == 0


def test_ran_and_found_nothing_is_distinguishable_from_did_not_run(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z", status="noop", noop_streak=3)])
    result = run(state)
    assert result.status == "complete"
    assert "did not run" not in result.summary
    assert result.metrics["ticks_in_window"] == 1
    assert result.metrics["prs_triaged"] == 0
    assert result.metrics["noop_streak"] == 3


def test_no_repositories_tracked_is_complete_and_says_so(tmp_path):
    (tmp_path / "repos").mkdir(parents=True)
    result = run(tmp_path)
    assert result.status == "complete"
    assert result.metrics["repos_tracked"] == 0
    assert "tracks no repositories" in result.summary


# --------------------------------------------------------------------------- #
# unreachable sources -> failed, never an exception
# --------------------------------------------------------------------------- #


def test_missing_state_directory_fails_without_raising(tmp_path):
    result = run(tmp_path / "does-not-exist")
    assert result.status == "failed"
    assert "does not exist" in result.reason
    assert "does-not-exist" in result.reason
    assert "unknown" in result.summary


def test_missing_repos_directory_fails(tmp_path):
    (tmp_path / "unrelated").mkdir()
    result = run(tmp_path)
    assert result.status == "failed"
    assert "repos" in result.reason


def test_state_directory_that_is_a_file_fails(tmp_path):
    path = tmp_path / "pr-crusher"
    path.write_text("not a directory", encoding="utf-8")
    result = run(path)
    assert result.status == "failed"


def test_every_repository_unreadable_fails(tmp_path):
    (tmp_path / "repos" / SLUG).mkdir(parents=True)
    result = run(tmp_path)
    assert result.status == "failed"
    assert "no tracked repository" in result.reason


def test_run_collector_turns_a_hostile_config_into_failed_not_a_crash(tmp_path):
    hostile = {"id": "pr-maintenance", "options": {"state_dir": 12345}}
    result = run_collector(lambda cfg: pr_maintenance.collect(cfg, DATE, CONFIG), hostile)
    assert result.status == "failed"
    assert result.id == "pr-maintenance"


def test_bad_report_date_fails_with_a_reason(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z")])
    result = run(state, date="17-08-2026")
    assert result.status == "failed"
    assert "ISO" in result.reason


# --------------------------------------------------------------------------- #
# partial data -> partial, never complete
# --------------------------------------------------------------------------- #


def test_corrupt_tick_file_degrades_to_partial(tmp_path):
    state = build_state(
        tmp_path,
        [
            tick_doc(20, "2026-08-17T07:10:55Z", candidates=[candidate(111)]),
            tick_doc(21, "2026-08-17T19:00:00Z", candidates=[candidate(115)]),
        ],
    )
    broken = next((state / "repos" / SLUG / "runs").glob("tick-000021-*")) / "summary.json"
    broken.write_text("{ truncated", encoding="utf-8")

    result = run(state)
    assert result.status == "partial"
    assert "could not be used" in result.reason
    assert any("not valid JSON" in item for item in result.caveats)
    assert result.metrics["state_files_unusable"] == 1
    assert result.metrics["ticks_in_window"] == 1, "the readable tick is still reported"


def test_tick_in_journal_without_a_run_directory_degrades_to_partial(tmp_path):
    docs = [
        tick_doc(20, "2026-08-17T07:10:55Z", candidates=[candidate(111)]),
        tick_doc(21, "2026-08-17T19:00:00Z"),
    ]
    state = build_state(tmp_path, docs, skip_run_dirs={21}, latest=docs[0])
    result = run(state)
    assert result.status == "partial"
    assert "run directories" in result.reason
    assert result.metrics["ticks_in_window"] == 2, "a tick we know ran is never dropped"
    assert any("run directory is absent" in line for line in result.detail)


def test_unreadable_journal_alone_is_partial_not_failed(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z")])
    (state / "repos" / SLUG / "journal.json").write_text("[]", encoding="utf-8")
    result = run(state)
    assert result.status == "partial"
    assert result.metrics["ticks_in_window"] == 1


def test_tick_without_a_readable_completed_at_is_partial(tmp_path):
    doc = tick_doc(20, "2026-08-17T07:10:55Z")
    doc["completed_at"] = "whenever"
    state = build_state(tmp_path, [doc])
    result = run(state)
    assert result.status == "partial"
    assert any("completed_at" in item for item in result.caveats)


def test_unexpected_state_version_is_partial(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z", version=2)])
    result = run(state)
    assert result.status == "partial"
    assert any("state version" in item for item in result.caveats)


def test_attempted_merge_without_a_completion_record_is_partial(tmp_path):
    state = build_state(
        tmp_path,
        [
            tick_doc(
                20,
                "2026-08-17T07:10:55Z",
                candidates=[candidate(111)],
                outcomes=[{"number": 111, "allowed": True, "attempted": True, "reasons": []}],
            )
        ],
    )
    result = run(state)
    assert result.status == "partial"
    assert result.metrics["merges_attempted"] == 1
    assert result.metrics["merges_completed"] == 0, "never claim a merge the state cannot confirm"
    assert result.metrics["merges_unconfirmed"] == 1
    assert "cannot be confirmed" in result.reason


def test_one_unreadable_repository_out_of_two_is_partial(tmp_path):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z")])
    (state / "repos" / "git-github.com-delorenj-other.git-0000").mkdir(parents=True)
    result = run(state)
    assert result.status == "partial"
    assert "unreadable state" in result.reason
    assert result.metrics["repos_tracked"] == 2


# --------------------------------------------------------------------------- #
# pr-crusher's own failures are reported, not converted into collector failures
# --------------------------------------------------------------------------- #


def test_failed_tick_is_reported_loudly_but_the_read_was_complete(tmp_path):
    state = build_state(
        tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z", status="failed", success=False)]
    )
    result = run(state)
    assert result.status == "complete", "the collector read that failure successfully"
    assert result.metrics["ticks_failed"] == 1
    assert "1 tick(s) did not succeed" in result.summary


# --------------------------------------------------------------------------- #
# structural field allowlist
# --------------------------------------------------------------------------- #


def test_unknown_source_fields_never_reach_the_artifact(tmp_path):
    doc = tick_doc(20, "2026-08-17T07:10:55Z", candidates=[candidate(111)])
    doc["provider_env"] = {"GITHUB_TOKEN": "value-that-must-not-appear"}
    doc["transcript"] = ["another-value-that-must-not-appear"]
    doc["result"]["raw_response"] = "third-value-that-must-not-appear"
    state = build_state(tmp_path, [doc])

    rendered = json.dumps(run(state).to_artifact("run-test", 24))
    assert "must-not-appear" not in rendered
    assert "GITHUB_TOKEN" not in rendered
    assert "transcript" not in rendered
    assert "PR #111" in rendered


def test_repository_label_never_carries_userinfo(tmp_path):
    doc = tick_doc(20, "2026-08-17T07:10:55Z")
    doc["repository"] = "https://someone:supersecret@github.com/delorenj/mcp-server-trello.git"
    state = build_state(tmp_path, [doc], journal_runs=[])
    (state / "repos" / SLUG / "journal.json").write_text(
        json.dumps({"version": 1, "repository": doc["repository"], "runs": []}), encoding="utf-8"
    )
    rendered = json.dumps(run(state).to_artifact("run-test", 24))
    assert "supersecret" not in rendered
    assert "delorenj/mcp-server-trello" in rendered


# --------------------------------------------------------------------------- #
# standalone entry point
# --------------------------------------------------------------------------- #


def test_main_prints_a_valid_artifact_and_exits_zero_when_complete(tmp_path, capsys):
    state = build_state(tmp_path, [tick_doc(20, "2026-08-17T07:10:55Z", candidates=[candidate(111)])])
    code = pr_maintenance.main(["--date", DATE, "--state-dir", str(state)])
    artifact = json.loads(capsys.readouterr().out)
    assert validate_section_artifact(artifact, "pr-maintenance") == artifact
    assert artifact["status"] == "complete"
    assert code == 0


def test_main_exits_non_zero_when_the_source_is_unreachable(tmp_path, capsys):
    code = pr_maintenance.main(
        ["--date", DATE, "--state-dir", str(tmp_path / "gone")]
    )
    artifact = json.loads(capsys.readouterr().out)
    assert validate_section_artifact(artifact, "pr-maintenance") == artifact
    assert artifact["status"] == "failed"
    assert code == 2, "a cron agent must not be able to read this as success"


def test_main_reports_an_unusable_config_as_a_failed_artifact(tmp_path, capsys):
    bad = tmp_path / "report.json"
    bad.write_text('{"version": 1}', encoding="utf-8")
    code = pr_maintenance.main(["--date", DATE, "--config", str(bad)])
    artifact = json.loads(capsys.readouterr().out)
    assert artifact["status"] == "failed"
    assert code == 2


def test_main_uses_a_section_from_a_real_config(tmp_path, capsys):
    state = build_state(tmp_path / "state", [tick_doc(20, "2026-08-17T07:10:55Z")])
    config = fixture_config(tmp_path)
    config["sections"].append(
        {
            "id": "pr-maintenance",
            "title": "Nightly PR Maintenance",
            "collector": "pr_maintenance",
            "required": False,
            "enabled": True,
            "max_age_hours": 24,
            "options": {"state_dir": str(state)},
        }
    )
    path = tmp_path / "report.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    code = pr_maintenance.main(["--date", DATE, "--config", str(path)])
    artifact = json.loads(capsys.readouterr().out)
    assert validate_section_artifact(artifact, "pr-maintenance") == artifact
    assert artifact["status"] == "complete"
    assert code == 0


def test_the_collector_never_raises_for_any_of_these_inputs(tmp_path):
    """Whatever is thrown at it, a SectionResult comes back."""
    cases = [
        {},
        {"id": "pr-maintenance", "options": None},
        {"id": "pr-maintenance", "options": {"state_dir": str(tmp_path)}},
        {"id": "pr-maintenance", "options": {"state_dir": str(tmp_path), "max_tick_runs": -1}},
    ]
    for case in cases:
        result = pr_maintenance.collect(case, DATE, CONFIG)
        assert result.status in {"complete", "partial", "stale", "failed"}
        if result.status != "complete":
            assert result.reason


def test_a_flood_of_unusable_files_is_counted_exactly_and_listed_boundedly(tmp_path):
    docs = [tick_doc(n, f"2026-08-17T{n % 24:02d}:00:00Z") for n in range(1, 26)]
    state = build_state(tmp_path, docs)
    for path in (state / "repos" / SLUG / "runs").glob("tick-*/summary.json"):
        path.write_text("{ truncated", encoding="utf-8")

    result = run(state)
    assert result.status == "partial"
    assert result.metrics["state_files_unusable"] == 25, "the count is always exact"
    assert sum("not valid JSON" in item for item in result.caveats) == pr_maintenance.MAX_ERROR_CAVEATS
    assert any("further unusable state file" in item for item in result.caveats)
    validate_section_artifact(result.to_artifact("run-test", 24), "pr-maintenance")
