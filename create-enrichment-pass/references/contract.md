# Portable enrichment-pass contract (wax.ep.v1)

This reference defines the authoring contract for a portable enrichment pass
as shipped by Wax (HeyMa `components/wax/`). It is the contract of record for
what a pass may read, return, and declare. Runtime operation — compiling
pipelines, importing n8n graphs, document bindings, retries and sweeps, and
Holocene's read-only catalog — is owned by the sibling skill at
[../wax-pipeline/SKILL.md](../../wax-pipeline/SKILL.md).

## Vocabulary

- **Document**: a UTF-8 text artifact presented to an EP. Markdown transcripts
  are documents. A host may normalize HTML, PDF, DOCX, email, or another
  format to text before invoking the EP.
- **Portable core**: content-derived logic with no knowledge of queues,
  databases, object stores, vault locations, or transcript lifecycle state.
- **Runner**: executes the command, validates its result, applies mutations,
  records state, and isolates failures.
- **Host adapter**: translates portable output to runner-specific intents or
  effects. Audio linkage is one such effect; it is not enrichment.

Interchangeability means the same portable core can consume a normalized
ordinary document or a transcript and return the same result shape. It does
not mean every host supports every optional effect, and it does not mean
every pass runs on every input shape — capabilities decide that.

## Command boundary

Use this CLI shape unless the host already defines a stricter one:

```text
PASS_EXECUTABLE DOCUMENT_PATH [ITEM_ID]
```

- `DOCUMENT_PATH` is the only required input. Wax expands `{md_path}` (which
  falls back to the document path for document runs) plus `{item_id}`,
  `{component_root}`, and `{home}` before exec.
- `ITEM_ID` is opaque correlation context. Never use it to fetch required
  content when the supplied path already contains that content.
- Configuration belongs in explicit environment variables or registry fields
  (registry `env` wins over the unit and the shell).
- Exit `0` only after printing a valid result. Use nonzero for failure.
- Diagnostics go to stderr. The last JSON object on stdout is the result.
- The pass must not edit, rename, move, delete, upload, or tag the document.

## Failure classification: `reason_code`

A pass that knows why it failed prints `reason_code=<code>` as the **first**
stderr line, matching `^reason_code=([a-z_]+)$` — lowercase letters and
underscores only, no digits. Detail lines follow the header. Without a valid
header the runner classifies from the exit path instead (`nonzero_exit`,
`timeout`, `run_error`, or `result_apply_failed` when the result cannot be
applied). A timeout is a timeout no matter what stderr said.

## Result envelope

```json
{
  "wax_ep_version": 1,
  "frontmatter": {"title": "Portable Document Enrichment", "title-slug": "portable-document-enrichment"},
  "state": "skipped", "reason_code": "no_project",
  "transcript": {"slug": "portable-document-enrichment"},
  "body_replace": {"sha256": "<sha256 of the body the pass read>", "text": "..."},
  "events": [{"type": "intake.detected", "key": "<stable dedup key>", "data": {}}],
  "link_audio": true
}
```

| Key | Audio run | Document run |
| --- | --- | --- |
| `wax_ep_version` | Required integer version; the portable minimum is `{"wax_ep_version": 1, "frontmatter": {...}}`. | Same. |
| `frontmatter` | Proposals applied in one batch under no-clobber rules. | Same; the only way a document pass changes its note. |
| `state` / `reason_code` | Optional explicit skip (`{"state": "skipped", "reason_code": "no_project"}`); frontmatter still applies and the skip satisfies gating and finalization. | Same. |
| `transcript.slug` | Adapter intent: collision-safe rename to `<date-prefix>-<slug>.md`; the ledger path updates before the pass records, so later passes see the new path. An existing human `title-slug` wins unless clobbered. | **Dropped, not honored** — a document keeps the name its owner gave it. |
| `body_replace` | Applied only when the registry authorizes `body_mutation: compare-and-replace` and the body still hashes to `sha256`; a human edit in between preserves the human text. | Same authorization and hash guard. |
| `events` | Allowed with a registry `emits` allowlist; schema-validated fail-closed before the note or ledger moves; published by the runner, never the pass. | **Rejected**: a document run declaring events fails itself with `result_apply_failed`. Anything that must become an event fact waits for the audio flow or an explicit workflow. |
| `link_audio` | Historical. Accepted and ignored: the worker refreshes the audio link after every run regardless of the passes. Do not emit in new passes. | Ignored. |

Anything else in the result is ignored. A command that prints no
`wax_ep_version` object still runs and is tracked, but proposes nothing.

Rules for `frontmatter` proposals:

- `frontmatter` must be an object, including when empty.
- Keys must match `[A-Za-z0-9_-]+`.
- Values must be JSON-safe and grounded in the supplied document.
- Absence means no proposal; never use `null` to erase existing metadata.
- A value lands only if the existing one is empty (`None`, `""`, `[]`, `{}`),
  identical, or the key is in `clobber`. `0` and `false` are values, not
  holes; a new `[]` does not erase a non-empty list.
- The runner owns merge policy; a pass never assumes its proposal replaces a
  non-empty value.

## Capabilities

`capabilities` is an explicit per-pass opt-in — a list of input shapes the
pass declares it can run over:

```yaml
capabilities: [document]        # plain Markdown documents only
capabilities: [audio]           # transcript notes of audio items only
capabilities: [document, audio] # same grounded logic, both shapes
```

- Absent means `audio` only; old registrations are unchanged by the field.
- A document run replaces an absent list with `["audio"]` and skips the pass
  with `inapplicable_capability`. The skip satisfies ordering exactly like
  any other skip, and a dependency gated on a skipped pass **runs** — it is
  never silently dropped.
- Declare only proven capabilities. A core text pass (title, summary, tags,
  classification, entities over note text) can declare both once both fixture
  shapes pass. An audio-dependent pass (diarization) declares `audio` and is
  tested with real source context, not a faked no-audio success. A
  notification or effect pass (clipboard copy, relay) is a host adapter, not
  portable text enrichment.
- A document run never fabricates transcript or audio provenance to make an
  audio pass applicable; there is no `transcripts` row for a document.

## Ownership and no-clobber

Keep three ownership classes distinct:

| Owner | Examples | EP behavior |
| --- | --- | --- |
| Source/ingest | capture time, source URI, checksum | Never return or modify |
| Human/upstream | an existing title, tags, corrections | Preserve unless explicit `clobber` policy allows replacement |
| This EP | newly derived summary, slug, entities | Propose declaratively; runner applies |

Wax rejects proposals for its runner-owned identity and provenance keys:
`wax-item-id`, the `wax` state block, `captured`, `created_at`, `source`,
`source-audio`, `source-s3-key`, `source-s3-uri`, `source-sha256`, and
`vault-id`. Read the live protected-field set in the runner because it may
evolve. The audio-to-transcript identity chain (`source-sha256` content ID,
S3 sidecars, object tags) exists so audio is never renamed after upload; a
pass never touches it.

## Pure-core pattern

Keep result construction separate from host adaptation:

```python
def enrich_document(text: str, *, item_id: str = "") -> dict[str, object]:
    """Return only content-derived frontmatter proposals."""
    return {"summary": summarize(text)}


def portable_result(text: str, *, item_id: str = "") -> dict[str, object]:
    return {
        "wax_ep_version": 1,
        "frontmatter": enrich_document(text, item_id=item_id),
    }
```

The function may understand transcript syntax when its purpose requires it,
but it must accept a normal document without audio metadata or a ledger row.

## Independence, gating, and halting

Default behavior is independent failure: a failed pass is recorded but does
not stop its siblings or the archive/link steps, and it does not publish
partial results. Independence is not unconditional:

- **`requires` is an explicit gate.** A dependent does not run until each
  requirement is `completed` or `skipped` at the wanted version; otherwise it
  records `dependency_failed` (a real attempt in the ledger). A requirement
  that is missing, disabled, quarantined, or manual-when-auto quarantines the
  dependent loudly — and only the dependent plus anything gated on it.
- **A failed pass withholds finalization.** The item stays
  `enrichment_pending` until the pass is retried (manual run or sweep), even
  though siblings finished.
- **A pipeline may choose `failure_policy: halt`**, stopping a run at the
  first failed node instead of running siblings.

So: state the gating edges a pass declares and test those edges. Never claim
— in docs, comments, or reviews — that one EP can never block another.

`after` is ordering only and never gates. `when` clauses route declaratively
on frontmatter at run time; a first unmet clause records
`skipped`/`condition_unmet`. Prefer `when` over the legacy single-clause
`skip_when` for anything new.

## Capability enforcement caveat

In the shipped Wax runner, `document` is an enforced opt-in for document runs.
The legacy audio path does not symmetrically reject a pass lacking `audio`.
Declare and fixture-test intended support; never infer a runtime deny rule from
the capability label alone. Pipeline activation still requires an explicit
selection and, for transcription, enabled+automatic registry snapshots.

## Registry baseline

```yaml
slug: example-pass
version: 1
description: "Derive example metadata from any text document"
capabilities: [document, audio]
enabled: false
auto: false
requires: []
after: []
clobber: []
timeout_s: 300
command: ["{component_root}/config/passes.d/bin/example-pass", "{md_path}", "{item_id}"]
```

- Slugs start with a letter and use only lowercase letters, digits, and
  hyphens — the same shape Wax validates for pipeline and n8n import names.
- A registry edit is live for manual runs and legacy-registry flows once the
  YAML is written (write atomically; a parse error silently disables the
  pass, and a malformed field quarantines it). Runner Python code is imported
  once into the daemon and needs a restart.
- Registry `env` placeholders expand the same command placeholders. Declare
  model routes and keys here (via `op://` references where secrets apply),
  never inside the portable core.

## Freeze, versions, and reruns

- A compiled pipeline freezes the registry **configuration** — command argv,
  env, edges, conditions, capabilities, and version — as it stood at compile.
  It does not freeze executable bytes: editing an executable changes behavior
  for any plan invoking that path, so code changes need their own
  verification (and a daemon restart when runner code changed). Compile is
  explicit; registry drift is reported, never auto-adopted.
- Existing minted audio plans never migrate to a new authority or definition,
  completed or not. An item finishes (or is retried) under the graph it was
  given.
- Automatic runs skip a pass already completed at the same `version` and
  definition; a bumped version runs the new definition once on unfinished and
  future items. A bump never implicitly backfills completed items — history
  is reached explicitly (`wax ep run <slug> <item>`, `wax documents
  backfill`), which is an operator action, not a registration side effect.
- Exhaustion is a dead-letter signal with a receipt; re-arming attempts is an
  explicit retry path, never ledger surgery. See ../wax-pipeline.

## Required test matrix

| Layer | Required proof |
| --- | --- |
| Portable core | Same function succeeds for generic document and transcript fixtures |
| Contract | Final stdout line parses; version and frontmatter types are valid; failure first stderr line is a valid `reason_code=` header |
| Capability | Document run skips an audio-only pass (`inapplicable_capability`); a dependency gated on that skip still runs; audio-only adapters tested with real source context |
| Ownership | Existing values survive unless explicitly clobberable — including `0`, `false`, and non-empty lists |
| Purity | Input bytes and path are unchanged after direct pass execution |
| Failure | Empty/malformed/non-UTF-8 input and dependency failures exit nonzero without partial mutation |
| Runner | Atomic metadata application and durable per-pass state |
| Adapter | `transcript.slug` rename is collision-safe and audio-only; documents keep their name; `events` absent from document results; `link_audio` not emitted by new passes |
| Isolation | Declared edges proven: a failed `requires` target blocks its dependent; an independent sibling proceeds; a `halt` graph stops at the first failure |
| Versioning | Same version skips when complete; bumped version reruns unfinished items; no implicit backfill of completed ones |
