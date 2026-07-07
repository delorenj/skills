# Schemas

Every bloodbank event is described by a versioned JSON Schema in the Bloodbank `schemas/` directory. The schema source of truth lives in the Bloodbank repo at `~/code/33GOD/bloodbank/`; it generates Pydantic models (Python) and Zod schemas (TypeScript) from those JSON Schemas. Producers and consumers import the generated types — they never construct envelopes by hand.

## Reading Order

| Task | Read |
|---|---|
| Author or version an event schema | `bloodbank-schemas.md` |
| Decide what to name an event_type / NATS subject | `naming.md` |
| Hit a confusing failure (drift, wrong version, allOf, etc.) | `gotchas.md` |

## Where things live

| Artifact | Path |
|---|---|
| JSON Schema sources (single source of truth) | `bloodbank/schemas/<domain>/<entity>.<action>.v<N>.json` |
| CloudEvents base schema (every event `allOf`-extends this) | `bloodbank/schemas/_common/cloudevent_base.v1.json` |
| Shared types ($defs for uuid, timestamp, etc.) | `bloodbank/schemas/_common/types.v1.json` |
| Generated Python (Pydantic) | `bloodbank/packages/python/src/generated/` |
| Generated TypeScript (Zod) | `bloodbank/packages/typescript/src/generated/` |
| Bloodbank schema commands | `bloodbank/mise.toml` (validate:schemas, generate:all, check:drift, ci) |

## High-level workflow

1. Draft or modify the JSON Schema under `bloodbank/schemas/<domain>/`.
2. `mise run validate:schemas` (catches malformed `$ref`, missing required, etc.).
3. `mise run generate:all` (rebuilds Pydantic + Zod from the schemas).
4. `mise run check:drift` (fails if generated code is out of sync).
5. `mise run ci` end-to-end before commit.
6. Import the generated type from the producer/consumer side. Never hand-edit the generated files.

For the per-step detail, the field-level conventions, and the `allOf` extension pattern, read [bloodbank-schemas.md](./bloodbank-schemas.md).
