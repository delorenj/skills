# Application runtime

Keep the owner-native `op` command available even when Connect or a cache is disabled. Verify account, vault scope and reference path through the installed CLI, then choose only references the application is authorized to resolve. `op://` references are not credentials themselves, but names/paths may be sensitive metadata.

## Split nonsecrets from secrets

- `.env` contains **nonsecret literals only** (hostnames, noncredential feature flags). It can be local or committed according to the project policy. Never place a password-bearing URL, token or resolved dotenv there.
- `.env.op` contains `NAME=op://<owner-vault>/<item>/<field>` **references only**, with locally correct vault/item/field names; it may be committed when metadata disclosure is acceptable. See [`templates/env.op.example`](../templates/env.op.example) and [`templates/env.example`](../templates/env.example). Do not ship example placeholders as if live references.
- Execute consumer with `op run --env-file .env.op -- <consumer>`. For a name-only readiness check: `op run --env-file .env.op -- python3 <skill-dir>/scripts/check-env.py APP_SECRET`, replacing `APP_SECRET` with required names. The checker rejects missing/blank values and strings containing unresolved `op://` references, without echoing values. This is a structural check, not proof the correct secret was fetched: validate exact disposable-value equality in an owner-private in-memory test during bootstrap.
- Keep stdout/stderr masking enabled (`--no-masking` and `OP_RUN_NO_MASKING` must not be set). Do not use `env`, `printenv`, debug trace, `eval "$(op ...)"`, shell startup exports, process argument secrets, or `docker compose config` if it can expand resolved secrets. Injected child processes can still leak their environment through logs/crash dumps; isolate and minimize scope. Never write resolved dotenv output to disk.
- For Compose consumers, check which side of `docker compose` needs expansion and ensure the environment is injected only into that process: `op run --env-file .env.op -- docker compose up -d` after inspecting Compose variable mapping. Do not assume `env_file: .env.op` in Compose resolves `op://` references (it does not). Use service-specific scopes rather than global tokens.

## Auth boundary

Connect CLI supports `read`, `inject`, `run` and `item get --format json` per official documentation. It is not a substitute for administrator commands or `op item edit`. A scoped Connect token and accessible API do not prove write capability. Desktop integration needs a signed-in interactive session; unattended consumers need a proven independently bootstrapped identity. Avoid making Connect's own token available only through itself. If wrapper/cache integration is not Mac-verified, use native CLI with owner auth and mark acceleration deferred.
