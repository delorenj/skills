# Environment Integration

How mise tasks interact with `[env]` section configuration.

## Automatic Inheritance

Tasks automatically inherit `[env]` values:

```toml
[env]
DATABASE_URL = "postgresql://localhost/mydb"
_.file = ".env"  # Load additional env vars

[tasks.migrate]
run = "diesel migration run"  # $DATABASE_URL available
```

## Credential Loading Pattern

```toml
[env]
_.file = { path = ".env.secrets", redact = true }

[tasks._check-env]
hide = true
run = '[ -n "$API_KEY" ] || { echo "Missing API_KEY"; exit 1; }'

[tasks.deploy]
depends = ["_check-env"]
run = "deploy.sh"
```

## Cross-Reference: mise-configuration

**Prerequisites**: Before defining tasks, ensure `[env]` section is configured.

> **PRESCRIPTIVE**: After defining tasks, invoke **[`mise-configuration` skill](../../mise-configuration/SKILL.md)** to ensure [env] SSoT patterns are applied.

The `mise-configuration` skill covers:

- `[env]` - Environment variables with defaults
- `[settings]` - mise behavior configuration
- `[tools]` - Version pinning
- Special directives: `_.file`, `_.path`, `_.python.venv`
