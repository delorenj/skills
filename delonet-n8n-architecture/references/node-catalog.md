# Node Catalog — community vs custom, and how to build custom

Read this when choosing a node for an action, or when building/packaging a custom
node. The governing rule: **use a community node for generic transport; build a
custom node only to enforce a DeLoNET convention a generic node cannot know.**

## Community vs custom — the decision

```
Does a community node already do this action?
├─ No  → build a custom node (see below) or use a subworkflow.
└─ Yes → does the action need to enforce a DeLoNET invariant
         (bloodbank envelope+schema, vault inbox/wiki/triage semantics,
          the transcribe structured-output contract, delo endpoint conventions)?
         ├─ No  → USE THE COMMUNITY NODE. Do not rebuild transport that works.
         └─ Yes → build a thin custom node that wraps the transport AND enforces
                  the invariant. The invariant is the whole value-add.
```

A generic `n8n-nodes-nats` can publish to a subject — but it cannot know the
CloudEvents envelope, the `bloodbank.evt.v1.*` subject binding, or the schema
registry. That gap is exactly why a custom Bloodbank node is worth a day of work
and a raw NATS node is not.

## What already exists (don't rebuild these)

Installed in `~/.n8n/nodes` (partial, relevant): `n8n-nodes-minio` (S3/MinIO —
usable for the archive step against `s3.delo.sh`/`drive.delo.sh` today),
`@elevenlabs/n8n-nodes-elevenlabs`, `n8n-nodes-planeso` (Plane), `n8n-nodes-plaud`,
`n8n-nodes-palatine-speech`, `n8n-nodes-mcp`, `n8n-nodes-qdrant`,
`n8n-nodes-langchain`, `n8n-nodes-puppeteer`/`-playwright`, `n8n-nodes-pushinator`,
`n8n-nodes-resend`, `n8n-nodes-text-manipulation`.

Published community nodes worth knowing (verify version before pinning):
`n8n-nodes-nats` (raw NATS — envelope-blind), `n8n-nodes-obsidian` (a starting
reference for a vault node), `n8n-nodes-minio`. **No** `n8n-nodes-dapr` exists —
and it would be useless here anyway (n8n has no Dapr sidecar).

## What to build (per-node micro-packages)

One node = one npm package `n8n-nodes-<thing>`, independently versioned. Priority
order for the pipeline:

| Package | Node does | Enforces (the value-add) |
|---|---|---|
| `n8n-nodes-bloodbank` | Publish a bloodbank event | Reads `bloodbank/schemas/**`, presents defined events as a dropdown, builds + validates the CloudEvents envelope, publishes to the bound subject. → bloodbank-emit |
| `n8n-nodes-transcribe` | Audio → structured transcript | The `{mdPath,text,segments,duration,model,lang,speakers}` output contract; faster-whisper + diarization; local/remote host selection. Wraps the thinned `bin/transcribe`. |
| `n8n-nodes-vault` | Write/route notes into the Obsidian vault | Knows `inbox` vs `wiki`; a `triage` boolean that sets a note status the triage flow skips; frontmatter conventions |
| `n8n-nodes-delo-minio` *(optional)* | S3 put/get against delo | Pre-wired `delo`/`drive` endpoints + the `recordings/YYYY-MM-DD/HHMMSS-<file>` key convention — build only if the generic minio node's UX proves painful |

## Self-contained is the destination — NOT `Execute Command`

A custom node's logic runs **in-process**, in its compiled `execute()`. It does NOT
shell out to a script on disk. Patterns, in order of preference:

- **In-process (default).** Do the work with n8n's helpers or a bundled client and
  return items. HTTP → `this.helpers.httpRequest(...)`. NATS → a ~6-line raw PUB over
  Node's `net.Socket` (zero deps), or the `nats` client bundled via rollup. S3 → the
  `minio`/AWS SDK client. Credentials via `this.getCredentials(...)`. The
  `n8n-nodes-hermes` node is the reference: properties generated from a schema table,
  work done via `httpRequest`, zero external processes.
- **Service-client (for heavy/native work).** Some work can't live in the node —
  faster-whisper is a Python+GPU pipeline. Run it as a **service** (HeyMa already has
  a Dockerfile) and make `n8n-nodes-transcribe` a thin HTTP/gRPC client to it. Bonus:
  the GPU work runs where the GPU is, decoupled from n8n.
- **Execute Command calling a host CLI (transitional ONLY).** The lowest rung. Fine
  to ship SRP + bus emits fast (as the v1 transcribe rebuild did with `bb-emit` /
  `secure-source`), but it couples the workflow to files on one host and is the first
  thing to promote. `bb-emit`'s envelope+PUB logic becomes `n8n-nodes-bloodbank`'s
  `execute()`; `secure-source`'s mc logic becomes the MinIO node's `execute()`.

## Build the node inside its domain repo, generated on deploy

Package the node **in the repo that owns the contract** so node and contract can't
drift:

- `n8n-nodes-bloodbank` lives in the `bloodbank` repo (e.g.
  `bloodbank/integrations/n8n-nodes-bloodbank/`). Its event dropdown is **generated
  from `schemas/bloodbank/v1/**`** at build time (codegen → `eventSchemas.ts`), so
  adding a schema + rebuild = the node offers the new event — the same trick the
  hermes node uses with `toolSchemas`.
- Wire a **deploy hook** (mise task / git hook / CI in the domain repo): on change,
  `codegen → build → install into ~/.n8n/nodes → restart n8n`. Restart uses
  `PM2_HOME=/home/delorenj/.pm2` and the node-dir `pm2` (the mise `pm2` shim is
  broken — see gotchas). The node then regenerates whenever the contract changes.

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
3. Keep the node **thin**: it wraps one transport and enforces one invariant. Push
   heavy logic (whisper, schema loading) into a lib the node calls, not into
   `execute` inline. Mirror `requestBuilder.ts`/`toolSchemas.ts` separation.
4. `npm run build` (rollup → `dist/`), `npm test`, `npm run lint`.

Use the `n8n-*` MCP skills (`n8n-node-configuration`, `n8n-validation-expert`) for
exact `INodeTypeDescription` parameter shapes — this skill governs *architecture*,
those govern *syntax*.

## Install / restart loop (this instance)

n8n is a PM2 service (`pm2 restart n8n`), custom nodes live in `~/.n8n/nodes`.

```bash
# from the node package, after a successful build:
npm pack                                   # or: keep dist/ and install by path
cd ~/.n8n/nodes && npm install /home/delorenj/code/n8n-nodes-<thing>
pm2 restart n8n                            # node appears in the picker after restart
```

For fast dev iteration, `npm link` the package into `~/.n8n/nodes` and
`pm2 restart n8n` after each `npm run build`. Bump the package version on every
change you install so n8n's node cache doesn't serve a stale build (→ mise-versioning).
