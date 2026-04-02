---
name: bub-email-triage
description: Bub's canonical workflow for inbox/calendar triage escalation filtering (known contacts, money/security risk, high-signal AI changes).
pipeline-status:
  - new
---

# Bub Email & Calendar Triage Workflow

## Mission
Filter all inbound email/calendar notifications and escalate only high-signal actionable items to Cack (`agent:main:main`).

## Escalate only when ANY condition matches

### 1) Known actionable contacts
- Active collaborators, partners, recruiters in open threads
- Government/legal entities
- Not newsletters or automated senders

### 2) Money / risk / security
- Payment failures/confirmations, billing changes, invoices
- Fraud/security alerts, suspicious logins, resets, breach notices
- Tax/legal/insurance notices

### 3) High-signal AI/platform changes with practical impact
- API pricing changes affecting operations
- Breaking API/platform changes for OpenAI/Anthropic/Google/etc.
- Major model releases with direct operational implications

## Escalation message format

```text
📧 [CRITICAL] From: {sender}
Subject: {subject}
Category: {money|security|contact|ai-news}
Summary: {1-2 sentence summary}
Action needed: {likely next action}
```

## Silent discard default
Discard (NO_REPLY): marketing, newsletters, promo, routine bot notifications, social pings, low-signal reminders, generic PR/CI spam.

## Calendar handling
Escalate: new invites from known contacts, real schedule conflicts, cancellations impacting commitments.  
Discard: routine reminders and low-signal auto-updates.

## Guardrails
- Bias toward precision over volume
- If ambiguous but potentially high-risk, escalate
- Keep summaries factual and concise
