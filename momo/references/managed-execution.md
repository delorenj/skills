# Managed execution v2

For `.project.json.execution.mode=managed`, Krebs is the sole execution authority.
Momo's shared playbook applies to Hermes PMs, interactive Codex and interactive
Claude; each host selects its own enrolled actor with `PILOT_ACTOR_ID`. Never borrow
the PM or operator key. A missing native identity, board membership, exact state
map, runtime supervisor, skill pin or legacy-writer fence blocks activation.

1. Read `px task status --actor ACTOR --json`. Root PM delegates child work to the
   owning component PM; it never claims that board as itself.
2. Freeze ticket revision, acceptance profile and starting artifact in a JSON
   payload. Claim using a fresh run UUID and stable command/idempotency UUID,
   expected board revision, and `px task claim TICKET_UUID -f PAYLOAD --json`.
   Persist the payload/IDs outside source. Retry exactly the same command after
   timeouts; inspect status before choosing another command.
3. Dispatch through `px run start TICKET_UUID -f ARGV_PAYLOAD --json` with the
   returned generation/revision. Krebs creates the enrolled systemd unit with
   KillMode=control-group. Do not launch a managed worker directly. Heartbeat every
   60 seconds; a lost heartbeat revokes mutation authority at 300 seconds.
4. `px run finish` records outcome and the delivered artifact. Success is not Done.
   A changed artifact invalidates earlier spec/quality reviews. Independent
   reviewers submit `px task review` with distinct reviewer run IDs under the accountable parent actor and
   current artifact/acceptance receipts. Never report your own work as reviewed.
5. Handoff advances exactly In Progress -> E2E Testing & QA -> Ready for
   Documentation -> Done. Tests, docs, notebook, skill, main/push and applicable
   deployment receipts must be current; inapplicable gates need explicit reasons.
   Parent closeout includes child completion command receipts and its own
   integration evidence. Done requires provider readback and durable receipt.
6. For a question use `px task attention` with stable question_id, context and
   text. Present it only after the receipt confirms Needs Attention and runtime
   stop. Resume references that question_id/answer and freezes readiness again;
   a new capacity acquisition produces a new generation. Release, cancel and
   takeover also require verified termination. Old-generation callbacks are audit
   only. Never free capacity because a lease expired or a subprocess exited.
7. Managed CRUD uses `px task get|create|comment|update`; direct tp, API writes,
   label hooks and legacy dispatch are fenced. Controller unavailability stops
   managed work. Shadow mode is observation only. Other ticket providers retain
   their existing adapters.
8. Material Pilot friction uses attributed `px idea --ticket ... --command ...
   --workaround ... --desired ...`; queued feedback never blocks ticket completion.

Installed source proof: run `python3 scripts/verify-managed-skill.py PATH` against
an installed SKILL.md. The JSON receipt includes canonical and installed SHA256,
resolved source paths and execution contract version. The deployment must bind
`execution.skill_version` to the released source version and `execution.momo_bundle_sha256`
to the complete installed bundle hash.

## Command payloads

Use human ticket references such as `PJAN-129` or provider UUIDs. Set your enrolled
`PILOT_ACTOR_ID`; interactive Codex/Claude actors have separate native credentials.
Review workers use distinct run UUIDs under their accountable parent actor.
`px task status --json` supplies board `revision`, active `generation` and run ID;
`px task get PJAN-129 --json` supplies immutable `content_revision`. Every mutation
passes the latest `--revision`; active operations also pass `--generation` and
`--run-id`. A review uses its own fresh run ID with the target generation. Successful
receipts contain the next revision. Never predict a revision after a failed call.
Payload files belong in `$XDG_STATE_HOME/pilot` or another runtime directory.

```sh
px task claim PJAN-129 --run-id "$RUN" --revision "$REV" -f "$STATE/claim.json" --json
# claim.json:
# {"ticket_revision":"CONTENT_HASH","artifact":"SOURCE_REVISION","acceptance":{"profile":"code","children":[]}}
px run start PJAN-129 --run-id "$RUN" --generation "$GEN" --revision "$REV" -f "$STATE/start.json" --json
# start.json: {"argv":["codex","exec","Implement the claimed ticket using Momo's managed playbook."]}
# Equivalent host wrapper, also suitable for Claude:
px-supervised PJAN-129 --run-id "$RUN" --generation "$GEN" --revision "$REV" -- codex exec "Implement the claimed ticket"
px run finish PJAN-129 --run-id "$RUN" --generation "$GEN" --revision "$REV" -f "$STATE/finish.json" --json
# finish.json: {"outcome":"success","artifact":"DELIVERED_REVISION","receipt":"test-and-delivery-evidence-uri"}
px task review PJAN-129 --run-id "$REVIEW_RUN" --generation "$GEN" --revision "$REV" -f "$STATE/review.json" --json
# review.json: {"kind":"spec","passed":true,"receipt":"review-evidence-uri","artifact":"DELIVERED_REVISION","acceptance":{"profile":"code","children":[]}}
# Repeat using a fresh quality reviewer run and kind "quality".
px task handoff PJAN-129 --run-id "$RUN" --generation "$GEN" --revision "$REV" -f "$STATE/handoff.json" --json
# handoff.json: {"lane":"E2E Testing & QA","evidence":{"artifact":"DELIVERED_REVISION","acceptance":{"profile":"code","children":[]},"tests":{"passed":true,"receipt":"test-evidence-uri"}}}
```

Next handoffs specify `Ready for Documentation`, then `Done`. Both carry the same
artifact/acceptance plus `tests`, `docs`, `notebook`, `skill`, `main`, `push`, and
`deployment` gates. Each gate is `{"passed":true,"receipt":"evidence-uri"}` or
`{"applicable":false,"reason":"specific reason"}`. Declared children are immutable
`{"command_id":"CHILD_DONE_UUID","project_id":"CHILD_PROJECT","ticket_id":"CHILD_UUID"}`
objects; parents also supply `integration` evidence. Operator override receipts
cannot satisfy child completion. An explicit `non-code` profile permits successful
artifact delivery without a code-worker launch; all relevant review gates still apply.

```sh
px task attention PJAN-129 --run-id "$RUN" --generation "$GEN" --revision "$REV" -f "$STATE/question.json" --json
# question.json: {"question_id":"stable-question-id","question":"Which behavior is intended?","context":"Options, evidence and recommendation"}
px task resume PJAN-129 --run-id "$NEW_RUN" --revision "$REV" -f "$STATE/resume.json" --json
# resume.json: {"question_id":"stable-question-id","answer":"User's decision","ticket_revision":"CURRENT_CONTENT_HASH","artifact":"CURRENT_REVISION","acceptance":{"profile":"code","children":[]}}
px task plan PJAN-130 --revision "$REV" -f "$STATE/plan.json" --json
# plan.json: {"ticket_revision":"CONTENT_HASH","lane":"Todo","reason":"Refined and ready"}
px task comment PJAN-130 --revision "$REV" -f "$STATE/comment.json" --json
# comment.json: {"ticket_revision":"CONTENT_HASH","text":"Planning note"}
px task update PJAN-130 --revision "$REV" -f "$STATE/update.json" --json
# update.json: {"ticket_revision":"CONTENT_HASH","name":"Refined title"}
px task reevaluate PJAN-130 --actor "$OPERATOR" --revision "$REV" -f "$STATE/reevaluate.json" --json
# reevaluate.json: {"ticket_revision":"CONTENT_HASH","reason":"New scope resolves exhausted retries","receipt":"operator-decision-uri"}
px task override PJAN-130 --actor "$OPERATOR" --revision "$REV" -f "$STATE/override.json" --json
# override.json: {"ticket_revision":"CONTENT_HASH","reason":"Explicit manual acceptance","receipt":"operator-decision-uri"}
```

An active override additionally needs its current generation and run ID. Override
produces a distinct manual completion receipt, never a reviewed completion.
For uncertain commands use `px task status --operation-id "$COMMAND_ID" --json`;
`--retry-command "$COMMAND_ID"` replays the persisted original request. An operator
can reconcile a permanently failed intent with a fresh command and payload
`{"operation_id":"PENDING_UUID","resolution":"cancel","reason":"investigation result","receipt":"operator-evidence-uri"}`.
Use `resolution: "abandon"` only to record unreconciled provider state explicitly.
Never delete controller rows to release capacity. `px idea flush` reconciles queued
feedback; uncertain POSTs remain readback-only until their original marker appears.
