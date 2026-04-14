from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.learning_core import (
    append_jsonl,
    bootstrap_seed_lessons,
    build_publish_command,
    classify_tool,
    ensure_state_tree,
    extract_candidates,
    finalize_session,
    load_json,
    record_post_tool,
    record_pre_tool,
    redact_text,
    promote_candidate,
    retrieve_lessons,
    rollback_lesson,
)


class HookRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name)
        self.seed_file = self.state_dir / "seed-patterns.json"
        self.seed_file.write_text(
            json.dumps(
                {
                    "patterns": {
                        "search_before_creating_components": {
                            "id": "pat-seed-001",
                            "pattern": "Search the codebase before adding a new component.",
                            "category": "development",
                            "target_skills": ["self-improving-agent", "code-reviewer"],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        self.env = patch.dict(
            "os.environ",
            {
                "SELF_IMPROVING_AGENT_STATE_DIR": str(self.state_dir),
                "SELF_IMPROVING_AGENT_SEED_PATTERNS": str(self.seed_file),
                "SELF_IMPROVING_AGENT_DISABLE_BLOODBANK": "1",
                "SELF_IMPROVING_AGENT_AGENT_NAME": "test-agent",
            },
        )
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.temp_dir.cleanup()

    def test_redact_text_strips_secrets(self) -> None:
        value = "token=sk-secretsecretsecret bearer abcdefghijklmnop"
        redacted = redact_text(value)
        self.assertIn("[REDACTED]", redacted)
        self.assertNotIn("sk-secretsecretsecret", redacted)

    def test_classify_tool_marks_verification(self) -> None:
        decision_type, tags, preview = classify_tool("Bash", json.dumps({"command": "uv run pytest tests/test_x.py"}))
        self.assertEqual(decision_type, "verification_step")
        self.assertIn("verification", tags)
        self.assertIn("command=uv run pytest tests/test_x.py", preview)

    def test_record_tool_flow_creates_observation(self) -> None:
        record_pre_tool(None, "Bash", json.dumps({"command": "uv run pytest tests/test_x.py"}))
        observation = record_post_tool(None, "Bash", "1 failed, 3 passed", 1)

        self.assertEqual(observation["decision_type"], "verification_step")
        self.assertEqual(observation["outcome"], "failure")
        self.assertEqual(observation["failure_mode"], "verification_failed")

        paths = ensure_state_tree(None)
        session = load_json(paths["current_session"], {})
        self.assertEqual(len(session["observations"]), 1)

    def test_finalize_session_extracts_candidate_after_repeated_episode_failures(self) -> None:
        paths = ensure_state_tree(None)
        episode_one = {
            "episode_id": "11111111-1111-1111-1111-111111111111",
            "agent_name": "test-agent",
            "session_key": "s1",
            "summary": "verification failed once",
            "outcome": "failure",
            "source_observation_ids": ["o1"],
            "task_tags": ["verification"],
            "failure_mode": "verification_failed",
            "fix_summary": None,
            "user_feedback_score": None,
            "user_feedback_summary": None,
        }
        episode_two = {
            "episode_id": "22222222-2222-2222-2222-222222222222",
            "agent_name": "test-agent",
            "session_key": "s2",
            "summary": "verification failed twice",
            "outcome": "failure",
            "source_observation_ids": ["o2"],
            "task_tags": ["verification"],
            "failure_mode": "verification_failed",
            "fix_summary": None,
            "user_feedback_score": None,
            "user_feedback_summary": None,
        }
        append_jsonl(paths["episodes"], episode_one)
        append_jsonl(paths["episodes"], episode_two)

        candidates = extract_candidates([episode_one, episode_two], paths)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["priority"], "high")
        self.assertEqual(candidates[0]["failure_mode"], "verification_failed")

    def test_promote_retrieve_and_rollback_lesson(self) -> None:
        paths = ensure_state_tree(None)
        bootstrap_seed_lessons(paths)
        candidate = {
            "candidate_id": "33333333-3333-3333-3333-333333333333",
            "rule_text": "Run focused verification before ending the session.",
            "supporting_episode_ids": ["e1", "e2"],
            "scope_skills": ["self-improving-agent"],
            "trigger_tags": ["testing"],
            "priority": "high",
            "rationale": "Repeated misses",
            "rule_key": "verification_failed",
            "created_at": "2026-04-05T00:00:00Z",
        }
        append_jsonl(paths["open_candidates"], candidate)

        lesson = promote_candidate(paths, candidate["candidate_id"], "active", 30)
        lessons = retrieve_lessons(paths, "self-improving-agent", ["testing"], limit=5)
        lesson_ids = {item["lesson_id"] for item in lessons}

        self.assertIn(lesson["lesson_id"], lesson_ids)

        rollback = rollback_lesson(paths, lesson["lesson_id"], "bad signal", "full")
        self.assertEqual(rollback["rollback_scope"], "full")

        active = load_json(paths["active_lessons"], {"lessons": []})
        self.assertNotIn(lesson["lesson_id"], {item["lesson_id"] for item in active["lessons"]})

    def test_build_publish_command_uses_cli_surface(self) -> None:
        command = build_publish_command(
            "agent.learning.observation.recorded",
            {"observation_id": "44444444-4444-4444-4444-444444444444"},
            "44444444-4444-4444-4444-444444444444",
            ["55555555-5555-5555-5555-555555555555"],
        )
        self.assertEqual(command[:4], ["uv", "run", "bb", "publish"])
        self.assertIn("--permissive-validation", command)
        self.assertIn("--correlation-id", command)


if __name__ == "__main__":
    unittest.main()
