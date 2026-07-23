# Sources

Use this reference to select public evidence and record citations without
credential material.

## Reading order

Choose the path that matches the source task you need to perform.

| Task | Read |
|---|---|
| Add a topic | This file → `journalist-lifecycle.md` |
| Investigate one run | This file → `investigator-workflow.md` |
| Resolve weak evidence | This file → `safety-gotchas.md` |

## Source policy

Prefer the strongest available evidence in the following order.

Prefer evidence in this order:

1. Primary official sources: release notes, repositories, regulator filings, first-party announcements, datasets.
2. Direct reporting with named authors, publication times, and linked evidence.
3. Specialist analysis that separates observation from inference.
4. Discovery-only aggregators and social posts; confirm their claims elsewhere.

Store public URLs in `topics[].sources`. Store secret references only as environment-variable names in `topics[].secret_env`; never store tokens, cookies, authorization headers, or signed URLs.

## Evidence requirements

Record enough metadata to audit every externally verifiable claim.

- Record canonical URL, title, publisher, publication time when available, retrieval time, and supported claim.
- Deduplicate canonical URLs and substantively identical syndications.
- Require two independent sources for high-impact claims unless a definitive primary source exists.
- Label unpublished, anonymous, inaccessible, or paywalled evidence and lower confidence.
- Separate “no update found” from “source unavailable.”

Before adding a topic, confirm each URL uses `https`, contains no credentials, and is relevant to the prompt.
