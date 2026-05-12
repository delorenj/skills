# Authoring a schema in holyfields

Holyfields owns the wire-level shape of every bloodbank event. Treat it like an API contract: a breaking change is a `.v2` file, never an edit-in-place.

## The two-layer schema model

Every event schema is the **base envelope** + a **per-event extension**:

```
holyfields/schemas/
├── _common/
│   ├── cloudevent_base.v1.json    # CloudEvents 1.0 + 33GOD extension fields
│   └── types.v1.json              # shared $defs (uuid, timestamp, …)
└── <domain>/
    └── <entity>.<action>.v<N>.json # YOUR schema, extends the base
```

Per-event schemas use `allOf` to inherit the base, then lock the `type` / `domain` consts and define the `data` object:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://33god.dev/schemas/agent/session.started.v1.json",
  "title": "Agent Session Started Event",
  "type": "object",
  "allOf": [ { "$ref": "../_common/cloudevent_base.v1.json" } ],
  "properties": {
    "type":   { "const": "agent.session.started" },
    "domain": { "const": "agent" },
    "data": {
      "type": "object",
      "properties": {
        "session_id":        { "$ref": "../_common/types.v1.json#/$defs/uuid" },
        "working_directory": { "type": "string", "minLength": 1 },
        "git_branch":        { "type": "string" },
        "started_at":        { "$ref": "../_common/types.v1.json#/$defs/timestamp" }
      },
      "required": ["session_id", "working_directory", "started_at"],
      "additionalProperties": false
    }
  },
  "required": ["data"]
}
```

Key rules:

- `$id` follows `https://33god.dev/schemas/<domain>/<entity>.<action>.v<N>.json` — the URL is logical, not fetched at runtime.
- `type` is **const-locked** to a single dotted value (matches `^[a-z0-9]+(\.[a-z0-9]+)+$`).
- `domain` is **const-locked** to the top-level folder name.
- `data` is the only payload field producers populate; everything else is envelope-level.
- Use `$ref` into `types.v1.json` for shared primitives (uuid, timestamp). Don't redeclare them inline.

## Workflow

From the holyfields checkout (`~/code/33GOD/holyfields/`):

```bash
mise run validate:schemas   # JSON Schema + 33GOD-specific structural rules
mise run generate:all       # writes packages/python + packages/typescript generated/
mise run check:drift        # fails if generated/ doesn't match the schemas
mise run ci                 # the full pipeline (validate → generate → typecheck → tests)
```

Generated artifacts are committed; CI fails on drift. Re-run `generate:all` whenever you touch a `.json` schema and include the regenerated files in the same commit.

## Importing the generated types

Python producer/consumer:

```python
from holyfields.generated.agent.session_started_v1 import AgentSessionStartedV1, AgentSessionStartedV1Data

envelope = AgentSessionStartedV1(
    id="...", source="urn:33god:service:my-svc", type="agent.session.started",
    subject=f"agent/{session_id}", time=now_iso(), domain="agent",
    data=AgentSessionStartedV1Data(session_id=session_id, working_directory=cwd, started_at=now_iso()),
)
```

TypeScript consumer:

```typescript
import { AgentSessionStartedV1Schema } from "@33god/holyfields";

const parsed = AgentSessionStartedV1Schema.safeParse(rawEnvelope);
if (!parsed.success) throw new Error(`schema mismatch: ${parsed.error}`);
```

## Versioning

- **Additive change** (new optional field, new enum variant): bump the `description`, keep the same `.v<N>.json`. Validate that consumers tolerate the new field.
- **Breaking change** (rename, remove, retype, add required field): copy to `.v<N+1>.json`, change the `const` `type` to the new versioned dotted form (rare — usually stays the same), update `dataschema` URIs. Run v1 and v2 in parallel until consumers cut over.

## When to add a `_common` type

Lift a `$defs` entry into `_common/types.v1.json` only when it is reused across ≥ 2 schemas. Premature sharing of "common" types fights schema evolution.

## Anti-patterns

- Adding fields to generated Pydantic/Zod files (regenerate instead).
- Skipping `mise run check:drift` before pushing.
- Editing the `cloudevent_base.v1.json` extension fields to fit a one-off use case — propose an ADR in `~/code/33GOD/docs/architecture/` instead.
- Using free-form `data: { type: object }` with no required fields ("anyone can put anything"). Tighten the schema before merging.
