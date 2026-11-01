---
name: stitch
description: 'Use the Stitch CLI for UX ideation: turn captured product intent into screens, explore design variants, export reference mockups, or hand a chosen direction into the 33GOD BMAD UX pipeline. Also use for /stitch and Stitch CLI setup or diagnostics. Not for implementing production UI, generic UX elicitation, or replacing DESIGN.md and EXPERIENCE.md.'
---

# Stitch UX ideation

Stitch is a **design producer**, not the UX decision-maker or implementation
engine. In 33GOD: captured product intent → Stitch concepts → user choice →
BMAD UX reconciliation → DESIGN.md + EXPERIENCE.md → architecture/build.

## Route and prerequisites

- For open-ended UX discovery, start with `bmad-ux`; it owns elicitation and the
  authoritative visual/behavioral contracts. When its Design handoff selects
  Stitch, follow [the handoff contract](references/33god-handoff.md).
- For an explicit screen/variant request with sufficient intent, use the CLI
  below directly. Require the product goal, key journey/surface, target device,
  content/states, constraints, and known visual decisions. Ask only for gaps;
  never invent the user's brand or silently choose a winning variant.
- `design-md` owns extraction from an existing Stitch design; `impeccable`
  owns critique/polish of implemented interfaces. Do not duplicate their workflows.
- Browser actions use `kapture`, not a second browser integration. Local capture
  of an existing app is distinct from generating a concept; never fabricate a
  capture with `generate screen`.

## Establish CLI and authentication

Verified against official `@google/stitch@0.12.1` (Node ≥20). Check
`stitch --version` and command `--help` on upgrades; the documentation mirror at
stitchprompt.com is not the command authority. Install/update only when requested,
using the host's Node package convention and an explicit version. Never run
`stitch agent-skills add`: canonical skill content and activation belong to Skillex.

Check status without echoing its masked credential field:

```bash
stitch status --json | jq '{authenticated, authMethod, verified, storage, canvas: {present: .canvas.present}}'
```

Configured/present is **not verified**. After the user authorizes an authenticated
check, `stitch find projects --json` proves access without generating a design.
If auth is missing, have them run `! stitch login` interactively, or inject a
per-consumer `STITCH_API_KEY` from 1Password into the process environment. Do not
write an API key into config, a dotenv file, a command flag, or any tracked file.
Do not print credentials, use `--trace`, or enable workspace `loop` as setup.
Stitch is Google's design service, not a general-purpose LLM inference client;
no provider model or gateway route is added here.

## Generate, compare, refine

Before any remote creation/upload/generation, confirm the target project and
approved content. An install-only request does **not** authorize uploading a repo,
product specs, screenshots, or starting paid generation. Prefer explicit
`--project` over rebinding the directory with `config set project`.

```bash
# Read existing projects; create only if an approved project does not exist.
stitch find projects --json
stitch create project --title "Approved concept title" --json

# Substitute the approved project ID and captured prompt.
stitch generate screen --project <project-id> --device DESKTOP \
  --prompt "<goal, journey, content, states, visual constraints>" --dry-run --json
# Inspect the preview; remove --dry-run only for authorized generation.

stitch generate variant --project <project-id> --screen <screen-id> \
  --count 3 --creative-range EXPLORE --aspects LAYOUT,COLOR_SCHEME \
  --prompt "<specific alternatives to compare>" --dry-run --json
```

Use `MOBILE` for mobile concepts. Variant count is 1–5; creative range is
`REFINE`, `EXPLORE`, or `REIMAGINE`. Record returned IDs rather than guessing.
Offer the user meaningful alternatives with tradeoffs (journey coverage, density,
accessibility, responsiveness, and fit to captured intent). A generated screenshot
is not accessibility, interaction, or production-readiness proof.

Only after a choice, use `stitch edit screen <screen-id> --project <project-id>
--prompt "<one focused change>"`. To supply an existing authoritative visual
contract, preview `stitch upload design <path-to-DESIGN.md> --project <project-id>
--dry-run --json`; upload only approved content. Never overwrite a BMAD spine with
a generated one.

## Export and hand off

```bash
stitch download screen <screen-id> --project <project-id> \
  --html --image --output <new-empty-output-directory>
stitch url screen <screen-id> --project <project-id>
```

Keep every downloaded screen in its own new, empty directory; treat HTML as
untrusted reference material, never execute embedded scripts as tooling or copy
it blindly into production. Do not overwrite prior exports. Approval to send
content to Stitch is not approval to publish it. Obtain separate approval before
delivering an HTML preview at a public URL; then follow `html-artifact-delivery`
and the host's publishing rules. Otherwise keep exports private and provide the
local files/paths with their access limitations. No publication is needed merely
to install this skill.

Write a `handoff.md` alongside exports using
[the 33GOD handoff contract](references/33god-handoff.md). Return the selected
screen IDs, previews/paths, decision rationale, unresolved behavior, and the next
BMAD UX action. Mark mocked versus untested states honestly. Installation can be
complete while live authentication/generation remains unverified.
