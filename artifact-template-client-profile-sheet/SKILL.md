---
name: artifact-template-client-profile-sheet
description: Create a document using the Client Profile Sheet template and its retained reference file. Use when the user selects this template, names Client Profile Sheet, or explicitly invokes $artifact-template-client-profile-sheet. Create an evidence-first prospect or client profile with qualification, source confidence, systems, stakeholders, opportunity boundaries, risks, next actions, and engagement history.
pipeline-status: new
---

# Client Profile Sheet

Create a new document from this template. Keep the reference file unchanged.

## Workflow

1. Read `artifact-template.json` and resolve its paths relative to this skill directory.
2. Load [@documents](plugin://documents@openai-primary-runtime) and invoke its reference/template workflow with the retained file.
3. Treat the user's prompt and available sources as the content input. Do not invent facts merely to fill a template slot.
4. Clone or import the reference instead of replacing its visual system with generic defaults.
5. Render and verify the finished document, then return the final artifact.

## Fidelity

Preserve page setup, sections, styles, lists, tables, headers, footers, and recurring page elements.

User instructions control requested content and explicit deviations. The retained reference controls layout and formatting where the user has not requested a change.
