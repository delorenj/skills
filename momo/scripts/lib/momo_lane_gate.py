"""momo_lane_gate — gated lane transitions (33GPM-7).

Encodes transitions to review/done as precondition checks, not later audit repairs.
Moving to `in_review` requires the close gate; moving to `completed` requires the
close gate plus the autonomous adversarial review verdict. The library shells out
to the existing sentinel scripts and `momo-board.sh` so no contract is duplicated.

Design pattern: Chain of Responsibility — each gate (close gate, autonomous review,
tree-lock guard, WIP lease) inspects the request and short-circuits on failure.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB))

from momo_handback import repo_root  # type: ignore[import]  # noqa: E402
from momo_tree_lock import TreeLockedError, guard  # type: ignore[import]  # noqa: E402


class LaneGateError(Exception):
    pass


@dataclass
class GateResult:
    gate: str
    passed: bool
    detail: str


class LaneGate:
    def __init__(self, root: Path, issue: str):
        self.root = root
        self.issue = issue
        self.role_dir = root / "agents" / "hermes" / "pm"
        self.sentinel_bin = self.role_dir / ".scripts" / "sentinel" / "bin"
        # Prefer the adapter bundled beside this installed skill. Profile installs
        # do not necessarily leave a repo-local momo checkout or role wrapper.
        self.board = Path(__file__).resolve().parents[1] / "momo-board.sh"
        if not self.board.is_file():
            self.board = root / "momo" / "skill" / "scripts" / "momo-board.sh"
        if not self.board.is_file():
            self.board = self.role_dir / ".scripts" / "momo-board.sh"

    def _run(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd, cwd=self.root, capture_output=True, text=True, timeout=180, **kwargs
        )

    def gate_tree_lock(self) -> GateResult:
        """Ensure no other active session holds the tree lock."""
        try:
            st = guard(root=self.root, owner="momo")
            if not st["locked"] or not st["fresh"]:
                return GateResult("tree_lock", True, "tree not locked")
            return GateResult("tree_lock", True, f"lock held by {st['owner']} (allowed)")
        except TreeLockedError as exc:
            return GateResult("tree_lock", False, str(exc))

    def gate_close(self) -> GateResult:
        script = self.sentinel_bin / "issue-close-gate.sh"
        if not script.is_file():
            return GateResult("close_gate", False, f"missing {script}")
        result = self._run([str(script), self.issue, str(self.root)])
        ok = result.returncode == 0
        return GateResult(
            "close_gate", ok,
            ("pass" if ok else (result.stderr or result.stdout or "fail")).strip(),
        )

    def gate_autonomous_review(
        self,
        review_file: Path | None = None,
        *,
        close: bool = False,
    ) -> GateResult:
        script = self.sentinel_bin / "issue-autonomous-review.sh"
        if not script.is_file():
            return GateResult("autonomous_review", False, f"missing {script}")
        out = review_file or (self.root / f"{self.issue}.review.md")
        command = [str(script), self.issue, str(out)]
        if close:
            command.append("--close")
        result = self._run(command)
        # Exit 0 = accepted, 3 = held/disabled, 2 = missing inputs, 1 = transition failed
        ok = result.returncode == 0
        if ok:
            detail = "accepted and completed" if close else "accepted"
        else:
            # Prefer the failure channel and preserve its full diagnostic.  In
            # particular, a required comment failure must not be hidden behind
            # earlier acceptance-shaped stdout from the canonical authority.
            detail = (result.stderr or result.stdout or "no output").strip()
        return GateResult("autonomous_review", ok, detail)

    def transition(self, target: str) -> subprocess.CompletedProcess[str]:
        if not self.board.is_file():
            raise LaneGateError(f"board adapter not found: {self.board}")
        return self._run([str(self.board), "transition", self.issue, target])

    def run(self, target: str, *, require_review: bool = True, review_file: Path | None = None) -> dict[str, Any]:
        target = target.lower()
        if target not in {"in_review", "completed"}:
            raise LaneGateError(f"no gate required for target '{target}'")

        results: list[GateResult] = []

        def blocked() -> dict[str, Any]:
            return {
                "issue": self.issue,
                "target": target,
                "allowed": False,
                "gates": [
                    {"gate": r.gate, "passed": r.passed, "detail": r.detail}
                    for r in results
                ],
            }

        tree_result = self.gate_tree_lock()
        results.append(tree_result)
        if not tree_result.passed:
            return blocked()

        close_result = self.gate_close()
        results.append(close_result)
        if not close_result.passed:
            return blocked()

        if target == "completed" and require_review:
            # The canonical autonomous-review command owns the completed
            # transition and its acceptance comment as one operation.  Calling
            # it without --close and then transitioning here would create two
            # authorities and could report acceptance for a failed transition.
            review_result = self.gate_autonomous_review(review_file, close=True)
            results.append(review_result)
            if not review_result.passed:
                return blocked()

        if target == "completed" and require_review:
            return {
                "issue": self.issue,
                "target": target,
                "allowed": True,
                "transition_authority": "autonomous_review",
                "gates": [
                    {"gate": r.gate, "passed": r.passed, "detail": r.detail}
                    for r in results
                ],
            }

        trans = self.transition(target)
        return {
            "issue": self.issue,
            "target": target,
            "allowed": trans.returncode == 0,
            "adapter_output": (trans.stdout or "").strip(),
            "adapter_error": (trans.stderr or "").strip(),
            "gates": [{"gate": r.gate, "passed": r.passed, "detail": r.detail} for r in results],
        }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gated lane transitions for Momo")
    ap.add_argument("--issue", required=True)
    ap.add_argument("--target", required=True, choices=["in_review", "completed"])
    ap.add_argument("--review-file", type=Path)
    ap.add_argument("--no-review", action="store_true", help="skip autonomous review for completed")
    args = ap.parse_args(argv)

    root = repo_root()
    gate = LaneGate(root, args.issue)
    try:
        result = gate.run(args.target, require_review=not args.no_review, review_file=args.review_file)
        print(json.dumps(result, indent=2))
        return 0 if result.get("allowed") else 1
    except LaneGateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
