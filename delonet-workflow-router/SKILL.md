---
name: delonet-workflow-router
description: Decision skill for new automation work. Routes the request to the right tool (n8n, a Python service, a Claude skill, cron+bash, or extending an existing workflow) and queries the n8n registry first so existing workflows are not reinvented. Use when the user wants to build, create, wire up, automate, schedule, integrate, or trigger anything. Trigger phrases include "wire up", "automate", "when X happens do Y", "build a workflow", "n8n workflow", "schedule X", "integrate A with B", "webhook", "event-driven", "pipeline", "trigger". ALWAYS run BEFORE designing or implementing new automation, even if the user already named a specific tool. Owner Jarad DeLorenzo, n8n at https://n8n.delo.sh.
---

# Workflow Router

## Purpose

Stop reinventing automation. This skill enforces three guardrails before any new workflow is built:

1. Check whether a workflow already exists that could be extended.
2. Choose the correct tool for the job using the decision tree below.
3. Apply the description convention so the workflow stays discoverable.

Run all three steps in order. Skipping any step is a failure mode.

## Step 1: Check the n8n Registry First

Before designing or implementing anything, list existing n8n workflows:

```bash
bash scripts/list_n8n_workflows.sh
```

The script reads the n8n public API at `https://n8n.delo.sh/api/v1/workflows` and prints each workflow's name, ID, active status, tags, and description.

Auth resolution order:

1. `N8N_API_KEY` env var if set
2. 1Password CLI fallback: `op read "op://DeLoSecrets/n8n/Saved on localhost/Cont"`
3. Exit non-zero with a clear error if both fail. In that case, ask the user for the key.

Decision rule:

- If a relevant workflow exists, default to extending it. Confirm with the user.
- If no relevant workflow exists, continue to Step 2.

## Step 2: Run the Decision Tree

Walk this tree top-down. Stop at the first branch that matches the request.

### Is the work orchestration across 2+ external services with humans-in-loop or visual debug value?

Route to **n8n**.

- Examples: Calendar event triggers Slack notification, Gmail to Postgres ingestion, multi-step approval workflows.
- Build via the n8n MCP server (`mcp__n8n-mcp__*` tools).

### Is the workload a pure transform or computation that needs git history, type safety, and unit tests?

Route to a **Python or Rust service**.

- FastAPI if it exposes an HTTP endpoint. Rust if performance or safety matters more than iteration speed.
- Containerize and deploy via the stacks repo (`~/docker/stacks/`). See the `stacks-deploy` skill.

### Is the work a one-shot or rare action that needs Claude's judgment to execute well?

Route to a **Claude skill**.

- Examples: Generate weekly digest, audit a repo's configs, refactor a module.
- Use the `skill-creator` skill to build it.

### Is the work a deterministic recurring shell action with no external integrations?

Route to **systemd timer or cron + bash**.

- Examples: Daily backup, log rotation, cache warming.

### Does it need state machine semantics, exactly-once delivery, or distributed coordination?

Route to a **real service backed by RabbitMQ (Bloodbank) and Postgres**, NOT n8n.

- n8n's retry and state model is too soft for these guarantees.

### Does it need sub-second latency or sustained throughput >100 req/sec?

Route to a **real service**, NOT n8n.

- n8n adds per-execution overhead that breaks these envelopes.

### Default

If no branch above matches cleanly, present the top two candidates to the user with a tradeoff summary. Do not silently pick.

## Step 3: Confirm Direction with the User

Before implementing, surface in one short message:

- Which tool was chosen and why
- Whether an existing workflow could be extended instead
- The structured description that will be applied (see Step 4)

Example:

> Routing to n8n. No existing workflow matches "calendar to slack". Description will tag TRIGGERS=googleCalendar:eventCreated, OUTPUTS=slack:#general. Proceed?

Wait for confirmation before building. This is one-line, not a multi-question gate.

## Step 4: Apply the Description Convention

Every n8n workflow created or updated MUST follow the structured description format.

Read [references/description-convention.md](references/description-convention.md) for the format and validation rules. Apply it before calling `create_workflow_from_code` or `update_workflow`.

The description field IS the registry until a real registry service exists. Skipping this step makes the workflow invisible to future discovery. Do not skip it.

## n8n vs Alternatives Cheat Sheet

| Need                                                       | Tool                            |
| ---------------------------------------------------------- | ------------------------------- |
| Trigger on external service event (Calendar, Gmail, Slack) | n8n                             |
| Scheduled multi-step orchestration                         | n8n                             |
| Pure transform with type safety and version control        | Python/Rust service             |
| Pure UI logic                                              | React component, not a workflow |
| Cron job, no external integrations                         | systemd/cron + bash             |
| Internal event-driven coordination                         | RabbitMQ consumers (Bloodbank)  |
| Long-running stateful coordination                         | Real service, not n8n           |
| Manual one-shot agentic task                               | Claude skill                    |
| Sub-second latency or high throughput                      | Real service, not n8n           |

## Failure Modes

- **Building when extending would do.** Step 1 is non-optional.
- **n8n for everything.** It is seductive because it is visual. Reject when the criteria point elsewhere.
- **Skipping the description.** A workflow without a description is invisible. Do not ship it without one.
- **Tool zealotry.** Choose by fit, not by preference. If the user already chose a tool, still walk the tree and surface a mismatch if it exists.
- **Silent picks at the default branch.** When no branch matches cleanly, present options. Do not guess.

## Resources

- `scripts/list_n8n_workflows.sh` - lists existing workflows from n8n's public API
- `references/description-convention.md` - structured description format and validation rules
