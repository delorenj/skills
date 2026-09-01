# Authoring a Bloodbank event schema

Bloodbank `schemas/` owns the wire-level shape of every bloodbank event. Treat it like an API contract: never edit one in place to mean something new. A breaking payload change gets a **new `action` or a new `entity`** — see event-naming.md §3.1. There is no `.v2.json` file and no version tier in the tree; the only version left anywhere is the schema revision in `dataschema` / `schemaref` (§13).

## The two-layer schema model

Every event schema is the **base envelope** + a **per-event extension**:

```
bloodbank/schemas/
├── _common/
│   ├── cloudevent_base.v1.json    # CloudEvents 1.0 + 33GOD extension fields
│   └── types.v1.json              # shared $defs (uuid, timestamp, …)
└── bloodbank/
    └── <domain>/
        └── <entity>.<action>.json      # YOUR schema, extends the base
```

Per-event schemas use `allOf` to inherit the base, then lock the `type` / `domain` consts and define the `data` object:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://33god.dev/schemas/bloodbank/agent/session.started.json",
  "title": "Agent Session Started Event",
  "type": "object",
  "allOf": [ { "$ref": "../../_common/cloudevent_base.v1.json" } ],
  "properties": {
    "type":   { "const": "bloodbank.agent.session.started" },
    "kind":   { "const": "event" },
    "domain": { "const": "agent" },
    "data": {
      "type": "object",
      "properties": {
        "session_id":        { "$ref": "../../_common/types.v1.json#/$defs/uuid" },
        "working_directory": { "type": "string", "minLength": 1 },
        "git_branch":        { "type": "string" },
        "started_at":        { "$ref": "../../_common/types.v1.json#/$defs/timestamp" }
      },
      "required": ["session_id", "working_directory", "started_at"],
      "additionalProperties": false
    }
  },
  "required": ["type", "kind", "domain", "data"]
}
```

Key rules:

- `$id` follows `https://33god.dev/schemas/bloodbank/<domain>/<entity>.<action>.json` — the URL is logical, not fetched at runtime.
- `type` is **const-locked** to the 4-token `bloodbank.<domain>.<entity>.<action>`.
- `kind` is **const-locked** to `event`, `command`, or `reply`; event subjects derive as `bloodbank.evt.<domain>.<entity>.<action>`.
- `domain` is **const-locked** to the top-level folder name.
- `data` is the only payload field producers populate; everything else is envelope-level.
- Use `$ref` into `types.v1.json` for shared primitives (uuid, timestamp). Don't redeclare them inline. The `_common/*.v1.json` files keep their `.v1` suffix on purpose — they are schema documents with their own revision line, not event types, so the version sweep does not touch them.

## Workflow

From the Bloodbank repo checkout (`~/code/33GOD/bloodbank`):

```bash
mise run validate:schemas   # JSON Schema + 33GOD-specific structural rules
mise run smoketest:schema-contract-consistency
mise run smoketest:schemas  # schema tree + naming contract + agent-hooks SSOT
```

Schema files are committed directly. The smoke tests fail if a schema's `$id`, `type`, `kind`, or contract-facing fields drift away from the naming contract.

## Building matching envelopes

The canonical hook path builds envelopes through `services/agent-hooks/core/envelope.py`; service producers should either reuse that builder or keep the same field math:

```python
ce_type = "bloodbank.agent.session.started"
envelope = {
    "type": ce_type,
    "subject": "bloodbank.evt.agent.session.started",
    "kind": "event",
    "domain": "agent",
    "schemaref": f"{ce_type}.v1",
    "dataschema": f"apicurio://holyfields/{ce_type}/versions/1",
    "data": {"session_id": session_id, "working_directory": cwd},
}
```

Do not hand-type the subject at every call site. Derive it from `(type, kind)` using the same `bloodbank.<evt|cmd|rpy>...` rule.

## Versioning

- **Additive change** (new optional field, new enum variant): bump the `description`, keep the same `.v<N>.json`. Validate that consumers tolerate the new field.
- **Breaking change** (rename, remove, retype, add required field): do NOT copy the file to a `.v<N+1>.json`. Per event-naming.md §3.1 a breaking payload change means the fact itself changed, so it earns a new `action` (or a new `entity`) and therefore a new file, a new `type`, and a new subject. Consumers bound to the old address keep receiving the old fact until it stops being emitted. Bump `dataschema` / `schemaref` only for compatible revisions.

## When to add a `_common` type

Lift a `$defs` entry into `_common/types.v1.json` only when it is reused across ≥ 2 schemas. Premature sharing of "common" types fights schema evolution.

## Anti-patterns

- Treating downstream generated bindings as the source of truth; the JSON Schemas own the wire contract.
- Skipping `mise run smoketest:schemas` before pushing.
- Editing the `cloudevent_base.v1.json` extension fields to fit a one-off use case — propose an ADR in `~/code/33GOD/docs/architecture/` instead.
- Using free-form `data: { type: object }` with no required fields ("anyone can put anything"). Tighten the schema before merging.
