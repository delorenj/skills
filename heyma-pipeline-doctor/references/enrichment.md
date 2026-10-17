# Enrichment passes — playbook

Symptoms that land here: transcripts keep bare timestamp filenames instead of
summary slugs; no `title`/`summary` in frontmatter; the vault taxonomy is missing;
`wax.passes.<slug>.state: failed`; a pass stuck `dependency_failed`; the S3
sidecar has no transcript projection.

The full pass contract (registry fields, result JSON, events, retries,
quarantine) lives in `components/wax/docs/ENRICHMENT-PASSES.md` — read it for
semantics; read this for triage. Authoring a *new* pass is the
`create-enrichment-pass` skill.

## How the stage actually works

Pass YAML lives in `components/wax/config/passes.d/*.yaml` (**not** repo-root
`passes.d/`). The registry is re-read on every call — a new or edited YAML and
a new executable take effect with no restart for live-registry operations.
Compiled graphs and minted plans retain their configuration until explicit
adoption; changing an executable changes its bytes even for an old plan. The Python runner
(`src/wax/passes.py`, `finalize.py`) is imported once into `waxd` and needs
`systemctl --user restart waxd`. Write YAML atomically: a parse error silently
disables that pass, and a malformed `requires`/`after`/`when`/`skip_when` gets
that pass — and only it, plus anything gated on it — **quarantined**
(`!! QUARANTINED: <reason>` in `wax ep list`, a FAIL in `wax doctor`).

For each new item, the worker mints a **plan** — from the frozen definition of
the one compiled+enabled `transcription` pipeline if that exists, else the
legacy live-registry plan (every `enabled: true, auto: true` pass). The runner
walks the plan in dependency order (a depth-first walk over `requires` +
`after`; unordered passes run alphabetically), expanding `{component_root}`,
`{md_path}`, `{item_id}`, `{home}` and running each `command` with the yaml's
`env:` injected. On `rc == 0` it parses the child's last stdout line as a
declarative result (`wax.ep.v1`: `frontmatter` proposals, `transcript.slug`
rename, optional `state`/`reason_code`, optional `events`), records a `passes`
row, and emits the `task.*` command events.

Key gates to know while triaging:

- **Plan gate.** `transcription.completed` (the summary fact) is written only
  when *every planned pass* is `completed`/`skipped` at the plan's version.
  A failed pass leaves the item `enrichment_pending` — not parked complete.
- **Subgraph gate.** A completed pass's declared events publish as soon as its
  own `requires` subgraph completes (`finalize.publish_pass_events()`) — a
  wedged 24 h sibling no longer withholds tickets that are done. Events may
  therefore legitimately precede `transcription.completed` in the outbox.
- **Attempt bound.** A failed pass retries under the sweep's attempt budget
  (default 3; `dependency_failed` exempt). A pass that fails its final attempt
  is **exhausted**: the runner stamps `passes.exhausted_at` and emits one
  `bloodbank.audio.task.exhausted` dead-letter event per (item, slug, version).
- **Versioning.** Automatic runs skip a pass already completed at the same
  `version` and definition. A registry version bump alone does not recompile a
  graph, migrate an existing plan or rerun history; use explicit adoption/retry.

Enabled and auto today: `frontmatter-stamp`, `clipboard-copy`,
`classification`, `title-slug`, `diarization` (the compiled
`transcript-standard` graph runs exactly these five as independent siblings).
Implemented but deliberately disabled: `project-extraction` and `ticketable`.
Unbuilt placeholders (do not "fix"): `domain-curation`, `mem-ops`,
`transcription-enhance`, `wikification`. A pass declaring
`capabilities: [document]` can also run over plain Markdown documents —
document runs are the `wax-pipeline` skill's territory.

## Triage order

### 1. What does the ledger say, in its own words?

```bash
sqlite3 -readonly "file:$HOME/HeyMa/var/wax.db?mode=ro" \
  "SELECT item_id, ep_slug, attempt, state, reason_code, substr(detail,1,160), updated_at
     FROM passes WHERE state<>'completed' ORDER BY updated_at DESC LIMIT 15;"
```

`detail` is the child's stderr. It is almost always the whole answer. If
`reason_code` is `nonzero_exit` with an unhelpful detail, the pass is not
classifying its own failures — fix that before debugging further, or you will do
this twice. `dependency_failed` means the pass never ran: read the `waiting on
<dep> (<state>@v<n>)` note entry and fix the *dependency* first.

### 2. Is the right registry loaded — and is anything quarantined?

```bash
bin/wax ep list
```

Look for `!! QUARANTINED` lines (a malformed field or a missing/disabled
dependency parks the pass and its dependents; fixing the YAML lifts it live) and
confirm the expected slugs are present. If the registry itself is wrong, the
runner may be reading the wrong `passes.d` — check `WAX_PASSES_DIR` and
`component.ROOT`. Repo-root `passes.d/` is a decoy the runner never loads.

`mise x -- ./bin/wax doctor` probes the registry, quarantine state, the title
provider's key and model, and every enabled pass's `emits` schemas in one run —
start there before hand-tracing.

### 3. Run the pass by hand — this is the fastest signal available

Portable pass cores read a document and print JSON proposals. They must not
mutate its bytes, but model calls can cost money and host-effect adapters such
as clipboard-copy have side effects. Prefer recorded reason codes and isolated
fixtures first. Run a real provider-backed pass directly only when that probe
is authorized; the direct call bypasses Wax receipts and is not a retry.

Remember a failed pass's `reason_code=<code>` is the **first** stderr line.

### 4. Re-drive after fixing

Retries are not manual-only: the worker sweeps failed passes every
`WAX_SWEEP_INTERVAL_S` (default 900 s) with the same attempt bound, so a fixed
transient (provider outage, dead key) self-heals. When you fixed a durable
cause and want it now:

```bash
bin/wax ep run title-slug <item_id>     # one pass on one item
bin/wax ep run-all <item_id>            # every planned pass for one item
bin/wax ep sweep --dry-run              # everything stranded, preview
bin/wax ep sweep --max-attempts 3       # actually re-drive
```

An *exhausted* pass (`passes.exhausted_at` set) is out of the sweep budget on
purpose — it already announced itself via `bloodbank.audio.task.exhausted`.
Re-arm it by bumping the pass's `version:` (a fixed definition announces
afresh) or by an explicit `wax ep run`. For a planned item the version is
frozen with its plan, so the explicit run is the retry path.

## title-slug specifically

It calls a hosted **OpenAI-compatible** endpoint. Provider is pure
configuration in `config/passes.d/title-slug.yaml` — base URL, model id, and a
dedicated `op://` inference-key reference resolved at call time (today the
AutomaticAI gateway and HeyMa's own key; read the live YAML, not this file,
for current values). Never point a pass at a shared or borrowed key, and never
put a management key where inference belongs — a provisioning key answers 401
`User not found` and looks like a dead account.

`wax doctor` resolves and probes all three: the base, the pinned model against
`{base}/models`, and the key — printing *which* field answered, never a
resolved secret.

**Context length is not a selection criterion.** The pass truncates to
`MAX_CONTEXT_CHARS` (24,000 chars, ~6k tokens) before anything leaves the
process, keeping head and tail because meetings state their purpose early and
their decisions late. Even a 3-hour meeting fits. Choose on titling quality
and price.

### Failure modes, by `reason_code`

| `reason_code` | Means | Do |
|---|---|---|
| `missing_model` | the pinned model is not served | `wax doctor` (model probe), then repin `WAX_TITLE_MODEL` in the yaml |
| `no_api_key` | the op:// reference did not resolve | `op whoami`; confirm `OP_SERVICE_ACCOUNT_TOKEN` is in waxd's environ (`tr '\0' '\n' < /proc/$(systemctl --user show -p MainPID --value waxd)/environ \| grep -c OP_`) |
| `provider_auth_rejected` | 401 — a statement about one specific credential | check which key reference resolved; a management/provisioning key answers like this |
| `provider_http_error` | other 4xx/5xx | read the marker in `detail`; provider bodies are deliberately not echoed wholesale |
| `provider_unreachable` | DNS/TCP/TLS | network, or a wrong base URL |
| `timeout` | exceeded the request budget | usually a model too large for the host, or a stalled provider |
| `provider_bad_response` | 200 but unusable JSON | the model ignored the schema; try one with real structured-output support |
| `result_apply_failed` | result violated the contract (e.g. events on a document run, unlisted emit) | fix the pass's result, not the provider |
| `run_error` | the script itself blew up | run it by hand (step 3) |

## Things that look like enrichment failures but are not

- **A transcript with a real title and summary already** — the pass
  short-circuits and never calls the provider. Grounded values a human or an
  earlier run set are never clobbered (`clobber:` is the explicit exception).
  That is correct.
- **A slug collision** — the rename is collision-safe; a suffixed filename is
  the design working.
- **`skipped` / `condition_unmet` or `condition_matched`** — a `when`/`skip_when`
  clause decided this pass does not apply to this note. Skips satisfy `requires`
  and finalization.
- **`skipped` / `inapplicable_capability`** — the pass declares no `document`
  capability and this is a document run. Expected; ordering still holds.
- **`dependency_failed`** — the gate doing its job. Fix the dependency; the
  dependent sweeps automatically once it completes.
- **The unbuilt placeholders** (`domain-curation`, `mem-ops`,
  `transcription-enhance`, `wikification`) — disabled and empty by design.
- **`frontmatter-stamp` completed but `title-slug` failed** — expected.
  Siblings are independent; one failing must not stop the other. The item waits
  in `enrichment_pending`, it does not park complete.
