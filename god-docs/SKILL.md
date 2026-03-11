---
name: god-docs
description: "Implement and maintain the GOD doc system - a documentation strategy for multi-component repositories. Use when: (1) a task requires any code modifications or analysis, (2) adding or modifying any documentation, (3) auditing doc freshness and detecting drift"
---

# GOD Docs

Developer-facing, template-enforced, dependency-tracked, deterministically verifiable architecture documentation.

## Core Concept

GOD Docs treat documentation as a **build artifact**. Staleness is computed, not guessed. Three-level hierarchy (System → Domain → Component), template-enforced structure, declared inter-doc dependencies, and enforcement via git hooks + CI.

Full specification: `references/spec.md`

## Pre-Requisite: Domain Decomposition

Before any GOD Docs, the repo MUST be split into **non-overlapping domains**. Every source file maps to exactly ONE domain. This is what makes dirty-checking deterministic.

## Hierarchy

```
docs/GOD.md                          # Level 0: System
docs/domains/{domain}/GOD.md         # Level 1: Domain
{component}/GOD.md                   # Level 2: Component
```

## Quick Start

### Initialize in a Repo

1. Create template directory and templates:

   ```bash
   mkdir -p docs/templates docs/domains docs/sync
   ```

2. Copy templates from `assets/COMPONENT-GOD-TEMPLATE.md` and `assets/DOMAIN-GOD-TEMPLATE.md`
3. Create system-level `docs/GOD.md` — see `references/spec.md` §3 for required sections
4. Install git hook from `assets/pre-commit` → `.githooks/pre-commit`
5. Run `git config core.hooksPath .githooks`

### Create a Component GOD Doc

1. Copy template: `cp docs/templates/COMPONENT-GOD-TEMPLATE.md {component}/GOD.md`
2. Fill ALL `{{PLACEHOLDER}}` tokens — zero unfilled placeholders allowed
3. Add `<!-- GOD-DEPS: ... -->` declaring upstream GOD Docs this component depends on
4. Register in parent domain GOD Doc (component map + link)
5. Register in system GOD Doc (component registry table)
6. Verify: `grep -c "{{" {component}/GOD.md` must return 0

### Create a Domain GOD Doc

1. Copy template: `cp docs/templates/DOMAIN-GOD-TEMPLATE.md docs/domains/{domain}/GOD.md`
2. Fill all placeholders
3. List all components in this domain with links to their Level 2 GOD Docs
4. Document domain-internal and cross-domain event contracts

## Inter-GOD Dependencies

Each GOD Doc declares dependencies via HTML comment:

```markdown
<!-- GOD-DEPS:
  - event-bus
  - schema-registry
-->
```

Meaning: this component consumes events/schemas/APIs from those components. When a dependency's GOD Doc changes, this doc is transitively flagged stale.

## Dirty-Check Algorithm

```
1. Collect changed files (git diff)
2. Map files → owning component
3. If source changed but GOD.md didn't → DIRTY
4. Walk GOD-DEPS graph: dependents of DIRTY docs → TRANSITIVELY DIRTY
5. Output: all DIRTY ∪ TRANSITIVELY DIRTY
```

Two enforcement layers:

- **Git hook** (pre-commit): interactive prompt, local
- **CI action**: blocks merge on stale docs — see `references/spec.md` §6.3

## Template Required Sections

### Component GOD Doc (Level 2)

- Overview (non-technical)
- Component-Centric Architecture (Mermaid component-level diagram)
- Interfaces (CLI commands, API endpoints)
- Technical Deep-Dive (patterns, implementation)
- Development & Deployment

### Domain GOD Doc (Level 1)

- Domain Overview
- Domain-centric Architecture/Topology (Mermaid diagram)
- Component Summaries (with links to Level 2 docs)
- Cross-Component Interactions and/or Messaging
- Shared Infrastructure

### System GOD Doc (Level 0)

- System Topology (Mermaid diagram)
- Domain Reference Table
- Component Registry (name, domain, status, GOD Doc link)
- Cross-Domain Dependency Graph
- System-Wide Data Flows
- Infrastructure Requirements

## Key Principle

> If you can't cleanly decompose your repo into non-overlapping domains, GOD Docs aren't ready for you yet. Fix that first.
