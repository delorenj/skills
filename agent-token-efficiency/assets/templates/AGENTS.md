---
pipeline-status: new
---
# Agent Token Efficiency Rules

Premium models make decisions. Cheap agents gather evidence.

Before reading many files, spawn or use a scout/explore worker. Before feeding logs to a premium model, summarize the first meaningful failure. Before researching library behavior, prefer Context7 or official docs.

## Token discipline

- Do not paste entire files unless necessary.
- Prefer `rg`, `git grep`, `fd`, and targeted reads before broad file reads.
- Use cheap scouts for file discovery, symbol maps, call sites, and config searches.
- Use docs researchers for current API/library facts.
- Use log summarizers for build/test/runtime failures.
- Compact or clear context when switching unrelated tasks.
- Keep MCP servers minimal; default to Context7 plus one code-search MCP only.

## Model discipline

Use premium/high-thinking modes for architecture, ambiguous bugs, multi-file tradeoffs, security-sensitive changes, and final review.

Use cheap/minimal-thinking modes for repo exploration, docs lookup, log summarization, test command discovery, dependency/config inspection, and rote edits with explicit instructions.

## Safety

- No global YOLO/AFK/auto-approval.
- No production secrets in prompts, logs, or reports.
- No global dependency upgrades unless explicitly requested.
- No broad refactors disguised as bug fixes.
