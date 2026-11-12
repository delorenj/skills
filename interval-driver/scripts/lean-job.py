#!/usr/bin/env python3
"""Make an existing Hermes cron job a lean interval driver (see ../SKILL.md).

Sets, on one job in one profile:
  enabled_toolsets  allowlist, default terminal,file plus the no_mcp sentinel (a per-job list
                    otherwise gets every enabled MCP server merged back in)
  skills            cleared (each preloaded skill is resent on every LLM call of the pass)
  script            the brief script: its stdout (the agent's own roadmap snapshot) is injected
                    into the prompt every run
  economics         per-job max_iterations / max_daily_tokens / max_daily_runs caps

It never touches the schedule, scheduler pin, monitor script or prompt. Run it with Hermes' own
Python so it uses the real jobs store and its validators:

  ~/.hermes/hermes-agent/.venv/bin/python lean-job.py --profile gruvato-launch-director \
      --job f605c72fd807 --brief gruvato-launch-brief.sh --max-iterations 10 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True, help="Hermes profile name (~/.hermes/profiles/<name>)")
    ap.add_argument("--job", required=True, help="hex job id")
    ap.add_argument("--toolsets", default="terminal,file", help="comma list; no_mcp is always added")
    ap.add_argument("--keep-mcp", action="store_true", help="do not add the no_mcp sentinel")
    ap.add_argument("--brief", help="brief script name in the profile's scripts/ dir ('' clears)")
    ap.add_argument("--keep-skills", action="store_true", help="leave the job's skills alone")
    ap.add_argument("--max-iterations", type=int)
    ap.add_argument("--max-daily-tokens", type=int)
    ap.add_argument("--max-daily-runs", type=int)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    home = Path.home() / ".hermes" / "profiles" / a.profile
    if not home.is_dir():
        print(f"lean-job: no profile dir {home}", file=sys.stderr)
        return 2
    os.environ["HERMES_HOME"] = str(home)
    sys.path.insert(0, str(Path.home() / ".hermes" / "hermes-agent"))
    from cron import jobs  # noqa: E402  (needs HERMES_HOME set first)

    job = jobs.get_job(a.job)
    if not job:
        print(f"lean-job: no job {a.job} in profile {a.profile}", file=sys.stderr)
        return 2

    updates: dict = {}
    toolsets = [t.strip() for t in a.toolsets.split(",") if t.strip()]
    if not a.keep_mcp and "no_mcp" not in toolsets:
        toolsets.append("no_mcp")
    updates["enabled_toolsets"] = toolsets
    if not a.keep_skills:
        updates["skills"] = []
        updates["skill"] = None
    if a.brief is not None:
        if a.brief:
            path = home / "scripts" / a.brief
            if not path.is_file() or path.is_symlink():
                print(f"lean-job: brief script must be a real file at {path} (Hermes refuses symlinks)", file=sys.stderr)
                return 2
        updates["script"] = a.brief or None
    econ = dict(job.get("economics") or {})
    for key, val in (("max_iterations", a.max_iterations), ("max_daily_tokens", a.max_daily_tokens),
                     ("max_daily_runs", a.max_daily_runs)):
        if val is not None:
            econ[key] = val
    if econ != (job.get("economics") or {}):
        updates["economics"] = econ

    keys = sorted(set(updates) | {"monitor_script", "context_from", "scheduler"})
    before = {k: job.get(k) for k in keys}
    print("before:", json.dumps(before, default=str))
    print("update:", json.dumps(updates, default=str))
    if a.dry_run:
        return 0
    after = jobs.update_job(a.job, updates)
    print("after: ", json.dumps({k: (after or {}).get(k) for k in keys}, default=str))
    if not after.get("monitor_script") and not after.get("monitor_url"):
        print("warning: no monitor gate on this job, so an unchanged board still costs a full pass", file=sys.stderr)
    if after.get("scheduler") != "external":
        print("warning: job is not pinned scheduler=external; Candybar must own the clock", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
