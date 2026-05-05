# Skill Design Principles

Reference for the principles that distinguish a skill that loads cleanly and triggers reliably from one that wastes context or fails to fire.

## Reading Order

| Task | Read |
|------|------|
| New skill, deciding structure | This file end-to-end |
| Existing skill bloated past 500 lines | [Progressive Disclosure](#progressive-disclosure) section |
| Skill spans multiple domains or variants | [Pattern 2: Domain-Specific Organization](#pattern-2-domain-specific-organization) |
| Picking how prescriptive to be | [Degrees of Freedom](#degrees-of-freedom) section |
| Designing reference file structure | [Pattern 1: High-Level Guide With References](#pattern-1-high-level-guide-with-references) |
| Debugging disclosure failures | [Gotchas](#gotchas) section |

## Concise Is Key

The context window is a public good. Skills share it with the system prompt, conversation history, other skills' metadata, and the actual user request.

**Default assumption: the agent is already very smart.** Only add context the agent does not already have. Challenge each piece of information:

- "Does the agent really need this explanation?"
- "Does this paragraph justify its token cost?"
- "Could a concrete example replace this prose?"

Prefer concrete examples over verbose explanations. Tables over paragraphs. Code blocks over descriptions of code.

## Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

| Freedom level | When to use | Form |
|---|---|---|
| **High** | Multiple approaches valid, decisions depend on context, heuristics guide the approach | Text-based instructions |
| **Medium** | Preferred pattern exists, some variation acceptable, configuration affects behavior | Pseudocode or scripts with parameters |
| **Low** | Operations are fragile and error-prone, consistency is critical, specific sequence required | Specific scripts with few parameters |

Mental model: the agent is exploring a path. A narrow bridge with cliffs needs specific guardrails (low freedom). An open field allows many routes (high freedom). Match the topology to the terrain.

## Progressive Disclosure

Skills use a three-level loading system to manage context efficiently:

| Level | What loads | Size budget |
|---|---|---|
| **1. Metadata** (`name` + `description`) | Always in context | ~100 words |
| **2. SKILL.md body** | When the skill triggers | <500 lines, target <200 |
| **3. Bundled resources** | As the agent determines need | Effectively unlimited (scripts can execute without loading) |

The agent reads metadata first, then body, then references on demand. Design accordingly: put trigger-relevant content in the description, put procedural instructions in the body, put deep reference material in `references/`.

### Key Principle

When a skill supports multiple variations, frameworks, or options, keep only the core workflow and selection guidance in SKILL.md. Move variant-specific details (patterns, examples, configuration) into separate reference files.

### Pattern 1: High-Level Guide With References

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [forms.md](./forms.md) for complete guide
- **API reference**: See [api.md](./api.md) for all methods
- **Examples**: See [examples.md](./examples.md) for common patterns
```

The agent loads `forms.md`, `api.md`, or `examples.md` only when needed.

### Pattern 2: Domain-Specific Organization

For skills with multiple domains, organize content by domain to avoid loading irrelevant context:

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── references/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

When a user asks about sales metrics, the agent reads only `sales.md`.

For skills supporting multiple frameworks or variants, organize by variant:

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

When the user chooses AWS, the agent reads only `aws.md`.

### Pattern 3: Conditional Details

Show basic content, link to advanced content:

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [docx-js.md](./docx-js.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [redlining.md](./redlining.md)
**For OOXML details**: See [ooxml.md](./ooxml.md)
```

The agent reads `redlining.md` or `ooxml.md` only when the user needs those features.

## Reading Order Tables

Every multi-file references directory should include reading order tables in the entry-point file (typically the longest reference or a README). The table maps task type to file sequence:

```markdown
| Task | Files to Read |
|------|---------------|
| Quick start | overview.md → configuration.md |
| Implement feature | api.md → patterns.md |
| Debug issues | gotchas.md → api.md |
```

This transforms reading decisions from reasoning tasks into table lookups. The agent saves cycles and produces consistent navigation.

## Important Guidelines

- **Avoid deeply nested references.** Keep references one level deep from SKILL.md. All reference files should link directly from SKILL.md or from the file the agent loaded first.
- **Structure longer reference files.** For files longer than 100 lines, include a table of contents or reading order table at the top so the agent sees the full scope when previewing.
- **Cross-reference consistently.** Use relative paths in markdown link syntax: `[gotchas.md](./gotchas.md)`. Use directional cross-references: `api.md` delegates to `gotchas.md` for errors; `gotchas.md` delegates to `patterns.md` for testing examples. Avoid duplication by delegating.
- **Name reference files by content, not by sequence.** Use `gotchas.md` not `step3.md`. Names should signal what is inside.

## Gotchas

### Reference files exist but are never loaded

**Cause:** The reference is mentioned in SKILL.md without explicit loading conditions.
**Solution:** Replace `"See references/X.md"` with `"For Y task, read references/X.md"` so the agent knows when to load it.

### SKILL.md body grows past 500 lines

**Cause:** Anatomy, design principles, and procedural steps are all in the body.
**Solution:** Extract permanent reference material to `references/`. Keep only procedural steps and routing tables in the body.

### Information duplicated between SKILL.md and references

**Cause:** Author copies content into the body for completeness.
**Solution:** Pick one home. If a piece of content is referenced by multiple sections of SKILL.md, leave a one-line summary in the body and full content in `references/`.

### Deeply nested references

**Cause:** Reference files link to other reference files that link to other reference files.
**Solution:** Flatten. All references load directly from SKILL.md or from the first reference loaded. The agent should never need three hops to reach the right content.

## See Also

- [anatomy.md](./anatomy.md) for the structural elements of a skill
- [frontmatter-guide.md](./frontmatter-guide.md) for description writing that affects metadata-level disclosure
- [routing-mechanics.md](./routing-mechanics.md) for the body-level primitives (decision trees, triage tables, reading order tables) that operationalize progressive disclosure
- [taxonomy-templates.md](./taxonomy-templates.md) for reference taxonomies that shape disclosure depth
- [topology-decision.md](./topology-decision.md) for choosing the topology that determines disclosure scale
- [gotchas.md](./gotchas.md) for skill-creation failure modes
