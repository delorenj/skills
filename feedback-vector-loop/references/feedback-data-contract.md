---
pipeline-status:
  - new
---
# Feedback Data Contract

## Feedback row schema (JSONL)

```json
{
  "timestamp": "ISO-8601",
  "item_id": "string",
  "verdict": "up | revise | down",
  "candidate": {
    "title": "string",
    "slogan": "string",
    "rationale": "string"
  },
  "direction": {
    "more": ["token or phrase"],
    "less": ["token or phrase"],
    "avoid": ["token or phrase"],
    "replace": {
      "old": "new"
    }
  },
  "notes": "optional free text"
}
```

## Semantics

- `more`: explicit positive vector target
- `less`: mild negative direction
- `avoid`: strong negative direction
- `replace`: pairwise rewrite signal and score correction rule

## Validation checks

- Missing `verdict` → reject row
- Missing `direction` object → reject row
- Empty directional arrays + no replace map on `revise`/`down` → reject row
