---
name: create-enrichment-pass
description: Create, extend, or refactor portable enrichment passes (EPs) for Wax document and transcript pipelines. Use when authoring a pass that derives title, summary, slug, tags, classification, entities, or links from Markdown documents or transcripts; declaring document or audio capabilities; making a transcript pass reusable for ordinary documents; defining a pass registry entry or the wax.ep.v1 result contract; or testing pass isolation, requires gating, versioning, provenance, and no-clobber behavior. Runtime operation, pipeline compilation, n8n import, and Holocene belong to the sibling wax-pipeline skill; incidents to heyma-pipeline-doctor.
---

# Create Enrichment Pass

## Goal

Author an EP as a portable, side-effect-free document processor. Treat a
transcript as a document with an optional audio relationship, not as a
separate kind of input. Filesystem renames, ledger updates, archive links,
notifications, and pipeline state belong to the host runner or a thin,
declared adapter.

Wax (HeyMa `components/wax/`) is the shipped reference host: its
`docs/ENRICHMENT-PASSES.md`, `src/wax/passes.py`, and registry entries are the
contract of record, and this skill's scaffold emits that shape. This skill
owns authoring only. For runtime operation — compiled pipelines, registry
drift, document bindings, retries and sweeps, n8n graph authoring and import,
and Holocene's read-only catalog — use the sibling
[../wax-pipeline/SKILL.md](../wax-pipeline/SKILL.md). For incidents and
silent failures, use `heyma-pipeline-doctor`.

Before implementing a pass, read
[references/contract.md](references/contract.md) completely. It defines the
command boundary, result envelope, capability semantics, ownership rules, and
the Wax adapter surface.

## Non-negotiable invariants

- Accept one document path and an optional opaque item ID. Never require audio
  to derive text metadata.
- Read the document; do not mutate, rename, move, delete, upload, or tag it
  from the pass process. Emit declarative JSON; the runner applies changes
  atomically.
- Return grounded enrichment only. Never invent missing source facts; never
  fabricate transcript or audio provenance a document does not have.
- Preserve non-empty human or upstream values (including `0`, `false`, and
  non-empty lists) unless the registry explicitly authorizes a field in
  `clobber`. Never return runner-owned identity or provenance fields.
- Capabilities are an explicit opt-in: `capabilities: [document]`, `[audio]`,
  or both. Absent means audio-only in Wax. Declare only proven capabilities —
  see step 3.
- Independence is a default, not a law. Siblings keep running past a failed
  pass, but `requires` explicitly gates dependents, a pipeline may choose
  `failure_policy: halt`, and a failed pass withholds its item's completion
  until retried. State the gating you mean; never claim a pass can never
  block another.
- Report classified failures with `reason_code=<code>` as the first stderr
  line. Codes are lowercase letters and underscores only — no digits, because
  that is what the runner's header regex accepts.

## Workflow

### 1. Map the host before editing

Locate the current runner, registry, result parser, metadata writer,
pass-state store, and tests. Record:

- supported command placeholders and environment variables;
- result-envelope version and recognized mutation intents;
- protected fields and no-clobber behavior;
- automatic-run ordering, retry and sweep semantics, and version skip rules;
- host-only side effects such as rename, ledger updates, or source-object
  links.

If the host is Wax, read its current `ENRICHMENT-PASSES.md` doc, registry
entries, `passes.py`, and at least one pass test from the deployed checkout
(`~/HeyMa`, not an older copy). Prefer the live implementation over stale
design documents, and current source over either this skill or recalled outages.

### 2. Define the pass boundary

Write down the pass's inputs, outputs, and owned fields before writing code.
Classify each desired behavior as one of:

1. **Portable enrichment** — values derived from document content, such as
   title, summary, slug, tags, entities, or classification.
2. **Document mutation intent** — rename or metadata updates the runner
   should apply safely, expressed declaratively in the result.
3. **Host effect** — transcript ledger changes, audio/S3 linkage, queue
   state, notifications, or another integration-specific action.

Implement category 1 in the shared core. Express category 2 declaratively.
Implement category 3 only in a host adapter or the runner. If the pass cannot
be described without embedding host state in the core, redesign the boundary.

### 3. Declare capabilities explicitly

`capabilities` is opt-in, per pass, in the registry:

- `[document]` — the pass runs over plain Markdown documents (document
  bindings). A document run skips a pass lacking `document` with
  `inapplicable_capability`, which satisfies ordering exactly like any other
  skip; a dependency gated on a skipped pass still runs.
- `[audio]` — declares support for transcript notes of audio items. The shipped
  legacy audio runner does not enforce the inverse gate: a pass without `audio`
  can still run there. Absent capabilities excludes ordinary documents, not
  legacy audio. Test declared support; do not infer a symmetric denial rule.
- `[document, audio]` — the same grounded logic truly serves both shapes.

A core text pass (title, summary, tags, classification, entities) should
declare both when its algorithm needs nothing but note text — then prove it
against a document fixture and a transcript fixture. An audio-dependent pass
(diarization) declares `audio` and is tested with its declared source
context, never faked into document success. A notification or effect pass
(clipboard, relay) is a host adapter, not portable text enrichment: declare
only what it genuinely is and keep the effect in the adapter.

### 4. Scaffold the files

Invoke the bundled generator directly — no wrapper task; this skill's scripts
run with a plain interpreter, not a repo task runner:

```bash
python3 scripts/scaffold_pass.py PASS-SLUG --registry-dir PATH --host wax \
  [--capability audio] [--description "..."]
```

- The slug must start with a letter and use only lowercase letters, digits,
  and hyphens — the same shape Wax validates for pipeline and n8n import
  names, so a scaffolded slug can always be named in a graph.
- Wax scaffolds default to `capabilities: [document]`; repeat `--capability`
  (document, audio) to declare both, or pass `--capability audio` alone.
- Descriptions round-trip safely (quotes, newlines, backslashes) through both
  the YAML registry entry and the generated docstring.
- The generator refuses to overwrite existing files, and creates a disabled,
  non-automatic entry plus a side-effect-free executable that reports
  failures with a first-line `reason_code=`.

Inspect both outputs, then replace the scaffold's enrichment function with
grounded logic. For a different registry format, preserve the same executable
contract and create the host registration manually. The scaffold's own tests
are isolated and stdlib-only: `python3 -m unittest discover -s tests` from
this skill's root.

### 5. Implement the portable core

- Name the main function for documents, for example `enrich_document`; use
  `enrich_transcript` only when the algorithm genuinely depends on transcript
  structure such as speaker turns.
- Isolate model/network calls behind a small function replaceable in tests.
- Bound context deterministically and retain semantically useful regions.
- Validate model or parser output before building the result envelope.
- Make reruns idempotent: same content and configuration, same effective
  metadata.
- Diagnostics go to stderr — with a `reason_code=<code>` first line for
  classified failures — and one compact result object as the final stdout
  line.

### 6. Add only the necessary adapter

Use the portable result directly for metadata-only passes. The Wax runner
already interprets the host intents; do not wrap them again:

- `transcript.slug` is an **audio-only** adapter intent: collision-safe
  rename of the transcript note. A document run drops the rename — a
  document keeps the name its owner gave it.
- `link_audio` is historical: accepted and ignored, because the worker
  refreshes the audio link after every run regardless of the passes. Do not
  emit it in new passes.
- `events` are the audio flow's contract (registry `emits` allowlist,
  Bloodbank schema validation, runner-side publication). A document run that
  declares events fails itself with `result_apply_failed` before the note or
  ledger moves; document enrichment proposes frontmatter (and authorized
  body edits) only.

Never make the shared enrichment function read the transcript ledger, call
S3, or publish events. A generic document host must be able to use the same
enrichment function and frontmatter result with the adapter omitted.

### 7. Register conservatively

- Start at `version: 1`. Bump it whenever behavior or output semantics change
  and items should rerun the new definition once.
- A version bump is not a migration and not a backfill: existing minted audio
  plans never move to a new definition, and completed items keep their stored
  plan — reaching history is an explicit operator action (`wax ep run
  <slug> <item>`, `wax documents backfill`; see ../wax-pipeline).
- Remember what compile freezes: a compiled pipeline freezes the registry
  configuration — command argv, env, edges, conditions, capabilities, version
  — not the executable bytes. Editing an executable changes behavior for any
  plan invoking that path; verify the code and restart the daemon for runner
  changes. Registry YAML edits are live for manual and legacy-registry runs.
- Start with `enabled: false` and `auto: false` while testing.
- Keep `requires: []` unless ordering is a proven semantic dependency; `after`
  orders without gating. Keep `clobber: []` unless overwriting a specific
  field is an explicit product decision.
- Set a finite timeout; declare model/config values in the registry or
  environment rather than embedding machine-specific paths in the core.

### 8. Prove interchangeability

Test the same portable core against at least:

- an ordinary document fixture with frontmatter and body text;
- a transcript fixture, including transcript-shaped text or speaker labels;
- a document with pre-existing owned values to prove no-clobber behavior;
- malformed, empty, and oversized input;
- invalid model/processor output and timeout/error paths, each reporting a
  valid first-line `reason_code=`;
- capability behavior: a document run skipping an audio-only pass
  (`inapplicable_capability`) while a dependency gated on it still runs.

Then test the host adapter separately for atomic writes, collision-safe
rename, state recording, and any archive/source linkage. Verify the gating
you declared: a failed `requires` target blocks its dependent
(`dependency_failed`); an independent sibling proceeds; a `halt`-policy graph
stops at the first failure — prove whichever your graph uses.

### 9. Enable and document

Run focused tests, the host suite, and a dry/manual invocation that captures
the final JSON. Enable the pass only after both a generic-document fixture
and the target host fixture pass. If setting `auto: true`, verify its exact
lifecycle position and rerun/skip behavior. Document owned fields, declared
capabilities, external dependencies, version changes, and optional host
effects.

## Completion report

Report the pass slug/version, declared capabilities, portable fields, host
adapter effects, registry state, tests run, and any explicit reruns or
backfills required. Explicitly state whether the same core was exercised
against both a document and a transcript, and name the gating edges the pass
declares.
