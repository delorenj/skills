# board.crank.v1

The input, deployment receipt, worker observation and output receipt schemas are
[`board.crank.v1.json`](board.crank.v1.json). This is a control adapter for the
existing Momo per-ticket pipeline, supporting the deployed Hermes profile route.
It does not implement stateless contractors or certify their prerequisites.

Use Node 24.6 or newer, Python 3, and installed dependencies in the supplied
Bloodbank source root:

```sh
node skill/scripts/momo-board-crank.mjs inspect \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank

node skill/scripts/momo-board-crank.mjs execute \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank

node skill/scripts/momo-board-crank.mjs execute --replay \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank

node skill/scripts/momo-board-crank.mjs reconcile \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank
```

`inspect` and `--dry-run` perform no lease, journal, bus or ticket writes.
`execute` selects at most one ticket, waits only for its matching started
lifecycle, and exits. It first attempts reconciliation of an active prior journal.
`reconcile` retires a proven completed fence without dispatch or ticket changes.
Exit 78 means refused/uncertain, 124 means the 45-second budget expired.
Busy and idle are normal exit-zero outcomes, distinguished in JSON.
The entry point supervises each pass in a detached subprocess. Its external
wall-clock limit includes synchronous Pilot/1Password reads. Timeout or child
error kills the entire process group and emits a sanitized result; already
fsynced intent remains an execution fence. Successful JSON is parsed after the
child's `close` event, when stdout has drained. Child stderr is discarded and
stdout is limited to 256 KiB. `MOMO_BOARD_CRANK_BUDGET_MS` is a private fixture
control that can shorten, never extend, the production limit.

## Deployment gate

No enabled configuration, deployment receipt, worker-status producer or cron is
shipped. Source tests cannot supply live prerequisites. The parent/runtime owner
must resolve 33GOD-44/46/50 and independently verify a single driver, gateway
command-ID/exact-envelope journal, deployed contractor/version, bundle digest,
board binding, profile, memory policy and independent review roles first.

The input explicitly names project/workspace/board/workdir; contractor/version in
`hermes-profile` mode; skill root/SHA256; memory `write_bank`/`recall_banks`; three
distinct implementer/spec-reviewer/quality-reviewer actors; runtime paths and
NATS hostname. No credentials belong in inputs or receipts. Pilot resolves its
normal configuration and credentials in memory.

The runtime owner authors the separate `board.crank.runtime.v1` receipt after
independent runtime acceptance. Matching binding, contractor, profile, shared
lease, journal directory, worker-status file, bundle digest, memory policy, roles,
`accepted`, `single_driver`, `gateway_command_journal`, `independent_reviews`,
`control_lease_handoff`, `verified_at` and `expires_at`
are checked on each pass. This is an acceptance attestation, not an automatic
installed-service audit. Fabricated/stale attestations are not deployment proof.

`skillDigest(skillRoot)` in `scripts/lib/board_crank_ports.mjs` computes SHA256 of
the canonical JSON array of sorted relative file paths and their content SHA256s:
SKILL.md and all files under references/, scripts/ and contracts/, excluding
tests/ and __pycache__/. This includes the executable adapter, lease helper and
schemas. File additions, renames and content edits change acceptance identity.
The executing source bundle must also match the installed accepted bundle.
Changed bundles need new acceptance; pending work binds the complete contractor
and runtime configuration, including receipt paths and broker, and refuses
changes. Configuration hashing sorts object keys recursively; it does not change
saved envelope bytes. Keep the accepted per-board journal directory stable.

The same runtime owner produces `board.crank.workers.v1` from actual implementation
and review supervision: board, `observed_at` and every pending/active/review
execution (`ticket_id`, `command_id`, `status`). Empty means verified absence,
never a failed probe. Observations older than 60 seconds or from the future
refuse execution. The driver lease must be exactly the manifest-bound
`<role_dir>/runtime/wip-driver.lock`. The adapter uses `momo-wip-lock.py`, unique
owners, refresh and owner-safe release; it never uses `--steal`.

The gateway publishes started before handing the prompt to Hermes. The control
adapter still holds its short lease while it verifies start and patches state/date.
The PM must wait for that lease's release and acquire the SAME path with a unique
owner before driving implementation/review. The invocation supplies that path and
instruction. `control_lease_handoff` attests that this installed handoff was tested;
it is a runtime acceptance prerequisite, not proof supplied by the prompt itself.

Journal storage must already exist at its canonical path outside source or in an
already ignored runtime directory; symlink aliases are refused. Deployment/worker
receipts also belong outside source or in existing
ignored runtime storage. A NATS URL cannot contain credentials. There is no
source-side runtime setup or default enabled input.

Before its first intent, while owning and refreshing that same driver lease,
execute atomically persists `${driver_lease}.board-crank.json` beside the lease.
The binding records the project, authoritative driver and canonical `state_dir`;
its file and containing directory are fsynced. All later configurations must
match it, including configurations carrying a renewed runtime receipt. A new
receipt cannot relocate a journal or hide its original uncertain execution.
Inspect/dry-run never creates this binding. Missing canonical storage, symlinks,
corrupt or differing bindings fail closed. The runtime owner investigates any
storage migration; there is no public rotation/clear command or TTL retirement.
No new manifest field is required.

## Readiness and selection

Only the unique exact `Todo` lane with `lifecycle:triaged` is considered. Tickets
need a title, enumerated/testable acceptance criteria and FR references. Drafts,
archives, deleted items, blocked/refining/needs-input labels, epic labels and
parents with children are excluded. Written unresolved prerequisites without
matching completed native predecessors are excluded. Every written reference
must match; one completed predecessor does not satisfy other written blockers.
Explicit no-dependency prose remains valid. Nonstring descriptions are thin
input and do not abort a mixed board. Only the acceptance section supplies
criteria, and every enumerated criterion is validated, including criteria after
interleaved prose; numbered Notes cannot fortify an empty acceptance section.

Pilot's current Plane API supplies `work-items/<id>/relations/`. Every `blocked_by`,
`start_after` and `finish_after` predecessor must be known on this board and
completed; cancellation does not satisfy a dependency. Missing/unknown/cross-board
dependency truth excludes the candidate. Cycle configuration must be an explicit
boolean. Cycle-enabled boards must supply trustworthy cycles/memberships;
future/finished assignments are ineligible. Cycle-disabled boards do not invent
cycles. Rank urgent/high/medium/low/none, then active-cycle fit, known downstream
tickets unblocked, oldest creation time and stable ID. Downstream credit requires
observed predecessors and written requirements showing this ticket would resolve
every remaining blocker; unknown relations or additional blockers earn no credit.
Scores, rubric, rationale and exclusions persist in the journal.

Any exact In Progress ticket, agent:working ticket or fresh runtime execution
blocks new dispatch. During recovery only a worker with both the saved ticket
and exact command ID is exempt; foreign/missing command IDs on the same ticket
still fence replay and writes. Expired driver TTL never frees implementation WIP.
A pass caps Todo hydration at 100 items. Native relations, downstream target
relations and enabled cycle membership share a 5-second hydration deadline with
at most eight concurrent reads, retaining dispatch/readback time within the
45-second supervised pass. A larger or unobservable board refuses rather than
selecting from a partial sample.

## Dispatch and recovery

Bloodbank's canonical builder/validator construct its existing invocation command,
carrying contractor/version, project, board, ticket, workdir, memory policy,
roles and shared lease. Canonical `reason: ticket-delegation` is retained for
existing completion consumers; `origin` attributes the Board Cranker. The existing
delegation prompt is extended to preserve fields and leave
initial state/date writes to the adapter. The PM delegates product code; spec and
quality review require distinct fresh actors and the existing gates.

The exact envelope and digest are fsynced before publication. Bloodbank's publisher
connection seam uses its installed official JetStream client to require a
BLOODBANK_COMMANDS PubAck. Stable IDs and identical bytes reach the gateway's
command-ID/envelope-digest journal. There is no new bus subject or copied
envelope/wire/credential grammar.
Journal ticket, project and route identities must match that envelope's context
and target before recovery. The intent also binds a content revision of the
prompted ticket ID, title, sequence and description. Fresh content must match
immediately before publication/replay and after start before claiming the ticket.
A changed eligible requirement keeps the exact original command fenced; it does
not mint a replacement prompt or command automatically.

PubAck is storage evidence. Started proof needs schema-valid turn.started caused
by the command and invocation.started caused by that turn. Command/idempotency,
correlation, target/profile, producer/service, thread/turn and full context must
match. Gateway starts precede actual Hermes handling: they acknowledge that
lifecycle, not proof that a delegated worker finished. Retained receipts are read
through Bloodbank direct-get helpers without creating a consumer. Searches begin
with a recent 16-sequence window and at most 100 requests, with 500-ms started
searches and a 1-second completed search. This bounded near-tip search reaches
recent matching events amid dense unrelated history; absence within the budget
preserves uncertainty rather than proving no execution.

After matching start, reload runtime, route, board and selected ticket. PATCH only
state and an absent start_date through Pilot editIssue. Preserve labels, assignees
and unrelated content. An immediate second ticket read refuses detected human
changes; journal the PATCH intent before sending and read back afterwards. Plane
does not supply an atomic conditional write here, so the final read/PATCH window
remains a concurrency limitation for independent review.
Runtime acceptance and worker freshness are rechecked, and the lease refreshed,
after hydration immediately before publication and provider mutation. Truth that
was fresh before a slow hydration cannot authorize a later external effect.

Publication failure or unmatched start leaves the ticket ready and retains
uncertainty. A normal pass checks receipts; explicit `--replay` sends only the
saved command after revalidation. No other worker can be minted while fenced.
After shared lease acquisition the adapter reloads the journal and decides from
that fresh value. A contender that observed no journal before waiting cannot
overwrite an intent persisted by the preceding driver.
Corrupt journals, changed pending configuration, missing/ineligible routes,
managed/shadow modes and unavailable prerequisites fail closed.

Lost PATCH responses are read back. Partial mutation, later human transitions and
missing readback remain truthful uncertainty. No PATCH or compensation is blindly
replayed. `mutation_conflict` needs the existing runtime owner's investigation.
There is no force-clear flag and no TTL expiry for an implementation fence.

## Completion reconciliation

The existing Momo runtime owner invokes reconciliation, explicitly or at the
start of a later execute pass, under the SAME driver lease. Only an active fence
can be retired, after all three agree:

1. A schema-valid invocation.completed matches the saved command, idempotency,
   target/profile, full context and exact started-event causation.
2. A worker observation at or after completion reports zero pending/active/review
   workers anywhere on this board and is no older than 60 seconds.
3. Fresh board/ticket reads show the original ticket in unique Done/completed,
   no other In Progress/agent:working WIP, unchanged route and binding.

Completion and original command/start/terminal/readback evidence are durably
archived in `completed/<command_id>.json`. The next pass can dispatch at most one
later ticket. A crash between completion persistence and archive creation is
recoverable: reconciliation repairs the archive, and execute confirms it before
replacing the completed journal. Archive failure prevents advancing a later ticket.
Inspect cannot retire a fence. PM completion alone, board state
alone, an empty snapshot alone, TTL, failure events and ambiguous mutation phases
never retire it. The post-completion worker-status producer and retained gateway
receipts are explicit runtime prerequisites; this change enables neither.

All output receipts carry `live_execution_proof: false`. Installed runtime/cron,
real broker receipts, worker evidence and independent review remain separate
parent acceptance work.
