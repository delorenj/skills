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
   reviewers submit `px task review` with distinct reviewer identities/run IDs and
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
`execution.skill_version` to this canonical hash.
