---
name: free-provider-scout
description: "Runbook for the unattended daily free-provider scout (gateway/ops/free-scout.py): research free LLM API providers, sign up in the operator's browser, confirm the account, mint an API key into 1Password, and add the provider's free models to the automaticai/free router as a new pool. Use only when free-scout.py invokes a stage (`research`, `signup`, `confirm`, `apikey`, `integrate`) or when an operator reruns one by hand. Skip for editing existing free pools, gateway deploys (the runner owns them), or general web research."
---

# Free-provider scout

The runner `gateway/ops/free-scout.py` owns the run: it picks the provider, schedules the
confirmation checks, commits, builds, deploys, rolls back and emits Bloodbank events. You do one
stage and write one result file. The run record (`run.json`, path in your prompt) holds the
provider and everything earlier stages learned; read it first. Write the result JSON to the path
in your prompt, even when you fail. A missing result file reads as a crashed stage.

Contract and router design: `gateway/ops/FREE-ROUTER.md`. Provider list: `gateway/ops/free-scout/providers.json`.

## Rules for every stage

- **Free only.** Never buy credits, start a paid plan, upgrade a tier, top up, or turn on
  auto-recharge. If the provider has no free API access (a free tier, recurring free credits,
  or permanently free models), the provider is `not_viable`.
- **Card.** Enter the card only when a free tier cannot start without card verification. Then set
  every spend limit, budget, or overage cap to $0 or the minimum, turn auto-recharge off, and
  report `card_added: true`. If the card would be charged right away, stop: `not_viable`.
- **Terms.** Accept terms of service and data-use terms on the operator's behalf. Record in notes
  whether the provider trains on prompts or logs them; the integrate stage maps that to `data_policy`.
- **Challenges.** Clicking a single "I'm not a robot" checkbox is fine. Do not attempt image,
  puzzle, or audio challenges, and do not try to get around bot detection. Report `needs_human` and stop.
- **Phone.** Use only the number your prompt names (the Telnyx number, whose texts reach the
  runner). Never give the personal cell: its texts cannot be read yet. If SMS is unavailable or
  the provider refuses the number (some refuse VoIP numbers), report `needs_phone`.
- **One account per provider.** If an account already exists for the operator, sign in to it.
  Do not create a second account.
- **Secrets.** Read identity and card values with `op read` / `op item get --reveal` when you
  type them. Never put a secret, card number, or API key in a file, a result, a commit, or your
  final message. The result holds `op://` references only.
- **Browsers.** Close every tab you open. Leave the operator's own tabs alone.

## Identity (1Password, vault DeLoSecrets)

| What | Where |
| --- | --- |
| Email for email sign-ups | `op://DeLoSecrets/Jarad/Email/main` |
| Phone | the reference in your prompt (default the Telnyx number, `op://DeLoSecrets/2zlolrgqalvybke5l6pxaeqnpe/sms number`). The personal cell `op://DeLoSecrets/Jarad/Address/cell` is not readable until it forwards or ports to Telnyx |
| Name, address, company and other profile fields | identity item `c4cqd2brp7c6bb2c3lvy3wtbui` (`op item get c4cqd2brp7c6bb2c3lvy3wtbui --vault DeLoSecrets --reveal --format json`) |
| Card, only under the card rule above | item `wtsd2u4uqdvae6pqu3rkigz2ge` |
| Company | AutomaticAI (automaticai.io). Use case: "internal developer tooling and memory summarization". |

Sign-up preference: **Google** (`jaradd@gmail.com`), then **GitHub** (`delorenj`), then email.
The operator's Chrome is signed in to Google and GitHub.

## Browsers

1. **Kapture** (load the `kapture` skill): the operator's live Chrome on this host, already signed
   in to Google and GitHub. Use it first. Open your own tab and drive it through the HTTP API on
   `127.0.0.1:61822`.
2. **computer-use** (load the `computer-use` skill; run `orca-ide`, never bare `orca`): use it for
   anything kapture cannot reach. That covers OAuth account choosers and consent windows
   (`chrome-extension://` pages and popups), browser chrome, native dialogs, and stubborn flows.
   Google's account chooser has failed under kapture clicks before, so go straight to
   computer-use there.
3. **ego-browser** (the operator's Mac profile): only if kapture and computer-use both fail and
   `ego-browser` reports the Mac bridge is up.

To read public docs without a browser, run `web-search fetch <url>` (the `web-search` skill).
The built-in WebSearch and WebFetch tools may fail on this host.

## Stage `research`

The run record names `results` (Tavily search results) and `known` (every provider already on
the list, with status and domains).

1. Read both. From the results, and from pages you fetch to check them, list every provider that
   gives free API access to LLM chat models. That means a free tier, recurring free credits,
   permanently free models, or a large one-off trial (say it is finite).
2. Skip any provider already in `known`, matched by id or by a shared domain, whatever its status.
3. Judge viability. A server-side API key is required, not a browser-only playground. An
   OpenAI-compatible chat completions endpoint is strongly preferred. The terms must allow use
   from a personal or small-business backend.
4. Result:

```json
{"status": "ok",
 "candidates": [{"id": "sambanova", "name": "SambaNova Cloud", "url": "https://cloud.sambanova.ai",
   "domains": ["sambanova.ai"], "free_offer": "free tier, 20 RPM on Llama 4 Maverick",
   "priority": 10, "notes": "OpenAI-compatible; no card"}],
 "not_viable": [{"id": "x", "name": "X", "url": "https://x.ai", "reason": "credits only for paying users"}],
 "notes": "..."}
```

Priority: 10 means recurring free usage that is OpenAI-compatible and generous. 30 means
recurring but small, or not OpenAI-compatible. 50 means one-off trial credits. 80 means tiny.
Lower priorities are tried first.

## Stage `signup`

1. Find the provider's sign-up or console URL and its free-tier terms. If there is no free API
   access, report `not_viable` with the reason and stop.
2. Sign up, or sign in if an account exists, following the sign-up preference. Fill profile
   forms from the identity item. Accept the terms.
3. If the provider sends a confirmation email or SMS, finish everything else you can, then
   report `needs_confirmation`. Give the channel, the sender domains the message will come from,
   any subject words you saw, and the UTC time the message was triggered. The runner checks
   Gmail, or the Telnyx SMS inbox, 2, 4, 6 and 8 minutes later.
4. If you reached a working console, report `signed_up`. Record the console and API-key page
   URLs for the next stages.

```json
{"status": "signed_up | needs_confirmation | not_viable | needs_phone | needs_human | failed",
 "started_at": "2026-10-09T08:41:00Z",
 "account": {"method": "google | github | email", "login_email": "jaradd@gmail.com",
   "console_url": "https://...", "keys_url": "https://..."},
 "confirmation": {"channel": "email | sms", "from_domains": ["sambanova.ai"],
   "subject_hint": "Verify your email", "sms_words": ["SambaNova", "code"]},
 "card_added": false,
 "notes": "free tier terms, training/logging policy, anything odd"}
```

## Stage `confirm`

Your prompt carries the candidate messages the runner found.

- **Email.** Messages are Gmail threads. Read them with
  `gog -a jaradd@gmail.com -j gmail thread get <threadId>`. Open the verification link in
  kapture, or enter the code in the provider's page. Ignore look-alike senders and anything that
  asks for a password.
- **SMS.** Every text the Telnyx number received around the sign-up is in the prompt, with its
  sender and time. Pick the provider's code (verification texts rarely name the provider, so go
  by the time and the wording) and enter it in the provider's page.

Then confirm that the console works.

```json
{"status": "confirmed | failed", "notes": "..."}
```

## Stage `apikey`

1. Sign in (the account details are in the run record) and create an API key. Name it
   **AutomaticAI**. Choose **never** for expiry, or the longest the provider allows. Give it the
   narrowest scope that still allows inference.
2. Store it in 1Password, vault **DeLoSecrets**, field **AutomaticAI API Key** (concealed):
   - If an item titled with the provider's name already exists, add or replace that field:
     `op item edit <item-id> --vault DeLoSecrets 'AutomaticAI API Key[password]=<key>'`.
   - Otherwise create it:
     `op item create --vault DeLoSecrets --category "API Credential" --title "<Provider name>" 'AutomaticAI API Key[password]=<key>'`.
   - Pass the key straight from the page into that one command. Never echo it or write it to a file.
3. Verify: `op read "op://DeLoSecrets/<item-id>/AutomaticAI API Key"` returns it, and the
   provider's models endpoint answers 200 with it.
4. Reference the item **by ID**, never by title, because the vault has duplicate titles.

```json
{"status": "ok | failed",
 "credential_ref": "op://DeLoSecrets/<item-id>/AutomaticAI API Key",
 "base_url": "https://api.provider.com", "chat_path": "/v1/chat/completions",
 "free_limits": "what the docs and headers say: rpm/rpd/tpm/tpd per model or per account, reset time",
 "notes": "..."}
```

## Stage `integrate`

Add the provider as one free pool. Do not commit, build, deploy or touch other pools. The runner
does all of that after you, and rolls everything back if the gateway refuses it.

1. **Free models.** List models from the API and the docs. Keep chat models that are free under
   this account, have at least 32,768 context, and allow at least 8,192 output tokens. Prefer
   strong general models with 131,072+ context.
2. **Probe** with the stored key, using small `curl`/python calls. Record the rate-limit headers.
   Find the switch that turns thinking off, if the model thinks. Try each of these in turn:
   `{"chat_template_kwargs": {"enable_thinking": false}}`, `{"thinking": {"type": "disabled"}}`,
   `{"reasoning_effort": "none"}`, `{"reasoning": {"enabled": false}}`. Keep the first one that
   removes reasoning tokens. Find the real output cap: a 400 naming a max_tokens limit gives it.
3. **Spec.** Write it to `spec.json`, at the path in your prompt:

```json
{"account": "sambanova-free",
 "base_url": "https://api.sambanova.ai", "chat_path": "/v1/chat/completions",
 "credential": "op://DeLoSecrets/<item-id>/AutomaticAI API Key",
 "pool": {"reset": "UTC", "rpm": 20, "rpd": 1000, "data_policy": "logs"},
 "routes": [{"name": "llama-4-maverick", "upstream": "Llama-4-Maverick-17B-128E-Instruct",
   "context_window": 131072, "max_output_tokens": 16384}],
 "members": [{"name": "llama-4-maverick", "tier": 2, "json_mode": true, "tools": true,
   "tool_choice_required": true, "limits": {"rpm": 20},
   "overrides": {"chat_template_kwargs": {"enable_thinking": false}}}]}
```

   - `account` is `<provider id>-free`. Route names are lowercase model slugs.
   - Pool limits are the documented free limits. Use the account-wide limits on the pool and
     per-model limits on members. Never pad them: the router keeps its own 10% headroom.
   - `reset` is `UTC` for a daily window that resets at 00:00 UTC, an IANA zone if the provider
     resets at another midnight, or `rolling` when there is no daily window. `rpd`, `tpd` and
     `neurons_per_day` need a daily window.
   - `data_policy`: use `trains` if prompts may train models, `logs` if they are kept, `no-train`
     if neither is stated beyond operations, and `zdr` for zero retention. If unsure, use the
     stricter-sounding one (`trains`).
   - A provider whose free usage is a money allowance can be paced like
     `mistral-allowance` (FREE-ROUTER.md): `neurons_per_day` in micro-dollars, with
     member `neurons_per_mtok` at list price.
4. **Apply:** run the `catalog-apply` command from your prompt. Add `--replace` on later applies.
5. **Accept:**
   `python3 -B gateway/ops/free-acceptance.py --direct --pool <account> --checks plain,json,tools,required,continuation --jobs 3 --retries 1 --format table`.
   - Drop members that fail `plain`.
   - Set `json_mode`, `tools` and `tool_choice_required` to exactly what passed.
   - Tiers:
     - 1: a strong general model, 131,072+ context, passes every check, p50 under 10 s.
     - 2: passes plain and json.
     - 3: slow (p50 over 20 s), small, or tools-only.
   - For a tier-1 candidate, also run `--checks long --long` (about 100k input tokens).
   - Re-apply with `--replace` until the spec matches the evidence. A failure from upstream
     overload (429, 503, "overloaded") is not a verdict; retry it once.
6. If no member passes, report `not_viable`. The runner restores routes.json.

```json
{"status": "ok | not_viable | failed", "pool": "sambanova-free", "members": 3,
 "notes": "which models, tiers, limits and why"}
```
