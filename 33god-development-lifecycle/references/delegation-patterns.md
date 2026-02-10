# Delegation Patterns for Cross-Component Workflows

## Core Delegation Workflow

### Pattern: Hierarchical Command Delegation

**Principle**: Meta-orchestrator identifies cross-component work, breaks it into component-specific tasks, and delegates to component orchestrators via Zellij workspace management.

**Steps**:
1. **Identify**: Meta-orchestrator receives platform-level request
2. **Decompose**: Break into component-specific tasks
3. **Delegate**: Spawn component orchestrators in parallel
4. **Monitor**: Track completion via status aggregation
5. **Integrate**: Verify cross-component integration

## Zellij-Based Delegation

### Why Zellij?

- **Parallel Coordination**: Multiple component tabs running simultaneously
- **Context Preservation**: Each tab maintains component-specific context
- **Visual Monitoring**: Tab names show component status at a glance
- **Session Persistence**: Work survives terminal disconnects

### Setup Pattern

```bash
# Create or attach to platform session
zellij --session 33god-platform

# For each component needing coordination:
zellij action new-tab --name "component-name"
zellij action write-chars "cd /path/to/component"
zellij action write 13  # Enter
```

### Execution Pattern

```bash
# Delegate task to component
zellij action go-to-tab-name "bloodbank"
zellij action write-chars "cat docs/delegated-task.md"
zellij action write 13

# Prompt component orchestrator
zellij action write-chars "/workflow-status"
zellij action write 13
zellij action write-chars "/create-story 'Implement task X'"
zellij action write 13
```

### Monitoring Pattern

```bash
# Check component progress
for component in bloodbank flume imi; do
  zellij action go-to-tab-name "$component"
  zellij action write-chars "/workflow-status"
  zellij action write 13
  sleep 2
done
```

## File-Based Communication

### Task Delegation Files

**Location**: `{component}/docs/delegated-task-{timestamp}.md`

**Template**:
```markdown
# Delegated Task: {Story Name}
**Component**: {component-name}
**Delegated**: {timestamp}
**Source**: Platform-level orchestration

## Context
{Full platform story context}

## Component-Specific Task
{What this component needs to implement}

## Acceptance Criteria
- [ ] Implementation complete
- [ ] Tests added
- [ ] Documentation updated
- [ ] Integration verified

## Related Components
{List of other components involved}
```

**Purpose**:
- Provides full context for component team
- Serves as reference during implementation
- Documents delegation history
- Links related component work

### Status Aggregation Files

**Component Status**: `{component}/docs/bmm-workflow-status.yaml`

Each component maintains its own workflow status:
```yaml
workflows:
  product-brief: "optional"
  prd: "docs/prd-bloodbank-2026-01-09.md"
  tech-spec: "optional"
  architecture: "docs/architecture-bloodbank-2026-01-09.md"
  sprint-planning: "docs/sprint-plan-q1-2026.md"
```

**Platform Status**: `33GOD/docs/platform-status.md`

Meta-orchestrator generates aggregated view:
```markdown
# Platform Status

## Component Overview
- bloodbank: ✓ Planning, ✓ Architecture, → Implementation
- flume: ✓ Planning, ⚠ Architecture, - Implementation
- imi: ⚠ Planning, - Architecture, - Implementation

## Cross-Component Stories
- Distributed Tracing: 2/3 components complete
```

## Delegation Script Usage

### Basic Delegation

```bash
# Delegate to specific components
./scripts/delegate-story.sh \
  --story docs/stories/distributed-tracing.md \
  --components "bloodbank,flume,imi"
```

**What happens**:
1. Script reads platform story
2. Creates task file in each component's `docs/`
3. Opens/switches to component tabs in Zellij
4. Displays task context in each tab
5. Prompts next steps for component orchestrators

### Ad-Hoc Task Delegation

```bash
# Delegate task without formal story file
./scripts/delegate-story.sh \
  --task "Add health check endpoint" \
  --components "bloodbank,flume"
```

**Use case**: Quick coordination for small changes

### Tracking Delegations

Script maintains: `33GOD/docs/delegated-stories-tracking.md`

```markdown
## Delegation: 2026-01-09 14:30:00
**Story**: distributed-tracing
**Components**: bloodbank, flume, imi

### Task Files
- bloodbank: `bloodbank/docs/delegated-task-20260109-143000.md`
- flume: `flume/docs/delegated-task-20260109-143000.md`
- imi: `imi/docs/delegated-task-20260109-143000.md`

### Status
- [ ] All tasks created
- [ ] All orchestrators notified
- [x] Integration verified
```

## Communication Patterns

### Asynchronous Coordination

**Pattern**: File-based status checks

```bash
# Meta-orchestrator polls component status
while ! all_components_complete; do
  ./scripts/platform-status.sh
  sleep 300  # Check every 5 minutes
done
```

**Benefits**:
- Non-blocking for meta-orchestrator
- Components work at their own pace
- Clear audit trail

**Drawbacks**:
- Delayed feedback
- Manual integration verification

### Synchronous Coordination

**Pattern**: Zellij session with active monitoring

```bash
# Meta-orchestrator watches all component tabs
zellij attach 33god-platform
# Visually monitor progress in each tab
# Respond to blockers in real-time
```

**Benefits**:
- Immediate feedback
- Quick blocker resolution
- Real-time integration testing

**Drawbacks**:
- Requires active monitoring
- Blocks meta-orchestrator attention

### Hybrid Coordination

**Pattern**: Async delegation + sync milestones

```bash
# Day 1: Delegate asynchronously
./scripts/delegate-story.sh --story distributed-tracing.md

# Day 2: Sync checkpoint
zellij attach 33god-platform
# Check each component tab for progress
# Address blockers
# Verify partial integration

# Day 3: Check aggregated status
./scripts/platform-status.sh
```

**Recommended approach**: Balance autonomy with coordination

## Parallel vs Sequential Delegation

### Parallel Delegation

**When**: Tasks are independent

```bash
# All components can start simultaneously
./scripts/delegate-story.sh \
  --story add-logging.md \
  --components "bloodbank,flume,imi"
```

**Example**: Adding structured logging to all components

**Benefits**:
- Faster completion
- No blocking dependencies

### Sequential Delegation

**When**: Tasks have dependencies

```bash
# Step 1: Update event backbone
./scripts/delegate-story.sh \
  --story add-trace-context.md \
  --components "bloodbank"

# Wait for completion
while ! component_complete "bloodbank"; do sleep 60; done

# Step 2: Update consumers
./scripts/delegate-story.sh \
  --story consume-trace-context.md \
  --components "flume,imi"
```

**Example**: Schema changes (producer must finish before consumers)

**Benefits**:
- Prevents integration issues
- Clear dependency management

## Error Handling Patterns

### Component Blocker

**Scenario**: Component encounters issue during implementation

**Pattern**:
1. Component orchestrator updates status in `bmm-workflow-status.yaml`:
   ```yaml
   current-story: "blocked"
   blocker: "Requires Bloodbank schema update"
   ```
2. Meta-orchestrator detects blocker via `platform-status.sh`
3. Meta-orchestrator intervenes:
   - Adjusts delegation sequence
   - Provides additional context
   - Escalates if needed

### Integration Failure

**Scenario**: Components complete individually but integration fails

**Pattern**:
1. Meta-orchestrator runs integration tests:
   ```bash
   ./scripts/integration-test.sh --components "bloodbank,flume"
   ```
2. If failure detected:
   - Document failure in platform-status
   - Create integration-fix story
   - Delegate to both components
3. Verify fix with re-test

### Abandoned Task

**Scenario**: Component task remains incomplete

**Pattern**:
1. Meta-orchestrator detects stale task (no update in N days)
2. Check delegation tracking file for task age
3. Options:
   - Re-delegate with adjusted scope
   - Escalate to component owner
   - Adjust platform story to work around

## Best Practices

### Clear Task Boundaries

**Do**:
```markdown
## Component-Specific Task (Bloodbank)
Add `trace_id` field to all event payloads:
- Update EventBase schema with trace_id: str
- Modify event publisher to accept trace context
- Ensure backward compatibility for consumers
```

**Don't**:
```markdown
## Task
Add tracing support
```

### Provide Full Context

**Do**: Include platform story in delegation file
**Don't**: Assume component knows broader context

### Track Dependencies

**Do**: Explicitly list component dependencies in delegation
**Don't**: Leave components to discover dependencies

### Verify Integration

**Do**: Create integration test suite for cross-component stories
**Don't**: Assume components will integrate correctly

### Document Completion

**Do**: Update platform-status when all components complete
**Don't**: Leave delegations untracked

## Example: End-to-End Delegation

**Platform Story**: Add distributed tracing

**Step 1: Decompose**
```markdown
# Platform Story: Distributed Tracing

## Scope
Add trace context propagation across all 33GOD components

## Component Tasks
- Bloodbank: Add trace_id to event schema
- Flume: Propagate trace_id in task execution
- iMi: Log trace_id in CLI operations
```

**Step 2: Delegate**
```bash
./scripts/delegate-story.sh \
  --story docs/stories/distributed-tracing.md \
  --components "bloodbank,flume,imi"
```

**Step 3: Monitor**
```bash
# Check status daily
./scripts/platform-status.sh

# Or attach to session
zellij attach 33god-platform
```

**Step 4: Verify Integration**
```bash
# Once all components complete
./scripts/integration-test.sh --story distributed-tracing

# Update platform status
echo "✓ Distributed tracing: Complete" >> docs/platform-status.md
```

**Step 5: Document**
```markdown
# Platform Story: Distributed Tracing - COMPLETE

## Implementation
- Bloodbank: v2.1.0 (trace_id in events)
- Flume: v1.8.0 (trace propagation)
- iMi: v0.9.0 (trace logging)

## Integration Verified
- End-to-end trace flow working
- Observability dashboard showing traces
- All components backward compatible
```
