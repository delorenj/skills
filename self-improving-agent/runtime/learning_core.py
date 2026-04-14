from __future__ import annotations

import json
import os
import re
import socket
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5


DEFAULT_AGENT_NAME = "codex"
DEFAULT_STATE_DIR = Path.home() / ".local" / "share" / "33god" / "self-improving-agent"
DEFAULT_BLOODBANK_ROOT = Path.home() / "code" / "33GOD" / "bloodbank"
REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_PATTERNS_PATH = REPO_ROOT / "memory" / "semantic-patterns.json"

TEST_TOKENS = (
    "pytest",
    "bun test",
    "npm test",
    "pnpm test",
    "yarn test",
    "mise run test",
    "uv run pytest",
    "python -m unittest",
)
SEARCH_TOKENS = ("rg ", "grep ", "fd ", "find ", "codebase-retrieval")
INSPECTION_TOKENS = ("git diff", "git status", "sed -n", "cat ", "ls ", "open ")
MUTATION_TOOLS = {"write", "edit"}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{12,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]{4,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

RULE_TEMPLATES = {
    "verification_failed": {
        "rule_text": "Run the narrowest relevant verification after edits and keep iterating until it passes or the blocker is recorded.",
        "scope_skills": ["self-improving-agent", "code-reviewer", "debugger"],
        "trigger_tags": ["verification", "testing"],
        "priority": "high",
        "rationale": "Repeated verification failures indicate the session stopped before the fix was proven.",
    },
    "search_skipped": {
        "rule_text": "Search the existing codebase before adding a new component, type, or workflow surface.",
        "scope_skills": ["self-improving-agent", "architecting-solutions", "code-reviewer"],
        "trigger_tags": ["search", "architecture"],
        "priority": "high",
        "rationale": "Repeated misses suggest the codebase was extended before reuse options were checked.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def hostname() -> str:
    return socket.gethostname()


def agent_name() -> str:
    return os.environ.get("SELF_IMPROVING_AGENT_AGENT_NAME", DEFAULT_AGENT_NAME)


def state_dir(base_dir: Path | None = None) -> Path:
    if base_dir is not None:
        return base_dir
    configured = os.environ.get("SELF_IMPROVING_AGENT_STATE_DIR")
    return Path(configured).expanduser() if configured else DEFAULT_STATE_DIR


def bloodbank_root() -> Path:
    configured = os.environ.get("SELF_IMPROVING_AGENT_BLOODBANK_ROOT")
    return Path(configured).expanduser() if configured else DEFAULT_BLOODBANK_ROOT


def seed_patterns_path() -> Path:
    configured = os.environ.get("SELF_IMPROVING_AGENT_SEED_PATTERNS")
    return Path(configured).expanduser() if configured else SEED_PATTERNS_PATH


def ensure_state_tree(base_dir: Path | None = None) -> dict[str, Path]:
    root = state_dir(base_dir)
    paths = {
        "root": root,
        "working_dir": root / "working",
        "candidates_dir": root / "candidates",
        "lessons_dir": root / "lessons",
        "current_session": root / "working" / "current_session.json",
        "last_error": root / "working" / "last_error.json",
        "session_end": root / "working" / "session_end.json",
        "observations": root / "working" / "observations.jsonl",
        "events": root / "working" / "events.jsonl",
        "episodes": root / "episodes.jsonl",
        "open_candidates": root / "candidates" / "open.jsonl",
        "candidate_validations": root / "candidates" / "validated.jsonl",
        "candidate_rejections": root / "candidates" / "rejected.jsonl",
        "active_lessons": root / "lessons" / "active.json",
        "archived_lessons": root / "lessons" / "archive.jsonl",
    }
    for key in ("working_dir", "candidates_dir", "lessons_dir"):
        paths[key].mkdir(parents=True, exist_ok=True)
    if not paths["active_lessons"].exists():
        atomic_write_json(paths["active_lessons"], {"lessons": []})
    return paths


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True))
        handle.write("\n")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def maybe_json(raw: str | None) -> Any:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def redact_text(value: str | None, limit: int = 500) -> str | None:
    if value is None:
        return None
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    redacted = re.sub(r"\s+", " ", redacted).strip()
    if len(redacted) <= limit:
        return redacted or None
    return f"{redacted[:limit - 3]}..."


def summarize_blob(raw: str | None) -> str | None:
    parsed = maybe_json(raw)
    if parsed is None:
        return None
    if isinstance(parsed, dict):
        preferred_keys = (
            "command",
            "path",
            "paths",
            "url",
            "query",
            "q",
            "title",
            "name",
            "message",
        )
        fragments: list[str] = []
        for key in preferred_keys:
            if key in parsed:
                value = parsed[key]
                if isinstance(value, (str, int, float, bool)):
                    fragments.append(f"{key}={value}")
                elif isinstance(value, list):
                    fragments.append(f"{key}[{len(value)}]")
                elif isinstance(value, dict):
                    fragments.append(f"{key}{{{','.join(sorted(value.keys())[:5])}}}")
        if not fragments:
            fragments.append(f"keys={','.join(sorted(parsed.keys())[:8])}")
        return redact_text("; ".join(fragments))
    if isinstance(parsed, list):
        return redact_text(f"list[{len(parsed)}]")
    return redact_text(str(parsed))


def classify_tool(tool_name: str, tool_input: str | None) -> tuple[str, list[str], str | None]:
    normalized_tool = (tool_name or "unknown").strip()
    preview = summarize_blob(tool_input)
    preview_lower = (preview or "").lower()
    tags = {normalized_tool.lower()}
    decision_type = "tool_execution"

    if normalized_tool.lower() == "bash":
        if any(token in preview_lower for token in TEST_TOKENS):
            decision_type = "verification_step"
            tags.add("verification")
            tags.add("testing")
        elif any(token in preview_lower for token in SEARCH_TOKENS):
            decision_type = "search_before_create"
            tags.add("search")
        elif any(token in preview_lower for token in INSPECTION_TOKENS):
            decision_type = "inspection_step"
            tags.add("inspection")
    elif normalized_tool.lower() in MUTATION_TOOLS:
        decision_type = "mutation_step"
        tags.add("mutation")

    return decision_type, sorted(tags), preview


def verification_status(decision_type: str, exit_code: int) -> str | None:
    if decision_type != "verification_step":
        return "not_run"
    return "passed" if exit_code == 0 else "failed"


def failure_mode_for(decision_type: str, exit_code: int, output_preview: str | None) -> str | None:
    if exit_code == 0:
        return None
    output_lower = (output_preview or "").lower()
    if decision_type == "verification_step":
        return "verification_failed"
    if decision_type == "search_before_create" and "no such file" in output_lower:
        return "search_skipped"
    if "timeout" in output_lower:
        return "timeout"
    if "permission denied" in output_lower:
        return "permission_denied"
    return "command_failed"


def derive_outcome(decision_type: str, exit_code: int) -> str:
    if exit_code != 0:
        return "failure"
    if decision_type == "inspection_step":
        return "neutral"
    return "success"


def stable_session_correlation(session_key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"self-improving-agent:{session_key}"))


def stable_uuid(prefix: str, raw_value: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"{prefix}:{raw_value}"))


def create_session_state(existing: dict[str, Any] | None = None) -> dict[str, Any]:
    session_key = os.environ.get("SELF_IMPROVING_AGENT_SESSION_KEY")
    if not session_key and existing:
        session_key = existing.get("session_key")
    session_key = session_key or f"session-{uuid4()}"
    started_at = existing.get("started_at") if existing else utc_now()
    return {
        "session_key": session_key,
        "correlation_id": stable_session_correlation(session_key),
        "agent_name": agent_name(),
        "started_at": started_at,
        "last_updated": utc_now(),
        "pending_tool": None,
        "observations": existing.get("observations", []) if existing else [],
        "event_log": existing.get("event_log", []) if existing else [],
    }


def bootstrap_seed_lessons(paths: dict[str, Path]) -> None:
    active = load_json(paths["active_lessons"], {"lessons": []})
    if active.get("lessons"):
        return

    seed_file = seed_patterns_path()
    if not seed_file.exists():
        return

    patterns = load_json(seed_file, {"patterns": {}})
    lessons: list[dict[str, Any]] = []
    for key, pattern in patterns.get("patterns", {}).items():
        lesson_text = pattern.get("pattern") or pattern.get("name")
        if not lesson_text:
            continue
        lessons.append(
            {
                "lesson_id": stable_uuid("seed-lesson", key),
                "candidate_id": stable_uuid("seed-candidate", key),
                "lesson_text": lesson_text,
                "scope_skills": pattern.get("target_skills", ["self-improving-agent"]),
                "trigger_tags": sorted(
                    {
                        key,
                        pattern.get("category", "seed"),
                        *pattern.get("target_skills", []),
                    }
                ),
                "rollout_status": "active",
                "lesson_version": "1.0.0",
                "ttl_days": 90,
                "promoted_at": utc_now(),
                "source_pattern_id": pattern.get("id"),
                "source": "seed-pattern",
            }
        )

    atomic_write_json(paths["active_lessons"], {"lessons": lessons})


def load_or_create_session(base_dir: Path | None = None) -> tuple[dict[str, Any], dict[str, Path]]:
    paths = ensure_state_tree(base_dir)
    existing = load_json(paths["current_session"], None)
    if existing and not existing.get("closed_at"):
        return existing, paths
    state = create_session_state(None)
    atomic_write_json(paths["current_session"], state)
    return state, paths


def save_session(state: dict[str, Any], paths: dict[str, Path]) -> None:
    state["last_updated"] = utc_now()
    atomic_write_json(paths["current_session"], state)


def latest_non_null(values: list[str | None]) -> str | None:
    for value in reversed(values):
        if value:
            return value
    return None


def summarize_episode(observations: list[dict[str, Any]], outcome: str, failure_mode: str | None) -> str:
    tool_counter = Counter(observation.get("tool_name") for observation in observations if observation.get("tool_name"))
    decision_counter = Counter(observation.get("decision_type") for observation in observations)
    tool_summary = tool_counter.most_common(1)[0][0] if tool_counter else "tools"
    decision_summary = decision_counter.most_common(1)[0][0] if decision_counter else "steps"
    if failure_mode:
        return f"Session ended {outcome} after {len(observations)} observations; dominant issue was {failure_mode} during {decision_summary} via {tool_summary}."
    return f"Session ended {outcome} after {len(observations)} observations; primary work was {decision_summary} via {tool_summary}."


def build_episode_payload(session: dict[str, Any], feedback_score: int | None = None, feedback_summary: str | None = None) -> dict[str, Any] | None:
    observations = session.get("observations", [])
    if not observations:
        return None

    outcomes = {observation["outcome"] for observation in observations}
    failures = [observation["failure_mode"] for observation in observations if observation.get("failure_mode")]
    task_tags = sorted({tag for observation in observations for tag in observation.get("task_tags", [])})
    outcome = "mixed" if len(outcomes) > 1 else ("failure" if "failure" in outcomes else "success")
    failure_mode = Counter(failures).most_common(1)[0][0] if failures else None
    fix_summary = latest_non_null([observation.get("fix_applied") for observation in observations])

    return {
        "episode_id": str(uuid4()),
        "agent_name": session["agent_name"],
        "session_key": session["session_key"],
        "summary": summarize_episode(observations, outcome, failure_mode),
        "outcome": outcome,
        "source_observation_ids": [observation["observation_id"] for observation in observations],
        "task_tags": task_tags,
        "failure_mode": failure_mode,
        "fix_summary": fix_summary,
        "user_feedback_score": feedback_score,
        "user_feedback_summary": redact_text(feedback_summary),
    }


def candidate_status_index(paths: dict[str, Path]) -> dict[str, str]:
    bootstrap_seed_lessons(paths)
    index: dict[str, str] = {}
    for row in load_jsonl(paths["open_candidates"]):
        index[row["candidate_id"]] = "open"
    for row in load_jsonl(paths["candidate_validations"]):
        index[row["candidate_id"]] = row["decision"]
    for row in load_jsonl(paths["candidate_rejections"]):
        index[row["candidate_id"]] = "rejected"
    active_lessons = load_json(paths["active_lessons"], {"lessons": []})
    for lesson in active_lessons.get("lessons", []):
        index[lesson["candidate_id"]] = "active"
    return index


def extract_candidates(episodes: list[dict[str, Any]], paths: dict[str, Path]) -> list[dict[str, Any]]:
    bootstrap_seed_lessons(paths)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for episode in episodes:
        failure_mode = episode.get("failure_mode")
        if failure_mode:
            grouped.setdefault(failure_mode, []).append(episode)

    extracted: list[dict[str, Any]] = []
    for failure_mode, grouped_episodes in grouped.items():
        template = RULE_TEMPLATES.get(failure_mode)
        if template is None or len(grouped_episodes) < 2:
            continue

        already_seen = any(
            candidate.get("rule_key") == failure_mode
            for candidate in load_jsonl(paths["open_candidates"])
        )
        if not already_seen:
            active = load_json(paths["active_lessons"], {"lessons": []})
            for lesson in active.get("lessons", []):
                if lesson.get("source") == "seed-pattern":
                    continue
                if lesson.get("rule_key") == failure_mode:
                    already_seen = True
                    break
        if already_seen:
            continue

        candidate_id = str(uuid4())
        payload = {
            "candidate_id": candidate_id,
            "rule_text": template["rule_text"],
            "supporting_episode_ids": [episode["episode_id"] for episode in grouped_episodes[-3:]],
            "scope_skills": template["scope_skills"],
            "trigger_tags": template["trigger_tags"],
            "priority": template["priority"],
            "rationale": template["rationale"],
            "failure_mode": failure_mode,
            "rule_key": failure_mode,
            "created_at": utc_now(),
        }
        extracted.append(payload)
    return extracted


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    support_count = len(candidate.get("supporting_episode_ids", []))
    decision = "needs_more_data"
    notes = f"Observed {support_count} supporting episode(s); automatic promotion remains disabled until a human review confirms the rule."
    return {
        "candidate_id": candidate["candidate_id"],
        "eval_suite": "self-improving-agent.local-heuristics.v1",
        "decision": decision,
        "replay_pass_rate_before": None,
        "replay_pass_rate_after": None,
        "regression_failures": None,
        "notes": notes,
        "validated_at": utc_now(),
    }


def promote_candidate(paths: dict[str, Path], candidate_id: str, rollout_status: str, ttl_days: int) -> dict[str, Any]:
    bootstrap_seed_lessons(paths)
    candidates = [candidate for candidate in load_jsonl(paths["open_candidates"]) if candidate["candidate_id"] == candidate_id]
    if not candidates:
        raise ValueError(f"Unknown candidate_id: {candidate_id}")
    candidate = candidates[-1]
    lesson = {
        "lesson_id": str(uuid4()),
        "candidate_id": candidate_id,
        "lesson_text": candidate["rule_text"],
        "scope_skills": candidate["scope_skills"],
        "trigger_tags": candidate.get("trigger_tags", []),
        "rollout_status": rollout_status,
        "lesson_version": "1.0.0",
        "ttl_days": ttl_days,
        "promoted_at": utc_now(),
        "rule_key": candidate.get("rule_key"),
        "source": "promoted-candidate",
    }
    active = load_json(paths["active_lessons"], {"lessons": []})
    active["lessons"] = [
        existing for existing in active.get("lessons", []) if existing["candidate_id"] != candidate_id
    ]
    active["lessons"].append(lesson)
    atomic_write_json(paths["active_lessons"], active)
    return lesson


def reject_candidate(paths: dict[str, Path], candidate_id: str, reason: str, blocking_failures: list[str] | None = None) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "rejection_reason": reason,
        "blocking_failures": blocking_failures or [],
        "rejected_at": utc_now(),
    }


def rollback_lesson(paths: dict[str, Path], lesson_id: str, reason: str, rollback_scope: str, replacement_lesson_id: str | None = None) -> dict[str, Any]:
    active = load_json(paths["active_lessons"], {"lessons": []})
    lessons = active.get("lessons", [])
    lesson = next((item for item in lessons if item["lesson_id"] == lesson_id), None)
    if lesson is None:
        raise ValueError(f"Unknown lesson_id: {lesson_id}")

    active["lessons"] = [item for item in lessons if item["lesson_id"] != lesson_id]
    atomic_write_json(paths["active_lessons"], active)
    append_jsonl(paths["archived_lessons"], {**lesson, "archived_at": utc_now()})

    return {
        "lesson_id": lesson_id,
        "rollback_reason": reason,
        "rollback_scope": rollback_scope,
        "replacement_lesson_id": replacement_lesson_id,
        "rolled_back_at": utc_now(),
    }


def retrieve_lessons(paths: dict[str, Path], target_skill: str | None, task_tags: list[str], limit: int = 3) -> list[dict[str, Any]]:
    bootstrap_seed_lessons(paths)
    active = load_json(paths["active_lessons"], {"lessons": []})
    lessons = []
    tag_set = set(task_tags)

    for lesson in active.get("lessons", []):
        if lesson.get("rollout_status") != "active":
            continue
        scope_skills = set(lesson.get("scope_skills", []))
        if target_skill and scope_skills and target_skill not in scope_skills:
            continue
        trigger_tags = set(lesson.get("trigger_tags", []))
        overlap = len(tag_set & trigger_tags) if tag_set and trigger_tags else 0
        lessons.append((overlap, lesson))

    lessons.sort(key=lambda item: (-item[0], item[1]["promoted_at"]))
    return [lesson for _, lesson in lessons[:limit]]


def build_publish_command(
    event_type: str,
    payload: dict[str, Any],
    event_id: str,
    correlation_ids: list[str],
) -> list[str]:
    command = [
        "uv",
        "run",
        "bb",
        "publish",
        event_type,
        "--json",
        "-",
        "--event-id",
        event_id,
        "--source-type",
        "hook",
        "--source-app",
        "self-improving-agent",
        "--source-host",
        hostname(),
        "--permissive-validation",
    ]
    for correlation_id in correlation_ids:
        command.extend(["--correlation-id", correlation_id])
    return command


def publish_event(
    paths: dict[str, Path],
    event_type: str,
    payload: dict[str, Any],
    event_id: str,
    correlation_ids: list[str],
) -> dict[str, Any]:
    command = build_publish_command(event_type, payload, event_id, correlation_ids)
    envelope = {
        "event_id": event_id,
        "event_type": event_type,
        "correlation_ids": correlation_ids,
        "payload": payload,
        "timestamp": utc_now(),
        "source_app": "self-improving-agent",
    }

    if os.environ.get("SELF_IMPROVING_AGENT_DISABLE_BLOODBANK") == "1":
        envelope["publish_status"] = "disabled"
        append_jsonl(paths["events"], envelope)
        return envelope

    root = bloodbank_root()
    if not root.exists():
        envelope["publish_status"] = "missing-bloodbank-root"
        append_jsonl(paths["events"], envelope)
        return envelope

    try:
        completed = subprocess.run(
            command,
            cwd=root,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        envelope["publish_status"] = "spawn-failed"
        envelope["publish_error"] = str(exc)
        append_jsonl(paths["events"], envelope)
        return envelope

    envelope["publish_status"] = "published" if completed.returncode == 0 else "failed"
    if completed.stdout.strip():
        envelope["publish_stdout"] = redact_text(completed.stdout.strip())
    if completed.stderr.strip():
        envelope["publish_stderr"] = redact_text(completed.stderr.strip())
    append_jsonl(paths["events"], envelope)
    return envelope


def record_pre_tool(base_dir: Path | None, tool_name: str, tool_input: str | None) -> dict[str, Any]:
    session, paths = load_or_create_session(base_dir)
    decision_type, task_tags, input_preview = classify_tool(tool_name, tool_input)
    session["pending_tool"] = {
        "tool_name": tool_name,
        "decision_type": decision_type,
        "task_tags": task_tags,
        "input_preview": input_preview,
        "started_at": utc_now(),
    }
    save_session(session, paths)
    return session


def record_post_tool(base_dir: Path | None, tool_name: str, tool_output: str | None, exit_code: int) -> dict[str, Any]:
    session, paths = load_or_create_session(base_dir)
    pending = session.get("pending_tool")
    if pending and pending.get("tool_name") == tool_name:
        decision_type = pending["decision_type"]
        task_tags = pending["task_tags"]
        input_preview = pending.get("input_preview")
    else:
        decision_type, task_tags, input_preview = classify_tool(tool_name, None)

    output_preview = summarize_blob(tool_output) or redact_text(tool_output)
    verification = verification_status(decision_type, exit_code)
    observation_id = str(uuid4())
    failure_mode = failure_mode_for(decision_type, exit_code, output_preview)
    observation = {
        "observation_id": observation_id,
        "agent_name": session["agent_name"],
        "session_key": session["session_key"],
        "decision_type": decision_type,
        "outcome": derive_outcome(decision_type, exit_code),
        "task_tags": task_tags,
        "source_event_ids": [],
        "tool_name": tool_name,
        "verification_status": verification,
        "failure_mode": failure_mode,
        "fix_applied": None,
        "notes_preview": output_preview or input_preview,
        "recorded_at": utc_now(),
    }

    session.setdefault("observations", []).append(observation)
    session["pending_tool"] = None
    save_session(session, paths)
    append_jsonl(paths["observations"], observation)

    if observation["outcome"] == "failure":
        atomic_write_json(paths["last_error"], observation)

    publish_event(
        paths,
        "agent.learning.observation.recorded",
        {
            key: observation[key]
            for key in (
                "observation_id",
                "agent_name",
                "session_key",
                "decision_type",
                "outcome",
                "task_tags",
                "source_event_ids",
                "tool_name",
                "verification_status",
                "failure_mode",
                "fix_applied",
                "notes_preview",
            )
            if observation.get(key) is not None
        },
        observation_id,
        [session["correlation_id"]],
    )
    return observation


def finalize_session(base_dir: Path | None, feedback_score: int | None = None, feedback_summary: str | None = None) -> dict[str, Any]:
    session, paths = load_or_create_session(base_dir)
    episode = build_episode_payload(session, feedback_score, feedback_summary)
    result: dict[str, Any] = {"session_key": session["session_key"], "events": []}

    if episode is None:
        atomic_write_json(paths["session_end"], {"session_key": session["session_key"], "ended_at": utc_now(), "observations": 0})
        session["closed_at"] = utc_now()
        save_session(session, paths)
        return result

    append_jsonl(paths["episodes"], episode)
    episode_event = publish_event(
        paths,
        "agent.learning.episode.created",
        {
            key: episode[key]
            for key in (
                "episode_id",
                "agent_name",
                "session_key",
                "summary",
                "outcome",
                "source_observation_ids",
                "task_tags",
                "failure_mode",
                "fix_summary",
                "user_feedback_score",
                "user_feedback_summary",
            )
            if episode.get(key) is not None
        },
        episode["episode_id"],
        [session["correlation_id"]],
    )
    result["events"].append(episode_event)

    episodes = load_jsonl(paths["episodes"])
    candidates = extract_candidates(episodes, paths)
    for candidate in candidates:
        append_jsonl(paths["open_candidates"], candidate)
        candidate_event = publish_event(
            paths,
            "agent.learning.candidate.extracted",
            {
                key: candidate[key]
                for key in (
                    "candidate_id",
                    "rule_text",
                    "supporting_episode_ids",
                    "scope_skills",
                    "trigger_tags",
                    "priority",
                    "rationale",
                )
                if candidate.get(key) is not None
            },
            candidate["candidate_id"],
            [session["correlation_id"]],
        )
        result["events"].append(candidate_event)

        validation = validate_candidate(candidate)
        append_jsonl(paths["candidate_validations"], validation)
        validation_event = publish_event(
            paths,
            "agent.learning.candidate.validated",
            {
                key: validation[key]
                for key in (
                    "candidate_id",
                    "eval_suite",
                    "decision",
                    "replay_pass_rate_before",
                    "replay_pass_rate_after",
                    "regression_failures",
                    "notes",
                )
                if validation.get(key) is not None
            },
            str(uuid4()),
            [session["correlation_id"]],
        )
        result["events"].append(validation_event)

    atomic_write_json(
        paths["session_end"],
        {
            "session_key": session["session_key"],
            "ended_at": utc_now(),
            "observation_count": len(session.get("observations", [])),
            "episode_id": episode["episode_id"],
            "candidate_count": len(candidates),
        },
    )
    session["closed_at"] = utc_now()
    save_session(session, paths)
    return result
