---
name: subagent-driven-development
description: Run an explicitly requested implementation-and-review team for independent tasks. Availability in a PM profile does not mandate delegation or multiple reviews for routine work.
---
# Requested implementation team

Use this workflow when delegation is requested or otherwise explicitly authorized
and independently useful tasks exist. Keep ordinary bounded work with the current
agent. Repository and user delivery instructions govern branches and publication.

Assign each worker a concrete outcome, file ownership, acceptance checks, and
side-effect boundary. Tell workers they share the codebase, must preserve others'
changes, and must adapt to concurrent work. Supply the context needed for the task.

Choose review depth from the changed behavior. Use a separate reviewer when the
risk or verification gap warrants it; do not require two reviewers per task or a
final review by default. Reproduce findings and rerun only invalidated checks.
A failed subtask can be repaired directly; preserving context is not a reason to
spawn another worker. Respect available agent limits and user-selected models.

## While the worker runs

The orchestrator owns the environment the worker depends on — spend the wait
maintaining it instead of polling the worker's transcript:

- **Prove gates from artifacts, not notifications.** A gate wrapped as
  `cmd > log 2>&1; printf '%s\n' "$?" > log.exit` always completes with wrapper
  exit 0; the proof is the `.exit` file's content plus the pass/fail counts in
  the log tail. Never call a gate green off a completion notification.
- **Attribute failures before reacting.** `node --test` output with
  `# fail 0 # cancelled N` is not a pass — find the file owning the cancelled
  tests and run it standalone. Cancellations that persist under
  `--test-concurrency=1` are cross-test interference, not parallel scheduling;
  document the attribution instead of re-running the whole gate.
- **Keep shared state alive.** Renew lease/driver-lock heartbeats before TTL
  expiry mid-run, and probe device rigs (emulator, adb server) for liveness —
  they die silently and the worker only finds out at its device step.
- **Steer, never respawn.** Push verified facts to the running worker (fresh
  gate exits, rig endpoints and env, remaining critical path) so it never
  duplicates green gates or infrastructure setup.

When quoting logs upward, strip credential-bearing lines first — Android build
logs embed the keystore password inside the apksigner command.

Integrate completed work promptly using `merge-forward` or the repository's own
workflow. Report implemented behavior, verification, and any remaining blocker.
There is no required dependency on the Superpowers skill family.

## Fallback when delegation is unavailable

Delegation is a convenience, not a dependency. Failure shapes that send you back
to implementing directly (or to fixing the rail first):

- **Billing or credit exhaustion on the provider**: the child fails instantly
  with a `429` / limit-exhausted error and zero tokens produced. The provider
  account behind the subagent model is out of quota for the window, not the task.
  Retry once if the model is configurable; otherwise implement in-session.
- **Hard route rejection (`400` model-not-supported and the like) on EVERY
  spawn, seconds after dispatch**: the configured delegation model route itself
  is broken, not the task. Do NOT keep re-dispatching with different prompts —
  two identical instant deaths means the rail is down. Diagnose the route
  (probe the model directly with a clean consumer token), fix it at its layer
  (for the AutomaticAI auto router that means the gateway tier chain — its
  skill's dead-route hygiene section; a temporary model pin is only a bridge
  until the chain is fixed), then re-dispatch and confirm the child survives
  past the first minute before trusting the rail again.
- **Identical-arguments retry loop**: if a retry with unchanged arguments fails
  identically (the runtime will warn you), do NOT send a third identical call.
  Change the model, the prompt, or the approach — never the same call again.

When you do fall back, keep the discipline the worker would have followed:
read the target files yourself first, make the smallest change that satisfies
the acceptance criteria, run the real tests/build against the live system the
task names, and commit with the repo's normal message shape. Falling back is
not a license to skip verification — it is the same work minus the hand-off.
