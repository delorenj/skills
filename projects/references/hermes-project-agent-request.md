---
pipeline-status:
  - new
---
# Hermes project agent request

When a 33god project asks for a Hermes agent, the project side owns only the request and the repo-local projection. The actual fleet/runtime mechanics live in `agent-fleet-operations`.

## What the project side provides

- A repo with valid `.project.json` bytes and a Plane `ticket_provider` whose
  state is `linked` and whose identifier/board id resolve live. Do not persist
  `ticket_provider.board_url`.
- A target role: `pm` (the unified single-PM model — the retired scrum-master's
  sentinel duties run on the PM heartbeat, so there is no companion to request).
- A request that the agent bind to the repo's **one** board — no role-suffixed boards.

## What pjangler writes

- `agents/hermes/<role>/` from the vendored `templates/hermes-agent` submodule.
- A real `~/.hermes/profiles/<repo>-<role>/` directory with identity metadata,
  an explicit Hindsight bank pin, a generated `config.yaml`, and a real
  override-only `config.delta.yaml` (typically only `terminal.cwd`).
- Ignored repo-local `agents/hermes/<role>/runtime/` state. It is neither the
  profile target nor a nested Git repository; explicit owned-state links are
  the only bridge to the named profile.
- The gateway unit plus heartbeat timer/service. If no channel credential is
  supplied, the gateway is explicitly deferred, disabled, and inactive; the
  independently healthy heartbeat remains enabled. The profile delta must
  explicitly set both `platforms.telegram.enabled` and
  `platforms.slack.enabled` false until ownership of the corresponding
  dedicated credential is verified.
- The immutable required skill core: `33god-projects`, `delonet-conventions`,
  `delonet-dotenv`, `agent-fleet-operations`, `hindsight`, and
  `subagent-driven-development`. Optional configuration may only add skills.
  `hermes-pm-template-maintenance` is deprecated; fleet/template maintenance is
  owned by `agent-fleet-operations`.

If the expected named profile is a legacy symlink, or `.project.json` is
malformed, provisioning aborts before any mutation. The fleet runbook owns the
sealing and migration procedure.

## What the project side does NOT do

- Edit fleet-wide shared `~/.hermes/config.yaml`.
- Decide the fleet default model or provider.
- Backfill existing agents after a template change.
- Repair systemd units or the shared Hermes checkout.
- Modify or restart `hermes-fleet-bloodbank-gateway.service`.

For those, and for the required pre/post/convergence proof, route to
`agent-fleet-operations` `references/pm-deployment.md`.
