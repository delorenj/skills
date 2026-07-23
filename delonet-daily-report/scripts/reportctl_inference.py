"""Hermes inference snapshot drift and safe cron creation helpers."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from reportctl_contracts import ConfigError
from reportctl_runtime import run_command

SNAPSHOT_FIELDS = ("provider_snapshot", "model_snapshot")
STAGING_SCHEDULE = "2099-12-31T23:59:59Z"
STAGING_PROMPT = "Staged DeLoNET Daily Report job; execution is disabled until verified."
DESIRED_FIELDS = (
    "schedule",
    "prompt",
    "deliver",
    "workdir",
    "skills",
    "script",
    "repeat_times",
)


def snapshot_mismatch(wanted: dict[str, Any], current: dict[str, Any]) -> bool:
    return any(current.get(field) != wanted[field] for field in SNAPSHOT_FIELDS)


def inference_issues(
    config: dict[str, Any], jobs: list[dict[str, Any]], managed: Callable[[str], bool]
) -> list[dict[str, str]]:
    expected = config["inference"]
    issues = []
    for job in jobs:
        if not managed(job["name"]):
            continue
        reasons = []
        for field, key in (("provider_snapshot", "provider"), ("model_snapshot", "model")):
            actual = job.get(field)
            if actual is None:
                reasons.append(f"{field}=null")
            elif actual != expected[key]:
                reasons.append(f"{field}={actual}")
        if reasons:
            issues.append({"id": job["id"], "name": job["name"], "reason": ", ".join(reasons)})
    return issues


def _stable_core(jobs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        job["id"]: {key: value for key, value in job.items() if key != "next_run_at"}
        for job in jobs
    }


def _created_id(stdout: str, name: str) -> str:
    match = re.search(r"Created job:\s*(\S+)", stdout)
    if not match:
        raise ConfigError(f"created job {name} but could not read its Hermes job ID")
    return match.group(1)


def _owned_job(action: dict[str, Any], created_id: str, jobs: list[dict[str, Any]]) -> dict:
    current = next((job for job in jobs if job["id"] == created_id), None)
    if current is None or current["name"] != action["name"]:
        raise ConfigError(f"created job {action['name']} missing from canonical Hermes state")
    return current


def _verify_created(
    action: dict[str, Any],
    created_id: str,
    jobs: list[dict[str, Any]],
    *,
    enabled: bool,
    desired_fields: bool,
) -> None:
    current = _owned_job(action, created_id, jobs)
    if snapshot_mismatch(action, current):
        raise ConfigError(f"created job {action['name']} has unexpected inference snapshots")
    if current["enabled"] != enabled:
        raise ConfigError(f"created job {action['name']} did not preserve enabled state")
    expected = (
        action
        if desired_fields
        else {
            "schedule": STAGING_SCHEDULE,
            "prompt": STAGING_PROMPT,
            "repeat_times": 1,
            "repeat_completed": 0,
        }
    )
    fields = DESIRED_FIELDS if desired_fields else (
        "schedule",
        "prompt",
        "repeat_times",
        "repeat_completed",
    )
    if any(current.get(field) != expected[field] for field in fields):
        raise ConfigError(f"created job {action['name']} has unexpected staged or desired fields")
    if desired_fields and current.get("repeat_completed") != action["repeat_completed"]:
        raise ConfigError(f"created job {action['name']} has unexpected desired repeat progress")


def _verify_only_created(
    before: list[dict[str, Any]], after: list[dict[str, Any]], created_id: str
) -> None:
    after_core = _stable_core(after)
    created_core = after_core.pop(created_id, None)
    if created_core is None or after_core != _stable_core(before):
        raise ConfigError("canonical Hermes jobs changed unexpectedly during create")


def _cleanup_created(
    created_id: str,
    name: str,
    environment: dict[str, str],
    stable_read: Callable[[], list[dict[str, Any]]],
) -> str | None:
    errors = []
    try:
        run_command(["hermes", "cron", "pause", created_id], env=environment)
    except Exception as exc:
        errors.append(f"pause: {exc}")
    try:
        current = next((job for job in stable_read() if job["id"] == created_id), None)
        if current is None:
            return "; ".join(errors) or None
        if current["name"] != name:
            errors.append(f"ownership: id {created_id} belongs to {current['name']}")
            return "; ".join(errors)
        run_command(["hermes", "cron", "remove", created_id], env=environment)
        if any(job["id"] == created_id for job in stable_read()):
            errors.append("remove verification: created ID remains")
    except Exception as exc:
        errors.append(f"verified remove: {exc}")
    return "; ".join(errors) or None


def apply_create(
    action: dict[str, Any],
    environment: dict[str, str],
    action_command: Callable[[dict[str, Any]], list[str]],
    stable_read: Callable[[], list[dict[str, Any]]],
) -> None:
    before = stable_read()
    if any(job["name"] == action["name"] for job in before):
        raise ConfigError(f"job {action['name']} appeared before create; abort and replan")
    staged = {
        **action,
        "action": "create",
        "schedule": STAGING_SCHEDULE,
        "prompt": STAGING_PROMPT,
        "enabled": False,
        "repeat_times": 1,
        "repeat_completed": 0,
    }
    result = run_command(action_command(staged), env=environment)
    created_id = _created_id(result.stdout, action["name"])
    try:
        run_command(["hermes", "cron", "pause", created_id], env=environment)
        staged_jobs = stable_read()
        _verify_only_created(before, staged_jobs, created_id)
        _verify_created(action, created_id, staged_jobs, enabled=False, desired_fields=False)
        changes = {field: action[field] for field in DESIRED_FIELDS}
        run_command(
            action_command(
                {"action": "edit", "id": created_id, "name": action["name"], "changes": changes}
            ),
            env=environment,
        )
        edited_jobs = stable_read()
        _verify_only_created(before, edited_jobs, created_id)
        _verify_created(action, created_id, edited_jobs, enabled=False, desired_fields=True)
        if action["enabled"]:
            run_command(["hermes", "cron", "resume", created_id], env=environment)
            resumed_jobs = stable_read()
            _verify_only_created(before, resumed_jobs, created_id)
            _verify_created(action, created_id, resumed_jobs, enabled=True, desired_fields=True)
    except Exception as exc:
        cleanup_error = _cleanup_created(created_id, action["name"], environment, stable_read)
        message = f"create transaction failed for {action['name']}: {exc}"
        if cleanup_error:
            message += f"; cleanup failed: {cleanup_error}"
        raise ConfigError(message) from exc


def apply_recreate(
    action: dict[str, Any],
    environment: dict[str, str],
    action_command: Callable[[dict[str, Any]], list[str]],
    stable_read: Callable[[], list[dict[str, Any]]],
) -> None:
    before = stable_read()
    current = next((job for job in before if job["id"] == action["id"]), None)
    if current is None or current["name"] != action["name"]:
        raise ConfigError("recreate target changed; abort and replan")
    run_command(["hermes", "cron", "remove", action["id"]], env=environment)
    after_remove = stable_read()
    expected = _stable_core(before)
    expected.pop(action["id"])
    if _stable_core(after_remove) != expected:
        raise ConfigError("canonical Hermes jobs changed unexpectedly after recreate removal")
    if any(job["name"] == action["name"] for job in after_remove):
        raise ConfigError("recreate name reappeared after removal; abort before create")
    apply_create(action, environment, action_command, stable_read)
