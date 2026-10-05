# 33GOD Integration (g33)

BMAD expansion module, version 1.1.0. g33 routes 33GOD ecosystem work to owner
components and turns worker evidence into BMAD implementation handoffs. It is a
consult/routing/evidence surface — not an employee, orchestrator, lifecycle
engine, or scheduler.

## Capabilities

| Menu | Action | What it does |
| --- | --- | --- |
| PF | preflight | Validate `.project.json` ticket binding, tool availability, Krebs enrollment (canonical executionReadiness port: managed must be fully ready; invalid mode is FAIL not legacy; shadow may be incremental WARN but never certifies managed readiness), install conflicts |
| ER | ecosystem-route | Classify a work request against the portable owner map and return owners + contract entrypoints; consumes the project's installed `[modules.g33]` config (ecosystem_root, doctrine_pointer) |
| EH | evidence-to-handoff | Evidence bundle (JSON) → handoff markdown; reads, hashes and parses the real diff and test proof; unresolved evidence is labeled claimed-unverified, never certified; attestation validates distinct implementer/reviewer identities |
| SU | configure | Safe idempotent installer (dry-run capable, additive merge, conflict-rejecting) |

## Install

Requires an existing BMAD install (`_bmad/`) in the target project and
Python >=3.11 with **PyYAML>=6.0** for structural authoring-config validation.
The dependency is declared in `requirements.txt` and the installer's PEP 723
script metadata. An environment owner may provision those requirements, or
invoke `uv run scripts/g33_install.py ...` to consume that metadata. The bridge's
`pythonExecutable` must select an environment with PyYAML. Missing PyYAML is an
explicit actionable preflight refusal with zero writes; there is no subset-parser
fallback and no automatic environment install by this module.

Manual:

```bash
python3 scripts/g33_install.py --project-root /abs/path/to/project --dry-run  # preview
python3 scripts/g33_install.py --project-root /abs/path/to/project            # apply
python3 scripts/g33_install.py --project-root /abs/path/to/project --answers answers.json
```

PJangler-driven (via the ES-module bridge — see below):

```bash
python3 scripts/g33_cli.py setup --project-root /abs/path/to/project [--dry-run] [--answers a.json]
```

Consumable CLI (safe, read-only):

```bash
python3 scripts/g33_cli.py preflight --project-root . --json
python3 scripts/g33_cli.py route --project-root . --request "add a new event" --json
python3 scripts/g33_cli.py evidence --project-root . --bundle evidence.json --out handoff.md
```

## PJangler companion bridge (API version 1)

`scripts/g33_pjangler_bridge.mjs` exports `g33Companion(request)` — the exact
callable PJangler's `src/bmad/companion.ts` resolves and invokes:

```js
import { g33Companion } from "<module>/scripts/g33_pjangler_bridge.mjs";
const reply = await g33Companion({
  schemaVersion: 1, moduleId: "g33",
  operation: "observe" | "plan" | "apply",
  projectRoot: "/abs/project",
  reason: "recipe" | "bmad-install" | "audit" | "repair",
  options: { /* moduleRoot?, pythonExecutable?, answers? */ },
});
// reply: { schemaVersion: 1, status, summary, details[], evidence[] }
```

Statuses per operation — observe: installed|missing|unavailable|conflict|error;
plan: planned|unchanged|unavailable|conflict|error; apply:
changed|unchanged|unavailable|conflict|error. `installed` requires real
content verification (customization content, resolver activation, help rows,
installed skill sources), never metadata claims; partial/tampered installs report
missing/conflict. plan performs zero writes. apply runs the installer then
re-observes. Unknown option keys are rejected, never silently ignored. Python
subprocesses run with `-B`/`PYTHONDONTWRITEBYTECODE=1` (no bytecode writes).
`import.meta.dirname` (with a `fileURLToPath` fallback) locates the module
root, so the module relocates freely; `options.moduleRoot` and
`options.pythonExecutable` override for testing.

## What the installer writes

| File | Layer | Notes |
| --- | --- | --- |
| `_bmad/config.yaml` | YAML authoring | `g33:` managed section; operator-edited values and unknown keys survive rerun (additive); `--force` re-emits managed keys only |
| `_bmad/_config/bmad-help.csv` | Help registry (ACTIVE) | Anti-zombie rows for this module only; other modules' rows preserved |
| `_bmad/custom/config.toml` | Team TOML | `[modules.g33]` — merged by the REAL upstream 4-layer resolver; additive merge preserves operator keys under `--force` |
| `_bmad/custom/bmad-*.toml` | Team TOML | Sparse overrides for skills actually installed in the project's activation roots (`.agents/skills`, `skills`, `_bmad/skills`), supported customize.toml keys only — build, code-review AND the planning family (prd, spec, architecture) |

## Supported layouts (explicit)

- **BMAD 6.12.1-next runtime layout** (this repo's install): TOML 4-layer
  resolver present — full registration, `toml_active: true`.
- **BMAD 6.12.0 pinned installer layout** (YAML manifest only): no TOML
  runtime integration exists. g33 reports the TOML registration explicitly
  `UNSUPPORTED/INACTIVE` (never "integrated active"); PJAN-166 (YAML→TOML
  migration) is out of scope for this module.

## Conflicts (rejected before any mutation, exit 2)

- malformed or unsupported `_bmad/config.yaml` (real safe YAML parse, duplicate
  mappings, unclosed quotes/collections, non-mapping document)
- foreign or duplicate top-level `g33:` shapes in config.yaml (inline values,
  comment-only headers, sections without the managed marker)
- pre-existing foreign `[modules.g33]` table with another module's `code`
- pre-broken `_bmad/custom/config.toml` or `_bmad/config.toml` (tomllib —
  the real resolver's parser)
- symlinked write ancestors or leaves, including every installed-skill override
- malformed or incompatible existing skill overrides

A rejected conflict leaves ZERO mutations.

## The YAML authoring / TOML runtime seam

BMAD authors module configuration in `_bmad/config.yaml` (YAML), but the
runtime resolves configuration from four TOML layers:
`_bmad/config.toml` → `config.user.toml` → `custom/config.toml` →
`custom/config.user.toml` (deep merge; keyed arrays replace by `code`/`id`;
other arrays append). g33 writes BOTH: the YAML section for authoring parity
and the namespaced `[modules.g33]` table in the team TOML layer so the module
is ACTIVE in the actual upstream resolver — never a YAML-only registration
described as active. When the upstream resolver is absent, the installer
skips the TOML write and reports the layout as unsupported/inactive rather
than pretending registration happened.

## Runtime config consumption

`route` and `preflight` read the project's installed `[modules.g33]` answers
(the same layer the real resolver merges): `ecosystem_root` appears in route
output; `doctrine_pointer` overrides the bundled doctrine pointer
(`momo/PILLARS.md`) for citations; `g33_output_folder` is reported at
preflight. The config is consumed, not ornamental.

## Portability

The owner map (`assets/ecosystem-map.toml`) contains no machine-absolute
paths: entrypoints are CLI names or repo-relative paths, doctrine is cited by
pointer and never copied. Identity wording: the identity bank is
`agent-<identity>` resolved from the agent registry's declared identity field
(NOT the Hermes routing profile directory; the 33GOD root PM is `grolf` →
`agent-grolf`; never target the stale `agent-33god-pm` bank). The org-wide
project bank is `33GOD` exact-case (33god/33god-core/33god-infra were
consolidated and deleted; naming one creates a NEW empty bank). Flume owns
agent lifecycle (hire/onboard/review/org chart); Hermes Fleet owns
runtime/profiles/templates — Flume renders what Hermes Fleet scaffolds.

## Safety

- Preflight-before-mutation: every conflict is detected before any write; a
  rejected conflict leaves zero mutations and exits nonzero.
- Idempotent: rerun with no operator edits changes nothing.
- Operator-edit preserving: edited managed values win on plain rerun;
  `--force` re-emits managed keys while preserving operator-added keys
  (additive, never wholesale replace).
- Evidence honesty: handoffs read+hash+parse the real diff and test proof;
  missing/empty/failing evidence is labeled unverified — never certified.
- No secrets are read or printed; CLI output is secret-scrubbed.
- Never assumes Krebs enrollment; validates it via the canonical
  policyVersion-2 executionReadiness field set when mode is managed (FAIL on
  any gap) or shadow (WARN; never certifies managed readiness).
- No new event types; event identity follows the Bloodbank contract.
- Live 33GOD install awaits explicit parent readiness — **deployed: false**.

## Upstream BMAD update boundary

**update-preservation: unavailable.** The observe/plan/apply v1 bridge does not
supply pre-update capture/protection, post-update restore/reconcile/verify, or
failure recovery for an upstream BMAD installer. It must not authorize a safe
upstream update. The owning updater must refuse updates before mutation until
it supplies that contract, including native installed BMAD projection bytes,
operator-edited help/SKILL.md, customizations, g33 declarations and foreign
mappings. Retained g33 trees and declarations remain protected after opt-out.
This module's additive rerun applies only to its own contained write targets.

Write containment uses the real project root: a supplied project-root symlink
is allowed as an alias for that real directory; every existing descendant
write component and leaf must be a regular directory/file, never a symlink
(including dangling links and links that point back inside the project).
Read-only reference activation symlinks in `.agents/skills` remain allowed.
Outputs are staged then replaced atomically. A caught apply failure rolls back
published files and created directories; rollback failure is returned explicitly.
Abrupt process termination or machine failure is not a supported update/recovery
protocol and requires operator inspection before another apply.

## Separate installed and deployed receipts

An evidence bundle may provide `installed_evidence_path` and
`deployed_evidence_path`. Each is a distinct JSON evidence file, separate from
the diff, test proof and other state receipt. The schema is
`{"state":"installed|deployed","claims":["exact claim"],"checks":[{"command":"verification command","exit_code":0,"observed":"recorded target observation"}]}`.
The receipt is read, hashed and structurally inspected. A valid record still
has unproven provenance and target observations: every supplied installed/deployed
claim remains `claimed-unverified`. A zero exit field or command string cannot
establish that a command actually ran. The generator never executes receipt
commands and never invents trust mechanisms; independent target verification
belongs to the owning workflow/reviewer. Evidence syntax and state truth are
separate.

Bridge `plan` and `apply` validate the same `answers` object through the installer.
Their temporary answers file is outside the project and cleaned up on success
and failure. `answers` is unsupported for `observe`, which reads installed state.
Invalid option values and unknown option keys return `error`. `observe` returns
`unavailable` if the runtime/customization resolver or an installed customization
surface is absent; `installed` includes real resolution of at least one g33
skill override, not file existence alone.

Test proof certification requires a positive pass summary and explicit zero exit
markers (`exit_code=0` or `command_exit_code=0`). A nonzero, missing or malformed
marker leaves the proof uncertified. In a combined log, each summary needs its own following exit markers before
the next summary/command block. Extra exits in one block cannot cover another
block; stray or malformed markers leave evidence uncertified. Prose about an
expected exit is not proof.

## Implementation claim linkage

A readable file is not implementation proof. The handoff parser validates
supported textual unified patches: paired file headers, valid hunk headers and
exact old/new line counts with actual changed lines. Empty, prose, malformed,
binary, combined and metadata-only patches stay invalid/unsupported evidence.
It reads recorded patches; it does not apply them or attest their provenance.

To link a worker claim to evidence, supply `claim_evidence`, for example:

```json
{
  "acceptance_criteria": ["AC1 safe installer"],
  "worker_claims": ["implemented safe installer"],
  "claim_evidence": [{
    "claim": "implemented safe installer",
    "acceptance_criteria": ["AC1 safe installer"],
    "diff_paths": ["scripts/g33_install.py"]
  }]
}
```

Each claim requires a unique link to known exact acceptance-criterion strings
and paths parsed from the valid diff, plus clean per-command test proof. Missing,
invalid or duplicate links leave the claim `claimed-unverified`. A successful
link is printed as `linked recorded evidence`; it validates artifact syntax and
references, while independent review determines semantic AC fulfillment. Overall
output retains this distinction and never certifies installed/deployed state.
The evidence CLI consumes the selected project's installed doctrine pointer.
