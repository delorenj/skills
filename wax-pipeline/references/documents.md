# Document scenarios and ownership

Read before binding a folder or running/backfilling Markdown. These are Wax
operations, not a generic vault watchdog/router procedure.

## Inspect first

From the verified HeyMa checkout:

```bash
mise x -- ./bin/wax catalog --json
mise x -- ./bin/wax pipeline show doc-standard --json
mise x -- ./bin/wax pipeline bindings --json
mise x -- ./bin/wax documents list --json
```

The released binding is `~/d/Inbox/Wax`, resolving on this host to
`~/code/DeLoDocs/Inbox/Wax`. `~/d/Transcripts` is transcript output and must not
become a second file-watch/enrichment trigger. Catalog is the safe read API;
operator listings/status may include more detail and must not be proxied raw.

## Bind deliberately

1. Pick one explicit Markdown input folder and compatible `document` passes.
   Check `capabilities` and availability from catalog, not a hardcoded inventory.
2. Check for **other recursive owners first**: DeLoDocs cleanup/watchdog/router,
   folder-curator, Syncthing transport rules and native n8n file triggers. Ensure
   an actual exclusion in each competing owner before activation. A skill saying
   "Wax owns this subtree" is not proof the other service excludes it. Do not
   silently stop or rewrite another pipeline during skill capture.
3. Author a `documents` trigger with absolute/home-qualified folders and explicit
   automatic enablement in the Wax Pipeline node or YAML. Missing folders must
   remain visibly missing/unseeded, never report healthy coverage.
4. Compile/import explicitly. First scan seeds every existing file with no EP
   execution; only subsequent **new paths** are arrivals. If a folder is not
   empty, this is intentional non-backfill, not a stuck pipeline.
5. Enable worker pickup only when authorized, then verify the seed/binding receipt
   and scan timestamp. Test with a single disposable new document, not a vault
   replay. Confirm one effective receipt after a later scan and an unchanged body.

For a temporary-root test, isolate ledger, vault, pass/pipeline registries and
source roots; do not run test fixtures against the live ledger.

## Arrival, revision and retry semantics

- Known paths do not auto-re-enrich on human edits or Wax writes. Explicit
  `documents run` is how to enrich an edit. New content at an existing path is
  therefore not an automatic arrival.
- Receipts are per binding/document/pipeline/compiled definition, not one global
  "done" bit. Bindings may share a path but must not steal each other's receipts.
- Content identity plus `current_sha256` prevents Wax's output from recursively
  arriving. A failed run may still have written pass diagnostics/frontmatter;
  retries adopt that document identity, not a new hash-shaped work item.
- Retryable failed arrivals are scanned within their budget. Human content changes
  supersede a failed registration rather than being consumed by its retry.
- Per-document run flock must span the full graph, not only a pass; a time expiry
  alone must not let another worker steal a genuinely running document.
- Capability mismatch records `skipped` / `inapplicable_capability`. Existing
  `requires` convergence accepts skipped dependencies; if a downstream pass truly
  needs produced metadata, guard the meaning field explicitly.

## Explicit operator mutations

```bash
# Re-enrich a new or edited ordinary document using this compiled pipeline.
mise x -- ./bin/wax documents run doc-standard /absolute/path/note.md --json

# Seed/scan one named binding now; naming a pipeline is an explicit operator
# action and may run even if its automatic enabled flag is false.
mise x -- ./bin/wax documents scan doc-standard --json

# Re-arm exhausted receipts; this does not grant permission to bulk backfill.
mise x -- ./bin/wax documents retry doc-standard --json

# Historical files intentionally skipped by seeding (only when requested).
mise x -- ./bin/wax documents backfill doc-standard --limit 1 --json
```

Confirm current CLI argument parsing in `components/wax/bin/wax` before inventing
flags. These commands mutate artifacts/receipts; none is a read-only dry run.
`backfill` is not an incident diagnostic or something to run automatically after
editing a skill. A named disabled pipeline supports explicit runs, but does not
make its worker binding active.

## Proof of success

Inspect `pipelines.worker`, binding `seeded_at`/`last_scan_at`, `recent_runs`, scoped
outcomes and document state. Receipt `completed` is stronger than service active
or an enabled YAML. Inspect the note for no-clobber/body/provenance preservation,
not just a title. Do not add fake audio fields to satisfy transcript invariants.
For failure details use CLI/operator ledger evidence without exposing bodies or
stderr on Holocene. Incidents route to `heyma-pipeline-doctor`.
