<!--
Momo review-report template. Copy to <ISSUE>.review.md and fill every <…>.
issue-autonomous-review.sh requires ALL of these "## " headings verbatim:
  Reviewer, Locked Intent Baseline, Drift Assessment, Adversarial Findings, Decision
and these field lines (first word parsed):
  "- Independent of implementer: yes"      (independence)
  "- Reviewer agent: <id>"                 (must differ from the evidence "- Worker:")
  "- Drift assessment: none|minor|significant"   (significant -> HOLD)
  "- Critical/high findings: none"         (any finding -> HOLD)
  "- Decision: accept|hold"                (accept clears it; legacy "close" tolerated)
The reviewer MUST be a different agent than the implementer named in the evidence file.
Delete this comment block before saving.
-->

# Autonomous Review Report: <ISSUE-KEY>

## Issue
- Ticket: <ISSUE-KEY>
- Review-lane reason: <why it entered review>

## Reviewer
- Reviewer agent: <independent reviewer agent id + model/provider>
- Independent of implementer: yes

## Locked Intent Baseline
- Acceptance criteria source: <ticket ACs / evidence file>
- Milestone / horizon: <active milestone / north star reference>

## Drift Assessment
- Drift assessment: none
- Notes: <what you checked the work against the locked intent for>

## Adversarial Findings
- Critical/high findings: none
- Attempts to break it: <inputs/paths you probed; regressions checked>

## Decision
- Decision: accept
- Rationale: <one line — why this clears, or why it is held>
