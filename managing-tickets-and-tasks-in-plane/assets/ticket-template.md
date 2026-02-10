# [{{TICKET_ID}}] {{TITLE}}

**Priority:** {{PRIORITY}}
**Story Points:** {{POINTS}}
**Sprint:** Sprint {{SPRINT_NUMBER}}
**Epic:** {{EPIC_NAME}}
**Labels:** {{LABELS}}

---

## User Story

As a {{USER_TYPE}}
I want {{CAPABILITY}}
So that {{BENEFIT}}

---

## Acceptance Criteria

{{#ACCEPTANCE_CRITERIA}}
- [ ] {{CRITERION}}
{{/ACCEPTANCE_CRITERIA}}

---

## Technical Notes

{{TECHNICAL_NOTES}}

**Implementation Approach:**
{{IMPLEMENTATION_APPROACH}}

**Files to Modify:**
{{#FILES}}
- {{FILE_PATH}}
{{/FILES}}

**Dependencies:**
{{#DEPENDENCIES}}
- Depends on: [{{DEP_TICKET_ID}}] {{DEP_TICKET_TITLE}}
{{/DEPENDENCIES}}

**Risks:**
{{#RISKS}}
- {{RISK_DESCRIPTION}}
{{/RISKS}}

---

## Development Log

{{#DEV_LOG}}
### Session {{SESSION_DATE}} {{SESSION_TIME}}
**Developer:** {{DEVELOPER_NAME}}
**Duration:** {{DURATION}}
**Branch:** {{GIT_BRANCH}}

**Changes:**
- Files changed: {{FILES_CHANGED}}
- Lines added: {{LINES_ADDED}}
- Lines removed: {{LINES_REMOVED}}

**Commits:**
{{#COMMITS}}
- {{COMMIT_MESSAGE}}
{{/COMMITS}}

**Progress:**
{{#AC_PROGRESS}}
- [{{STATUS}}] {{CRITERION}}
{{/AC_PROGRESS}}

**Developer Notes:**
{{DEVELOPER_NOTES}}

---
{{/DEV_LOG}}

## Links

- **Story Document:** {{STORY_DOC_PATH}}
- **Sprint Plan:** {{SPRINT_PLAN_PATH}}
- **Related Tickets:** {{#RELATED}}[{{TICKET_ID}}]{{/RELATED}}
- **Pull Request:** {{PR_URL}}

---

**Created:** {{CREATED_TIMESTAMP}}
**Created By:** {{CREATED_BY}}
**Last Updated:** {{UPDATED_TIMESTAMP}}
**Status:** {{STATUS}}
