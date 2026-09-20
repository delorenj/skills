---
pipeline-status:
  - new
---
# Hermes project agent request

When a 33god project asks for a Hermes agent, the project side owns only the
request and the repo-local projection. The command is `flume hire <title>`, and
the fleet/runtime mechanics behind it live in `agent-fleet-operations`.

## What the project side provides

- A repo with valid `.project.json` bytes and a Plane `ticket_provider` whose
  state is `linked` and whose identifier/board id resolve live. Do not persist
  `ticket_provider.board_url`.
- A job title: `pm` for the standard project deployment, and it is the default
  argument — `flume hire` and `flume hire pm` are the same request.
- A request that the agent bind to the repo's **one** board — no role-suffixed boards.

## What Flume writes

- `agents/hermes/<title>/` from Flume's own version-locked
  `templates/hermes-agent` submodule.
- A real `~/.hermes/profiles/<repo>-<title>/` directory with identity metadata,
  an explicit Hindsight bank pin, a generated `config.yaml`, and a real
  override-only `config.delta.yaml`.
- Ignored repo-local `agents/hermes/<title>/runtime/` state. It is neither the
  profile target nor a nested Git repository; explicit owned-state links are
  the only bridge to the named profile.
- Exactly one systemd unit, `hermes-<agent-id>-gateway.service`. If no channel
  credential is supplied the gateway is explicitly deferred, disabled, and
  inactive, and the profile delta must set both `platforms.telegram.enabled`
  and `platforms.slack.enabled` false until ownership of the corresponding
  dedicated credential is verified.
- The org-chart row in `~/.hermes/agents-registry.yaml`. That row is the record;
  `.project.json.agents` is its projection, and `pj init` only carries it
  forward.
- The skill core pinned by `fleet.symlinked_runtime_skills` in
  `~/.config/hermes-agent-template/config.toml`. Read the pin rather than
  trusting a list in a document; configuration may append but never subtract.

If the expected named profile is a legacy symlink, or `.project.json` is
malformed, hiring aborts before any mutation. The fleet runbook owns the
sealing and migration procedure.

## What the project side does NOT do

- Edit fleet-wide shared `~/.hermes/config.yaml`.
- Decide the fleet default model or provider.
- Backfill existing agents after a template change.
- Repair systemd units or the shared Hermes checkout.
- Modify or restart `hermes-fleet-bloodbank-gateway.service`.
- Remove an agent's record. `pj project identity` reports an abandoned agent and
  names the command; `flume offboard <employee>` is what deletes the row, and it
  is a dry run until `--apply`.

For those, and for the required pre/post/convergence proof, route to
`agent-fleet-operations` `references/pm-deployment.md`.
