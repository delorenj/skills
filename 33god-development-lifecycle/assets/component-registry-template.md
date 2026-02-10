# 33GOD Component Registry

**Last Updated**: {YYYY-MM-DD}
**Platform Version**: {Version number or date}

## Overview

This registry tracks all components in the 33GOD platform, their maturity levels, responsibilities, and integration points.

## Component Maturity Summary

| Maturity Level | Count | Components |
|----------------|-------|------------|
| 🟢 Mature (8-9) | {N} | {component-list} |
| 🟡 Developing (5-7) | {N} | {component-list} |
| 🟠 Emerging (2-4) | {N} | {component-list} |
| 🔴 Early (0-1) | {N} | {component-list} |

**Total Components**: {N}

---

## Production Components

### {Component Name}

**Status**: 🟢 Mature | 🟡 Developing | 🟠 Emerging | 🔴 Early
**Maturity Score**: {X}/9
**Type**: {Backend API | Frontend | CLI Tool | Event Backbone | Orchestrator | Storage}

#### Overview
{Brief description of component purpose and responsibilities}

#### Key Capabilities
- {Capability 1}
- {Capability 2}
- {Capability 3}

#### Technology Stack
- **Language**: {Python | TypeScript | Rust | etc}
- **Framework**: {FastAPI | React | etc}
- **Database**: {PostgreSQL | Redis | etc}
- **Deployment**: {Docker | Kubernetes | etc}

#### BMAD Status
- **Project Level**: {0-4}
- **Planning**: {✅ Complete | ⚠️ In Progress | ❌ Not Started}
- **Architecture**: {✅ Complete | ⚠️ In Progress | ❌ Not Started}
- **Testing**: {Coverage percentage}
- **Documentation**: {✅ Complete | ⚠️ Partial | ❌ Missing}

#### Integration Points

**Depends On**:
- {Component A}: {Description of dependency}
- {Component B}: {Description of dependency}

**Consumed By**:
- {Component C}: {How this component is used}
- {Component D}: {How this component is used}

**Event Flows**:
- **Publishes**: {event-type-1}, {event-type-2}
- **Subscribes**: {event-type-3}, {event-type-4}

#### API Contracts
- **REST API**: {URL or file reference}
- **Event Schema**: {File reference}
- **GraphQL Schema**: {File reference if applicable}

#### Deployment Info
- **Repository**: {Git URL or path}
- **Container**: {Docker image name}
- **Ports**: {Port numbers}
- **Environment**: {prod | staging | dev}

#### Monitoring
- **Health Endpoint**: {URL}
- **Metrics**: {Prometheus endpoint or dashboard link}
- **Logs**: {Log aggregation location}
- **Alerts**: {Alert definitions or runbook link}

#### Ownership
- **Primary Team**: {Team name}
- **Tech Lead**: {Name or role}
- **On-Call**: {Rotation or contact}

#### Next Steps
{What needs to happen to improve maturity or add features}

---

{Repeat for each production component}

---

## Components in Development

### {Component Name}

**Status**: 🟠 Emerging
**Maturity Score**: {X}/9
**Target Production Date**: {Estimate or TBD}

#### Purpose
{What this component will do}

#### Current State
- [x] {Completed milestone}
- [ ] {In-progress item}
- [ ] {Planned item}

#### Blockers
- {Blocker 1}
- {Blocker 2}

#### Path to Production
1. {Step 1}
2. {Step 2}
3. {Step 3}

---

{Repeat for each in-development component}

---

## Deprecated / Archived Components

### {Component Name}

**Status**: ⚫ Deprecated
**Deprecation Date**: {YYYY-MM-DD}
**Removal Date**: {YYYY-MM-DD or TBD}

#### Reason for Deprecation
{Why this component is being phased out}

#### Migration Path
{How users should migrate to replacement}

#### Replacement Component
{Component that replaces this functionality}

---

## Component Architecture Diagram

```mermaid
graph TB
    subgraph "33GOD Platform"
        {Component1}[Component 1<br/>Type]
        {Component2}[Component 2<br/>Type]
        {Component3}{{Component 3<br/>Event Backbone}}
        {Component4}[(Component 4<br/>Storage)]

        {Component1} --> {Component3}
        {Component2} --> {Component3}
        {Component3} --> {Component4}
        {Component2} --> {Component4}
    end

    style {Component1} fill:#e1f5ff
    style {Component2} fill:#fff3e0
    style {Component3} fill:#f3e5f5
    style {Component4} fill:#f1f8e9
```

---

## Integration Patterns

### Event-Driven Communication
{Description of how components use events}

**Event Backbone**: {Component name, e.g., bloodbank}
**Message Broker**: {Technology, e.g., RabbitMQ}

**Common Event Patterns**:
- **Request-Response**: {Description}
- **Pub-Sub**: {Description}
- **Event Sourcing**: {Description if applicable}

### Synchronous APIs
{Description of direct API calls between components}

**API Gateway**: {Component name if applicable}
**Authentication**: {OAuth, JWT, API keys, etc}

**Common API Patterns**:
- **REST**: {Description}
- **GraphQL**: {Description if applicable}
- **gRPC**: {Description if applicable}

### Data Flow
{High-level description of data flow through the system}

```
User Action → {Entry Component} → {Processing Components} → {Storage} → {Output}
```

---

## Dependency Matrix

| Component | bloodbank | flume | imi | {other} |
|-----------|-----------|-------|-----|---------|
| bloodbank | -         | ✓     | ✓   | ✓       |
| flume     | ✓         | -     | -   | -       |
| imi       | ✓         | -     | -   | -       |
| {other}   | ✓         | -     | -   | -       |

**Legend**:
- ✓ = Direct dependency (row depends on column)
- - = No direct dependency

---

## Technology Standards

### Preferred Stack
- **Backend**: {Python with FastAPI | TypeScript with Node.js}
- **Frontend**: {React with TypeScript}
- **Database**: {PostgreSQL for relational, Redis for caching}
- **Message Queue**: {RabbitMQ}
- **Containerization**: {Docker with docker-compose}
- **Orchestration**: {Kubernetes | Docker Swarm | None}

### Code Quality Standards
- **Testing**: Minimum 80% coverage for Mature components
- **Linting**: {Tools used, e.g., ruff, eslint}
- **Type Checking**: {mypy for Python, TypeScript strict mode}
- **Documentation**: Docstrings, README, API docs

### Deployment Standards
- **CI/CD**: {GitHub Actions | GitLab CI}
- **Containerization**: All components must have Dockerfile
- **Health Checks**: All services must expose /health endpoint
- **Logging**: Structured JSON logging with trace IDs

---

## Maturity Improvement Roadmap

### Q{N} {Year} Goals

**Target State**:
- {N} components at Mature level
- {N} components at Developing level
- {N} new components initialized

**Priority Actions**:
1. {Component A}: {Action to improve maturity}
2. {Component B}: {Action to improve maturity}
3. {Component C}: {Action to improve maturity}

---

## Component Gaps

**Missing Capabilities**:
- [ ] {Capability 1 needed but no component provides it}
- [ ] {Capability 2}

**Recommended New Components**:
1. **{Component Name}**: {Purpose and justification}
2. **{Component Name}**: {Purpose and justification}

---

## Historical Changes

### {YYYY-MM-DD}
- Added: {Component name}
- Updated: {Component name} - {Change description}
- Deprecated: {Component name}

### {YYYY-MM-DD}
- {Previous changes}

---

## Appendices

### Glossary
- **BMAD**: Breakthrough Method for Agile AI-Driven Development
- **Maturity Score**: 0-9 scale measuring production readiness
- **Component**: Self-contained service or module in the platform

### Contact Information
- **Platform Team**: {Contact method}
- **Architecture Review**: {Contact method}
- **DevOps Support**: {Contact method}

---

**Generated by**: `./scripts/component-inventory.sh`
**Automation**: This file can be regenerated on demand
