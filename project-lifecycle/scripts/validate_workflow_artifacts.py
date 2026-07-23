#!/usr/bin/env python3
"""Validate CAF runtime workflow artifacts (PLC-E3-S2 / CAF-123)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = PROJECT_ROOT / "workflow-artifacts" / "workflow-schema.json"
DEFAULT_EXAMPLES = PROJECT_ROOT / "workflow-artifacts" / "workflow-examples"

TOP_LEVEL_REQUIRED = {
    "workflow_id",
    "version",
    "status",
    "source_intent_id",
    "phase_or_protocol",
    "session",
    "fields",
    "steps",
}
ANSWER_TYPES = {"text", "number", "rating_0_10", "yes_no", "list_item", "freeform"}
REPEAT_POLICIES = {"none", "for_declared_count", "until_no_or_done", "until_valid_rating"}
DUPLICATE_POLICIES = {"allow", "reject_duplicate", "merge_with_existing", "ask_if_anything_else"}
TRANSITION_EVENTS = {"valid_answer", "needs_clarification", "duplicate", "done", "coach_approval"}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)


def _mapping(value: object, label: str, result: ValidationResult) -> dict[str, object]:
    if not isinstance(value, dict):
        result.error(f"{label} must be an object")
        return {}
    return value


def _string(payload: dict[str, object], key: str, label: str, result: ValidationResult) -> None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        result.error(f"{label}.{key} must be a non-empty string")


def validate_workflow(payload: object, *, label: str = "workflow") -> ValidationResult:
    result = ValidationResult()
    data = _mapping(payload, label, result)
    missing = sorted(TOP_LEVEL_REQUIRED - set(data))
    if missing:
        result.error(f"{label} missing top-level keys: {', '.join(missing)}")

    for key in ("workflow_id", "version", "source_intent_id", "status"):
        _string(data, key, label, result)

    phase = _mapping(data.get("phase_or_protocol"), f"{label}.phase_or_protocol", result)
    for key in ("id", "name", "kind"):
        _string(phase, key, f"{label}.phase_or_protocol", result)

    session = _mapping(data.get("session"), f"{label}.session", result)
    if session.get("pin_workflow_version") is not True:
        result.error(f"{label}.session.pin_workflow_version must be true")
    _string(session, "state_scope", f"{label}.session", result)

    fields_value = data.get("fields")
    if not isinstance(fields_value, list) or not fields_value:
        result.error(f"{label}.fields must be a non-empty list")
        fields: list[dict[str, object]] = []
    else:
        fields = [_mapping(field_value, f"{label}.fields[{index}]", result) for index, field_value in enumerate(fields_value)]

    field_ids: set[str] = set()
    for index, field_item in enumerate(fields):
        field_label = f"{label}.fields[{index}]"
        field_id = field_item.get("field_id")
        if not isinstance(field_id, str) or not field_id.strip():
            result.error(f"{field_label}.field_id must be a non-empty string")
        elif field_id in field_ids:
            result.error(f"{field_label}.field_id duplicate: {field_id}")
        else:
            field_ids.add(field_id)
        if field_item.get("answer_type") not in ANSWER_TYPES:
            result.error(f"{field_label}.answer_type is invalid")
        storage = _mapping(field_item.get("storage"), f"{field_label}.storage", result)
        _string(storage, "kind", f"{field_label}.storage", result)
        _string(storage, "target", f"{field_label}.storage", result)

    steps_value = data.get("steps")
    if not isinstance(steps_value, list) or not steps_value:
        result.error(f"{label}.steps must be a non-empty list")
        return result

    steps = [_mapping(step_value, f"{label}.steps[{index}]", result) for index, step_value in enumerate(steps_value)]
    step_ids: set[str] = set()
    for index, step in enumerate(steps):
        step_id = step.get("step_id")
        if not isinstance(step_id, str) or not step_id.strip():
            result.error(f"{label}.steps[{index}].step_id must be a non-empty string")
        elif step_id in step_ids:
            result.error(f"{label}.steps[{index}].step_id duplicate: {step_id}")
        else:
            step_ids.add(step_id)

    for index, step in enumerate(steps):
        step_label = f"{label}.steps[{index}]"
        field_id = step.get("field_id")
        if not isinstance(field_id, str) or field_id not in field_ids:
            result.error(f"{step_label}.field_id must reference a declared field")

        prompt = _mapping(step.get("prompt"), f"{step_label}.prompt", result)
        _string(prompt, "text", f"{step_label}.prompt", result)
        if not isinstance(prompt.get("exact"), bool):
            result.error(f"{step_label}.prompt.exact must be boolean")

        answer = _mapping(step.get("answer"), f"{step_label}.answer", result)
        answer_type = answer.get("type")
        if answer_type not in ANSWER_TYPES:
            result.error(f"{step_label}.answer.type is invalid")
        if answer_type == "rating_0_10" and (answer.get("rating_min"), answer.get("rating_max")) != (0, 10):
            result.error(f"{step_label}.answer rating_0_10 must declare rating_min 0 and rating_max 10")

        if step.get("repeat_policy") not in REPEAT_POLICIES:
            result.error(f"{step_label}.repeat_policy is invalid")
        if step.get("duplicate_policy") not in DUPLICATE_POLICIES:
            result.error(f"{step_label}.duplicate_policy is invalid")

        clarification = _mapping(step.get("clarification_behavior"), f"{step_label}.clarification_behavior", result)
        if not isinstance(clarification.get("allow_clarification"), bool):
            result.error(f"{step_label}.clarification_behavior.allow_clarification must be boolean")
        if not isinstance(clarification.get("advance_on_clarification"), bool):
            result.error(f"{step_label}.clarification_behavior.advance_on_clarification must be boolean")

        gate = _mapping(step.get("completion_gate"), f"{step_label}.completion_gate", result)
        _string(gate, "gate_id", f"{step_label}.completion_gate", result)
        _string(gate, "condition", f"{step_label}.completion_gate", result)
        if answer_type == "rating_0_10" and gate.get("rating_required") is not True:
            result.error(f"{step_label}.completion_gate.rating_required must be true for rating_0_10")

        transitions = step.get("transitions")
        if not isinstance(transitions, list) or not transitions:
            result.error(f"{step_label}.transitions must be a non-empty list")
            continue
        for t_index, transition_value in enumerate(transitions):
            transition = _mapping(transition_value, f"{step_label}.transitions[{t_index}]", result)
            if transition.get("on") not in TRANSITION_EVENTS:
                result.error(f"{step_label}.transitions[{t_index}].on is invalid")
            target = transition.get("target")
            if not isinstance(target, str) or not target.strip():
                result.error(f"{step_label}.transitions[{t_index}].target must be a non-empty string")
            elif target != "complete" and target not in step_ids:
                result.error(f"{step_label}.transitions[{t_index}].target references unknown step: {target}")

    return result


def validate_file(path: Path) -> ValidationResult:
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:
        result = ValidationResult()
        result.error(f"{path}: invalid JSON: {exc}")
        return result
    return validate_workflow(payload, label=str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Workflow artifact JSON files to validate")
    args = parser.parse_args(argv)

    paths = [Path(path) for path in args.paths]
    if not paths:
        paths = sorted(DEFAULT_EXAMPLES.glob("*.json"))
    if not DEFAULT_SCHEMA.exists():
        print(f"error: missing schema {DEFAULT_SCHEMA.relative_to(PROJECT_ROOT)}", file=sys.stderr)
        return 1
    if not paths:
        print("error: no workflow artifact examples found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in paths:
        result = validate_file(path)
        errors.extend(result.errors)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"validated {len(paths)} workflow artifact file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
