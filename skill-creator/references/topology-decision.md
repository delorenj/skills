# Topology Decision

The first non-obvious decision when authoring a skill is its topology: standalone, member of a skill-set, or hub. The topology determines the rest of the skill's shape: the description form, the references taxonomy, the routing mechanics, and the migration path. Make this decision before writing any prose.

## Reading Order

| Task | Read |
|------|------|
| New skill, choosing topology | [The Three Topologies](#the-three-topologies) and [Decision Criteria](#decision-criteria) |
| Existing skill, considering restructure | [When to Reconsider Topology](#when-to-reconsider-topology) and [migration.md](./migration.md) |
| Picking between hub flavors | [Hub Flavors](#hub-flavors-reference-hub-vs-skill-set-hub) |
| Worked examples | [Examples](#worked-examples) |
| Pitfalls | [Gotchas](#gotchas) |

## The Three Topologies

| Topology | Lives in | Children | Composable into multiple skill-sets | Typical body length |
|---|---|---|---|---|
| **Standalone** | `all-skills/<name>/` | None | No (or one only) | <200 lines |
| **Member** | `all-skills/<name>/` | None | Yes (designed for composition) | <200 lines |
| **Hub** | `all-skills/<name>/` or `skill-sets/<name>/` | Yes (children or topic refs) | Hubs themselves are usually not members | <250 lines |

Visual:

```
all-skills/                         skill-sets/
├── pdf-tools/         (standalone) ├── cloudflare-focused/  (skill-set hub)
├── wrangler/          (member)     │   ├── SKILL.md  (hub)
├── workers-best-prac/ (member)     │   ├── wrangler →  ../../all-skills/wrangler
├── durable-objects/   (member)     │   ├── workers-best-prac → ../../all-skills/workers-best-prac
└── cloudflare/        (hub)        │   └── durable-objects → ../../all-skills/durable-objects
    └── references/                 └── document-tools/  (skill-set hub)
        ├── workers/                    ├── SKILL.md
        ├── kv/                         ├── pdf-tools → ../../all-skills/pdf-tools
        └── d1/                         └── docx-tools → ../../all-skills/docx-tools
        (reference-hub topic dirs)
```

## Decision Criteria

### Standalone

Choose standalone when:

- The skill covers exactly one cohesive capability that does not naturally combine with others
- No anticipated need to compose this skill with siblings under a unified entry point
- The full body fits in <200 lines without splitting

Examples: a one-shot CLI helper, a single file-format converter, a single API integration with no related siblings.

### Member

Choose member when:

- The skill has a single cohesive capability that other skills naturally combine with
- You can imagine 2+ skill-sets that would compose this skill alongside related siblings
- The skill scope is deliberately narrow so a hub can layer multiple members for composite tasks
- The skill has a clear contract with consumers about what it does and does NOT cover (out-of-scope explicit)

Examples: `cloudflare-wrangler` (joins cloudflare-focused, also potentially joins a deployment-focused skill-set), `pdf-tools` (joins document-tools and form-processing skill-sets), `git-commit-conventions` (joins many development skill-sets).

The defining feature of a member is the **scope contract**: explicit out-of-scope declarations that tell hubs what to layer alongside it.

### Hub

Choose hub when:

- The skill coordinates 4+ related sub-domains or child skills
- A user's request typically needs guidance from multiple sub-domains, not just one
- There exists shared cross-cutting knowledge that belongs at the coordinator level (not in any single child)
- Triage cost (deciding which child to use) outweighs the cost of one extra indirection

Examples: cloudflare platform hub, cloudflare-focused skill-set hub, a hypothetical `react-stack` hub coordinating routing/state/styling/testing children.

Hubs come in two flavors. See [Hub Flavors](#hub-flavors-reference-hub-vs-skill-set-hub).

### Quick Decision Tree

```
Does the skill cover one capability or many sub-capabilities?
├─ One capability
│  └─ Will it compose into 2+ skill-sets alongside siblings?
│     ├─ Yes → MEMBER
│     └─ No  → STANDALONE
└─ Many sub-capabilities (4+)
   └─ Are the sub-capabilities related products/topics, or sibling-skills?
      ├─ Related topics under one umbrella → REFERENCE-HUB (own skill, references/topic/)
      └─ Sibling skills already exist → SKILL-SET HUB (skill-sets/X/, symlinked children)
```

## Hub Flavors: Reference-Hub vs Skill-Set Hub

### Reference-Hub

Lives at `all-skills/<name>/SKILL.md`. Children are subdirectories under `references/<topic>/`, each with its own taxonomy of files (e.g., `references/kv/api.md`, `references/kv/patterns.md`).

Choose reference-hub when:
- The sub-domains are tightly coupled to one platform/product/vendor
- The sub-domains do not need to be reused independently in other skill-sets
- One canonical source of truth for the platform makes sense (e.g., the cloudflare platform)

Example: `all-skills/cloudflare/` covers 60+ Cloudflare products as `references/<product>/` directories.

### Skill-Set Hub

Lives at `skill-sets/<name>/SKILL.md`. Children are sibling skills symlinked from `all-skills/`, e.g., `skill-sets/cloudflare-focused/cloudflare-wrangler -> ../../all-skills/cloudflare-wrangler`.

Choose skill-set hub when:
- Children are independently useful and may join multiple skill-sets
- Children have their own SKILL.md that triggers and loads independently
- The hub's job is composition, not authorship of the children's content

Example: `skill-sets/cloudflare-focused/` symlinks four members (wrangler, workers-best-practices, durable-objects, agents-sdk) and triages between them.

### Mixed

Some platforms warrant both: a reference-hub for breadth (the platform skill) and a skill-set hub for depth (the focused composition). Cloudflare uses both. Build the reference-hub first; add the skill-set hub when specific child compositions emerge as common combinations.

## When to Reconsider Topology

Trigger conditions that suggest a topology change:

| Symptom | Likely change | See |
|---|---|---|
| Standalone skill keeps getting new sub-capabilities, body crossing 300 lines | Standalone → Member, then Member → Hub | [migration.md](./migration.md) |
| Two skill-sets keep wanting to use the same content | Standalone → Member | [migration.md](./migration.md) |
| Members in one skill-set are always loaded together | Skill-set hub justified | [migration.md](./migration.md) |
| Reference-hub has 50+ topic directories, becoming unwieldy | Add a skill-set hub for the most common subset | [migration.md](./migration.md) |
| Hub has only 1-2 children that are never used independently | Hub may be premature; collapse back to standalone | [migration.md](./migration.md) |

## Worked Examples

### Example 1: `pdf-tools` as Member

A skill for PDF manipulation. Capabilities: rotation, merging, text extraction, form filling.

Why member, not standalone: PDF work commonly composes with document conversion (`docx-tools`), OCR (`ocr-tools`), and report generation (`report-builder`). These four naturally cluster under a `document-tools` skill-set.

Why member, not hub: PDF tools is one cohesive capability with sub-operations, not 4+ sibling-skills that need their own SKILL.md. The sub-operations (rotation, merging, etc.) are reference topics, not separate skills.

If PDF work later requires distinct rendering, parsing, and signing children with their own descriptions, member becomes hub via [migration.md](./migration.md).

### Example 2: `cloudflare-wrangler` as Member

A skill for the Wrangler CLI. Capabilities: wrangler.jsonc config, deploys, secrets, types, environments.

Why member: Wrangler is one cohesive tool. It naturally composes with Worker authoring (`workers-best-practices`), runtime (`workers-runtime`), and Durable Objects (`durable-objects`). Used alone for CLI tasks; used with siblings for full-stack tasks.

The `cloudflare-focused` skill-set hub triages between members based on task signal.

### Example 3: `cloudflare` as Reference-Hub

The platform-wide cloudflare skill at `all-skills/cloudflare/`. Covers 60+ products.

Why reference-hub: All children are Cloudflare-specific products that share retrieval sources, type generation flows, and configuration patterns. They do not need independent lives outside Cloudflare context.

Why not skill-set hub: 60 symlinked children would be unwieldy. Subdirectory per topic with the five-file taxonomy is the right shape.

### Example 4: `cloudflare-focused` as Skill-Set Hub

The four-skill composition at `skill-sets/cloudflare-focused/`.

Why skill-set hub: The four children (wrangler, workers-best-practices, durable-objects, agents-sdk) are independently useful in other contexts (e.g., wrangler appears in deployment-focused skill-sets). Each has its own SKILL.md and triggers independently. Composition is the hub's job.

## Gotchas

### Choosing standalone when the skill is actually a member

**Symptom:** Two months in, you copy the skill into another skill-set because composition is not formalized. Now you have two divergent copies.

**Cause:** Standalone was chosen because the second use case was not foreseen.

**Solution:** Default to member when in doubt. The cost of marking a skill as member (writing an explicit out-of-scope section) is small. The cost of converting a divergent copy back to a single source of truth is large.

### Choosing hub prematurely

**Symptom:** Hub with 1-2 children, both of which are never used independently. Hub adds an indirection without saving any cost.

**Cause:** Author anticipated growth that did not materialize.

**Solution:** Start with standalone or member. Promote to hub only when the 4+ children criterion is met. See `migration.md` member-to-hub for the upgrade path.

### Choosing reference-hub when skill-set hub fits better

**Symptom:** Reference-hub's references/topic/ directories are actually independent skills that other skill-sets want to compose.

**Cause:** Author treated topics as content rather than as composable units.

**Solution:** Identify the topics that need independent lives. Move those out of references/ and make them member skills under all-skills/. The hub becomes a skill-set hub, or a hybrid with reference-hub for tightly-coupled topics and skill-set hub for composable ones.

### Mixing scope contracts

**Symptom:** A member skill has no out-of-scope section and the consuming hub does not know what to layer alongside it.

**Cause:** Member status was chosen but the scope contract was never written.

**Solution:** Every member's SKILL.md must end with an explicit Out-of-Scope section that names the adjacent skills the consumer should layer in.

## See Also

- [taxonomy-templates.md](./taxonomy-templates.md) for the reference structure that goes with each topology
- [routing-mechanics.md](./routing-mechanics.md) for the routing patterns hubs use
- [migration.md](./migration.md) for converting between topologies
- [frontmatter-guide.md](./frontmatter-guide.md) for description forms specific to each topology
