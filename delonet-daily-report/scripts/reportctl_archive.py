"""Daily report artifact health and archive operations."""

from __future__ import annotations

import copy
import datetime as dt
from pathlib import Path
from typing import Any

from reportctl_config import load_json
from reportctl_contracts import (
    ConfigError,
    parse_iso,
    validate_daily_report,
    validate_run_manifest,
    validate_section_artifact,
)
from reportctl_runtime import archive_paths, publish_archive_pair
from reportctl_security import contains_secret


def section_path(config: dict[str, Any], topic_id: str, date: str = "{date}") -> str:
    return str(Path(config["artifact_dir"]) / date / "sections" / f"{topic_id}.json")


def artifact_health(config: dict[str, Any], date: str) -> list[dict[str, str]]:
    archive_paths(config, date)
    now = dt.datetime.now(dt.UTC)
    result = []
    for topic in config["topics"]:
        if not topic["enabled"]:
            continue
        path = Path(section_path(config, topic["id"], date))
        status, reason = "missing", "file absent"
        if path.exists():
            try:
                artifact = validate_section_artifact(load_json(path), topic["id"])
                fresh = parse_iso(artifact["fresh_until"], "fresh_until")
                status, reason = (
                    ("stale", "fresh_until elapsed") if fresh < now else (artifact["status"], "")
                )
            except (ConfigError, ValueError, AttributeError) as exc:
                status, reason = "invalid", str(exc)
        result.append({"id": topic["id"], "status": status, "reason": reason, "path": str(path)})
    return result


def manifest_health(config: dict[str, Any], date: str) -> dict[str, str]:
    path = Path(archive_paths(config, date)["manifest"])
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    try:
        validate_run_manifest(load_json(path), config)
        return {"status": "valid", "path": str(path)}
    except ConfigError as exc:
        return {"status": "invalid", "reason": str(exc), "path": str(path)}


def archive_report(
    config: dict[str, Any],
    report_file: str,
    markdown_file: str,
    manifest_file: str | None = None,
) -> dict[str, Any]:
    report = validate_daily_report(load_json(Path(report_file)), config)
    paths = archive_paths(config, report["report_date"])
    manifest_path = Path(manifest_file) if manifest_file else Path(paths["manifest"])
    manifest = validate_run_manifest(load_json(manifest_path), config)
    if manifest["run_id"] != report["run_id"] or manifest["report_date"] != report["report_date"]:
        raise ConfigError("RunManifest and DailyReport run_id/report_date must match exactly")
    try:
        markdown = Path(markdown_file).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read Markdown {markdown_file}: {exc}") from exc
    if not markdown.strip():
        raise ConfigError("Markdown archive input must be non-empty")
    if contains_secret(markdown):
        raise ConfigError("Markdown contains secret-like material")
    archived = copy.deepcopy(report)
    archived["markdown_path"] = "report.md"
    return publish_archive_pair(
        Path(paths["archive_root"]), markdown, archived, manifest, report["report_date"]
    )
