---
name: hermes-project-avatar
description: Set a Hermes agent's Telegram avatar from the associated project's current branding. Use when asked to give a bot its project logo/avatar, verify what the project's real logo is, or create a design task when no logo exists.
version: 1.0.0
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

### 2. Convert to a square raster

`rsvg-convert` + Pillow (both present on this host) — see
[scripts/telegram_avatar.py](scripts/telegram_avatar.py) for the full pipeline.
Key points: pad the viewBox symmetrically (e.g. `0 0 24 24` → `-5 -5 34 34`)
so a circular crop keeps the mark intact, flatten onto a background color from
the design tokens, and emit RGB JPEG ~1024×1024. Inspect the result visually
before uploading.

### 3. Upload and verify

- Endpoint: `POST https://api.telegram.org/bot<token>/setMyProfilePhoto`,
  multipart with field `photo` whose value is JSON
  `{"type":"static","photo":"attach://avatar"}` and file part `avatar` holding
  the JPEG bytes.
- Verify: `getUserProfilePhotos(<bot_user_id>, limit=1)` shows a NEW unique
  `file_unique_id` (compare against the pre-upload value), then `getFile` +
  download and visually compare the returned image. `result: true` alone is
  NOT verification.

### 4. Receipt

Write `<profile>/cache/avatar-telegram.json` (create `cache/` if needed):

```json
{
  "bot_id": 8297904211,
  "bot_username": "@HolocenePMBot",
  "source": "apps/web/app/hub/hub-app.tsx Brand() inline SVG (hub.css tokens)",
  "checked_at": "2026-10-16T…Z",
  "photo_file_unique_id": "…",
  "verified_download": "/…/cache/scratch/<name>-telegram-avatar-verified.jpg"
}
```

Before any upload, read the receipt: if it names the same source and a current
photo id, report "already set" instead of re-uploading. Missing creds or a
disabled/dead bot is a truthful blocker, never a reason to use another token or
reactivate anything.

## No-logo branch — make it a priority, don't stall

When the project genuinely has no logo, do not stop at a placeholder:

1. Create/reuse a high-priority scoped design task on the project's board via
   its board tools (project-lifecycle / pilot `px`), respecting WIP limits.
2. Gather existing product/design context from the repo.
3. Propose a small concrete set of concepts (2–4) to the user; iterate on
   feedback until one is accepted. No unbounded retries.
4. Save the accepted design as the canonical source through the authorized
   worker, then run steps 2–4 above.
5. Distinguish "waiting on user feedback" (task stays open) from "complete".
   An explicit request to upload an EXISTING logo is authorized as-is; new
   branding is selected WITH the user, never silently replacing site identity.
   If a named/persona branding intentionally conflicts with project branding,
   keep the persona and ask one clarifying question.

## Evidence

Report receipts without secrets: bot id/username, source file + line, converted
raster path, Telegram photo file_unique_id, and verification download path.
Output counts, not tokens.
