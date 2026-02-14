# {{DOMAIN_NAME}} Domain - GOD Document

> **Guaranteed Organizational Document** - Developer-facing reference for the {{DOMAIN_NAME}} domain
>
> **Last Updated**: {{DATE}}
> **Components**: {{COMPONENT_COUNT}}

---

## Domain Overview

{{DOMAIN_PURPOSE}}

**Responsibilities:**
- {{RESPONSIBILITY_1}}
- {{RESPONSIBILITY_2}}
- {{RESPONSIBILITY_3}}

---

## Component Map

```mermaid
graph TB
    subgraph "{{DOMAIN_NAME}} Domain"
        {{COMPONENT_DEFINITIONS}}
    end

    {{COMPONENT_RELATIONSHIPS}}
    {{EXTERNAL_CONNECTIONS}}
```

---

## Components

{{#each COMPONENTS}}
### {{name}}

**Purpose**: {{purpose}}
**Type**: {{type}}
**Status**: {{status}}

**Key Events:**
- Emits: {{emitted_events}}
- Consumes: {{consumed_events}}

**Interfaces:**
{{interfaces}}

[📄 Component GOD Doc]({{god_doc_path}})

---
{{/each}}

## Domain Event Contracts

### Cross-Component Events

Events that flow between components within this domain:

| Event | Producer | Consumer(s) | Purpose |
|-------|----------|-------------|---------|
{{#each INTERNAL_EVENTS}}
| `{{name}}` | {{producer}} | {{consumers}} | {{purpose}} |
{{/each}}

### External Event Interfaces

Events exchanged with other domains:

| Event | Direction | External Domain | Purpose |
|-------|-----------|-----------------|---------|
{{#each EXTERNAL_EVENTS}}
| `{{name}}` | {{direction}} | {{domain}} | {{purpose}} |
{{/each}}

---

## Shared Infrastructure

{{SHARED_INFRASTRUCTURE_NOTES}}

---

## Development Guidelines

{{DEVELOPMENT_GUIDELINES}}

---

## References

- **System Doc**: `docs/GOD.md`
- **Source Domain Docs**: `docs/domains/{{domain_folder}}/`
