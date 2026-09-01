#!/usr/bin/env python3
"""Record a Momo decision as a canonical Bloodbank decision event.

Repo-agnostic: resolves the repo slug from the nearest ancestor `.project.json`
(the pjangler CommonProject marker). Emits the canonical CloudEvents 1.0 envelope
`bloodbank.repo.decision.recorded` (repo slug lives in data.repo, NOT the type).

Two sinks, both attempted unless flags narrow them:
  1. Durable local trail  — appends the full envelope as JSONL to
     <root>/_bmad-output/implementation-artifacts/bloodbank-events.jsonl
     (same spool the Hermes sentinel reads). Always written unless --dry-run.
  2. Live bus (NATS)      — PUB to subject `bloodbank.evt.repo.decision.recorded`
     via bloodbank's stdlib publisher. Best-effort: a bus outage never loses the
     decision (the local trail still captures it). Skipped with --local-only.

Pillars a decision rests on go in data.basis (the schema-blessed array); the prose
"why" goes in data.reasoning (allowed by the schema's additionalProperties:true).

Usage:
  record-decision.py --decision "Pull CANDYS-42 from To Do; enough AC to start" \
      --basis "keep-the-pipeline-unblocked" --basis "evidence-over-status" \
      --reasoning "Only backlog otherwise; AC is enumerated and testable." \
      [--root DIR] [--actor momo] [--artifacts-root _bmad-output/implementation-artifacts] \
      [--correlation-id UUID] [--dry-run] [--local-only]

Exit 0 on success (local trail written and, if attempted, bus publish succeeded or
was cleanly skipped). Exit 3 if the local trail was written but the live publish
failed (decision is safe, bus is behind). Exit 2 on bad input / no .project.json.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import uuid
from datetime import datetime, timezone

CE_TYPE = "bloodbank.repo.decision.recorded"
# NATS subject == the CloudEvents type with the `evt` kind-marker inserted after segment 1.
# Derived from CE_TYPE so the two can never silently drift (Bloodbank Event Naming Contract).
NATS_SUBJECT = CE_TYPE.replace("bloodbank.", "bloodbank.evt.", 1)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    d = start.resolve()
    for cand in [d, *d.parents]:
        if (cand / ".project.json").is_file():
            return cand
    return None


def load_project(root: pathlib.Path) -> dict:
    """Load .project.json; raise ValueError if it is present but not valid JSON."""
    try:
        return json.loads((root / ".project.json").read_text())
    except Exception as exc:
        raise ValueError(str(exc)) from exc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--decision", required=True, help="one-line decision statement")
    ap.add_argument("--basis", action="append", default=[], metavar="PILLAR",
                    help="a pillar this decision rests on (repeatable)")
    ap.add_argument("--reasoning", default="", help="why: tradeoffs, alternatives rejected")
    ap.add_argument("--root", default=None, help="repo root (default: nearest ancestor with .project.json)")
    ap.add_argument("--actor", default="momo", help="agent_id of the deciding agent (default: momo)")
    ap.add_argument("--artifacts-root", default="_bmad-output/implementation-artifacts")
    ap.add_argument("--issue", default=None, help="optional related ticket id/key")
    ap.add_argument("--correlation-id", default=os.environ.get("BLOODBANK_CORRELATION_ID"))
    ap.add_argument("--causation-id", default=os.environ.get("BLOODBANK_CAUSATION_ID"))
    ap.add_argument("--dry-run", action="store_true", help="print envelope only; write/publish nothing")
    ap.add_argument("--local-only", action="store_true", help="write local trail; skip the live bus")
    ap.add_argument("--quiet", action="store_true")
    # actor.cli/provider identify the CARRIER Momo runs under. Parameterized (not hardcoded)
    # so a non-Claude carrier (OpenCode/Codex/Hermes) emits an accurate actor per
    # event-naming v1 (provider/CLI identity lives truthfully in actor.*). Default to the
    # Claude carrier for backward compatibility; env MOMO_CLI/MOMO_PROVIDER override.
    ap.add_argument("--cli", default=os.environ.get("MOMO_CLI", "claude"),
                    help="carrier CLI in actor.cli (default: env MOMO_CLI or 'claude')")
    ap.add_argument("--provider", default=os.environ.get("MOMO_PROVIDER", "anthropic"),
                    help="carrier provider in actor.provider (default: env MOMO_PROVIDER or 'anthropic')")
    # Fleet agent_id for the ENVELOPE carrier fields (source/producer/actor), so a
    # Momo decision self-attributes to its distinct fleet identity (<slug>-<actor>,
    # e.g. holocene-momo) matching the on-disk scheme hermes://agent/<agent_id>.
    # The stable human signature stays in data.decided_by (= --actor, "momo").
    ap.add_argument("--agent-id", dest="agent_id_override",
                    default=os.environ.get("MOMO_AGENT_ID"),
                    help="fleet agent_id for envelope carrier fields (default: env MOMO_AGENT_ID or <slug>-<actor>)")
    args = ap.parse_args()

    start = pathlib.Path(args.root) if args.root else pathlib.Path.cwd()
    root = find_project_root(start)
    if root is None:
        print("record-decision: no .project.json in this repo tree — Momo requires a "
              "pjangler CommonProject repo.", file=sys.stderr)
        return 2

    try:
        pj = load_project(root)
    except ValueError as exc:
        print(f"record-decision: .project.json present but not valid JSON: {exc}", file=sys.stderr)
        return 2
    slug = (pj.get("project_slug") or pj.get("ticket_provider", {}).get("identifier") or root.name).strip()
    if not slug:
        print("record-decision: could not resolve repo slug from .project.json", file=sys.stderr)
        return 2

    # Momo's DISTINCT fleet identity — the twin of <slug>-pm (never <slug>-pm
    # itself; masquerading as Hermes would break attributability). Feeds the
    # envelope carrier fields below to match the fleet scheme on disk.
    agent_id = args.agent_id_override or (
        args.actor if "-" in args.actor else f"{slug}-{args.actor}"
    )

    data: dict[str, object] = {
        "repo": slug,
        "decision": args.decision,
        "basis": args.basis,
        "reasoning": args.reasoning,
        "decided_by": args.actor,
        "decided_at": now_iso(),
        "artifacts_root": args.artifacts_root,
    }
    if args.issue:
        data["issue"] = args.issue

    env = {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": f"hermes://agent/{agent_id}",
        "type": CE_TYPE,
        "subject": NATS_SUBJECT,
        "time": now_iso(),
        "datacontenttype": "application/json",
        "kind": "event",
        "domain": "repo",
        "producer": f"hermes-agent:{agent_id}",
        "service": slug,
        "actor": {"type": "agent_cli", "agent_id": agent_id, "cli": args.cli, "provider": args.provider},
        "ordering_key": f"repo:{slug}",
        "correlationid": args.correlation_id or str(uuid.uuid4()),
        "causationid": args.causation_id,
        "data": data,
    }

    body = json.dumps(env, sort_keys=True)

    if args.dry_run:
        print(json.dumps(env, indent=2, sort_keys=True))
        print(f"[dry-run] would publish subject={NATS_SUBJECT} and append local trail", file=sys.stderr)
        return 0

    # Sink 1: durable local trail (never lose a decision).
    log_path = pathlib.Path(os.environ.get(
        "BLOODBANK_EVENTS_LOG",
        str(root / "_bmad-output" / "implementation-artifacts" / "bloodbank-events.jsonl"),
    ))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(body + "\n")

    # Sink 2: live bus (best-effort).
    bus_ok, bus_note = None, "skipped (--local-only)"
    if not args.local_only:
        bus_ok, bus_note = publish_nats(NATS_SUBJECT, body.encode("utf-8"), actor=args.actor)

    if not args.quiet:
        print(f"decision recorded: {env['id']}")
        print(f"  repo={slug}  basis={args.basis or '[]'}")
        print(f"  local trail: {log_path}")
        print(f"  live bus:    {bus_note}")

    if bus_ok is False:
        return 3
    return 0


def publish_nats(subject: str, body: bytes, *, actor: str) -> tuple[bool, str]:
    bb_home = os.environ.get("BLOODBANK_HOME", os.path.expanduser("~/code/33GOD/bloodbank"))
    core = os.path.join(bb_home, "services", "agent-hooks", "core")
    if not os.path.isdir(core):
        return False, f"NOT published — bloodbank publisher missing at {core} (set BLOODBANK_HOME)"
    sys.path.insert(0, core)
    try:
        from nats_publish import publish  # type: ignore
    except Exception as exc:  # pragma: no cover
        return False, f"NOT published — import nats_publish failed: {exc}"
    try:
        publish(subject, body, client_name=f"{actor}-decision")
        return True, f"published to NATS subject {subject}"
    except Exception as exc:
        return False, f"NOT published — NATS unreachable/err: {exc} (decision is safe in local trail)"


if __name__ == "__main__":
    raise SystemExit(main())
