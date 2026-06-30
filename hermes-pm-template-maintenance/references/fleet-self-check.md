---
pipeline-status:
  - new
---
# Fleet self-check workflow

Use this lane when the operator asks for a Hermes fleet self-check, especially when PM/scrum-master agents disagree with other CLIs or when MCP servers fail only in repo-backed daemons.

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
- Confirm PM and scrum-master both bind to the same board

2. Inherited profile contract
- Read `agents/hermes/pm/runtime/profile.yaml`
- Read `agents/hermes/scrum-master/runtime/profile.yaml`
- Expect:
  - `config.inherit_from: default`
  - `config.save_mode: delta`

3. Local runtime override contract
- Read each role's `runtime/config.yaml`
- Expect override-only config, not a duplicated global config dump
- Hooks may point to shared Bloodbank publishers; that is normal

4. Shared fleet config
- Inspect `~/.hermes/config.yaml`
- Treat `mcp_servers` there as the live fleet source of truth when inherited profiles are in play
- Compare repo-local runtime state against shared `mcp_servers` before blaming the repo

5. Template and fanout baseline
- Read `33god-projects` for `.project.json` / one-board-per-repo conventions
- Read `hermes-pm-template-maintenance` for template/backfill rules
- Use `ssot-fanout` / universal-hook evidence to distinguish shared hook deployment from repo-local emitters

## Reproduction checklist

1. Confirm live CLI/runtime view
- `hermes mcp list`
- `./agents/hermes/pm/hermes mcp list`
- `./agents/hermes/scrum-master/hermes mcp list`

2. Confirm shared config entries
- Parse `~/.hermes/config.yaml` `mcp_servers`
- Record each configured server's command/url shape without exposing secrets

3. Check daemon health
- `systemctl --user status hermes-<repo>-pm-gateway.service`
- `systemctl --user status hermes-<repo>-pm-consumer.service`
- `systemctl --user status hermes-<repo>-scrum-master-gateway.service`
- `systemctl --user status hermes-<repo>-scrum-master-consumer.service`
- `systemctl --user status hermes-<repo>-scrum-master-continuous-ticket-sentinel.timer`

4. Pull runtime evidence
- Search PM and scrum-master logs for:
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
- This is a config inheritance/discovery problem before transport-level debugging

Check:
- shared `~/.hermes/config.yaml`
- named profile wiring
- runtime/profile inheritance
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

3. Gateway dead, consumer alive
- Messaging ingress may be broken even while background consumers still run
- Do not claim the agent is healthy if the gateway is down

4. Duplicate gateways share one Slack token
- Two external gateways for one repo can create avoidable startup collisions
- For PM + scrum-master repos, default to PM as ingress and treat scrum-master as an internal worker unless the architecture explicitly requires dual ingress

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

- Repo board / profile inheritance verified from live files
- Shared `mcp_servers` entries inspected from `~/.hermes/config.yaml`
- Gateway/consumer/timer status checked from systemd
- Historical log evidence gathered for each failing server
- Repo-local server artifact smoke-tested where applicable
- Every suggested fix routed to a specific board
- If tickets are created, capture board, identifier, and issue key/URL

## Pitfalls

- Do not treat current `hermes mcp list` output as the whole story when logs prove a different earlier runtime state
- Do not blame the repo-local server implementation if direct tests pass
- Do not file all MCP failures on one repo board when ownership spans shared config and external services
- Do not forget gateway health; an MCP fix does not matter if the repo's only ingress is dead
- Do not expose secrets from `runtime/.env` or shared config while collecting evidence
