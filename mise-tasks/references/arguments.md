# mise Task Arguments

Complete reference for the `usage` specification in mise tasks.

## Overview

The `usage` field defines task arguments and flags using a specialized DSL. Arguments become environment variables accessible in the `run` script.

**DEPRECATION WARNING**: The Tera template method (`{{arg(name="...")}}`) will be removed in mise 2026.11.0. Use `usage` spec exclusively.

---

## Positional Arguments

### Required Argument

```toml
[tasks.process]
usage = 'arg "<file>" help="Input file to process"'
run = 'cat "${usage_file}"'
```

- Angle brackets `<file>` = required
- Task fails if not provided

### Optional Argument

```toml
[tasks.compile]
usage = 'arg "[output]" default="a.out" help="Output filename"'
run = 'gcc main.c -o "${usage_output}"'
```

- Square brackets `[output]` = optional
- `default` provides fallback value

### With Choices

```toml
[tasks.deploy]
usage = '''
arg "<environment>" help="Target environment" {
  choices "dev" "staging" "prod"
}
'''
run = 'deploy.sh "${usage_environment}"'
```

### Variadic Arguments

```toml
[tasks.concat]
usage = 'arg "<files>" var=#true help="Files to concatenate"'
run = 'cat ${usage_files}'
```

With limits:

```toml
usage = 'arg "<files>" var=#true var_min=1 var_max=10'
```

---

## Flags

### Boolean Flag

```toml
[tasks.build]
usage = 'flag "-v --verbose" help="Enable verbose output"'
run = '''
if [ "${usage_verbose:-false}" = "true" ]; then
  set -x
fi
cargo build
'''
```

### Flag with Value

```toml
[tasks.server]
usage = 'flag "-p --port <port>" default="8080" help="Server port"'
run = 'uvicorn app:main --port "${usage_port}"'
```

### Environment-Backed Flag

```toml
[tasks.deploy]
usage = 'flag "--region <region>" env="AWS_REGION" default="us-east-1"'
run = 'aws --region "${usage_region}" ecs deploy'
```

Flag value can come from:

1. Command line: `--region eu-west-1`
2. Environment variable: `AWS_REGION=eu-west-1`
3. Default value: `us-east-1`

### Count Flag

```toml
[tasks.debug]
usage = 'flag "-v" count=#true help="Verbosity level"'
run = '''
case "${usage_v:-0}" in
  0) LOG_LEVEL="error" ;;
  1) LOG_LEVEL="warn" ;;
  2) LOG_LEVEL="info" ;;
  *) LOG_LEVEL="debug" ;;
esac
echo "Log level: $LOG_LEVEL"
'''
```

Usage: `mise run debug -vvv` sets `usage_v=3`

### Negation Flag

```toml
[tasks.build]
usage = 'flag "--color" negate="--no-color" default=#true'
run = '''
if [ "${usage_color}" = "true" ]; then
  cargo build --color=always
else
  cargo build --color=never
fi
'''
```

---

## Complex Examples

### Multiple Arguments and Flags

```toml
[tasks.migrate]
description = "Run database migration"
usage = '''
arg "<direction>" help="Migration direction" {
  choices "up" "down"
}
arg "[count]" default="1" help="Number of migrations"
flag "-f --force" help="Skip confirmation"
flag "--dry-run" help="Preview changes only"
'''
run = '''
#!/usr/bin/env bash
set -euo pipefail

DIR="${usage_direction}"
COUNT="${usage_count}"
FORCE="${usage_force:-false}"
DRY="${usage_dry_run:-false}"

if [ "$DRY" = "true" ]; then
  echo "[DRY RUN] Would migrate $DIR by $COUNT"
  exit 0
fi

if [ "$FORCE" != "true" ]; then
  echo "Migrating $DIR by $COUNT. Press Enter to continue..."
  read
fi

diesel migration "$DIR" --count "$COUNT"
'''
```

### Custom Completion

```toml
[tasks.deploy]
usage = '''
arg "<service>"
complete "service" run="kubectl get services -o name | sed 's|service/||'"
'''
run = 'kubectl rollout restart deployment/${usage_service}'
```

Shell completion will show available Kubernetes services.

---

## Accessing Arguments in Scripts

### Environment Variable Pattern

Arguments become `usage_<name>` environment variables:

```toml
[tasks.example]
usage = '''
arg "<input>" help="Input file"
arg "[output]" default="out.txt"
flag "-v --verbose"
flag "-n --count <n>" default="10"
'''
run = '''
echo "Input: ${usage_input}"
echo "Output: ${usage_output}"
echo "Verbose: ${usage_verbose:-false}"
echo "Count: ${usage_count}"
'''
```

### Bash Variable Patterns

| Pattern                 | Meaning          | Use Case                  |
| ----------------------- | ---------------- | ------------------------- |
| `${usage_var}`          | Variable value   | When you're sure it's set |
| `${usage_var:-default}` | Default if unset | Boolean flags             |
| `${usage_var:?error}`   | Error if unset   | Required validation       |
| `${usage_var:+value}`   | Value if set     | Conditional flags         |

**Conditional flag passing**:

```toml
run = 'myapp ${usage_verbose:+--verbose} ${usage_debug:+--debug}'
```

Only adds `--verbose` if `usage_verbose` is set.

---

## Multi-line Usage Specification

For complex tasks, use multi-line format:

```toml
[tasks.complex]
usage = '''
arg "<environment>" help="Target environment" {
  choices "dev" "staging" "prod"
}
arg "[version]" default="latest" help="Version to deploy"

flag "-f --force" help="Skip all confirmations"
flag "-n --dry-run" help="Preview without changes"
flag "--timeout <seconds>" default="300" help="Operation timeout"
flag "--region <region>" env="AWS_REGION" default="us-east-1"

complete "environment" run="echo 'dev\nstaging\nprod'"
'''
run = '''
# Script here
'''
```

---

## Validation

### Required vs Optional

- `<arg>` (angle brackets) = required, task fails if missing
- `[arg]` (square brackets) = optional, uses default or empty

### Type Coercion

All values are strings. Cast in script if needed:

```toml
[tasks.batch]
usage = 'flag "-n --count <n>" default="10"'
run = '''
COUNT="${usage_count}"
for i in $(seq 1 "$COUNT"); do
  echo "Processing batch $i"
done
'''
```

### Environment Variable Satisfaction

If a flag has `env="VAR"`, the environment variable satisfies required checks:

```toml
[tasks.deploy]
usage = 'flag "--token <token>" env="DEPLOY_TOKEN" help="Auth token"'
```

Works with:

- `mise run deploy --token abc123`
- `DEPLOY_TOKEN=abc123 mise run deploy`

---

## Best Practices

1. **Always add `help` text** - Improves discoverability
2. **Use `default` for optional flags** - Avoids empty string issues
3. **Use `env` for secrets** - Don't require secrets on command line
4. **Prefer `usage` over legacy methods** - Future-proof your tasks
5. **Validate early** - Check arguments at script start
