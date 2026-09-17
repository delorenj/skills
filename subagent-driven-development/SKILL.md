---
name: subagent-driven-development
description: Run an explicitly requested implementation-and-review team for independent tasks. Availability in a PM profile does not mandate delegation or multiple reviews for routine work.
---
# Requested implementation team

Use this workflow when delegation is requested or otherwise explicitly authorized
and independently useful tasks exist. Keep ordinary bounded work with the current
agent. Repository and user delivery instructions govern branches and publication.

Assign each worker a concrete outcome, file ownership, acceptance checks, and
side-effect boundary. Tell workers they share the codebase, must preserve others'
changes, and must adapt to concurrent work. Supply the context needed for the task.

Choose review depth from the changed behavior. Use a separate reviewer when the
risk or verification gap warrants it; do not require two reviewers per task or a
final review by default. Reproduce findings and rerun only invalidated checks.
A failed subtask can be repaired directly; preserving context is not a reason to
spawn another worker. Respect available agent limits and user-selected models.

Integrate completed work promptly using `merge-forward` or the repository's own
workflow. Report implemented behavior, verification, and any remaining blocker.
There is no required dependency on the Superpowers skill family.
