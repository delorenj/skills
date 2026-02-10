# Workflow: Create Ticket from Story

Creates a Plane ticket from a BMAD story document or user requirements.

## Input

- Story file path (markdown)
- OR task description (text)
- Sprint number (optional)
- Priority (optional)

## Process

1. **Parse Story Document**
   - Extract title from heading
   - Parse user story (As a... I want... So that...)
   - Extract acceptance criteria (checklist items)
   - Extract story points (if present)
   - Extract technical notes
   - Extract dependencies

2. **Generate Ticket Metadata**
   - Title: `[TICKET-ID] {Story Title}`
   - Description: Full story content + acceptance criteria
   - Priority: Map from story priority or default to medium
   - Points: Extract from story or ask user
   - Labels: Auto-detect from story content
     - "security" if mentions auth, keys, credentials
     - "performance" if mentions optimization, speed, bundle
     - "frontend" if mentions UI, React, component
     - "backend" if mentions API, database, server
     - Sprint label: "sprint-{number}"

3. **Check for Duplicates**
   - Search existing tickets for similar titles
   - Compare descriptions using fuzzy matching
   - Warn if >80% similarity found
   - Ask user to confirm or update existing ticket

4. **Create Ticket**
   - POST to Plane REST API: `/api/v1/workspaces/{workspace}/projects/{project}/issues/`
   - Set state to "backlog" or current sprint state
   - Add labels via label IDs
   - Link to story file in description

5. **Link Related Tickets**
   - Parse "Dependencies:" section
   - Add dependency links in Plane
   - Update parent epic if specified

6. **Return Confirmation**
   - Ticket ID
   - Plane URL
   - Summary of what was created

## Output Format

```markdown
✓ Ticket Created: [CWS-015] Fix API authentication bug

**Details:**
- Priority: urgent
- Story Points: 3
- Sprint: Sprint 1
- Labels: security, backend, critical

**Plane URL:** https://plane.internal.intelliforia.com/intelliforia/projects/.../issues/CWS-015

**Acceptance Criteria:**
- [ ] Revoke exposed credentials
- [ ] Generate new API key
- [ ] Update environment variables
- [ ] Verify authentication flow

**Next Steps:**
Run `/dev-story CWS-015` to begin implementation.
```

## Error Handling

**Story file not found:**
- Search for similar file names
- Offer to create ticket from inline description

**Missing required fields:**
- Prompt user for missing info
- Use sensible defaults where possible
- Never fail silently

**API failure:**
- Retry with exponential backoff
- Save draft ticket locally
- Offer to retry later

## Integration

**BMAD `/create-story`:**
```bash
# After story document created
claude skill managing-tickets-and-tasks-in-plane:create-ticket-from-story \
  --story-file "$STORY_FILE" \
  --sprint "$CURRENT_SPRINT"
```

**Manual usage:**
```bash
# From story file
claude skill managing-tickets-and-tasks-in-plane:create-ticket-from-story \
  --story-file "docs/stories/user-authentication.md"

# From inline description
claude skill managing-tickets-and-tasks-in-plane:create-ticket-from-story \
  --description "Fix the login page styling bug" \
  --priority "high" \
  --points 2
```
