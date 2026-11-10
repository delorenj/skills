# Interim per-host secret store (hosts without a 1Password service account)

Some DeLoNET-adjacent hosts (peer machines, e.g. a collaborator's Mac) must
resolve `op://` references but must **never** hold a DeLoSecrets service
token. For those, `scripts/env-op-resolve.py` replaces `op run` against a
per-host plaintext store.

## Layout on the host

| Path | Mode | Contents |
|---|---|---|
| `~/.config/33god/secrets.env` | 0600, created under `umask 077`, outside any repo | `KEY=value` lines (quoting like dotenv; comments allowed) |
| `~/.config/33god/refmap.tsv` | 0644 | `op://Vault/Item/Field<TAB>DERIVED_KEY` — refs and key names only, **no values** |

Store keys are **derived deterministically** from the ref
(`env-op-resolve key 'op://DeLoSecrets/Some Item/credential'` →
`OP_DELOSECRETS_SOME_ITEM_CREDENTIAL`). The resolver refuses to run if
refmap.tsv disagrees with the derivation, lists a ref twice, maps two refs to
one key, or a `.env.op` uses a ref the refmap doesn't list. Values are never
logged.

## Usage

```sh
# render .env.op -> .env (atomic, 0600); respects ./.env.op by default
env-op-resolve render .env.op .env

# inject resolved vars and run (file values override inherited env)
env-op-resolve exec --env-file .env.op -- docker compose up -d
```

Repos keep their committed `.env.op` files byte-identical on both kinds of
host. Verify the repo's own `.gitignore` covers `.env` before rendering
(per-repo check, never assumed).

## Migration caveat (written down 2026-11-10, mirror plan W0-5)

Existing `op://DeLoSecrets/...` refs cannot be presumed resolvable in the
peer's eventual 1Password account. Moving the peer off the interim store
means either (a) recreating matching items in a vault the peer's own account
can read, keeping refs identical, or (b) a permanent resolver mapping from
DeLoSecrets refs to the peer's vault refs. Until then the refmap.tsv on the
host **is** that mapping — keep it under version-free, plaintext-safe hygiene
(refs and key names only) and update it whenever a secret is added.
