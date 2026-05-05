# Routing Mechanics

The body of a hub skill is a routing surface, not a tutorial. This file specifies the four routing primitives a skill body uses to direct an agent to the right content with minimum reasoning: decision trees, navigation tables, triage tables, and reading order tables. It also specifies the four-part structure for authoring gotchas and the format for cross-cutting rules and out-of-scope declarations.

These primitives are how cloudflare-style hubs deliver O(depth) routing instead of O(N) scanning.

## Reading Order

| Task | Read |
|------|------|
| Building a hub SKILL.md body | [Decision Trees](#decision-trees) and [Triage Tables](#triage-tables) |
| Building a single-skill SKILL.md body | [Quick Navigation Tables](#quick-navigation-tables) and [Reading Order Tables](#reading-order-tables) |
| Authoring failure-mode entries | [Four-Part Gotcha Structure](#four-part-gotcha-structure) |
| Hoisting cross-cutting rules | [Cross-Cutting Rules](#cross-cutting-rules) |
| Setting boundaries | [Out-of-Scope Declarations](#out-of-scope-declarations) |
| Pre-computing common combinations (hub) | [Common Combinations Tables](#common-combinations-tables) |
| Disambiguating ambiguous task signals | [Discovery Hints](#discovery-hints) |
| Pitfalls | [Gotchas](#gotchas) |

## Decision Trees

Use ASCII decision trees for routing by user intent. Place them at the top of the body, before any prose or index.

Template:

```
Need [X]?
├─ [condition A] → topic-or-skill
├─ [condition B] → topic-or-skill
│  ├─ [sub-condition B1] → specific-leaf
│  └─ [sub-condition B2] → specific-leaf
└─ [fallback] → topic-or-skill
```

Rules:
1. Every leaf must resolve to a concrete file path or topic short-name. No vague leaves like "general guidance" or "see docs".
2. Branches must be mutually exclusive. If two branches could match, the agent has to reason. Add a tiebreaker condition or split the branches.
3. Depth: 2-3 levels max. Deeper trees fail to render legibly.
4. One tree per user intent. Use multiple trees for distinct intents (`Need to run code?`, `Need to store data?`, `Need AI?`) rather than one mega-tree.

Verbatim example from cloudflare hub:

```
Need to store data?
├─ Key-value (config, sessions, cache) → kv/
├─ Relational SQL → d1/ (SQLite) or hyperdrive/ (existing Postgres/MySQL)
├─ Object/file storage (S3-compatible) → r2/
├─ Versioned file trees (repos, build outputs, checkpoints) → artifacts/
└─ ...
```

Each leaf resolves to a `references/<topic>/` directory, never to a vague concept.

### When to use a decision tree vs a triage table

| Use decision tree | Use triage table |
|---|---|
| Routing by user intent ("I need to do X") | Routing by task signal (specific files, imports, commands) |
| Branching is hierarchical | Routing is flat |
| 8+ leaves total | 2-6 routes |

## Triage Tables

Use two-column tables to map task signals to specific files. Place them in skill-set hubs and reference-hubs that load child SKILL.md files.

Template:

```markdown
| Task signal | Load |
|---|---|
| <specific signal phrase, comma-separated> | <skill-name> → <relative path to SKILL.md> |
```

Rules:
1. Left column: comma-separated specific signals. Include file names, command names, library imports, error types, vocabulary the user would actually use.
2. Right column: the exact file to load, including relative path.
3. Order rows by frequency (most-likely-to-match first) or by alphabetical skill name.
4. No prose between rows.

Verbatim example from cloudflare-focused hub:

```markdown
| Task signal | Load |
|---|---|
| `wrangler …` command, `wrangler.jsonc` config, KV/R2/D1/Vectorize/... CLI, secrets, deploys, environments, `wrangler types` | **wrangler** → `cloudflare-wrangler/SKILL.md` |
| Writing or reviewing Worker source, handler signatures, streaming, ... | **workers-best-practices** → `cloudflare-workers-best-practices/SKILL.md` |
```

Density of signals on the left column is intentional: dense signals reduce ambiguity and reduce reasoning cost.

## Quick Navigation Tables

Use two-column tables to map "user situations" to specific guidance for non-hub skills (standalone or member). The Quick Navigation table sits near the top of the body, after operating principles and before the procedural steps.

Template:

```markdown
| Your situation | Read |
|---|---|
| <user situation in their words> | <step number or reference path> |
```

Rules:
1. Left column phrasing should match how the user thinks about their problem, not how the skill is structured.
2. Right column may point to a step number ("Step 3 below"), a reference file ("references/X.md"), or a section anchor.
3. Cover every entry path the user might have, including the existing-skill case.

Example for a meta-skill:

```markdown
| Your situation | Read |
|---|---|
| New skill from scratch | Phases 1-7 below |
| Existing skill, restructuring | references/migration.md |
| Existing skill, fixing trigger reliability | references/frontmatter-guide.md |
| Debugging skill quality issues | references/gotchas.md |
```

## Reading Order Tables

Use two-column tables in `references/<topic>/README.md` files (or in flat `references/` files when no README exists) to map task type to the sequence of files to read.

Template:

```markdown
## Reading Order

| Task | Files to Read |
|------|---------------|
| <task name> | file1.md → file2.md → file3.md |
```

Rules:
1. Left column: task type from the user's perspective.
2. Right column: file sequence with arrows indicating order.
3. Cover the common task types: quick start, implement feature, debug, performance tuning, batch operations.
4. Place at the top of the README, after the overview and before deep content.

Verbatim example from cloudflare KV README:

```markdown
| Task | Files to Read |
|------|---------------|
| Quick start | README → configuration.md |
| Implement feature | README → api.md → patterns.md |
| Debug issues | gotchas.md → api.md |
| Batch operations | api.md (bulk section) → patterns.md |
| Performance tuning | gotchas.md (performance) → patterns.md (caching) |
```

This transforms reading decisions from reasoning tasks into table lookups.

## Common Combinations Tables

For hubs whose tasks typically require loading 2+ children, pre-compute the combinations.

Template:

```markdown
## Common combinations

Most non-trivial tasks load 2-3 skills. Load the primary skill first, then layer.

| Scenario | Load (in order) |
|---|---|
| <scenario description> | primary → secondary → optional-tertiary |
```

Rules:
1. Identify the 5-10 most common multi-skill tasks.
2. Specify the load order. Primary first; later skills layer on top.
3. Use parentheses for optional layering: `(durable-objects only if customizing the underlying DO)`.

Verbatim example from cloudflare-focused hub:

```markdown
| Scenario | Load (in order) |
|---|---|
| New Worker from scratch | wrangler → workers-best-practices |
| Building a chat room / multiplayer app | durable-objects → workers-best-practices → wrangler |
| Building an AI agent (chat, MCP server, scheduled) | agents-sdk → wrangler (durable-objects only if customizing the underlying DO) |
```

Pre-computed combinations remove the agent's burden of inferring multi-skill compositions.

## Discovery Hints

For hubs where task signals can be ambiguous, add a Discovery Hints section with concrete code-level signals.

Template:

```markdown
## Discovery hints

If unsure which skill applies, look for these in the user's message or the code:

- `<concrete code signal>` → <skill name>
- `<concrete file or command signal>` → <skill name>
```

Rules:
1. Use code signals when natural-language task descriptions are ambiguous.
2. Quote the signal exactly as it would appear: `import { DurableObject } from "cloudflare:workers"`.
3. Map each signal to exactly one skill (or list "ambiguous, see X" if truly ambiguous).

Verbatim example from cloudflare-focused hub:

```markdown
- `import { DurableObject } from "cloudflare:workers"` → durable-objects
- `import { Agent, … } from "agents"` or `from "agents/react"` → agents-sdk
- `import { McpAgent }` or MCP server/transport mentions → agents-sdk
- `wrangler …` in shell, or any `wrangler.jsonc` field discussion → wrangler
```

## Cross-Cutting Rules

Rules that apply across all child skills (or all reference topics) of a hub. Hoist them to the hub level so children stay focused and so an agent loading the hub sees them once instead of N times.

Template:

```markdown
## Cross-cutting rules (apply regardless of [skill | topic])

- **<rule heading>**. <one-or-two-sentence rule with rationale or example>.
- **<rule heading>**. <...>
```

Rules:
1. Bold the rule heading for fast scanning.
2. One sentence per rule when possible. Two sentences when the rationale is non-obvious.
3. Phrase as imperative (`Prefer JSONC over TOML`) not descriptive (`JSONC is preferred`).

Verbatim example from cloudflare-focused hub:

```markdown
- **`wrangler.jsonc` is canon.** Prefer JSONC over TOML; newer features are JSON-only.
- **`compatibility_date` recent + `nodejs_compat` flag.** Most libraries assume both.
- **`wrangler types` after every config change.** Never hand-write the `Env` interface.
- **Secrets via `wrangler secret put` (interactive) or `secret bulk` from file.** Never echo, log, hardcode, or pass as CLI args.
```

## Out-of-Scope Declarations

Every skill must declare what it does NOT cover and where to go instead.

Template:

```markdown
## Out of scope

This skill covers <scope>. It does NOT cover:

- **<topic>**: <one-line redirect or explanation>
- **<topic>**: <...>
```

Rules:
1. Name each excluded topic explicitly.
2. Provide a redirect: name the alternative skill, link the canonical doc, or explain why the topic is excluded.
3. Keep this section at the bottom of the body so the agent reads it last (after the procedural content).

Verbatim example:

```markdown
## Out of scope here

- Generic frontend frameworks deployed to Pages — load **wrangler** for `wrangler pages …`, otherwise framework-specific skills.
- Workflows authored *outside* the Agents SDK — see [Rules of Workflows](https://developers.cloudflare.com/workflows/build/rules-of-workflows/); no dedicated child skill yet.
- Cloudflare Access/Zero Trust, Magic Transit, Stream — not covered by this set.
```

## Four-Part Gotcha Structure

Failure-mode entries in `gotchas.md` (or any gotchas section) must follow a strict four-part structure for fast pattern-matching against live errors.

Template:

```markdown
### "<exact error name as it would appear in logs>"

**Cause:** <one-sentence cause>
**Solution:** <one-sentence solution>

```<language>
// ❌ BAD: <bad approach>
<bad code>

// ✅ GOOD: <good approach>
<good code>
```

Rules:
1. **Quoted error name first.** Use the exact string the agent would match in a stack trace, log, or error message. If there is no canonical error name, use a descriptive phrase in quotes.
2. **Cause line.** One sentence explaining why this happens, not how to fix it.
3. **Solution line.** One sentence with the fix. If the fix has multiple steps, list them as a sub-list under the Solution line.
4. **Bad/good code pair.** A runnable code example showing both the wrong way and the right way, with `❌ BAD` and `✅ GOOD` markers as comments.

Verbatim example from cloudflare KV gotchas.md:

```markdown
### "Stale Read After Write"

**Cause:** Eventual consistency means writes may not be immediately visible in other regions
**Solution:** Don't read immediately after write; return confirmation without reading or use the local value you just wrote.

```typescript
// ❌ BAD: Read immediately after write
await env.KV.put("key", "value");
const value = await env.KV.get("key"); // May be null in other regions!

// ✅ GOOD: Use the value you just wrote
const newValue = "value";
await env.KV.put("key", newValue);
return new Response(newValue); // Don't re-read
```

This four-part structure lets an agent debugging a live error match the quoted error name to the entry, read the Cause to confirm context, apply the Solution, and verify against the bad/good code pair.

### When the four-part structure does not fit

Some gotchas are not error-message-shaped (e.g., "this performs poorly under load"). For those, use a similar four-part structure with adapted parts:

```markdown
### "<symptom name>"

**Symptom:** <how the failure manifests>
**Cause:** <root cause>
**Solution:** <fix>

[bad/good code pair when applicable]
```

The structure is the same; only the labels differ.

## Composing the Routing Primitives in a Hub Body

A complete hub SKILL.md body composes the primitives in this order:

1. **Title and one-line framing** (1-2 lines)
2. **Operating principles or biases declaration** (5-10 lines)
3. **Quick Navigation OR Triage Table** (use Quick Navigation for non-hubs, Triage for hubs)
4. **Decision trees** (for reference-hubs covering many topics)
5. **Common Combinations table** (for skill-set hubs with multi-skill tasks)
6. **Discovery Hints** (when ambiguity is common)
7. **Cross-cutting rules** (when shared rules exist)
8. **Procedural steps** (the workflow, if applicable)
9. **Out of scope** (always last)

Not every hub needs every primitive. The hub body should include only the primitives that match the routing problems it actually has.

## Composing the Routing Primitives in a Non-Hub Body

A standalone or member SKILL.md body uses a subset:

1. **Title and one-line framing**
2. **Operating principles**
3. **Quick Navigation table**
4. **Procedural steps or core content**
5. **Cross-cutting rules** (if any, even single-skill skills can have them)
6. **Out of scope**

## Gotchas

### Decision tree leaves are vague

**Symptom:** A leaf like "for general usage, see the docs" or "consult the appropriate file."

**Cause:** Author did not have a concrete destination at design time and used a placeholder.

**Solution:** Every leaf must resolve to a concrete file or topic. If no concrete destination exists, the leaf does not belong in the tree; restructure the tree.

### Triage table signals are too generic

**Symptom:** Left column reads "general task" or "API call." The agent cannot disambiguate.

**Cause:** Author tried to be flexible but flexibility costs routing accuracy.

**Solution:** Use specific signals. Names of commands, files, imports, error types. The narrower the signal, the more reliable the routing.

### Reading order table missing or buried

**Symptom:** README has good content but no reading order table, or it is at the bottom of the file.

**Cause:** Author wrote the deep content first and never added the navigation surface.

**Solution:** Add the table in the top third of the README. Treat it as table of contents for task types.

### Cross-cutting rules duplicated in children

**Symptom:** The same rule appears in 3+ child SKILL.md files. When the rule changes, only some children update.

**Cause:** Cross-cutting rules were not hoisted to the hub.

**Solution:** Move the rule to the hub. Children may briefly reference it ("see hub for the canonical rule") but should not restate it.

### Gotchas without quoted error names

**Symptom:** Gotcha entries use prose headings like "Watch out for stale reads" instead of `"Stale Read After Write"`.

**Cause:** Author thought of failures conceptually rather than by their observable signature.

**Solution:** Use the error message or error name as it appears in stack traces. The agent matches against the actual symptom.

### Out-of-scope section missing

**Symptom:** Skill triggers for adjacent domains because boundaries are implicit.

**Cause:** Author thought the scope was obvious from the description.

**Solution:** Add an explicit Out-of-Scope section with redirects. The cost is small; the disambiguation value is large.

## See Also

- [topology-decision.md](./topology-decision.md) for which routing primitives apply to which topology
- [taxonomy-templates.md](./taxonomy-templates.md) for the file structure that the routing primitives navigate
- [frontmatter-guide.md](./frontmatter-guide.md) for description routing (the layer above body routing)
- [gotchas.md](./gotchas.md) for the four-part structure applied to skill-creation failures
