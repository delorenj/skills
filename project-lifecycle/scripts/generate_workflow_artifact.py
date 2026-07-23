#!/usr/bin/env python3
"""Generate draft CAF workflow artifacts from intent captures or raw notes.

BMAD story: PLC-E3-S3 / CAF-124.

This generator is intentionally conservative. It creates draft, review-required
workflow artifacts only; it does not approve runtime behavior.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ARTIFACT_DIRS = {
    (PROJECT_ROOT / "workflow-artifacts" / "workflow-examples").resolve(),
}


@dataclass
class GenerationResult:
    workflow: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "draft-workflow"


def _today() -> str:
    return date.today().isoformat()


def _generated_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_source(path: Path) -> tuple[dict[str, Any] | None, str]:
    text = path.read_text()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, text
    if isinstance(payload, dict) and "intent_id" in payload and "steps" in payload:
        return payload, text
    return None, text


def _session_scope(kind: str) -> str:
    if kind == "onboarding":
        return "onboarding_case"
    if kind == "protocol":
        return "protocol_session"
    if kind == "review":
        return "review_session"
    return "client_phase"


def _field_from_step(step: dict[str, Any], *, warnings: list[str]) -> dict[str, Any]:
    answer = step.get("answer") if isinstance(step.get("answer"), dict) else {}
    step_id = str(step.get("step_id") or "draft_step")
    field_id = str(
        answer.get("field_id")
        or answer.get("mapped_field")
        or answer.get("loose_note_key")
        or step_id
    )
    answer_type = str(answer.get("type") or "freeform")
    mapped_field = answer.get("mapped_field")
    loose_note_key = answer.get("loose_note_key")
    if isinstance(mapped_field, str) and mapped_field.strip():
        storage = {"kind": "strict_field", "target": mapped_field}
    elif isinstance(loose_note_key, str) and loose_note_key.strip():
        storage = {
            "kind": "loose_note",
            "target": loose_note_key,
            "category": "misc",
            "salience": 3,
        }
    else:
        storage = {
            "kind": "loose_note",
            "target": f"draft.{field_id}",
            "category": "misc",
            "salience": 2,
        }
        warnings.append(f"{step_id}: storage target inferred; review mapping before approval")
    return {
        "field_id": field_id,
        "answer_type": answer_type,
        "storage": storage,
        "required": True,
        "repeatable": _repeat_policy(step) != "none",
    }


def _repeat_policy(step: dict[str, Any]) -> str:
    loop = step.get("loop")
    if isinstance(loop, dict) and isinstance(loop.get("repeat_policy"), str):
        return loop["repeat_policy"]
    return "none"


def _duplicate_policy(step: dict[str, Any]) -> str:
    loop = step.get("loop")
    if isinstance(loop, dict) and isinstance(loop.get("duplicate_policy"), str):
        return loop["duplicate_policy"]
    return "allow"


def _prompt(step: dict[str, Any]) -> dict[str, Any]:
    prompt = step.get("prompt")
    if isinstance(prompt, dict):
        text = str(prompt.get("text") or "Please answer this step.")
        exact = bool(prompt.get("exact", False))
        result: dict[str, Any] = {"text": text, "exact": exact}
        coach_context = prompt.get("coach_context")
        if isinstance(coach_context, str) and coach_context.strip():
            result["coach_context"] = coach_context
        return result
    return {"text": "Please answer this step.", "exact": False}


def _workflow_step(step: dict[str, Any], *, field_id: str, next_target: str) -> dict[str, Any]:
    prompt = _prompt(step)
    answer_source = step.get("answer") if isinstance(step.get("answer"), dict) else {}
    answer_type = str(answer_source.get("type") or "freeform")
    answer: dict[str, Any] = {"type": answer_type}
    if answer_type == "rating_0_10":
        answer["rating_min"] = 0
        answer["rating_max"] = 10
    completion = step.get("completion") if isinstance(step.get("completion"), dict) else {}
    rating_required = bool(completion.get("rating_required")) or answer_type == "rating_0_10"
    step_id = str(step.get("step_id") or field_id)
    transitions = [
        {"on": "valid_answer", "target": next_target},
        {"on": "needs_clarification", "target": step_id},
    ]
    if _duplicate_policy(step) != "allow":
        transitions.append({"on": "duplicate", "target": step_id})
    return {
        "step_id": step_id,
        "field_id": field_id,
        "prompt": prompt,
        "answer": answer,
        "repeat_policy": _repeat_policy(step),
        "duplicate_policy": _duplicate_policy(step),
        "clarification_behavior": {
            "allow_clarification": True,
            "advance_on_clarification": False,
            "bounded_reply": (
                "I can clarify the current question, but we should stay on this "
                f"step: {prompt['text']}"
            ),
        },
        "completion_gate": {
            "gate_id": f"{step_id}_gate",
            "condition": str(completion.get("gate") or "valid answer captured"),
            "rating_required": rating_required,
            "coach_approval_required": bool(completion.get("coach_approval_required", False)),
        },
        "transitions": transitions,
    }


def generate_from_intent_capture(
    capture: dict[str, Any],
    *,
    source_reference: str,
    generated_at: str | None = None,
) -> GenerationResult:
    warnings: list[str] = []
    phase = (
        capture.get("phase_or_protocol")
        if isinstance(capture.get("phase_or_protocol"), dict)
        else {}
    )
    phase_id = str(phase.get("id") or _slug(str(capture.get("title") or "draft-workflow")))
    fields = [
        _field_from_step(step, warnings=warnings)
        for step in capture.get("steps", [])
        if isinstance(step, dict)
    ]
    field_ids = [field["field_id"] for field in fields]
    workflow_steps: list[dict[str, Any]] = []
    source_steps = [step for step in capture.get("steps", []) if isinstance(step, dict)]
    for index, step in enumerate(source_steps):
        next_target = (
            source_steps[index + 1].get("step_id")
            if index + 1 < len(source_steps)
            else "complete"
        )
        workflow_steps.append(
            _workflow_step(
                step,
                field_id=str(field_ids[index]),
                next_target=str(next_target or "complete"),
            )
        )
    ambiguities = capture.get("ambiguities") if isinstance(capture.get("ambiguities"), list) else []
    uncertain_mappings = [
        {
            "source": "intent.ambiguities",
            "question": str(item.get("question", "")),
            "impact": str(item.get("impact", "")),
        }
        for item in ambiguities
        if isinstance(item, dict)
    ]
    uncertain_mappings.extend(
        {
            "source": "generator",
            "question": warning,
            "impact": "Requires reviewer approval before runtime use.",
        }
        for warning in warnings
    )
    workflow = {
        "workflow_id": f"damian-method.{phase_id}",
        "version": "0.1.0-draft",
        "status": "draft",
        "source_intent_id": str(capture.get("intent_id") or f"{phase_id}.intent"),
        "phase_or_protocol": {
            "id": phase_id,
            "name": str(phase.get("name") or phase_id.replace("-", " ").title()),
            "kind": str(phase.get("kind") or "protocol"),
            "coach_approval_required": bool(phase.get("coach_approval_required", True)),
        },
        "session": {
            "pin_workflow_version": True,
            "state_scope": _session_scope(str(phase.get("kind") or "protocol")),
            "resume_policy": "resume_current_step",
        },
        "fields": fields,
        "steps": workflow_steps,
        "generation": {
            "source_reference": source_reference,
            "generated_at": generated_at or _generated_timestamp(),
            "review_required": True,
            "uncertain_mappings": uncertain_mappings,
        },
    }
    return GenerationResult(workflow=workflow, warnings=warnings)


def generate_from_plain_text(
    text: str,
    *,
    source_reference: str,
    generated_at: str | None = None,
) -> GenerationResult:
    title = next((line.strip() for line in text.splitlines() if line.strip()), "Draft Workflow")
    phase_id = _slug(title)[:64]
    workflow = {
        "workflow_id": f"damian-method.{phase_id}",
        "version": "0.1.0-draft",
        "status": "draft",
        "source_intent_id": f"{phase_id}.raw-intent.{_today()}",
        "phase_or_protocol": {
            "id": phase_id,
            "name": title[:80],
            "kind": "protocol",
            "coach_approval_required": True,
        },
        "session": {
            "pin_workflow_version": True,
            "state_scope": "protocol_session",
            "resume_policy": "resume_current_step",
        },
        "fields": [
            {
                "field_id": "operator_source_notes",
                "answer_type": "freeform",
                "storage": {
                    "kind": "loose_note",
                    "target": "draft.operator_source_notes",
                    "category": "misc",
                    "salience": 2,
                },
                "required": True,
                "repeatable": False,
            }
        ],
        "steps": [
            {
                "step_id": "review_source_notes",
                "field_id": "operator_source_notes",
                "prompt": {
                    "text": "Review the source notes and define exact prompts before approval.",
                    "exact": False,
                },
                "answer": {"type": "freeform"},
                "repeat_policy": "none",
                "duplicate_policy": "allow",
                "clarification_behavior": {
                    "allow_clarification": True,
                    "advance_on_clarification": False,
                    "bounded_reply": (
                        "This draft came from raw notes; a reviewer must define "
                        "exact runtime prompts."
                    ),
                },
                "completion_gate": {
                    "gate_id": "source_notes_reviewed",
                    "condition": "reviewer maps source notes into explicit workflow steps",
                    "rating_required": False,
                    "coach_approval_required": True,
                },
                "transitions": [
                    {"on": "valid_answer", "target": "complete"},
                    {"on": "needs_clarification", "target": "review_source_notes"},
                ],
            }
        ],
        "generation": {
            "source_reference": source_reference,
            "generated_at": generated_at or _generated_timestamp(),
            "review_required": True,
            "source_excerpt": text[:2000],
            "uncertain_mappings": [
                {
                    "source": "raw_text",
                    "question": (
                        "Raw natural-language input needs human decomposition "
                        "into exact steps, fields, loops, and gates."
                    ),
                    "impact": (
                        "The draft cannot be approved for runtime use until a "
                        "reviewer maps the coaching rules."
                    ),
                }
            ],
        },
    }
    return GenerationResult(
        workflow=workflow,
        warnings=["raw text source generated review-only workflow shell"],
    )


def generate_artifact(
    source_path: Path,
    *,
    generated_at: str | None = None,
) -> GenerationResult:
    capture, text = _load_source(source_path)
    source_reference = str(source_path)
    if capture is not None:
        return generate_from_intent_capture(
            capture,
            source_reference=source_reference,
            generated_at=generated_at,
        )
    return generate_from_plain_text(
        text,
        source_reference=source_reference,
        generated_at=generated_at,
    )


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    return json.dumps(str(value))


def _emit_toml_table(data: dict[str, Any], *, path: list[str] | None = None) -> list[str]:
    path = path or []
    lines: list[str] = []
    scalar_items: list[tuple[str, Any]] = []
    dict_items: list[tuple[str, dict[str, Any]]] = []
    table_arrays: list[tuple[str, list[dict[str, Any]]]] = []
    for key, value in data.items():
        if isinstance(value, dict):
            dict_items.append((key, value))
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            table_arrays.append((key, value))
        else:
            scalar_items.append((key, value))
    for key, value in scalar_items:
        lines.append(f"{key} = {_toml_value(value)}")
    for key, value in dict_items:
        lines.append("")
        lines.append(f"[{'.'.join([*path, key])}]")
        lines.extend(_emit_toml_table(value, path=[*path, key]))
    for key, items in table_arrays:
        for item in items:
            lines.append("")
            lines.append(f"[[{'.'.join([*path, key])}]]")
            lines.extend(_emit_toml_table(item, path=[*path, key]))
    return lines


def dump_toml(data: dict[str, Any]) -> str:
    return "\n".join(_emit_toml_table(data)) + "\n"


def render_artifact(workflow: dict[str, Any], *, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(workflow, indent=2, sort_keys=False) + "\n"
    if output_format == "toml":
        return dump_toml(workflow)
    raise ValueError(f"unsupported output format: {output_format}")


def _format_from_output(output: Path | None, explicit: str | None) -> str:
    if explicit:
        return explicit
    if output is not None and output.suffix.lower() == ".json":
        return "json"
    return "toml"


def _is_runtime_artifact_path(path: Path) -> bool:
    resolved = path.resolve()
    return any(parent == resolved or parent in resolved.parents for parent in RUNTIME_ARTIFACT_DIRS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        help="Intent-capture JSON, source document, or pasted transcript file.",
    )
    parser.add_argument("--output", help="Output draft artifact path. Defaults to stdout.")
    parser.add_argument(
        "--format",
        choices=("json", "toml"),
        help="Output format. Defaults to TOML unless --output ends in .json.",
    )
    parser.add_argument(
        "--generated-at",
        help="Override generation timestamp/date for deterministic tests.",
    )
    parser.add_argument(
        "--allow-runtime-path",
        action="store_true",
        help=(
            "Allow writing into workflow runtime/example directories. Defaults "
            "to false to enforce review workflow."
        ),
    )
    args = parser.parse_args(argv)

    source = Path(args.source)
    if not source.exists():
        print(f"error: source not found: {source}", file=sys.stderr)
        return 1
    output = Path(args.output) if args.output else None
    if output is not None and not args.allow_runtime_path and _is_runtime_artifact_path(output):
        print(
            (
                "error: refusing to write generated draft into runtime/example "
                "artifact directory without --allow-runtime-path"
            ),
            file=sys.stderr,
        )
        return 1
    result = generate_artifact(source, generated_at=args.generated_at)
    output_format = _format_from_output(output, args.format)
    rendered = render_artifact(result.workflow, output_format=output_format)
    if output is None:
        sys.stdout.write(rendered)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
        print(f"wrote {output}")
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
