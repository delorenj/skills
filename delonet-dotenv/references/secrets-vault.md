# Vault references and runtime resolution

Use `DeLoSecrets` as the credential owner. `.env.op` contains `op://` references;
`.env` may contain nonsecret literals only. Prefer item UUIDs when titles collide.
Inspect field labels and IDs without printing their values. Never put credentials
in shell arguments, logs, temporary files, or generated configuration files.

For new credentials, create the vault item through the CLI's stdin/structured
input support, keeping the value in process memory. Verify by reading back and
comparing in memory; output only success/failure. Inspect `op item create --help`
for the installed syntax. Do not invent field names or a nonexistent reference.

## Runtime use

```bash
op run --env-file .env.op -- docker compose --env-file .env up -d
op run --env-file .env.op -- node scripts/seed.ts
```

For a credential-bearing connection URL, store the complete URL in one vault
field and reference it. Use service hostnames. Never render a resolved template
to disk or export a dumped environment through `eval`.

## Verification

Run the skill's presence checker for the exact required names:

```bash
op run --env-file .env.op -- python3 <skill-dir>/scripts/check-env.py DATABASE_URL
```

It exits nonzero for missing, empty, or unresolved references and prints names
only. Do not use `printenv`, environment dumps, or full item output to verify a
secret. Verify the service behavior separately after startup.

## Legacy migration

An encountered plaintext value, including a legacy `secrets.zsh` entry, is a
migration source. Store it in the vault, replace the consumer with a reference,
remove the obsolete plaintext storage within scope, and verify the real consumer.
Do not copy legacy secrets into a new file as an intermediate step. Report the
migration without disclosing values; history rewriting is a separate operation.
