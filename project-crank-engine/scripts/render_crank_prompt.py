#!/usr/bin/env python3
import argparse
from textwrap import dedent


def main() -> None:
    p = argparse.ArgumentParser(description="Render a Project Crank Engine prompt")
    p.add_argument("--project", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--goal", required=True)
    p.add_argument("--pace", default="aggressive", choices=["light", "balanced", "aggressive"])
    p.add_argument("--ticket-metric", required=True)
    p.add_argument("--pr-metric", required=True)
    p.add_argument("--validation-metric", required=True)
    p.add_argument(
        "--done-metric-query",
        default="Compute Done/Total story count from the sprint board.",
    )
    args = p.parse_args()

    prompt = dedent(
        f"""
        Project Crank Engine — Sprint Finish Loop

        Project: {args.project}
        Pace: {args.pace}
        Current Focus: {args.scope}
        Goal: {args.goal}

        Mission
        - Execute the highest-leverage unblocked work to finish the sprint.
        - Follow BMAD + ticket-first + PR-first discipline.

        Required status evidence on every update
        1) Repo facts
        - git rev-parse --abbrev-ref HEAD
        - git log -1 --oneline
        - git status --short
        - git stash list
        - gh pr list --state open

        2) Sprint facts
        - Done/Total stories: {args.done_metric_query}
        - Remaining blockers: explicit list with owner + next action

        3) Visual proof
        - Capture one screenshot showing current board/PR completion state (path or link).

        Finish contract (all must pass)
        - Ticket metric: {args.ticket_metric}
        - PR metric: {args.pr_metric}
        - Validation metric: {args.validation_metric}
        - Evidence metric: screenshot provided + command-backed facts included

        Decision rule
        - If ALL finish contract checks pass: respond DONE with evidence summary.
        - Else respond NOT DONE with exact gap and immediate next action.

        If NOT DONE
        - Continue execution immediately on the next highest-impact gap.
        - No idle waiting.
        """
    ).strip()

    print(prompt)


if __name__ == "__main__":
    main()
