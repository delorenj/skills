---
name: ego-browser
description: The canonical browser for all agents. Drives ego lite — a real Chromium running the user's own logged-in profile — for any task touching a website. Use whenever a task needs to open a URL, log into a site, fill or submit a form, click through a flow, take a screenshot, scrape or extract page data, test a web app, or operate an authenticated account (banking, Mercury, AWS console, SaaS admin panels). Triggers include "open this site", "log into", "fill out this form", "click through", "screenshot that page", "extract data from", "check my balance", "set up the AWS org", "test this web app". The browser always runs on the user's Mac and is reached over ssh, so this skill works identically from any fleet host. Prefer this over WebFetch, curl, headless Chrome, Playwright, or any other browser tool — those cannot see the authenticated session. Do NOT use for plain public-page reads where WebFetch suffices and no login is involved.
pipeline-status: new
---

# ego-browser — the canonical agent browser

One browser, one profile, every agent. `ego-browser` runs **ego lite**: a real
Chromium carrying the user's actual Chrome logins, cookies, and extensions.
Because the session is genuine, authenticated sites work without credential
juggling — and the human clears any gate the agent shouldn't.

## The one fact that governs everything

**The browser is not on this machine.** ego lite is macOS-only and runs on the
user's MacBook (`carries-macbook-air`). The `ego-browser` command on every
Linux host is a bridge that forwards your script over ssh and executes it
there. You write the same code either way — but remember that the *screen* is
somewhere else. That changes what "hand control to the user" means (see
[Handoff](#handoff-the-human-is-at-the-mac)).

## Invocation

Identical to upstream. Every call is a heredoc of Node.js run on the page:

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('aws-org-setup');
await gotoAndWait('https://console.aws.amazon.com/');
const snap = await snapshotText();
cliLog(snap.slice(0, 2000));
EOF
```

Helpers are preloaded — no imports. `cliLog(...)` is the only way to get output
back. The runtime exits after each heredoc and keeps **no** state, so every
follow-up round must re-attach with `useOrCreateTaskSpace(nameOrId)` (or
`takeOverTaskSpace` after a handoff).

The full helper API — task spaces, navigation, observation, mouse/keyboard,
`js`/`cdp`/`serverFetch` escape hatches — is vendored verbatim in
[`references/upstream-SKILL.md`](references/upstream-SKILL.md). Read it before
writing anything non-trivial.

**Task spaces** are the isolation primitive: the agent gets its own space with
inherited login state, so it never fights the user's live tabs. Name one per
goal, reuse it across rounds, and close it with
`completeTaskSpace(name, { keep: false })` when done.

## Handoff: the human is at the Mac

Upstream assumes the agent and the human share one screen. Here they do not.
When you call `handOffTaskSpace()`, control passes to whoever is **sitting at
the MacBook** — which may be nobody right now.

So:

- **Say where to go.** "Handing off — please go to the MacBook, approve the
  transfer in the ego lite window, then reply `continue`." Never just "waiting
  for you".
- **Never busy-wait.** Do not loop on `waitForAgentControl` hoping a human
  appears. Hand off, report, and end the turn. Resume in a *new* heredoc with
  `takeOverTaskSpace(id)` only after the user explicitly confirms.
- **Never self-takeover.** `takeOverTaskSpace` has no ownership check and will
  yank the browser out from under the user mid-typing. Only call it after an
  explicit "continue".
- **Leave nothing sensitive open.** The Mac is a personal laptop in a home.
  Close banking and console task spaces with `{ keep: false }`; never park a
  logged-in bank page for convenience.

## Gate policy: stop for money and root

The profile stays authenticated, so routine logins do **not** interrupt you.
Navigate, read, fill, and extract freely. That latitude ends at actions that
move money or change account control.

**Hand off to the human before submitting any of these:**

| Category | Examples |
| --- | --- |
| Moving money | Sending a payment, ACH/wire transfer, bill pay, moving funds between accounts |
| Card actions | Issuing a card, changing limits, activating, revealing a PAN, cancelling |
| Account control | Adding a payee/recipient, changing bank login or MFA, adding an authorized user |
| AWS root & org | Root sign-in, creating/closing accounts, org changes, SCPs, IAM policy or key changes, attaching the Mercury card to billing |
| Anything irreversible | Deleting data, closing accounts, signing agreements, accepting terms that bind the company |

The rule is **submission**, not navigation. Filling a wire form and showing the
user the filled state is fine and useful. Clicking the final confirm is theirs.

When you reach a gate: fill in everything you can, snapshot the page so the
user can see exactly what will happen, hand off, and state plainly what remains
to be clicked.

**Read-only mode.** For a session that should not write at all, the user can set
`EGO_BROWSER_DISABLE=1` to hard-stop the bridge, or ask for read-only work — in
which case navigate and extract, but submit nothing.

**No gate evasion, ever.** ego lite has no stealth, fingerprint-spoofing, or
captcha-solving machinery, and none should be added. When a site presents a
captcha, a 2FA prompt, or a step-up challenge, that is a handoff — not a puzzle
to route around. Do not read OTP codes out of the user's mail or messages to
feed a login. The human clears the challenge; you drive everything around it.

## Auditability

Every script forwarded to the Mac is appended to
`~/.local/state/ego-browser/audit.log` with a timestamp and the calling host.
Review recent activity with `ego-browser audit 10`. Given this browser can
reach banking and cloud-root surfaces, treat that log as a real control: do not
suppress or bypass it by ssh-ing to the Mac directly to run `ego-browser`.

## When it breaks

`ego-browser doctor` runs the whole path in stages and tells you exactly which
link is down: ssh reachability → macOS → CLI binary → app running → Node
runtime → live browser connection.

The common failure is simply that **the MacBook is asleep or off the tailnet**.
The bridge fails loudly on purpose. When it does:

- Retry with a wait if it's likely waking: `EGO_BROWSER_WAIT=120 ego-browser ...`
- **Do not silently fall back** to WebFetch, curl, Playwright, or headless
  Chrome for a task that needed the authenticated profile. Those tools cannot
  see the session and will produce a confidently wrong answer — a login wall
  rendered as "the page is empty". Report that the browser host is down and stop.

First-time setup and the launchd/GUI-session caveat are documented in
[`references/remote-architecture.md`](references/remote-architecture.md).

## Supersedes

This replaces the dormant `agent-browser` skill and any ad-hoc use of
Playwright, kapture, or headless Chrome for authenticated work. If a task only
needs a public page's text and no session, `WebFetch` is still the cheaper call.
