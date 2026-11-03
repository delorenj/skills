---
name: html-artifact-delivery
description: Deliver every HTML artifact (reports, dashboards, docs, BMAD/worktree/hidden outputs, self-contained or built sites) as a public URL at https://s3.delo.sh/projects/{project-slug}/{bb-session-id}/{artifact}/ with all CSS, JS and images. Use whenever you hand an HTML file to the user, whichever skill authored it.
---

# HTML artifact delivery

Delivery policy for **any** HTML you hand to the user. It composes with whichever
skill authored the page (BMAD, dashboards, reports, docs, build tools). A local
path or `file://` link is not a delivery. The delivery is the exact public
**entry URL**. S3 serves no directory index, so never give a bare prefix.

This is guidance, not enforcement. Nothing blocks a local link, so the job is
yours.

## Workflow

1. **Stage** the artifact in its own directory: the entry HTML plus every file it
   loads, with relative paths. Never point `--bundle` at a repo root. For built
   apps (Vite, Next export, etc.), stage the **complete build output**
   (`dist/`, `out/`) and use relative asset paths (Vite: `base: './'`).
2. **Plan** (default, offline, writes nothing):
   ```bash
   S=~/.agents/skills/html-artifact-delivery/scripts/publish_html_artifact.py
   python3 "$S" --bundle ./out/report --entry index.html --artifact sprint-review \
     --project-root "$PWD"
   ```
   Fix every `errors` entry. Then localize or bundle every `external_resources`
   (CDN scripts, styles, fonts, images) and `unresolved` entry (bare module
   specifiers, templated paths). `--publish` refuses while either is non-empty
   (`publishable: false`). Plain external hyperlinks (`<a href>`) are fine.
3. **Waive inspected JS false positives** (only if the plan reports them). JS
   module discovery is raw text matching, so import-shaped text in strings,
   comments and regex literals is reported too. React's development build, for
   example, reports `./MyComponent` from a warning string in `_vendor/react.js`.
   First run the plan with **no** flag. Then a human opens the named file and
   inspects **every** occurrence of the reported specifier. Only when none of
   them is a real import, re-plan with the exact pair:
   ```bash
   python3 "$S" ... --accept-js-candidate _vendor/react.js:./MyComponent
   ```
   - `FILE` is the bundle-relative POSIX path of the `.js`/`.mjs` file, or of
     the `.html`/`.htm`/`.svg` file whose inline `<script>` emitted it. The
     value is split at the **first** colon, so the specifier may contain colons.
   - `SPECIFIER` is the exact emitted string. There is no normalization, glob,
     prefix or fuzzy matching. Never waive a vendor or React file wholesale.
   - One pair waives **all** JS occurrences of that specifier in that one file,
     **including a real import that shares the string**. That is why every
     occurrence must be checked. The same specifier in another file still blocks.
     HTML attributes and CSS references are never waived.
   - Unused or malformed pairs are refused (`bundle_invalid` /
     `acceptance_invalid`, exit 2). Repeat the flag for each pair; identical
     duplicates collapse. Security checks (dangerous names, key material,
     symlinks, traversal) cannot be waived.
   - The receipt lists the waivers in `accepted_js_candidates` (`[]` when none).
4. **Publish** (opt-in): run the same command with `--publish`, repeating any
   `--accept-js-candidate` flags unchanged. It uploads with the
   existing `mc` alias `delo` into the fixed `projects` bucket, then fetches every
   object anonymously from `https://s3.delo.sh` and checks status, MIME, and the
   exact SHA-256 of the bytes served.
5. **Report** `entry_url` from the receipt only when `ok` is `true` (the receipt
   also carries `delivered: true` only for a verified publish; a plan or any
   failure is `delivered: false`). For dynamic JS, also open the URL in a
   browser and confirm it renders without console or network errors before
   calling it delivered.

## Identity (fails closed when missing or ambiguous)

- **Project**: `--project SLUG`, or `.project.json` `project_slug` and then
  `project_id`, read from the main worktree (via Git `commondir`) and the current
  worktree. Branch names, directory basenames, and board identifiers are never used.
  Conflicting values fail.
- **Session**: `--bb-session-id UUID`, or `--harness NAME --native-session-id ID`,
  or auto-detected from exactly one of `CODEX_THREAD_ID`/`CODEX_SESSION_ID`,
  `HERMES_SESSION_ID`, `CLAUDE_SESSION_ID`/`CLAUDE_CODE_SESSION_ID`. Mapping matches
  Bloodbank agent-hooks: a UUID passes through, and anything else becomes
  `uuid5(NAMESPACE_URL, "bloodbank:{harness}:{native}")`. The receipt records the
  provenance.
- **Artifact**: `--artifact NAME` is required. It keeps two artifacts in one session
  from overwriting each other. A new version means a new name, because there is no
  replace mode.

## What the scan rejects

Symlinks, `.git`/`.env*`/credential/key files (including `.s3cfg`, `.pgpass`,
`credentials*`, `secrets.*`), private-key material (OpenSSL, OpenSSH, PGP
armor), `..` escapes, root-relative (`/x`), `file:`, localhost/private-network
URLs, insecure `http:` subresources, `<base href>`, directory links, missing
local assets, a `--bundle` path that goes through a symlink, unreadable files,
an unreadable subdirectory (enumeration fails closed: no partial publish), and
names with control characters or trailing newlines. Assets
load from HTML attributes (`src`, `href`, `srcset`, `poster`, …), inline and
external CSS `url()`/`@import`, raw JS `import`/`import(...)`/`from` literal
specifiers (in `.js`/`.mjs` files and inline scripts), and standalone
SVG `href`/`xlink:href`/`<?xml-stylesheet?>` references. Non-JavaScript
`<script type>` blocks (JSON, import maps, templates) are data, not code, and
are not parsed as JS. Dotfiles, `.map`/`.ts`/`.tsx`/`.jsx` sources publish only
with an explicit `warnings` entry saying they will be public.

## Limits (say these when they apply)

- Discovery is static. `fetch()`, computed URLs, and runtime-injected assets are not
  seen, so ship the full build output and verify in a browser.
- JS import discovery is raw text matching, not a lexer or parser, and it does
  not decide whether a match is code. It reports a string literal after
  `import`, after `import (` (including `...import(` and whitespace or comment
  gaps), and after `from` (whatever the binding names). Matches inside strings,
  comments and regexes are reported on purpose, and a closing quote can be read
  as an opener (for example `"passed from " + name` reports `+ name +`). Each
  false positive blocks until it is inspected and waived exactly.
- It does not find computed `import(expr)`, escaped keywords, or anything that
  only a full ECMAScript parser could find. It does not cover arbitrary
  ECMAScript. Specifier escapes stay raw. A template specifier keeps its
  `${...}` and stays unresolved. A literal cut off by a line break or the end of
  the file is skipped. A literal longer than 4096 characters is reported
  truncated. If the bounded work budget runs out, the bundle is rejected
  instead of returning a partial scan. Browser verification remains necessary.
- Every required resource has to be a local file. External resources, bare module
  specifiers, and templated paths are listed in the dry run and block `--publish`.
- There is no atomic collision guard. Preflight `mc ls` refuses a non-empty prefix
  (and fails if the listing can't be parsed), but two concurrent publishes to the
  same prefix can still race. Use distinct `--artifact` names.
- A partial failure leaves the objects that were already uploaded (nothing is
  deleted). Every failure path — including a timeout, `mc` disappearing, or any
  other OS error mid-upload — reports `uploaded`, `failed` (or the failing
  command) and `not_attempted`. Retry with a new `--artifact`.
- Uploads read a private snapshot of the validated bytes, not the live source
  paths: a file swapped or rewritten between the plan and the upload fails the
  publish (`bundle_changed`) instead of publishing unvalidated bytes. Scan and
  snapshot both open sources through `O_NOFOLLOW` directory-descriptor chains
  and read from the validated handles, so a name swapped to a symlink between
  enumeration and the byte read cannot publish outside bytes. A failed
  snapshot attempt removes its partial copy.
- Objects are public and use `Cache-Control: no-cache, no-transform`. The
  `no-transform` stops the Cloudflare proxy from injecting its analytics beacon
  into HTML, which would break the byte-exact SHA check. Verification is never
  relaxed or normalized to accept a rewritten body. Never publish anything private.

## Exit codes

`0` ok · `2` invalid input/bundle/identity/remote, or unresolved dependencies on publish · `3` collision · `4` mc/preflight/timeout before any upload ·
`5` upload failed (partial, including a timeout or missing mc mid-upload) · `6` public verification failed. The JSON goes to stdout.
mc stderr is never echoed, and mc messages are redacted.

## Do not

Create buckets, change bucket policy, run `mc alias list`, read mc config or
credential files, use `mc mirror --remove`, or delete objects.

Sample bundle for a live check: `assets/sample-bundle/`. Its page shows
CSS/Image/JavaScript status lines, and all three should turn green. It declares a
relative favicon so the browser doesn't request the bucket-root `/favicon.ico`
(403).
Tests: `python3 -m unittest discover -s tests -v` (from this directory).
