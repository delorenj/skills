# Story: {Feature Name}

## User Story

As a **{user type}** (e.g., developer, operator, end-user)
I want **{capability}**
So that **{benefit}**

## Scope

**Components involved**: {comma-separated list of components}
**Story type**: {Integration | Performance | Infrastructure | Security | Feature}
**Priority**: {Critical | High | Medium | Low}

## Platform-Level Acceptance Criteria

- [ ] {Criterion 1 - What does success look like at the platform level?}
- [ ] {Criterion 2 - What must be true for this story to be complete?}
- [ ] Integration verified end-to-end
- [ ] Documentation updated
- [ ] Monitoring/observability in place

## Component Breakdown

### {Component 1 Name}

**Responsibility**: {High-level description of what this component must deliver}

**Acceptance Criteria**:
- [ ] {Specific, testable criterion 1}
- [ ] {Specific, testable criterion 2}
- [ ] Tests added with >80% coverage
- [ ] API contract implemented and documented

**Dependencies**:
- {Other component name}: {What this component needs from the dependency}

**Estimated Effort**: {S/M/L/XL}

**Implementation Notes**:
{Any technical details, edge cases, or architectural considerations}

---

### {Component 2 Name}

**Responsibility**: {Description}

**Acceptance Criteria**:
- [ ] {Criterion 1}
- [ ] {Criterion 2}

**Dependencies**:
- {Dependency description}

**Estimated Effort**: {S/M/L/XL}

**Implementation Notes**:
{Notes}

---

{Repeat for each component}

---

## Integration Requirements

**Integration Points**:
- {Component A} → {Component B}: {Data flow or API call description}
- {Component B} → {Component C}: {Description}

**Integration Tests**:
- [ ] {End-to-end test scenario 1}
- [ ] {End-to-end test scenario 2}
- [ ] Performance test: {metric} < {threshold}
- [ ] Error handling: {scenario} gracefully handled

**Integration Validation**:
```bash
# Commands to verify integration
{example test command}
{example verification command}
```

## Technical Considerations

### Architecture Impact
{How does this change the system architecture?}

### Performance Impact
- **Baseline**: {Current performance metric}
- **Target**: {Expected performance after change}
- **Acceptable degradation**: {Threshold}

### Security Considerations
{Any security implications, auth changes, data exposure concerns}

### Breaking Changes
- [ ] {Breaking change 1}
- [ ] Migration guide created
- [ ] Backward compatibility strategy defined
- [ ] Deprecation timeline: {date or version}

## Deployment Strategy

**Rollout Sequence**:
1. **Phase 1**: {First component or set of components}
   - Why first: {Rationale}
   - Validation: {How to verify}

2. **Phase 2**: {Next component(s)}
   - Dependencies: {What must complete in Phase 1}
   - Validation: {How to verify}

3. **Phase 3**: {Final component(s)}
   - Integration verification: {End-to-end validation}

**Rollout Duration**: {Estimated effort: S/M/L/XL}

**Progressive Rollout** (if applicable):
- 10% traffic: {duration}
- 50% traffic: {duration}
- 100% traffic: {duration}

**Monitoring During Rollout**:
- [ ] {Metric 1} monitored
- [ ] {Metric 2} monitored
- [ ] Error rate < {threshold}
- [ ] Latency < {threshold}

## Rollback Plan

**Trigger Conditions**:
- {Condition 1 requiring rollback}
- {Condition 2 requiring rollback}

**Rollback Procedure**:
1. {Step 1}
2. {Step 2}
3. {Verification step}

**Rollback Impact**:
- Data loss: {Yes/No - details}
- User impact: {Description}
- Time to rollback: {Estimate}

**Feature Flags** (if applicable):
```yaml
feature_flags:
  {feature_name}: false  # Default off, can enable per environment
```

## Success Metrics

**Quantitative**:
- {Metric 1}: {Baseline} → {Target}
- {Metric 2}: {Baseline} → {Target}

**Qualitative**:
- {User feedback criterion}
- {Developer experience improvement}

## Documentation

**Required Documentation**:
- [ ] Architecture diagram updated
- [ ] API documentation updated
- [ ] Integration guide created
- [ ] Runbook for operations
- [ ] Migration guide (if breaking changes)

**Documentation Locations**:
- Architecture: `docs/system-architecture.md`
- Integration: `docs/integration-map.md`
- API docs: {component-specific locations}

## Timeline and Dependencies

**Dependency Graph**:
```
{Component A} ──┐
                ├─→ Integration Test ──→ Deployment
{Component B} ──┘
```

**Critical Path**:
1. {First blocker}
2. {Second blocker}
3. {Final gate}

**Estimated Completion**: {Effort across all components}

## Related Stories

- {Link to related platform story}
- {Link to prerequisite story}
- {Link to follow-up story}

## Open Questions

- [ ] {Question 1 that needs answering before implementation}
- [ ] {Question 2}

## Notes

{Any additional context, historical decisions, or future considerations}

---

**Created**: {YYYY-MM-DD}
**Last Updated**: {YYYY-MM-DD}
**Status**: {Draft | Approved | In Progress | Completed}
**Assigned to**: {Team or individual, if applicable}
