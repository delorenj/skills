# Cross-Component User Stories

## Overview

Cross-component user stories describe features or capabilities that span multiple components in the 33GOD platform. These stories require coordination between component teams and integration verification.

## Story Template

```markdown
# Story: {Feature Name}

## User Story
As a {user type}
I want {capability}
So that {benefit}

## Scope
Components involved: {list}

## Platform-Level Acceptance Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] Integration verified end-to-end

## Component Breakdown

### {Component 1}
**Responsibility**: {What this component must do}

**Acceptance Criteria**:
- [ ] {Component-specific criterion}
- [ ] API contract implemented
- [ ] Tests added

**Dependencies**: {Other components this depends on}
**Estimated Effort**: {S/M/L/XL}

### {Component 2}
{Repeat structure}

## Integration Requirements
- [ ] {Integration test 1}
- [ ] {Integration test 2}
- [ ] End-to-end flow verified

## Deployment Strategy
{How to roll out across components}

## Rollback Plan
{How to revert if integration fails}
```

## Story Examples

### Example 1: Distributed Tracing

```markdown
# Story: Distributed Tracing Across All Components

## User Story
As a **platform operator**
I want **trace IDs propagated through all components**
So that **I can debug issues across service boundaries**

## Scope
Components: bloodbank, flume, imi, all future services

## Platform-Level Acceptance Criteria
- [ ] Trace IDs generated at entry points (CLI, API)
- [ ] Trace IDs propagated through event backbone
- [ ] Trace IDs logged by all components
- [ ] Unified trace visualization available
- [ ] Integration verified end-to-end

## Component Breakdown

### bloodbank (Event Backbone)
**Responsibility**: Add trace context to all events

**Acceptance Criteria**:
- [ ] EventBase schema includes trace_id field
- [ ] Event publisher accepts trace context
- [ ] Trace context propagated to subscribers
- [ ] Backward compatibility maintained

**Dependencies**: None (schema owner)
**Estimated Effort**: M

**Implementation Notes**:
- Add optional trace_id: str to EventBase
- Update publisher to inject trace_id if not provided
- Document schema change in migration guide

---

### flume (Session/Task Manager)
**Responsibility**: Propagate traces through task execution

**Acceptance Criteria**:
- [ ] Extract trace_id from incoming events
- [ ] Attach trace_id to task context
- [ ] Log trace_id in all task operations
- [ ] Emit trace_id in result events

**Dependencies**: bloodbank (requires schema update)
**Estimated Effort**: M

**Implementation Notes**:
- Update TaskContext to include trace_id
- Modify task executor to propagate context
- Add trace_id to structured logging

---

### imi (Worktree Manager)
**Responsibility**: Generate and log traces for CLI operations

**Acceptance Criteria**:
- [ ] Generate trace_id for each CLI command
- [ ] Log trace_id in all operations
- [ ] Emit events with trace_id
- [ ] Display trace_id in verbose mode

**Dependencies**: bloodbank (for event emission)
**Estimated Effort**: S

**Implementation Notes**:
- Use uuid4 for trace generation
- Add trace_id to logger context
- Include trace_id in CLI output with --verbose

---

## Integration Requirements
- [ ] End-to-end trace flow test: CLI → Event → Task → Result
- [ ] Trace continuity verified across all components
- [ ] Observability dashboard shows unified traces
- [ ] Performance impact <5ms per operation

## Deployment Strategy
1. **Phase 1**: Deploy bloodbank (schema backward compatible)
2. **Phase 2**: Deploy flume and imi in parallel
3. **Phase 3**: Verify integration, enable tracing by default

**Rollout Duration**: M effort

## Rollback Plan
1. Disable trace emission at entry points (imi CLI flag)
2. Components continue working without traces
3. No data loss, graceful degradation
```

---

### Example 2: Unified CLI

```markdown
# Story: Unified CLI Wrapper for All 33GOD Tools

## User Story
As a **developer**
I want **a single CLI entry point for all 33GOD operations**
So that **I have a consistent interface and easier discovery**

## Scope
Components: imi, flume, bloodbank, [new: 33god-cli]

## Platform-Level Acceptance Criteria
- [ ] Single binary: `33god` with subcommands
- [ ] All existing functionality preserved
- [ ] Consistent flag patterns across commands
- [ ] Unified help system
- [ ] Configuration management centralized

## Component Breakdown

### 33god-cli (New Component)
**Responsibility**: Provide unified CLI wrapper

**Acceptance Criteria**:
- [ ] Subcommand router implemented
- [ ] Delegates to component CLIs
- [ ] Shared configuration system
- [ ] Consistent logging format
- [ ] Man pages and help system

**Dependencies**: imi, flume, bloodbank (CLI interfaces)
**Estimated Effort**: L

**Implementation Notes**:
- Use Python Click for CLI framework
- Import component CLI modules as plugins
- Shared config: `~/.config/33god/config.yaml`
- Logging: structured JSON with trace support

---

### imi (Worktree Manager)
**Responsibility**: Expose CLI as importable module

**Acceptance Criteria**:
- [ ] CLI functions refactored as library
- [ ] Entry point supports both standalone and imported usage
- [ ] Backward compatibility for `imi` command

**Dependencies**: None
**Estimated Effort**: M

**Implementation Notes**:
- Refactor `cli.py` → `cli_module.py` + `cli_entry.py`
- Export main CLI group for 33god-cli to import
- Maintain `imi` command as alias

---

### flume (Session Manager)
**Responsibility**: Expose CLI as importable module

**Acceptance Criteria**:
- [ ] CLI functions refactored as library
- [ ] Entry point supports both standalone and imported usage
- [ ] Backward compatibility for `flume` command

**Dependencies**: None
**Estimated Effort**: M

**Implementation Notes**:
- Similar refactoring to imi
- Export Flume CLI group

---

### bloodbank (Event Backbone)
**Responsibility**: Provide admin CLI for event inspection

**Acceptance Criteria**:
- [ ] CLI for event monitoring
- [ ] Event replay functionality
- [ ] Queue inspection commands
- [ ] Expose as importable module

**Dependencies**: None
**Estimated Effort**: M-L

**Implementation Notes**:
- Create new `bloodbank_cli` module
- Commands: inspect, replay, monitor, stats

---

## Integration Requirements
- [ ] All component commands accessible via `33god <component> <command>`
- [ ] Shared configuration picked up by all components
- [ ] Consistent help format across all commands
- [ ] Trace IDs work across all CLI operations

## Deployment Strategy
1. **Phase 1**: Refactor imi and flume for importable CLI (parallel)
2. **Phase 2**: Create bloodbank CLI
3. **Phase 3**: Build 33god-cli wrapper
4. **Phase 4**: Documentation and migration guide

**Rollout Duration**: XL effort

## Rollback Plan
1. Individual component CLIs remain functional
2. Users can continue using `imi`, `flume`, `bloodbank` directly
3. `33god` wrapper is additive, not breaking
```

---

### Example 3: Component Health Monitoring

```markdown
# Story: Unified Health Check System

## User Story
As a **platform operator**
I want **a unified health check endpoint across all components**
So that **I can monitor system health from a single dashboard**

## Scope
Components: bloodbank, flume, imi, [new: health-dashboard]

## Platform-Level Acceptance Criteria
- [ ] All components expose `/health` endpoint
- [ ] Health status aggregated in dashboard
- [ ] Dependency health checked (DB, Redis, RabbitMQ)
- [ ] Alerting on unhealthy components
- [ ] Health checks run every 30 seconds

## Component Breakdown

### bloodbank (Event Backbone)
**Responsibility**: Expose health endpoint, check RabbitMQ connection

**Acceptance Criteria**:
- [ ] `/health` endpoint returns 200 if healthy
- [ ] Check RabbitMQ connection status
- [ ] Report queue depths and consumer counts
- [ ] Return 503 if critical issues detected

**Dependencies**: None
**Estimated Effort**: S

---

### flume (Session Manager)
**Responsibility**: Expose health endpoint, check task executor status

**Acceptance Criteria**:
- [ ] `/health` endpoint returns 200 if healthy
- [ ] Check Redis connection for session storage
- [ ] Report active session count
- [ ] Return 503 if task executor unresponsive

**Dependencies**: None
**Estimated Effort**: S

---

### imi (Worktree Manager)
**Responsibility**: Expose health endpoint as CLI command

**Acceptance Criteria**:
- [ ] `imi health` command returns status
- [ ] Check git availability and worktree state
- [ ] Report worktree count and disk usage
- [ ] Exit code 0 if healthy, 1 if unhealthy

**Dependencies**: None
**Estimated Effort**: S

---

### health-dashboard (New Component)
**Responsibility**: Aggregate and display component health

**Acceptance Criteria**:
- [ ] Poll all component health endpoints
- [ ] Display status dashboard
- [ ] Alert on component failures
- [ ] Log health history

**Dependencies**: All components (health endpoints)
**Estimated Effort**: M

**Implementation Notes**:
- FastAPI service
- Poll components every 30s
- Store health history in Redis
- Emit alerts to Bloodbank events

---

## Integration Requirements
- [ ] All components respond to health checks within 1 second
- [ ] Dashboard aggregates status correctly
- [ ] Alerts triggered within 1 minute of failure
- [ ] Health data retained for 30 days

## Deployment Strategy
1. **Phase 1**: Add health endpoints to all components (parallel)
2. **Phase 2**: Deploy health-dashboard
3. **Phase 3**: Configure alerting

**Rollout Duration**: M effort

## Rollback Plan
1. Health endpoints are read-only, safe to deploy
2. Dashboard is new service, can be removed without impact
3. Components continue operating without health checks
```

---

## Story Patterns

### Pattern 1: Schema Evolution

**Applies when**: Changing event schemas, API contracts, or data models

**Template additions**:
```markdown
## Breaking Changes
- [ ] Migration guide created
- [ ] Backward compatibility strategy defined
- [ ] Deprecation timeline established

## Migration Strategy
1. Add new fields as optional (Phase 1)
2. Update consumers to handle new fields (Phase 2)
3. Make fields required (Phase 3, after grace period)
```

---

### Pattern 2: New Infrastructure Component

**Applies when**: Adding a new service to the platform

**Template additions**:
```markdown
## Infrastructure Requirements
- [ ] Docker container defined
- [ ] Deployment configuration created
- [ ] Networking and service discovery configured
- [ ] Monitoring and logging set up

## Component Dependencies
- [ ] Document what existing components depend on new service
- [ ] Define graceful degradation if service unavailable
```

---

### Pattern 3: Performance Optimization

**Applies when**: Optimizing across multiple components

**Template additions**:
```markdown
## Performance Baselines
- Current latency: {measurement}
- Target latency: {goal}

## Component Optimizations
### {Component 1}
- Optimization: {description}
- Expected improvement: {percentage or ms}

## Integration Impact
- [ ] End-to-end latency measured
- [ ] No performance regressions in other areas
```

---

## Anti-Patterns to Avoid

### ❌ Overly Broad Scope

**Bad**:
```markdown
Story: Improve system performance
Components: All
```

**Why bad**: Unclear deliverables, no specific acceptance criteria

**Better**:
```markdown
Story: Reduce event processing latency by 50%
Components: bloodbank (event routing), flume (task execution)
Target: Median latency from 200ms → 100ms
```

---

### ❌ Hidden Dependencies

**Bad**:
```markdown
### Component A
Dependencies: None
```

**Actually depends on**: Component B API change, Component C schema

**Why bad**: Causes integration failures, delays

**Better**:
```markdown
### Component A
Dependencies:
- Component B: Requires new /v2/endpoint API
- Component C: Requires trace_id in event schema
Blocked until: B and C complete their changes
```

---

### ❌ Missing Integration Tests

**Bad**:
```markdown
## Acceptance Criteria
- [ ] Component A complete
- [ ] Component B complete
```

**Why bad**: No verification that components work together

**Better**:
```markdown
## Acceptance Criteria
- [ ] Component A complete
- [ ] Component B complete
- [ ] Integration test: A → B data flow verified
- [ ] Integration test: B → A response validated
- [ ] End-to-end scenario tested
```

---

### ❌ No Rollback Strategy

**Bad**:
```markdown
## Deployment
1. Deploy all components
2. Hope for the best
```

**Why bad**: No plan if integration fails in production

**Better**:
```markdown
## Deployment Strategy
1. Deploy Component A (backward compatible)
2. Deploy Component B (consumes A's new features)
3. Verify integration in staging
4. Progressive rollout: 10% → 50% → 100%

## Rollback Plan
1. Feature flags allow disabling new behavior
2. Component B gracefully degrades if A unavailable
3. Can revert to previous versions independently
```

---

## Review Checklist

Before finalizing a cross-component story:

- [ ] **Clear scope**: All involved components listed
- [ ] **User value**: Story explains who benefits and why
- [ ] **Component tasks**: Each component has specific acceptance criteria
- [ ] **Dependencies**: All cross-component dependencies documented
- [ ] **Integration tests**: End-to-end verification defined
- [ ] **Deployment strategy**: Rollout sequence planned
- [ ] **Rollback plan**: Failure recovery documented
- [ ] **Effort estimates**: Realistic effort sizing per component
- [ ] **Breaking changes**: Migration strategy if applicable
- [ ] **Performance impact**: Baseline and targets if relevant

---

## Delegation Workflow

Once story is complete:

1. **Meta-orchestrator**: Review and approve story
2. **Delegation**: Use `delegate-story.sh` to distribute to components
3. **Component work**: Each component creates implementation stories
4. **Integration**: Meta-orchestrator verifies end-to-end
5. **Documentation**: Update platform status and integration map

See [delegation-patterns.md](delegation-patterns.md) for detailed delegation workflow.
