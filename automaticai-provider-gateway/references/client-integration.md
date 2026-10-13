# Integrate a real consumer

Start with the deployment's current `ops/examples/` files. They are tested
examples, not instructions to replace an entire user configuration. Mint a
named consumer token, use its returned `op://` reference, and merge the relevant
provider settings while preserving sibling settings.

## OpenAI-compatible clients

Provide these settings through the owning configuration/launcher:

```text
OPENAI_BASE_URL=https://api.automaticai.io/v1
OPENAI_API_KEY=op://DeLoSecrets/AutomaticAI Gateway Tokens/<consumer-name>
```

The reference must be resolved by `op run` or the credential launcher; most SDKs
do not resolve `op://` themselves. A raw key must not be written into any file,
including ignored environment files. Explicit client construction takes
precedence over a library's environment conventions:

```python
from openai import OpenAI

client = OpenAI(base_url="https://api.automaticai.io/v1")
reply = client.chat.completions.create(
    model="automaticai/personal/kimi-k3",
    reasoning_effort="high",
    messages=[{"role": "user", "content": "Say hello."}],
)
result = client.responses.create(
    model="automaticai/personal/kimi-k3",
    reasoning={"effort": "high"},
    input="Say hello.",
)
```

Run with the consumer key supplied in process environment. Send `stream=True`
when streaming. Preserve the complete assistant/tool history, including all
call IDs and outputs. For converted Responses routes, do not rely on remote
`previous_response_id` storage: resend the complete relevant history. Multiple
tool calls and their reasoning history must remain in the same turn.
Tool outputs may be strings or protocol-shaped block arrays. Resumed clients
can insert developer instructions and assistant progress between parallel
results, and often end the input at the final tool result without a new user
turn. Preserve that actual shape in regression fixtures; a synthetic final user
prompt can hide Claude's assistant-prefill failure. The gateway converter owns
nested block translation and native tool-batch adjacency, not each client.

These API styles support normal stateless function-tool round trips. They do
not imply support for every vendor hosted tool, image/audio endpoint or
WebSocket feature. Inspect discovery capabilities and probe the consumer's real
feature set before migrating it.

## Native Claude Code

Use `ops/examples/claude-code.env.op` and
`ops/examples/claude-code.settings.json`. Configure:

- `ANTHROPIC_AUTH_TOKEN`: the consumer's resolved gateway token.
- `ANTHROPIC_BASE_URL`: `https://api.automaticai.io`, without `/v1`.
- Main model: `automaticai/personal/claude-opus-5.5` or
  `automaticai/intelliforia/claude-opus-5.5` as intended.
- `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL` and
  `ANTHROPIC_DEFAULT_HAIKU_MODEL`: that same account-specific route.
- `CLAUDE_CODE_EFFORT_LEVEL=xhigh` and the checked-in harness settings enabling
  `effortLevel`, `ultracode`, and its workflow keyword trigger.

Inspect inherited credentials and wrapper precedence by **variable name and
presence**, never value. Remove `CLAUDE_CODE_OAUTH_TOKEN` and other conflicting
direct-provider auth from this launch scope so the gateway token wins; do not
delete interactive account sessions globally. Confirm the installed Claude
version and schema before carrying these settings into a different release.
The verified baseline was Claude Code 2.1.285.

Launch the checked-in example with:

```sh
op run --env-file=ops/examples/claude-code.env.op -- \
  claude --settings ops/examples/claude-code.settings.json \
  --model automaticai/personal/claude-opus-5.5
```

Adapt the env example to the named token and clear any inherited credential
conflicts in the owning launcher. For the team plan, update the main model and
all three helper models together. Verify native Messages streaming with the
real CLI, rather than treating a Chat-only SDK probe as sufficient.

The gateway's Claude subscription adaptors prepend the required Claude Agent SDK
system preamble when absent, preserve caller system blocks/cache controls/tool
IDs, and merge required OAuth beta defaults with native client feature headers.
Leave this behavior in the adaptor. Do not make every client spoof headers or
rewrite its system instructions. Paid OpenRouter traffic keeps its own contract.

## Codex / Astra / Sol

The durable Codex owner is `~/.agents/providers/automaticai/`, including
`codex-provider.toml`, `consumer.env.op`, `codex-gateway.py`, focused tests and its
README. Use the source installer/launcher; do not overwrite global trust,
MCP configuration, foreign profiles or hooks with a copied TOML fragment.

```sh
python3 ~/.agents/providers/automaticai/codex-gateway.py plan
python3 ~/.agents/providers/automaticai/codex-gateway.py install
python3 ~/.agents/providers/automaticai/codex-gateway.py check
```

Codex 0.159.2 uses separate `<profile>.config.toml` files. This owner uses
command-backed `[model_providers.automaticai.auth]` with `op read` and a named
consumer reference. Secrets remain in memory; native OpenAI login does not own
this custom provider. Do not combine that auth mode with `env_key`, a static
bearer or `requires_openai_auth`. HTTP/SSE Responses is accepted independently
of WebSockets and hosted web search; unsupported capabilities stay disabled.

Map the current model exactly. `automaticai/personal/sol-6.1` is `gpt-6.1-sol`;
`automaticai/personal/sol` remains `gpt-6-sol`. Default effort is `xhigh`, no
ultra. Preserve a consumer's explicit normalized effort such as `max`.
`activate` requires an exact available personal OpenAI route and the correct
consumer token; only activate after a real installed-client receipt.

Refresh the generated model catalog through `codex-gateway.py install` after
adding routes to the consumer's scope, then use `check`. Discovery/scope changes
do not update a running Codex process's picker. Preserve global model, provider,
effort and sibling settings; a second install should be unchanged. A missing
catalog-metadata warning during an isolated probe is not itself inference failure.

Use [prompt and session proof](prompt-proof.md). A synthetic Kimi probe cannot
prove that the executing OpenAI parent migrated. Do not kill that parent;
verify a fresh ordinary launch after changing the durable next-launch default.
If a future account is disconnected, complete preparation and keep that
cutover pending without substituting another model, account or paid provider.

## Other frameworks, services and helpers

For Hermes, Flume workers, hooks, Hindsight inference, n8n jobs, SDK services or
other agent frameworks, inspect the active owner's schema and launcher. Configure
its custom OpenAI-compatible provider with the gateway base URL, a catalog model,
appropriate wire API and the consumer token. Do not assume one framework's
configuration keys work in another.

Trace every separate model selector: primary, fast/helper, planner, critic,
summarizer, background memory, retry/fallback and spawned-worker defaults. A
primary model migrated while its helper or fallback still calls a vendor is
incomplete. Preserve account intent on each role, and accept each distinct path.

Gateway upstream egress, provider OAuth exchange/refresh and credential control
planes still contact their owners directly. Embeddings/reranking and unsupported
features require their own verified gateway capability before a valid migration;
do not point them at Chat merely to make the hostname match.

## Hermes fleet agents

Hermes uses a YAML config (`~/.hermes/config.yaml`) with a named provider block.
The fleet base config defines the `automaticai` provider; profiles inherit it
and override only `secrets.onepassword.env.AUTOMATICAI_GATEWAY_KEY` in their
`config.delta.yaml` for per-member token tracking.

Key Hermes-specific behaviors:

- `hermes config set` is the only safe way to modify config — direct file edits
  are refused by the tool. Lists are replaced wholesale, not appended.
- `providers.<name>.models` controls which routes appear in `/model` completion
  and what delegation can resolve. Auto routes must be listed here.
- `model.aliases` adds shortcut names (`auto`, `auto-orch`, `auto-sub`,
  `auto-fast`) that resolve via `/model <alias>`.
- `delegation.model` sets the default for spawned workers. Set it to
  `automaticai/auto/subagent` for adaptive worker routing.
- `providers.<name>.extra_body.reasoning_effort` is merged into every request
  because `delegation.reasoning_effort` never reaches a named provider (only
  `custom` providers receive it).

Auto router wiring procedure:

1. Mint token: `python3 ops/gateway-tokens.py mint hermes --auto` (from
   `~/code/client-portal/gateway`).
2. Add routes: `hermes config set providers.automaticai.models '["...","automaticai/auto","automaticai/auto/orchestrator","automaticai/auto/subagent","automaticai/auto/fast"]'`
3. Add aliases: `hermes config set model.aliases.auto 'automaticai/auto'` etc.
4. Point key: `hermes config set secrets.onepassword.env.AUTOMATICAI_GATEWAY_KEY 'op://.../hermes'`
5. Set delegation: `hermes config set delegation.model 'automaticai/auto/subagent'`
6. Verify: curl `/v1/models` and `/v1/chat/completions` with auto model names.
