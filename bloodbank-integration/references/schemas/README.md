# Schemas

Every bloodbank event is described by a JSON Schema in the Bloodbank `schemas/` directory. The schema source of truth lives in the Bloodbank repo at `~/code/33GOD/bloodbank/`; validation scripts check `$id` uniqueness, `$ref` resolution, Draft 2020-12 validity, and consistency with the naming contract in `docs/event-naming.md`.

## Reading Order

| Task | Read |
|---|---|
| Author or version an event schema | `bloodbank-schemas.md` |
| Decide what to name an event_type / NATS subject | `naming.md` |
| Hit a confusing failure (drift, wrong version, allOf, etc.) | `gotchas.md` |

## Where things live

| Artifact | Path |
|---|---|
| JSON Schema sources (single source of truth) | `bloodbank/schemas/bloodbank/<domain>/<entity>.<action>.json` |
| CloudEvents base schema (every event `allOf`-extends this) | `bloodbank/schemas/_common/cloudevent_base.v1.json` |
| Shared types ($defs for uuid, timestamp, etc.) | `bloodbank/schemas/_common/types.v1.json` |
| Schema validator | `bloodbank/scripts/validate_schemas.sh` |
| Naming/schema consistency smoke | `bloodbank/ops/smoketest/smoketest-schema-contract-consistency.sh` |
| Bloodbank schema commands | `bloodbank/mise.toml` (`validate:schemas`, `smoketest:schema-contract-consistency`, `smoketest:schemas`) |

## High-level workflow

1. Draft or modify the JSON Schema under `bloodbank/schemas/bloodbank/<domain>/`.
2. `mise run validate:schemas` (catches malformed `$ref`, missing required, etc.).
3. `mise run smoketest:schema-contract-consistency` (catches schema names/types the contract validator rejects).
4. `mise run smoketest:schemas` before commit.

For the per-step detail, the field-level conventions, and the `allOf` extension pattern, read [bloodbank-schemas.md](./bloodbank-schemas.md).
