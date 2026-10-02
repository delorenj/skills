# Why WebSearch and WebFetch return HTTP 400 here, and the verified fix

Status on 2026-10-02: **diagnosed and fix verified, not applied.** The user chose to move to the `web-search` skill
instead. Everything below is specific to Claude Code 2.1.287 (the newest release that day, per `npm view`) and the
AutomaticAI gateway. Re-verify before relying on it after an upgrade.

## Symptom

Both built-in tools fail with:

```
API Error: 400 To turn thinking off on this model, send "thinking": {"type": "between_tools"} instead of
{"type": "disabled"}. The model does not think before responding. ...
```

## Root cause

Claude Code canonicalizes model ids by substring match. The gateway alias `automaticai/personal/claude-sonnet-5.5`
(dotted) contains `claude-sonnet-5` but not the dashed real id `claude-sonnet-5-5`, so the client treats it as the
older `claude-sonnet-5`, which its table says tolerates `thinking: {"type":"disabled"}`. Its small-model helper
(WebFetch's page summarizer, and WebSearch's side request) therefore sends `disabled`, and WebSearch also forces
`tool_choice` to the `web_search` tool. The real Sonnet 5.5 and Opus 5.5 reject both. The same reasoning covers
`claude-opus-5.5`.

The Haiku slot is not the fault. `ANTHROPIC_DEFAULT_HAIKU_MODEL` (set in
`~/.agents/providers/automaticai/claude-code.env.op:19` and loaded by the `claude()` wrapper in
`~/.config/zshyzsh/lastagent.zsh:55`, not in `~/.claude/settings.json`) happens to be `claude-sonnet-5.5`, but moving it
is neither needed nor sufficient: WebFetch always uses the small-fast slot, while WebSearch uses it only when the
server-side GrowthBook flag `tengu_plum_vx3` is on and otherwise uses the main-loop model.

Gateway facts (direct matrix, tiny `max_tokens` requests):

| model | thinking `disabled` | `between_tools` | omitted |
| --- | --- | --- | --- |
| claude-sonnet-5.5 | 400 | 400 unless `output_config.effort` is high or lower (the gateway injects xhigh) | 200 |
| claude-opus-5.5 | 400 | 400 | 200 |
| glm-5.3, glm-5.3-flash | 200 | 200 | 200 |

Both Claude 5.5 routes also reject a forced `tool_choice` (`type: "tool"`). The gateway does relay the server-side
`web_search_20250305` tool to the Claude backend (a request with `tool_choice: auto` returned real results), so
WebSearch works once the client request shape is right. There is no Haiku-class or Sonnet-4 route on the gateway, and no
newer Claude Code release or upstream issue covers the dotted-alias case.

## The verified fix (do not use `CLAUDE_CODE_DISABLE_THINKING=1`: it fixes WebFetch only)

Add a `modelOverrides` block to the **gateway-only** settings file that the `claude()` wrapper passes with
`--settings`, `~/.agents/providers/automaticai/claude-code.settings.json`:

```json
{
  "effortLevel": "max",
  "ultracode": true,
  "workflowKeywordTriggerEnabled": true,
  "modelOverrides": {
    "claude-sonnet-5-5": "automaticai/personal/claude-sonnet-5.5",
    "claude-opus-5-5": "automaticai/personal/claude-opus-5.5"
  }
}
```

Keep it out of the shared `~/.claude/settings.json`, which the `claude-direct` launcher also reads and would then send
gateway ids to the direct login. Mirror it in `~/docker/stacks/ai/newapi/ops/examples/claude-code.settings.json`
(the checked-in owner), refresh the stale text in `~/.agents/providers/automaticai/CLAUDE-CODE.md` and the
`automaticai-provider-gateway` skill's `client-integration.md`, and commit both repos. `~/.agents` already carried
uncommitted slot-migration edits when this was written.

Verified end to end with the real 2.1.287 binary behind a recording proxy, on a Sonnet and an Opus main model: WebFetch's
side request omits `thinking`, WebSearch omits `thinking` and sends `tool_choice: auto`, and both return real results.
The zshyzsh gateway tests (`mise run test:claude-gateway`) should still pass. Start a new `claude` launch to pick it up.

## Side effects to weigh before applying

- Claude Code then treats the aliases as the native 5.5 models, so **the main loop changes shape**: `max_tokens` 64000 to
  128000, a much shorter system prompt (Sonnet 27 KB to 5.9 KB), and two extra beta headers
  (`mid-conversation-tool-changes-2026-07-01`, `per-turn-control-2026-07-01`). Short multi-turn tool rounds worked; long
  sessions, auto-compaction and hooks were not exercised.
- Other small-model features on the same path are probably failing the same way today and would be fixed too (unverified):
  session titles, `/rename`, `/insights`, tool-use summaries, prompt and agent hooks without an explicit model, and the
  built-in claude-code-guide agent.
- The fix depends on the client's current canonicalizer and capability tables. A release that changes them may change
  behavior; Opus 5.5 still needs `thinking` omitted rather than `between_tools`, so keep the override.
- Built-in WebSearch then bills Claude subscription quota and returns Anthropic's backend results, which is one reason
  to keep this skill as an independent fallback.

## If it must be reported upstream

Version aliases spelled with a dot (`claude-sonnet-5.5`, common in gateways and LiteLLM) fall through the substring
checks to `claude-sonnet-5` and get `thinking: disabled` plus a forced `tool_choice`. Gateway-side alternatives are an
effort-aware shim (Sonnet: `disabled` to `between_tools` with effort at most high; Opus: drop `thinking`) or dashed
alias routes.
