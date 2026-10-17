# Node Catalog — community vs custom, and how to build custom

Read this when choosing a node for an action, or when building/packaging a custom
node. The governing rule: **use a community node for generic transport; build a
custom node only to enforce a DeLoNET convention a generic node cannot know.**

## Community vs custom — the decision

```
Does a community node already do this action?
├─ No  → build a custom node (see below) or use a subworkflow.
└─ Yes → does the action need to enforce a DeLoNET invariant
         (bloodbank envelope+schema, the Wax control-surface contract,
          delo endpoint conventions)?
         ├─ No  → USE THE COMMUNITY NODE. Do not rebuild transport that works.
         └─ Yes → build a thin custom node that wraps the transport AND enforces
                  the invariant. The invariant is the whole value-add.
```

A generic `n8n-nodes-nats` can publish to a subject — but it cannot know the
CloudEvents envelope, the `bloodbank.evt.*` subject binding, or the schema
registry. That gap is exactly why a custom Bloodbank node is worth a day of work
and a raw NATS node is not.

## What already exists (don't rebuild these)

Our own micro-packages, installed in `~/.n8n/nodes`:

| Package | Lives in | Nodes |
|---|---|---|
| `n8n-nodes-bloodbank` | `bloodbank` repo (`integrations/n8n-nodes-bloodbank`), installed by path | **Bloodbank** — schema-driven event publish (→ bloodbank-emit) |
| `n8n-nodes-heyma` | HeyMa repo (`components/n8n-nodes-heyma`), installed from a packed tarball | **HeyMa** (Recording), **Wax Enrichment Pass**, generated **Wax Pass · \<pass\>** (`wax-pass-*`), **Wax Pipeline** (→ the family section below) |
| `n8n-nodes-folder-curator`, `n8n-nodes-orwell`, `n8n-nodes-pdf-markdown` | their domain repos, installed by path | their own domains |

Community nodes also installed (partial, relevant): `n8n-nodes-minio` (S3/MinIO —
usable against `s3.delo.sh`/`drive.delo.sh` today), `@elevenlabs/n8n-nodes-elevenlabs`,
`n8n-nodes-planeso` (Plane), `n8n-nodes-plaud`, `n8n-nodes-palatine-speech`,
`n8n-nodes-mcp`, `n8n-nodes-qdrant`, `n8n-nodes-puppeteer`/`-playwright`,
`n8n-nodes-pushinator`, `n8n-nodes-resend`, `n8n-nodes-text-manipulation`.

Published community nodes worth knowing (verify version before pinning):
`n8n-nodes-nats` (raw NATS — envelope-blind), `n8n-nodes-minio`. **No**
`n8n-nodes-dapr` exists — and it would be useless here anyway (n8n has no Dapr
sidecar).

Do **not** build an `n8n-nodes-transcribe` / transcription-service node:
transcription and diarization belong to Wax, reached through the
`n8n-nodes-heyma` control adapters or the Wax CLI — never through a parallel
n8n-owned GPU service (→ wax-boundary).

## Self-contained is the destination — NOT `Execute Command`

A custom node's logic runs **in-process**, in its compiled `execute()`. It does NOT
shell out to a script on disk. Patterns, in order of preference:

- **In-process (default).** Do the work with n8n's helpers or a bundled client and
  return items. HTTP → `this.helpers.httpRequest(...)`. NATS → a ~6-line raw PUB over
  Node's `net.Socket` (zero deps), or the `nats` client bundled via rollup. S3 → the
  `minio`/AWS SDK client. Credentials via `this.getCredentials(...)`. The
  `n8n-nodes-hermes` node is the reference: properties generated from a schema table,
  work done via `httpRequest`, zero external processes.
- **Owner-daemon via its CLI (when the work already has an owner).** Heavy or
  native work that another service owns — Wax's GPU transcription/diarization,
  ledger, retries — is invoked through **that owner's CLI**, not duplicated as a
  new HTTP service and not inlined into `execute()`. The `n8n-nodes-heyma`
  package is exactly this pattern: each operation is one validated invocation of
  the absolute `wax` executable, so state transitions, receipts, and retries stay
  inside the owning daemon (→ the family section below, wax-boundary).
- **Execute Command calling a host CLI (transitional ONLY).** The lowest rung.
  Fine to ship SRP + bus emits fast, but it couples the workflow to files on one
  host and is the first thing to promote — the Bloodbank node does in-process
  today what the `bb-emit` CLI did behind an Execute Command.

## The `n8n-nodes-heyma` family — the Wax control adapters

The real, deployed exception to the in-process rule. One package
(`components/n8n-nodes-heyma` in the HeyMa repo, `@n8n/node-cli` toolchain,
nodes under `nodes/<Class>/`), four node kinds:

- **HeyMa** (`heyma`) — Recording control: Start/Stop Recording.
- **Wax Enrichment Pass** (`waxEp`) — the generic pass shell. Two operations:
  **Author (Graph Only)** is the default — pure authoring, zero side effects,
  no CLI call; **Run (Preview One Item)** is the explicit CLI-backed
  `wax ep run`. The Pass dropdown loads live from `wax catalog --json`, so a
  new `passes.d/*.yaml` appears without a package change.
- **Wax Pass · \<pass\>** (`wax-pass-<slug>`) — one generated node per
  registered pass, sharing the same Author/Run contract. Regenerate
  deliberately: `npm run nodes:passes` (reads the catalog, emits
  `nodes/WaxPass<Class>/`, updates the manifest). Generated files carry an
  AUTO-GENERATED banner and are committed.
- **Wax Pipeline** (`waxPipeline`) — pipeline-level operations: Configure
  (Authoring) (trigger, folders, policy, enabled — executing it is a pure
  preview), Compile, **Import Workflow** (`wax pipeline import` — the graph
  authoring path), Show, Scan Documents, Run Document.

**Native-loader requirements (package-killing if violated):**

- Every node lives at `nodes/<PascalClass>/<PascalClass>.node.ts`, and the
  **basename must equal the exported PascalCase class name** — n8n's native
  `PackageDirectoryLoader` instantiates `new (require(path).<basename>)()`
  inside a `vm.Script`; a kebab-case basename is not a valid identifier and
  kills the **entire package** load, legacy nodes included.
- `description.name` keeps the **stable kebab type** (`wax-pass-title-slug`) —
  that string is the identity stored in existing workflow exports; never
  rename it casually.
- `tests/nativeLoader.test.cjs` loads the whole built package with the REAL
  installed n8n-core loader — no mocks — and asserts every manifest entry
  loads and every `file:` icon resolves on disk. Keep that test green.

**Graph-authoring ports.** Pass nodes expose **two stock `main` output ports**:
`continue` (source output **0**, ordering only) and `requires` (source output
**1**, success-gated). Both are ordinary main connections, so the editor wires
and renders them natively; the edge *kind* travels as the source output index,
and `wax pipeline import` maps source output 0 → `after` edges, source output
1 → `requires` edges. Manual execution emits on `continue` only, so clicking
Execute can never double-run downstream work wired to `requires`.

Boundary recap: every operation is one validated invocation of the absolute
`wax` executable (never PATH lookup); nodes never execute pass scripts, read
`passes.d/` or the ledger, or schedule anything. Graphs authored with these
nodes are **never published** — export → `wax pipeline import` → Wax runs the
compiled definition (→ wax-boundary; operation → `wax-pipeline`).

## Build the node inside its domain repo, generated on deploy

Package the node **in the repo that owns the contract** so node and contract can't
drift:

- `n8n-nodes-bloodbank` lives in the `bloodbank` repo (e.g.
  `bloodbank/integrations/n8n-nodes-bloodbank/`). Its event dropdown is **generated
  from `schemas/bloodbank/**`** at build time (`npm run codegen`; labels read
  `Repo · On Task Created (bloodbank.repo.task.created)`), so
  adding a schema + rebuild = the node offers the new event — the same trick the
  hermes node uses with `toolSchemas`.
- Wire a **deploy hook** (mise task / git hook / CI in the domain repo): on change,
  `codegen → build → install into ~/.n8n/nodes → restart n8n`. Restart with
  `mise x -- pm2 restart n8n` (it resolves the real pm2 and the daemon's
  `PM2_HOME`; a bare `pm2` from a fresh shell does not — see gotchas). The node
  then regenerates whenever the contract changes.

## The scaffold — clone `n8n-nodes-hermes`

`/home/delorenj/code/n8n-nodes-hermes/` is the proven template: rollup build +
vitest + eslint + release-it, `src/{credentials,nodes}/`, `.project.json`
(a pjangler CommonProject). Bootstrap a new node package from it:

1. Copy the repo skeleton (`package.json`, `rollup.config.ts`, `tsconfig.json`,
   `eslint`, `vitest.config.ts`, `.project.json`, `src/index.ts`) into a new
   `n8n-nodes-<thing>` repo; rename the package and the `n8n.nodes`/`n8n.credentials`
   entries in `package.json`.
2. Implement `src/nodes/<Name>/<Name>.node.ts` (the `INodeType` — `displayName`,
   `properties`, `execute`) and, if it needs auth, `src/credentials/<Name>Api.credentials.ts`.
   Whatever layout or toolchain, the loader's "manifest basename = exported
   PascalCase class" rule applies (a newer `@n8n/node-cli` package like
   n8n-nodes-heyma uses `nodes/<Class>/` instead of `src/nodes/`).
3. Keep the node **thin**: it wraps one transport and enforces one invariant. Push
   heavy logic (schema loading, client plumbing) into a lib the node calls, not
   into `execute` inline. Mirror `requestBuilder.ts`/`toolSchemas.ts` separation.
4. `npm run build` (rollup → `dist/`), `npm test`, `npm run lint`.

Use the `n8n-*` MCP skills (`n8n-node-configuration`, `n8n-validation-expert`) for
exact `INodeTypeDescription` parameter shapes — this skill governs *architecture*,
those govern *syntax*.

## Install / restart loop (this instance)

n8n is a PM2 service (`mise x -- pm2 restart n8n`), custom nodes live in
`~/.n8n/nodes`. The **verified** install is a packed tarball — build it, keep
the tarball in a durable local package dir, install that tarball (this is how
`n8n-nodes-heyma` ships: `~/.local/share/wax/packages/n8n-nodes-heyma-0.2.0-1f77a72.tgz`):

```bash
# from the node package, after a successful build:
npm run pack:check                        # inspect what would ship
npm pack                                  # writes n8n-nodes-<thing>-<ver>.tgz
mv n8n-nodes-<thing>-<ver>.tgz <durable-package-dir>/
cd ~/.n8n/nodes && npm install <durable-package-dir>/n8n-nodes-<thing>-<ver>.tgz
mise x -- pm2 restart n8n                 # node appears in the picker after restart
```

A local directory install (`npm install <repo-path>`, as `n8n-nodes-bloodbank`
uses) also works when the repo itself is durable on this host — but a symlink
is **not** sufficient proof of n8n discovery; after any install, confirm the
node loads (the nativeLoader test is the strongest check). Bump the package
version on every change you install so n8n's node cache doesn't serve a stale
build (→ mise-versioning).
