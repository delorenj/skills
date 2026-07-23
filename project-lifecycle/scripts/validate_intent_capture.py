#!/usr/bin/env python3
"""Validate CAF intent-capture artifacts (PLC-E3-S1 / CAF-122)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = PROJECT_ROOT / "workflow-artifacts" / "intent-capture.schema.json"
DEFAULT_EXAMPLES = PROJECT_ROOT / "workflow-artifacts" / "examples"

TOP_LEVEL_REQUIRED = {
    "intent_id",
    "title",
    "source",
    "phase_or_protocol",
    "purpose",
    "exact_language_policy",
    "steps",
    "data_capture",
    "ambiguities",
}
STEP_REQUIRED = {"step_id", "intent", "prompt", "answer", "completion"}
ANSWER_TYPES = {"text", "number", "rating_0_10", "yes_no", "list_item", "freeform"}
REPEAT_POLICIES = {"none", "for_declared_count", "until_no_or_done", "until_valid_rating"}
DUPLICATE_POLICIES = {"allow", "reject_duplicate", "merge_with_existing", "ask_if_anything_else"}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)


def _require_mapping(payload: object, label: str, result: ValidationResult) -> dict[str, object]:
    if not isinstance(payload, dict):
        result.error(f"{label} must be an object")
        return {}
    return payload


def _require_string(payload: dict[str, object], key: str, label: str, result: ValidationResult) -> None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        result.error(f"{label}.{key} must be a non-empty string")


def validate_capture(payload: object, *, label: str = "intent") -> ValidationResult:
    result = ValidationResult()
    data = _require_mapping(payload, label, result)
    missing = sorted(TOP_LEVEL_REQUIRED - set(data))
    if missing:
        result.error(f"{label} missing top-level keys: {', '.join(missing)}")

    source = _require_mapping(data.get("source"), f"{label}.source", result)
    _require_string(source, "kind", f"{label}.source", result)
    _require_string(source, "reference", f"{label}.source", result)

    phase = _require_mapping(data.get("phase_or_protocol"), f"{label}.phase_or_protocol", result)
    for key in ("id", "name", "kind"):
        _require_string(phase, key, f"{label}.phase_or_protocol", result)

    purpose = _require_mapping(data.get("purpose"), f"{label}.purpose", result)
    _require_string(purpose, "client_visible_summary", f"{label}.purpose", result)
    _require_string(purpose, "operator_intent", f"{label}.purpose", result)

    exact_policy = _require_mapping(data.get("exact_language_policy"), f"{label}.exact_language_policy", result)
    if not isinstance(exact_policy.get("preserve_exact_prompts"), bool):
        result.error(f"{label}.exact_language_policy.preserve_exact_prompts must be boolean")
    if exact_policy.get("allowed_interpretation") not in {
        "none",
        "clarify_only",
        "summarize_after_capture",
        "coach_with_constraints",
    }:
        result.error(f"{label}.exact_language_policy.allowed_interpretation is invalid")

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        result.error(f"{label}.steps must be a non-empty list")
    else:
        seen_step_ids: set[str] = set()
        for index, step_value in enumerate(steps):
            step_label = f"{label}.steps[{index}]"
            step = _require_mapping(step_value, step_label, result)
            missing_step = sorted(STEP_REQUIRED - set(step))
            if missing_step:
                result.error(f"{step_label} missing keys: {', '.join(missing_step)}")
            step_id = step.get("step_id")
            if not isinstance(step_id, str) or not step_id.strip():
                result.error(f"{step_label}.step_id must be non-empty")
            elif step_id in seen_step_ids:
                result.error(f"{step_label}.step_id duplicate: {step_id}")
            else:
                seen_step_ids.add(step_id)

            prompt = _require_mapping(step.get("prompt"), f"{step_label}.prompt", result)
            _require_string(prompt, "text", f"{step_label}.prompt", result)
            if not isinstance(prompt.get("exact"), bool):
                result.error(f"{step_label}.prompt.exact must be boolean")

            answer = _require_mapping(step.get("answer"), f"{step_label}.answer", result)
            if answer.get("type") not in ANSWER_TYPES:
                result.error(f"{step_label}.answer.type is invalid")
            if not (answer.get("field_id") or answer.get("mapped_field") or answer.get("loose_note_key")):
                result.error(f"{step_label}.answer must declare field_id, mapped_field, or loose_note_key")

            loop = step.get("loop")
            if loop is not None:
                loop_obj = _require_mapping(loop, f"{step_label}.loop", result)
                if loop_obj.get("repeat_policy") not in REPEAT_POLICIES:
                    result.error(f"{step_label}.loop.repeat_policy is invalid")
                if loop_obj.get("duplicate_policy") not in DUPLICATE_POLICIES:
                    result.error(f"{step_label}.loop.duplicate_policy is invalid")

            completion = _require_mapping(step.get("completion"), f"{step_label}.completion", result)
            _require_string(completion, "gate", f"{step_label}.completion", result)

    capture = _require_mapping(data.get("data_capture"), f"{label}.data_capture", result)
    strict_fields = capture.get("strict_fields")
    loose_notes = capture.get("loose_notes")
    if not isinstance(strict_fields, list):
        result.error(f"{label}.data_capture.strict_fields must be a list")
    if not isinstance(loose_notes, list):
        result.error(f"{label}.data_capture.loose_notes must be a list")

    ambiguities = data.get("ambiguities")
    if not isinstance(ambiguities, list):
        result.error(f"{label}.ambiguities must be a list")
    else:
        for index, ambiguity_value in enumerate(ambiguities):
            ambiguity = _require_mapping(ambiguity_value, f"{label}.ambiguities[{index}]", result)
            _require_string(ambiguity, "question", f"{label}.ambiguities[{index}]", result)
            _require_string(ambiguity, "impact", f"{label}.ambiguities[{index}]", result)
    return result


def validate_file(path: Path) -> ValidationResult:
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:
        result = ValidationResult()
        result.error(f"{path}: invalid JSON: {exc}")
        return result
    return validate_capture(payload, label=str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Intent capture JSON files to validate")
    args = parser.parse_args(argv)

    paths = [Path(path) for path in args.paths]
    if not paths:
        paths = sorted(DEFAULT_EXAMPLES.glob("*-intent-capture.json"))
    if not DEFAULT_SCHEMA.exists():
        print(f"error: missing schema {DEFAULT_SCHEMA.relative_to(PROJECT_ROOT)}", file=sys.stderr)
        return 1
    if not paths:
        print("error: no intent capture examples found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in paths:
        result = validate_file(path)
        errors.extend(result.errors)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"validated {len(paths)} intent capture file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
