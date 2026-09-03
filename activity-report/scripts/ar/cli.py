"""argparse tree for `activity-report`.

Every subcommand that reads or writes an audience-specific artifact requires
--audience; none defaults it. Subcommands dispatch to `<module>.<name>_cmd(args)`,
which returns an exit code; SkillError subclasses are turned into their code.
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys

from . import __version__
from .common import AUDIENCES, EXIT_CONFIG, SkillError, eprint

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def _mod(name: str):
    return importlib.import_module(f"ar.{name}")


def _dispatch(module: str, func: str):
    def _run(args: argparse.Namespace) -> int:
        return int(getattr(_mod(module), func)(args) or 0)
    return _run


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--project", metavar="SLUG",
                   help="pjangler project slug (via `pjangler project show`); default: the .project.json found upward from cwd")
    p.add_argument("--json", action="store_true", help="machine-readable output")


def _audience(p: argparse.ArgumentParser) -> None:
    p.add_argument("--audience", required=True, choices=AUDIENCES,
                   help="who reads this: internal (the team) or external (the client). Required; never defaulted.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="activity-report",
        description="Periodic project updates for one declared audience, from Candystore, git, the board and Hindsight; "
                    "emitted as bloodbank.project.activity.recorded.",
    )
    ap.add_argument("--version", action="version", version=f"activity-report {__version__}")
    sub = ap.add_subparsers(dest="command", required=True, metavar="COMMAND")

    p = sub.add_parser("resolve", help="print the project, merged config and scope set")
    _common(p)
    p.set_defaults(func=_dispatch("config", "resolve_cmd"))

    p = sub.add_parser("window", help="resolve the reporting window for one audience")
    _common(p); _audience(p)
    p.add_argument("--since", help="explicit window start (ISO-8601)")
    p.add_argument("--until", help="explicit window end (ISO-8601); default now")
    p.add_argument("--force", action="store_true", help="accept a window shorter than window.min_minutes")
    p.set_defaults(func=_dispatch("window", "window_cmd"))

    p = sub.add_parser("collect", help="write the digest for one audience")
    _common(p); _audience(p)
    p.add_argument("--since"); p.add_argument("--until")
    p.add_argument("--run-id", help="uuid4 shared by both audiences of one run; default: a new one")
    p.add_argument("--out", help="digest path; default runtime/<slug>/<label>-<audience>.digest.json")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=_dispatch("digest", "collect_cmd"))

    p = sub.add_parser("lint", help="check a raw.txt for the audience; exit 3 on any error")
    _common(p); _audience(p)
    p.add_argument("raw", help="path to raw.txt (line 1 is `# <title>`)")
    p.add_argument("--digest", help="digest path (enables ticket-aware checks)")
    p.add_argument("--lint-json", help="path to <label>-external.lint.json; default: next to the digest")
    p.add_argument("--warnings-as-errors", action="store_true")
    p.set_defaults(func=_dispatch("lint", "lint_cmd"))

    p = sub.add_parser("render", help="raw.txt -> markdown + self-contained html")
    _common(p); _audience(p)
    p.add_argument("raw")
    p.add_argument("--digest", required=True)
    p.add_argument("--md", help="markdown output path; default next to the digest")
    p.add_argument("--html", help="html output path; default next to the digest")
    p.set_defaults(func=_dispatch("render", "render_cmd"))

    p = sub.add_parser("assemble", help="digest + bodies -> the event data object")
    _common(p); _audience(p)
    p.add_argument("--digest", required=True)
    p.add_argument("--raw", required=True)
    p.add_argument("--md", required=True)
    p.add_argument("--html", required=True)
    p.add_argument("--out", help="event data path; default next to the digest")
    p.add_argument("--model", help="model name recorded in generator.model")
    p.add_argument("--dry-run", action="store_true", help="stamp generator.dry_run=true")
    p.set_defaults(func=_dispatch("assemble", "assemble_cmd"))

    p = sub.add_parser("emit", help="publish an event data file through bb-emit (--check first, then --strict)")
    _common(p)
    p.add_argument("event", help="path to <label>-<audience>.event.json")
    p.add_argument("--dry-run", action="store_true", help="bb-emit --check only; publish nothing")
    p.add_argument("--out", help="where to record the emitter output; default next to the event")
    p.set_defaults(func=_dispatch("emit", "emit_cmd"))

    p = sub.add_parser("verify", help="prove the event was projected into Candystore")
    _common(p)
    p.add_argument("--run-id", required=True)
    p.add_argument("--timeout-seconds", type=int, default=90)
    p.add_argument("--audience", choices=AUDIENCES,
                   help="also require data.audience to match (optional; a run emits one event per audience)")
    p.add_argument("--expect", type=int, default=1, help="how many matching events to wait for (default 1)")
    p.set_defaults(func=_dispatch("verify", "verify_cmd"))

    p = sub.add_parser("portal", help="write the portal row for an event (external => visible to the client)")
    _common(p)
    p.add_argument("event")
    p.add_argument("--dry-run", action="store_true", help="validate and print the row; write nothing")
    p.set_defaults(func=_dispatch("portal", "portal_cmd"))

    p = sub.add_parser("retain", help="store the raw report in the project's Hindsight bank")
    _common(p); _audience(p)
    p.add_argument("raw")
    p.add_argument("--digest", required=True)
    p.set_defaults(func=_dispatch("hindsight", "retain_cmd"))

    p = sub.add_parser("ensure-labels", help="create the xp:external / xp:internal labels on the board")
    _common(p)
    p.add_argument("--confirm", action="store_true", help="actually create the missing labels (a live-workspace write)")
    p.set_defaults(func=_dispatch("board", "ensure_labels_cmd"))

    p = sub.add_parser("init", help="install the ~/.local/bin shim and check the project's config block")
    _common(p)
    p.set_defaults(func=_dispatch("config", "init_cmd"))

    p = sub.add_parser("install-timer", help="install the systemd user timer for this project")
    _common(p)
    p.set_defaults(func=_dispatch("schedule", "install_timer_cmd"))

    p = sub.add_parser("timer-status", help="when the report last ran and when it runs next")
    _common(p)
    p.set_defaults(func=_dispatch("schedule", "timer_status_cmd"))

    p = sub.add_parser("run", help="the unattended chain: collect, compose, lint, render, assemble, emit, verify, portal, retain")
    _common(p)
    p.add_argument("--audience", action="append", choices=AUDIENCES,
                   help="restrict to one audience (repeatable); default: every configured audience, internal first")
    p.add_argument("--dry-run", action="store_true", help="emit with generator.dry_run=true; no portal row, no retain, no durable copy")
    p.add_argument("--since"); p.add_argument("--until")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=run_cmd)

    return ap


def run_cmd(args: argparse.Namespace) -> int:
    """Exec scripts/run.sh with the same flags; it owns the lock, the log and the stages."""
    run_sh = os.path.join(SCRIPTS_DIR, "run.sh")
    if not os.path.isfile(run_sh):
        eprint(f"activity-report: missing {run_sh}")
        return EXIT_CONFIG
    argv = ["bash", run_sh]
    if args.project:
        argv += ["--project", args.project]
    for audience in args.audience or []:
        argv += ["--audience", audience]
    if args.dry_run:
        argv.append("--dry-run")
    if args.since:
        argv += ["--since", args.since]
    if args.until:
        argv += ["--until", args.until]
    if args.force:
        argv.append("--force")
    sys.stdout.flush()
    os.execvp("bash", argv)
    return EXIT_CONFIG  # not reached


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except SkillError as exc:
        eprint(f"activity-report: {exc}")
        return exc.exit_code
    except KeyboardInterrupt:
        return 130
