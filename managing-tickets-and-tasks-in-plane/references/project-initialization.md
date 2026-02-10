# Project Initialization Workflow

## Overview

Full onboarding workflow for new projects in Plane, including absurd art generation.

## Prerequisites

- Plane API access configured
- `fal-text-to-image` skill available
- Project has at minimum a README or CLAUDE.md

## Detailed Steps

### Step 1: Project Discovery

```
1. Check for existing `.plane.json` in project root
2. If not found, search Plane for project by:
   - Directory name match
   - Git remote URL patterns
3. If project doesn't exist, prompt to create
```

### Step 2: Art Theme Generation

**Context Gathering:**
- Read project description from README/CLAUDE.md
- Identify core domain (diagramming, task management, AI, etc.)
- Extract any existing mascot/brand references
- Note tech stack for visual element inspiration

**Prompt Construction Formula:**
```
"A weird [DOMAIN_CREATURE] creature that [DOMAIN_ACTIVITY],
with [TECH_STACK_ELEMENTS] as physical features,
[SETTING_FROM_PROJECT_CONTEXT],
surrounded by [DOMAIN_ARTIFACTS],
absurdist corporate art style, vibrant colors,
slightly unsettling but friendly,
like a mascot designed by a 5-year-old CEO"
```

**Example Prompts by Domain:**

| Domain | Creature | Activity | Elements |
|--------|----------|----------|----------|
| Diagramming | chicken/flowchart hybrid | sitting on syntax throne | boxes, arrows, diamonds |
| Task Management | hamster/kanban hybrid | juggling sticky notes | columns, cards, checkmarks |
| AI/ML | octopus/neural net hybrid | processing data streams | neurons, embeddings, tensors |
| DevOps | robot/pipeline hybrid | orchestrating containers | docker whales, kubernetes wheels |
| E-commerce | shopping cart centaur | galloping through checkout | credit cards, receipts |

**Model Selection:**
- Use `recraft/v3/text-to-image` for clean vector style
- Fallback to `flux-2` for more photorealistic absurdity

### Step 3: Label Taxonomy

**Standard Labels (always create):**

```yaml
priority:
  - name: "priority:high"
    color: "#EF4444"  # red
    description: "Urgent, blocks other work"
  - name: "priority:medium"
    color: "#F59E0B"  # amber
    description: "Important but not blocking"
  - name: "priority:low"
    color: "#6B7280"  # gray
    description: "Nice to have"

effort:
  - name: "effort:S"
    color: "#10B981"  # green
    description: "Small, < 2 hours"
  - name: "effort:M"
    color: "#3B82F6"  # blue
    description: "Medium, 2-8 hours"
  - name: "effort:L"
    color: "#8B5CF6"  # purple
    description: "Large, 1-3 days"
  - name: "effort:XL"
    color: "#EC4899"  # pink
    description: "Extra large, > 3 days"

type:
  - name: "type:feature"
    color: "#06B6D4"  # cyan
    description: "New functionality"
  - name: "type:enhancement"
    color: "#14B8A6"  # teal
    description: "Improvement to existing"
  - name: "type:bug"
    color: "#F43F5E"  # rose
    description: "Defect fix"
  - name: "type:chore"
    color: "#78716C"  # stone
    description: "Maintenance task"
```

**Phase Labels (project-specific):**
- Parse PRD for phase structure
- Create `phase:N-shortname` for each phase
- Color gradient from blue (phase 1) to purple (later phases)

**Special Labels (conditional):**
- `premium` - if monetization in PRD
- `security` - if security features mentioned
- `performance` - if performance goals stated

### Step 4: Backlog Seeding

**PRD Parsing:**
1. Look for feature sections (F1.1, F1.2, etc.)
2. Extract user story format
3. Extract acceptance criteria
4. Map to phase labels
5. Estimate effort from complexity indicators

**Ticket Creation Order:**
1. Create all tickets in single batch
2. Assign phase labels
3. Set initial priority based on phase order
4. Link related tickets where dependencies mentioned

### Step 5: Art Theme Documentation

Create `docs/PLANE_ART_THEME.md`:

```markdown
# [Project] Plane Art Theme

## Theme Name
"[Catchy Theme Name]"

## Visual Language
- [Element 1]: [Description]
- [Element 2]: [Description]
- [Recurring motif]: [Description]

## Tone
[One paragraph describing the absurdist vibe]

## Original Mascot Prompt
```
[Full prompt used to generate mascot]
```

## Usage Guidelines

| Ticket Type | Art Direction |
|-------------|---------------|
| Sprint Header | [Mascot doing X] |
| Epic Banner | [Mascot achieving Y] |
| Bug Ticket | [Mascot struggling with Z] |
| Feature Release | [Triumphant mascot] |

## Variation Prompts

### Sprint Planning
"[Mascot] studying a giant calendar made of [domain elements]..."

### Bug Hunting
"[Mascot] with magnifying glass inspecting broken [domain elements]..."

### Feature Ship
"[Mascot] launching [domain artifact] into space..."
```

## Error Handling

| Error | Recovery |
|-------|----------|
| fal.ai unavailable | Skip art, note in output, continue with labels |
| PRD not found | Create minimal labels only, no backlog seeding |
| Project exists with tickets | Skip seeding, only add missing labels |
| Label name conflict | Append project prefix to labels |

## Idempotency

Running initialization twice should:
- NOT duplicate labels (check by name)
- NOT duplicate tickets (check by external_id or title match)
- UPDATE cover image if regenerated
- APPEND new phase labels if PRD updated
