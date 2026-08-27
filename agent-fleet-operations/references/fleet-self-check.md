---
pipeline-status:
  - new
---
# Fleet self-check workflow

Use this lane when the operator asks for a Hermes fleet self-check, especially when PM agents disagree with other CLIs or when MCP servers fail only in repo-backed daemons.

> **Canonical service model (2026-08):** per agent, only `hermes-<agent>-gateway.service`
> (chat ingress) and `hermes-<agent>-heartbeat.timer` (sentinel/checkpoint tick).
> Bloodbank commands enter through the single fleet-shared
> `hermes-fleet-bloodbank-gateway.service`. The scrum-master role is retired
> (folded into the PM heartbeat), and per-agent consumer/checkpoint units are
> drift — flag them, don't debug them; `pj migrate hermes.registry-parity`
> removes them.

## Goal

Produce a grounded split between:
- repo-local behavior
- shared Hermes fleet config/template drift
- external service/server drift

Do not stop at "MCP failed". Identify which layer owns each failure and route follow-up work to the right Plane board.

## Baseline architecture to confirm first

1. Repo board binding
- Read the repo root `.project.json`
- Treat `ticket_provider` as the board source of truth
- Confirm `ticket_provider.state: linked`, resolve the stored identifier and
  board id against live Plane, and reject persisted `ticket_provider.board_url`
- Confirm the PM binds to that board (one PM per repo; no scrum-master role)

2. Generated profile contract
- Confirm `~/.hermes/profiles/<repo>-pm/` is a real directory, not a symlink
- A legacy profile symlink is a pre-mutation hard stop, not a healthy alias
- Expect a generated `config.yaml`, real override-only `config.delta.yaml`,
  identity-only `profile.yaml`, and an explicit Hindsight bank pin in
  `hindsight/config.json`
- Run the profile renderer's `check`; do not infer native inheritance from an
  inert `profile.yaml` `config:` block

3. Local runtime contract
- Confirm `agents/hermes/pm/runtime/` is ignored/untracked local state, not a
  profile target, submodule, or nested Git repository
- Explicit owned-state links may target the real profile; generated fleet config
  must not be duplicated into repo-local runtime
- Hooks may point to shared Bloodbank publishers; that is normal
- Run `git check-ignore -q -- agents/hermes/pm/runtime/` and separately require
  `git ls-files -- agents/hermes/pm/runtime/` to return empty stdout

4. Shared fleet config
- Inspect `~/.hermes/config.yaml`
- Treat `mcp_servers` there as the base source and confirm the named profile's
  generated config contains the expected merge
- Compare the profile delta/rendered state against shared `mcp_servers` before
  blaming the repo

5. Template and fanout baseline
- Read `33god-projects` for `.project.json` / one-board-per-repo conventions
- Read `hermes-pm-template-maintenance` for template/backfill rules
- Use `ssot-fanout` / universal-hook evidence to distinguish shared hook deployment from repo-local emitters

## Reproduction checklist

1. Confirm live CLI/runtime view
- `hermes mcp list`
- `./agents/hermes/pm/hermes mcp list`

2. Confirm shared config entries
- Parse `~/.hermes/config.yaml` `mcp_servers`
- Record each configured server's command/url shape without exposing secrets

3. Check daemon health
- `systemctl --user status hermes-<repo>-pm-gateway.service`
- `systemctl --user status hermes-<repo>-pm-heartbeat.timer`
- `systemctl --user status hermes-fleet-bloodbank-gateway.service`
- Any `hermes-<repo>-pm-consumer.service` or `*-checkpoint.timer` sighting is
  drift, not something to debug — record it and converge with
  `pj migrate hermes.registry-parity`
- Record unit-file, enabled, active, failed, and restart state. A gateway
  intentionally deferred for lack of a channel credential must be disabled and
  inactive, not classified as broken or left in a crash loop. Heartbeat health
  is independent; its oneshot service may be inactive between successful ticks.
- Use a bounded stabilization window over `Result`, `ExecMainStatus`,
  `NRestarts`, and the latest heartbeat service result. Never close from one
  `is-active` sample.
- For each unverified/deferred channel, confirm the profile delta explicitly
  sets `platforms.<telegram|slack>.enabled: false`; fleet-base true is otherwise
  inherited and unsafe.

4. Pull runtime evidence
- Search PM gateway and heartbeat logs for:
  - `MCP: registered`
  - server names (`pjangler`, `codegraph`, `plane`, `vox`)
  - `No MCP servers configured`
  - `Failed to connect`
  - `Connection closed`
  - `Network is unreachable`
  - `No such file or directory`
  - `Slack app token already in use`

5. Verify repo-local server artifacts separately
- For repo-local stdio servers, run their direct regression/smoke test outside Hermes
- Example for pjangler:
  - `node tests/mcp-server-regressions.mjs`

## How to classify failures

### A. No servers configured now
Interpretation:
- The current runtime/CLI cannot see any `mcp_servers`
- This is a config render/discovery problem before transport-level debugging

Check:
- shared `~/.hermes/config.yaml`
- real named profile, delta, and rendered config
- renderer drift status
- wrapper / launch environment

### B. Historical logs show N failed servers
Interpretation:
- The fleet did load `mcp_servers` during that run
- Each server may still have a different root cause
- Do not collapse them into one ticket unless the evidence supports a common cause

### C. Repo-local server passes direct test but fails under Hermes
Interpretation:
- usually command-shape, PATH, env, or systemd/runtime drift
- not a server implementation bug

### D. Service worked earlier, then failed later
Interpretation:
- likely shared runtime drift or external service drift
- use log timestamps to split "always broken" from "regressed later"

## Common patterns from the June 2026 pjangler case

1. `command` contains a whole shell string
- Bad for native MCP stdio:
  - `command: "mise x -- node /path/to/server.js"`
- Good:
  - `command: "mise"`
  - `args: ["x", "--", "node", "/path/to/server.js"]`
- Or:
  - `command: "node"`
  - `args: ["/path/to/server.js"]`

2. Interactive CLI works, systemd daemon fails
- Usually PATH drift
- Prefer absolute executable paths for daemon-launched MCP servers, or explicitly export PATH in the unit/runtime env

3. Gateway dead, heartbeat alive
- Chat ingress may be broken even while the heartbeat sentinel still ticks —
  and Bloodbank command routing (fleet gateway) is independent of both
- Do not claim the agent is healthy if its gateway is down; do not claim it is
  unreachable without checking the fleet Bloodbank gateway
- First determine whether chat ingress was intentionally deferred because no
  per-agent channel credential exists. The correct state then is disabled and
  inactive, while heartbeat may remain healthy.

4. Duplicate gateways share one chat token
- Two gateways consuming one Telegram/Slack credential create startup
  collisions; the fleet gateway refuses to start the duplicate
- One dedicated bot credential per agent profile, always

5. Stale systemd units
- Timeout and env warnings usually mean template/backfill drift, not repo application drift

## Board routing rules

Open remediation tickets on the board that owns the fix:

1. Repo-specific architecture / role behavior / ingress ownership
- Use the repo board from `.project.json`
- Example: PM-only ingress for pjangler

2. Shared Hermes fleet config / template / backfill / wrapper / systemd contract
- Use the Hermes Agent PM board
- This includes:
  - shared `~/.hermes/config.yaml` MCP definitions
  - template repo changes
  - vendored submodule bump tasks
  - fleet-wide backfills

3. External service with its own board
- Use that service board
- Example: Voxxy board for vox MCP endpoint drift

4. External/shared service with no dedicated board
- Use 33GOD Infrastructure
- Example: a shared MCP bridge/server with no configured repo board

## Required output shape

Every self-check report should end with:

1. Baseline architecture summary
2. Current live state summary
3. Server-by-server root cause split
4. Repo-local vs shared-fleet vs external ownership table
5. Concrete fix list in execution order
6. Acceptance checks
7. Ticket routing recommendation

## Acceptance checks

Minimum acceptance checks for closure:

- Repo board and real profile base-plus-delta state verified from live files
- Immutable skill core verified: `33god-projects`, `delonet-conventions`,
  `delonet-dotenv`, `hermes-pm-template-maintenance`, `hindsight`, and
  `subagent-driven-development`; optional configuration only adds members
- Shared `mcp_servers` entries inspected from `~/.hermes/config.yaml`
- Gateway / heartbeat timer / fleet-bloodbank-gateway status checked from systemd
- Bounded service window proves successful `Result`, zero `ExecMainStatus`,
  stable restart count, and successful latest heartbeat result
- Credential-less gateway classified as explicitly deferred (disabled/inactive),
  never an enabled restart loop
- Shared `.env` inspected only for secret *names/patterns*; any literal
  credential is routed to a separate DeLoSecrets + `secrets.onepassword.env`
  migration without printing or migrating it during the self-check
- Historical log evidence gathered for each failing server
- Repo-local server artifact smoke-tested where applicable
- Every suggested fix routed to a specific board
- If tickets are created, capture board, identifier, and issue key/URL

## Pitfalls

- Do not treat current `hermes mcp list` output as the whole story when logs prove a different earlier runtime state
- Do not blame the repo-local server implementation if direct tests pass
- Do not file all MCP failures on one repo board when ownership spans shared config and external services
- Do not forget gateway health; an MCP fix does not matter if the repo's only ingress is dead
- Do not expose secrets from profile/runtime `.env` or shared config while
  collecting evidence. A literal credential in `~/.hermes/.env` is a finding,
  not an invitation to echo it; nonsecret toggles may remain there.
- Do not treat `pj audit`, deploy summaries, or registry dumps alone as proof;
  reconcile them with `.project.json`, profile files, and direct systemd state.
