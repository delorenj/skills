# Frozen pipelines and n8n authoring

## Authoring is not execution

`components/n8n-nodes-heyma` is an owner-daemon CLI adapter, not a place to
reimplement Wax in TypeScript. The host n8n service runs via PM2; a directory
mount alone does not create host recording/systemd access. Keep absolute Wax
executable/root configuration and use `execFile` argv, never a shell command
constructed from document contents. Wax records execution outcomes and retries.

A Wax n8n graph is a **saved, unpublished authoring artifact**. Do not publish or
add a schedule/file/webhook trigger to make Wax execute it. Imported graphs
support only the static Wax wrapper/pass family plus annotations; native n8n
triggers/actions and dynamic expressions are rejected. Separate ordinary n8n
workflows may consume Wax Bloodbank events for notification/integration.

## Node family

| Node | Role |
|---|---|
| HeyMa | Existing recording start/stop control through CLI |
| Wax Pipeline | Configure (Authoring): trigger, folders, enabled, version, description, independent/halt policy; explicit compile/import/show/scan/run operations |
| Wax Enrichment Pass (`waxEp`) | Generic live-catalog pass selector, author by default; explicit one-item CLI preview |
| Generated `wax-pass-<slug>` | Each registered pass as its own node, derived from shared `WaxPassNodeBase`; same author/preview boundary |

**Author (Graph Only)** is the pass default: no item ID or CLI side effects.
**Run (Preview One Item)** is explicit and requires an audio or scoped document
key. Preview is not a substitute for compiled graph conditions; edit/export/import
the graph to test authoring semantics under the Wax runner.

## Draw the semantics

Both outputs are stock n8n `main` ports; custom `requirement` connection types
cannot connect to a normal main input.

| Source output | Label | Compiles to | Failure behavior |
|---|---|---|---|
| 0 | continue | `after` | Orders the target; source failure does not gate it |
| 1 | requires | `requires` | Orders and gates target on completed **or skipped** source at expected version |

Use `when` JSON list clauses and legacy `skipWhen` JSON object (not a list).
`when` clauses are ANDed, evaluated by Wax against meaning fields in frontmatter:
`equals`, `not_equals`, `in`, `not_in`, `exists`, `absent`, `empty`, `not_empty`,
`length`, `min_length`, `max_length`. A condition skip is not success/output.
Example: `[{"field":"classification","exists":true}]`. `skipWhen` shape:
`{"field":"classification","equals":"other"}`. Keep runtime routing controls
out of note frontmatter; read meaning fields instead.

`independent` keeps unrelated siblings running; `halt` stops at the first failed
pass and leaves the tail un-run. Dependencies remain local graph semantics,
not a reason to stop independent siblings. Zero wires in an n8n export means
zero edges; do not secretly inherit registry edges. YAML may inherit registry
edges only where a node did not explicitly override its edge fields.

## Compile and maintain

From the verified checkout (mutations require the task's authorization):

```bash
# Adopt a saved/exported n8n graph; exactly one wrapper and unique pass slugs.
mise x -- ./bin/wax pipeline import /absolute/path/export.json --name scenario-name --json

# Alternative: compile authored config/pipelines.d YAML by explicit name.
mise x -- ./bin/wax pipeline compile scenario-name --json

# Inspect safe graph, binding and outcome projections.
mise x -- ./bin/wax pipeline show scenario-name --json
```

Import validates nodes, indexes, folders, missing dependencies and cycles. A
changed import increments the compiled version; identical normalized input is a
no-op, including after a prior change incremented the version. Invalid input
must fail, not silently drop malformed edges.

Compiled definitions hold registry command/env configuration (secret **references**
only), versions, edges and conditions. Do not dump raw compiled definitions to a
hosted surface. Executable bytes remain live checkout code. `exported_snapshot`
means Wax knows the imported n8n export identity, **not** whether someone changed
the current editor draft. Registry drift is independently visible and may include
an intentional per-graph condition override. Never present that unknown as in-sync.

Exactly one enabled compiled `transcription` graph mints future audio plans.
Zero uses the legacy registry plan; multiple authorities are visibly refused and
fall back. Existing minted plans, including unfinished ones, stay intact. Bare
`pipeline compile` may compile every YAML definition and adopt an enabled audio
authority: prefer a named compile and inspect the intended activation effect.

A pass version/config edit does not recompile a graph, rerun historical notes,
or migrate a stored audio plan. There is currently **no general audio replan or
bulk upgrade command**. Deliberate per-item `wax ep run <slug> <item>` / `run-all`
can apply current registry passes; `ep sweep` retries failures, not every old
version. These do not replace the stored plan. Any new bulk replan needs a
separate explicit operation and contract; do not promise automatic upgrade.

## Native node maintenance / release gate

1. Change canonical pass definition and tests, then regenerate the per-pass node
   projection deliberately from the CLI: `npm run nodes:passes` inside the adapter.
2. Generated filenames and exported classes must match valid PascalCase JS
   identifiers (`WaxPassClassification.node.ts` → `WaxPassClassification`). n8n's
   native loader uses the basename to access the class; hyphenated basenames
   caused `pass is not defined` and prevented even legacy HeyMa from loading.
   Keep `description.name: wax-pass-classification` stable for saved workflows.
3. Shared icons resolve relative to each node directory; verify packed assets,
   not only source paths. No duplicate copied business logic per generated node.
4. Run `mise x -- npm test` and `mise x -- npm run lint`; the adapter suite must
   execute its real native PackageDirectoryLoader test and load **every** manifest
   node/icon. Also import the actual example workflows in isolated Wax tests.
5. Build/pack, install the tarball from a durable local package directory into
   `~/.n8n/nodes`, then authorized `mise x -- pm2 restart n8n`. A symlinked directory
   or successful `require()` is insufficient proof of runtime discovery.
6. Verify HTTP readiness (`/healthz/readiness`) and actual palette/configuration,
   ports and graph after startup. PM2 `online` is not readiness; preserve existing
   unrelated workflows. Re-import to Wax only when adopting the changed graph.

For current editor IDs/deployed tarball, use repo `CONTROL-SURFACE.md`, not stale
version literals in a skill. This capture procedure does not itself authorize
installing, publishing, replaying or restarting any service.
