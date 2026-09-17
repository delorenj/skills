---
name: pr-creator
description: Create a requested pull request from the current task's changes, using the repository template and validation commands. Does not require PRs for ordinary delivery.
---
# Pull request creation

Inspect the branch, status, upstream, and diff before selecting changes. Preserve
unrelated WIP. Stage explicit task paths; never use `git add .` as a default.
Follow the user's and repository's delivery policy. A requested PR may need a
short-lived branch; do not turn that into a general prohibition on main commits.

1. Locate the repository's PR template and relevant contribution instructions.
2. Discover validation commands from the actual project, then run checks relevant
   to the change. Report pre-existing failures separately from new failures.
3. Lead the description with the concrete problem and resulting behavior. Include
   the checks run and material limits. Check boxes only when supported by evidence.
4. Commit and push the scoped changes as authorized. Use `gh pr create` with
   `--body-file` for multiline descriptions; do not interpolate prose into shell.
5. Verify the PR URL, source branch, base branch, and changed-file scope.

A request for a PR draft or description alone does not authorize publishing it.
Reuse existing approval and publication scope rather than asking again.
