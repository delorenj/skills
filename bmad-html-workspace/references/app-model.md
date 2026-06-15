# App Model (v0)

Use this model to normalize repo data into the HTML workspace.

```json
{
  "project": {
    "name": "skillex",
    "phase": "Discovery",
    "health": "green"
  },
  "summary": {
    "northStar": "Single-pane planning + execution visibility",
    "lastUpdated": "2026-05-09"
  },
  "timeline": [
    {"label": "Ideation", "status": "done"},
    {"label": "Scaffold", "status": "active"},
    {"label": "Automation", "status": "todo"}
  ],
  "todos": [
    {
      "title": "Wire BMAD docs into state",
      "owner": "agent",
      "priority": "high",
      "status": "in_progress"
    }
  ],
  "docs": [
    {"title": "MVP plan", "path": "docs/plan/skillex-mvp-plan.md", "type": "plan"}
  ],
  "decisions": [
    {
      "date": "2026-05-09",
      "title": "HTML-first cockpit",
      "rationale": "Improve update velocity and interactivity"
    }
  ],
  "risks": [
    {"title": "State drift", "mitigation": "Regenerate from source docs frequently"}
  ],
  "diffs": [
    {
      "title": "Recent code delta",
      "before": "old snippet",
      "after": "new snippet"
    }
  ],
  "feedback": {
    "prompt": "What should change next?",
    "fields": ["priority", "notes"]
  }
}
```
