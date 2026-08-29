from __future__ import annotations

from pathlib import Path


def config(root: Path) -> dict:
    """A minimal but realistic schema v2 configuration."""
    return {
        "version": 2,
        "timezone": "America/New_York",
        "artifact_dir": str(root / "artifacts"),
        "archive_dir": str(root / "archive"),
        "max_age_hours": 24,
        "core_sections": [
            {"id": "executive-brief", "title": "Executive Brief", "required": True},
            {"id": "key-changes", "title": "Key Changes", "required": True},
            {"id": "risks-watchlist", "title": "Risks and Watchlist", "required": True},
            {"id": "coverage-freshness", "title": "Coverage and Freshness", "required": True},
        ],
        "narrator": {"enabled": True, "provider": "openai-codex", "model": "gpt-5.4"},
        "project_roots": [str(root / "code" / "33GOD")],
        "sections": [
            {
                "id": "dev-activity",
                "title": "Developer Activity",
                "collector": "dev_activity",
                "required": True,
                "enabled": True,
                "max_age_hours": 24,
                "options": {"candystore_url": "http://127.0.0.1:8683"},
            },
            {
                "id": "fleet-health",
                "title": "Hermes Fleet Health",
                "collector": "fleet_health",
                "required": False,
                "enabled": True,
                "max_age_hours": 24,
                "options": {},
            },
        ],
    }


def local_artifact(fresh_until: str, section_id: str = "dev-activity") -> dict:
    """What a local collector emits: metrics and detail, no URLs at all."""
    return {
        "schema_version": 2,
        "run_id": "run-1",
        "topic_id": section_id,
        "generated_at": "2026-08-17T10:00:00Z",
        "fresh_until": fresh_until,
        "status": "complete",
        "summary": "14 commits across 3 repositories.",
        "metrics": {"commits": 14, "repositories": 3, "candystore_reachable": True},
        "detail": ["=== 33GOD ===", "abc1234 chore(fleet): pin momo scaffold"],
        "caveats": ["Two repositories had no commits in the window."],
    }


def sourced_artifact(fresh_until: str, section_id: str = "dev-activity") -> dict:
    """The remote-source shape, still valid in v2."""
    artifact = local_artifact(fresh_until, section_id)
    artifact.pop("metrics")
    artifact.pop("detail")
    artifact["findings"] = [
        {
            "claim": "A release shipped.",
            "significance": "Improves reliability.",
            "source_urls": ["https://example.org/releases/1"],
        }
    ]
    artifact["sources"] = [
        {
            "url": "https://example.org/releases/1",
            "title": "Release",
            "publisher": "Example",
            "published_at": "2026-08-17T09:00:00Z",
            "retrieved_at": "2026-08-17T10:00:00Z",
        }
    ]
    return artifact


def manifest(statuses: dict[str, str] | None = None) -> dict:
    statuses = statuses or {"dev-activity": "complete", "fleet-health": "complete"}
    return {
        "schema_version": 1,
        "run_id": "run-1",
        "report_date": "2026-08-17",
        "started_at": "2026-08-17T10:00:00Z",
        "completed_at": "2026-08-17T10:01:00Z",
        "sections": [
            {"id": section_id, "status": status, "path": f"/tmp/{section_id}.json"}
            for section_id, status in statuses.items()
        ],
    }


def report(value: dict, title: str = "Daily Developer Report", degraded: list | None = None) -> dict:
    degraded = degraded or []
    complete = [
        section["id"]
        for section in value["sections"]
        if section["enabled"] and section["id"] not in degraded
    ]
    # One narrator-written lead, then each enabled collector. The four
    # core_sections are still validated in config and no longer projected.
    sections = [
        {
            "id": "summary",
            "title": "Summary",
            "body": "Body for Summary",
            "source_urls": [],
        }
    ] + [
        {
            "id": section["id"],
            "title": section["title"],
            "body": f"Body for {section['title']}",
            "source_urls": [],
        }
        for section in value["sections"]
        if section["enabled"]
    ]
    return {
        "schema_version": 1,
        "run_id": "run-1",
        "report_date": "2026-08-17",
        "title": title,
        "generated_at": "2026-08-17T11:00:00Z",
        "sections": sections,
        "coverage": {"complete": complete, "degraded": degraded},
        "markdown_path": "/pending/report.md",
    }
