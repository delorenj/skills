"""Command-line parser construction for reportctl."""

from __future__ import annotations

import argparse
import datetime as dt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reportctl")
    parser.add_argument("--config", required=True, help="operator-owned strict JSON config")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    for name in ("plan", "status", "health"):
        sub = commands.add_parser(name)
        sub.add_argument("--jobs", help="JSON Hermes job snapshot")
        if name == "health":
            sub.add_argument("--date", default=dt.date.today().isoformat())
    reconcile = commands.add_parser("reconcile")
    reconcile.add_argument("--jobs", help="JSON Hermes job snapshot")
    reconcile.add_argument("--apply", action="store_true", help="execute the reviewed plan")
    paths = commands.add_parser("paths")
    paths.add_argument("--date", default=dt.date.today().isoformat())
    archive = commands.add_parser("archive")
    archive.add_argument("--report", required=True, help="validated DailyReport JSON input")
    archive.add_argument("--markdown", required=True, help="rendered Markdown input")
    archive.add_argument(
        "--manifest",
        help="RunManifest JSON input; defaults to the canonical artifact path",
    )
    topic = commands.add_parser("topic")
    topic_commands = topic.add_subparsers(dest="topic_command", required=True)
    add = topic_commands.add_parser("add")
    add.add_argument("topic_id")
    add.add_argument("title")
    add.add_argument("--prompt", required=True)
    add.add_argument("--schedule", required=True)
    add.add_argument("--source", action="append", default=[])
    add.add_argument("--secret-env", action="append", default=[])
    update = topic_commands.add_parser("update")
    update.add_argument("topic_id")
    update.add_argument("--title")
    update.add_argument("--prompt")
    update.add_argument("--schedule")
    update.add_argument("--source", action="append")
    update.add_argument("--secret-env", action="append")
    for name in ("pause", "resume", "remove"):
        child = topic_commands.add_parser(name)
        child.add_argument("topic_id")
    return parser
