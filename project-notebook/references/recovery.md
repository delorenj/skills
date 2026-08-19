# Project Notebook recovery

## Diagnose before repairing

Start with `pj notebook status [repo]`, then run
`pj notebook audit [repo]`. Use `--local-only` when remote observation is not
authorized or available. Follow the exact bounded `next_actions` returned by
the command.

For `PROJECT NOTEBOOK OVERVIEW DRIFT`, treat the stored Overview as stale. Run
the reported `notebook.overview-note` audit and use
`pj notebook migrate [repo] --apply --live` only when same-note remote repair is
intended. Do not create a replacement Overview ID and never copy notebook text
back over authoritative repository documents.

## Capture receipts and admission pressure

List visible work with `pj notebook capture list [repo]`. Receipt states are
`queued`, `processing`, `succeeded`, `failed`, `retry-exhausted`, and
`blocked-missing-baseline`. Retention pressure is a current admission finding,
not another state.

Never delete or compact unresolved receipts. Succeeded receipts may age out
under configured retention. At a count or byte cap, the refused session has no
receipt and was not captured; use the exact list/retry actions in the bounded
diagnostic. Admission resumes only below both prospective caps.

One explicit `pj notebook capture retry RECEIPT_ID [repo]` invocation grants
one attempt on that same failed or retry-exhausted receipt. A
`blocked-missing-baseline` receipt additionally needs a validated explicit
`--baseline GIT_REF`.

## Restore hook settings

Projector mutations store the exact prior JSON bytes under:

```text
$XDG_STATE_HOME/pjangler/notebook/v1/hook-install/snapshots/<sha256>.json
```

The fallback state home is `~/.local/state`. Projector-owned directories are
mode `0700`; lock and snapshot files are mode `0600`. An absent original target
is represented by the empty JSON object snapshot. Snapshot filenames are
content-addressed, so repeated identical preimages do not create duplicates.
All projector state and target mutations are relative to no-follow directory
descriptors, so replacing an ancestor pathname with a symlink cannot redirect
the snapshot, temporary file, or final atomic replacement.

Inspect the target and snapshot before manual restoration. Do not print their
contents because operator settings may be sensitive. `uninstall` is normally
safer: it removes only recognized Project Notebook hooks and prunes only the
group/event made empty by that removal. It leaves the skill source, remote
notebook, bindings, Bloodbank, Hindsight, Git checkpoint, notifications, and
all other foreign settings intact.
