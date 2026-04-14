#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.learning_core import (  # noqa: E402
    append_jsonl,
    ensure_state_tree,
    finalize_session,
    load_or_create_session,
    promote_candidate,
    publish_event,
    record_post_tool,
    record_pre_tool,
    reject_candidate,
    retrieve_lessons,
    rollback_lesson,
)


def read_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def json_dump(data: object) -> None:
    json.dump(data, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def command_pre_tool(_args: argparse.Namespace) -> int:
    tool_name = read_env("TOOL_NAME", "unknown")
    tool_input = read_env("TOOL_INPUT", "")
    session = record_pre_tool(None, tool_name, tool_input)
    json_dump(
        {
            "status": "ok",
            "command": "pre-tool",
            "session_key": session["session_key"],
            "tool_name": tool_name,
        }
    )
    return 0


def command_post_tool(_args: argparse.Namespace) -> int:
    tool_name = read_env("TOOL_NAME", "bash")
    tool_output = read_env("TOOL_OUTPUT", "")
    exit_code = int(read_env("EXIT_CODE", "0") or "0")
    observation = record_post_tool(None, tool_name, tool_output, exit_code)
    json_dump({"status": "ok", "command": "post-tool", "observation_id": observation["observation_id"]})
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    summary = finalize_session(None, args.feedback_score, args.feedback_summary)
    json_dump({"status": "ok", "command": "finalize-session", **summary})
    return 0


def command_promote(args: argparse.Namespace) -> int:
    paths = ensure_state_tree(None)
    lesson = promote_candidate(paths, args.candidate_id, args.rollout_status, args.ttl_days)
    publish_event(
        paths,
        "agent.learning.lesson.promoted",
        {
            key: lesson[key]
            for key in (
                "lesson_id",
                "candidate_id",
                "lesson_text",
                "scope_skills",
                "trigger_tags",
                "rollout_status",
                "lesson_version",
                "ttl_days",
            )
            if lesson.get(key) is not None
        },
        lesson["lesson_id"],
        [],
    )
    json_dump({"status": "ok", "command": "promote-candidate", "lesson": lesson})
    return 0


def command_reject(args: argparse.Namespace) -> int:
    paths = ensure_state_tree(None)
    rejection = reject_candidate(paths, args.candidate_id, args.reason, args.blocking_failure)
    append_jsonl(paths["candidate_rejections"], rejection)
    publish_event(
        paths,
        "agent.learning.lesson.rejected",
        {
            key: rejection[key]
            for key in ("candidate_id", "rejection_reason", "blocking_failures")
            if rejection.get(key) is not None
        },
        str(uuid4()),
        [],
    )
    json_dump({"status": "ok", "command": "reject-candidate", "rejection": rejection})
    return 0


def command_rollback(args: argparse.Namespace) -> int:
    paths = ensure_state_tree(None)
    rollback = rollback_lesson(paths, args.lesson_id, args.reason, args.rollback_scope, args.replacement_lesson_id)
    publish_event(
        paths,
        "agent.learning.lesson.rolled_back",
        {
            key: rollback[key]
            for key in ("lesson_id", "rollback_reason", "rollback_scope", "replacement_lesson_id")
            if rollback.get(key) is not None
        },
        rollback["lesson_id"],
        [],
    )
    json_dump({"status": "ok", "command": "rollback-lesson", "rollback": rollback})
    return 0


def command_retrieve(args: argparse.Namespace) -> int:
    session, paths = load_or_create_session(None)
    lessons = retrieve_lessons(paths, args.target_skill, args.task_tag, args.limit)
    retrieval_id = str(uuid4())
    publish_event(
        paths,
        "agent.learning.retrieval.applied",
        {
            "retrieval_id": retrieval_id,
            "agent_name": session["agent_name"],
            "session_key": session["session_key"],
            "lesson_ids": [lesson["lesson_id"] for lesson in lessons],
            "task_tags": args.task_tag,
            "target_skill": args.target_skill,
        },
        retrieval_id,
        [],
    )
    json_dump({"status": "ok", "command": "retrieve-lessons", "lessons": lessons})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Structured runtime for the self-improving-agent hooks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pre_tool = subparsers.add_parser("pre-tool")
    pre_tool.set_defaults(func=command_pre_tool)

    post_tool = subparsers.add_parser("post-tool")
    post_tool.set_defaults(func=command_post_tool)

    finalize = subparsers.add_parser("finalize-session")
    finalize.add_argument("--feedback-score", type=int, default=None)
    finalize.add_argument("--feedback-summary", default=None)
    finalize.set_defaults(func=command_finalize)

    promote = subparsers.add_parser("promote-candidate")
    promote.add_argument("candidate_id")
    promote.add_argument("--rollout-status", default="active", choices=["shadow", "active"])
    promote.add_argument("--ttl-days", type=int, default=30)
    promote.set_defaults(func=command_promote)

    reject = subparsers.add_parser("reject-candidate")
    reject.add_argument("candidate_id")
    reject.add_argument("--reason", required=True)
    reject.add_argument("--blocking-failure", action="append", default=[])
    reject.set_defaults(func=command_reject)

    rollback = subparsers.add_parser("rollback-lesson")
    rollback.add_argument("lesson_id")
    rollback.add_argument("--reason", required=True)
    rollback.add_argument("--rollback-scope", default="full", choices=["partial", "full"])
    rollback.add_argument("--replacement-lesson-id", default=None)
    rollback.set_defaults(func=command_rollback)

    retrieve = subparsers.add_parser("retrieve-lessons")
    retrieve.add_argument("--target-skill", default=None)
    retrieve.add_argument("--task-tag", action="append", default=[])
    retrieve.add_argument("--limit", type=int, default=3)
    retrieve.set_defaults(func=command_retrieve)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
