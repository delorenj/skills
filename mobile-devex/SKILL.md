---
name: mobile-devex
description: Operate mobile app releases on DeLoNET through mobile-deploy-hub. Use when shipping, checking or debugging a version of Tower of Lost Things, Green In Between or Gruvato; starting or reading a Deploy workflow run; changing the hub, its caller template or its deploy policy; or working on the S26/iPad installs, Quickdrop, the builds bucket, catch-up installers, the metered-Mac data budget, or Bloodbank deployment events and their ntfy links.
---

# Mobile DevEx: mobile-deploy-hub

Every mobile app version on DeLoNET ships through one reusable hub:
[delorenj/mobile-deploy-hub](https://github.com/delorenj/mobile-deploy-hub)
(local: `~/code/mobile-deploy-hub`). The apps are Tower of Lost Things
(`pile-of-dumb-things`), Green In Between (`green-in-between`) and Gruvato
(`gruvato`). The design of record is `docs/design-hub-v1.1.md` in the hub repo.

## The one rule

**Mobile app versions ship only through mobile-deploy-hub: `mise run deploy`
(dry run), then `mise run deploy --dry-run false`; never bump, tag,
`gh release create`, upload to TestFlight or install a release build by hand.**

- A real deploy bumps (patch by default; `--bump minor|major`), commits and
  tags `vX.Y.Z` on `main` itself, then installs and reads back.
- A failed deploy is finished with `gh run rerun <run-id> --failed` (same
  version, same commit), never a second bump.
- Installs are always in place (`adb install -r`, `devicectl device install
  app`) with version readback: never uninstall an app, clear its data, or
  install an older build over a newer one. The hub refuses downgrades before it
  spends the bump.
- Each app carries only a thin caller (`.github/workflows/deploy.yml` copied
  verbatim from the hub's `templates/deploy.yml`, pinning `@v1`), a manifest
  (`tools/ci/mobile-deploy.json`, schema 2) and the `mise run deploy` task that
  fetches the hub's front door. Nothing in an app bumps, tags or announces a
  version on its own. The git guard enforces it: a staged hub `uses:` outside
  `deploy.yml` or not at `@v1` is refused, and so is an app workflow line that
  uploads a build; the hub's commands also refuse any run whose caller is not
  the app's `deploy.yml`.
- On the devices, one-time: subscribe ntfy-ios on the iPad to the `deploys`
  topic (the upstream gate forwards it), set Syncthing on the S26 to sync on
  Wi-Fi only, and keep the Safari `https://s3.delo.sh/builds/index.html`
  bookmark. An S26 install from the notification is: **Install APK (size)**,
  then Download (Chrome's harm warning), Open, Update — the first time also
  allow the browser to install unknown apps. Never uninstall.

## Front door (how a deploy starts)

- In the app repo: `mise run deploy` (dry run, changes nothing), then
  `mise run deploy --dry-run false` (real). Works from any machine with `gh`,
  including the Mac; from the phone, use the GitHub app (the repo's Deploy
  workflow, Run workflow, untick `dry_run`).
- All three apps in Jarad's order: `mise run deploy:train [--dry-run false]`
  in the hub (Tower, then Green In Between, then Gruvato; stops at the first
  red run).
- Real runs happen only on `main` and only with released hub code
  (`HUB_REF vX.Y.Z`); the gate refuses anything else before a version or a Mac
  byte is spent.

## The policy

- The rules live in one file, `tools/ci/policy.json`, read from the exact tag
  the run pins — never from an input, env var, app manifest or hook — so every
  entry point (front door, `gh workflow run`, the phone, a rerun) obeys the
  same rules.
- The `gate` job enforces it first: caller template hash in `callers.accept`,
  `strict: true`, pinned self-hosted runners, manifest schema, required lanes,
  a released `HUB_REF`, and no downgrades. Every job logs
  `HUB_POLICY sha256=<8>`.
- To change a rule once for all apps: edit `policy.json` with its test in the
  hub, then `mise run release` (conformance across the three apps, tag
  `vX.Y.Z`, move `v1`, one strict dry run per app — `v1` moves back if any is
  red). Never special-case an app; apps never edit policy, they inherit it
  through the `@v1` pin.

## Devices: installed, pending, skipped, failed

- Present and healthy → installed, read back, green run.
- Present but refusing the install or readback, wrong device or signer, or a
  planned downgrade → the run fails and sends `.failed`.
- Absent (the S26 off adb, the iPad unavailable, the Mac offline or over its
  data budget) → `pending` (built and published, waiting for the device) or
  `skipped` (not built). The run still bumps, builds, publishes and goes
  green; catch-up converges the devices later.
- The Mac on a hotspot is metered: the Xcode handoff is an rsync delta into a
  persistent cache on the Mac, the IPA returns only when needed, and past
  150 MiB of estimated Mac traffic the iPad lane is skipped unless
  `--metered allow` says otherwise. Minimise bytes to and from the Mac.

## Where builds land

- S3/MinIO bucket `builds`, public read at `https://s3.delo.sh/builds/`:
  per-app install pages, `latest.json` forward-only pointers, and the one OTA
  manifest. Writes happen only from big-chungus over the loopback endpoint as
  the MinIO user scoped to `builds`; its keys come from `op read` at call
  time, never from a file, argv or env a hook can see.
- Quickdrop: `~/quickdrop/builds/<slug>-<X.Y.Z>-<code>.apk`, one per app,
  capped at 120 MB (Gruvato's debug APK is skipped), written as a regular file
  through Syncthing's own temp name then renamed — never a symlink.
- A private GitHub Release `vX.Y.Z` per version.

## Events and links

- One `bloodbank.project.deployment.completed|.failed` per run attempt, sent
  `--strict`. Never mint `lifecycle.*` types; the bus's naming contract
  rejects them.
- `data.links` (`apk` "Install APK (74.7 MB)", `ota` "Install on iPad", `page`
  "Builds", `run` "Run") become the ntfy notification's buttons; the Click
  opens the build page. The router also publishes every deploy event to the
  `deploys` topic, which the upstream gate forwards to ntfy.sh for the iPad's
  ntfy-ios subscription.
- Catch-up installs send their own event (`data.trigger: catch-up`), one per
  device status change, reusing the deploy's run and correlation.

## Catch-up

- A systemd user timer on big-chungus (every 120 s, the S26) and a LaunchAgent
  on the Mac (every 300 s, the iPad) install or confirm each `pending` build —
  always in place, with sha256 and signer checks — then report one event per
  status change. After three failures on one version: one `.failed`, then
  silence until the next deploy or `catchup.mjs retry <slug> <platform>`.
- Both hosts run live (mode in `~/.config/mobile-deploy-hub/catchup.json`;
  `watch` is the safe default for a new host). A deploy in flight holds every
  pending build at or below its version on both passes; the S26 waits while
  the app is on top with the screen on, the iPad while the app runs. The Mac
  validates its pointers with the strong ETag and reads over ssh from
  big-chungus when `s3.delo.sh` does not answer.
- A Mac that goes away after the gate cannot hold a deploy: the iPad lane is
  `skip-lost` at the plan, and the host watchdog (`tools/ci/macwatch.mjs`, a
  systemd timer every 2 min) cancels a run whose Mac job waited past
  `mac.queue_limit_min` with its runner not busy — only once `deliver-android`
  is done, so the S26's publish is never cut short.

## Reading a run

- Markers tell the story: `HUB_GATE`, `HUB_GATE_REFUSED`, `HUB_POLICY`,
  `HUB_PLAN`, `HUB_S26_PENDING`, `HUB_IPAD_PENDING`, `HUB_IPAD_NEWER`,
  `HUB_IOS_DEFERRED`, `HUB_MAC_LINK`, `HUB_MAC_BYTES`, `HUB_MAC_LOST`,
  `HUB_HANDOFF_DELTA`, `HUB_PUBLISHED`, `HUB_PUBLISH_DRY_RUN`,
  `HUB_POINTER`, `HUB_QUICKDROP`, `HUB_EVENT_SENT`, and the `HUB_CATCHUP_*`
  family. The job graph ends in `deliver-android` (never waits for the Mac)
  and `deliver-ios`; announce needs both.
- A dry run changes nothing: no tag, no Release, no S3 object, no Quickdrop
  file, no event.
