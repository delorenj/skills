# Prompt and native session receipt proof

The gateway operator owner is
`~/docker/stacks/ai/newapi/ops/gateway-proof.py`. Its complete workflow and
accepted identity contract are in `ops/SESSION-ROUTING-PROOF.md`.

```sh
python3 -B ~/docker/stacks/ai/newapi/ops/gateway-proof.py session
```

Inside Codex this checks the current native thread's latest hook challenge
against authenticated completed gateway consumption. For a different child,
use `--session-id <its actual thread.started UUID>`. Inherited parent markers
or environment labels cannot prove a child, and child receipts cannot prove
their parent. The gateway records native Codex session-id/thread-id headers.

For a chosen prompt, generate a marker with `gateway-proof.py marker`, include
it in the real prompt and use `check --marker ... --since ... --session-id ...`.
Optionally require the exact text fingerprint, route, account, full generated
token name or request ID. `hash` hashes exact UTF-8 stdin without printing it.
The receipt includes account, native model, effective effort and billing.

`verified` proves the matched completed request. `unverified` can mean no
request yet, a delayed log or missing evidence; absence alone is not bypass.
`unavailable` means the proof service could not be read. A configured/recorded
native provider outside AutomaticAI is separate evidence of a bypass.

The canonical hook hub challenges each startup/user prompt, then checks usage
after a tool request or asynchronously at Stop. It invokes the lazy-migration
skill for a real finding and requires the agent to fork/join a real worker.
The shell hook does not claim to have spawned an agent merely by returning
context. Proofs and migration requests are deduplicated and runtime-only.

`probe` deliberately labels separate test inference. Never use its receipt to
claim that the executing parent, historical prompts or every session request
used the gateway. Existing parent connections remain unchanged until relaunch.
