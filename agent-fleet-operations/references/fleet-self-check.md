---
pipeline-status:
  - new
---
# Workforce self-check workflow

Use this lane when the operator asks for a Hermes workforce self-check,
especially when employees disagree with other CLIs or when MCP servers fail only
in repo-backed daemons.

> **Canonical service model (since 2026-10-11):** an employee owns NO systemd
> unit. One host unit, `hermes-gateway.service` (`hermes gateway run`,
> `HERMES_HOME=~/.hermes`), multiplexes every profile: each profile's
> Telegram/Slack adapters and the Bloodbank fleet command lane (durable consumer
> `bloodbank-hermes-gateway`; profile `fleet-bloodbank-gateway`) run inside it.
> Liveness is `hermes-gateway.service` (`Restart=always`) plus
> `hermes-gateway-watchdog.timer`; scheduling is Candybar, which fires Bloodbank
> commands and Hermes invocations; persistence is krebs leases. The scrum-master
> title is retired. Per-agent `hermes-<agent>-gateway.service` units,
> `hermes-fleet-bloodbank-gateway.service`, and per-agent heartbeat, consumer and
> checkpoint units are all drift: flag them and retire them, never debug, start
> or reinstall them (a leftover per-agent gateway that starts fights the host
> role: james-brennan-pm 2026-10-20, tolt-pm 2026-11-02). `flume remediate
> hermes.registry-parity` converges the registry side and re-running
> `70-systemd.sh` (template f8da8f0+) retires leftover units. A self-check never
> restarts the host gateway; a needed restart is one batched
> `hermes-gateway-restart --reason "<why>"`.

## Goal

Produce a grounded split between:
- repo-local behavior
- shared Hermes fleet config/template drift
- external service/server drift

Do not stop at "MCP failed". Identify which layer owns each failure and route
follow-up work to the right Plane board.

## Baseline architecture to confirm first

1. Repo board binding
- Read the repo root `.project.json`
- Treat `ticket_provider` as the board source of truth
- Confirm `ticket_provider.state: linked`, resolve the stored identifier and
  board id against live Plane, and reject persisted `ticket_provider.board_url`
- Confirm the PM binds to that board (one PM per repo; no scrum-master title)

2. Generated desk contract
- Confirm `~/.hermes/profiles/<repo>-pm/` is a real directory, not a symlink
- A legacy profile symlink is a pre-mutation hard stop, not a healthy alias
- Expect a generated `config.yaml` with the renderer's header marker, a real
  override-only `config.delta.yaml`, identity-only `profile.yaml`, and an
  explicit Hindsight bank pin in `hindsight/config.json`
- Run the profile renderer's `check`; do not infer native inheritance from an
  inert `profile.yaml` `config:` block

3. Local runtime contract
- Confirm `agents/hermes/pm/runtime/` is ignored/untracked local state, not a
  desk target, submodule, or nested Git repository
- Explicit owned-state links may target the real desk; generated fleet config
  must not be duplicated into repo-local runtime
- Hooks may point to shared Bloodbank publishers; that is normal
- Run `git check-ignore -q -- agents/hermes/pm/runtime/` and separately require
  `git ls-files -- agents/hermes/pm/runtime/` to return empty stdout

4. Shared fleet config
- Inspect `~/.hermes/config.yaml`
- Treat `mcp_servers` there as the base source and confirm the named desk's
  generated config contains the expected merge
- Compare the desk delta/rendered state against shared `mcp_servers` before
  blaming the repo; a delta that redeclares a base list replaces it

5. Template and fanout baseline
- Read `33god-projects` for `.project.json` / one-board-per-repo conventions
- Read [pm-template-maintenance.md](pm-template-maintenance.md) for
  template/backfill rules
- Use `agent-config-fanout` / universal-hook evidence to distinguish shared hook
  deployment from repo-local emitters

## Reproduction checklist

1. Confirm live CLI/runtime view
- `hermes mcp list`
- `./agents/hermes/pm/hermes mcp list`

2. Confirm shared config entries
- Parse `~/.hermes/config.yaml` `mcp_servers`
- Record each configured server's command/url shape without exposing secrets

3. Check daemon health
- `systemctl --user status hermes-gateway.service` (the one host gateway; read
  only, never restart it from a self-check)
- Confirm the profile is served: `jq '.served_profiles, .parked_profiles'
  ~/.hermes/gateway_state.json` names `<repo>-pm`, and
  `journalctl --user -u hermes-gateway.service -n 200 --no-pager | grep <repo>-pm`
  shows its adapters attaching
- Scan for leftover per-agent units: `ls ~/.config/systemd/user/ | grep -E
  '^hermes-.+-(gateway|heartbeat|consumer|checkpoint)\.(service|timer)$'`. Any
  hit (for example `hermes-<repo>-pm-gateway.service` or
  `hermes-fleet-bloodbank-gateway.service`) is drift, not something to debug;
  record it and converge it with `70-systemd.sh`. The pattern needs a segment
  between `hermes-` and the suffix, so it never matches `hermes-gateway.service`
  or `hermes-gateway-watchdog.*`, which are the host's own units
- Record the host unit's active, failed and restart state. A channel
  intentionally deferred for lack of a credential is a delta pin
  (`platforms.<x>.enabled: false`) plus `provisioning_status`, not a broken
  gateway and not a disabled unit.
- Use a bounded stabilization window over `Result`, `ExecMainStatus`, and
  `NRestarts`. Never close from one `is-active` sample.
- For each unverified/deferred channel, confirm the desk delta explicitly
  sets `platforms.<telegram|slack>.enabled: false`; fleet-base true is otherwise
  inherited and unsafe.

4. Pull runtime evidence
- Search gateway logs for:
  - `MCP: registered`
  - server names (`pjangler`, `codegraph`, `plane`, `vox`)
  - `No MCP servers configured`
  - `Failed to connect`
  - `Connection closed`
  - `Network is unreachable`
  - `No such file or directory`
  - `Slack app token already in use`

5. Verify repo-local server artifacts separately
- For repo-local stdio servers, run their direct regression/smoke test outside
  Hermes
- Example for pjangler:
  - `node tests/mcp-server-regressions.mjs`

## How to classify failures

### A. No servers configured now
Interpretation:
- The current runtime/CLI cannot see any `mcp_servers`
- This is a config render/discovery problem before transport-level debugging

Check:
- shared `~/.hermes/config.yaml`
- real named desk, delta, and rendered config
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

2. Interactive CLI works, the host gateway fails
- Usually PATH drift: `hermes-gateway.service` does not run with your shell's PATH
- Prefer absolute executable paths for gateway-launched MCP servers, or set the
  PATH in the server's own `mcp_servers` env; never hand-edit the host unit for
  one profile's server

3. Chat adapter dead, Bloodbank routing alive
- Both are adapters in one process, the host gateway. A profile's Telegram/Slack
  adapter may fail (dead or parked bot, auth error) while the Bloodbank lane of
  the same `hermes-gateway.service` still routes commands to that profile
- Do not claim the agent is healthy if its chat adapter is down; do not claim it
  is unreachable without checking the host gateway's Bloodbank lane
  (`Bloodbank gateway connected` in its journal) and the agent's registry
  eligibility (`enabled` absent or `true` -- no key means enabled, explicit
  `false` quarantines -- `gateway_scope: fleet`, matching `target_agent_id`,
  nonblank `profile_name`)
- First determine whether chat ingress was intentionally deferred because no
  per-agent channel credential exists. The correct state then is
  `platforms.<x>.enabled: false` in the delta plus a deferred/offline
  `provisioning_status`.

4. Duplicate gateways share one chat token
- Two gateways consuming one Telegram/Slack credential create startup
  collisions; the second refuses to start
- One dedicated bot credential per agent desk, always

5. Stale systemd units and launchers
- Timeout and env warnings usually mean template/backfill drift, not repo
  application drift
- Any per-agent unit is drift whatever its env says; retire it. A role launcher
  (`agents/hermes/<title>/hermes`) whose `HERMES_HOME` is not the named desk path
  is split-brain; that is `hermes.profile-wiring`

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

- Repo board and real desk base-plus-delta state verified from live files
- PM skill ownership verified with `skillex profile show <name> --project <repo>
  --json` and a strict sync preview: real root, recorded selected canonical
  targets, persistent strict policy, bundled opt-out, no local shadows, and
  empty `skills.external_dirs`. Actual Hermes discovery contains only that map.
- Shared `mcp_servers` entries inspected from `~/.hermes/config.yaml`
- `hermes-gateway.service` status checked; the profile is served
  (`gateway_state.json` `served_profiles`); no per-agent gateway unit present
- Bounded service window proves successful `Result`, zero `ExecMainStatus`, and a
  stable restart count on the host unit
- Credential-less channel classified as explicitly deferred (delta
  `platforms.<x>.enabled: false` plus `provisioning_status`), never an enabled
  restart loop
- Shared `.env` inspected only for secret *names/patterns*; any literal
  credential is routed to a separate DeLoSecrets + `secrets.onepassword.env`
  migration without printing or migrating it during the self-check
- Historical log evidence gathered for each failing server
- Repo-local server artifact smoke-tested where applicable
- Every suggested fix routed to a specific board
- If tickets are created, capture board, identifier, and issue key/URL

## Pitfalls

- Do not treat current `hermes mcp list` output as the whole story when logs prove
  a different earlier runtime state
- Do not blame the repo-local server implementation if direct tests pass
- Do not file all MCP failures on one repo board when ownership spans shared
  config and external services
- Do not forget channel health; an MCP fix does not matter if the repo's only
  chat adapter is dead
- Do not expose secrets from desk/runtime `.env` or shared config while
  collecting evidence. A literal credential in `~/.hermes/.env` is a finding,
  not an invitation to echo it; nonsecret toggles may remain there.
- Do not treat `flume audit`, `flume review`, hire summaries, or registry dumps
  alone as proof; reconcile them with `.project.json`, desk files, the host
  gateway's `served_profiles`, and direct `hermes-gateway.service` state. A `flume review` verdict of `unproven` ("unable to assess")
  means the observation could not be trusted — it is not a pass.
