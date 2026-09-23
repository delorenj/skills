# Verified surfaces

Every claim here was probed live on **2026-09-20** against `https://plane.delo.sh`
(makeplane preview 2026-07-17) and the Mac bridge. Re-run before trusting it — this file
will go stale, and a stale surface map is worse than none.

## Plane REST — what exists and what does not

```
/api/v1/workspaces/                        404   ← v1 has no workspace list
/api/v1/workspaces/33god/members/          200   ✓ list members
/api/v1/workspaces/33god/invitations/      200   ✓ invite (and read pending)
/api/v1/users/me/                          200   ✓ identity of the calling key
/api/v1/api-tokens/                        404   ✗ no REST token mint
/api/workspaces/33god/api-tokens/          404   ✗ not on the app surface either
/god-mode/                                 200   (instance admin UI, session auth)
```

Auth header is `X-API-Key: <key>` — **not** `Authorization: Bearer`.

**The 404 on `api-tokens` is the entire reason this skill needs a browser.** Plane's token
surface is session-authenticated and mints only for the caller, so there is no key-based path
to "create a token for user X". Signing in as the agent is the only way.

## Instance configuration — why self-signup works

`GET /api/instances/` returns:

```json
"enable_signup": true,
"is_email_password_enabled": true,
"is_magic_login_enabled": false,
"whitelist_emails": null
```

So an agent can register itself with email + password. **No invitation email is needed**, which
matters because this instance's mail backend is the console backend — invitation mail is never
actually delivered. Do not build a flow that waits for an email.

## Signup form shape

`https://plane.delo.sh/` is a two-stage form.

Stage 1 — `input[name=email]` + a `Continue` submit.
Stage 2 — branches on whether the address is known:

| address | heading | inputs |
|---|---|---|
| unknown | "Create your Plane account" | `csrfmiddlewaretoken` (hidden), `email` (hidden), `email`, `password`, `confirm_password` |
| known | "Welcome back to Plane" | password |

That branch is the account-exists check — it needs no API call.

### The one thing that will waste your afternoon

Plane's inputs are **React-controlled**. `input.value = x` updates the DOM and leaves React's
internal state empty, so the form submits blank with no error. Use the native setter:

```js
const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
s.call(input, value);
input.dispatchEvent(new Event('input', { bubbles: true }));
```

## Existing membership — proof the pattern already worked

`/api/v1/workspaces/33god/members/` returned 8 members, six of them `@delo.sh` with
`accepted: true` invitations dating to 2026-02-17: `tonny`, `rar`, `rererere`, `lenoon`,
`grolf`, `cack`. Roles are `15` (member) and `20` (admin). So email → invite → member is not
theoretical here; it has been done before under an older naming scheme.

## ego-browser audit log

`audit()` in `skillex/all-skills/ego-browser/scripts/ego-browser` appends the **forwarded
script verbatim** to `~/.local/state/ego-browser/audit.log`. It records the script, not its
output — so a token returned via `cliLog` is not persisted, but a password embedded in the
heredoc would be, permanently, in plaintext.

`EGO_BROWSER_REDACT` (added 2026-09-20) takes newline-separated literal secrets and masks any
that appear in the script before it is logged. Set it around every call that carries a
credential. `op` is **not** installed on the Mac, so the secret genuinely has to cross.
