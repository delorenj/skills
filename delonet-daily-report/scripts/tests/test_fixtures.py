from pathlib import Path


def config(root: Path) -> dict:
    return {
        "version": 1,
        "timezone": "America/New_York",
        "inference": {"provider": "openai-codex", "model": "gpt-5.4"},
        "artifact_dir": str(root / "artifacts"),
        "archive_dir": str(root / "archive"),
        "max_age_hours": 24,
        "core_sections": [
            {"id": "executive-brief", "title": "Executive Brief", "required": True},
            {"id": "key-changes", "title": "Key Changes", "required": True},
            {"id": "risks-watchlist", "title": "Risks and Watchlist", "required": True},
            {"id": "coverage-freshness", "title": "Coverage and Freshness", "required": True},
        ],
        "daily": {"enabled": True, "schedule": "0 7 * * *", "deliver": "local"},
        "topics": [
            {
                "id": "ai-agents",
                "title": "AI Agents",
                "prompt": "Track material releases",
                "schedule": "15 6 * * *",
                "enabled": True,
                "sources": ["https://example.org/releases"],
                "secret_env": ["NEWS_API_TOKEN"],
            }
        ],
    }


def valid_artifact(fresh_until: str) -> dict:
    return {
        "schema_version": 1,
        "run_id": "run-1",
        "topic_id": "ai-agents",
        "generated_at": "2026-07-15T10:00:00Z",
        "fresh_until": fresh_until,
        "status": "complete",
        "summary": "Material release found.",
        "findings": [
            {
                "claim": "A release shipped.",
                "significance": "Improves reliability.",
                "source_urls": ["https://example.org/releases/1"],
            }
        ],
        "sources": [
            {
                "url": "https://example.org/releases/1",
                "title": "Release",
                "publisher": "Example",
                "published_at": "2026-07-15T09:00:00Z",
                "retrieved_at": "2026-07-15T10:00:00Z",
            }
        ],
        "caveats": ["Independent adoption data is unavailable."],
    }
