# {{COMPONENT_NAME}} - GOD Document

> **Guaranteed Organizational Document** - Developer-facing reference for {{COMPONENT_NAME}}
>
> **Last Updated**: {{DATE}}
> **Domain**: {{DOMAIN}}
> **Status**: {{STATUS}}

---

## Product Overview

{{NON_TECHNICAL_OVERVIEW}}

**Key Capabilities:**
- {{CAPABILITY_1}}
- {{CAPABILITY_2}}
- {{CAPABILITY_3}}

---

## Architecture Position

```mermaid
graph TB
    subgraph "33GOD Pipeline"
        {{UPSTREAM_COMPONENTS}}
        Component[{{COMPONENT_NAME}}]
        {{DOWNSTREAM_COMPONENTS}}
    end

    {{UPSTREAM_CONNECTIONS}}
    {{DOWNSTREAM_CONNECTIONS}}
```

**Role in Pipeline**: {{PIPELINE_ROLE}}

---

## Event Contracts

### Bloodbank Events Emitted

| Event Name | Routing Key | Payload Schema | Trigger Condition |
|------------|-------------|----------------|-------------------|
{{#each EMITTED_EVENTS}}
| `{{name}}` | `{{routing_key}}` | `{{schema}}` | {{trigger}} |
{{/each}}

### Bloodbank Events Consumed

| Event Name | Routing Key | Handler | Purpose |
|------------|-------------|---------|---------|
{{#each CONSUMED_EVENTS}}
| `{{name}}` | `{{routing_key}}` | `{{handler}}` | {{purpose}} |
{{/each}}

---

## Non-Event Interfaces

### CLI Interface
{{#if HAS_CLI}}
```bash
{{CLI_EXAMPLES}}
```

**Commands:**
{{CLI_COMMAND_TABLE}}
{{else}}
_No CLI interface_
{{/if}}

### API Interface
{{#if HAS_API}}
**Base URL**: `{{API_BASE_URL}}`

**Endpoints:**
{{API_ENDPOINTS_TABLE}}
{{else}}
_No API interface_
{{/if}}

---

## Technical Deep-Dive

### Technology Stack
- **Language**: {{LANGUAGE}}
- **Framework**: {{FRAMEWORK}}
- **Dependencies**: {{KEY_DEPENDENCIES}}

### Architecture Pattern
{{ARCHITECTURE_PATTERN_DESCRIPTION}}

### Key Implementation Details
{{IMPLEMENTATION_NOTES}}

### Data Models
{{DATA_MODELS}}

### Configuration
{{CONFIGURATION_DETAILS}}

---

## Development

### Setup
```bash
{{SETUP_COMMANDS}}
```

### Running Locally
```bash
{{RUN_COMMANDS}}
```

### Testing
```bash
{{TEST_COMMANDS}}
```

---

## Deployment

{{DEPLOYMENT_NOTES}}

---

## References

- **Domain Doc**: `docs/domains/{{DOMAIN}}/GOD.md`
- **System Doc**: `docs/GOD.md`
- **Source**: `{{SOURCE_PATH}}`
