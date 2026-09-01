"""momo_handback — structured worker hand-back bundle (33GPM-3).

Defines the canonical hand-back schema, a filesystem-backed spool, and a
heartbeat/timeout policy so silent worker death is detected and retried.

Design patterns:
  - Template Method: HandbackBundle is the immutable shape; subclasses may
    override validation hooks.
  - Strategy: the retry policy is pluggable (default fixed-count with backoff).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
DEFAULT_TTL_SECONDS = 300
DEFAULT_MAX_RETRIES = 3


class HandbackError(Exception):
    pass


class HandbackValidationError(HandbackError):
    pass


@dataclass
class WorkerIdentity:
    agent_id: str = ""
    agent_type: str = ""
    model: str = ""
    provider: str = ""
    session_id: str = ""
    pid: int = 0
    host: str = field(default_factory=socket.gethostname)


@dataclass
class GitPointer:
    base_sha: str = ""
    head_sha: str = ""
    branch: str = ""


@dataclass
class Checks:
    tests_passed: bool = False
    lint_passed: bool = False
    mutation_check_passed: bool = False
    type_check_passed: bool | None = None


@dataclass
class Heartbeat:
    started_at: str = field(default_factory=lambda: _now_iso())
    last_seen_at: str = field(default_factory=lambda: _now_iso())
    ttl_seconds: int = DEFAULT_TTL_SECONDS


@dataclass
class RetryState:
    attempt: int = 1
    max_attempts: int = DEFAULT_MAX_RETRIES
    policy: str = "fixed_backoff"
    backoff_seconds: int = 30


@dataclass
class HandbackBundle:
    """Canonical hand-back bundle. All fields are optional defaults; callers fill
    in what they know. The schema_version and issue are required at finalization."""

    schema_version: str = SCHEMA_VERSION
    issue: str = ""
    repo_slug: str = ""
    worker: WorkerIdentity = field(default_factory=WorkerIdentity)
    git: GitPointer = field(default_factory=GitPointer)
    status: str = ""  # DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
    summary: str = ""
    diff_file: str = ""
    test_log: str = ""
    evidence_file: str = ""
    checks: Checks = field(default_factory=Checks)
    findings: list[dict[str, Any]] = field(default_factory=list)
    heartbeat: Heartbeat = field(default_factory=Heartbeat)
    retries: RetryState = field(default_factory=RetryState)
    meta: dict[str, Any] = field(default_factory=dict)

    def bump_heartbeat(self) -> None:
        self.heartbeat.last_seen_at = _now_iso()

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise HandbackValidationError(f"unsupported schema_version {self.schema_version}")
        if not self.issue or not re.match(r"^[A-Z0-9]+-\d+$", self.issue):
            raise HandbackValidationError("issue must match <PROJECT>-<NUMBER>")
        if self.status not in {"DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT", ""}:
            raise HandbackValidationError(f"invalid status {self.status}")
        if self.retries.attempt < 1:
            raise HandbackValidationError("retries.attempt must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> HandbackBundle:
        d = dict(d)
        if d.get("schema_version") != SCHEMA_VERSION:
            raise HandbackValidationError("schema_version mismatch")
        d.setdefault("worker", {})
        d.setdefault("git", {})
        d.setdefault("checks", {})
        d.setdefault("heartbeat", {})
        d.setdefault("retries", {})
        d.setdefault("findings", [])
        d.setdefault("meta", {})
        return cls(
            schema_version=d["schema_version"],
            issue=d.get("issue", ""),
            repo_slug=d.get("repo_slug", ""),
            worker=WorkerIdentity(**d["worker"]),
            git=GitPointer(**d["git"]),
            status=d.get("status", ""),
            summary=d.get("summary", ""),
            diff_file=d.get("diff_file", ""),
            test_log=d.get("test_log", ""),
            evidence_file=d.get("evidence_file", ""),
            checks=Checks(**d["checks"]),
            findings=list(d["findings"]),
            heartbeat=Heartbeat(**d["heartbeat"]),
            retries=RetryState(**d["retries"]),
            meta=dict(d["meta"]),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root(start: str | Path | None = None) -> Path:
    """Walk up until .project.json is found."""
    d = Path(start or os.getcwd()).resolve()
    while d != d.parent:
        if (d / ".project.json").is_file():
            return d
        d = d.parent
    raise HandbackError("no .project.json found; not inside a CommonProject repo")


def default_spool(root: Path | None = None) -> Path:
    r = root or repo_root()
    return r / "_bmad-output" / "implementation-artifacts" / "handback"


def bundle_path(issue: str, spool: Path | None = None) -> Path:
    p = (spool or default_spool()) / f"{issue}.handback.json"
    return p


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".handback-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def save(bundle: HandbackBundle, spool: Path | None = None) -> Path:
    bundle.validate()
    p = bundle_path(bundle.issue, spool)
    _write_atomic(p, bundle.to_dict())
    return p


def load(issue: str, spool: Path | None = None) -> HandbackBundle:
    p = bundle_path(issue, spool)
    if not p.is_file():
        raise HandbackError(f"no handback bundle for {issue} at {p}")
    with open(p) as f:
        d = json.load(f)
    return HandbackBundle.from_dict(d)


def collect_git_pointer(root: Path | None = None) -> GitPointer:
    r = root or repo_root()
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=r, capture_output=True, text=True, check=True,
        ).stdout.strip()
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=r, capture_output=True, text=True, check=True,
        ).stdout.strip()
        base = subprocess.run(
            ["git", "merge-base", "origin/HEAD", "HEAD"],
            cwd=r, capture_output=True, text=True, check=False,
        ).stdout.strip()
        if not base:
            # fall back to parent commit
            base = subprocess.run(
                ["git", "rev-parse", "HEAD~1"],
                cwd=r, capture_output=True, text=True, check=False,
            ).stdout.strip()
        return GitPointer(base_sha=base, head_sha=head, branch=branch)
    except Exception as exc:
        return GitPointer(branch=f"<error: {exc}>")


def write_diff(issue: str, base_sha: str, head_sha: str, root: Path | None = None) -> Path:
    r = root or repo_root()
    out = r / "_bmad-output" / "implementation-artifacts" / "diffs" / f"{issue}.diff"
    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "diff", "--binary", f"{base_sha}...{head_sha}"],
        cwd=r, capture_output=True, text=True,
    )
    out.write_text(result.stdout or "(no diff)\n")
    return out


def is_stale(bundle: HandbackBundle, now: float | None = None) -> bool:
    now = now or time.time()
    try:
        last = datetime.fromisoformat(bundle.heartbeat.last_seen_at).timestamp()
    except Exception:
        return True
    return (now - last) > bundle.heartbeat.ttl_seconds


def next_retry_wait(bundle: HandbackBundle) -> int:
    """Fixed-count backoff. Override via RetryState.policy."""
    if bundle.retries.policy == "fixed_backoff":
        return bundle.retries.backoff_seconds * bundle.retries.attempt
    return bundle.retries.backoff_seconds


def finalize(
    issue: str,
    status: str,
    summary: str,
    *,
    evidence_file: str = "",
    test_log: str = "",
    checks: Checks | None = None,
    findings: list[dict[str, Any]] | None = None,
    worker: WorkerIdentity | None = None,
    spool: Path | None = None,
    root: Path | None = None,
) -> Path:
    """Convenience: create/update a handback bundle at the end of a worker run."""
    r = root or repo_root()
    try:
        bundle = load(issue, spool)
    except HandbackError:
        bundle = HandbackBundle(issue=issue)
        bundle.heartbeat.started_at = _now_iso()
    bundle.status = status
    bundle.summary = summary
    bundle.git = collect_git_pointer(r)
    bundle.evidence_file = evidence_file or bundle.evidence_file
    bundle.checks = checks or bundle.checks
    bundle.findings = findings or bundle.findings
    if worker:
        bundle.worker = worker
    bundle.worker.pid = os.getpid()
    bundle.worker.host = socket.gethostname()
    if not bundle.test_log:
        bundle.test_log = test_log
    if not bundle.diff_file:
        try:
            diff = write_diff(issue, bundle.git.base_sha, bundle.git.head_sha, r)
            bundle.diff_file = str(diff.relative_to(r))
        except Exception:
            pass
    bundle.bump_heartbeat()
    return save(bundle, spool)


def _cli_init(args: argparse.Namespace) -> int:
    bundle = HandbackBundle(
        issue=args.issue,
        repo_slug=args.repo_slug or "",
        worker=WorkerIdentity(
            agent_id=args.agent_id,
            agent_type=args.agent_type,
            model=args.model,
            provider=args.provider,
            session_id=args.session_id,
        ),
        git=collect_git_pointer(),
        retries=RetryState(
            attempt=1,
            max_attempts=args.max_retries,
            backoff_seconds=args.backoff,
        ),
        heartbeat=Heartbeat(ttl_seconds=args.ttl),
    )
    p = save(bundle, args.spool)
    print(p)
    return 0


def _cli_heartbeat(args: argparse.Namespace) -> int:
    bundle = load(args.issue, args.spool)
    bundle.bump_heartbeat()
    save(bundle, args.spool)
    print("OK")
    return 0


def _cli_finalize(args: argparse.Namespace) -> int:
    checks = Checks(
        tests_passed=args.tests,
        lint_passed=args.lint,
        mutation_check_passed=args.mutation,
    )
    p = finalize(
        issue=args.issue,
        status=args.status,
        summary=args.summary,
        evidence_file=args.evidence,
        test_log=args.test_log,
        checks=checks,
        worker=WorkerIdentity(agent_id=args.agent_id),
        spool=args.spool,
    )
    print(p)
    return 0


def _cli_show(args: argparse.Namespace) -> int:
    bundle = load(args.issue, args.spool)
    print(json.dumps(bundle.to_dict(), indent=2, sort_keys=True))
    return 0


def _cli_validate(args: argparse.Namespace) -> int:
    bundle = load(args.issue, args.spool)
    bundle.validate()
    print("VALID")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Momo worker hand-back bundle CLI")
    ap.add_argument("--spool", type=Path, help="handback spool directory")
    ap.add_argument("--issue", required=True, help="ticket key, e.g. 33GPM-3")
    sub = ap.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="create a new handback bundle for a worker")
    init.add_argument("--repo-slug", default="")
    init.add_argument("--agent-id", default="")
    init.add_argument("--agent-type", default="")
    init.add_argument("--model", default="")
    init.add_argument("--provider", default="")
    init.add_argument("--session-id", default="")
    init.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS)
    init.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    init.add_argument("--backoff", type=int, default=30)
    init.set_defaults(func=_cli_init)

    hb = sub.add_parser("heartbeat", help="update last_seen_at")
    hb.set_defaults(func=_cli_heartbeat)

    fin = sub.add_parser("finalize", help="finalize the handback bundle")
    fin.add_argument("--status", required=True, choices=["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"])
    fin.add_argument("--summary", required=True)
    fin.add_argument("--evidence", default="")
    fin.add_argument("--test-log", default="")
    fin.add_argument("--agent-id", default="")
    fin.add_argument("--tests", action="store_true", default=False)
    fin.add_argument("--lint", action="store_true", default=False)
    fin.add_argument("--mutation", action="store_true", default=False)
    fin.set_defaults(func=_cli_finalize)

    show = sub.add_parser("show", help="print the bundle JSON")
    show.set_defaults(func=_cli_show)

    val = sub.add_parser("validate", help="validate bundle schema")
    val.set_defaults(func=_cli_validate)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
