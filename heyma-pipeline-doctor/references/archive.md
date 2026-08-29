# S3 / MinIO archive — playbook

**The audio is the irreplaceable artifact and is never deleted.** Everything in
this file follows from that. A transcript is recomputable; a recording is not.

Symptoms that land here: audio missing from S3; `cause=archive_failed`; files
piling up in `recovered/unbacked/`; the sidecar has no transcript projection.

## The policy

Archive happens **before** transcription, not after. The order is deliberate: the
expensive, failure-prone step must never stand between a recording and its backup.

1. `mc cp` the source to `s3://recordings/YYYY-MM-DD/<sha12>-<name>`
2. verify (retried), then write two sidecars:
   - `<key>.wax.json` — the item's record beside the object
   - `.by-content/<sha256>.json` — content-addressed, so a rebuild can find an
     object whose name it does not know
3. only after a **live S3 HEAD re-verify** is the audio moved to `archive/YYYY/MM/`
4. if S3 fails: the source is **kept** *and* stashed in `recovered/unbacked/`, and
   transcription proceeds anyway

## The only real emergency

Audio on this disk with no byte-verified S3 copy:

```bash
sqlite3 -readonly "file:$HOME/HeyMa/var/wax.db?mode=ro" \
  "SELECT i.path FROM items i
     LEFT JOIN backups b ON b.item_id=i.item_id AND b.verified_at IS NOT NULL
    WHERE b.item_id IS NULL AND i.state NOT IN ('complete','skipped');" \
 | while IFS= read -r p; do [ -f "$p" ] && echo "UNBACKED: $p"; done
```

Anything printed: **do not move or delete it.** Fix the archive path first, then
`bin/wax archive <path>` per file, or `bin/wax drain`.

## Triage

```bash
mc alias list                 # is 'delo' even configured?
mc ready delo                 # reachable?
mc admin info delo            # capacity, drives, erasure config
mc ls delo/recordings/ | tail
```

Credentials come from the environment / 1Password, never a file. If `mc` works for
you interactively but waxd's archive fails, compare environments — waxd is a user
unit and gets no login shell.

### Verify a specific object end to end

```bash
K=$(sqlite3 -readonly "file:$HOME/HeyMa/var/wax.db?mode=ro" \
      "SELECT s3_key FROM backups ORDER BY verified_at DESC LIMIT 1")
mc stat "delo/recordings/$K"
mc stat "delo/recordings/$K.wax.json"
mc cat  "delo/recordings/$K.wax.json" | python3 -m json.tool | head -30
```

A ledger row claiming a verified backup that S3 no longer agrees with means the
object was deleted, truncated, or overwritten — exactly the class of failure the
verify loop exists to prevent.

## Known gaps — do not mistake these for faults you introduced

- **Verification is size-only in places.** WAX-DESIGN.md claimed
  "mc cp + ETag verify ×3"; the code compared remote size. Real ETag comparison
  only works for single-part uploads — a multipart ETag contains `-` and is not a
  plain MD5, which is why it was originally dropped. Check what the code does now
  before trusting either the doc or this file.
- **Transcript linkage was gated on the title-slug pass.** `link_transcript` only
  ran when an enrichment pass returned a slug, so an LLM outage silently disabled
  the audio↔transcript link and the `Transcription=Complete` tag. Since
  WAX-DESIGN.md makes an absent tag mean "assume no transcript", that gap is worse
  than cosmetic — it corrupts disaster recovery. Linkage should be gated on
  *a transcript exists for a backed-up item*, nothing else.

## Durability — worth stating plainly

`mc admin info delo` reports **one drive, `EC:0`, un-versioned**, and MinIO's
`/data` is a bind mount of `/home/delorenj/DeLoDrive` on `/dev/nvme0n1p2` —
**the same partition the original audio lives on.**

So the archive protects against accidental deletion, a bad transcode, and
overwrite. It does **not** protect against losing that disk: both copies die
together. Bucket versioning and an off-device replication target are the fix; the
free-space floor (`WAX_MIN_FREE_BYTES`, default 5 GiB) also fires far too late to
be a useful warning on a 3.4 TB volume.

When the drive fills, every new item halts at state `failed` with a copy in
`recovered/unbacked/` — safe, but stopped, and historically nothing on screen said so.
