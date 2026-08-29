"""The contract every collector implements.

Three things live here:

``SectionResult``
    What a collector returns. ``to_artifact`` turns it into a SectionArtifact v2
    that ``validate_section_artifact`` accepts -- including deriving ``reason``
    and refusing to emit a bare non-complete status.

``allowlist``
    The structural field allowlist. Collector output is bounded by *naming the
    keys that may survive*, not by pattern-matching for things that must not.
    An allowlist cannot false-positive (a denylist regex took this pipeline
    down on 2026-07-25) and cannot miss a token shape nobody has seen yet.

``run_collector``
    Runs a collector so that any exception becomes ``status="failed"`` with the
    exception text as the reason. A crashing collector degrades the report; it
    never aborts the run and never quietly disappears from it.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportctl_contracts import (  # noqa: E402
    SECTION_ARTIFACT_VERSION,
    SECTION_STATUSES,
    ConfigError,
    validate_section_artifact,
)

DEFAULT_BYTE_CAP = 256_000
SCALAR_TYPES = (bool, int, float, str)

#: Keys a SectionResult carries.
SECTION_RESULT_FIELDS = frozenset(
    {
        "id",
        "status",
        "reason",
        "summary",
        "metrics",
        "detail",
        "caveats",
        "generated_at",
        "fresh_until",
    }
)

#: The only keys allowed to reach the narrator. Anything else a collector
#: attaches is dropped before the LLM ever sees it.
NARRATOR_FIELDS = frozenset(
    {
        "report_date",
        "run_id",
        "sections",
        "id",
        "topic_id",
        "title",
        "status",
        "reason",
        "summary",
        "metrics",
        "detail",
        "caveats",
        "generated_at",
        "fresh_until",
    }
)

#: Keys whose *values* are data maps rather than schema objects. Their keys are
#: not known in advance, so they are copied wholesale -- but only scalar leaves
#: survive, which keeps them just as bounded as an explicitly named key.
OPAQUE_KEYS = frozenset({"metrics"})


def _scalar_map(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(key, str) and key.strip() and isinstance(item, SCALAR_TYPES)
    }


def allowlist(
    obj: Any, allowed_keys: Any, *, opaque_keys: Any = OPAQUE_KEYS
) -> Any:
    """Return a copy of ``obj`` containing only ``allowed_keys``, recursively.

    Mappings keep only the named keys and are filtered at every depth; sequences
    are mapped element-wise; scalars pass through. Keys listed in ``opaque_keys``
    hold caller-defined data maps, so their contents are kept but reduced to
    scalar leaves.
    """
    allowed = frozenset(allowed_keys)
    opaque = frozenset(opaque_keys)

    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                if key not in allowed:
                    continue
                result[key] = _scalar_map(item) if key in opaque else walk(item)
            return result
        if isinstance(value, (list, tuple)):
            return [walk(item) for item in value]
        return value

    return walk(obj)


def _iso(value: Any) -> str | None:
    if isinstance(value, dt.datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=dt.UTC)
        return moment.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _byte_size(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8"))


@dataclass
class SectionResult:
    """What a collector returns. Status is never assumed; it is always stated."""

    id: str
    status: str = "complete"
    reason: str = ""
    summary: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    detail: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    generated_at: Any = None
    fresh_until: Any = None

    def to_artifact(
        self,
        run_id: str,
        max_age_hours: int,
        *,
        byte_cap: int = DEFAULT_BYTE_CAP,
    ) -> dict[str, Any]:
        caveats = [item for item in self.caveats if isinstance(item, str) and item.strip()]

        status = self.status
        if status not in SECTION_STATUSES:
            caveats.append(f"collector reported unknown status {self.status!r}")
            status = "failed"

        generated_at = _iso(self.generated_at) or _iso(dt.datetime.now(dt.UTC))
        fresh_until = _iso(self.fresh_until)
        if fresh_until is None:
            try:
                base = dt.datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            except ValueError:
                base = dt.datetime.now(dt.UTC)
            fresh_until = _iso(base + dt.timedelta(hours=int(max_age_hours)))

        summary = self.summary.strip() if isinstance(self.summary, str) else ""
        if not summary:
            summary = f"{self.id}: collector produced no summary"
            caveats.append("collector produced no summary")

        reason = self.reason.strip() if isinstance(self.reason, str) else ""
        if status != "complete" and not reason:
            reason = "collector reported a non-complete status without a reason"
            caveats.append(reason)

        metrics = _scalar_map(self.metrics)
        if isinstance(self.metrics, dict) and len(metrics) != len(self.metrics):
            caveats.append("dropped non-scalar metric values")

        detail = [item for item in (self.detail or []) if isinstance(item, str)]
        if len(detail) != len(self.detail or []):
            caveats.append("dropped non-string detail lines")

        artifact: dict[str, Any] = {
            "schema_version": SECTION_ARTIFACT_VERSION,
            "run_id": run_id,
            "topic_id": self.id,
            "generated_at": generated_at,
            "fresh_until": fresh_until,
            "status": status,
            "summary": summary,
            "caveats": caveats,
        }
        if reason:
            artifact["reason"] = reason
        if metrics:
            artifact["metrics"] = metrics
        if detail:
            artifact["detail"] = detail
        artifact = enforce_byte_cap(artifact, byte_cap)
        return validate_section_artifact(artifact, self.id)


def _truncation_caveat(kept: int, total: int, cap: int) -> str:
    return f"detail truncated: showing {kept} of {total} lines to stay within the {cap}-byte cap"


def enforce_byte_cap(artifact: dict[str, Any], cap: int = DEFAULT_BYTE_CAP) -> dict[str, Any]:
    """Shrink an artifact to ``cap`` bytes, recording every drop in ``caveats``.

    Nothing is ever removed silently: detail lines go first and the count is
    stated, then metrics, then the summary is clipped. If even the bookkeeping
    does not fit, that is a defect and it raises rather than lying about size.
    """
    if _byte_size(artifact) <= cap:
        return artifact
    base_caveats = list(artifact.get("caveats", []))
    total = len(artifact.get("detail", []))
    detail = list(artifact.get("detail", []))
    while detail:
        detail.pop()
        candidate = dict(artifact)
        candidate["caveats"] = base_caveats + [_truncation_caveat(len(detail), total, cap)]
        if detail:
            candidate["detail"] = detail
        else:
            candidate.pop("detail", None)
        if _byte_size(candidate) <= cap:
            return candidate

    candidate = dict(artifact)
    candidate.pop("detail", None)
    caveats = base_caveats + ([_truncation_caveat(0, total, cap)] if total else [])
    if "metrics" in candidate:
        candidate.pop("metrics")
        caveats = caveats + [f"metrics dropped to stay within the {cap}-byte cap"]
    candidate["caveats"] = caveats
    if _byte_size(candidate) <= cap:
        return candidate

    overflow = _byte_size(candidate) - cap
    summary = candidate["summary"]
    clipped = summary[: max(1, len(summary) - overflow - 64)]
    candidate["summary"] = clipped
    candidate["caveats"] = caveats + [f"summary clipped to stay within the {cap}-byte cap"]
    if _byte_size(candidate) > cap:
        raise ConfigError(
            f"section {artifact['topic_id']} cannot be reduced to {cap} bytes without "
            "discarding its own truncation record"
        )
    return candidate


def bound_for_narrator(
    value: Any, *, cap: int = DEFAULT_BYTE_CAP, fields: Any = NARRATOR_FIELDS
) -> Any:
    """Field-allowlist then size-check anything on its way to the narrator."""
    bounded = allowlist(value, fields)
    if _byte_size(bounded) > cap:
        raise ConfigError(f"narrator input exceeds the {cap}-byte cap after allowlisting")
    return bounded


def run_collector(
    fn: Callable[[dict[str, Any]], SectionResult], section_cfg: dict[str, Any]
) -> SectionResult:
    """Call a collector and convert *any* failure into an honest failed result."""
    section_id = section_cfg.get("id", "unknown") if isinstance(section_cfg, dict) else "unknown"
    try:
        result = fn(section_cfg)
    except Exception as exc:  # noqa: BLE001 - degrading the report is the whole point
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"{type(exc).__name__}: {exc}",
            summary=f"{section_id}: collector raised {type(exc).__name__}",
        )
    if not isinstance(result, SectionResult):
        return SectionResult(
            id=section_id,
            status="failed",
            reason=f"collector returned {type(result).__name__}, expected SectionResult",
            summary=f"{section_id}: collector returned the wrong type",
        )
    if result.id != section_id:
        result.caveats = list(result.caveats) + [
            f"collector returned id {result.id!r}; configured id {section_id!r} used instead"
        ]
        result.id = section_id
    return result
