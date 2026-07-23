#!/usr/bin/env python3
"""Review draft CAF workflow artifacts before runtime approval.

BMAD story: PLC-E3-S4 / CAF-125.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

SCRIPTS_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = SCRIPTS_DIR / "validate_workflow_artifacts.py"
BOUNDARY_TERMS = (
    "private",
    "internal",
    "coach-only",
    "coach only",
    "assistant-only",
    "assistant only",
    "do not show",
    "hidden",
)

Decision = Literal["approve", "request_changes", "retire"]
Severity = Literal["blocking", "warning", "info"]


@dataclass(frozen=True)
class Finding:
    severity: Severity
    kind: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "kind": self.kind,
            "path": self.path,
            "message": self.message,
        }


@dataclass
class ReviewResult:
    report: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)

    @property
    def blocking_findings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.severity == "blocking"]

    @property
    def warning_findings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.severity == "warning"]


def _load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("validate_workflow_artifacts", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load validator: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_artifact(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if path.suffix.lower() == ".toml":
        payload = tomllib.loads(text)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("workflow artifact must be a JSON/TOML object")
    return payload


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps = workflow.get("steps")
    if not isinstance(steps, list):
        return []
    return [step for step in steps if isinstance(step, dict)]


def _fields(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    fields = workflow.get("fields")
    if not isinstance(fields, list):
        return []
    return [field for field in fields if isinstance(field, dict)]


def _nested_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_nested_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_nested_text(item) for item in value)
    return ""


def _highlight_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    highlights: list[dict[str, Any]] = []
    for step in _steps(workflow):
        prompt = step.get("prompt") if isinstance(step.get("prompt"), dict) else {}
        gate = (
            step.get("completion_gate")
            if isinstance(step.get("completion_gate"), dict)
            else {}
        )
        transitions = step.get("transitions") if isinstance(step.get("transitions"), list) else []
        highlights.append(
            {
                "step_id": step.get("step_id"),
                "field_id": step.get("field_id"),
                "prompt": prompt.get("text"),
                "prompt_exact": prompt.get("exact"),
                "repeat_policy": step.get("repeat_policy"),
                "duplicate_policy": step.get("duplicate_policy"),
                "completion_gate": gate.get("condition"),
                "rating_required": gate.get("rating_required"),
                "coach_approval_required": gate.get("coach_approval_required"),
                "transitions": [
                    {"on": item.get("on"), "target": item.get("target")}
                    for item in transitions
                    if isinstance(item, dict)
                ],
            }
        )
    return highlights


def _highlight_mappings(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for field_item in _fields(workflow):
        storage = (
            field_item.get("storage")
            if isinstance(field_item.get("storage"), dict)
            else {}
        )
        mappings.append(
            {
                "field_id": field_item.get("field_id"),
                "answer_type": field_item.get("answer_type"),
                "storage_kind": storage.get("kind"),
                "storage_target": storage.get("target"),
                "category": storage.get("category"),
                "required": field_item.get("required"),
                "repeatable": field_item.get("repeatable"),
            }
        )
    return mappings


def _structural_findings(workflow: dict[str, Any], *, label: str) -> list[Finding]:
    validator = _load_validator()
    result = validator.validate_workflow(workflow, label=label)
    return [
        Finding(
            severity="blocking",
            kind="schema",
            path=label,
            message=error,
        )
        for error in result.errors
    ]


def _policy_findings(workflow: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for index, step in enumerate(_steps(workflow)):
        step_id = step.get("step_id") or f"steps[{index}]"
        prompt = step.get("prompt") if isinstance(step.get("prompt"), dict) else {}
        answer = step.get("answer") if isinstance(step.get("answer"), dict) else {}
        gate = (
            step.get("completion_gate")
            if isinstance(step.get("completion_gate"), dict)
            else {}
        )
        duplicate_policy = step.get("duplicate_policy")
        if not duplicate_policy:
            findings.append(
                Finding(
                    severity="blocking",
                    kind="duplicate_policy",
                    path=f"steps[{index}].duplicate_policy",
                    message=f"{step_id}: duplicate policy is missing",
                )
            )
        elif duplicate_policy == "allow":
            findings.append(
                Finding(
                    severity="info",
                    kind="duplicate_policy",
                    path=f"steps[{index}].duplicate_policy",
                    message=f"{step_id}: duplicates are allowed; confirm this is intentional",
                )
            )
        prompt_text = str(prompt.get("text") or "")
        if "0 to 10" in prompt_text.lower() and answer.get("type") != "rating_0_10":
            findings.append(
                Finding(
                    severity="warning",
                    kind="rating_requirement",
                    path=f"steps[{index}].answer.type",
                    message=(
                        f"{step_id}: prompt appears to request a 0-10 rating but "
                        "answer.type is not rating_0_10"
                    ),
                )
            )
        if answer.get("type") == "rating_0_10" and gate.get("rating_required") is not True:
            findings.append(
                Finding(
                    severity="blocking",
                    kind="rating_requirement",
                    path=f"steps[{index}].completion_gate.rating_required",
                    message=f"{step_id}: rating step must require a rating gate",
                )
            )
        boundary_text = _nested_text(
            {
                "prompt": prompt,
                "completion_gate": gate,
                "clarification_behavior": step.get("clarification_behavior"),
            }
        ).lower()
        if any(term in boundary_text for term in BOUNDARY_TERMS):
            findings.append(
                Finding(
                    severity="warning",
                    kind="client_private_boundary",
                    path=f"steps[{index}]",
                    message=(
                        f"{step_id}: client-facing step may contain private or "
                        "coach-only language"
                    ),
                )
            )
    for index, field_item in enumerate(_fields(workflow)):
        storage = (
            field_item.get("storage")
            if isinstance(field_item.get("storage"), dict)
            else {}
        )
        target_text = _nested_text(storage).lower()
        if any(term in target_text for term in BOUNDARY_TERMS):
            findings.append(
                Finding(
                    severity="warning",
                    kind="client_private_boundary",
                    path=f"fields[{index}].storage",
                    message=(
                        f"{field_item.get('field_id')}: storage mapping includes "
                        "private-boundary terms; confirm visibility rules"
                    ),
                )
            )
    generation = workflow.get("generation") if isinstance(workflow.get("generation"), dict) else {}
    uncertain = generation.get("uncertain_mappings")
    if isinstance(uncertain, list) and uncertain:
        findings.append(
            Finding(
                severity="warning",
                kind="uncertain_mapping",
                path="generation.uncertain_mappings",
                message=f"{len(uncertain)} uncertain mapping(s) require review",
            )
        )
    return findings


def _decision_status(
    decision: Decision,
    *,
    findings: list[Finding],
    ack_uncertain: bool,
) -> tuple[bool, str]:
    blocking = [finding for finding in findings if finding.severity == "blocking"]
    uncertainty = [finding for finding in findings if finding.kind == "uncertain_mapping"]
    if decision == "approve" and blocking:
        return False, "approval blocked by structural or policy findings"
    if decision == "approve" and uncertainty and not ack_uncertain:
        return False, "approval requires --ack-uncertain while uncertain mappings exist"
    if decision == "approve":
        return True, "approved for reviewer handoff"
    if decision == "retire":
        return True, "retired by reviewer decision"
    return True, "changes requested by reviewer decision"


def review_artifact(
    artifact_path: Path,
    *,
    decision: Decision,
    reviewer: str,
    notes: str = "",
    reviewed_at: str | None = None,
    ack_uncertain: bool = False,
) -> ReviewResult:
    workflow = _load_artifact(artifact_path)
    findings = [
        *_structural_findings(workflow, label=str(artifact_path)),
        *_policy_findings(workflow),
    ]
    decision_allowed, decision_reason = _decision_status(
        decision,
        findings=findings,
        ack_uncertain=ack_uncertain,
    )
    generation = workflow.get("generation") if isinstance(workflow.get("generation"), dict) else {}
    recommended_status = {
        "approve": "approved" if decision_allowed else "draft",
        "request_changes": "draft",
        "retire": "deprecated",
    }[decision]
    report = {
        "review_schema": "caf.workflow_artifact_review.v1",
        "artifact_path": str(artifact_path),
        "workflow_id": workflow.get("workflow_id"),
        "workflow_version": workflow.get("version"),
        "source_intent_id": workflow.get("source_intent_id"),
        "source_reference": generation.get("source_reference"),
        "reviewed_at": reviewed_at or _now(),
        "reviewer": reviewer,
        "decision": decision,
        "decision_allowed": decision_allowed,
        "decision_reason": decision_reason,
        "recommended_workflow_status": recommended_status,
        "review_required": generation.get("review_required", True),
        "notes": notes,
        "summary": {
            "step_count": len(_steps(workflow)),
            "field_count": len(_fields(workflow)),
            "blocking_findings": len([f for f in findings if f.severity == "blocking"]),
            "warning_findings": len([f for f in findings if f.severity == "warning"]),
        },
        "highlights": {
            "steps": _highlight_steps(workflow),
            "database_mappings": _highlight_mappings(workflow),
        },
        "findings": [finding.to_dict() for finding in findings],
        "uncertain_mappings": generation.get("uncertain_mappings", []),
    }
    return ReviewResult(report=report, findings=findings)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Workflow Artifact Review",
        "",
        f"- Workflow: `{report.get('workflow_id')}` `{report.get('workflow_version')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Decision allowed: `{report.get('decision_allowed')}`",
        f"- Reason: {report.get('decision_reason')}",
        f"- Reviewer: {report.get('reviewer')}",
        f"- Reviewed at: {report.get('reviewed_at')}",
        "",
        "## Findings",
    ]
    findings = report.get("findings")
    if isinstance(findings, list) and findings:
        for finding in findings:
            if isinstance(finding, dict):
                lines.append(
                    "- "
                    f"`{finding.get('severity')}` `{finding.get('kind')}` "
                    f"`{finding.get('path')}`: {finding.get('message')}"
                )
    else:
        lines.append("- None")
    lines.extend(["", "## Steps"])
    steps = report.get("highlights", {}).get("steps", [])
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                lines.append(
                    "- "
                    f"`{step.get('step_id')}` -> `{step.get('field_id')}`: "
                    f"{step.get('prompt')}"
                )
    lines.extend(["", "## Database Mappings"])
    mappings = report.get("highlights", {}).get("database_mappings", [])
    if isinstance(mappings, list):
        for mapping in mappings:
            if isinstance(mapping, dict):
                lines.append(
                    "- "
                    f"`{mapping.get('field_id')}` "
                    f"`{mapping.get('storage_kind')}` -> "
                    f"`{mapping.get('storage_target')}`"
                )
    return "\n".join(lines) + "\n"


def render_report(report: dict[str, Any], *, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report, indent=2) + "\n"
    if output_format == "md":
        return render_markdown(report)
    raise ValueError(f"unsupported report format: {output_format}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", help="Draft workflow artifact JSON or TOML file.")
    parser.add_argument(
        "--decision",
        choices=("approve", "request_changes", "retire"),
        default="request_changes",
        help="Reviewer decision to record.",
    )
    parser.add_argument("--reviewer", default="unassigned", help="Reviewer name.")
    parser.add_argument("--notes", default="", help="Reviewer notes.")
    parser.add_argument("--ack-uncertain", action="store_true")
    parser.add_argument("--output", help="Review report path. Defaults to stdout.")
    parser.add_argument(
        "--format",
        choices=("json", "md"),
        help="Report format. Defaults to JSON unless output ends in .md.",
    )
    parser.add_argument("--reviewed-at", help="Override review timestamp for tests.")
    args = parser.parse_args(argv)

    artifact = Path(args.artifact)
    if not artifact.exists():
        print(f"error: artifact not found: {artifact}", file=sys.stderr)
        return 1
    output = Path(args.output) if args.output else None
    output_format = args.format or ("md" if output and output.suffix.lower() == ".md" else "json")
    try:
        result = review_artifact(
            artifact,
            decision=args.decision,
            reviewer=args.reviewer,
            notes=args.notes,
            reviewed_at=args.reviewed_at,
            ack_uncertain=args.ack_uncertain,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    rendered = render_report(result.report, output_format=output_format)
    if output is None:
        sys.stdout.write(rendered)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
        print(f"wrote {output}")
    if not result.report["decision_allowed"]:
        print(f"error: {result.report['decision_reason']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
