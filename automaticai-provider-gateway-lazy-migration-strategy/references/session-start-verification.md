# Session-start migration and actual request proof

The installed Codex implementation is owned by Bloodbank's canonical
`services/hook-hub/automaticai.py` and `handlers.toml`. Existing trusted native
`bb-hook` bindings reach it; do not add another hook writer or hand-edit the
generated native hooks. Use `agent-config-fanout` for binding/dialect changes.

1. At SessionStart and each UserPromptSubmit, inspect actual native session
   evidence, the caller's profile/CLI overrides and their source owner. Inject
   a fresh non-secret proof marker. A hook runs before inference and cannot
   truthfully verify a future prompt yet.
2. On a bypass, return an explicit invocation of this skill and an immediate
   real remediation-worker instruction. The originating agent forks through its
   harness. Join an existing worker for the same owner; assign file ownership
   and preserve unrelated edits. Emitting context records a delegation request,
   not proof that an agent was spawned.
3. Complete the source fix in `~/.agents/providers/automaticai/` for Codex. Use
   gateway account/token operations for any missing prerequisite. Preserve the
   exact model and explicit effort. The old executing connection is not killed
   or retroactively relabeled.
4. After the actual first model request, PostToolUse or async Stop checks the
   marker plus native session identity in completed gateway usage. An inherited
   marker in a child cannot satisfy the parent's native session receipt.
5. Accept a fresh ordinary installed-client launch, its real stream/tool path,
   receipt/account/charge, and repeat install/check. Land all owning source and
   submodule changes. Missing OAuth/capability gates remain named blockers.

Check the current session deterministically with:

```sh
python3 -B ~/docker/stacks/ai/newapi/ops/gateway-proof.py session
```

Read the gateway's `ops/SESSION-ROUTING-PROOF.md` for explicit prompt checks,
receipt fields and limits. Native Codex 0.159.2 session-id/thread-id headers are
accepted; other clients need their own accepted session-identity contract.

Do not start migration solely because usage is missing, delayed or unreachable.
A separate successful probe does not verify the parent's traffic. An assigned
migration worker handles its inherited bootstrap inline and never recursively
forks itself. Separate scripted probes use `AUTOMATICAI_PROOF_PROBE=1`; an
explicit remediation launch may use `AUTOMATICAI_MIGRATION_WORKER=1`. The hook
client forwards only these named non-secret controls, not credential variables.
