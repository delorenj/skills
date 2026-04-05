---
pipeline-status:
  - new
---
# Vector Update Policy

Use stable, interpretable weights so humans can reason about model behavior.

## Recommended defaults

- `more`: +1.3
- `less`: -1.0
- `avoid`: -2.2
- `replace old`: -1.2
- `replace new`: +1.2
- verdict `up` token boost: +0.2
- verdict `down` token penalty: -0.25

## Why this works

- Keeps directional intent dominant (`more/less/avoid`)
- Uses verdict as secondary local correction
- Preserves human readability (no black-box gradient updates)

## Tuning strategy

1. Start with defaults.
2. Measure drift and output quality over 20-50 feedback rows.
3. Tune one coefficient at a time.
4. Keep changelog for coefficient versions.
