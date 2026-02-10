# Hierarchical BMAD Structure

## Overview

Hierarchical BMAD extends the standard BMAD Method (Breakthrough Method for Agile AI-Driven Development) to support multi-level orchestration across platform and component boundaries.

## Two-Level Architecture

### Meta-Level (Platform)

**Scope**: Entire 33GOD platform ecosystem
**Project Level**: 4 (Enterprise expansion)
**Responsibilities**:
- Strategic platform roadmap
- Cross-component feature coordination
- Integration architecture
- Component portfolio management
- Platform-wide sprint planning

**Artifacts**:
- Platform PRD (product vision across all components)
- System architecture (component interaction patterns)
- Integration map (event flows, API contracts)
- Cross-component user stories
- Platform-wide sprint plans

**Directory Structure**:
```
33GOD/
├── bmad/
│   ├── config.yaml           # Meta-level config (Level 4)
│   └── agent-overrides/
│       └── DirectorOfEngineering.yaml
├── docs/
│   ├── bmm-workflow-status.yaml
│   ├── platform-prd.md
│   ├── system-architecture.md
│   ├── integration-map.md
│   ├── component-inventory.md
│   └── stories/
│       ├── distributed-tracing.md
│       └── unified-cli.md
└── [component directories...]
```

### Component-Level

**Scope**: Individual microservice or subsystem
**Project Level**: 0-3 (varies by component)
**Responsibilities**:
- Component-specific feature development
- Local architecture decisions
- Component documentation
- Component testing and deployment

**Artifacts**:
- Component PRD or Tech Spec
- Component architecture (if Level 2+)
- Component stories and sprint plans
- API documentation
- Test suites

**Directory Structure**:
```
bloodbank/
├── bmad/
│   ├── config.yaml           # Component config (Level 2-3)
│   └── agent-overrides/
├── docs/
│   ├── bmm-workflow-status.yaml
│   ├── prd-bloodbank.md
│   ├── architecture.md
│   └── stories/
└── [component source code...]
```

## Workflow Coordination

### Story Propagation Pattern

**Top-Down**:
1. **Meta-Orchestrator** creates platform-level story
2. Story decomposed into component-specific tasks
3. Tasks delegated to **Component Orchestrators**
4. Component orchestrators run local BMAD workflows
5. Meta-orchestrator tracks integration completion

**Example**:
```
Platform Story: "Add distributed tracing across all components"

Decomposes to:
├─ Bloodbank Task: "Add trace context to event schema"
├─ Flume Task: "Propagate trace IDs in task execution"
└─ iMi Task: "Log trace IDs in CLI operations"

Each component runs its own /create-story workflow
```

### Status Aggregation Pattern

**Bottom-Up**:
1. Each component maintains independent `bmm-workflow-status.yaml`
2. Meta-orchestrator periodically scans all component status files
3. Synthesizes platform-wide status report
4. Identifies cross-component blockers
5. Recommends prioritization adjustments

## Phase Alignment

### Analysis Phase Alignment

**Meta-Level Analysis**:
- Platform vision and market positioning
- Component gap analysis
- Technology stack standardization
- Integration strategy

**Component-Level Analysis**:
- Component-specific use cases
- Technical feasibility studies
- Dependency research

**Handoff**: Platform analysis informs component-level product briefs

### Planning Phase Alignment

**Meta-Level Planning**:
- Platform PRD (what the ecosystem delivers)
- Component responsibility matrix
- Integration contracts (API schemas, event formats)
- Shared infrastructure requirements

**Component-Level Planning**:
- Component PRD or Tech Spec
- Component API design
- Internal architecture decisions

**Handoff**: Platform PRD defines component boundaries and integration requirements

### Solutioning Phase Alignment

**Meta-Level Solutioning**:
- System architecture (how components interact)
- Deployment topology
- Observability architecture
- Security and compliance patterns

**Component-Level Solutioning**:
- Component internal architecture
- Technology choices within component
- Performance optimization strategies

**Handoff**: System architecture defines integration points and constraints

### Implementation Phase Alignment

**Meta-Level Implementation**:
- Cross-component sprint planning
- Integration milestones
- Platform-wide acceptance testing
- Release coordination

**Component-Level Implementation**:
- Component story implementation
- Component testing
- Component documentation
- Component deployments

**Handoff**: Cross-component stories trigger component-level sprints

## Independence vs Coordination

### When Components Work Independently

- Internal refactoring (no API changes)
- Component-specific features (no integration impact)
- Performance optimizations (within component)
- Bug fixes (non-breaking)

→ **Component orchestrator drives workflow autonomously**

### When Coordination Required

- API contract changes (affects consumers)
- Event schema modifications (affects subscribers)
- Breaking changes (requires migration)
- Cross-component features (multi-service)

→ **Meta-orchestrator coordinates, delegates tasks, tracks integration**

## Practical Guidelines

### Meta-Orchestrator Triggers

Use meta-level BMAD when:
- Feature spans 2+ components
- Architecture changes affect multiple services
- Breaking change coordination needed
- Platform-wide standards or policies
- Component portfolio planning

### Component-Orchestrator Triggers

Use component-level BMAD when:
- Feature contained within single component
- Implementation details local to component
- No breaking changes to integration contracts
- Standard component development workflow

### Delegation Mechanics

**File-Based Communication**:
```
Meta creates: 33GOD/docs/stories/platform-story.md
Meta delegates to: bloodbank/docs/delegated-task-20260109.md
Component implements via: bloodbank/docs/stories/story-123.md
Component reports status in: bloodbank/docs/bmm-workflow-status.yaml
Meta aggregates via: scripts/platform-status.sh
```

**Zellij-Based Coordination**:
```bash
# Meta-orchestrator spawns component sessions
zellij --session 33god-platform
  ├─ Tab: bloodbank (component orchestrator running)
  ├─ Tab: flume (component orchestrator running)
  └─ Tab: imi (component orchestrator running)

# Each tab cd's to component dir and runs:
/workflow-status
/create-story "Implement delegated task"
```

## Anti-Patterns

**Don't**:
- Micro-manage component implementations from meta-level
- Skip component-level BMAD for complex features
- Allow components to make breaking changes without meta-level approval
- Duplicate planning artifacts at both levels

**Do**:
- Define clear component boundaries at meta-level
- Let components own their implementation details
- Use meta-level for integration contracts only
- Maintain single source of truth per artifact

## Migration Path

**Existing Component-Only BMAD**:
1. Initialize meta-level BMAD at platform root
2. Keep existing component BMAD workflows intact
3. Create platform architecture document
4. Define integration contracts
5. Begin using meta-level for cross-component work

**New Component**:
1. Check meta-level architecture for component role
2. Initialize component BMAD with aligned project level
3. Reference platform integration contracts
4. Report status to meta-level tracking
