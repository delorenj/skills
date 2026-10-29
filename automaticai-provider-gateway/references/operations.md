# Gateway operations

Run from `~/code/client-portal/gateway`. `~/docker/stacks/ai/newapi` is only a
compatibility symlink, not a second source owner. Read local `AGENTS.md` first.
Keep credential references in `.env.op`; use `op run --env-file=.env.op -- ...`
when a command
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

Unit sources live in `ops/systemd/`. Install the matching OAuth `.service`
into `~/.config/systemd/user` and reload the user manager. The schedule is the
Candybar `newapi-oauth-connections` (every five minutes; see the `candybar`
skill). Its old `newapi-oauth-connections.timer` is retired: do not enable it. It
renews with 30 minutes remaining. Vault access is supplied to the manager in process
environment, not a plaintext credential file.

Prove renewal with the account's interactive CLI stopped: force renewal, inspect
safe status, make an authenticated request and inspect the oneshot result.
After reboot, verify manager vault access and run the oneshot explicitly. Candybar
registration or an enabled state alone proves neither successful refresh nor all-account health.

## Claude access-only setup tokens

Catalog routes with `credential_mode: "claude_setup_token"` use a raw OAuth
access credential, not an Anthropic API key or rotating JSON session. They have
no refresh token and are excluded from the gateway OAuth renewal owner. Preserve
an existing API key in its separate vault field; load the exact catalog reference
fresh and reconcile only the affected account after replacement. Do not invent
expiry/refresh metadata or send a setup token to the refresh endpoint.

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
scope. `--models all` scopes to today's catalog minus every Anthropic route
(Claude/Fable), so future additions require updating that scope; a consumer that
needs Claude adds `--anthropic`. `rotate` without `--models` keeps the consumer's
current scope; `scope` requires `--models`. Prefer `gateway-tokens.py scope <consumer> --models ...`
with its dry-run first for an allowlist-only change: it preserves the existing
key, expiry, group and restrictions. Rotation is not required merely to add
routes. Default expiry is 90 days; `--days -1` is an
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

Deployment source is `~/code/client-portal/gateway`. Overlay owners include
`brand/gateway.patch`, `brand/gateway/`, `brand/apply-gateway.py`,
`brand/prepare-source.sh`, `brand/build.sh` and `ops/routes.json`. `SOURCE.json`
pins the exact upstream commit. Preparation exports that commit and applies
checked-in overlays; neither the old Docker path nor edits in `~/code/newapi`
are an independent build source.

From the portal repository root:

```sh
pnpm gateway:check
IMAGE_TAG=<candidate-tag> pnpm gateway:build
pnpm gateway:compose config --quiet
```

After pinning the built candidate tag in `gateway/compose.yml`, recreate only
`new-api` with `pnpm gateway:compose up -d --no-deps --force-recreate new-api`.
Do not move the deployed tag or `:latest` during a candidate build. The canonical
Compose wrapper resolves secrets and keeps project `newapi`; Postgres uses the
existing external `newapi_pg_data` volume. Its absence must fail rather than
initialize a replacement database.

`gateway/TARGET` names the serving host: big-chungus (`home`) or the Lightsail
VM `aai-gateway` (`cloud`, Docker context `aai-cloud`, `ssh aai-gateway`). The
wrapper follows it, ships the locally built image to the VM and holds
`deploy.lock`; a bare `docker compose` fails by design. Inspect the VM with
`docker --context aai-cloud ...`, never `docker context use`. Scripts that exec
into Postgres resolve the daemon through `ops/gateway_target.py`. The VM,
backups, cutover and rollback are in `gateway/ops/CLOUD.md`; outage handling,
alerts and cost are summarized in [hosting](hosting.md).

`v1.0.0-rc.40` is the pinned baseline at skill creation. For an upgrade, inspect
current source and deliberately match the exact tag in both build and Compose.
The stack has no Compose `build:` section; `up --build` does not rebuild it.
The branded image is local with a mutable tag, so verify the installed image ID
after recreation. Recreate only the changed service; never use `down -v`.

Run affected Go tests in a fresh exported, patched upstream tree.
`relaykit` is a separate Go module: root `go test` cannot cover its converters.
For converter repairs, run its `go test ./relayconvert/... -run TestAutomaticAI`
and focused bridge tests, then vet/race as appropriate. `pnpm gateway:check` and
the image's `go build` do not run these Go regressions. Add fixtures through
`ConvertRequestByID` and the advancedcustom bridge. Relevant root packages
include `automaticai`, `middleware`, `relay/channel/advancedcustom`,
`relay/channel/claude`, `controller`, `model`, `router`, and `service`.

The broad relaykit suite had an existing Claude cache-control golden mismatch
on October 6, 2026. Establish the pre-change baseline and report unchanged drift;
do not regenerate snapshots just to hide it. Controller tests took about
195 seconds on this host, so use a suitable timeout rather than diagnosing a
120-second tool timeout as a test failure. For shell/Python edits, use syntax
checks that leave no cache in source and the affected CLI help path.

### Gateway patch format

Regenerate changed hunks against the exact pristine file pinned by `SOURCE.json`,
including existing overlay changes to that file. Do not append overlapping hunks
or hand-adjust line counts. Verify the complete patch through
`brand/prepare-source.sh` into an empty scratch directory before building;
additive Go files are copied after patching and must not overwrite upstream files.

Docker cache reuse is content-addressed. An unchanged frontend layer is expected
for a Go-only repair; inspect that changed Go source reaches `COPY . .` and the
`go build` layer reruns. Do not edit `build.sh` to disable caching without evidence
of a missing build input. Fresh source preparation, applied patch and exact image
ID are the useful controls, not blanket `--no-cache`.

### Claude model settings

Runtime Claude options live in the NewAPI options table and hot-reload:

Run from the canonical gateway directory:

```python
python3 -B - <<'PY'
import sys; sys.path.insert(0, 'ops')
from aai import Gateway
g = Gateway()
print(g.options().get('claude.default_max_tokens'))
print(g.options().get('claude.thinking_adapter_budget_tokens_percentage'))
PY
```

Runtime option snapshots age quickly: read `claude.default_max_tokens` and the
thinking-budget setting before interpreting a cap. On October 6, 2026 the map
was `{"default":32768,"claude-opus-5-5":65536,"claude-sonnet-5-5":65536}`.
These persist across restarts. Existing cache creation/read ledger evidence can
settle whether caching works without another expensive synthetic turn.

A portal push deploys neither the gateway nor the Worker; their release paths
are separate. A container recreation can briefly produce a Traefik edge 404 at
home, or a JSON 503 with `Retry-After` from Caddy on the VM.
Inspect current image/health and use bounded readiness retries before restarting
again or blaming an API endpoint. Deployed runtime and published source are
separate facts. Runtime reports, caches, databases, logs and backups stay out of
Git. Follow [bounded acceptance](acceptance.md#bound-the-verification), including
the user's stop instruction, rather than repeatedly certifying working traffic.
