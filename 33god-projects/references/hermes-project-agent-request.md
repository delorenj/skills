---
pipeline-status:
  - new
---
# Hermes project agent request

When a 33god project asks for a Hermes agent, the project side owns only the request and the repo-local projection. The actual fleet/runtime mechanics live in `hermes-fleet-operations`.

## What the project side provides

- A repo with a valid `.project.json` including the `ticket_provider` block.
- A target role: `pm`, `scrum-master`, `dev`, `ops`, `review`, or `qa`.
- Optional companion request: the PM role may request its scrum-master (Ticket Sentinel) companion.
- A request that the agent bind to the repo's **one** board — no role-suffixed boards.

## What pjangler writes

- `agents/hermes/<role>/` from the vendored `templates/hermes-agent` submodule.
- `~/.hermes/profiles/<repo>-<role>` pointing at `agents/hermes/<role>/runtime/`.
- `runtime/profile.yaml` with `config.inherit_from: default` and `config.save_mode: delta`.
- `runtime/config.yaml` containing only local overrides (typically `terminal.cwd`).

## What the project side does NOT do

- Edit fleet-wide shared `~/.hermes/config.yaml`.
- Decide the fleet default model or provider.
- Backfill existing agents after a template change.
- Repair systemd units or the shared Hermes checkout.

For those, route to `hermes-fleet-operations`.
