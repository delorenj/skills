# Read-only Holocene and operating proof

Surface: `https://holocene.delo.sh/wax`, sibling to Agents/Projects/Voice.
API: `/api/modules/wax/catalog`. Holocene's host API invokes the absolute Wax
CLI; the web container does not read the Wax checkout or SQLite directly.

## Read contract

`wax catalog --json` exposes pass purposes/capabilities, availability, registry
conditions, compiled graph and edge policies, trigger/binding configuration,
scoped recent receipt summaries, registry drift and worker heartbeat. Allowlist
fields at both CLI and API boundaries. Exclude pass env/command argv, credentials,
raw stderr/error prose and note bodies; detailed CLI `ep status` is not this API.
Recent runs carry machine reason codes, not raw provider error text.

Distinguish unavailable/disabled/uncompiled from healthy idle. When the CLI fails,
show source DOWN and any last-good value as stale; never return an empty healthy
catalog. A freshly generated response is not worker proof: inspect heartbeat age,
actual binding `last_scan_at` and receipts. The dedicated heartbeat stays fresh
through long work; busy/stuck scan age is different evidence from process death.

Pipeline nodes/conditions/edges must render the **frozen** compiled definition,
not be re-derived from current registry YAML. Registry totals and pipeline totals
have different scope/version meaning. `exported_snapshot` does not prove live
n8n draft synchronization. Intentional graph conditions may look like registry
drift even at the same pass version. No hidden editor/enable/run buttons here.

## Source owners

- Wax: `components/wax/src/wax/catalog.py`, `pipelines.py`, `documents.py`, CLI.
- Holocene: `~/code/33GOD/holocene/apps/api/src/wax.ts` + `wax.test.ts`;
  `apps/web/app/wax/` plus hub/voice sibling navigation.
- Durable shared facts: Bloodbank/Candystore; numeric/log/trace work belongs to
  the monitoring stack. Do not add another durable store or send Holocene via
  Grafana to get Wax data.

## Change/deploy proof (only when authorized)

Run affected isolated API tests and web typecheck/build; planted-secret fixtures
must cover compiled nodes and recent-run receipts, not only pass registry rows.
For Wax Python changes restart `waxd.service` and verify the worker heartbeat
and active capture survive as intended. For n8n package changes use native loader
and actual editor checks in [pipelines-and-n8n.md](pipelines-and-n8n.md).

Holocene live API is `holocene-api.service` running `apps/api/dist/server.js` on
4000. Live web is `holocene-web` in the parent **33god-platform** Compose project,
not automatically the component-local Compose file. Read Holocene's current
`AGENTS.md`, confirm container Compose labels, use its deploy workflow, and verify
public `/wax`, API source freshness, frozen graph and receipt display. Preserve
unrelated work and advance any parent component pin under the delivery policy.

No service restart, pipeline compile, provider call or production replay is
required just to capture these procedures into skills. Use existing release
proof and offline metadata/link/fixture checks for that task.
