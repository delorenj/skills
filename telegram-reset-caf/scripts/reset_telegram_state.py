#!/usr/bin/env python3
"""Reset CAF Telegram onboarding dogfood state for one client.

This is intentionally local-dev oriented and shells out to docker compose/psql so
it works even when the host Python environment does not have app dependencies.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


CLIENT_ID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def run(cmd: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return result.stdout if capture and result.stdout is not None else ""


def psql(sql: str, *, capture: bool = False) -> str:
    return run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "lamp_app",
            "-d",
            "lamp",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        capture=capture,
    )


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def resolve_client_id(args: argparse.Namespace) -> str:
    if args.client_id:
        if not CLIENT_ID_RE.match(args.client_id):
            raise SystemExit(f"Invalid UUID: {args.client_id}")
        return args.client_id.lower()

    if not args.email:
        raise SystemExit("Provide --client-id or --email")

    email = args.email.strip().lower()
    sql = f"""
        SELECT c.id::text
        FROM clients c
        LEFT JOIN onboarding_cases oc ON oc.client_id = c.id
        WHERE lower(oc.email) = {sql_literal(email)}
        ORDER BY oc.created_at DESC NULLS LAST
        LIMIT 1;
    """
    out = psql(sql, capture=True).strip().splitlines()
    ids = [line.strip() for line in out if CLIENT_ID_RE.match(line.strip())]
    if not ids:
        raise SystemExit(f"No client found for email {email}")
    return ids[0]


def reset_client(client_id: str, *, clear_binding: bool, clear_conversations: bool) -> None:
    binding_sql = ""
    case_status = "awaiting_client" if clear_binding else "ready"
    if clear_binding:
        binding_sql = """
            telegram_id = NULL,
            telegram_chat_id = NULL,
            telegram_user_id = NULL,
            telegram_group_chat_id = NULL,
            telegram_group_title = NULL,
            telegram_group_bound_by_user_id = NULL,
            telegram_group_bound_at = NULL,
            onboarding_token_consumed_at = NULL,
            onboarding_link_clicked_at = NULL,
        """

    conversation_sql = (
        f"DELETE FROM telegram_conversation_events WHERE client_id = {sql_literal(client_id)};"
        if clear_conversations
        else ""
    )

    sql = f"""
        BEGIN;

        DELETE FROM seed_config
        WHERE key = {sql_literal(client_id)}
          AND kind IN (
            'telegram_onboarding_interview',
            'client_program_readiness',
            'daily_rhythm_config'
          );

        DELETE FROM workflow_sessions
        WHERE client_id = {sql_literal(client_id)}
          AND workflow_id IN ('damian-method.onboarding');

        DELETE FROM client_profile_facts
        WHERE client_id = {sql_literal(client_id)};

        DELETE FROM client_objectives
        WHERE client_id = {sql_literal(client_id)};

        DELETE FROM coaching_protocol_sessions
        WHERE client_id = {sql_literal(client_id)};

        {conversation_sql}

        UPDATE clients
        SET lifecycle_status = 'onboarding',
            current_stage_id = 'onboarding',
            updated_at = now()
        WHERE id = {sql_literal(client_id)};

        UPDATE onboarding_cases
        SET
            {binding_sql}
            first_greeting_sent_at = NULL,
            status = {sql_literal(case_status)},
            updated_at = now()
        WHERE client_id = {sql_literal(client_id)};

        COMMIT;
    """
    psql(sql)


def restart_stack() -> None:
    run(["docker", "compose", "up", "-d", "--build", "api", "telegram-poll-bridge"])


def verify(client_id: str) -> None:
    sql = f"""
        SELECT
            c.lifecycle_status,
            c.current_stage_id,
            COALESCE(oc.status, '') AS onboarding_status,
            COALESCE(oc.telegram_id, '') AS telegram_id,
            COALESCE(oc.telegram_group_chat_id, '') AS group_chat_id,
            (SELECT count(*) FROM workflow_sessions ws WHERE ws.client_id = c.id AND ws.status = 'active') AS active_workflows,
            (SELECT count(*) FROM client_profile_facts f WHERE f.client_id = c.id) AS facts,
            (SELECT count(*) FROM client_objectives o WHERE o.client_id = c.id) AS objectives
        FROM clients c
        LEFT JOIN onboarding_cases oc ON oc.client_id = c.id
        WHERE c.id = {sql_literal(client_id)};
    """
    print(psql(sql, capture=True).strip())
    run(["docker", "compose", "ps", "api", "telegram-poll-bridge"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id")
    parser.add_argument("--email")
    parser.add_argument("--clear-binding", action="store_true")
    parser.add_argument("--clear-conversations", action="store_true")
    parser.add_argument("--restart-stack", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if not Path("docker-compose.yml").exists() or not Path("lamp-skills").exists():
        raise SystemExit("Run this from the CoachingAgentFramework repo root.")

    client_id = resolve_client_id(args)
    reset_client(
        client_id,
        clear_binding=args.clear_binding,
        clear_conversations=args.clear_conversations,
    )
    if args.restart_stack:
        restart_stack()
    if args.verify:
        verify(client_id)
    print(f"Reset complete for client {client_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
