---
name: coding-strategy
description: Compare execution or provider options when explicitly asked to choose an agent strategy. Not a prerequisite for coding and not part of the default global loadout.
---
# Execution strategy

Start with the current agent and the requested outcome. Delegate only when
independent work can proceed usefully and delegation is authorized. File count
alone is not a reason to spawn agents or install an orchestration framework.

When asked to compare providers, inspect the user's current access, installed
commands, supported models, and budget. Verify changing prices and capabilities
rather than using a frozen subscription table. Do not silently override the
user's selected provider or model.

Prefer a bounded implementation and its necessary checks. Use `merge-forward`
for repository integration; the explicit `subagent-driven-development` workflow
is available when a user requests a separate implementation/review team.
