# Frontmatter Guide

Reference for designing the YAML frontmatter that determines whether and when a skill triggers. The frontmatter is the most token-efficient surface in the entire skill: it is read once at every prompt, but only briefly. Every word counts.

## Reading Order

| Task | Read |
|------|------|
| New skill, writing the description | [The Description Field](#the-description-field) section |
| Existing skill not triggering reliably | [Common Description Failures](#common-description-failures) section |
| Picking the skill name | [The Name Field](#the-name-field) section |
| Adding optional fields | [Optional Frontmatter Extensions](#optional-frontmatter-extensions) section |
| Multi-skill hub frontmatter | [Hub Skill Frontmatter](#hub-skill-frontmatter) section |

## The Two Required Fields

Every SKILL.md must have:

```yaml
---
name: skill-name
description: One-line summary plus trigger keywords plus when-to-use signals
---
```

These are the only fields guaranteed to be read by the harness for routing. Other fields may be ignored or, in some harnesses, cause errors.

## The Name Field

- Use lowercase kebab-case: `skill-creator`, not `SkillCreator` or `skill_creator`
- Match the directory name exactly: directory `skill-creator/` must contain a SKILL.md with `name: skill-creator`
- Keep it short and descriptive: `pdf-tools` over `pdf-processing-and-manipulation-toolkit`
- Avoid generic names that could collide: `helper`, `utils`, `tools` are too generic

The name is the routing key in some harnesses. Once a skill is published, renaming it breaks all references. Pick well the first time.

## The Description Field

The description is the primary triggering mechanism. The agent reads only the name and description before deciding to load the skill body. If the description does not contain the trigger signals, the skill does not load even when it is the right answer.

### Required Components

Every description must contain:

1. **What the skill does** (the outcome): one phrase describing the core capability.
2. **Concrete trigger keywords**: every artifact name, file format, command, library, framework, or domain term that would appear in a relevant request.
3. **When-to-use signals**: phrases like "Use when...", "Load for...", "Triggers on..." followed by specific scenarios.
4. **When-to-skip signals (optional but valuable)**: phrases like "Do NOT use for..." or "Skip when..." that prevent over-triggering.
5. **Biases declaration (optional)**: phrases like "Biases towards retrieval" or "Prefers X over Y" that set the operating mode before any body content loads.

### Description Length

Aim for 50-200 words. Too short and triggering is unreliable. Too long and the metadata layer becomes bloated.

### Strong Description Example

From `cloudflare` (one of the most polished skills in the ecosystem):

```yaml
description: Comprehensive Cloudflare platform skill covering Workers, Pages, storage (KV, D1, R2), AI (Workers AI, Vectorize, Agents SDK), feature flags (Flagship), networking (Tunnel, Spectrum), security (WAF, DDoS), and infrastructure-as-code (Terraform, Pulumi). Use for any Cloudflare development task. Biases towards retrieval from Cloudflare docs over pre-trained knowledge.
```

What makes it work:
- 50+ trigger keywords in one sentence
- Explicit "Use for any Cloudflare development task" signal
- Biases declaration sets the retrieval-first mode before anything else loads
- Lists every product category, not just the headline ones

### Weak Description Example

```yaml
description: Guide for creating effective skills.
```

What is wrong:
- No trigger keywords (no `SKILL.md`, `init_skill.py`, `.skill`, `references/`)
- No use-case signals
- No bias declaration
- Generic "creating effective" provides no routing value

### Comparing Weak vs Strong

| Description property | Weak | Strong |
|---|---|---|
| Length | <20 words | 50-200 words |
| Trigger keywords | 0-2 | 10-30+ |
| Use-case scenarios | Generic | Specific |
| Skip conditions | None | At least one |
| Operating mode | Implicit | Explicit |

## Common Description Failures

### "When to Use This Skill" content lives in the body, not the description

**Cause:** Author writes the use cases inside SKILL.md body thinking the agent will read them.
**Solution:** All trigger logic must live in the description. The body loads only after the skill triggers, which is too late.

```markdown
# ❌ BAD: trigger logic buried in body
---
name: my-skill
description: Helps with documents.
---

# My Skill
## When to use this skill
Use when working with PDFs, DOCX, or...   # <-- agent never reads this before triggering
```

```markdown
# ✅ GOOD: trigger logic in description
---
name: my-skill
description: PDF and DOCX document creation, editing, and analysis. Use when working with .pdf or .docx files for content extraction, form filling, redlining, format conversion, or document generation.
---

# My Skill
## How to use this skill
[procedural instructions only]
```

### Description names the skill but not its targets

**Cause:** "Skill for working with documents" mentions the action but not the artifacts.
**Solution:** Name every concrete artifact. File extensions (`.pdf`), library names (`pdfplumber`), command names (`wrangler deploy`), and concept names (`tracked changes`) are all triggers.

### Description does not differentiate from sibling skills

**Cause:** Two skills have similar descriptions; the agent loads the wrong one.
**Solution:** Add a "Use this skill for X, NOT for Y (load other-skill instead)" clause.

## Optional Frontmatter Extensions

Some harnesses support extension fields. The two required fields are the only ones guaranteed across all harnesses, but these extensions appear in production:

### `references` (used by some hub skills)

```yaml
references:
  - workers
  - pages
  - d1
```

A hint to the harness about which subdirectories under `references/` to pre-warm. Useful for hubs with 50+ reference directories where pre-warming the most common five reduces first-load latency.

### Things NOT to Include

The following fields are commonly added but should be removed:

- `license:` License terms belong in a `LICENSE` or `LICENSE.txt` file, not in frontmatter
- `pipeline-status:` Build/release state is not skill metadata; it is process metadata
- `version:` Skills are versioned by their containing distribution (a `.skill` file), not in frontmatter
- `author:` Authorship is git history, not metadata
- `tags:` Tags are derivable from the description text

If you see any of these in an existing skill, delete them as part of refactoring.

## Hub Skill Frontmatter

Hubs that route to child skills have specific frontmatter conventions:

```yaml
---
name: cloudflare
description: Hub skill for any Cloudflare Workers platform task. Triages the request and routes to one or more specialized skills covering CLI/config (wrangler), Worker code authoring & review (workers-best-practices), stateful coordination (durable-objects), and AI agents on Workers (agents-sdk). Load when the user mentions Cloudflare, Workers, Pages, Wrangler, Durable Objects, KV, R2, D1, Vectorize, Hyperdrive, Queues, Workflows, Workers AI, the Agents SDK, MCP servers on Workers, or any deploy/dev/binding/observability task targeting Cloudflare's edge.
---
```

Hub-specific elements:
- The word "hub" or "router" in the description
- Explicit naming of every child skill in the description
- A "Load when the user mentions..." clause with high keyword density
- No `references:` field (hubs route to child SKILL.md files, not to subdirectories)

## See Also

- [topology-decision.md](./topology-decision.md) for choosing the topology that drives description form (hub frontmatter differs from member frontmatter)
- [design-principles.md](./design-principles.md) for the broader progressive disclosure model
- [anatomy.md](./anatomy.md) for the relationship between frontmatter and body
- [routing-mechanics.md](./routing-mechanics.md) for the body-level routing the description hands off to
- [gotchas.md](./gotchas.md) for failure modes specific to triggering and frontmatter
