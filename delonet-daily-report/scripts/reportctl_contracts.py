"""Strict stdlib validators for DeLoNET Daily Report artifacts."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from reportctl_security import contains_secret, is_safe_https_url

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ConfigError(ValueError):
    pass


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def strict_object(value: Any, required: set[str], allowed: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{where} must be an object")
    missing, extra = required - set(value), set(value) - allowed
    if missing or extra:
        raise ConfigError(
            f"{where} contract mismatch (missing={sorted(missing)}, extra={sorted(extra)})"
        )
    return value


def parse_iso(value: Any, where: str, date_only: bool = False) -> dt.date | dt.datetime:
    if not nonempty(value):
        raise ConfigError(f"{where} must be non-empty ISO date/time")
    try:
        parsed = (
            dt.date.fromisoformat(value)
            if date_only
            else dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        )
        if isinstance(parsed, dt.datetime) and parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed
    except ValueError as exc:
        raise ConfigError(f"{where} must be valid ISO date/time") from exc


def valid_url(value: Any) -> bool:
    return is_safe_https_url(value)


def validate_section_artifact(value: Any, topic_id: str | None = None) -> dict[str, Any]:
    if contains_secret(value):
        raise ConfigError("SectionArtifact contains secret-like material")
    required = {
        "schema_version",
        "run_id",
        "topic_id",
        "generated_at",
        "fresh_until",
        "status",
        "summary",
        "findings",
        "sources",
        "caveats",
    }
    artifact = strict_object(value, required, required, "SectionArtifact")
    if artifact["schema_version"] != 1 or not all(
        nonempty(artifact[key]) for key in ("run_id", "topic_id", "summary")
    ):
        raise ConfigError("SectionArtifact version and required strings are invalid")
    if not ID_RE.fullmatch(artifact["topic_id"]) or (topic_id and artifact["topic_id"] != topic_id):
        raise ConfigError("SectionArtifact topic_id is invalid")
    parse_iso(artifact["generated_at"], "generated_at")
    parse_iso(artifact["fresh_until"], "fresh_until")
    if artifact["status"] not in {"complete", "partial", "stale", "failed"}:
        raise ConfigError("SectionArtifact status is invalid")
    if not all(isinstance(artifact[key], list) for key in ("findings", "sources", "caveats")):
        raise ConfigError("SectionArtifact arrays are invalid")
    for index, finding in enumerate(artifact["findings"]):
        finding = strict_object(
            finding,
            {"claim", "significance", "source_urls"},
            {"claim", "significance", "source_urls"},
            f"findings[{index}]",
        )
        if (
            not nonempty(finding["claim"])
            or not nonempty(finding["significance"])
            or not isinstance(finding["source_urls"], list)
            or not all(valid_url(url) for url in finding["source_urls"])
        ):
            raise ConfigError(f"findings[{index}] is invalid")
    source_keys = {"url", "title", "publisher", "published_at", "retrieved_at"}
    for index, source in enumerate(artifact["sources"]):
        source = strict_object(source, {"url", "retrieved_at"}, source_keys, f"sources[{index}]")
        if not valid_url(source["url"]) or any(
            key in source and source[key] is not None and not nonempty(source[key])
            for key in ("title", "publisher", "published_at")
        ):
            raise ConfigError(f"sources[{index}] is invalid")
        parse_iso(source["retrieved_at"], f"sources[{index}].retrieved_at")
        if source.get("published_at") is not None:
            parse_iso(source["published_at"], f"sources[{index}].published_at")
    if not all(nonempty(item) for item in artifact["caveats"]):
        raise ConfigError("caveats must contain non-empty strings")
    return artifact


def validate_daily_report(value: Any, config: dict[str, Any]) -> dict[str, Any]:
    if contains_secret(value):
        raise ConfigError("DailyReport contains secret-like material")
    required = {
        "schema_version",
        "run_id",
        "report_date",
        "title",
        "generated_at",
        "sections",
        "coverage",
        "markdown_path",
    }
    report = strict_object(value, required, required, "DailyReport")
    if report["schema_version"] != 1 or not all(
        nonempty(report[key]) for key in ("run_id", "title", "markdown_path")
    ):
        raise ConfigError("DailyReport version and required strings are invalid")
    parse_iso(report["report_date"], "report_date", True)
    parse_iso(report["generated_at"], "generated_at")
    if not isinstance(report["sections"], list):
        raise ConfigError("DailyReport.sections must be an array")
    active = [item["id"] for item in config["topics"] if item["enabled"]]
    expected = [item["id"] for item in config["core_sections"]] + active
    actual = []
    for index, section in enumerate(report["sections"]):
        section = strict_object(
            section,
            {"id", "title", "body"},
            {"id", "title", "body", "source_urls"},
            f"sections[{index}]",
        )
        if (
            not all(nonempty(section[key]) for key in ("id", "title", "body"))
            or not isinstance(section.get("source_urls", []), list)
            or not all(valid_url(url) for url in section.get("source_urls", []))
        ):
            raise ConfigError(f"sections[{index}] is invalid")
        actual.append(section["id"])
    if actual != expected or len(actual) != len(set(actual)):
        raise ConfigError(
            "DailyReport sections must exactly match core_sections then active topics"
        )
    coverage = strict_object(
        report["coverage"], {"complete", "degraded"}, {"complete", "degraded"}, "coverage"
    )
    if not all(
        isinstance(coverage[key], list) and all(nonempty(item) for item in coverage[key])
        for key in coverage
    ):
        raise ConfigError("DailyReport coverage arrays are invalid")
    complete, degraded = coverage["complete"], coverage["degraded"]
    if len(complete) != len(set(complete)) or len(degraded) != len(set(degraded)):
        raise ConfigError("DailyReport coverage IDs must be unique")
    if set(complete) & set(degraded) or set(complete) | set(degraded) != set(active):
        raise ConfigError("DailyReport coverage must partition every active topic exactly once")
    return report


def validate_run_manifest(value: Any, config: dict[str, Any]) -> dict[str, Any]:
    if contains_secret(value):
        raise ConfigError("RunManifest contains secret-like material")
    required = {"schema_version", "run_id", "report_date", "started_at", "completed_at", "sections"}
    manifest = strict_object(value, required, required, "RunManifest")
    if manifest["schema_version"] != 1 or not nonempty(manifest["run_id"]):
        raise ConfigError("RunManifest version/run_id is invalid")
    parse_iso(manifest["report_date"], "report_date", True)
    parse_iso(manifest["started_at"], "started_at")
    parse_iso(manifest["completed_at"], "completed_at")
    if not isinstance(manifest["sections"], list):
        raise ConfigError("RunManifest.sections must be an array")
    expected = [item["id"] for item in config["topics"] if item["enabled"]]
    actual = []
    for index, section in enumerate(manifest["sections"]):
        section = strict_object(
            section,
            {"id", "status", "path"},
            {"id", "status", "path", "reason"},
            f"manifest.sections[{index}]",
        )
        if not nonempty(section["id"]) or section["status"] not in {
            "complete",
            "partial",
            "missing",
            "invalid",
            "stale",
            "failed",
        }:
            raise ConfigError(f"manifest.sections[{index}] is invalid")
        if section["path"] is not None and not nonempty(section["path"]):
            raise ConfigError(f"manifest.sections[{index}].path is invalid")
        if "reason" in section and not nonempty(section["reason"]):
            raise ConfigError(f"manifest.sections[{index}].reason is invalid")
        actual.append(section["id"])
    if actual != expected or len(actual) != len(set(actual)):
        raise ConfigError("RunManifest must cover active topics exactly once in config order")
    return manifest
