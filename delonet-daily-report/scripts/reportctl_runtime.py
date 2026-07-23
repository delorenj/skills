"""Locked process and atomic filesystem primitives for reportctl."""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
import re
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from reportctl_contracts import ConfigError, parse_iso
from reportctl_profile import skill_entry_installed
from reportctl_security import contains_secret, redact_text


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser().resolve()


def _profile_error(reason: str) -> ConfigError:
    return ConfigError(f"cannot inspect Hermes profile config: {reason}")


def _starts_yaml_quote(value: str, index: int) -> bool:
    previous = value[:index].rstrip()[-1:] or ""
    return not previous or previous in ":,[{-?"


def _uncomment_yaml(line: str) -> str:
    quote = ""
    index = 0
    while index < len(line):
        character = line[index]
        if quote == "'" and character == "'" and index + 1 < len(line) and line[index + 1] == "'":
            index += 2
            continue
        if character in "'\"":
            if quote == character:
                quote = ""
            elif not quote and _starts_yaml_quote(line, index):
                quote = character
        elif character == "#" and not quote and (index == 0 or line[index - 1].isspace()):
            return line[:index]
        elif character == "\\" and quote == '"':
            index += 1
        index += 1
    if quote:
        raise _profile_error("unterminated quoted scalar")
    return line


def _profile_scalar(raw: str, path: str) -> str:
    value = raw.strip()
    if not value:
        raise _profile_error(f"{path} must be a scalar")
    if value.startswith(("&", "*", "!")):
        raise _profile_error(f"{path} uses unsupported YAML aliases, anchors, or tags")
    if value.startswith(("|", ">")):
        raise _profile_error(f"{path} uses an unsupported block scalar")
    if value[0] == "'":
        if len(value) < 2 or value[-1] != "'":
            raise _profile_error(f"{path} has an invalid quoted scalar")
        return value[1:-1].replace("''", "'")
    if value[0] == '"':
        try:
            decoded = json.loads(value)
        except (json.JSONDecodeError, TypeError) as exc:
            raise _profile_error(f"{path} has an invalid quoted scalar") from exc
        if not isinstance(decoded, str):
            raise _profile_error(f"{path} must be a string")
        return decoded
    if any(character in value for character in "{}[]"):
        raise _profile_error(f"{path} uses unsupported YAML structure")
    return value


def _has_yaml_reference(value: str) -> bool:
    quote = ""
    index = 0
    while index < len(value):
        character = value[index]
        if quote == "'" and character == "'" and index + 1 < len(value) and value[index + 1] == "'":
            index += 2
            continue
        if character in "'\"":
            if quote == character:
                quote = ""
            elif not quote and _starts_yaml_quote(value, index):
                quote = character
        elif not quote:
            previous = value[index - 1] if index else " "
            if character in "&*!" and (previous.isspace() or previous in "[{,:"):
                return True
            if value.startswith("<<:", index) and (not index or previous.isspace()):
                return True
        if character == "\\" and quote == '"':
            index += 1
        index += 1
    return False


def _split_flow_fields(value: str) -> list[str]:
    fields: list[str] = []
    quote = ""
    start = 0
    index = 0
    while index < len(value):
        character = value[index]
        if quote == "'" and character == "'" and index + 1 < len(value) and value[index + 1] == "'":
            index += 2
            continue
        if character in "'\"":
            if quote == character:
                quote = ""
            elif not quote and _starts_yaml_quote(value, index):
                quote = character
        elif character == "," and not quote:
            fields.append(value[start:index])
            start = index + 1
        if character == "\\" and quote == '"':
            index += 1
        index += 1
    fields.append(value[start:])
    return fields


def _parse_model_flow(raw: str) -> dict[str, str]:
    if not raw.endswith("}"):
        raise _profile_error("model has an invalid flow mapping")
    result: dict[str, str] = {}
    for field in _split_flow_fields(raw[1:-1]):
        if not field.strip():
            continue
        key, separator, value = field.partition(":")
        key = key.strip()
        if not separator or not re.fullmatch(r"[A-Za-z_][\w-]*", key):
            raise _profile_error("model has an invalid flow mapping")
        if key == "<<":
            raise _profile_error("model uses unsupported YAML aliases")
        if key in {"provider", "default"}:
            if key in result:
                raise _profile_error(f"duplicate model.{key}")
            result[key] = _profile_scalar(value, f"model.{key}")
    return result


def _parse_profile_config(text: str) -> dict[str, Any]:
    top: dict[str, str] = {}
    seen_top: set[str] = set()
    nested_model: dict[str, str] | None = None
    current_section = ""
    model_indent: int | None = None
    tracked_closed = False
    document_started = False
    saw_content = False
    for raw_line in text.splitlines():
        if "\t" in raw_line:
            raise _profile_error("tabs are unsupported")
        line = _uncomment_yaml(raw_line).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if content.startswith("%") or content == "...":
            raise _profile_error("YAML directives and document end markers are unsupported")
        if content == "---":
            if indent or document_started or saw_content:
                raise _profile_error("multiple YAML documents are unsupported")
            document_started = True
            continue
        if _has_yaml_reference(content):
            raise _profile_error("unsupported YAML aliases, anchors, or tags")
        if indent and tracked_closed:
            raise _profile_error("tracked scalar settings cannot contain nested values")
        if indent == 0:
            saw_content = True
            tracked_closed = False
            current_section = ""
            model_indent = None
            if content.startswith("-"):
                raise _profile_error("top-level sequences are unsupported")
            match = re.fullmatch(r"([A-Za-z_][\w-]*):\s*(.*)", content)
            if not match:
                raise _profile_error("invalid top-level mapping syntax")
            key, raw_value = match.groups()
            if key in seen_top:
                raise _profile_error(f"duplicate {key}")
            seen_top.add(key)
            if key not in {"timezone", "provider", "model"}:
                current_section = key if not raw_value else ""
                continue
            if key == "model" and not raw_value:
                nested_model = {}
                current_section = "model"
            elif key == "model" and raw_value.startswith("{"):
                nested_model = _parse_model_flow(raw_value)
                tracked_closed = True
            else:
                top[key] = _profile_scalar(raw_value, key)
                tracked_closed = True
            continue
        if current_section != "model" or nested_model is None:
            continue
        match = re.fullmatch(r"([A-Za-z_][\w-]*):\s*(.*)", content)
        if not match:
            raise _profile_error("model has invalid nested syntax")
        key, raw_value = match.groups()
        if model_indent is None:
            model_indent = indent
        if indent != model_indent:
            raise _profile_error("model nesting is unsupported")
        if key == "<<":
            raise _profile_error("model uses unsupported YAML aliases")
        if key in {"provider", "default"}:
            if key in nested_model:
                raise _profile_error(f"duplicate model.{key}")
            nested_model[key] = _profile_scalar(raw_value, f"model.{key}")

    if nested_model is not None and "provider" in top:
        raise _profile_error("ambiguous flat and nested inference settings")
    if nested_model is not None:
        model: Any = nested_model
    else:
        model = top.get("model", "")
    return {
        "timezone": top.get("timezone", ""),
        "provider": top.get("provider", ""),
        "model": model,
    }


def profile_config() -> dict[str, Any]:
    path = hermes_home() / "config.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise ConfigError(f"cannot inspect Hermes profile config: {exc}") from exc
    return _parse_profile_config(text)


def timezone_state(config: dict[str, Any]) -> dict[str, Any]:
    profile = profile_config().get("timezone", "")
    profile = profile if isinstance(profile, str) else ""
    environment = os.environ.get("HERMES_TIMEZONE", "").strip()
    conflict = bool(environment and environment != profile)
    return {
        "profile": redact_text(profile) if profile else "unset",
        "environment": redact_text(environment) if environment else "unset",
        "conflict": conflict,
        "valid": profile == config["timezone"] and not conflict,
    }


def inference_state(config: dict[str, Any]) -> dict[str, Any]:
    profile = profile_config()
    model_config = profile.get("model", {})
    if isinstance(model_config, dict):
        provider = model_config.get("provider", "")
        model = model_config.get("default", "")
    else:
        provider = profile.get("provider", "")
        model = model_config
    provider = provider if isinstance(provider, str) else ""
    model = model if isinstance(model, str) else ""
    expected = config["inference"]
    return {
        "profile_provider": redact_text(provider) if provider else "unset",
        "profile_model": redact_text(model) if model else "unset",
        "expected_provider": expected["provider"],
        "expected_model": expected["model"],
        "valid": provider == expected["provider"] and model == expected["model"],
    }


def profile_skill_installed(name: str) -> bool:
    return skill_entry_installed(hermes_home(), name)


def timezone_preflight(config: dict[str, Any]) -> None:
    state = timezone_state(config)
    if not state["valid"]:
        raise ConfigError(
            f"Hermes profile timezone must be {config['timezone']} with no conflicting HERMES_TIMEZONE"
        )
    inference = inference_state(config)
    if not inference["valid"]:
        raise ConfigError("Hermes profile inference must match configured provider/model")
    if not profile_skill_installed("delonet-daily-report"):
        raise ConfigError(
            "delonet-daily-report must be installed in the active HERMES_HOME skills directory"
        )


def daily_next_run_valid(
    value: Any, config: dict[str, Any], now: dt.datetime | None = None
) -> bool:
    try:
        parsed = parse_iso(value, "daily_next_run_at")
        current = now or dt.datetime.now(dt.UTC)
        if current.tzinfo is None:
            return False
        zone = ZoneInfo(config["timezone"])
        local_now = current.astimezone(zone)
        expected = local_now.replace(hour=7, minute=0, second=0, microsecond=0)
        if expected <= local_now:
            expected = (local_now + dt.timedelta(days=1)).replace(
                hour=7, minute=0, second=0, microsecond=0
            )
        return parsed.astimezone(dt.UTC) == expected.astimezone(dt.UTC)
    except (ConfigError, AttributeError, TypeError, ValueError):
        return False


def archive_paths(config: dict[str, Any], date: str) -> dict[str, Any]:
    try:
        parsed = dt.date.fromisoformat(date)
    except ValueError as exc:
        raise ConfigError("date must use YYYY-MM-DD") from exc
    base = Path(config["artifact_dir"]) / date
    archive = Path(config["archive_dir"]) / f"{parsed.year:04d}" / f"{parsed.month:02d}" / date
    return {
        "sections_dir": str(base / "sections"),
        "manifest": str(base / "run-manifest.json"),
        "archive_root": str(archive),
        "commit_marker": str(archive / "current.json"),
    }


def fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(
    path: Path, value: Any, *, after_replace: Callable[[], None] | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if after_replace:
            after_replace()
        fsync_dir(path.parent)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_dir(path.parent)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


@contextmanager
def file_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = path.open("a+", encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"lock failure at {path}: {exc}") from exc
    with handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX)
        except OSError as exc:
            raise ConfigError(f"lock failure at {path}: {exc}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def run_command(
    command: list[str], *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command, check=True, text=True, capture_output=True, env=env, timeout=30
        )
    except FileNotFoundError as exc:
        raise ConfigError(f"missing executable: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ConfigError(f"command timed out: {command[0]}") from exc
    except OSError as exc:
        raise ConfigError(f"command failed to start: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        message = redact_text(exc.stderr or exc.stdout or str(exc))
        raise ConfigError(f"command failed: {message}") from exc


def publish_archive_pair(
    archive_root: Path,
    markdown: str,
    report: dict[str, Any],
    manifest: dict[str, Any],
    report_date: str,
) -> dict[str, Any]:
    if contains_secret(markdown) or contains_secret(report) or contains_secret(manifest):
        raise ConfigError("archive generation contains secret-like material")
    marker_path = archive_root / "current.json"
    with file_lock(marker_path.with_suffix(".lock")):
        generations = archive_root / "generations"
        generations.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        staged = generations / f".stage-{token}"
        generation = generations / token
        pointer_replaced = False

        def record_pointer_replace() -> None:
            nonlocal pointer_replaced
            pointer_replaced = True

        staged.mkdir()
        try:
            atomic_write_text(staged / "report.md", markdown)
            atomic_write(staged / "report.json", report)
            atomic_write(staged / "run-manifest.json", manifest)
            fsync_dir(staged)
            os.replace(staged, generation)
            fsync_dir(generations)
            atomic_write(
                marker_path,
                {
                    "schema_version": 1,
                    "report_date": report_date,
                    "generation": token,
                },
                after_replace=record_pointer_replace,
            )
        except BaseException:
            if staged.exists():
                for path in staged.iterdir():
                    path.unlink(missing_ok=True)
                staged.rmdir()
            pointer_target = None
            try:
                pointer = json.loads(marker_path.read_text(encoding="utf-8"))
                pointer_target = pointer.get("generation") if isinstance(pointer, dict) else None
            except (OSError, json.JSONDecodeError):
                pass
            if generation.exists() and not (pointer_replaced or pointer_target == token):
                for path in generation.iterdir():
                    path.unlink(missing_ok=True)
                generation.rmdir()
            fsync_dir(generations)
            raise
    markdown_path, report_path, manifest_path = (
        generation / "report.md",
        generation / "report.json",
        generation / "run-manifest.json",
    )
    return {
        "archived": True,
        "markdown": str(markdown_path),
        "report_json": str(report_path),
        "manifest": str(manifest_path),
        "commit_marker": str(marker_path),
    }
