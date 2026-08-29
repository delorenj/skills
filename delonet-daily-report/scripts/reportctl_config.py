"""Operator configuration (schema v2): loading, validation, atomic mutation.

v2 replaced news ``topics`` with collector-backed ``sections``. Each section
names a deterministic collector module instead of a prompt and a source list,
and coverage is always enumerated from this file -- never from whatever
artifacts happen to exist on disk.

Two rules here exist purely to make a false "complete" impossible:

* a section may not be ``required`` while ``enabled`` is false -- a required
  section that is never collected would make "every required section completed"
  vacuously true;
* at least one enabled section must be required, for the same reason.

A third rule protects the operator from a silently stale file: a schema v1
config (``topics``/``inference``/``daily``) is rejected with the exact command
that migrates it, and :func:`migrate_v1_to_v2` performs that migration. v1 has
no ``project_roots``, so migration refuses to invent them -- an invented root
set would understate developer activity while still reporting ``complete``.

A fourth rule is the same idea applied to ``enabled``. The live v1 config has
every topic ``enabled: false``: that is not a preference, it is the state
delonet died in on 2026-07-25, frozen into a file nobody has opened since. A
migration that carries those flags forward "faithfully" emits a config that
validates, prints ``"migrated": true``, and watches almost nothing -- a false
green manufactured by an honest-looking transformation. So migration does not
inherit that state by default: when any v1 topic is disabled the operator must
say what they meant with ``--disabled-topics enable`` or
``--disabled-topics preserve``, and a section that ends up disabled is shouted
on stderr and named in the result, never filed away in a notes array.

Disabling is also strictly worse than it looks: an *enabled* section whose
source is unreachable produces a ``failed`` artifact and degrades the report,
which is the pipeline correctly reporting bad news. A *disabled* section is not
in the coverage set at all, so nothing is ever missing and every run is green.

This module is also directly runnable::

    python3 scripts/reportctl_config.py migrate --config <v1> --out <v2> \
        --project-root /abs/repo [--project-root /abs/other] \
        --disabled-topics {enable|preserve}
    python3 scripts/reportctl_config.py validate --config <path>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from reportctl_contracts import ConfigError
from reportctl_runtime import atomic_write

CONFIG_VERSION = 2
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COLLECTOR_RE = re.compile(r"^[a-z][a-z0-9_]*$")
OPTION_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
OPTION_VALUE_TYPES = (bool, int, float, str)
DEFAULT_SECTIONS_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "default-core-sections.json"
)

CONFIG_KEYS = {
    "version",
    "timezone",
    "artifact_dir",
    "archive_dir",
    "max_age_hours",
    "core_sections",
    "narrator",
    "project_roots",
    "sections",
    "distribution",
}
SECTION_KEYS = {"id", "title", "collector", "required", "enabled", "max_age_hours", "options"}
OPTIONAL_CONFIG_KEYS = {"max_age_hours", "distribution"}

# --- schema v1 -> v2 migration -------------------------------------------------
V1_VERSION = 1
V1_MARKER_KEYS = {"topics", "inference", "daily"}
V1_CONFIG_KEYS = {
    "version",
    "timezone",
    "inference",
    "artifact_dir",
    "archive_dir",
    "max_age_hours",
    "core_sections",
    "daily",
    "topics",
}
V1_TOPIC_KEYS = {
    "id",
    "title",
    "prompt",
    "schedule",
    "enabled",
    "sources",
    "secret_env",
    "script",
}
# Every v1 topic maps onto exactly one v2 collector-backed section. A v1 topic
# with no mapping is an error, never a silent drop: a dropped topic is a source
# the operator configured and the report would stop covering without saying so.
V1_TOPIC_TO_SECTION = {
    "nightly-pr-maintenance": "pr-maintenance",
    "hermes-fleet-health": "fleet-health",
    "report-delivery-health": "report-delivery",
}
# v2 introduced this section; no v1 topic corresponds to it.
V2_ADDED_SECTION_IDS = ("dev-activity",)
#: What the operator can say about v1 topics that are disabled. There is no
#: default: "preserve" is what round 2 did implicitly, and it is exactly how a
#: dead config's state becomes a live config's coverage.
DISABLED_TOPIC_INTENTS = ("enable", "preserve")
EXAMPLE_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "example-config.v2.json"
)
MIGRATE_COMMAND = (
    "python3 {script} migrate --config <v1-config> --out <v2-config> "
    "--project-root /abs/path/to/repo [--project-root ...]"
).format(script=Path(__file__).resolve())


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


def validate_age(value: Any, where: str) -> int:
    if not isinstance(value, int) or is_bool(value) or not 1 <= value <= 168:
        raise ConfigError(f"{where} must be an integer from 1 to 168")
    return value


def validate_options(options: Any, where: str) -> dict[str, Any]:
    if not isinstance(options, dict):
        raise ConfigError(f"{where} must be an object")
    for key, value in options.items():
        if not isinstance(key, str) or not OPTION_KEY_RE.fullmatch(key):
            raise ConfigError(f"{where}.{key} must be a lower_snake_case key")
        if isinstance(value, list):
            if not all(isinstance(item, OPTION_VALUE_TYPES) for item in value):
                raise ConfigError(f"{where}.{key} array must hold strings, numbers, or booleans")
            continue
        if not isinstance(value, OPTION_VALUE_TYPES):
            raise ConfigError(
                f"{where}.{key} must be a string, number, boolean, or array of those"
            )
    return options


def validate_section(section: Any, index: int) -> dict[str, Any]:
    where = f"sections[{index}]"
    if not isinstance(section, dict):
        raise ConfigError(f"{where} must be an object")
    require_keys(section, SECTION_KEYS, where)
    missing = SECTION_KEYS - set(section)
    if missing:
        raise ConfigError(f"{where}: missing keys: {', '.join(sorted(missing))}")
    if not ID_RE.fullmatch(section["id"] if isinstance(section["id"], str) else ""):
        raise ConfigError(f"{where}.id must be lowercase kebab-case")
    if not nonempty(section.get("title")):
        raise ConfigError(f"{where}.title must be a non-empty string")
    if not isinstance(section["collector"], str) or not COLLECTOR_RE.fullmatch(
        section["collector"]
    ):
        raise ConfigError(f"{where}.collector must be a lower_snake_case module name")
    for key in ("required", "enabled"):
        if not is_bool(section.get(key)):
            raise ConfigError(f"{where}.{key} must be boolean")
    if section["required"] and not section["enabled"]:
        raise ConfigError(
            f"{where} cannot be required while disabled; a required section that is never "
            "collected would make an overall complete status vacuously true"
        )
    section["max_age_hours"] = validate_age(section["max_age_hours"], f"{where}.max_age_hours")
    validate_options(section["options"], f"{where}.options")
    return section


def validate_core_sections(sections: Any) -> list[str]:
    if not isinstance(sections, list) or not sections:
        raise ConfigError("core_sections must be a non-empty array")
    section_ids: list[str] = []
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ConfigError(f"core_sections[{index}] must be an object")
        require_keys(section, {"id", "title", "required"}, f"core_sections[{index}]")
        if (
            not ID_RE.fullmatch(section.get("id", "") if isinstance(section.get("id"), str) else "")
            or not nonempty(section.get("title"))
            or not is_bool(section.get("required"))
        ):
            raise ConfigError(
                f"core_sections[{index}] requires kebab id, title, and boolean required"
            )
        if section["id"] in section_ids:
            raise ConfigError(f"duplicate core section id: {section['id']}")
        section_ids.append(section["id"])
    if "coverage-freshness" not in section_ids:
        raise ConfigError("core_sections must include coverage-freshness")
    default_ids = {section["id"] for section in load_json(DEFAULT_SECTIONS_PATH)}
    if not default_ids.issubset(section_ids):
        raise ConfigError(
            f"core_sections must include shipped defaults: {', '.join(sorted(default_ids))}"
        )
    return section_ids



#: Where a published report is delivered. Optional: a config without it still
#: produces reports, they just stay on disk.
DISTRIBUTION_TARGETS = {"vault", "notebook", "email", "slack"}
_TARGET_KEYS = {
    "vault": {"enabled", "path", "git_commit"},
    "notebook": {"enabled", "base_url", "notebook_name"},
    "email": {"enabled", "to", "from", "mode", "subject_template"},
    "slack": {"enabled", "to", "from", "mode", "subject_template"},
}


def validate_distribution(distribution: Any) -> dict[str, Any]:
    """Validate delivery targets.

    Credentials are deliberately NOT part of this schema. A Resend key belongs
    in the environment or the vault, never in a config file that gets committed
    -- so there is no key field here to put one in by accident.
    """
    if not isinstance(distribution, dict):
        raise ConfigError("distribution must be an object")
    unknown = set(distribution) - DISTRIBUTION_TARGETS
    if unknown:
        raise ConfigError(f"distribution: unknown target(s): {', '.join(sorted(unknown))}")
    for name, cfg in distribution.items():
        if not isinstance(cfg, dict):
            raise ConfigError(f"distribution.{name} must be an object")
        extra = set(cfg) - _TARGET_KEYS[name]
        if extra:
            raise ConfigError(f"distribution.{name}: unknown key(s): {', '.join(sorted(extra))}")
        if "enabled" in cfg and not is_bool(cfg["enabled"]):
            raise ConfigError(f"distribution.{name}.enabled must be boolean")
        if not cfg.get("enabled"):
            continue
        if name == "vault" and not nonempty(cfg.get("path")):
            raise ConfigError("distribution.vault.path must be a non-empty string when enabled")
        if name in {"email", "slack"}:
            recipients = cfg.get("to")
            if not isinstance(recipients, list) or not recipients or not all(
                nonempty(r) and "@" in r for r in recipients
            ):
                raise ConfigError(f"distribution.{name}.to must be a non-empty list of addresses")
            if not nonempty(cfg.get("from")):
                raise ConfigError(f"distribution.{name}.from must be a non-empty string")
            if cfg.get("mode", "full") not in {"full", "digest"}:
                raise ConfigError(f"distribution.{name}.mode must be 'full' or 'digest'")
        if any(_looks_like_secret(v) for v in cfg.values() if isinstance(v, str)):
            raise ConfigError(
                f"distribution.{name}: a value looks like a credential. Keys belong in the "
                "environment (RESEND_API_KEY) or 1Password, never in this file"
            )
    return distribution


def _looks_like_secret(value: str) -> bool:
    return value.startswith(("re_", "xoxb-", "xoxp-", "sk-", "ghp_"))


def validate_narrator(narrator: Any) -> dict[str, Any]:
    if not isinstance(narrator, dict):
        raise ConfigError("narrator must be an object")
    require_keys(narrator, {"enabled", "provider", "model", "reasoning"}, "narrator")
    missing = {"enabled", "provider", "model"} - set(narrator)
    if missing:
        raise ConfigError(f"narrator: missing keys: {', '.join(sorted(missing))}")
    if not is_bool(narrator["enabled"]):
        raise ConfigError("narrator.enabled must be boolean")
    if not nonempty(narrator["provider"]) or not nonempty(narrator["model"]):
        raise ConfigError("narrator.provider and narrator.model must be non-empty strings")
    # Optional. This report runs once a day and is read by a human, so the
    # effort knob is exposed rather than left at whatever the provider defaults
    # to -- it is the cheapest quality lever in the pipeline.
    if "reasoning" in narrator:
        levels = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
        if narrator["reasoning"] not in levels:
            raise ConfigError(f"narrator.reasoning must be one of {sorted(levels)}")
    return narrator


def validate_project_roots(roots: Any) -> list[str]:
    if not isinstance(roots, list) or not roots:
        raise ConfigError("project_roots must be a non-empty array")
    seen: set[str] = set()
    for index, root in enumerate(roots):
        if not nonempty(root) or not Path(root).is_absolute():
            raise ConfigError(f"project_roots[{index}] must be an absolute path")
        if root in seen:
            raise ConfigError(f"duplicate project root: {root}")
        seen.add(root)
    return roots


def validate_config(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ConfigError("config must be a JSON object")
    legacy = v1_diagnosis(config)
    if legacy:
        raise ConfigError(legacy)
    require_keys(config, CONFIG_KEYS, "config")
    # `distribution` is optional: a config without it still produces reports,
    # they just stay on disk. Requiring it would break every config written
    # before delivery existed.
    missing = CONFIG_KEYS - OPTIONAL_CONFIG_KEYS - set(config)
    if missing:
        raise ConfigError(f"config: missing keys: {', '.join(sorted(missing))}")
    if config["version"] != CONFIG_VERSION:
        raise ConfigError(f"version must be {CONFIG_VERSION}")
    for key in ("timezone", "artifact_dir", "archive_dir"):
        if not nonempty(config[key]):
            raise ConfigError(f"{key} must be a non-empty string")
    try:
        ZoneInfo(config["timezone"])
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ConfigError(f"timezone must be a valid IANA zone: {config['timezone']}") from exc
    if (
        not Path(config["artifact_dir"]).is_absolute()
        or not Path(config["archive_dir"]).is_absolute()
    ):
        raise ConfigError("artifact_dir and archive_dir must be absolute")
    config["max_age_hours"] = validate_age(config.get("max_age_hours", 24), "max_age_hours")
    validate_core_sections(config["core_sections"])
    validate_narrator(config["narrator"])
    if "distribution" in config:
        validate_distribution(config["distribution"])
    validate_project_roots(config["project_roots"])
    sections = config["sections"]
    if not isinstance(sections, list) or not sections:
        raise ConfigError("sections must be a non-empty array")
    seen: set[str] = set()
    for index, section in enumerate(sections):
        validate_section(section, index)
        if section["id"] in seen:
            raise ConfigError(f"duplicate section id: {section['id']}")
        seen.add(section["id"])
    if not any(section["enabled"] and section["required"] for section in sections):
        raise ConfigError(
            "at least one enabled section must be required; without one, an overall "
            "complete status would be vacuously true"
        )
    return config


def load_config(path: Path) -> dict[str, Any]:
    return validate_config(load_json(Path(path).expanduser()))


def save_config(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Validate first, replace second. A config file is never left invalid."""
    validated = validate_config(config)
    atomic_write(Path(path).expanduser(), validated)
    return validated


def is_v1(config: Any) -> bool:
    """True when this document is a schema v1 config rather than a v2 one."""
    if not isinstance(config, dict):
        return False
    version = config.get("version")
    if version == V1_VERSION and not is_bool(version):
        return True
    return version != CONFIG_VERSION and bool(V1_MARKER_KEYS & set(config))


def v1_diagnosis(config: Any) -> str | None:
    """The actionable error text for a v1 config, or None when it is not v1.

    The failure this replaces was ``config: unknown keys: daily, inference,
    topics`` -- true, but it told the operator nothing about what to do, so the
    live config sat unmigrated and every documented command failed.
    """
    if not is_v1(config):
        return None
    markers = sorted(V1_MARKER_KEYS & set(config))
    found = f"found {config.get('version')!r}"
    keys = f" with v1 key(s): {', '.join(markers)}" if markers else ""
    return (
        f"config is schema v1 ({found}{keys}); version must be {CONFIG_VERSION}. "
        f"Migrate it, then validate the result:\n  {MIGRATE_COMMAND}\n"
        "  reportctl --config <v2-config> validate\n"
        "Migration cannot invent project_roots -- v1 has no equivalent key -- so "
        "pass every repository root the report must cover."
    )


def section_templates() -> dict[str, dict[str, Any]]:
    """Shipped v2 section defaults, keyed by section id."""
    example = load_json(EXAMPLE_CONFIG_PATH)
    if not isinstance(example, dict) or not isinstance(example.get("sections"), list):
        raise ConfigError(f"shipped example config is unusable: {EXAMPLE_CONFIG_PATH}")
    return {section["id"]: section for section in example["sections"]}


def _migrated_section(
    template: dict[str, Any], *, enabled: bool, title: str | None = None
) -> dict[str, Any]:
    section = json.loads(json.dumps(template))
    section["enabled"] = enabled
    # required is only meaningful for a section that actually gets collected.
    section["required"] = bool(template.get("required")) and enabled
    if title:
        section["title"] = title
    return section


def _resolve_disabled_intent(
    disabled: list[str], disabled_topics: str | None, enable_all: bool
) -> str:
    """Decide what to do with disabled v1 topics, or refuse to decide for them.

    ``enable_all=True`` is the older spelling of ``disabled_topics="enable"``
    and is kept so existing callers and docs keep working. What is NOT kept is
    the old default: silence used to mean "preserve", so the live config's three
    dead topics migrated forward disabled, the file validated, and the report
    covered one section out of four while reporting complete.
    """
    intent = "enable" if enable_all else disabled_topics
    if intent is not None and intent not in DISABLED_TOPIC_INTENTS:
        raise ConfigError(
            f"disabled_topics must be one of {', '.join(DISABLED_TOPIC_INTENTS)}; "
            f"got {intent!r}"
        )
    if not disabled:
        return intent or "enable"
    if intent is None:
        raise ConfigError(
            f"{len(disabled)} v1 topic(s) are disabled: {', '.join(disabled)}. "
            "Migration will not inherit that state for you -- 'all topics enabled: "
            "false' is the state delonet died in on 2026-07-25, and a config that "
            "watches nothing never reports anything missing. Say what you mean:\n"
            "  --disabled-topics enable    collect them. A section whose source is "
            "down reports that failure honestly; a disabled section reports nothing "
            "at all.\n"
            "  --disabled-topics preserve  keep them disabled deliberately. The "
            "migration will name every section the report stops covering."
        )
    return intent


def migrate_v1_to_v2(
    v1: Any,
    *,
    project_roots: list[str],
    disabled_topics: str | None = None,
    enable_all: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Convert a schema v1 config into a validated v2 config.

    Returns ``(config, notes)``. Every decision that changes what the report
    covers -- a topic carried over disabled, a section v2 added, a v1 block
    dropped -- appears in ``notes``; nothing is changed silently, and a topic
    that would be carried over disabled is not changed *at all* without
    ``disabled_topics``. See :func:`_resolve_disabled_intent`.
    """
    if not isinstance(v1, dict):
        raise ConfigError("config must be a JSON object")
    if not is_v1(v1):
        raise ConfigError(
            f"not a schema v1 config (version={v1.get('version')!r}); nothing to migrate"
        )
    require_keys(v1, V1_CONFIG_KEYS, "v1 config")
    if not isinstance(project_roots, list) or not project_roots:
        raise ConfigError(
            "migration requires at least one --project-root: schema v1 has no "
            "project_roots key, and inventing one would let the report claim "
            "'complete' while never reading a repository the operator cares about"
        )
    validate_project_roots(project_roots)

    inference = v1.get("inference")
    if not isinstance(inference, dict) or not {"provider", "model"} <= set(inference):
        raise ConfigError("v1 config: inference must be an object with provider and model")

    notes: list[str] = []
    templates = section_templates()
    topics = v1.get("topics", [])
    if not isinstance(topics, list):
        raise ConfigError("v1 config: topics must be an array")

    # Pass one resolves and validates every topic. Nothing is decided about
    # `enabled` yet: an unmapped topic must still be the error the operator
    # sees first, and the disabled-topic question is not answerable until the
    # whole topic list has been read.
    mapped: list[dict[str, Any]] = []
    claimed: set[str] = set()
    for index, topic in enumerate(topics):
        if not isinstance(topic, dict):
            raise ConfigError(f"v1 config: topics[{index}] must be an object")
        require_keys(topic, V1_TOPIC_KEYS, f"v1 config: topics[{index}]")
        topic_id = topic.get("id")
        section_id = V1_TOPIC_TO_SECTION.get(topic_id if isinstance(topic_id, str) else "")
        if section_id is None:
            raise ConfigError(
                f"v1 config: topics[{index}].id {topic_id!r} has no v2 collector; "
                f"known topics: {', '.join(sorted(V1_TOPIC_TO_SECTION))}. Migrating it "
                "away silently would drop a configured source from the report"
            )
        if section_id in claimed:
            raise ConfigError(f"v1 config: two topics map onto section {section_id}")
        claimed.add(section_id)
        template = templates.get(section_id)
        if template is None:
            raise ConfigError(f"shipped example config has no section {section_id}")
        mapped.append(
            {
                "index": index,
                "topic": topic,
                "topic_id": topic_id,
                "section_id": section_id,
                "template": template,
                "was_enabled": bool(topic.get("enabled")),
            }
        )

    intent = _resolve_disabled_intent(
        [item["topic_id"] for item in mapped if not item["was_enabled"]],
        disabled_topics,
        enable_all,
    )

    sections: list[dict[str, Any]] = []
    for item in mapped:
        topic, template = item["topic"], item["template"]
        enabled = True if intent == "enable" else item["was_enabled"]
        title = topic.get("title") if nonempty(topic.get("title")) else None
        sections.append(_migrated_section(template, enabled=enabled, title=title))
        notes.append(
            f"topic {item['topic_id']} -> section {item['section_id']} (collector "
            f"{template['collector']}, enabled={enabled}, "
            f"required={sections[-1]['required']})"
        )
        if not enabled:
            notes.append(
                f"WARNING: section {item['section_id']} is carried over DISABLED because "
                f"v1 topic {item['topic_id']} was disabled and the migration was run with "
                "--disabled-topics preserve; it will not be collected, it will not appear "
                "in coverage, and its absence will never make a run anything but complete"
            )
        elif not item["was_enabled"]:
            notes.append(
                f"ENABLED section {item['section_id']}: v1 topic {item['topic_id']} was "
                "disabled and --disabled-topics enable overrode that. A section that "
                "cannot reach its source now fails visibly instead of vanishing"
            )
        for dropped in ("prompt", "schedule", "sources", "secret_env", "script"):
            if topic.get(dropped):
                notes.append(
                    f"dropped topics[{item['index']}].{dropped}: v2 sections are "
                    "collector-backed, not prompt-and-source-backed"
                )

    for section_id in V2_ADDED_SECTION_IDS:
        if section_id in claimed:
            continue
        template = templates.get(section_id)
        if template is None:
            raise ConfigError(f"shipped example config has no section {section_id}")
        sections.append(_migrated_section(template, enabled=True))
        notes.append(
            f"ADDED section {section_id} (collector {template['collector']}): v2 introduced "
            "it and v1 had no equivalent topic; it is enabled and required"
        )

    # Present sections in the shipped order so a migrated report reads like the
    # documented one; the set is unchanged.
    order = {section_id: index for index, section_id in enumerate(templates)}
    sections.sort(key=lambda section: order.get(section["id"], len(order)))

    if v1.get("daily"):
        notes.append(
            "dropped the v1 'daily' block: scheduling now lives in the cron job that calls "
            "reportctl, not in this config"
        )

    config: dict[str, Any] = {
        "version": CONFIG_VERSION,
        "timezone": v1.get("timezone"),
        "artifact_dir": v1.get("artifact_dir"),
        "archive_dir": v1.get("archive_dir"),
        "max_age_hours": v1.get("max_age_hours", 24),
        "core_sections": v1.get("core_sections"),
        "narrator": {
            "enabled": True,
            "provider": inference.get("provider"),
            "model": inference.get("model"),
        },
        "project_roots": list(project_roots),
        "sections": sections,
    }
    notes.append(
        f"narrator carried over from v1 inference: {config['narrator']['provider']} "
        f"{config['narrator']['model']} (enabled)"
    )
    notes.append(f"project_roots set from {len(project_roots)} --project-root argument(s)")
    return validate_config(config), notes


def coverage_warning(config: dict[str, Any], destination: Path | str) -> str | None:
    """One sentence naming every section this config will never look at.

    ``None`` when nothing is disabled. This is deliberately computed from the
    final config rather than from the migration's decisions, so it is equally
    true of a config an operator hand-edited afterwards.
    """
    disabled = [section["id"] for section in config["sections"] if not section["enabled"]]
    if not disabled:
        return None
    return (
        f"{len(disabled)} section(s) are DISABLED and will not be collected: "
        f"{', '.join(sorted(disabled))}. They are not part of coverage, so no run will "
        "ever report them missing and every run can still be 'complete'. Enable them in "
        f"{destination}, or accept that the report does not cover them."
    )


def migrate_config_file(
    source: Path,
    destination: Path,
    *,
    project_roots: list[str],
    disabled_topics: str | None = None,
    enable_all: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Migrate a v1 file to a v2 file. Never overwrites without ``force``.

    The result names what the migrated config covers and what it does not, at
    the top level. Burying "section X will not be collected" in a notes array
    is how a migration reports success at producing an inert config.
    """
    source = Path(source).expanduser()
    destination = Path(destination).expanduser()
    if destination.exists() and not force:
        raise ConfigError(f"refusing to overwrite {destination} without --force")
    if destination.resolve() == source.resolve():
        raise ConfigError("--out must differ from --config; migrate to a new file")
    config, notes = migrate_v1_to_v2(
        load_json(source),
        project_roots=project_roots,
        disabled_topics=disabled_topics,
        enable_all=enable_all,
    )
    save_config(destination, config)
    return {
        "migrated": True,
        "source": str(source),
        "destination": str(destination),
        "from_version": V1_VERSION,
        "to_version": CONFIG_VERSION,
        "sections": [
            {"id": s["id"], "enabled": s["enabled"], "required": s["required"]}
            for s in config["sections"]
        ],
        "enabled_sections": [s["id"] for s in config["sections"] if s["enabled"]],
        "disabled_sections": [s["id"] for s in config["sections"] if not s["enabled"]],
        "coverage_warning": coverage_warning(config, destination),
        "warnings": [note for note in notes if note.startswith("WARNING")],
        "notes": notes,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="reportctl_config",
        description="Validate a config, or migrate one from schema v1 to v2.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate", help="validate a config against schema v2")
    check.add_argument("--config", required=True)
    move = commands.add_parser("migrate", help="convert a schema v1 config into a v2 config")
    move.add_argument("--config", required=True, help="the v1 config to read (never written)")
    move.add_argument("--out", required=True, help="destination path for the v2 config")
    move.add_argument(
        "--project-root",
        action="append",
        default=[],
        dest="project_roots",
        help="absolute repository root the report must cover; repeatable, required",
    )
    move.add_argument(
        "--disabled-topics",
        choices=DISABLED_TOPIC_INTENTS,
        default=None,
        dest="disabled_topics",
        help=(
            "what to do with v1 topics that are disabled: 'enable' collects them, "
            "'preserve' keeps them off. Required when any topic is disabled -- there "
            "is no default, because inheriting a dead config's flags is how a migration "
            "reports success at producing a config that watches nothing"
        ),
    )
    move.add_argument(
        "--enable-all",
        action="store_true",
        help="older spelling of --disabled-topics enable",
    )
    move.add_argument("--force", action="store_true", help="overwrite an existing --out")
    args = parser.parse_args(argv)
    warnings: list[str] = []
    try:
        if args.command == "validate":
            config = load_config(Path(args.config))
            warning = coverage_warning(config, Path(args.config))
            output: dict[str, Any] = {
                "valid": True,
                "version": config["version"],
                "sections": len(config["sections"]),
                "enabled_sections": [s["id"] for s in config["sections"] if s["enabled"]],
                "disabled_sections": [s["id"] for s in config["sections"] if not s["enabled"]],
                "coverage_warning": warning,
            }
            if warning:
                warnings.append(f"WARNING: {warning}")
        else:
            output = migrate_config_file(
                Path(args.config),
                Path(args.out),
                project_roots=args.project_roots,
                disabled_topics=args.disabled_topics,
                enable_all=args.enable_all,
                force=args.force,
            )
            warnings.extend(output["warnings"])
            if output["coverage_warning"]:
                warnings.append(f"WARNING: {output['coverage_warning']}")
    except (ConfigError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    # Warnings go to stderr, where an operator running this by hand sees them
    # even when stdout is piped into jq -- and the exit code stays 0, because
    # correctly reporting that a config covers less than it could is this
    # command doing its job, not failing at it.
    for line in warnings:
        print(line, file=sys.stderr)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
