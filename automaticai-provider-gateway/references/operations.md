# Gateway operations

Run from `~/docker/stacks/ai/newapi`. Read local `AGENTS.md` first. Keep credential
references in `.env.op`; use `op run --env-file=.env.op -- ...` when a command
needs that environment. Do not materialize a plaintext `.env` or a resolved key.
The operations scripts own their management/vault access; inspect their current
`--help` before adapting an invocation.

## Dedicated account connection

```sh
python3 ops/oauth-connections.py begin claude-personal
python3 ops/oauth-connections.py finish claude-personal
python3 ops/oauth-connections.py begin claude-intelliforia
python3 ops/oauth-connections.py finish claude-intelliforia
python3 ops/oauth-connections.py begin openai-personal
python3 ops/oauth-connections.py finish openai-personal
python3 ops/oauth-connections.py status all
```

Choose `jaradd@gmail.com` and the intended personal or tri-devs organization.
Use the private terminal prompt for Claude's authorization code/state. Never
paste those values into arguments, chat, issue bodies or log files. OpenAI uses
device sign-in; a local callback server is unnecessary. Pending authorizations
expire after 15 minutes, so begin afresh when resuming an expired flow.

OpenAI Advanced Account Security can require a phone/security-key passkey.
A stored TOTP does not prove that this login offers a TOTP path. Human passkey
verification is a real blocker; do not select account recovery, disable account
protection, reuse a different grant or change providers to avoid it. The observed
recovery flow had a 48-hour wait and was not submitted.

Before enabling an account, verify gateway refresh ownership, the fixed account
identifier, expected email/organization, `identity_verified`, expiry and absence
of an incomplete refresh. NewAPI channels receive access tokens only.

### Refresh ownership and rotation

```sh
python3 ops/oauth-connections.py renew all --dry-run
python3 ops/oauth-connections.py renew claude-personal --force
python3 ops/oauth-connections.py status claude-personal
```

The gateway owns **new dedicated grants**. Interactive Claude/Codex profiles
keep their grants; do not copy their refresh tokens into this owner. Legacy
`sync-claude-token.py` can follow its existing CLI-owned access token but must
never perform a refresh grant.

Renewal saves a durable `refresh_pending` intention before a rotating refresh,
persists and reads back the new session before channel synchronization, and
repairs access-token synchronization on a later run. A crash after an ambiguous
refresh must trigger reconnect through `begin`/`finish`, not blind reuse of the
old refresh token. Preserve unrelated accounts while repairing one grant.

Unit sources live in `ops/systemd/`. Install the matching OAuth service/timer
into `~/.config/systemd/user`, reload the user manager and enable
`newapi-oauth-connections.timer`. It runs every five minutes and renews with
30 minutes remaining. Vault access is supplied to the manager in process
environment, not a plaintext credential file.

Prove renewal with the account's interactive CLI stopped: force renewal, inspect
safe status, make an authenticated request and inspect the oneshot result.
After reboot, verify manager vault access and run the oneshot explicitly. Timer
enabled state alone proves neither successful refresh nor all-account health.

## Scoped consumer tokens

```sh
python3 ops/gateway-tokens.py mint <consumer-name> --models <canonical-route> --dry-run
python3 ops/gateway-tokens.py mint <consumer-name> --models <canonical-route>
python3 ops/gateway-tokens.py status <consumer-name>
python3 ops/gateway-tokens.py rotate <consumer-name>
python3 ops/gateway-tokens.py revoke <consumer-name>
```

Replace angle-bracket placeholders; they are not executable examples. Use a
stable name for the real service/profile, and include helper-model routes in its
scope. `--models all` scopes to today's catalog, so future additions require
updating or rotating that scope. Default expiry is 90 days; `--days -1` is an
explicit non-expiring choice.

Tokens belong to enabled role-1 `delo-relay`, group `aai-personal`. Credentials
are saved and read back in `op://DeLoSecrets/AutomaticAI Gateway Tokens/<name>`;
commands print only the reference. Rotation stores the replacement before
deleting old tokens. A shared `tokens-vault` lock serializes all consumer-token
mutations so different consumers cannot overwrite the shared vault item.
On lock contention, wait for the existing operation and retry; never bypass it.

Inject the reference through an owning launcher or `op run`. Remove direct
provider credential precedence from the agent inference path, but keep those
upstream references available to their gateway control-plane owner. Never print
process environments or use shell tracing while handling credentials.

## Managed route reconciliation

```sh
python3 ops/reconcile-routes.py --dry-run
python3 ops/reconcile-routes.py --apply
python3 ops/reconcile-routes.py --dry-run
```

Dry-run is the default. The reconciler preflights credentials, channel ownership
and pricing before writes, preserves legacy groups/models/settings, and disables
only the disconnected account's managed channels. Inspect all proposed changes,
then read channel and option state back through the management API/database.

NewAPI channel creation nests `channel` under `mode=single`, uses `status=1`,
and comma-separated `models`/`group`. Channel update is a flat full-body PUT:
preserve fields such as `advanced_custom`, omit `status`, and use the dedicated
status endpoint. A 200 transport response can contain `success=false`; check
both. API scripts require an explicit recognizable User-Agent for Cloudflare.

Pricing updates replace complete maps, so merge against the current state.
Model pricing and channel model lists are separate reconciliation concerns.
The rc.40 cache-write option is `CreateCacheRatio`; do not invent similarly
named ratio options. Route ownership checks and alias-to-native mappings must
remain active on cache hits, affinity, pinned channels and retries.

Do not use `ops/provision-client.py` to inspect state: it has no dry-run and can
write live options before all preconditions pass. Use the scoped gateway scripts
and read-only management queries instead.

## Build and deploy relay changes

Deployment source is the Docker repo. Overlay owners include `brand/gateway.patch`,
`brand/gateway/`, `brand/apply-gateway.py`, `brand/build.sh` and `ops/routes.json`.
The build archives an exact upstream tag, applies checked-in overlays and checks
literal patch anchors. Changes in the pristine `~/code/newapi` worktree do not
enter that image.

```sh
python3 -B -m unittest discover -s ops -p 'test_gateway_ops.py'
./brand/build.sh v1.0.0-rc.40
op run --env-file=.env.op -- docker compose config --quiet
op run --env-file=.env.op -- docker compose up -d --no-deps --force-recreate new-api
```

`v1.0.0-rc.40` is the pinned baseline at skill creation. For an upgrade, inspect
current source and deliberately match the exact tag in both build and Compose.
The stack has no Compose `build:` section; `up --build` does not rebuild it.
The branded image is local with a mutable tag, so verify the installed image ID
after recreation. Recreate only the changed service; never use `down -v`.

Run affected Go tests in an exported, patched upstream tree, preserving the
pristine checkout. Relevant packages include `automaticai`, `middleware`,
`relay/channel/advancedcustom`, `controller`, `model`, `router`, `service`, and
the independent `relaykit/dto` / `relaykit/relayconvert/...` module. Python
syntax checks must leave no cache in the source tree. Run the documented
contrast check and supported CLI help/dry-run paths for affected changes.

A push to Docker main can invoke a broad Portainer webhook; it is not deployment
proof. Verify the actual image, health, authenticated relay and ledger after
the scoped recreation. Runtime reports, caches, databases, logs and backups do
not belong in Git.
