# Coding Workflow

Use this when writing or modifying code in 33GOD.

## Routing

1. Choose implementation strategy first (complexity, parallelism, risk).
2. Use specialist reference based on task type:
   - service implementation → `service-development.md`
   - event/command contract lifecycle → `event-command-lifecycle.md`
   - full workflow generation → `workflow-generation.md`
   - cross-component changes → `platform-lifecycle.md`

## Coding checklist

- [ ] Contract/schema impact identified first
- [ ] Event naming/routing conventions preserved
- [ ] Tests updated/added
- [ ] Docs/GOD drift resolved
- [ ] Delivery evidence attached

## Commit format (minimum)

```text
<type>(<scope>): <summary>

Task-Source: <ticket-id | event-id | directive>
Notes: <short rationale>
```
