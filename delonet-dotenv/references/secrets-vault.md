---
pipeline-status:
  - new
---
# Secrets vault (.env.op + op CLI)

How secrets actually get into the running container.

## The model

```
.env.op           ←  committable: contains op:// references and comments
.env              ←  gitignored: contains non-secret literals (URLs, ports, brand strings, flags)
DeLoSecrets vault ←  source of truth for every secret value
                     resolved at run time by `op run`, never persisted to disk
```

`op run --env-file .env.op -- <cmd>` does this:
1. Parses `.env.op`.
2. Resolves every `op://...` reference against the signed-in 1Password account.
3. Exports resolved values as env vars in `<cmd>`'s process and that process's children only.
4. Never writes the resolved values to disk.

This is why `.env.op` is safe to commit — it leaks no secrets, only addresses.

## File header (start every .env.op with this)

```bash
# 1password reference file. Safe to commit.
# `op run --env-file .env.op -- <cmd>`
# Resolves at invocation time and exports to the child process only.
#
# Path convention: op://<vault>/<item>/<field>.
```

## Reference syntax

```
KEY=op://DeLoSecrets/<ItemName>/<fieldName>
```

- Vault is always `DeLoSecrets` for personal infra.
- `<ItemName>` is the literal item title in 1Password (case-sensitive, spaces and parens allowed).
- `<fieldName>` is the literal field name (`username`, `password`, `credential`, `api_token`, etc.).
- Inspect actual field names: `op item get "<Item>" --vault DeLoSecrets --format json | jq '.fields[] | {label,id}'`.

## Lookup workflow

Before assuming an item or field exists:

```bash
# 1. List items matching a keyword
op item list --vault DeLoSecrets | grep -i <keyword>

# 2. Inspect an item's fields
op item get "<Item Name>" --vault DeLoSecrets

# 3. Test a single reference resolves to non-empty
op read "op://DeLoSecrets/<Item>/<field>"
```

If `op read` returns empty, the item or field doesn't exist or the field is empty. Fix the vault, not the reference.

## Creating a new item

For generated secrets (NEXTAUTH_SECRET, CRON_API_KEY, encryption keys):

```bash
SECRET=$(openssl rand -base64 32)
op item create \
  --vault DeLoSecrets \
  --category 'API Credential' \
  --title '<Service> NEXTAUTH_SECRET' \
  credential="$SECRET"

# Then reference it:
# NEXTAUTH_SECRET=op://DeLoSecrets/<Service> NEXTAUTH_SECRET/credential
```

For multi-field secrets (OAuth client_id + client_secret):

```bash
op item create \
  --vault DeLoSecrets \
  --category 'API Credential' \
  --title '<Service> Google OAuth' \
  client_id='...' \
  client_secret='...'
```

Keep titles unique and discoverable. Pattern: `<Service> <Purpose>`.

## Writing the .env / .env.op pair

Walk the upstream `.env.example` top-to-bottom. For each var:

| Looks like… | Where it goes |
|---|---|
| URL, port, hostname, boolean flag, brand string, log level | `.env` (literal value) |
| Anything ending in `_KEY`, `_SECRET`, `_TOKEN`, `_PASSWORD`, `_DSN`, `_CREDENTIALS` | `.env.op` (op reference) |
| `DATABASE_URL` (contains password) | `.env.op` (full URL string with op ref interpolation isn't supported — embed the password directly into the op item or use shell expansion at run time; see below) |
| OAuth `*_CLIENT_ID` (technically public but treated as secret) | `.env.op` |
| Webhook secrets, encryption keys | `.env.op` |
| `NEXT_PUBLIC_*` non-secret tracking IDs (PostHog, Sentry DSN) | `.env` (these run in the browser anyway) |
| `NEXT_PUBLIC_*` site keys (Turnstile, Stripe publishable) | `.env.op` (uniformity > technicality) |

### DATABASE_URL gotcha (verified 2026-05)

`op run` does NOT do mid-string substitution of `op://` references in `.env` files. The reference must occupy the entire RHS:

```
# WORKS — whole RHS is a single op reference
DATABASE_URL=op://DeLoSecrets/<Service>/DATABASE_URL

# DOES NOT WORK — mid-string refs pass through as literal text
DATABASE_URL=postgresql://op://DeLoSecrets/<Service>/user:op://DeLoSecrets/<Service>/pass@host/db
```

So: store the FULL connection URL as a single field in op, then reference that one field. When you create the op item, include a `DATABASE_URL` field with the assembled URL using internal hostnames (`@database:5432/calendso`, etc.).

If you absolutely need template substitution into a file, use `op inject -i template -o resolved` instead — `op inject` does support inline `{{ op://... }}` substitution into arbitrary text. But `op run` for env-file mode is line-based, not template-based.

## Loading at runtime

For docker compose:

```bash
op run --env-file .env.op -- docker compose --env-file .env up -d
```

Or wrap it as a project script — most of the active stacks have a `mise run up` task that does this.

For a one-off command:

```bash
op run --env-file .env.op -- node scripts/seed.ts
```

For a long-running shell session (rare, secrets exposed to entire shell history):

```bash
eval $(op run --env-file .env.op -- env | grep -E '^[A-Z_]+=' | sed 's/^/export /')
```

Avoid that pattern when possible — it defeats the "child process only" property.

## Shell secrets fallback

`~/.config/zshyzsh/secrets.zsh` (= `$ZC/secrets.zsh`) auto-exports a handful of legacy vars to every interactive shell:

```
$DEFAULT_USERNAME, $DEFAULT_PASSWORD, $RESEND_API_KEY,
$MINIO_ACCESS_KEY, $MINIO_SECRET_KEY, ...
```

These work for shell-invoked scripts but NOT inside containers (Docker doesn't inherit your shell env automatically). Prefer op references in `.env.op` so docker compose actually receives them.

When you find a stack relying on `$VAR` style values in `.env`, migrate to op:

1. Find the corresponding op item (or create one).
2. Replace `MY_KEY=$RESEND_API_KEY` in `.env` with `MY_KEY=op://DeLoSecrets/Resend API Key/credential` in `.env.op`.
3. Blank the `.env` line.
4. Test: `op run --env-file .env.op -- printenv MY_KEY`.

## Verification recipe

Before `docker compose up`:

```bash
# Resolve all op references and assert they're non-empty
op run --env-file .env.op -- env | grep -E '^[A-Z_]+=' | awk -F= 'NF<2 || $2=="" {print "EMPTY: " $1}'

# Should print nothing. Anything printed = unresolved or empty in vault.
```
