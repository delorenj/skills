# n8n Workflow Description Convention

## Purpose

Until a dedicated registry service exists, the n8n `description` field IS the registry. Every workflow created or updated MUST follow this format so future agents and humans can discover, understand, and govern workflows without spelunking the n8n UI.

## Format

Every workflow's description starts with a structured block at the top:

```
PURPOSE: <one-line summary of what this workflow does>
TRIGGERS: <comma-separated triggers, e.g. "schedule:1m, webhook, googleCalendar:eventCreated">
INPUTS: <upstream data sources>
OUTPUTS: <downstream consumers>
OWNER: <github handle or name>
TAGS: <comma-separated tags for filtering>
CRITICALITY: <low | medium | high>
```

Optional prose may follow the structured block. Keep it under 3 sentences.

## Tooling Constraints (Important)

The n8n MCP tooling (`mcp__n8n-mcp__create_workflow_from_code`, `mcp__n8n-mcp__update_workflow`) caps the `description` parameter at **255 characters**. The underlying n8n data model has NO such cap, so the limit is a tool constraint, not a data constraint.

**Two paths for setting descriptions:**

1. **Compact form via MCP** (default for new workflows): trim PURPOSE to ~70 chars, single-line OUTPUTS, drop optional prose. Aim for ~245 chars total.
2. **Full form via direct n8n API** (preferred for richness): use the public API directly with `curl` to PUT the workflow with the full structured block plus prose. No length limit applies.

Direct API command shape:

```bash
N8N_API_KEY=$(op read "op://DeLoSecrets/n8n/Saved on localhost/Cont")
curl -sf -H "X-N8N-API-KEY: $N8N_API_KEY" "$HOST/api/v1/workflows/$WF_ID" \
  | jq --arg desc "$NEW_DESC" '{name, nodes, connections, settings, description: $desc}' \
  | curl -sf -X PUT -H "X-N8N-API-KEY: $N8N_API_KEY" -H "Content-Type: application/json" -d @- "$HOST/api/v1/workflows/$WF_ID"
```

Tags are NOT settable via MCP. Always use direct API for tags. See `scripts/list_n8n_workflows.sh` for the auth pattern.

## Discovery Caveat

n8n's `/api/v1/workflows` list endpoint does NOT return the `description` field. To populate the registry view, the script must fetch each workflow individually (`/api/v1/workflows/{id}`). This is why `list_n8n_workflows.sh` defaults to full mode with N+1 fetches.

## Field Definitions

| Field | Required | Notes |
|---|---|---|
| PURPOSE | Yes | Single line. Describe outcome, not implementation. |
| TRIGGERS | Yes | Format: `<source>:<event>` or `<source>:<schedule>`. Multiple triggers comma-separated. |
| INPUTS | Yes | Where data comes from. Specify accounts/calendars/topics where relevant. |
| OUTPUTS | Yes | Where data goes. List actual downstream consumers. Use `(none)` only if truly terminal. |
| OWNER | Yes | Use the github handle or the person's name. |
| TAGS | Yes | At least one project tag and one lifecycle tag. |
| CRITICALITY | Yes | Drives alerting, on-call attention, freeze rules. |

## Tag Conventions

Use lowercase, no spaces. Hyphens allowed.

**Project tags** (pick at least one):
- `33god`, `chorescore`, `agentforge`, `infra`, `personal`

**Source tags** (when applicable):
- `calendar`, `gmail`, `slack`, `github`, `webhook`, `cron`

**Account tags** (when applicable):
- `personal`, `wean`, `automaticai`

**Integration tags** (when applicable):
- `rabbitmq`, `bloodbank`, `postgres`, `qdrant`, `redis`

**Lifecycle tags** (pick exactly one):
- `experimental`, `stable`, `deprecated`

## Example: Good

```
PURPOSE: Watch jarad@automaticai.io calendar and emit normalized event payloads for downstream handlers.
TRIGGERS: googleCalendar:eventCreated (poll 1m)
INPUTS: Google Calendar (jarad@automaticai.io)
OUTPUTS: rabbitmq:bloodbank.calendar.events
OWNER: jarad
TAGS: infra, calendar, wean, automaticai, rabbitmq, bloodbank, stable
CRITICALITY: low

Polls every minute. Extend by cloning the trigger for eventUpdated/eventCancelled and routing through Normalize Event Payload.
```

## Example: Bad

```
Watches my calendar.
```

Unsearchable. No ownership. No criticality signal. No downstream context. No lifecycle marker.

## Validation Checklist

Before calling `create_workflow_from_code` or `update_workflow`, verify:

- [ ] All 7 structured fields present
- [ ] PURPOSE is one line and outcome-focused
- [ ] TRIGGERS uses `<source>:<event>` or `<source>:<schedule>` format
- [ ] OUTPUTS lists actual consumers (or `(none)` only if truly terminal)
- [ ] TAGS includes at least one project tag AND one lifecycle tag
- [ ] CRITICALITY is exactly one of: low, medium, high

If any check fails, fix before saving. Workflows without proper descriptions are invisible to discovery and a violation of the registry contract.

## Migration of Existing Workflows

When encountering an existing workflow without this format:
1. Read the workflow's nodes to infer purpose, triggers, inputs, outputs.
2. Ask the owner for OWNER, TAGS, CRITICALITY if unclear.
3. Update via `mcp__n8n-mcp__update_workflow` with the structured description.

Do not silently leave existing workflows non-compliant once you encounter them.
