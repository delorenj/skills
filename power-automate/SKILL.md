---
name: power-automate
description: "Author, edit, enable, run and debug Microsoft Power Automate cloud flows, including flows built in the Teams Workflows app, from any agent CLI. Wraps FlowAgent, the MCP engine inside Microsoft's official power-automate plugin, behind a shell CLI (scripts/pa) and an MCP launcher (pa serve). Covers the passkey-safe device-code sign-in, listing environments and flows, exporting and surgically editing a flow, creating flows from validated definition patterns (Teams webhook to card, Teams chat or channel message forwarded out), run history and diagnosis, connections, and which Teams events can reach a webhook such as n8n without a premium licence. Triggers: power automate, cloud flow, Teams workflow, Workflows app, flow definition, edit the flow, turn the flow on/off, why did the flow fail, Teams webhook, forward Teams messages, premium connector, HTTP action licence. Do NOT use for posting a message through an existing workflow (call its webhook, e.g. a repo's teams:post task), Power Apps or Power Pages apps, Copilot Studio agents, Dataverse table design, or Graph app registrations beyond the permission table in references/teams-events-and-licensing.md."
---

# power-automate

Microsoft ships an official Power Automate plugin for Claude Code and GitHub Copilot CLI
(`power-automate@power-platform-skills`). Its working part is **FlowAgent**, a self-contained
MCP server (`server/mcp.mjs`, 62 tools) that signs in through the Azure CLI. This skill makes
that engine usable from every agent: `scripts/pa` speaks MCP over stdio to it, and `pa serve`
registers it as an MCP server in any client. Provenance and what changed:
[references/provenance.md](references/provenance.md).

```bash
PA=<this skill>/scripts/pa         # python3, standard library only; needs node 18+ and az
$PA doctor                         # node, az, signed-in user, tenant, token expiry, engine (never a token)
$PA envs                           # environments
$PA flows --name "forum"           # cloud flows in the default environment (or --env <id>)
$PA get <flow-id> --path properties.definition.actions
$PA export <flow-id> -o /tmp/flow.json      # reviewable copy before any change
$PA tools                          # all 62 engine tools;  $PA tools <name> for one schema
$PA call <tool> '{"json":"args"}'  # any tool; also @file, -, or --arg key=value (JSON-parsed)
$PA batch steps.jsonl              # several calls in ONE engine session (keeps current env/flow)
$PA mcp-config codex|claude|gemini|opencode|copilot   # register `pa serve` as an MCP server
```

Exit status: 0 success, 1 tool error (the JSON says why), 2 sign-in or engine failure,
3 engine not found (`pa engine install` makes a sparse checkout of Microsoft's repo).

## Sign-in: one human step, then agents reuse it

Read [references/auth.md](references/auth.md) before the first call on a machine.

1. `pa doctor`. If `az_account` is null, run `pa login` (device code). It prints a URL and a
   code; the human opens it on any device and approves with their passkey. An agent may start it
   in a background shell and relay the code; never approve or type credentials yourself.
2. Only for connection management (creating or repairing a connection): `pa login --connectivity`.
3. After that, tokens refresh silently for every agent on the machine; the sign-in survives
   while used at least once every 90 days.

Non-secret defaults (tenant, login hint, default environment) live in
`~/.config/power-automate/profile.env`, local to the machine and never committed. Teams Workflows
flows are in the tenant's default environment, `Default-<tenantId>`, which `pa` uses when
`PA_TENANT_ID` is set.

## Working on flows

Rules: [references/flow-authoring.md](references/flow-authoring.md). Tool catalogue:
[references/engine-tools.md](references/engine-tools.md).

- **Read before writing.** `pa export <id>` first; quote the step you will change.
- **Never guess a parameter name or an id.** `get_operation_details`, `resolve_entity`,
  `resolve_params`. An `ambiguous` resolution goes back to the human.
- **Edit surgically.** `edit_flow` with `"dryRun": true`, show the diff, then apply with the
  returned `previewToken`. Parameter names containing `/` are changed with `op: merge` on the
  `parameters` object. `update_flow`/`edit_flow` keep the last 10 backups (`restore_backup`).
- **Create stopped, validate, then enable.** `validate_flow` and `preflight_flow`, then
  `create_flow` (Stopped by default), test, then `publish_flow` (= turn on). `disable_flow` turns
  it off.
- **Managed solutions are read-only** unless the human explicitly accepts `forceManaged`.
- **Debug from the run.** `get_run_history`, `diagnose_run`, `get_run_actions`,
  `get_run_action_content` (inputs/outputs of one action).
- **Webhook trigger URLs are credentials.** Store them in the secret vault, never in a repo, a
  log, a ticket or chat; `pa` never prints tokens.
- **One writer per flow.** The API has no conditional write; concurrent agents can clobber each
  other.

## Patterns

Validated or annotated definitions in `references/patterns/`:

- `teams-chat-to-email-relay.json`: every message in named group/meeting chats and in all 1:1
  DMs, forwarded as a base64 JSON event by email (standard licence only).
- `teams-channel-to-email-relay.json`: a channel's posts (and replies, once verified) forwarded
  the same way.
- `teams-webhook-to-channel-card.json`: the Teams Workflows webhook-to-channel-card shape.
- `forum-workflow-chat-step.edit.json`: `edit_flow` arguments repointing a webhook workflow's
  "post message" step at a group chat and posting the payload's `chatText`.

## Teams events to a webhook (n8n) and licensing

[references/teams-events-and-licensing.md](references/teams-events-and-licensing.md). In short:
the HTTP action and the "When an HTTP request is received" trigger are premium, the Teams
connector (including the Teams webhook trigger) and Outlook are standard. A standard flow reaches
n8n by email (Outlook "Send an email (V2)" to a Cloudflare Email Routing Worker or an IMAP
mailbox). Chats and DMs can also go straight to n8n's Microsoft Teams Trigger with delegated
`Chat.Read`; channel messages through Graph need admin consent.

## Without the engine

`pa rest GET environments` and friends call the Flow service, Dataverse or Graph with an Azure
CLI token: [references/rest-and-dataverse.md](references/rest-and-dataverse.md).
