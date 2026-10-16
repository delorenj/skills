---
name: hermes-project-avatar
description: Set a Hermes agent's Telegram avatar from the associated project's current branding. Use when asked to give a bot its project logo/avatar, verify what the project's real logo is, or create a design task when no logo exists.
version: 1.1.0
author: Jarad DeLorenzo
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [telegram, avatar, branding, logo, hermes, fleet]
    related_skills: [agent-fleet-operations, project-lifecycle, 33god-projects]
---

# Hermes project avatar

Make the agent's own Telegram bot wear the associated project's CURRENT branding,
never a stale file. One canonical skill for the whole fleet; never per-profile
copies.

## Non-negotiables

1. **Find the real current logo first.** A `logo.svg` / `logo.png` at the repo
   root is often stale. Trace what the live frontend actually renders: the
   header/brand component source, inline `<svg>` in JSX/TSX, favicon,
   `manifest.json` icons, and branding assets. When a site is served locally
   (e.g. a docker container), fetch the rendered HTML and confirm which markup
   is served. Prefer the exact inline SVG the header component uses, with fills
   resolved from the CSS custom properties / design tokens it references.
2. **The bot's identity is its own.** Call `getMe` and confirm the bot id AND
   username match the profile's registered bot (role.yaml / registry row). Never
   run against a shared/default token because the right one was missing.
3. **Secrets never surface.** The token is an `op://` reference in the
   profile's `config.yaml` `secrets.onepassword.env.TELEGRAM_BOT_TOKEN`. Read it
   inside a subprocess (e.g. `op read` captured into a variable), never print
   the token, request URL, full exception text, or argv containing it. Use
   urllib in-process; no third-party HTTP libs needed.
4. **No repeat uploads.** Check a receipt before uploading; write one after
   (see Receipts). Verification of an existing avatar is read-only
   (`getUserProfilePhotos` + `getFile` download), never a re-upload "to test".
5. **Bulk changes are out of scope.** This skill sets the avatar of the
   RUNNING agent's own bot only. Fleet-wide sweeps, new bots, or reactivating
   disabled/dead bots require explicit operator authority (agent-fleet-operations).

## Workflow

### 1. Resolve the project and its branding

- The associated project is the profile's project (`.project.json`, role.yaml,
  or the Skillex profile receipt's `project` field).
- Gather candidates in order: inline SVG in the header/brand component →
  favicon / manifest icons → static branding assets → root logo files. Record
  file paths + last-commit dates as evidence; a root `logo.svg` months older
  than the brand component is presumptively stale.
- Rendered-page proof beats filename: `curl` the served page and match the
  inline SVG markup against component source before choosing.

### 2. Persona check — BEFORE any replacement

Run this gate before converting or replacing anything, on every request, not
only when no logo exists:

- If the bot has an intentional named/persona branding (check the profile's
  role.yaml / registry row / prior receipts) that deliberately differs from
  the project's branding, PRESERVE the persona. Do not silently replace it
  with project branding.
- Only when there is a genuine, unintended conflict (persona looks stale,
  project branding was rebranded, or the persona was never intentional) ask
  ONE clarifying question; never unbounded back-and-forth.
- An explicit request to upload a specific EXISTING logo is authorized as-is.

### 3. Convert to a square raster

[scripts/telegram_avatar.py](scripts/telegram_avatar.py) is a CONVERTER ONLY —
it renders an SVG to a circle-safe, centered, square RGB JPEG on a requested
background. It is NOT a Telegram upload pipeline: it never touches a bot
token, uploads nothing, and verifies nothing. Upload and read-only
verification below are performed by the agent per the documented API.

The converter reads the mark's real viewBox (override with `--viewbox`),
pads it symmetrically so an inscribed circular crop keeps the mark intact,
preserves aspect ratio for non-square marks, and prints one JSON line whose
`content_hash` covers the source bytes plus every render parameter
(viewBox, pad, background, size). That hash is what makes receipt gating
sound: a NEW design written to the SAME file path produces a DIFFERENT hash.
Regression tests live in `tests/test_telegram_avatar.py`; run them with an
interpreter that has Pillow + pytest (e.g. `/usr/bin/python3 -m pytest`).
Inspect the result visually before uploading.

### 4. Upload and verify

- Endpoint: `POST https://api.telegram.org/bot<token>/setMyProfilePhoto`,
  multipart with field `photo` whose value is JSON
  `{"type":"static","photo":"attach://avatar"}` and file part `avatar` holding
  the JPEG bytes.
- Verify: `getUserProfilePhotos(<bot_user_id>, limit=1)` shows a NEW unique
  `file_unique_id` (compare against the pre-upload value), then `getFile` +
  download and visually compare the returned image. `result: true` alone is
  NOT verification. Verification is READ-ONLY (these two getters plus a
  download); never re-upload or call setters "to test".

### 5. Receipt

Write `<profile>/cache/avatar-telegram.json` (create `cache/` if needed):

```json
{
  "bot_id": 8297904211,
  "bot_username": "@HolocenePMBot",
  "source": "apps/web/app/hub/hub-app.tsx Brand() inline SVG (hub.css tokens)",
  "content_hash": "sha256:…",
  "render": {"pad": 5, "background": "#f1f0eb", "size": 1024},
  "checked_at": "2026-10-16T…Z",
  "photo_file_unique_id": "…",
  "verified_download": "/…/cache/scratch/<name>-telegram-avatar-verified.jpg"
}
```

**No-op only when ALL of these match, verified fresh this run:**

1. **Identity:** `getMe` returns the same bot id AND username as the receipt
   (the running profile's own bot — not a shared token's bot).
2. **Content:** the receipt's `content_hash` equals the hash from a FRESH
   `convert` run of the current source (same bytes AND same render
   parameters). Same source PATH alone is NOT enough — a new design written
   to the same file path must change the hash and trigger a re-upload. A
   receipt missing `content_hash` fails this check closed.
3. **Remote state:** `getUserProfilePhotos` right now returns the same
   `file_unique_id` as the receipt. A photo id recorded from a past run with
   no fresh readback does not gate anything.

Only when all three hold, report "already set" and skip the upload. Anything
else — different hash, different live photo id, missing receipt fields,
unreachable bot — means upload (or a truthful blocker). Never fabricate a
receipt retroactively: it is written only after an actual upload and
verification this run.

Missing creds or a disabled/dead bot is a truthful blocker, never a reason to
use another token or reactivate anything.

## No-logo branch — make it a priority, don't stall

When the project genuinely has no logo, do not stop at a placeholder:

1. Create/reuse a high-priority scoped design task on the project's board via
   its board tools (project-lifecycle / pilot `px`), respecting WIP limits.
2. Gather existing product/design context from the repo.
3. Propose a small concrete set of concepts (2–4) to the user; iterate on
   feedback until one is accepted. No unbounded retries.
4. Save the accepted design as the canonical source through the authorized
   worker, then run steps 3–5 above (convert, upload, verify, receipt).
5. Distinguish "waiting on user feedback" (task stays open) from "complete".
   New branding is selected WITH the user, never silently replacing site
   identity. Persona conflicts are already handled by the step-2 gate; if
   this branch is reached, no intentional persona branding exists.

## Evidence

Report receipts without secrets: bot id/username, source file + line, converted
raster path, Telegram photo file_unique_id, and verification download path.
Output counts, not tokens.
