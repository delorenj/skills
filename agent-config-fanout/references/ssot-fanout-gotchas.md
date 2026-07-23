---
pipeline-status:
  - new
---
# Gotchas

Read a section only when the matching symptom appears.

## `--check` keeps reporting a target "out of date" right after `--apply`

**Symptom:** apply succeeds, but the very next check says the same generated file is stale.
**Cause:** generation is non-deterministic — a timestamp, a `Date.now()`, `set()` iteration order, or
`json.dumps(sort_keys=True)` reordering vs the source — so generated-from-master never byte-matches
on-disk.
**Fix:** make `generate()` pure: no clocks, no RNG, preserve the master's declared order, and serialize
the same way you compare (`json.dumps(..., indent=2, ensure_ascii=False) + "\n"`, no `sort_keys`).
**Why it matters:** the whole `check`-as-CI-gate contract rests on "no master change ⇒ zero bytes
written." A churning generator turns the gate into noise and re-introduces the drift it exists to catch.

## A hand-edit to a generated config silently vanishes

**Symptom:** someone tweaks `copilot/hooks.json` (or a publisher's `EVENT_MAP`); the next sync reverts it.
**Cause:** that file is GENERATED — it is an output, not a source. Editing it is editing build artifacts.
**Fix:** make the change in the master (`*.master.json`) and `sync`. Mark every generated file with a
`_do_not_edit` header and add an anti-pattern note in the repo's README/CLAUDE.md so the rule is visible.
**Why it matters:** the pattern's entire value is "one place to edit." A hand-edit downstream is invisible
drift the moment anyone re-syncs — exactly the failure class the SSOT removes.

## An ambiguity won't clear even after I added a lock entry

**Symptom:** `--check` still lists `role:X` (or `type:Y`) as unresolved.
**Cause:** the lock key doesn't match the id the detector computes (e.g. you wrote `post_tool` instead of
`role:post_tool`, or `type:bloodbank...` with a typo), or the entry is under the wrong top-level key
(`resolutions` is where the engine looks).
**Fix:** copy the exact id from the `--check --json` ambiguity output into `resolutions`; ids are
`role:<role>` and `type:<value>` verbatim.
**Why it matters:** "remembered = seamless" only holds if the recorded key is the same string the
detector looks up; a near-miss re-prompts forever.

## Divergence isn't detected even though two targets clearly map the same thing differently

**Symptom:** target A's post-step → `tool.invoked`, target B's → `tool.completed`, but `--check` is green.
**Cause:** divergence detection groups bindings by `role`. If the two bindings carry different `role`
values (or none), they're not compared. Roles are the normalization unit, not native names.
**Fix:** give bindings that represent the same lifecycle moment the **same `role`**. Then the detector
sees one role with two catalog values and flags it.
**Why it matters:** without shared roles the engine can't know two targets are talking about the same
thing, so genuine divergence ships unnoticed — the opposite of the pattern's purpose.

## A consumer broke after the generated map went missing/corrupt

**Symptom:** delete or truncate `X.generated.json` and the tool stops emitting / crashes.
**Cause:** the consumer hard-loads the generated file with no fallback.
**Fix:** `resolve_map(dir, default)` = small embedded default, with the generated file merged OVER it;
return the default on missing/corrupt. The generated projection wins for the keys it defines.
**Why it matters:** generated files get gitignored, mis-pathed, or half-written. A drop-in hook script
must degrade, not fail the host tool.

## Migration aliases stopped working after switching the consumer to the generated map

**Symptom:** an old/alias arg (`session-start`, `notify`) that the embedded map handled now no-ops.
**Cause:** `resolve_map` *replaces* the embedded default with the generated map instead of merging — and
the generated projection only contains the canonical native names from the master's bindings.
**Fix:** merge generated OVER default (`merged = dict(default); merged.update(generated)`), so aliases in
the embedded default survive while canonical names track the SSOT.
**Why it matters:** the master intentionally lists only canonical names; aliases are a consumer-local
back-compat concern that the SSOT shouldn't have to carry.

## Sync generated a legal-looking config that fails at runtime

**Symptom:** `--check` is green but the target rejects the config, or emitted output fails a schema.
**Cause:** the engine templated blindly — it never validated the projection against the domain contract
(regex/allowlist/schema).
**Fix:** add the contract assertions into `--check` and a per-binding verifier (build one representative
output per binding, validate it). The agent-hooks verifier is `smoketest:agent-hooks-ssot`.
**Why it matters:** a propagation engine that emits contract-invalid output just moves the breakage from
"hand-edit drift" to "confidently-generated drift." Validation is what makes the SSOT trustworthy.

## Overwrote a shared live config when installing the fragment

**Symptom:** merging the generated fragment into `~/.claude/settings.json` clobbered unrelated hooks.
**Cause:** treated a partial fragment as a full-file replacement. The generated `*.settings.hooks.json`
covers ONLY this system's entries; the live file holds many others.
**Fix:** surgical merge — replace only this system's entries, preserve the rest; back up first
(`cp settings.json settings.json.bak-<ts>`) and re-validate the JSON parses.
**Why it matters:** shared global configs are owned by the user, not the generator. Full overwrite is
destructive and erodes trust in running `sync` at all.

## Merging a sub-block round-tripped (and silently rewrote) the whole operator file

**Symptom:** installing your block into a YAML/TOML/JSON operator config quietly changes *unrelated*
content — e.g. PyYAML `safe_load`→`safe_dump` coerces YAML 1.1 scalars (`on`/`off`/`yes`/`no` →
`true`/`false`) and strips comments across keys you never touched.
**Cause:** you parsed the entire document, mutated one sub-key, and re-serialized the whole thing.
The serializer reformats everything, not just your block.
**Fix:** splice only your block back into the original raw text — locate the top-level key, replace
its span, leave every other byte verbatim. Detect change on *your sub-tree* (`_norm(block)`), not the
whole doc, so you only rewrite when your block actually changed. (A comment/style-preserving round-trip
loader like ruamel.yaml also works, but it's a non-stdlib dep.)
**Why it matters:** the config is operator-owned. "I only changed the hooks block" must be literally
true at the byte level, or the first deploy that touches a file with comments or `on/off` scalars
corrupts settings the operator hand-tuned — exactly the trust-breaker the SSOT is meant to prevent.

## One bad target aborted the whole fleet fan-out

**Symptom:** deploying to N discovered targets, an exception on target #7 (locked file, malformed
config, a scalar where a list was expected) kills the loop — targets 1–6 are half-written, 8–N never
run, and no summary prints.
**Cause:** the per-target install is called bare inside the fan-out loop; any unguarded operation
(list comprehension over a non-list, a write, a backup) propagates and aborts the batch.
**Fix:** wrap each per-target call in try/except, count failures, print a per-target WARN, and continue.
Also defensively type-check operator-supplied sub-values (a key whose value should be a list may be a
scalar). Emit a final `N processed, X installed, Y up-to-date, Z skipped, W warned` summary.
**Why it matters:** fleet deploys hit heterogeneous, operator-edited targets; fault isolation is the
difference between "1 agent needs attention" and "half the fleet is now in an unknown state."

## Source payload nested its real fields under a wrapper key

**Symptom:** the mapped event always reports the same value (e.g. `outcome: success` even on failure),
and identity fields (`model`, ids) come out null — yet the source clearly provides them.
**Cause:** the upstream hook/runtime promotes only a few keys to the top level and nests everything
else under a wrapper (hermes puts all but `{tool_name, args, session_id}` under `payload['extra']`).
Your projector reads top-level keys only.
**Fix:** flatten the wrapper before mapping (`merged = {**payload['extra'], **top_level}`; top-level
wins), and for error state, inspect the actual result object (an error encoded inside `result` as a
dict or JSON string), not just a top-level `is_error` flag.
**Why it matters:** a projector that reads the wrong nesting level produces contract-valid but
semantically dead events (always-success) — worse than failing loudly, because it looks correct.

## Surgical merge STILL deleted sibling hooks (the granularity trap)

**Symptom:** the merge replaces "only our entry", yet foreign hooks vanish anyway — e.g. installing the
publisher into Claude's `Stop` wiped the co-resident `hindsight-session-end`, `git-checkpoint`, and
`notify` hooks.
**Cause:** merging at the wrong granularity. Many hook formats nest *multiple* hooks inside ONE group:
`{"Stop": [ { "hooks": [hindsight, git-checkpoint, OURS, notify] } ]}`. Identifying the GROUP as "ours"
(because it contains our command) and replacing the whole group destroys its siblings.
**Fix:** operate at INNER-hook granularity. Find the inner hook whose `command` matches your publisher
substring and update only *that* hook's `command`/`timeout` in place; never replace its enclosing group.
If absent for an event, append your generated group. Detect change semantically
(`json.dumps(merged, sort_keys=True)` vs original) so formatting-only diffs don't trigger rewrites.
**Why it matters:** the publisher hook is sometimes its own group and sometimes one of several siblings
in a shared group — group-level logic looks correct in the common case and silently eats neighbors in
the nested one. Always diff the live file against its backup after the first install to prove siblings
survived.

## Canonical publisher migration matched the wrong hook

**Symptom:** after normalizing many per-client publishers into one root `publish.py`, install starts
classifying unrelated commands as "ours" or fails to replace old `claude/publish.py` entries.

**Cause:** the merge marker was a broad substring like `publish.py`. Once every agent calls
`bloodbank/publish.py`, that marker is no longer specific enough, and old per-client command paths still
need one migration pass.

**Fix:** use a narrow canonical marker plus explicit legacy markers. In the Bloodbank reference,
`publisher` is `bloodbank/publish.py` and each agent carries `legacy_publishers`
(`claude/publish.py`, `codex/publish.py`, etc.). The installer treats any of those as this system's hook,
updates the entry in place, and leaves foreign hooks alone.

**Why it matters:** a normalized runtime surface should simplify maintenance, not make the installer
guess. Marker specificity is the difference between a safe migration and a spooky global-config bite.
