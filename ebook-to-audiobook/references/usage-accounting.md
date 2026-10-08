# Token and cost accounting (optional)

Skip this unless the user wants to know what a build used or cost. It is a separate sub-workflow because the
pilot proved how easily the numbers get mixed up.

## Four different ledgers

| Ledger | Unit | Source | Pilot chapter 1 |
| --- | --- | --- | --- |
| Local TTS | VoxCPM2 text tokens, wall seconds, audio seconds | `requests.jsonl` -> `metrics.json` | 9,906 tokens, 1,460.8 s, 3,043.8 s audio, 307 calls |
| Local ASR | wall seconds, WER | `qa-*.json` | 24 samples, 109 s CPU |
| LLM orchestration | provider tokens (input, cache read/write, output, reasoning) | agent session store | 202 assistant messages, 13.55M uncached input + 3.53M cache read + 0.19M output = 17.28M |
| Infrastructure | kWh, search API calls | assumptions, receipts | GPU 0.9-2.1 cents (assumed); search unknown |

Never add TTS tokens to LLM tokens: different tokenizers, different bills. The 17.3M LLM tokens were research,
engineering and orchestration (mostly repeated context), not the chapter; the chapter itself is ~7.7k words.

## Capture LLM usage (OpenCode)

```bash
python3 -B $S/usage.py capture <main-session-id> --children --out $B/usage/build.json
```

- Discovers **delegated child sessions** (`session.parent_id`, transitive) in OpenCode's sqlite store, read-only. The
  pilot had 9 children; subagents carried most of the tokens. Find sessions with
  `sqlite3 -readonly ~/.local/share/opencode/opencode.db "select id,title from session where directory like '%<book>%'"`.
- Counts **completed assistant messages** only (`time.completed`), reports the excluded in-flight one, and flags
  messages lacking usage/total/cost instead of estimating. OpenCode v2 has no `export` subcommand; the DB route works
  even when the TUI is hung (a pty-wrapped `opencode export` is the fallback for older versions).
- **Freeze a snapshot at the moment the build completes** and say so. `--children` is cumulative: a later capture
  also includes report writing, skill authoring, and unrelated follow-up work. The pilot's frozen snapshot stayed at
  202 messages while the live session had grown to 300+.
- Cache reads recur on every request; `reported_total_tokens` already includes them. Do not add reasoning or cache again.
- `opencode_reported_cost_usd` was `0.0` on a subscription route. That means "not metered here", not "free".

Feed it to the renderer's metrics: `render_chapter.py report --llm-usage-snapshot $B/usage/build.json`
(unknown fields stay `null`). Record in the book: `usage.py record --book $B --chapter 1 --label build --snapshot ... [--pricing ...]`.

## Cost assumptions (always labeled)

```bash
python3 -B $S/usage.py cost --snapshot $B/usage/build.json --pricing $B/usage/pricing.json
python3 -B $S/usage.py energy --seconds 1460.767 --low-watts 150 --high-watts 350 --usd-per-kwh 0.15
```

- `pricing.json` is the user's cited assumptions (see `pricing.example.json`, which holds the pilot's numbers: model
  `gpt-6.1-sol` at $2.00 uncached input, $0.10 cache read, $2.50 cache write, $10.00 output per million tokens, up to
  272k input per request). Pilot result: **$29.40 API-equivalent, not an actual charge** (route is subscription-billed).
  Verify rates and long-context multipliers against the provider's current page before reusing them. An aggregate
  snapshot cannot detect requests that crossed a long-context threshold; the output notes that caveat.
- Resolve what a friendly model alias really is before pricing it: `sol-6.1` in OpenCode -> gateway route
  `automaticai/personal/sol-6.1` -> OpenAI native `gpt-6.1-sol`, account `openai-personal`, subscription (see the
  automaticai-provider-gateway skill; routes live in the gateway's `ops/routes.json`). Settled gateway rows for sampled
  requests were `$0`.
- Electricity is a scenario from assumed watts (`measured: false`). Search API spend (Brave/Tavily) is `null` without receipts.
- `observed_paid_provider_charge_usd: 0` for TTS holds only because the engine check forbids fallback.

## CandyStore reconciliation (only if a ledger report is requested)

CandyStore (`http://127.0.0.1:8683`, `candystore context latest` for hand-offs) is the durable event ledger for agent
and gateway events. What the pilot learned when reconciling it with the local receipts:

- `GET /events` pages by **offset with a capped total** (no cursor, no `has_more`); keep reading until a page comes back
  short, and record that the total was capped. `GET /events/{id}/raw` returns the raw payload.
- `candystore` must run from a registered project or be given `--project`; a bare `candystore context latest` in an
  unregistered directory errors out.
- Agent events carry session ids (`session_id`, `parent_session_id`); **gateway settled-usage events do not**. They have
  provider, model, account and billing, but no session or project link. Do not attribute them to the build by timestamp
  alone; count them only with an independent correlation (request id, session id), and list the rest as unmatched.
- Gateway settlement lags the request by ~10 minutes; widen the window accordingly.
- Keep local TTS/ASR receipts as their own ledger; they are not CandyStore events and should not be presented as such.
- Group rows by phase (research, source preparation, pipeline engineering, voice design, narration, QA, reporting) and
  keep report-generation overhead out of the frozen experiment totals.
- Redact: ids and numbers only; drop anything matching key/token/secret patterns.
