# Maintain an enrichment pass in Wax

The reusable implementation procedure belongs to sibling `create-enrichment-pass`.
This reference owns Wax registration, capability and compiled-pipeline integration.

## Discover before changing

Read `components/wax/config/passes.d/<slug>.yaml`, its executable, `src/wax/passes.py`
and relevant tests. Use CLI `catalog --json` for safe discovery, `ep list --json`
for the operator registry view, and `ep status <item-key> --json` for detailed
outcomes (may contain body/error detail; never proxy it to Holocene).

At release, automatic passes were frontmatter-stamp, classification, diarization,
clipboard-copy and title-slug. project-extraction/ticketable were implemented but
disabled, four other registrations were placeholders. **Query current truth**;
never enable a disabled definition just because a skill describes its purpose.

## Registration contract

```yaml
slug: example-pass
version: 1
description: Grounded metadata from ordinary Markdown and transcript text.
capabilities: [document, audio]
enabled: false
auto: false
requires: []
after: []
clobber: []
timeout_s: 300
command: ["{component_root}/config/passes.d/bin/example-pass", "{md_path}", "{item_id}"]
```

`document` opts into ordinary Markdown execution. `audio` identifies a linked
recording/host adapter. Declare only proven capabilities. A portable text pass
can support both; a diarizer needs linked audio, and clipboard notification is
an effect rather than portable enrichment. A document run skips passes lacking
`document` capability and never fabricates audio to make them applicable.

For legacy registry auto flow, `enabled` plus `auto` enters new audio plans.
Compiled transcription definitions require enabled+automatic pass snapshots.
Document graphs select compatible enabled passes explicitly; `auto` is not a
folder-binding switch. Set `enabled` and `auto` **before** importing a pass into
a transcription graph; otherwise compilation correctly refuses that snapshot.
Compiled graphs continue their frozen definition even when registry YAML moves;
recompile/import deliberately to adopt it.

Current capability enforcement is **one-sided**: document execution requires
`document`; the legacy audio path does not reject a text pass merely because its
capabilities list lacks `audio`. Do not treat the declaration as proof of a
symmetric runtime gate. Declare/test the intended supported contexts anyway;
`project-extraction` is currently document-declared but would be callable from
an enabled audio plan. Do not silently turn it on to demonstrate that behavior.

## Result and ownership

Pass reads one document path with optional opaque item key and returns a final
stdout JSON object containing integer `wax_ep_version: 1`, `frontmatter`, optional
compare-and-replace `body_replace`, optional explicit skip/reason. No direct
mutation from the portable pass. Wax applies no-clobber, body hash compare,
protected identity/provenance and collision-safe transcript rename.

`transcript.slug` is an **audio transcript adapter** intent; document runs keep
their path. Historical `link_audio` is accepted and ignored: the audio worker
refreshes linkage, not the pass. Document results reject `events`. Audio/business
event declarations require registry `emits` and schema validation before apply
and publication; load `bloodbank-integration` for schema work.

For a classified failure, the first stderr line is `reason_code=<lowercase_code>`;
allowed codes use lowercase letters/underscores. Exit nonzero on processor
failure. Do not log credentials or return runner-owned fields (`wax-item-id`,
`wax`, capture/source/vault identity). No-clobber includes existing false/zero and
nonempty lists, not just strings.

## Dependencies, conditions and failure

`requires` orders+gates, `after` only orders; `when` is a declarative AND-list.
Skipped dependencies currently satisfy convergence. Add a meaning-field condition
when the consumer genuinely needs produced metadata. Independent siblings continue
unless the graph explicitly uses halt. Invalid registry content quarantines a pass
and its dependents, not every unrelated pass. Compiler validation does not excuse
invalid command configuration or a missing executable at runtime.

Same semantic version means completed work need not rerun. Bump version when
behavior/output semantics change; it does not mutate old plans or auto-backfill.
Sweep exhaustion, command IDs and attempts must stay monotonic/idempotent; never
reset ledger attempts manually. Use the existing retry interfaces.

## Tests that prevent real failures

- Generic Markdown and transcript fixtures for portable cores; audio-only
  adapters tested with their declared source context, not fake no-audio success.
- Direct processor leaves input bytes/path unchanged; runner applies metadata
  and authorized body changes without losing human values.
- Failure/condition/unavailable states visible; required consumer blocked on
  failure, independent/order-only sibling proceeds, skip convergence explicit.
- Body compare-and-replace protects an intervening human edit.
- Frozen graph remains pinned after live-registry changes; current-version
  counts and pipeline-scoped outcomes do not become global totals.
- New path arrival, edited known path, own-write retry, duplicate/concurrent
  delivery, exhausted retry and missing folder behavior.
- After pass registration changes, generated n8n nodes and packed native-loader
  proof match the real catalog; test actual example exports, not only synthetic
  nodes. See [graph maintenance](pipelines-and-n8n.md).

Use temp-root fixtures and stub provider calls in ordinary tests. Model-backed
acceptance and production enablement are deliberate actions, not incidental to
editing a skill. Prefer the AutomaticAI gateway with per-consumer `op://` references;
Jev's existing decisions-route exception is intentional, not a template to copy.
