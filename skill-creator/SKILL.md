---
name: skill-creator
description: Create, restructure, compose, and migrate skills for agentic CLI tools (Claude Code, Codex, OpenCode, etc.). Use when authoring a new SKILL.md, deciding skill topology (standalone vs member vs hub), designing a references/ taxonomy, building routing mechanics (decision trees, triage tables, reading order tables), writing keyword-dense descriptions that trigger reliably, hoisting cross-cutting rules to a hub, authoring gotchas in the four-part structure, scaffolding with init_skill.py, packaging with package_skill.py for distribution, or migrating an existing skill between topologies (standalone-to-member, member-to-hub, flat-to-hub). Biases towards progressive disclosure, hub-and-spoke composition over monoliths, and concise SKILL.md bodies (target <250 lines) with deep content in references/.
references:
  - topology-decision
  - taxonomy-templates
  - routing-mechanics
  - migration
  - frontmatter-guide
  - design-principles
  - anatomy
  - gotchas
  - output-patterns
  - workflows
---

# Skill Creator

Build skills that trigger reliably, route efficiently, and compose into larger systems. The workflow below produces skills ranging from 20-line standalones to 60-product reference-hubs. The shape of the output is determined by Phase 2 (topology decision); the rest of the workflow specializes accordingly.

## Operating Principles

Internalize these before authoring or modifying any skill:

- **Concise is canon.** The context window is a public good. Every paragraph must justify its tokens.
- **The agent is already smart.** Add only what the agent does not already know.
- **Progressive disclosure is structural, not aspirational.** Long content lives in `references/`, linked from SKILL.md with explicit loading conditions.
- **Trigger logic lives in the description.** "When to use" sections in the body are unreachable; the body loads only after triggering.
- **Topology is a deliberate choice, not an emergent property.** Decide standalone vs member vs hub in Phase 2, before writing any prose.
- **Routing is a primitive, not prose.** Hub bodies are decision trees, triage tables, reading order tables, not tutorials.
- **Test scripts by running them.** Reading code does not surface runtime errors.

## Quick Navigation

| Your situation | Read |
|---|---|
| New skill, starting from scratch | All phases below, in order |
| Existing skill, restructuring | [Phase 9 (Migration)](#phase-9-migration-conditional) and [references/migration.md](./references/migration.md) |
| Choosing topology (standalone/member/hub) | [Phase 2](#phase-2-decide-topology) and [references/topology-decision.md](./references/topology-decision.md) |
| Designing the references/ taxonomy | [Phase 4](#phase-4-design-the-reference-taxonomy) and [references/taxonomy-templates.md](./references/taxonomy-templates.md) |
| Building hub routing (decision trees, triage) | [Phase 6](#phase-6-build-routing-mechanics) and [references/routing-mechanics.md](./references/routing-mechanics.md) |
| Fixing trigger reliability | [Phase 3](#phase-3-author-the-description) and [references/frontmatter-guide.md](./references/frontmatter-guide.md) |
| Authoring gotchas | [routing-mechanics.md (Four-Part Structure)](./references/routing-mechanics.md) |
| Producing structured output (reports, formatted text) | [references/output-patterns.md](./references/output-patterns.md) |
| Designing multi-step procedures within a skill | [references/workflows.md](./references/workflows.md) |
| Debugging skill-creation failures | [references/gotchas.md](./references/gotchas.md) |

## Topology Decision Tree

Every skill is one of three topologies. The choice drives the rest of the workflow.

```
Does the skill cover one capability or many sub-capabilities?
├─ One capability
│  └─ Will it compose into 2+ skill-sets alongside related siblings?
│     ├─ Yes → MEMBER (lives in all-skills/, designed for symlink composition, has scope contract)
│     └─ No  → STANDALONE (lives in all-skills/, atomic capability)
└─ Many sub-capabilities (4+)
   └─ Are children tightly coupled to one platform, or independently composable?
      ├─ Tightly coupled to one platform → REFERENCE-HUB (one skill, references/<topic>/ subdirs)
      └─ Independently composable into other skill-sets → SKILL-SET HUB (skill-sets/<name>/, symlinked siblings)
```

For criteria, worked examples, and hub-flavor selection, read [references/topology-decision.md](./references/topology-decision.md).

## Workflow

The eight phases below produce a new skill. Phase 9 handles migration of existing skills between topologies. Phases 1-2 are universal; Phases 3-8 specialize based on the topology chosen in Phase 2.

### Phase 1: Gather Examples and Scope Boundaries

Skip only when usage patterns are already clearly understood.

Gather two artifacts:
1. **Concrete usage examples**: 3-5 realistic prompts and the desired skill behavior for each.
2. **Out-of-scope examples**: 3-5 prompts that look related but should NOT trigger this skill, with the alternative skill that should handle each.

Useful elicitation questions:
- "What functionality should this skill support?"
- "What would a user say that should trigger this skill?"
- "What would a user say that looks similar but should trigger a different skill?"

The out-of-scope examples seed Phase 6's Out-of-Scope section and prevent over-triggering.

### Phase 2: Decide Topology

Apply the topology decision tree above. Output: one of `STANDALONE`, `MEMBER`, `REFERENCE-HUB`, `SKILL-SET HUB`.

Decision criteria summarized:
- **Standalone**: 1 capability, no anticipated composition into other skill-sets.
- **Member**: 1 capability, 2+ skill-sets benefit from composing it. Requires explicit scope contract (Phase 6 Out-of-Scope).
- **Reference-hub**: 4+ tightly-coupled sub-domains under one platform/vendor.
- **Skill-set hub**: 4+ sub-domains as independently composable members.

Mixed flavor (reference-hub + skill-set hub for the same platform) is permitted; cloudflare uses both. Build the reference-hub first; add the skill-set hub when specific common compositions emerge.

For full criteria and worked examples, read [references/topology-decision.md](./references/topology-decision.md).

### Phase 3: Author the Description

The description is the routing key. The agent reads only `name` and `description` before deciding to load the body.

Required components, regardless of topology:
1. What the skill does (the outcome).
2. Concrete trigger keywords: every artifact name, command, file format, library, and domain term.
3. When-to-use signals (`Use when...`).
4. Optional but valuable: when-to-skip signals (`Do NOT use for...`) and biases declaration (`Biases towards...`).

Topology-specific additions:
- **Hub descriptions** name every child or major topic explicitly. List children's keywords with high density.
- **Member descriptions** state composition affordance: "Composable into [skill-set X, skill-set Y]" or use scope-contract language.

Validate the description by drafting 5 sample prompts (real and adjacent) and checking that the description matches only the prompts that should trigger.

For weak-vs-strong examples, hub-specific patterns, and the optional `references` frontmatter field, read [references/frontmatter-guide.md](./references/frontmatter-guide.md).

### Phase 4: Design the Reference Taxonomy

Pick a taxonomy template by domain type:

| Domain | Template | Files |
|---|---|---|
| API/SDK/product | API/Product | README, api, patterns, gotchas, configuration (per topic for hubs) |
| Meta-skill (about authoring/reviewing) | Meta | anatomy, design-principles, frontmatter-guide, gotchas, output-patterns, workflows |
| Workflow orchestration | Workflow | phases, decision-points, gotchas, output-templates |
| Tool/CLI | Tool | commands, configuration, recipes, gotchas |

For hubs, apply the template per topic directory. For members and standalones, apply the template at the flat references/ level.

Output of Phase 4: a populated rename map of files to create, with the chosen template applied. For hubs, also: the list of children (skill-set hub) or topic directories (reference-hub).

For full templates, hybrid taxonomies, and topic naming conventions, read [references/taxonomy-templates.md](./references/taxonomy-templates.md).

### Phase 5: Initialize and Implement Resources

Skip if the skill already exists.

For a new skill, run `init_skill.py`:

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

This creates the skill directory with template SKILL.md and example `scripts/`, `references/`, `assets/`.

Implementation order:
1. Create the reference taxonomy from Phase 4. Populate file scoping per template; add reading order table to each README or longest reference file (see [routing-mechanics.md](./references/routing-mechanics.md)).
2. Implement bundled resources: scripts (test by running, not by reading), assets (templates and static files).
3. For hub topologies, scaffold child skills (skill-set hub) or topic directories (reference-hub) per Phase 4.
4. Delete unused example files generated by `init_skill.py`.

For structural reference on what goes in scripts/ vs references/ vs assets/, read [references/anatomy.md](./references/anatomy.md).

### Phase 6: Build Routing Mechanics in SKILL.md

The body is a routing surface. Compose primitives by topology:

| Primitive | Standalone | Member | Reference-Hub | Skill-Set Hub |
|---|---|---|---|---|
| Operating Principles | recommended | recommended | required | required |
| Quick Navigation table | required | required | optional | optional |
| Decision trees (multiple, by intent) | optional | optional | required | optional |
| Triage table (signal → file) | n/a | n/a | optional | required |
| Common Combinations table | n/a | n/a | optional | recommended |
| Discovery Hints (code signals) | optional | optional | optional | recommended |
| Cross-cutting rules | n/a | optional | required | required |
| Out-of-Scope | required | required (scope contract) | required | required |
| Gotchas (four-part structure) | recommended | recommended | recommended | recommended |

Place primitives in this order in the body:
1. Title and one-line framing
2. Operating principles or biases declaration
3. Quick Navigation OR Triage Table
4. Decision trees (reference-hubs)
5. Common Combinations (skill-set hubs)
6. Discovery Hints (when ambiguous)
7. Cross-cutting rules (when shared rules exist)
8. Procedural steps or workflow (if applicable)
9. Out of scope (always last)

For exact templates, anti-patterns, and the four-part gotcha structure, read [references/routing-mechanics.md](./references/routing-mechanics.md).

### Phase 7: Validate Trigger and Disclosure

Run this checklist before packaging:

- **Description completeness:** 5 sample prompts triggered, 5 negative prompts skipped.
- **No trigger logic in body:** "When to Use This Skill" sections in the body are deleted (those instructions belong in the description).
- **Frontmatter has only `name`, `description`, and optional `references`:** no `license`, `pipeline-status`, `version`, `author`, `tags`.
- **Body length within budget:** standalone <200 lines, member <200, reference-hub <250, skill-set hub <250.
- **References one level deep:** all reference files load directly from SKILL.md or from the first reference loaded. No nested chains.
- **Reading order tables present:** every README.md (or top-level reference file) has a reading order table.
- **Out-of-Scope section present** with explicit redirects.
- **Cross-cutting rules at the right level:** rules applying to all children live in the hub, not duplicated.
- **For hubs only:** every child or topic resolves from the triage table or decision tree to a real file path.

If any check fails, return to the relevant phase. Common failures and recovery patterns are catalogued in [references/gotchas.md](./references/gotchas.md).

### Phase 8: Package and Iterate

Once Phase 7 passes, package:

```bash
scripts/package_skill.py <path/to/skill-folder>
```

The script validates frontmatter, naming, structure, and description quality, then produces a `.skill` file (zip with `.skill` extension) preserving directory structure.

Iteration loop after real-world use:
1. Use the skill on real tasks.
2. Capture failure modes (add to references/gotchas.md in four-part structure).
3. Update SKILL.md or references.
4. Re-validate (Phase 7) and re-package (Phase 8).

For common iteration patterns and signals that suggest a topology change, see [references/migration.md](./references/migration.md).

### Phase 9: Migration (Conditional)

Use this phase when modifying an existing skill, not creating one. Migration paths:

| Trigger | Migration | Effort |
|---|---|---|
| Standalone now wanted by 2+ skill-sets | Standalone → Member | Small |
| Member body crossed 500 lines with 4+ themes | Member → Hub | Medium |
| Single SKILL.md bloated past 500 lines | Flat → Hub or Better References | Medium-Large |
| Hub has only 1-2 children always loaded together | Hub → Member | Small-Medium |
| Reference-hub topics are wanted independently | Reference-Hub → Skill-Set Hub | Medium |
| Member has 2-3 distinct capabilities under one name | Member → Multiple Members | Small-Medium |

Migration discipline:
1. Take inventory: every file, every consuming skill-set.
2. Plan a complete rename map before moving any file.
3. Migrate in a single commit; partial migrations leave inconsistent state.
4. Update consuming skill-sets in the same commit.
5. Run Phase 7 validation against the new shape.

For step-by-step procedures per migration type, read [references/migration.md](./references/migration.md).

## Cross-Cutting Rules

These apply to every skill regardless of topology or domain:

- **Frontmatter has only `name`, `description`, and optional `references`.** No `license` (use LICENSE.txt), no `pipeline-status`, no `version` (versioning lives at the .skill distribution layer), no `author` (git history is authoritative), no `tags`.
- **Description contains all trigger logic.** Body content loads only after triggering; trigger conditions in the body are unreachable.
- **References load on demand.** Each reference linked from SKILL.md must include an explicit loading condition: "For X task, read references/Y.md" or via a reading order table.
- **References are one level deep.** All reference files load directly from SKILL.md or from the first reference loaded. No deep chains.
- **Imperative form throughout.** Write "Do X" not "This skill does X".
- **Examples are concrete and complete.** Use real names and runnable code, not placeholders like `function foo()`.
- **No README.md, INSTALLATION_GUIDE.md, or other auxiliary docs in the skill itself.** The skill contains only what an agent needs to act. Repo-level READMEs are fine; in-skill READMEs are not (the SKILL.md is the README).
- **Skills exist once in `all-skills/` and are composed via symlinks.** No duplicate skill content across skill-sets. The single source of truth is `all-skills/<name>/`.
- **Hubs do not duplicate child content.** A hub's references describe routing and shared rules, not the children's content. Children's content lives in children.

## Out of Scope

This skill covers SKILL.md packages for agentic CLI tools (Claude Code, Codex, OpenCode, and compatible harnesses). It does NOT cover:

- **MCP tool definitions or the Claude API tool_use format.** Those describe tools to a model at the API level, not skills to an agent harness. Use a dedicated MCP skill or the API documentation directly.
- **Raw system prompt engineering or persona configuration.** Those govern model behavior at the prompt level, below the skill abstraction.
- **Anthropic plugin manifests or Claude.ai extensions.** Plugins use a different format and lifecycle than skills.
- **n8n workflows, automation scripts, or CI/CD pipelines.** These are workflow tools, not agent skills, even when they orchestrate agent calls.
- **CLAUDE.md or AGENTS.md project-level instruction files.** Those configure the harness or repo, not skill content.
- **`.skill` file format internals or harness-specific loading behavior.** Those are platform concerns; this skill produces compliant artifacts but does not specify how harnesses consume them.

For each excluded category, locate the dedicated skill, framework documentation, or harness manual rather than treating the topic as a skill-creation problem.
