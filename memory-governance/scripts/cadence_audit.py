#!/usr/bin/env python3
"""Audit heartbeat/cron/QMD cadence configuration and produce a deterministic report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenClaw cadence and memory configuration")
    parser.add_argument("--config", default="~/.openclaw/openclaw.json", help="OpenClaw config path")
    parser.add_argument("--cron", default="~/.openclaw/cron/jobs.json", help="Cron jobs file path")
    parser.add_argument("--output", default=None, help="Optional markdown output path")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    cron_path = Path(args.cron).expanduser().resolve()

    cfg = _load_json(config_path)

    heartbeat_every = _get(cfg, "agents", "defaults", "heartbeat", "every")
    heartbeat_model = _get(cfg, "agents", "defaults", "heartbeat", "model")
    heartbeat_target = _get(cfg, "agents", "defaults", "heartbeat", "target")

    memory_backend = _get(cfg, "memory", "backend")
    qmd_mode = _get(cfg, "memory", "qmd", "searchMode")
    qmd_update = _get(cfg, "memory", "qmd", "update", "interval")
    qmd_sessions = _get(cfg, "memory", "qmd", "sessions", "enabled")

    cron_jobs = []
    if cron_path.exists():
        raw = _load_json(cron_path)
        cron_jobs = raw.get("jobs", []) if isinstance(raw, dict) else []

    enabled_jobs = [j for j in cron_jobs if j.get("enabled", True)]
    heartbeat_named_jobs = [
        j for j in cron_jobs
        if "heartbeat" in (j.get("name", "").lower()) or "heartbeat" in (j.get("payload", {}).get("text", "").lower())
    ]

    findings: list[str] = []
    if not heartbeat_every:
        findings.append("❌ Native heartbeat not configured (agents.defaults.heartbeat.every missing).")
    else:
        findings.append(f"✅ Native heartbeat configured: every {heartbeat_every} (model={heartbeat_model}, target={heartbeat_target}).")

    if memory_backend != "qmd":
        findings.append(f"⚠️ Memory backend is '{memory_backend}', not 'qmd'.")
    else:
        findings.append(f"✅ QMD backend enabled (mode={qmd_mode}, update interval={qmd_update}, sessions={qmd_sessions}).")

    findings.append(f"ℹ️ Cron jobs total={len(cron_jobs)}, enabled={len(enabled_jobs)}.")
    if heartbeat_named_jobs:
        findings.append(f"⚠️ Found {len(heartbeat_named_jobs)} cron jobs that look like heartbeat duplicates.")
    else:
        findings.append("✅ No cron heartbeat-duplicate jobs detected.")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Cadence Audit Report",
        "",
        f"Generated: {ts}",
        f"Config: {config_path}",
        f"Cron file: {cron_path}",
        "",
        "## Summary",
    ]
    lines.extend([f"- {f}" for f in findings])

    lines.extend([
        "",
        "## Recommended operating model",
        "- Heartbeat handles triage/dispatch loops.",
        "- Cron handles precise or one-shot scheduled tasks only.",
        "- QMD refresh interval is independent of heartbeat/cron.",
        "",
    ])

    if heartbeat_named_jobs:
        lines.extend([
            "## Potential duplicate heartbeat cron jobs",
            *[f"- {j.get('id')} :: {j.get('name','(unnamed)')}" for j in heartbeat_named_jobs],
            "",
        ])

    out_text = "\n".join(lines)
    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(out_text, encoding="utf-8")
        print(out)
    else:
        print(out_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
