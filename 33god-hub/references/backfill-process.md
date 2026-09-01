# Backfill Process

Backfills live in `33god-platform/backfills/*.yaml`.

Start read-only:

```bash
python3 scripts/platform.py backfills check
```

Only add `apply` behavior after the migration is reversible, idempotent, and
tested on a dirty checkout.
