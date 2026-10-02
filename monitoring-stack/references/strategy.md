# DeLoNET observability strategy

Approved 2026-10-02. The strategy is deliberately split by data shape and consumer; no UI owns the data.

## Canonical layers

| Data shape | System of record / query engine | Primary consumers |
| --- | --- | --- |
| Immutable 33GOD facts | Bloodbank event on NATS, projected by Candystore | Holocene, replay/backfill, audit |
| Numeric time series | Prometheus | Grafana, Alertmanager, aggregate Holocene panels |
| Logs | Loki | Grafana Explore and incident correlation |
| Traces | Tempo, once enabled | Grafana Trace UI and request correlation |
| Operator incident/exploration UI | Grafana | Homelab operator |
| Product control-plane UI | Holocene | Everyday fleet, agent and pipeline operation |

Grafana is not an intermediary API and must never sit between Holocene and its data. Holocene reads Candystore, Prometheus or Loki directly (or through owned service APIs), while Grafana reads the same durable stores for exploration and incident response.

## AutomaticAI LLM usage

- Settled gateway requests publish `bloodbank.evt.llm.usage.recorded`.
- Provider-reported subscription windows publish `bloodbank.evt.llm.allowance.observed`.
- The schemas are authoritative in `~/code/33GOD/bloodbank/schemas/bloodbank/llm/`.
- Event identity and ordering keys are deterministic so exporter retries and ledger backfill do not duplicate facts.
- `usage.input_tokens` is normalized to uncached input plus cache reads plus cache writes, matching GenAI semantic-convention intent while retaining component counts.
- Gauges are filled from provider utilization/reset data, never inferred from token counts. Gateway ledger tokens split the used portion by model and expose any unexplained use as outside-gateway usage.
- Events never contain prompts, prompt hashes, proof markers, credentials or resolved secrets.

The NewAPI ledger remains the request-level source. An exporter tails it with a read-only role and durable cursor; it does not add synchronous NATS publication to the relay hot path.

## Cardinality and privacy

- Keep Prometheus labels bounded: account, provider, route/model, consumer, project and window are useful; session ID, request ID and prompt identity are not.
- Query Candystore or a bounded recent-event API for live per-session panels.
- Do not mirror every Bloodbank envelope into Loki. Candystore owns durable events; export low-cardinality counters to Prometheus and, when needed, selected structured summaries to Loki.
- Host or container logs may contain incidental operational detail; treat them as logs, not canonical facts.

## Current integration gaps

The stack already has Prometheus, Grafana, Alertmanager, Loki, Alloy, cAdvisor, node/process exporters and an OTLP collector. Known gaps:

- Alloy tails Docker logs, not systemd/journald services.
- Traefik and NATS expose metrics but are not scraped.
- Redis and Postgres exporters are absent.
- Cloudflare and scoped client AWS accounts are not integrated.
- Tempo is provisioned as a Grafana datasource but not running; OTel traces currently go to the collector debug exporter.
- Prometheus `docker` and `metamcp` jobs are down because `host.docker.internal` does not resolve in their containers.
- Bloodbank NATS runs with `-DV`, producing hundreds of MB of trace logs per day; keep monitoring, remove production trace verbosity.
