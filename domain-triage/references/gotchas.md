---
pipeline-status: new
---
# Gotchas

## folder-curator `plan` crashes on `.md` with a date in frontmatter

- **Symptom:** `folder-curator … plan "<file>.md"` exits with `TypeError: Object of type date is not
  JSON serializable`.
- **Why:** PyYAML parses `captured: 2026-06-14` into a Python `date`; the engine's `json.dumps` of the
  plan has no serializer for it. Any existing `.md` with a date value trips it. PDFs (no frontmatter)
  are unaffected.
- **Fix:** add `default=str` to the `json.dumps(make_plan(...))` call (~line 802 of
  `folder_curator.py`). It is a **shared** skill (`skillex/all-skills/folder-curator`, symlinked into
  `.agents/skills` and `.claude/skills`) — apply via the skill's fan-out, not a one-off edit.
- **Until fixed:** Layer 2 classifies `.md` files from content (the agent path the domain uses anyway).

## Overlapping category rules → parked, not routed

- **Symptom:** a file that "obviously" matches a type lands in the ingest queue at `confidence: low`.
- **Why:** folder-curator routes only when **exactly one** category matches; zero *or* two+ matches →
  review queue. E.g. a `Gmail - Invitation_ … Coding Interview @ …` matches both `invites` and
  `correspondence`.
- **This is correct.** A genuinely ambiguous file should reach a human/Layer-2, not be force-routed.
  Tighten `name_regex` only if a *common* case parks wrongly; otherwise let Layer 2 decide.

## Never guess the entity

- If entity detection (registry → contacts → content) doesn't resolve, **park at `confidence: low`**
  in `_triage/` with `<entity>: unknown` and a `needs-*-id` tag. A misfiled artifact is worse than an
  unfiled one, and the human edit is cheap. This is a feature of the procedure, not a failure.

## Don't run `apply`/`normalize --apply` at an entity-organized root

- folder-curator's `apply` moves files into **type**-subfolders (`threads/`, `application/`, …) at the
  client-root. For a domain organized by **entity** (JobHunting's per-company folders), that would
  flatten the structure. Use `plan` for typing/enrichment; let Layer 2 do the entity routing. `apply`
  is safe only for domains that *are* organized by folder-curator's type categories.

## The `domain:` block is engine-invisible

- The folder-curator engine deep-merges the `domain:` block but **ignores** it (unknown keys). It is
  read only by this skill's Layer-2 agent. So a bare `folder-curator` invocation will type + enrich a
  file correctly but will **not** detect the entity or apply sub-rules — that requires this skill's
  procedure. Keep the block and the Hindsight bank in sync by hand.

## One active entity (domains that need it)

- Some domains have an "active" entity (e.g. AutomaticAI: one client at a time). Encode it as a
  heuristic in the bank (*"cofounder Damian Miller → current client James Brennan"*) so ambiguous
  correspondence attributes correctly. Update it when the active entity changes.
