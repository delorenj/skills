# Licensing, and getting Teams events out to a webhook (n8n)

## What is premium

A flow that uses any premium connector needs a Power Automate Premium (or per-flow, or trial)
entitlement for its owner. For event plumbing the line falls here:

| Standard (Microsoft 365 seeded licence) | Premium |
| --- | --- |
| Microsoft Teams connector: every trigger and action, including **When a Teams webhook request is received** | **HTTP** action (any outbound call to an arbitrary URL) |
| Office 365 Outlook (Send an email V2, mailbox triggers), Mail, Notifications, Approvals | **When an HTTP request is received** trigger (Request, kind `Http`) |
| SharePoint, OneDrive for Business, Forms, Planner | HTTP with Microsoft Entra ID, custom connectors, most third-party enterprise connectors |

FlowAgent's `validate_flow` flags a Request trigger of kind `Http` with `premium-trigger-warning`.

**So a standard flow can RECEIVE from the internet (Teams webhook trigger) but cannot CALL a URL.**
Check before designing around that: if a flow that uses *When an HTTP request is received*
actually runs for this owner (`pa call get_run_history --arg flow=<id>` shows Succeeded runs),
the owner holds a premium entitlement (a licence or a trial) and the HTTP action is available.

## Ways to reach n8n without premium

| Route | Works? | Latency | Notes |
| --- | --- | --- | --- |
| Outlook **Send an email (V2)** to an address whose domain uses Cloudflare Email Routing, with an **Email Worker** that POSTs to the n8n webhook | Yes | seconds | Recommended when the domain's MX is already Cloudflare Email Routing. The flow puts a base64 JSON event in the body (`PA-EVENT-B64:<b64>:END`) so HTML mangling cannot break it. |
| Same email to a mailbox n8n polls (Email Trigger (IMAP), Gmail Trigger) | Yes | about 1 minute | Simplest if no Worker is wanted. |
| **Mail** connector "Send an email notification (V3)" | Yes | as above | Sends from Microsoft's no-reply; no Outlook connection needed. |
| ntfy email publishing | Only if the ntfy server runs its SMTP listener with an MX record | | A Cloudflare-tunnelled ntfy has no inbound SMTP. It also bypasses n8n. |
| Teams "Post card / Post message" to a webhook | No | | Teams actions only post into Teams. |
| Custom connector pointing at n8n | Premium | | Custom connectors are premium. |
| HTTP action | Premium | | |

## Or skip Power Automate: Graph subscriptions from n8n

n8n's **Microsoft Teams Trigger** node (events: New Chat Message, New Channel Message, New Chat,
New Channel, New Team Member) creates and renews Microsoft Graph change-notification
subscriptions itself. It needs an Entra app registration (client id and secret in n8n's
Microsoft Teams OAuth2 credential) and these DELEGATED permissions:

| Source | Graph resource | Delegated permission | Admin consent? |
| --- | --- | --- | --- |
| Every chat the user is in (all 1:1 DMs, group and meeting chats) | `/users/{id}/chats/getAllMessages` | `Chat.Read` | Not required by Microsoft's definition, but the tenant's user-consent setting decides; if users may not consent, an admin must |
| One chat | `/chats/{chat-id}/messages` | `Chat.Read` | as above |
| One channel, posts AND replies | `/teams/{team-id}/channels/{channel-id}/messages` | `ChannelMessage.Read.All` | **Yes**, a tenant admin. Alternative: resource-specific consent `ChannelMessage.Read.Group` through a Teams app installed in that team (team-owner consent) |

n8n's default Teams scopes include `User.Read.All` and `Group.ReadWrite.All`, both admin-only:
turn on **Custom Scopes** on the credential and request only `openid offline_access User.Read
Chat.Read` (plus `ChannelMessage.Read.All` once an admin has consented). Subscriptions longer
than one hour need a lifecycle notification URL; the n8n node handles renewal.

## Recommendation per source

Do both halves through ONE intake in n8n (one webhook, one normaliser), whichever transport
delivers the event.

1. **The named group/meeting chats and every 1:1 DM.**
   - Works today, no admin, no premium: one flow on the Teams trigger **When a new chat message
     is added** (`WebhookChatMessageTrigger`, push-based, fires for every chat the flow owner is
     in). Filter `conversationId`: equal to one of the named chat ids, OR ending in
     `@unq.gbl.spaces` (every 1:1 chat id does; meeting chats are `19:meeting_...@thread.v2`,
     other group chats `19:...@thread.v2`). Then **Get message details**, then the email relay.
     Pattern: [patterns/teams-chat-to-email-relay.json](patterns/teams-chat-to-email-relay.json).
     The trigger supports one user per flow: the owner's chats only.
   - Cleaner if the tenant lets the user consent to `Chat.Read`: the n8n Microsoft Teams Trigger,
     event New Chat Message, watching all chats; filter the same ids inside n8n. Real time, no
     email hop, no flow to maintain.
2. **A team channel, posts and replies** (for example a private "forum" channel).
   - Graph needs `ChannelMessage.Read.All` (admin consent), so without an admin use a flow on
     **When a new message is added to a chat or channel** (`WebhookNewMessageTrigger`, message
     type channel) plus the email relay:
     [patterns/teams-channel-to-email-relay.json](patterns/teams-channel-to-email-relay.json).
     Graph channel subscriptions include replies; confirm the connector passes them on by
     posting a test reply and reading the run's trigger output (`replyToId` set).
   - Do NOT use **When a new channel message is added** (`OnNewChannelMessage`) for this: it fires
     for root posts only and polls every 3 minutes.
   - If replies do not come through, the remaining routes are admin consent for
     `ChannelMessage.Read.All` on the n8n app, or a Teams app with resource-specific consent in
     that team.
   - A private channel's id often is not offered in the designer's dropdown; pass the id
     directly. The Flow bot cannot POST into a private channel (posting as User can).
3. **Events that are not Microsoft's** (GitHub pull requests and their comments): no Power
   Automate. A repository or organisation webhook (events `pull_request`, `issue_comment`,
   `pull_request_review`, `pull_request_review_comment`) to the same n8n intake, or n8n's GitHub
   Trigger node.

## The n8n side of the email relay

The Email Worker (or IMAP trigger) hands n8n the message. Extract the text between
`PA-EVENT-B64:` and `:END`, base64-decode it, parse the JSON (`source`, `conversationId`,
`messageId`, `link`, `fromName`, `fromId`, `createdDateTime`, `content`, ...), and drop the
intake mail afterwards. Treat message content as untrusted input everywhere downstream.
