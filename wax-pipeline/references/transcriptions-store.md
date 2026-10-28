# Transcriptions store

Read for transcript version history, semantic search, store lag or provisioning.
Design of record: `~/HeyMa/components/wax/docs/TRANSCRIPTIONS-STORE.md` (section
G lists where the build followed reality over the plan). Code:
`components/wax/src/wax/transcriptions/`.

## What it holds

Postgres `transcriptions`, schema `tx`, on the host cluster (`localhost:5432`,
never `postgres.delo.sh` or a LAN IP). One identity per vault note (documents
excluded; Hermes STT and legacy notes included), one append-only version per
transcription, completed pass, backfill and detected vault edit. Skipped and
failed runs are `tx.pass_run` (pass history) rows only. Every version restores
byte-for-byte. Search (`tx.search`) reads only the head tables, so a hit is
always the latest version. Embeddings: local Ollama `qwen3-embedding:8b`,
pinned by digest, `halfvec(2048)`; frontmatter-only passes cost zero chunk
embeddings.

Roles: `transcriptions_owner` (migrations), `transcriptions_app` (waxd + CLI),
`transcriptions_ro` (outside readers). Passwords are 1Password DATABASE items
"Transcriptions Postgres Owner|App|RO" in DeLoSecrets, referenced by item UUID.

## How data gets there

- `passes.run` and `transcribe_adapter` enqueue a snapshot in
  `var/wax.db` `transcript_snapshots`, then project best-effort behind a 300 s
  breaker. They never raise.
- waxd thread `wax-transcriptions` (15 s): drain, reconcile the vault every
  600 s, embed when no item holds the GPU. The moment an item starts it
  unloads the embedder (Ollama `keep_alive: 0`; default keep-alive 2m): a
  resident 5.3 GB model starves whisper's 5,000 MB VRAM floor and pushes
  transcription to CPU (design G.7).
- Config: environment first, then the INSTALLED waxd unit's `Environment=`
  lines (`WAX_TRANSCRIPTS_DSN`, `*_PASSWORD_OP`, `WAX_TRANSCRIPTS_OWNER_*`,
  `WAX_EMBED_*`). `WAX_TRANSCRIPTS=0` is the rollback switch.

## Commands

```bash
wax transcripts sync --dry-run --json      # what projection + reconcile would do
wax transcripts sync [--embed]             # project the queue, reconcile/backfill the vault
wax transcripts sync --check               # parity disk/ledger/store; exit 2 on drift
wax transcripts search "phone with the kids" -n 3 [--since 2026-10-01 --tag x --classification meeting --origin wax --lexical]
wax transcripts show <item|#id|note name> [--version N] [--raw]
wax transcripts history <ref>              # versions + pass runs + path history
wax transcripts migrate [--dry-run]        # schema, owner role
wax transcripts embed [--limit N]          # embed pending vectors now
```

mise: `wax:transcripts:sync|search|migrate`, `wax:test:pg`.

## Diagnosis

`wax status` prints `transcripts <state> (queued N, embed pending M)`:
`disabled` (no DSN or `WAX_TRANSCRIPTS=0`), `ok`, `lagging` (queue older than
600 s, the last tick could not connect, no or a stale waxd tick, or waxd still
ticking `disabled` because the unit changed after it started: restart waxd), `error` (queue older than
`WAX_TRANSCRIPTS_LAG_FAIL_S`, embed backlog older than 6 h, or a model digest
mismatch; `wax status` exits 2). `wax doctor` has seven `transcripts *` probes:
store reachable + schema current, projection drained, parity, invariants,
embeddings current, embedder digest, and the vector index (FAIL only when the
canonical ANN plan cannot use `chunk_vector_current_hnsw`; the detail also says
whether `tx.search`, at its own `ef_search = 200`, plans HNSW or an exact scan,
which is what it does at today's ~7.3k chunks and is correct).

Live since 2026-10-28 on big-chungus: DeLoSecrets items Owner
`xgnmsebepsybgd627rtudh2iuq`, App `dncjuqof2przgk6me6ct6f2xma`, RO
`jdt6hd7awwzxd376agaszc7z3u` (outside readers use RO). Numbers and evidence:
design section G.6.

On a fresh install, a placeholder `op://DeLoSecrets/REPLACE_WITH_*_ITEM_UUID/password` in the unit
means provisioning has not run: `deploy/provision-transcriptions` (dry run by
default, `--apply` to create items, roles, database and extensions and fill the
placeholders), then commit the unit, `deploy/install-systemd-user`,
`wax transcripts migrate`, restart waxd, and follow the F.1 backfill runbook.

## Do not

- Re-run passes to "fix" store lag; the snapshot is already queued.
- Point tests, a scratch ledger or a copied vault at the real DSN: versions are
  append-only and cannot be deleted. The Wax suite pins
  `WAX_TRANSCRIPTS_UNIT_FILE` to a nonexistent path for this reason.
- Write a password into the unit, `.env.op` or any file; DSNs stay password-less.
- Change the embedding model by environment: it is a migration (new model row,
  shadow re-embed, swap).
