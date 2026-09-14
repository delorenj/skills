---
name: web-source-ingestion
description: "Fetch and normalize web articles or docs for downstream note/wiki ingestion, especially when the primary source blocks direct extraction or uses anti-bot protection."
pipeline-status:
  - new
---

# Web Source Ingestion

Use when a user asks to add a web article, blog post, documentation page, or research note into a wiki, knowledge base, notes system, or raw-source archive and the fetch path is unreliable.

## Triggers

- "add this article to the wiki"
- "save this blog post"
- "ingest this page/source/doc"
- direct fetch returns empty content, bot checks, paywall chrome, or an interstitial instead of the article body
- Medium or similar publishing platforms that often block generic fetchers

## Goal

Preserve the original source identity while still getting a usable text snapshot for downstream synthesis.

## Retrieval order

1. Try the canonical source URL directly.
2. If extraction fails or returns anti-bot/interstitial content, try an accessible text mirror or proxy.
3. Keep the original article URL as the canonical source in the saved raw note even when the body was obtained through a mirror.
4. Record the collected date and published date separately.
5. Only ask the user to paste content after mirror/proxy paths fail.

## Medium-specific workaround

For Medium articles, try a text proxy form such as:

- `https://r.jina.ai/http://medium.com/@author/...`
- equivalent canonical Medium URL variants that point to the same article

Important:
- Prefer the canonical `medium.com/...` article URL in the saved metadata.
- Treat the proxy only as the retrieval path.
- If one hostname variant returns a bot-check page, try the canonical Medium URL variant before giving up.
- Strip proxy wrapper lines such as `Title:`, `URL Source:`, `Published Time:`, and `Markdown Content:` before saving the article body.

## Normalization rules

- Remove fetch-wrapper boilerplate and navigation chrome.
- Preserve the article text faithfully; do not rewrite the source in the raw note.
- Keep useful structural headings, quotes, and reference lists.
- It is acceptable to retain inline image links when they are part of the fetched markdown.
- If the source body came from a proxy, avoid falsely claiming the original site was directly fetched.

## Output contract for downstream wiki work

When handing off to a wiki/raw ingestion workflow, provide:

- canonical source URL
- collected date
- published date
- cleaned body text
- any caveat that a proxy/mirror was used for retrieval

## Pitfalls

- Do not replace the original source URL with the mirror URL in the archived raw note.
- Do not save anti-bot challenge text as if it were the article.
- Do not stop after a single failed extractor if a proxy or alternate canonical URL is obvious.
- Do not summarize too early; preserve a raw source artifact first when the workflow expects one.

## See Also

- karpathy-llm-wiki
- llm-wiki
