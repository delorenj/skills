# Workflow: Select Next Logical Ticket

Recommends the next optimal ticket to work on based on priority scoring algorithm.

## Selection Algorithm

### Phase 1: Filter Candidates

**Criteria:**
- Sprint: Current sprint only (or specified sprint)
- Status: `todo` or `backlog` (not `in-progress`, not `done`)
- Blockers: All dependencies complete
- Assignee: Assigned to me OR unassigned

**SQL-like query:**
```sql
SELECT * FROM tickets
WHERE sprint = current_sprint
  AND status IN ('todo', 'backlog')
  AND NOT EXISTS (
    SELECT 1 FROM dependencies d
    WHERE d.blocks = ticket.id
    AND d.status != 'done'
  )
  AND (assigned_to = current_user OR assigned_to IS NULL)
```

### Phase 2: Score Candidates

**Scoring Formula:**
```python
score = (
    priority_score
    + effort_score
    + age_score
    + dependency_bonus
    + critical_path_bonus
    - blocker_penalty
)
```

**Priority Scoring:**
```python
priority_weights = {
    "urgent": 10,
    "high": 7,
    "medium": 3,
    "low": 0
}
```

**Effort Scoring** (favor quick wins):
```python
effort_weights = {
    1: 5,   # 1 point: quick win
    2: 5,   # 2 points: quick win
    3: 3,   # 3 points: medium
    5: 3,   # 5 points: medium
    8: -2,  # 8 points: large (penalized)
    13: -5  # 13 points: epic (heavily penalized)
}
```

**Age Scoring** (address stale tickets):
```python
def age_score(days_old):
    if days_old > 14:
        return 3  # Very stale
    elif days_old > 7:
        return 2  # Stale
    else:
        return 0  # Fresh
```

**Dependency Bonus:**
```python
# If ticket unblocks other tickets
unblocks_count = count_tickets_blocked_by(ticket)
dependency_bonus = min(unblocks_count * 2, 10)  # Cap at 10
```

**Critical Path Bonus:**
```python
# If ticket is on critical path for sprint completion
if is_critical_path(ticket):
    critical_path_bonus = 8
else:
    critical_path_bonus = 0
```

**Blocker Penalty:**
```python
# Even if all dependencies complete, penalize if risky
if has_external_dependency(ticket):
    blocker_penalty = 3
else:
    blocker_penalty = 0
```

### Phase 3: Rank and Recommend

**Ranking:**
1. Sort by score descending
2. Break ties by priority, then by effort (smaller first)
3. Select top 3 candidates

**Output:**
- Primary recommendation (highest score)
- Alternative 1 (second highest)
- Alternative 2 (quick win with highest score)

### Phase 4: Update Status

**Actions:**
- Mark selected ticket `in-progress`
- Assign to current user if unassigned
- Log start time in ticket description
- Create git branch with ticket ID (optional)

## Example Execution

### Input State

**Candidate Tickets:**
```
[CWS-001] Revoke exposed GEMINI API key
  Priority: urgent | Points: 3 | Age: 1 day | Unblocks: 0

[CWS-002] Remove dev host permissions
  Priority: urgent | Points: 3 | Age: 1 day | Depends on: CWS-004

[CWS-004] Fix production build
  Priority: urgent | Points: 3 | Age: 1 day | Unblocks: 2 (CWS-002, CWS-014)

[CWS-012] Add explicit CSP
  Priority: medium | Points: 1 | Age: 1 day | Unblocks: 0

[CWS-009] Fix lint errors
  Priority: high | Points: 5 | Age: 1 day | Unblocks: 0
```

### Scoring

```
[CWS-001] Score: 18
  Priority: 10 (urgent)
  Effort: 3 (3pts)
  Age: 0 (1 day)
  Dependency: 0
  Critical: 5 (security blocker)
  Total: 18

[CWS-002] Score: FILTERED (blocked by CWS-004)

[CWS-004] Score: 21
  Priority: 10 (urgent)
  Effort: 3 (3pts)
  Age: 0
  Dependency: 4 (unblocks 2 tickets)
  Critical: 4 (blocks others)
  Total: 21

[CWS-012] Score: 8
  Priority: 3 (medium)
  Effort: 5 (1pt quick win)
  Age: 0
  Dependency: 0
  Critical: 0
  Total: 8

[CWS-009] Score: 10
  Priority: 7 (high)
  Effort: 3 (5pts)
  Age: 0
  Dependency: 0
  Critical: 0
  Total: 10
```

### Recommendation

```
🎯 Recommended Next Ticket: [CWS-004] Fix production build manifest

**Why:**
- Score: 21 (highest)
- Priority: URGENT
- Effort: 3 points (manageable)
- Unblocks: 2 other tickets (CWS-002, CWS-014)
- On critical path for sprint completion

**Alternatives:**
1. [CWS-001] Revoke exposed GEMINI API key (18 pts, security critical)
2. [CWS-012] Add explicit CSP (8 pts, quick win - 1 point)

**Impact:**
Completing CWS-004 will unblock CWS-002 and CWS-014, enabling parallel work
on host permissions and build validation.

**Action:**
Marking [CWS-004] as "in-progress"...
✓ Status updated
✓ Assigned to: Jarad DeLorenzo
✓ Start time logged: 2026-01-15 10:30 AM

Creating git branch: feature/cws-004-production-build-fix
✓ Branch created and checked out

Ready to begin implementation.
```

## Override Options

### User Preference Override

**Scenario:** User wants to work on different ticket

```
User: "Actually, I want to work on CWS-001 first"

Response:
✓ Understood. Marking [CWS-001] as in-progress instead.

Note: This is lower priority (18 vs 21), but both are URGENT.
CWS-001 is valid choice (security blocker).

Starting [CWS-001] Revoke exposed GEMINI API key...
```

### Quick Win Mode

**Scenario:** User wants small task to fill time

```
User: "What's a quick win I can knock out?"

Response:
🚀 Quick Win Recommendation: [CWS-012] Add explicit CSP

**Why:**
- Only 1 story point (~1-2 hours)
- No dependencies
- High value (security hardening)

This is perfect for filling time between larger tasks.
```

### Critical Override

**Scenario:** More urgent ticket appears mid-session

```
Pre-prompt hook:
⚠️ CRITICAL ALERT: New urgent ticket detected

[CWS-099] Production outage - API authentication failing
Priority: URGENT | Effort: 5 | Age: 5 minutes

Recommendation: Pause current work ([CWS-004]) and address CWS-099 immediately.

This is a production incident requiring immediate attention.
```

## Integration

### BMAD `/dev-story`

```bash
# If user doesn't specify ticket
/dev-story

# Skill automatically selects optimal ticket
# → Runs select-next-ticket workflow
# → Marks ticket in-progress
# → Creates branch
# → Proceeds with implementation
```

### Pre-Prompt Hook

```bash
# Before every prompt
~/.claude/hooks/pre-prompt-plane.sh

# If no active ticket:
# → Suggests next ticket
# → User can accept or specify different ticket
```

### Manual Call

```bash
# Explicit request
claude skill managing-tickets-and-tasks-in-plane:select-next-ticket

# With filters
claude skill managing-tickets-and-tasks-in-plane:select-next-ticket \
  --sprint 2 \
  --quick-wins-only
```

## Output Format

```markdown
🎯 Recommended Next Ticket: [TICKET-ID] Title

**Why:**
- Score: {score} (highest in sprint)
- Priority: {priority}
- Effort: {points} points
- Unblocks: {count} other tickets
- {Additional context}

**Alternatives:**
1. [ALT-ID-1] Alternative title ({score} pts, {reason})
2. [ALT-ID-2] Alternative title ({score} pts, quick win)

**Impact:**
{What completing this ticket enables}

**Action:**
Marking [TICKET-ID] as "in-progress"...
✓ Status updated
✓ Assigned to: {user}
✓ Start time logged: {timestamp}

Creating git branch: feature/{ticket-id}-{slug}
✓ Branch created

Ready to begin implementation.
```

## Customization

### Adjust Scoring Weights

Edit algorithm in this file:

```python
# Favor quick wins more
effort_weights = {
    1: 10,   # Increased from 5
    2: 10,   # Increased from 5
    3: 5,    # Increased from 3
    5: 2,    # Decreased from 3
    8: -5,   # More penalty
    13: -10  # More penalty
}

# Favor newer tickets
def age_score(days_old):
    if days_old > 14:
        return 1  # Reduced from 3
    elif days_old > 7:
        return 0  # Reduced from 2
    else:
        return 0
```

### Add Custom Filters

```python
# Only frontend tickets
def filter_frontend_only(tickets):
    return [t for t in tickets if "frontend" in t.labels]

# Only security tickets
def filter_security_only(tickets):
    return [t for t in tickets if "security" in t.labels]
```

### Define Team Preferences

```python
# Team-specific scoring
team_preferences = {
    "frontend_team": {
        "labels_bonus": {"frontend": 5, "ui": 3},
        "labels_penalty": {"backend": -5}
    },
    "backend_team": {
        "labels_bonus": {"backend": 5, "api": 3},
        "labels_penalty": {"frontend": -5}
    }
}
```

## Error Handling

**No eligible tickets:**
```
No eligible tickets found in current sprint.

All tickets are either:
- Already in-progress
- Blocked by dependencies
- Assigned to others

Options:
1. Work on tickets from backlog
2. Help with in-progress tickets
3. Review and test completed work
```

**All candidates blocked:**
```
⚠️ All candidate tickets are blocked by dependencies.

Blockers:
- [CWS-002] depends on [CWS-004] (in-progress)
- [CWS-006] depends on [CWS-011] (not started)
- [CWS-014] depends on [CWS-004] (in-progress)

Recommendation:
Work on unblocking ticket: [CWS-004] Fix production build
This will unblock 2 other tickets.
```

**WIP limit exceeded:**
```
⚠️ WIP Limit Exceeded

Current in-progress: 6 tickets (limit: 5)

Recommendation: Complete existing work before starting new tasks.

In-progress tickets:
1. [CWS-001] Revoke API key (70% complete)
2. [CWS-004] Fix production build (30% complete)
...

Suggest focusing on CWS-001 (closest to completion).
```
