---
name: plane-identity-provisioning
description: Give a Hermes agent its own real identity — an <agent>@delo.sh address, its own Plane
  user account, workspace membership, and its own Plane API token — fully automated, no manual step.
  Use when an agent needs to act as itself on a board instead of borrowing the one shared key, when
  `flume iam provision` reports a missing identity, or when rotating an agent's Plane token. The
  token mint runs through ego-browser against the authenticated Mac profile because Plane's
  API-token surface is session-authenticated and has no REST endpoint. Do NOT use for human
  teammates, for non-Plane ticket providers, or to hand an agent the shared workspace key.
metadata:
  pipeline-status: new
---

# Plane identity provisioning

Every agent on this fleet writes to Plane with **one shared workspace key**
(`PLANE_33GOD_API_KEY`, read from `~/.hermes/fleet.env` by 40-plane.sh). That means no
per-agent attribution, and no way to revoke one agent without revoking all 25.

This skill closes that. It gives an agent a real Plane user, and that user its own token.

## Why a browser is required for exactly one step

Plane self-hosted exposes members and invitations on the `/api/v1/` REST surface, but **not
API tokens** — those live behind session auth and only ever mint a token for the caller.
Verified on this instance:

```
/api/v1/workspaces/33god/members/       200    ✓ list / add
/api/v1/workspaces/33god/invitations/   200    ✓ invite
/api/v1/api-tokens/                     404    ✗ no REST mint
```

So step 5 signs in **as the agent** and mints the token through the UI. Everything else is
plain HTTP. See [`references/verified-surfaces.md`](references/verified-surfaces.md) for the
probes behind every claim here — re-run them before trusting this file, it will go stale.

## Preconditions

```bash
ego-browser doctor        # all 6 checks must pass; this is the Mac bridge
op read "op://DeLoSecrets/Plane/Main/apiKey" >/dev/null   # 1Password must not be rate-limited
```

If `op` reports *"Too many requests"*, **stop**. A rate-limited vault makes every step fail in a
way that reads like a bad credential — see `feedback_op_ratelimit_fakes_bad_token`. Wait it out.

## The seven steps

`scripts/provision-plane-identity.sh <agent-id>` runs all of them, idempotently. Each step
checks for its own prior result first, so a re-run after a failure resumes rather than duplicates.

| # | step | mechanism | idempotency check |
|---|---|---|---|
| 1 | `<agent>@delo.sh` email routing | Cloudflare API | existing rule with that `to` matcher |
| 2 | generate password | `openssl rand` | existing `op` item field |
| 3 | create the Plane account | **ego-browser** | sign-in succeeds ⇒ account exists |
| 4 | add to the `33god` workspace | Plane REST | already in `members/` |
| 5 | mint the API token | **ego-browser** | existing token named `hermes:<agent>` |
| 6 | store password + token | 1Password | field already set |
| 7 | write the registry row | `flume iam` | `plane.key_ref` already present |

### Never do these

- **Never write the token or password into a file.** Both go to `op://DeLoSecrets/Plane Agent
  <agent-id>/{password,apiKey}`; the registry gets the `op://` *reference*, never the value.
- **Never `cliLog` a secret.** ego-browser's audit log at `~/.local/state/ego-browser/audit.log`
  is plaintext and permanent. Read the token into a variable and write it straight to `op`.
- **Never reuse one password across agents.** One compromised agent must not be all of them.

## The browser steps, concretely

The signup form is a two-stage flow on `https://plane.delo.sh/`. Stage one is a single
`input[name=email]` plus a `Continue` submit. Entering an **unknown** address switches the page
to *"Create your Plane account"*, which carries `csrfmiddlewaretoken`, a hidden `email`, a
visible `email`, `password`, `confirm_password`, and a `Create account` button.

```js
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('plane-iam-<agent>');
await gotoAndWait('https://plane.delo.sh/');
// React controls these inputs — a plain .value assignment is silently discarded.
// Use the native setter so React's onChange actually fires.
await js(`(()=>{const i=document.querySelector('input[name=email]');
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(i, EMAIL); i.dispatchEvent(new Event('input',{bubbles:true}));})()`);
EOF
```

That native-setter detail is not optional and is the single thing most likely to waste an hour:
Plane's inputs are React-controlled, so `input.value = x` updates the DOM and leaves React's
state empty, and the form submits blank.

Each heredoc is a **fresh runtime with no state**, so every round must re-attach with
`useOrCreateTaskSpace(name)`. Close with `completeTaskSpace(name, { keep: false })`.

## Verifying a provision

```bash
flume record <agent-id> | grep -A4 plane      # key_ref + member_id present
op read "op://DeLoSecrets/Plane Agent <agent-id>/apiKey" >/dev/null && echo stored
curl -s -H "X-API-Key: $(op read 'op://DeLoSecrets/Plane Agent <agent-id>/apiKey')" \
     https://plane.delo.sh/api/v1/users/me/ | jq -r .email    # must be <agent>@delo.sh
```

That last call is the real gate: it proves the token authenticates **as the agent**, not as you.
