# Secret Injection (1Password + op inject)

Pattern for resolving secrets from 1Password at deploy time so no plaintext
secret ever lives in the stacks repo. Secrets rotate by editing the
1Password item and redeploying — never by touching the repo.

## Invariants

- **Stacks `.env` is gitignored**. Always. Never commit a resolved secret.
- **`.env.template` is committed** alongside the stack's `compose.yml`.
- **All secret values are `op://VAULT/ITEM/FIELD` references** in the template.
- **Non-secret values stay plaintext** (URLs, hostnames, ports, feature flags).
- **Resolution happens via `~/docker/stacks/_lib/op-inject.sh`**, never per-stack reimplementation.

## Layout

```
~/docker/stacks/
├── _lib/
│   └── op-inject.sh         # shared resolver (chmod +x)
└── <category>/<service>/
    ├── compose.yml
    ├── .env.template        # committed; op:// references
    └── .env                 # gitignored; generated at deploy time
```

## The resolver

`~/docker/stacks/_lib/op-inject.sh`:

```bash
#!/usr/bin/env bash
# Resolve op:// references in a template into a .env file.
# Defaults to cwd's .env.template -> .env.
# Override with: op-inject.sh <template> <output>

set -euo pipefail
TEMPLATE="${1:-.env.template}"
OUTPUT="${2:-.env}"

command -v op >/dev/null || { echo "op CLI missing" >&2; exit 1; }
[[ -f "$TEMPLATE" ]] || { echo "template not found: $TEMPLATE" >&2; exit 1; }

TMP=$(mktemp "${OUTPUT}.XXXXXX")
trap 'rm -f "$TMP"' EXIT
op inject -f -i "$TEMPLATE" -o "$TMP" >/dev/null
chmod 600 "$TMP"
mv "$TMP" "$OUTPUT"
trap - EXIT

ref_count=$(grep -cE '\{\{ *op://' "$TEMPLATE" || true)
echo "op-inject: resolved $ref_count secret(s) from 1Password -> $OUTPUT"
```

Behavior:
- Writes to a temp file first; a partial inject doesn't leave a half-written .env.
- `chmod 600` because the resolved file contains real secrets.
- Concise stdout line for both humans and CI logs.
- Exit non-zero on any failure (missing op CLI, missing template, 1Password
  auth expired) so deploy pipelines fail loudly.

## Template syntax

```env
# Plaintext (commit-safe)
DB_HOST=scout-db
DB_PORT=5432
RUNTIME_ENV=stg

# Secret (op:// reference)
OPENAI_API_KEY={{ op://DeLoSecrets/Scout/OPENAI_API_KEY }}
SLACK_BOT_TOKEN={{ op://DeLoSecrets/Scout/botToken }}
```

Field names on the 1Password side don't need to match env-var names — the
`op://...` path is what binds them. Prefer matching names when adding NEW
fields; keep existing names when adopting fields already created elsewhere.

## Per-stack mise task (optional but recommended)

When the stack has a source repo with `mise.toml`, wire an `inject` task that
calls the shared script:

```toml
[tasks.inject]
description = "Resolve secrets from 1Password into ~/docker/stacks/<category>/<service>/.env"
run = """
cd ~/docker/stacks/<category>/<service>
~/docker/stacks/_lib/op-inject.sh
"""

[tasks.deploy]
description = "Re-inject secrets, pull latest image, restart stack"
depends = ["inject"]
run = """
cd ~/docker/stacks/<category>/<service>
docker compose pull <service>
docker compose up -d <service>
"""

[tasks.ship]
description = "Build, push, inject, deploy"
depends = ["push", "inject"]
run = """
cd ~/docker/stacks/<category>/<service>
docker compose pull <service>
docker compose up -d <service>
"""
```

For stacks without a source repo, drop a thin local `mise.toml` in the stack
dir, or invoke `~/docker/stacks/_lib/op-inject.sh` directly.

## Migration recipe (existing stack → 1Password)

For each existing `~/docker/stacks/<category>/<service>/.env`:

1. Identify which values are secrets (API keys, passwords, tokens) vs config
   (URLs, hostnames, ports). Only secrets get `op://` references.
2. Find or create a 1Password item in `DeLoSecrets` matching the service name.
3. Push secrets into the item with `op item edit`:
   ```bash
   op item edit "<Service>" --vault DeLoSecrets \
     "OPENAI_API_KEY[password]=$(grep ^OPENAI_API_KEY= .env | cut -d= -f2-)" \
     ...
   ```
4. Write `.env.template`: plaintext for config, `{{ op://... }}` for secrets.
5. Run `~/docker/stacks/_lib/op-inject.sh` and diff against the existing
   `.env` to confirm parity before swapping.
6. Replace `.env` with the resolved output. Confirm the stack still boots.
7. Verify `.env` is gitignored at the stacks repo root.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `op-inject: 1Password CLI ('op') not on PATH` | `op` not installed | Install 1Password CLI; ensure mise/PATH includes it |
| `op-inject: template not found` | Wrong cwd or missing file | cd into stack dir or pass explicit path |
| `[ERROR] You are not currently signed in.` | Session expired | `op signin` (interactive) or set `OP_SERVICE_ACCOUNT_TOKEN` for CI |
| Resolved values look like literal `op://...` strings | Template uses single braces or wrong syntax | Must be `{{ op://... }}` with double braces and spaces around the URL |
| `op-inject` succeeds but container still uses old secrets | Container env was set at start; needs restart | `docker compose up -d <service>` to recreate with new env |

## CI / service-account note

For unattended deploys (CI, scheduled runs, fresh machines), set
`OP_SERVICE_ACCOUNT_TOKEN` in the environment. `op inject` honors it without
an interactive signin. Scope the service account to only the items it needs
to read.

## Reference implementation

`~/docker/stacks/ai/scout/` — first stack migrated. See its `.env.template`
for the canonical example and `~/code/scout/mise.toml` for the wired mise
task graph.
