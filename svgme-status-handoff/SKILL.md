---
name: svgme-status-handoff
description: Deterministic SVGMe/Cack status handoff workflow for cron or manual updates. Use when reporting repo state, blockers, unknowns, and next actions with git evidence (branch, head, status, stashes, PRs, branch inventory, test health), and when avoiding repetitive status spam by summarizing deltas only.
---

# SVGMe Status Handoff

Run this workflow for status updates to leadership (Cack/Jarad) where evidence and consistency matter.

## Required evidence commands

Run exactly:

1. `git rev-parse --abbrev-ref HEAD`
2. `git log -1 --oneline`
3. `git status --short`
4. `git stash list`
5. `gh pr list --state open`
6. `git branch --all --list '*SVGME*'`

If testing context changed, run:

- `pytest -q web/test_api.py web/test_app_onboarding.py`
- `pytest -q web/test_api_smoke.py`
- `cargo test -q`

## Output format

Always respond in this structure:

- **Facts**
- **Unknowns**
- **Blockers**
- **Next action**

Never use guess language where commands can verify facts.

## Delta-only anti-spam rule

For periodic cron handoffs, do not resend identical full reports repeatedly.

- If state changed, report the change and refreshed evidence.
- If state is unchanged, send one compact line: "No material change since last sweep; tests/PR state unchanged." plus any new risk.
- Aggregate repetitive updates in daily memory as a single summarized block instead of many near-duplicate entries.

## Policy defaults

- PR-first delivery.
- Keep strict API-key enforcement unless explicitly changed by leadership decision.
- If a prioritization tradeoff appears, request a direct call quickly and continue execution immediately after decision.
