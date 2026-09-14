---
name: upstream-sync-pr
description: Use when syncing Damian's fork with Jarad's upstream repository, preserving local work, pushing a Codex branch to the fork remote, and opening a pull request into the upstream main branch.
metadata:
  short-description: Sync fork and open upstream PR
---

# Upstream Sync PR

Use this workflow for CoachingAgentFramework fork/upstream handoffs.

## Remotes

Expected remotes:

- `fork`: Damian's fork, `DamiMiller/CoachingAgentFramework`
- `origin`: Jarad's upstream, `delorenj/CoachingAgentFramework`

Verify with `git remote -v` before pushing or creating a PR.

## Workflow

1. Inspect state:
   - `git status --short`
   - `git branch --show-current`
   - `git remote -v`
2. Preserve local work:
   - Do not run `git reset --hard`, `git checkout -- .`, or destructive cleanup.
   - If the current branch already has a PR, create a fresh `codex/` branch for a new PR.
3. Sync awareness:
   - Fetch upstream with `git fetch origin main`.
   - If local work is dirty, commit first or create the new branch before any rebase/merge.
   - Prefer a normal PR into `origin/main` over risky local history surgery.
4. Validate:
   - Run the relevant local quality gate before commit when the change touches code.
   - For `lamp-skills`, the standard gate is full pytest, ruff, and mypy inside Docker.
5. Commit:
   - Stage intentional files only, including new untracked files.
   - Use a concise message that describes the ticket wave or workflow.
6. Push to Damian's fork:
   - `git push -u fork <branch>`
7. Create the upstream PR:
   - `gh pr create --repo delorenj/CoachingAgentFramework --base main --head DamiMiller:<branch>`
   - Include local verification results and any external blockers.

## Guardrails

- Never push directly to `origin/main`.
- Never mark GitHub branch protection done unless the protection write succeeds.
- If GitHub returns `404` for branch protection, treat it as missing admin permission.
- Keep secrets, `.env*`, backup files, and local `session_data/*` out of commits.
