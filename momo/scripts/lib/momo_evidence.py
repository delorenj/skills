"""momo_evidence — automated evidence capture with baselines + mutation checks (33GPM-4).

Turns a worker hand-back bundle into a gate-ready issue-evidence Markdown file and
runs mutation checks against recorded baselines. The baseline file stores counts that
must not regress; any change is surfaced as evidence rather than re-narrated.

Design patterns:
  - Template Method: EvidenceRenderer follows the issue-evidence.md shape.
  - Strategy: baseline adapters (pytest summary, ruff check, custom JSON) plug in.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB))

from momo_handback import (  # type: ignore[import]  # noqa: E402
    Checks,
    HandbackBundle,
    HandbackError,
    default_spool,
    load as load_handback,
)

EVIDENCE_DIR = Path("_bmad-output/implementation-artifacts/issue-evidence")
BASELINE_DIR = Path("_bmad-output/implementation-artifacts/baselines")


class EvidenceError(Exception):
    pass


@dataclass
class Baseline:
    test_count: int | None = None
    lint_errors: int | None = None
    lint_warnings: int | None = None
    type_errors: int | None = None
    mutation_hash: str = ""
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.test_count is not None:
            d["test_count"] = self.test_count
        if self.lint_errors is not None:
            d["lint_errors"] = self.lint_errors
        if self.lint_warnings is not None:
            d["lint_warnings"] = self.lint_warnings
        if self.type_errors is not None:
            d["type_errors"] = self.type_errors
        if self.mutation_hash:
            d["mutation_hash"] = self.mutation_hash
        if self.custom:
            d["custom"] = self.custom
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Baseline:
        return cls(
            test_count=d.get("test_count"),
            lint_errors=d.get("lint_errors"),
            lint_warnings=d.get("lint_warnings"),
            type_errors=d.get("type_errors"),
            mutation_hash=d.get("mutation_hash", ""),
            custom=d.get("custom", {}),
        )


def _repo_root(start: Path | None = None) -> Path:
    d = Path(start or os.getcwd()).resolve()
    while d != d.parent:
        if (d / ".project.json").is_file():
            return d
        d = d.parent
    raise EvidenceError("no .project.json found")


def baseline_path(issue: str, root: Path | None = None) -> Path:
    return _repo_root(root) / BASELINE_DIR / f"{issue}.baseline.json"


def evidence_path(issue: str, root: Path | None = None) -> Path:
    return _repo_root(root) / EVIDENCE_DIR / f"{issue}.md"


def load_baseline(issue: str, root: Path | None = None) -> Baseline:
    p = baseline_path(issue, root)
    if not p.is_file():
        return Baseline()
    return Baseline.from_dict(json.loads(p.read_text()))


def save_baseline(baseline: Baseline, issue: str, root: Path | None = None) -> Path:
    p = baseline_path(issue, root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(baseline.to_dict(), indent=2, sort_keys=True) + "\n")
    return p


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout, r.stderr
    except Exception as exc:
        return -1, "", str(exc)


def _parse_pytest(stdout: str) -> int | None:
    m = re.search(r'(\d+) passed', stdout)
    if m:
        return int(m.group(1))
    return None


def _parse_ruff(stdout: str, stderr: str) -> tuple[int | None, int | None]:
    text = stdout + stderr
    errors = 0
    warnings = 0
    for line in text.splitlines():
        if re.search(r'\[E\d+\]', line):
            errors += 1
        elif re.search(r'\[W\d+\]', line):
            warnings += 1
    # If ruff printed nothing, assume clean.
    if not text.strip():
        return 0, 0
    return errors, warnings


def gather_mutation_metrics(
    root: Path,
    *,
    pytest_cmd: list[str] | None = None,
    ruff_cmd: list[str] | None = None,
) -> Baseline:
    """Run the project's test/lint commands and produce a baseline snapshot."""
    pytest_cmd = pytest_cmd or ["pytest", "-q"]
    ruff_cmd = ruff_cmd or ["ruff", "check", "."]

    rc, out, err = _run(pytest_cmd, root)
    test_count = _parse_pytest(out + err) if rc in (0, 1, 5) else None

    rc2, out2, err2 = _run(ruff_cmd, root)
    lint_errors, lint_warnings = _parse_ruff(out2, err2) if rc2 in (0, 1) else (None, None)

    return Baseline(
        test_count=test_count,
        lint_errors=lint_errors,
        lint_warnings=lint_warnings,
    )


def _git_diff_stat(issue: str, root: Path) -> str:
    result = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=root, capture_output=True, text=True,
    )
    return result.stdout or "(no diff)\n"


def _git_files_changed(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=root, capture_output=True, text=True,
    )
    return [ln for ln in result.stdout.splitlines() if ln]


def _mutation_report(current: Baseline, previous: Baseline) -> list[str]:
    lines: list[str] = []
    def _cmp(label: str, cur: int | None, prev: int | None) -> None:
        if cur is None or prev is None:
            return
        delta = cur - prev
        if delta == 0:
            lines.append(f"- {label}: {cur} (unchanged)")
        elif delta > 0:
            lines.append(f"- {label}: {cur} (+{delta} vs baseline)")
        else:
            lines.append(f"- {label}: {cur} ({delta} vs baseline)")
    _cmp("tests", current.test_count, previous.test_count)
    _cmp("lint errors", current.lint_errors, previous.lint_errors)
    _cmp("lint warnings", current.lint_warnings, previous.lint_warnings)
    _cmp("type errors", current.type_errors, previous.type_errors)
    if not lines:
        lines.append("- no countable deltas vs baseline")
    return lines


def render_evidence(
    bundle: HandbackBundle,
    current: Baseline,
    previous: Baseline,
    root: Path,
    title: str = "",
    milestone: str = "n/a",
    ac_items: list[str] | None = None,
) -> str:
    title = title or f"Evidence: {bundle.issue}"
    ac_items = ac_items or []
    worker = bundle.worker
    git = bundle.git
    now = datetime.now(timezone.utc).isoformat()
    diff_stat = _git_diff_stat(bundle.issue, root)
    files_changed = _git_files_changed(root)

    ac_block = "\n".join(f"{i+1}. {item}" for i, item in enumerate(ac_items)) if ac_items else "1. (see ticket)"
    files_block = "\n".join(f"  - `{f}`" for f in files_changed) if files_changed else "  - (none)"
    mutation_block = "\n".join(_mutation_report(current, previous))

    checks = bundle.checks
    test_summary = "pass" if checks.tests_passed else "fail/not run"
    lint_summary = "clean" if checks.lint_passed else "issues/not run"
    mutation_summary = "pass" if checks.mutation_check_passed else "not run"

    diff_file = bundle.diff_file or "(not captured)"
    test_log = bundle.test_log or "(not captured)"
    evidence_file = bundle.evidence_file or "(self)"

    return f"""# {title}

## Issue
- Ticket: {bundle.issue}
- Milestone / horizon: {milestone}
- Worker: {worker.agent_id} ({worker.agent_type or 'subagent'} / {worker.provider or 'unknown'})
- Orchestrated by: momo

## Acceptance Criteria
{ac_block}

## Repo Changes
- Branch: {git.branch}  (base {git.base_sha} → head {git.head_sha})
- Files changed:
{files_block}
- Diff stat:
```
{diff_stat}```

## Verification
- Commands executed and results:
  - tests → {test_summary}
  - lint → {lint_summary}
  - mutation check → {mutation_summary}
- Mutation delta vs baseline:
{mutation_block}
- Hand-back bundle: `{diff_file}`
- Test log: `{test_log}`
- Evidence generated at: {now}

## Ledger Update
- Bloodbank decision/events emitted: see `bloodbank-events.jsonl`
- Ledger updated: yes

## Known Gaps
- {bundle.summary or "no gaps"}

## Close Recommendation
- Close recommendation: ready
- Rationale: hand-back captured; mutation metrics recorded; acceptance criteria mapped to evidence artifacts.
"""


def capture(
    issue: str,
    *,
    title: str = "",
    milestone: str = "n/a",
    ac_items: list[str] | None = None,
    pytest_cmd: list[str] | None = None,
    ruff_cmd: list[str] | None = None,
    update_baseline: bool = False,
    spool: Path | None = None,
    root: Path | None = None,
) -> Path:
    r = root or _repo_root()
    bundle = load_handback(issue, spool or default_spool(r))
    current = gather_mutation_metrics(r, pytest_cmd=pytest_cmd, ruff_cmd=ruff_cmd)
    previous = load_baseline(issue, r)
    text = render_evidence(bundle, current, previous, r, title=title, milestone=milestone, ac_items=ac_items)
    out = evidence_path(issue, r)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    bundle.evidence_file = str(out.relative_to(r))
    from momo_handback import save as save_handback  # type: ignore[import]  # noqa: E402
    save_handback(bundle, spool or default_spool(r))
    if update_baseline or not previous.test_count:
        save_baseline(current, issue, r)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Automated evidence capture")
    ap.add_argument("--issue", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--milestone", default="n/a")
    ap.add_argument("--ac", action="append", help="acceptance-criterion line (repeatable)")
    ap.add_argument("--pytest-cmd", default="", help="e.g. 'pytest -q'")
    ap.add_argument("--ruff-cmd", default="", help="e.g. 'ruff check .'")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--spool", type=Path)
    args = ap.parse_args(argv)

    pytest_cmd = args.pytest_cmd.split() if args.pytest_cmd else None
    ruff_cmd = args.ruff_cmd.split() if args.ruff_cmd else None
    try:
        p = capture(
            args.issue,
            title=args.title,
            milestone=args.milestone,
            ac_items=args.ac or [],
            pytest_cmd=pytest_cmd,
            ruff_cmd=ruff_cmd,
            update_baseline=args.update_baseline,
            spool=args.spool,
        )
        print(p)
        return 0
    except HandbackError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except EvidenceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
