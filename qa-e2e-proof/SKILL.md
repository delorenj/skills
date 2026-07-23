---
name: qa-e2e-proof
description: >
  Run an IntelliForia Chrome-extension QA runbook AC end-to-end against the REAL
  unpacked extension and produce visual proof (annotated gif + screenshots +
  pass/fail report). Use when asked to "prove RGxx", "run the QA runbook in a
  browser", "load the unpacked extension and test it", "record a gif of the
  save-gate / compliance behavior", or to add a new browser-E2E scenario. Covers
  the Chrome-150 load-extension gotcha, the hermetic Passage fixture pattern, the
  content-script breadcrumb observables, and the harness under extension/qa/.
  Do NOT use for Flutter/Dart tests, the backend, or vitest unit tests.
---

# QA end-to-end proof (real extension in Chrome)

Loads the **actual unpacked extension** (`extension/dist/`) into Chrome via
Playwright, drives a **hermetic Passage fixture** that the content script injects
into, runs one runbook AC, and emits an **annotated gif + screenshots + a
pass/fail report** as proof. No live EMR, no credentials, no network, nothing
mutated.

Harness lives in `extension/qa/`. Run from `extension/`.

## Run an existing scenario

```bash
cd extension
xvfb-run -a node qa/run.mjs rg-modal-save      # offscreen (CI / polite)
# or, to watch it live on the desktop:
node qa/run.mjs rg-modal-save
```

Artifacts → `extension/qa/artifacts/<id>/`: `report.md`, `report.json`,
`<id>.gif`, `shots/*.png`. Exit code is the pass/fail. `node qa/run.mjs`
defaults to `rg-modal-save`.

## The recipe — and the four gotchas that make or break it

The harness (`qa/lib/harness.mjs`) already encodes all of this; read it before
changing anything. Each of these cost real debugging:

1. **Stable google-chrome (≥137, incl. 150) hard-ignores `--load-extension`.**
   The extension silently never loads (no service worker, no content scripts).
   Fix: use **Playwright's bundled Chromium** (`chromium.launchPersistentContext`
   with no `executablePath`) — its build honors the flag. (CDP
   `Extensions.loadUnpacked` on google-chrome loads the extension but its static
   content scripts still don't inject — dead end.) Keep
   `--disable-features=...,DisableLoadExtensionCommandLineSwitch` anyway.

2. **Serve the fixture AT the real EMR host, not localhost** — the content-script
   match pattern is `*://*.passagehealth.com/*`. The harness runs a local HTTP
   server and maps the host with
   `--host-resolver-rules=MAP *.passagehealth.com 127.0.0.1:<port>` +
   `--ignore-certificate-errors`, then navigates to
   `http://clinical.passagehealth.com/dashboard/clients/42/sessions/99`.
   (Playwright `route.fulfill` at the real URL also commits the URL, but a local
   server + host-map is what proved reliable here.)

3. **First-run gating blocks the page.** Signed-out, the extension throws up an
   onboarding modal (`#intelliforia-onboarding-modal-root`) that intercepts all
   clicks, and the save-gate won't produce a verdict. Seed via the service
   worker BEFORE navigating: `onboardingCompleted:true` and a signed-in
   `auth-storage` Zustand envelope (`seedSignedIn`). The stub score endpoint
   ignores the fake token.

4. **Don't abort the extension's own requests.** A catch-all `context.route`
   must `continue()` `chrome-extension://` (and `data:`/`blob:`) URLs, or the
   compliance shadow-host CSS fetch fails ("Failed to mount compliance shadow
   host") and the gate never mounts. Stub the AI endpoints
   (`score-provider-note`, `generate-session-note`), pass Passage through to the
   local server, block everything else.

## Fixtures must satisfy the adapter's detectors

The extension only ACTIVATES (and arms the save-gate) once
`PassageHealthProvider.detectSessionField()` finds the session-note field. It
matches a `<textarea>` to a nearby label in `KNOWN_SESSION_NOTE_LABELS`
(currently `'Summary of session'`, `'Session summary'`). A fixture whose note
label is anything else → the adapter loads but never arms (silent).
`qa/fixtures/passage-session-editor.html` uses `Session summary` + a wrapping
`<form>`. When a rule reads other fields (billing code, Start/End datetime via
Mantine buttons, care-location), reproduce those DOM shapes too — grep
`src/providers/PassageHealthProvider.ts` and `src/providers/passage/*` for the
exact selectors/labels.

## The observable = content-script breadcrumbs

The extension logs `[IF:...]` breadcrumbs to the page console (preserved in
non-store builds); the harness captures them and scenarios assert on them:

| Signal | Breadcrumb |
|---|---|
| save-gate armed | `[IF:SaveGate] interception armed (delegated)` |
| modal Save ignored (the AC) | `[IF:SaveGate] ↪ modal Save … passthrough (no gate)` |
| session Save gated | `[IF:SaveGate] ◀ submit intercepted` |
| score dispatched | `[IF:SaveGate] ⇢ dispatching score-note …` |

Breadcrumbs are the robust, backend-independent pass/fail signal; the gif/verdict
UI is the human-facing proof.

## Add a new AC scenario

1. **Fixture** — reuse or copy `qa/fixtures/passage-session-editor.html`; add the
   DOM the rule reads (match the adapter's detectors, see above). To discover
   what the extension does on your fixture, run `node qa/probe.mjs` and read the
   breadcrumbs it dumps.
2. **Scenario** — copy `qa/scenarios/rg-modal-save.mjs`. Export
   `meta = { id, title, fixture, runbookRef }` and `async run({ page, logs,
   banner, screenshot, phase })` returning `{ checks:[{name,pass,evidence}],
   pass }`. Use `banner()` for on-gif captions, `screenshot(name)` for
   checkpoints, `phase(name)` to timestamp a window and slice `logs` by `.t`.
3. **Run** — `xvfb-run -a node qa/run.mjs <id>`. Iterate until green, then view
   `shots/*.png` to confirm the gif reads clearly.

Keep scenarios ~10s of action (the gif is trimmed to a 10s window around the
first `phase()`).

## Files

- `qa/lib/harness.mjs` — launch + host-map + seed + routes + console capture (the recipe).
- `qa/fixtures/*.html` — hermetic EMR pages that satisfy the adapter's detectors.
- `qa/scenarios/*.mjs` — one AC each: steps + breadcrumb assertions.
- `qa/run.mjs` — orchestrates a scenario → gif + screenshots + report.
- `qa/probe.mjs` — dev tool: load a fixture, dump breadcrumbs + injected DOM.
- `qa/artifacts/<id>/` — generated proof (git-ignored except reports/gifs).
