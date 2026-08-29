"""Strict stdlib validators for DeLoNET Daily Report artifacts.

Contract versions are independent. SectionArtifact moved to v2 when local
collectors were introduced: ``findings``/``sources`` became optional, ``metrics``
and ``detail`` were added, and a ``reason`` became mandatory whenever ``status``
is not ``complete``. That last rule is the point of the whole package: a section
may never claim a non-complete status without saying why.

RunManifest and DailyReport are unchanged and stay at v1.

There is no secret-regex scanner here by design. A denylist both false-positives
(which took this pipeline down on 2026-07-25) and misses novel token shapes.
Bounding is done structurally instead -- see ``collectors/base.allowlist``.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any
from urllib.parse import urlsplit

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

SECTION_ARTIFACT_VERSION = 2
RUN_MANIFEST_VERSION = 1
DAILY_REPORT_VERSION = 1

SECTION_STATUSES = frozenset({"complete", "partial", "stale", "failed"})
MANIFEST_STATUSES = frozenset(
    {"complete", "partial", "missing", "invalid", "stale", "failed"}
)
METRIC_VALUE_TYPES = (bool, int, float, str)


#: The narrator-authored lead, first section of every report.
LEAD_SECTION_ID = "summary"


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


def is_public_https_url(value: Any) -> bool:
    """Structural URL policy: https, a host, no userinfo, no query string.

    This inspects URL *structure* only. It never pattern-matches content.
    """
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
        and not parsed.query
    )


def valid_url(value: Any) -> bool:
    return is_public_https_url(value)


def active_section_ids(config: dict[str, Any]) -> list[str]:
    """Enabled sections, in config order. Coverage is enumerated from config,
    never from whatever happens to be on disk."""
    return [section["id"] for section in config["sections"] if section["enabled"]]


def required_section_ids(config: dict[str, Any]) -> list[str]:
    return [
        section["id"]
        for section in config["sections"]
        if section["enabled"] and section["required"]
    ]


def _validate_findings(findings: Any) -> None:
    if not isinstance(findings, list):
        raise ConfigError("SectionArtifact.findings must be an array")
    for index, finding in enumerate(findings):
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


def _validate_sources(sources: Any) -> None:
    if not isinstance(sources, list):
        raise ConfigError("SectionArtifact.sources must be an array")
    source_keys = {"url", "title", "publisher", "published_at", "retrieved_at"}
    for index, source in enumerate(sources):
        source = strict_object(source, {"url", "retrieved_at"}, source_keys, f"sources[{index}]")
        if not valid_url(source["url"]) or any(
            key in source and source[key] is not None and not nonempty(source[key])
            for key in ("title", "publisher", "published_at")
        ):
            raise ConfigError(f"sources[{index}] is invalid")
        parse_iso(source["retrieved_at"], f"sources[{index}].retrieved_at")
        if source.get("published_at") is not None:
            parse_iso(source["published_at"], f"sources[{index}].published_at")


def _validate_metrics(metrics: Any) -> None:
    if not isinstance(metrics, dict):
        raise ConfigError("SectionArtifact.metrics must be an object")
    for key, value in metrics.items():
        if not nonempty(key):
            raise ConfigError("SectionArtifact.metrics keys must be non-empty strings")
        if not isinstance(value, METRIC_VALUE_TYPES):
            raise ConfigError(
                f"SectionArtifact.metrics[{key}] must be a string, number, or boolean"
            )


def _validate_detail(detail: Any) -> None:
    if not isinstance(detail, list) or not all(isinstance(item, str) for item in detail):
        raise ConfigError("SectionArtifact.detail must be an array of strings")


def validate_section_artifact(value: Any, topic_id: str | None = None) -> dict[str, Any]:
    required = {
        "schema_version",
        "run_id",
        "topic_id",
        "generated_at",
        "fresh_until",
        "status",
        "summary",
        "caveats",
    }
    optional = {"findings", "sources", "metrics", "detail", "reason"}
    artifact = strict_object(value, required, required | optional, "SectionArtifact")
    if artifact["schema_version"] != SECTION_ARTIFACT_VERSION:
        raise ConfigError(
            f"SectionArtifact.schema_version must be {SECTION_ARTIFACT_VERSION}"
        )
    if not all(nonempty(artifact[key]) for key in ("run_id", "topic_id", "summary")):
        raise ConfigError("SectionArtifact required strings are invalid")
    if not ID_RE.fullmatch(artifact["topic_id"]) or (topic_id and artifact["topic_id"] != topic_id):
        raise ConfigError("SectionArtifact topic_id is invalid")
    parse_iso(artifact["generated_at"], "generated_at")
    parse_iso(artifact["fresh_until"], "fresh_until")
    if artifact["status"] not in SECTION_STATUSES:
        raise ConfigError("SectionArtifact status is invalid")
    if artifact["status"] != "complete" and not nonempty(artifact.get("reason")):
        raise ConfigError(
            f"SectionArtifact status {artifact['status']} requires a non-empty reason"
        )
    if "reason" in artifact and not nonempty(artifact["reason"]):
        raise ConfigError("SectionArtifact.reason must be a non-empty string when present")
    if not isinstance(artifact["caveats"], list) or not all(
        nonempty(item) for item in artifact["caveats"]
    ):
        raise ConfigError("caveats must contain non-empty strings")
    if "findings" in artifact:
        _validate_findings(artifact["findings"])
    if "sources" in artifact:
        _validate_sources(artifact["sources"])
    if "metrics" in artifact:
        _validate_metrics(artifact["metrics"])
    if "detail" in artifact:
        _validate_detail(artifact["detail"])
    return artifact


def validate_daily_report(value: Any, config: dict[str, Any]) -> dict[str, Any]:
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
    if report["schema_version"] != DAILY_REPORT_VERSION or not all(
        nonempty(report[key]) for key in ("run_id", "title", "markdown_path")
    ):
        raise ConfigError("DailyReport version and required strings are invalid")
    parse_iso(report["report_date"], "report_date", True)
    parse_iso(report["generated_at"], "generated_at")
    if not isinstance(report["sections"], list):
        raise ConfigError("DailyReport.sections must be an array")
    active = active_section_ids(config)
    # One narrator-written lead, then every enabled collector in config order.
    # This used to be `core_sections + active`; the four inherited core sections
    # restated the collector summaries twice above the collectors themselves.
    expected = [LEAD_SECTION_ID] + active
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
            f"DailyReport sections must be exactly {expected!r}, got {actual!r}"
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
        raise ConfigError("DailyReport coverage must partition every enabled section exactly once")
    return report


def validate_run_manifest(value: Any, config: dict[str, Any]) -> dict[str, Any]:
    required = {"schema_version", "run_id", "report_date", "started_at", "completed_at", "sections"}
    manifest = strict_object(value, required, required, "RunManifest")
    if manifest["schema_version"] != RUN_MANIFEST_VERSION or not nonempty(manifest["run_id"]):
        raise ConfigError("RunManifest version/run_id is invalid")
    parse_iso(manifest["report_date"], "report_date", True)
    parse_iso(manifest["started_at"], "started_at")
    parse_iso(manifest["completed_at"], "completed_at")
    if not isinstance(manifest["sections"], list):
        raise ConfigError("RunManifest.sections must be an array")
    expected = active_section_ids(config)
    actual = []
    for index, section in enumerate(manifest["sections"]):
        section = strict_object(
            section,
            {"id", "status", "path"},
            {"id", "status", "path", "reason"},
            f"manifest.sections[{index}]",
        )
        if not nonempty(section["id"]) or section["status"] not in MANIFEST_STATUSES:
            raise ConfigError(f"manifest.sections[{index}] is invalid")
        if section["path"] is not None and not nonempty(section["path"]):
            raise ConfigError(f"manifest.sections[{index}].path is invalid")
        if "reason" in section and not nonempty(section["reason"]):
            raise ConfigError(f"manifest.sections[{index}].reason is invalid")
        actual.append(section["id"])
    if actual != expected or len(actual) != len(set(actual)):
        raise ConfigError("RunManifest must cover enabled sections exactly once in config order")
    return manifest
