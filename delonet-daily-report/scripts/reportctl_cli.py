"""Command-line surface for reportctl.

The cron subcommands (``plan``, ``reconcile``, and the scheduler half of
``health``) are gone. The merged pipeline has one job -- ``run`` -- and its
correctness is established by ``verify``, which inspects the published artifact
rather than trusting a scheduler's own account of itself.
"""

from __future__ import annotations

import argparse
import datetime as dt


def default_date() -> str:
    """Yesterday. The report is always about a day that has finished."""
    return (dt.date.today() - dt.timedelta(days=1)).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reportctl",
        description="Collect, compose, publish, and verify the daily developer report.",
    )
    parser.add_argument("--config", required=True, help="operator-owned strict JSON config")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("validate", help="validate the config against schema v2")

    paths = commands.add_parser("paths", help="show artifact and archive paths for a date")
    paths.add_argument("--date", default=default_date())

    status = commands.add_parser("status", help="report section, manifest, and publish state")
    status.add_argument("--date", default=default_date())

    collect = commands.add_parser("collect", help="run collectors and write section artifacts")
    collect.add_argument("--date", default=default_date())
    collect.add_argument(
        "--section",
        action="append",
        default=[],
        help="limit to this section id; repeatable, defaults to every enabled section",
    )
    collect.add_argument("--run-id", help="reuse an existing run identifier")

    run = commands.add_parser("run", help="collect, compose, narrate, and publish one report")
    run.add_argument("--date", default=default_date())
    run.add_argument("--run-id", help="reuse an existing run identifier")
    run.add_argument("--no-emit", action="store_true", help="skip the Bloodbank event")
    run.add_argument("--no-narrate", action="store_true", help="use the deterministic render")
    run.add_argument("--no-mirror", action="store_true", help="skip the git-tracked mirror copy")
    run.add_argument(
        "--section",
        action="append",
        default=[],
        help="limit COLLECTION to this section id; repeatable. Every enabled section is "
        "still enumerated in the manifest, so one left uncollected is reported, not dropped",
    )

    verify = commands.add_parser(
        "verify", help="exit non-zero unless a valid report is published for the date"
    )
    verify.add_argument("--date", default=default_date())
    verify.add_argument(
        "--require-complete",
        action="store_true",
        help="also fail when any enabled section did not complete",
    )

    dist = commands.add_parser(
        "distribute",
        help="deliver the published report to the vault, notebook, email and Slack",
    )
    dist.add_argument("--date", default=default_date())
    dist.add_argument(
        "--only",
        action="append",
        default=[],
        choices=["vault", "notebook", "email", "slack"],
        help="limit to this target; repeatable. Unselected targets are reported as "
        "skipped, never as delivered",
    )
    dist.add_argument(
        "--dry-run",
        action="store_true",
        help="resolve every target and render every payload without sending",
    )

    archive = commands.add_parser("archive", help="publish a validated report generation")
    archive.add_argument("--report", required=True, help="validated DailyReport JSON input")
    archive.add_argument("--markdown", required=True, help="rendered Markdown input")
    archive.add_argument(
        "--manifest",
        help="RunManifest JSON input; defaults to the canonical artifact path",
    )
    return parser
