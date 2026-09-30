# Route, identity and effort contract

The live source of truth is `~/docker/stacks/ai/newapi/ops/routes.json`, not this
table. Extend that catalog and its acceptance checks when adding another model.
The initial list describes the user's use cases; it is not the complete fleet.

## Initial catalog

| Canonical request model | Account | Native model | Context | Billing |
| --- | --- | --- | --- | --- |
| `automaticai/personal/claude-opus-5.5` | `claude-personal` | `claude-opus-5-5` | Not established by discovery | Subscription |
| `automaticai/intelliforia/claude-opus-5.5` | `claude-intelliforia` | `claude-opus-5-5` | Not established by discovery | Subscription |
| `automaticai/openrouter/claude-opus-5.5` | `openrouter-personal` | `anthropic/claude-opus-5.5` | 1,000,000 | Metered |
| `automaticai/personal/kimi-k3` | `kimi-personal` | `k3` | 1,048,576 | Subscription |
| `automaticai/personal/kimi-k3s` | `kimi-personal` | `k3-256k` | 262,144 | Subscription |
| `automaticai/personal/kimi-2.8` | `kimi-personal` | `kimi-for-coding` | 1,048,576 | Subscription |
| `automaticai/personal/astra` | `openai-personal` | `gpt-6-astra` | Not established by discovery | Subscription |
| `automaticai/personal/sol` | `openai-personal` | `gpt-6-sol` | Not established by discovery | Subscription |
| `automaticai/personal/sol-6.1` | `openai-personal` | `gpt-6.1-sol` | Not published in route metadata | Subscription |

Replacing only `automaticai/` with `aai/` selects exactly the same route and
token scope. Persist canonical spelling in maintained configuration where
possible. Do not invent aliases such as `aai-auto`, native provider prefixes or
unverified Gemini/Copilot equivalents.

Kimi's `kimi-2.8` is a user-facing alias to the Coding plan's `kimi-for-coding`.
The alias alone cannot prove which underlying release the provider currently
serves. Inspect the authenticated native catalog before asserting a version.
Unknown context windows remain unknown; do not infer them from the route name.

## Account identities and credential boundaries

- Personal Claude: `jaradd@gmail.com`, dedicated personal subscription grant;
  verified organization `f25c449f-64ab-4bb8-812d-328e2f77f29e` in the 2026-09-30
  acceptance record.
- Intelliforia Claude: the same email with the tri-devs / TriumphABA team plan;
  required organization `28b201ed-bc28-4793-973f-c7ed110bb3b7`.
- Kimi: `jaradd@gmail.com`'s Kimi Coding plan key, not a metered Moonshot key.
- Astra/Sol: `jaradd@gmail.com`'s dedicated personal OpenAI subscription grant,
  not a platform API key and not another account's interactive CLI session.
- OpenRouter: a separately chosen personal inference key. A management key
  administers keys and must not be used as a relay credential.

Upstream references are in `ops/routes.json`. Dedicated sessions are stored in:

```text
op://DeLoSecrets/AutomaticAI OAuth - Claude Personal/session
op://DeLoSecrets/AutomaticAI OAuth - Claude Intelliforia/session
op://DeLoSecrets/AutomaticAI OAuth - OpenAI Personal/session
```

These are gateway control-plane inputs. Agent consumers receive only their own
AutomaticAI gateway token, never the upstream access or refresh credential.
The example/default consumer token reference is
`op://DeLoSecrets/yeurk5dpqkaarspvsn3cjtmkki/default`; mint a named consumer token
for maintained integrations instead of multiplying use of this shared example.

## Availability and routing

`GET /v1/models` returns only connected, enabled models permitted by the calling
token. Metadata includes account, native model, context when established, effort
and endpoint capabilities. Never equate absence with an unrecognized name until
checking current catalog membership and token permissions.

- Unknown explicit route or invalid effort: 400.
- Invalid/expired token or denied scope: authentication/authorization failure.
- Known but unconnected route: 503; no replacement account is selected.
- Provider authentication or rate limit failure: retain the chosen account and
  return its failure; never select the paid route implicitly.

Managed channel identity requires both its `AutomaticAI / <account>` name and
`automaticai-managed:v1:<account>` marker, plus the correct alias-to-native
mapping. Filtering covers cached candidates, pinned channels, affinity and
retries. A renamed channel or an admin-pinned token is not a substitute for this
ownership proof. The verified configuration used retry count zero.

The relay principal is enabled role-1 `delo-relay` in `aai-personal`. Its token
scope can permit models from several explicit accounts, but a request still
selects exactly one. Do not use an administrator token to prove normal routing.

## Effort and harness settings

Accepted request forms:

```json
{"reasoning_effort": "xhigh"}
```

```json
{"reasoning": {"effort": "xhigh"}}
```

Chat convention is `reasoning_effort`; Responses convention is `reasoning.effort`.
The gateway also accepts top-level `effort`. It normalizes case and rejects
conflicting explicit values with 400. Preserve a caller's explicit effort.

| Family | Default | Effective upstream effort |
| --- | --- | --- |
| Claude subscription / OpenRouter Claude | `xhigh` | Preserve `medium`, `high`, `xhigh`, `max` |
| Astra / Sol / Sol 6.1 | `xhigh` | Preserve `medium`, `high`, `xhigh`, `max`; verified on both APIs |
| K3 / K3s | `high` | `medium` and `high` become `high`; `xhigh` and `max` become `max` |
| Kimi 2.8 alias | `max` | Same Kimi mapping |

`ultracode` belongs to Claude Code's harness. The checked-in settings enable
`effortLevel: xhigh`, `ultracode: true`, and `workflowKeywordTriggerEnabled: true`.
Generic gateway requests containing `ultracode` are rejected; do not pretend
that every OpenAI-compatible client has this harness feature. Astra/Sol use
`xhigh` with no ultra setting.

## Billing

Subscription aliases have model ratio zero and ledger quota zero. The paid
OpenRouter route uses its selected upstream rates and group multiplier 1.
The 2026-09-30 rc.40 verification recorded model/completion ratios 2/5 and cache
read/write ratios 0.05/1.25, with one-hour write ratio 2. Re-read current rates
when reconciling; this is a dated rate snapshot, not a permanent price promise.

`groupRatio` is a price multiplier, not a discount label. NewAPI quota is
500,000 units per USD. Rate-based ledger settlement does not separately reconcile
provider-specific discounts in OpenRouter `usage.cost`. Account, native model,
requested/effective effort and actual charge must be read back after a probe.

## Dated acceptance baseline

On 2026-09-30, six initial routes passed live acceptance: both Claude accounts,
OpenRouter Claude and all three Kimi aliases. Astra and Sol were unconnected
because OpenAI Advanced Account Security required user passkey verification.
The OAuth oneshot synchronized both Claude accounts but failed overall while
OpenAI was missing. Read `ops/ACCEPTANCE-unified-provider.md` and current account
status before claiming that this snapshot still holds.

The personal OpenAI device sign-in was completed later on 2026-09-30 and its
identity verified. The subscription model catalog confirmed gpt-6.1-sol with max;
an exact sol-6.1 route was added while preserving sol. Current native Codex and
receipt acceptance is in `ops/SESSION-ROUTING-PROOF.md`; the earlier disconnected
snapshot above must not be used as current account status.

The later three-route API/stream/parallel-tool suite passed 24/24 checks after
renewal/recreation. Another 24 requests verified all four efforts through both
APIs with zero subscription charge. Bare native Codex and its session hook
verified the exact Sol 6.1 account/model/effort. The all-account OAuth oneshot
now succeeds. A current consumer-specific receipt remains required; these dated
results do not prove an arbitrary agent's own traffic.
