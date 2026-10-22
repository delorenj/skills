---
name: typesafe-ai
description: Use TypeSafe Jev for typed AI judgments via System One API.
---

# typesafe-ai

Jev returns typed answers (a choice, a score, or a yes/no probability) instead of prose. Use it for decision points in pipelines — routing, gating, attention triage — where a fast structured verdict beats generated text. Also use when migrating a Jev caller off the OpenRouter proxy or debugging a systemone request.

## Calling the API

```python
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <key>
{"model": "jev-latest",
 "state": "<the text being judged>",
 "questions": {"q": {"type": "noul",
                    "instructions": "<what to judge>",
                    "criteria": {"true": "<when true>", "false": "<when false>"}}}}
```

Response carries `answers.<q>.noul` (probability of the true criterion), `choice` + `probabilities`, or `score`, plus `usage: {input_tokens, output_tokens}`.

## Rules

- **Model names differ by front door.** Direct TypeSafe accepts `jev-latest` / `jev-preview` (resolves to `jev-1.13.0`). The `typesafe/jev-1.13` spelling is OpenRouter's proxy name — it 400s on the direct API. OpenRouter's `/api/alpha/decisions` and TypeSafe's `/v1/systemone` share the exact request/response wire shape, so migrating a caller is a base-URL + model-name swap only.
- **There is no chat endpoint.** `/v1/chat/completions` on api.typesafe.ai 404s. Jev is decisions-only; pick a normal LLM for prose.
- **State and questions are both billed input.** Keep state to the decision-relevant window, one question per state, and dedupe on (state_hash, question) — every byte re-bills at full rate (no prompt caching).
- **Fleet wiring — everything goes through the ingress.** The operator's rule is that no Jev caller bypasses a gateway: the default `JEV_URL` for fleet tools (`~/.local/bin/zcrank-gate`, `jev-*`) and containers is the jev-litellm proxy, and `~/.config/jev-clairic/typesafe.key` holds the *ingress* key (the raw provider key is backed up beside it as `typesafe.key.direct.bak`). Callers honor `JEV_URL` / `JEV_MODEL` env overrides. When adding a new Jev caller, point it at the ingress URL + that key file — never mint parallel keys and never hand out the raw provider key.
- **Never leave a caller on the OpenRouter proxy while a direct key exists** — a dead OpenRouter balance takes down every proxied Jev call even though the direct API is fine.

## Fronting with LiteLLM

LiteLLM ships a TypeSafe pass-through (`/typesafe/v1/systemone` plus unified `/v1/systemone`) with virtual keys, cost tracking, and fallbacks. The fleet runs this as the `jev-litellm` stack behind Traefik at `https://jev.delo.sh/typesafe/*` — the single front door for every Jev caller (operator rule: nothing bypasses a gateway; the aai gateway's own auto-router classifier routes through it too). The proxy injects the real TypeSafe credential server-side from `op://DeLoSecrets/Jev/credential`; callers only ever hold the ingress key. Template: `~/docker/stacks/ai/jev-litellm/compose.yml` (shared external `proxy` network, wildcard `*.delo.sh` DNS resolves automatically).

- **Version gate:** the `/typesafe` pass-through does not exist in LiteLLM 1.94.0 (the digest the hindsight router pins) — every path under `/typesafe/` returns a bare 404. Run `main-stable` or newer, and pin a digest only after the route answers a live probe.

## Verify

Minimal probe through the ingress (the path every caller actually uses) — expect 200 with `noul` present:
```bash
/usr/bin/python3 -c "import json,urllib.request; k=open('/home/delorenj/.config/jev-clairic/typesafe.key').read().strip(); b=json.dumps({'model':'jev-latest','state':'connectivity check','questions':{'ok':{'type':'noul','instructions':'Is this a connectivity check?','criteria':{'true':'it says so','false':'otherwise'}}}}).encode(); r=urllib.request.Request('https://jev.delo.sh/typesafe/v1/systemone',data=b,headers={'Authorization':'Bearer '+k,'Content-Type':'application/json'}); print(json.load(urllib.request.urlopen(r,timeout=20))['answers'])"
```
Break-glass direct probe: swap the URL for `https://api.typesafe.ai/v1/systemone` and the key for `typesafe.key.direct.bak` (or `op://DeLoSecrets/Jev/credential`). The ingress key 401s against the direct API — they are different credentials.
