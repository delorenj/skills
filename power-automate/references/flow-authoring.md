# Authoring and editing flows

Distilled from Microsoft's plugin references (`definition-reference.md`,
`connection-patterns.md`, `error-troubleshooting.md`) and checked against FlowAgent 3.2.1's
validator and templates.

## Definition rules (validate_flow enforces them)

```json
{
  "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "$authentication": { "defaultValue": {}, "type": "SecureObject" },
    "$connections": { "defaultValue": {}, "type": "Object" }
  },
  "triggers": { },
  "actions": { },
  "outputs": {}
}
```

1. Declare both `$authentication` and `$connections` (a missing `$authentication` surfaces as a
   500 `NullReferenceException`). `create_flow` injects them if absent.
2. Connector actions are `"type": "OpenApiConnection"` (never `ApiConnection`) with
   `inputs.host = {apiId, operationId, connectionName}` and `inputs.parameters`.
3. Push triggers are `"type": "OpenApiConnectionWebhook"`; polling triggers are
   `OpenApiConnection` with a `recurrence`. Use `splitOn` (for example
   `@triggerOutputs()?['body/value']`) to get one run per item; `triggerBody()` is then the item.
4. Never put `authentication` in action inputs; Power Automate injects it.
5. `host.connectionName` must be a key of the connection references.
6. Every `runAfter` must name an existing action. No `@odata.bind` parameter suffixes.
7. Connection references use `"source": "Embedded"`. `Invoker` fails with
   `InvokerConnectionOverrideFailed` when the flow is run by API.
8. Any JSON string that starts with `@` is parsed as an expression. A literal that starts with
   `@` (for example the 1:1 chat suffix `@unq.gbl.spaces` as a condition operand) must be written
   `@@unq.gbl.spaces`, or kept inside an expression as `'@unq.gbl.spaces'`. `validate_flow`
   does not catch this; the save fails with a template error.

```json
"connectionReferences": {
  "shared_teams": {
    "connectionName": "<from pick_or_create_connection or resolve_refs>",
    "source": "Embedded",
    "id": "/providers/Microsoft.PowerApps/apis/shared_teams",
    "tier": "NotSpecified"
  }
}
```

## Never guess a parameter name or an id

Connector parameters are often dynamic and their keys contain `/` (`body/recipient`,
`emailMessage/To`). Resolve them instead of guessing:

```bash
pa call search_operations --arg query="post message" --arg connector=shared_teams
pa call get_operation_details --arg connector=shared_teams --arg operation=PostMessageToConversation
pa call resolve_entity --arg connector=shared_teams --arg entityType=groupId --arg query="Team name"
pa call resolve_entity --arg connector=shared_teams --arg entityType=channelId --arg query="Channel name" \
  --arg 'dependencies={"groupId":"<team id>"}'
pa call resolve_params '{"connector":"shared_teams","operation":"PostMessageToConversation", ...}'
pa call pick_or_create_connection --arg connector=shared_office365     # Connectivity sign-in; see auth.md
```

`resolve_entity` is fail-closed: an `ambiguous` result goes back to the human, never into a flow.

## Operation ids used by the patterns

From Microsoft's connector reference and FlowAgent's built-in templates. Confirm parameters with
`get_operation_details` before creating a flow.

| Connector | Operation | operationId | Kind |
| --- | --- | --- | --- |
| Teams | When a new chat message is added (any chat the owner is in) | `WebhookChatMessageTrigger` | webhook trigger; outputs `value[]` of `conversationId`, `messageId`, `linkToMessage` |
| Teams | When a new message is added to a chat or channel | `WebhookNewMessageTrigger` | webhook trigger; `threadType` + dynamic `requestBody` |
| Teams | When a new channel message is added (root posts only, 3-minute poll) | `OnNewChannelMessage` | polling trigger |
| Teams | When I'm @mentioned / When keywords are mentioned | `WebhookAtMentionTrigger` / `WebhookKeywordTrigger` | webhook triggers |
| Teams | When a Teams webhook request is received | `TeamsIncomingWebhookTrigger` | standard-licence webhook trigger; answers 202 when queued |
| Teams | Post message in a chat or channel | `PostMessageToConversation` | `poster` (`Flow bot`/`User`), `location` (`Channel`, `Group chat`, `Chat with Flow bot`), `body/recipient`, `body/messageBody` |
| Teams | Post card in a chat or channel | `PostCardToConversation` | channel target `body/recipient/groupId` + `body/recipient/channelId`, card in `body/messageBody` |
| Teams | Get message details | `GetMessageDetails` | `messageId`, `threadType`, recipient |
| Outlook | Send an email (V2) | `SendEmailV2` | `emailMessage/To`, `emailMessage/Subject`, `emailMessage/Body` |
| Outlook | When a new email arrives (V3) | `OnNewEmailV3` | polling trigger |

Teams ids: a 1:1 chat is `19:<a>_<b>@unq.gbl.spaces`, a meeting chat `19:meeting_<x>@thread.v2`,
another group chat `19:<x>@thread.v2`, a channel `19:<x>@thread.tacv2` (team = its group id, a
GUID). Ids pasted from a Teams link are URL-encoded (`%3A` is `:`, `%40` is `@`).

Limits worth knowing: a Teams post is capped near 28 KB; the Flow bot cannot post into a private
channel; *When a new chat message is added* serves one user per flow; a Teams webhook answers 202
on queueing, so a disabled flow fails silently afterwards.

## Patterns

| File | What |
| --- | --- |
| [patterns/teams-chat-to-email-relay.json](patterns/teams-chat-to-email-relay.json) | Named chats + all DMs to an email relay (validated: `valid: true`) |
| [patterns/teams-channel-to-email-relay.json](patterns/teams-channel-to-email-relay.json) | One channel to an email relay; resolve the trigger's channel keys first |
| [patterns/teams-webhook-to-channel-card.json](patterns/teams-webhook-to-channel-card.json) | Teams webhook to a channel card, one per attachment; copy the trigger from a live flow |
| [patterns/forum-workflow-chat-step.edit.json](patterns/forum-workflow-chat-step.edit.json) | `edit_flow` arguments that repoint a webhook workflow's chat step at another group chat and post the payload's `chatText` |

Each pattern file holds `definition` + `connectionReferences` (or `edit_flow` arguments). Fill
the `<...>` placeholders, then `validate_flow` / `preflight_flow` before `create_flow`.

## Lifecycle

```bash
# create (always Stopped first). Note the argument names differ per tool:
# validate_flow/create_flow take connectionRefs, preflight_flow takes connectionReferences.
jq '{definition, connectionReferences}' pattern.json > /tmp/pre.json
pa call preflight_flow @/tmp/pre.json           # definition + connection refs + solution-wrap risk
jq '{name: "My flow", definition, connectionRefs: .connectionReferences}' pattern.json > /tmp/create.json
pa call create_flow @/tmp/create.json           # refuses a duplicate display name; returns the flow id
pa call run_flow --arg flow=<id> --arg wait=true  # manual-trigger flows only
pa call publish_flow --arg flow=<id>            # turn it on (publish_flow = enable/start)
pa call disable_flow --arg flow=<id>            # turn it off

# change an existing flow
pa export <id> -o /tmp/<id>.before.json         # reviewable copy first
pa call edit_flow @edit.json                    # with "dryRun": true -> diff + previewToken
pa call edit_flow @edit.json --arg dryRun=false --arg previewToken=<token>
pa call list_backups --arg flow=<id>            # update/edit keep the last 10 snapshots
pa call restore_backup --arg flow=<id> --arg file=<backup>

# debug
pa call get_run_history --arg flow=<id> --arg top=5
pa call diagnose_run --arg flow=<id> --arg run=<run id>
pa call get_run_action_content --arg flow=<id> --arg run=<run id> --arg action=<name> --arg which=outputs
```

`edit_flow` paths are slash-delimited into the definition (`actions/Send_Email/inputs`). A
connector parameter whose NAME contains `/` cannot be addressed by a path: use `op: merge` on the
`.../inputs/parameters` object with the parameter names as keys (siblings are preserved).

`update_flow`, `edit_flow`, `publish_flow`, `disable_flow` and `delete_flow` refuse flows in a
managed solution unless `forceManaged: true`; the change would be overwritten by the next
solution import. `update_flow` and `edit_flow` re-check the flow's last-modified time before
writing, but the API has no conditional write, so two writers can still race: one agent per flow.

## Teams Workflows specifics

Flows created in the Teams **Workflows** app are ordinary cloud flows in the tenant's default
environment, owned by whoever built them, and editable here. Signing a Teams or Outlook
connection in as a person (posting "as User") happens when the connection is created or fixed,
not in the definition. When a repository documents a specific workflow (IntelliForia's forum
workflow: `docs/guides/teams-team-channel.md` in that repo), read that guide first and change
only the step it describes.
