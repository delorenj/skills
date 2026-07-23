"""Strict operator configuration loading and validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from reportctl_contracts import ConfigError
from reportctl_security import contains_secret, is_safe_https_url

SUPPORTED_TIMEZONE = "America/New_York"
DAILY_SCHEDULE = "0 7 * * *"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DAILY_CRON_RE = re.compile(r"^(\d{1,2}) (\d{1,2}) \* \* \*$")
ENV_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
SCRIPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:py|sh|bash)$")
DEFAULT_SECTIONS_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "default-core-sections.json"
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read JSON {path}: {exc}") from exc


def is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_keys(value: dict[str, Any], allowed: set[str], where: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise ConfigError(f"{where}: unknown keys: {', '.join(sorted(extra))}")


def validate_daily_cron(schedule: str, where: str) -> None:
    match = DAILY_CRON_RE.fullmatch(schedule)
    if not match or int(match.group(1)) > 59 or int(match.group(2)) > 23:
        raise ConfigError(f"{where} must be a simple five-field daily cron schedule")


def validate_topic(topic: Any, index: int = 0) -> None:
    where = f"topics[{index}]"
    if not isinstance(topic, dict):
        raise ConfigError(f"{where} must be an object")
    require_keys(
        topic, {"id", "title", "prompt", "schedule", "enabled", "sources", "secret_env", "script"}, where
    )
    for key in ("id", "title", "prompt", "schedule"):
        if not nonempty(topic.get(key)):
            raise ConfigError(f"{where}.{key} must be a non-empty string")
    if not ID_RE.fullmatch(topic["id"]):
        raise ConfigError(f"{where}.id must be lowercase kebab-case")
    validate_daily_cron(topic["schedule"], f"{where}.schedule")
    if not is_bool(topic.get("enabled")):
        raise ConfigError(f"{where}.enabled must be boolean")
    sources = topic.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        raise ConfigError(f"{where}.sources must be an array of strings")
    if len(sources) != len(set(sources)):
        raise ConfigError(f"{where}.sources contains duplicates")
    for source in sources:
        if not is_safe_https_url(source):
            raise ConfigError(
                f"{where}.sources must be public https URLs without userinfo or query strings"
            )
    if contains_secret(topic["prompt"]):
        raise ConfigError(f"{where}.prompt contains a literal secret-like value; use secret_env")
    envs = topic.get("secret_env", [])
    if not isinstance(envs, list) or not all(
        isinstance(item, str) and ENV_RE.fullmatch(item) for item in envs
    ):
        raise ConfigError(f"{where}.secret_env must contain environment-variable names")
    topic["secret_env"] = envs
    if "script" in topic and (
        not isinstance(topic["script"], str)
        or (topic["script"] and not SCRIPT_RE.fullmatch(topic["script"]))
    ):
        raise ConfigError(f"{where}.script must be empty or a safe scripts-directory filename")


def validate_config(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ConfigError("config must be a JSON object")
    require_keys(
        config,
        {
            "version",
            "timezone",
            "inference",
            "artifact_dir",
            "archive_dir",
            "max_age_hours",
            "core_sections",
            "daily",
            "topics",
        },
        "config",
    )
    required = {
        "version",
        "timezone",
        "inference",
        "artifact_dir",
        "archive_dir",
        "core_sections",
        "daily",
        "topics",
    }
    missing = required - set(config)
    if missing:
        raise ConfigError(f"config: missing keys: {', '.join(sorted(missing))}")
    if config["version"] != 1:
        raise ConfigError("version must be 1")
    for key in ("timezone", "artifact_dir", "archive_dir"):
        if not isinstance(config[key], str) or not config[key].strip():
            raise ConfigError(f"{key} must be a non-empty string")
    if config["timezone"] != SUPPORTED_TIMEZONE:
        raise ConfigError(
            f"timezone must be {SUPPORTED_TIMEZONE}; Hermes cron has no per-job timezone"
        )
    inference = config["inference"]
    if not isinstance(inference, dict):
        raise ConfigError("inference must be an object")
    require_keys(inference, {"provider", "model"}, "inference")
    if not nonempty(inference.get("provider")) or not nonempty(inference.get("model")):
        raise ConfigError("inference.provider and inference.model must be non-empty strings")
    if (
        not Path(config["artifact_dir"]).is_absolute()
        or not Path(config["archive_dir"]).is_absolute()
    ):
        raise ConfigError("artifact_dir and archive_dir must be absolute")
    age = config.get("max_age_hours", 24)
    if not isinstance(age, int) or is_bool(age) or not 1 <= age <= 168:
        raise ConfigError("max_age_hours must be an integer from 1 to 168")
    config["max_age_hours"] = age
    daily = config["daily"]
    if not isinstance(daily, dict):
        raise ConfigError("daily must be an object")
    require_keys(daily, {"enabled", "schedule", "deliver", "workdir", "script"}, "daily")
    if (
        not is_bool(daily.get("enabled"))
        or not nonempty(daily.get("schedule"))
        or not nonempty(daily.get("deliver"))
    ):
        raise ConfigError("daily requires boolean enabled and non-empty schedule/deliver")
    if daily["schedule"] != DAILY_SCHEDULE:
        raise ConfigError(f"daily.schedule must be {DAILY_SCHEDULE} (07:00 America/New_York)")
    if "workdir" in daily and (
        not isinstance(daily["workdir"], str)
        or (daily["workdir"] and not Path(daily["workdir"]).is_absolute())
    ):
        raise ConfigError("daily.workdir must be empty or absolute")
    if "script" in daily and (
        not isinstance(daily["script"], str)
        or (daily["script"] and not SCRIPT_RE.fullmatch(daily["script"]))
    ):
        raise ConfigError("daily.script must be empty or a safe scripts-directory filename")
    sections = config["core_sections"]
    if not isinstance(sections, list) or not sections:
        raise ConfigError("core_sections must be a non-empty array")
    section_ids: set[str] = set()
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ConfigError(f"core_sections[{index}] must be an object")
        require_keys(section, {"id", "title", "required"}, f"core_sections[{index}]")
        if (
            not ID_RE.fullmatch(section.get("id", ""))
            or not nonempty(section.get("title"))
            or not is_bool(section.get("required"))
        ):
            raise ConfigError(
                f"core_sections[{index}] requires kebab id, title, and boolean required"
            )
        if section["id"] in section_ids:
            raise ConfigError(f"duplicate core section id: {section['id']}")
        section_ids.add(section["id"])
    if "coverage-freshness" not in section_ids:
        raise ConfigError("core_sections must include coverage-freshness")
    default_ids = {section["id"] for section in load_json(DEFAULT_SECTIONS_PATH)}
    if not default_ids.issubset(section_ids):
        raise ConfigError(
            f"core_sections must include shipped defaults: {', '.join(sorted(default_ids))}"
        )
    topics = config["topics"]
    if not isinstance(topics, list):
        raise ConfigError("topics must be an array")
    seen: set[str] = set()
    for index, topic in enumerate(topics):
        validate_topic(topic, index)
        if topic["id"] in seen:
            raise ConfigError(f"duplicate topic id: {topic['id']}")
        seen.add(topic["id"])
    return config
