# Signing in once, then reusing the token

FlowAgent (and therefore `pa`) holds no credentials of its own. It uses two sign-ins, and both
are cached on disk so agents reuse them without a human.

| Path | Used for | Token source | Cache |
| --- | --- | --- | --- |
| Azure CLI | flows, runs, environments, Dataverse, Graph, API Hub (almost everything) | `az account get-access-token --resource <api>` | `~/.azure/msal_token_cache.json` (plain JSON, mode 600, on Linux) plus FlowAgent's copy in `~/.cache/flowagent/tokens/` |
| Connectivity | connection management on `api.powerplatform.com`: `pick_or_create_connection`, `fix_connection`, `list_connections` where the environment has no Dataverse, connection creation | MSAL public client `9cee029c-6210-4654-90bb-17e6e9d36617` (the Power Platform CLI client) | `~/.cache/flowagent/msal-cache/<tenantId>.json` |

## The one human step (passkey accounts)

Accounts that sign in with a passkey ("Face, fingerprint, PIN or security key") cannot be signed
in by an agent, and a browser on a headless box cannot show the passkey prompt. The device-code
flow moves the passkey step to any device the human holds.

1. Run (an agent may run it in a background shell and relay the printed code):

   ```bash
   pa login                      # = az login --use-device-code --tenant $PA_TENANT_ID --allow-no-subscriptions
   ```

   It prints: *To sign in, use a web browser to open the page https://microsoft.com/devicelogin
   and enter the code XXXXXXXXX*. The code expires after about 15 minutes.
2. The human opens that page on a phone or laptop, enters the code, picks the work account and
   approves with the passkey. The command returns and prints the signed-in user and tenant.
3. Only if the work needs connection management (creating or repairing a Teams or Outlook
   connection, for example), seed the second sign-in the same way:

   ```bash
   pa login --connectivity       # device code for the Connectivity client, written to FlowAgent's MSAL cache
   ```

   Without it, the first connection-management call opens a browser on the machine running the
   engine (useless on a headless box, and it stops at the passkey prompt). `pa login
   --connectivity` writes the cache in MSAL's shared format with `uv run --with msal`; confirm it
   took with `pa call list_accounts` (the account should appear as the effective identity).
4. Verify: `pa doctor` (prints the signed-in user, tenant and token expiry, never a token), then
   `pa envs`.

Never type a password or approve a passkey on the human's behalf, and never ask for one.

## How long it lasts

- Access tokens live 60 to 90 minutes and are refreshed silently from the refresh token on the
  next call.
- Refresh tokens for these public clients expire after 90 days of NON-use and roll forward on
  every use. Any agent call at least once every 90 days keeps the sign-in alive indefinitely.
- It ends early when: the password or passkey is reset, an admin revokes sessions, a Conditional
  Access sign-in-frequency policy applies, the account is disabled, or someone runs `az logout`
  or FlowAgent's `reconnect`. The symptom is `not-logged-in` or `AADSTS700082` /
  `AADSTS50173`; repeat the one human step.
- Every CLI on the machine shares `~/.azure`, so one sign-in serves every agent. Set
  `AZURE_CONFIG_DIR` to isolate an identity.

## When device code is refused

Some tenants block the device-code flow with Conditional Access (`AADSTS53003`, or a message
that the authentication flow is blocked). Then sign in where a browser can show the passkey
prompt, on the human's own laptop: `az login --tenant <tenant> --allow-no-subscriptions`. On
macOS and Linux the Azure CLI token cache is plain JSON, so `~/.azure/msal_token_cache.json` and
`~/.azure/azureProfile.json` can be copied to the agent machine (`scp`, mode 600). On Windows
the cache is DPAPI-encrypted and does not travel. Treat those files as credentials: never commit
them, never paste them anywhere.

## Tenant and environment

`pa` reads non-secret defaults from `~/.config/power-automate/profile.env` (override the path
with `PA_PROFILE`). Recognised keys: `PA_TENANT_ID`, `PA_LOGIN_HINT`, `PA_DEFAULT_ENVIRONMENT`,
`PA_CLOUD`, `PA_CLIENT_ID`, `FLOWAGENT_MCP`, `PA_ENGINE_REF`. Values already in the environment
win. Never put a secret in it.

- Flows built in the **Teams Workflows app** live in the tenant's **default environment**,
  whose id is `Default-<tenantId>`. `pa` uses that as the default environment when
  `PA_TENANT_ID` is set and `PA_DEFAULT_ENVIRONMENT` is not.
- Flows made at make.powerautomate.com can land in another environment when the tenant turned
  on environment routing: `pa call resolve_environment` says where, `pa envs` lists them all.
- `InvalidEnvironmentId` or `ENOTFOUND *.environment.api.powerplatform.com` almost always means
  a display name or bare tenant GUID was passed instead of the environment id.

## Identity troubleshooting

`pa call whoami` shows the active Azure CLI account, the token's tenant and the Connectivity
identity. `pa call doctor` runs FlowAgent's full checklist. `pa call reconnect` clears both
caches (it does not sign anyone in). `switch_account` changes only the Connectivity preference,
never the Azure CLI account.
