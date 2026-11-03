import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, readFileSync, writeFileSync, existsSync, statSync, lstatSync, symlinkSync, cpSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { crank, reconcile, Journal, rankCandidates, matchStarted, matchCompleted, validateRuntime } from '../lib/board_crank.mjs';
import { loadBloodbank, loadProductionPorts, commandFor, publishExact, resolveRoute, skillDigest } from '../lib/board_crank_ports.mjs';

// Use the current canonical builders/validators, with no broker, HTTP or vault.
// Source roots are supplied explicitly; the tests never modify those sources.
const bb = loadBloodbank(process.env.BLOODBANK_SOURCE_ROOT);
const scripts = resolve(fileURLToPath(new URL('..', import.meta.url)));
const clock = Date.parse('2026-10-05T10:30:00Z');
const boardId = '15258893-0206-4e8f-aea6-340eb217988c';
const ticketId = n => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`;
const clone = value => structuredClone(value);
const states = [{ id: 'todo', name: 'Todo', group: 'unstarted' },
  { id: 'started', name: 'In Progress', group: 'started' },
  { id: 'refine', name: 'Needs Re-evaluation', group: 'unstarted' },
  { id: 'blocked', name: 'Needs Attention', group: 'started' },
  { id: 'done', name: 'Done', group: 'completed' }, { id: 'cancelled', name: 'Cancelled', group: 'cancelled' }];
const labels = [{ id: 'triaged', name: 'lifecycle:triaged' }, { id: 'working', name: 'agent:working' },
  { id: 'blocked-label', name: 'lifecycle:blocked' }, { id: 'epic', name: 'type:epic' }];
const emptyRelations = () => ({ blocked_by: [], blocking: [], start_after: [], finish_after: [] });
const ticket = (n, changes = {}) => ({ id: ticketId(n), name: `Work ${n}`, sequence_id: n, state: 'todo',
  priority: 'high', labels: ['triaged'], assignees: ['existing-person'], start_date: null,
  created_at: '2026-10-01T12:00:00Z', updated_at: '2026-10-02T12:00:00Z', parent: null,
  description_html: '<h2>Business goal</h2><p>Preserve existing work.</p><h2>Acceptance criteria / FR coverage</h2>' +
    '<ol><li>AC-1 / FR-25: Given ready work, when invoked, then exactly one command is persisted.</li>' +
    '<li>AC-2 / FR-26: Given a restart, when retried, then the original ticket fields are preserved.</li></ol>', ...changes });

function receipts(envelope, route) {
  const data = { command_id: envelope.command_id, idempotency_key: envelope.idempotency_key, target_agent_id: envelope.data.target_agent_id,
    profile_name: route.profileName, thread_id: `bloodbank:${envelope.correlationid}`, turn_id: envelope.command_id };
  const common = { source: 'urn:33god:service:bloodbank-hermes-gateway', producer: `hermes-agent:${route.profileName}`,
    service: 'bloodbank-hermes-gateway', actor: { type: 'agent_api', agent_id: route.agentId, cli: 'hermes' },
    correlationId: envelope.correlationid, orderingKey: `turn:${envelope.command_id}`, observedAt: envelope.time };
  const turn = bb.nats.buildEnvelope({ ...common, type: 'bloodbank.conversation.turn.started',
    causationId: envelope.id, data: { ...data, prompt_text: null } }).envelope;
  const started = bb.nats.buildEnvelope({ ...common, type: 'bloodbank.agent.invocation.started',
    causationId: turn.id, data: { ...data, invocation_id: envelope.command_id, parent_invocation_id: null,
      context: envelope.data.context } }).envelope;
  for (const e of [turn, started]) bb.nats.validateEnvelope(e.type, e);
  return [turn, started];
}

function fixture(t, issues = [ticket(1), ticket(2)]) {
  const dir = mkdtempSync(join(tmpdir(), 'board-crank-fixture-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const c = { contract: 'board.crank.v1', enabled: true,
    project: { id: 'test', workspace: '33god', board_id: boardId, workdir: dir },
    contractor: { name: 'momo', version: '1', mode: 'hermes-profile', skill_root: '/fixture/skill',
      skill_sha256: 'a'.repeat(64), memory_policy: { write_bank: 'test', recall_banks: ['test'] },
      roles: { implementer: 'worker', spec_reviewer: 'spec-reviewer', quality_reviewer: 'quality-reviewer' } },
    runtime: { state_dir: dir, driver_lease: join(dir, 'wip-driver.lock'), registry_file: join(dir, 'registry.yaml'),
      worker_status_file: join(dir, 'workers.json'), deployment_receipt: join(dir, 'deployed.json'),
      profile_root: dir, nats_server: 'nats://fixture.invalid:4222', ack_timeout_ms: 1000 } };
  const route = { agentId: 'test-pm', eligible: true, matchedBy: 'board', profileName: 'test-pm',
    workspace: c.project.workspace, identifier: 'TEST', projectPath: dir };
  const f = { c, dir, clock, route, commands: [], patches: [], runtimeReads: 0, boardReads: 0, ticketReads: 0,
    acknowledge: true, publishFails: false, patchFails: false, partial: false, acquireCalls: 0,
    workers: { contract: 'board.crank.workers.v1', board_id: boardId, observed_at: new Date(clock).toISOString(), active: [] },
    board: { id: boardId, identifier: 'TEST', states: clone(states), labels: clone(labels), issues: clone(issues), relations: {}, cycle_view: false } };
  for (const i of issues) f.board.relations[i.id] = emptyRelations();
  const deployment = { contract: 'board.crank.runtime.v1', accepted: true, pipeline: 'momo-per-ticket',
    contractor: 'momo', version: '1', project_id: c.project.id, board_id: boardId, workdir: dir,
    profile_name: route.profileName, driver_lease: c.runtime.driver_lease, skill_sha256: c.contractor.skill_sha256,
    state_dir: c.runtime.state_dir, worker_status_file: c.runtime.worker_status_file, control_lease_handoff: true,
    memory_policy: clone(c.contractor.memory_policy), roles: clone(c.contractor.roles), single_driver: true,
    gateway_command_journal: true, independent_reviews: true, verified_at: '2026-10-05T09:00:00Z', expires_at: '2026-10-06T09:00:00Z' };
  f.deployment = deployment;
  f.journal = new Journal(dir, boardId);
  f.ports = {
    now: () => f.clock, journal: f.journal,
    async runtime() {
      f.runtimeReads++;
      f.onRuntime?.(f.runtimeReads);
      return { manifest: { project_id: c.project.id, ticket_provider: { type: 'plane',
        board_id: boardId, workspace: c.project.workspace }, execution: { mode: f.mode ?? 'legacy' } },
      route: clone(f.route), deployment: clone(f.deployment), workers: clone(f.workers), skillSha256: c.contractor.skill_sha256 };
    },
    async board() { await f.onBoard?.(++f.boardReads); return clone(f.board); },
    async leaseBusy(path) {
      if (!existsSync(path)) return false;
      const lease = JSON.parse(readFileSync(path));
      return Date.now() / 1000 - lease.heartbeat_at < lease.ttl;
    },
    async lease(op, path, owner) {
      if (op === 'acquire') f.acquireCalls++;
      try { execFileSync('python3', [join(scripts, 'momo-wip-lock.py'), op, path, owner], { stdio: 'pipe' }); return true; }
      catch { return false; }
    },
    async command(c, chosen, route) { return commandFor(bb, c, chosen, route, f.clock); },
    async publish(c, envelope) {
      assert.equal(f.journal.load().intent.envelope.command_id, envelope.command_id, 'intent precedes transport');
      f.commands.push(clone(envelope));
      await f.onPublish?.(envelope);
      if (f.publishFails) throw new Error('fixture transport timeout');
      return { status: 'stored', stream: 'BLOODBANK_COMMANDS', sequence: f.commands.length };
    },
    async started(c, envelope, route) {
      if (!f.commands.some(command => command.command_id === envelope.command_id) || !f.acknowledge) return [];
      const pair = receipts(envelope, route);
      f.alterReceipt?.(pair);
      return pair;
    },
    async completed(c, j, route) {
      if (!f.completed) return null;
      const e = j.intent.envelope, started = j.started[1];
      const terminal = bb.nats.buildEnvelope({ type: 'bloodbank.agent.invocation.completed',
        source: 'urn:33god:service:bloodbank-hermes-gateway', producer: `hermes-agent:${route.profileName}`,
        service: 'bloodbank-hermes-gateway', actor: { type: 'agent_api', agent_id: route.agentId, cli: 'hermes' },
        correlationId: e.correlationid, causationId: started.id, orderingKey: `turn:${e.command_id}`,
        observedAt: new Date(f.clock).toISOString(), data: { command_id: e.command_id,
          idempotency_key: e.idempotency_key, target_agent_id: route.agentId, profile_name: route.profileName,
          invocation_id: e.command_id, thread_id: started.data.thread_id, turn_id: started.data.turn_id, context: e.data.context } }).envelope;
      bb.nats.validateEnvelope(terminal.type, terminal); f.alterCompleted?.(terminal); return terminal;
    },
    async ticket(c, id) {
      f.ticketReads++; f.onTicket?.(f.ticketReads);
      if (f.readbackFails && f.patches.length) throw new Error('fixture readback unavailable');
      return clone(f.board.issues.find(i => i.id === id));
    },
    async patch(c, id, fields) {
      assert.ok(f.journal.load().started, 'started receipt precedes mutation');
      f.patches.push({ id, fields: clone(fields) });
      const i = f.board.issues.find(i => i.id === id);
      Object.assign(i, f.partial ? { state: fields.state } : fields);
      if (f.patchFails) throw new Error('fixture response lost after apply');
    },
  };
  f.run = options => crank(c, f.ports, { execute: true, ...options });
  f.zero = () => { assert.equal(f.commands.length, 0); assert.equal(f.patches.length, 0); };
  return f;
}

test('idle and inspect have no lease writes, publication or ticket mutations', async t => {
  const f = fixture(t, []);
  assert.equal((await f.run()).status, 'idle'); f.zero(); assert.equal(f.acquireCalls, 0);
  f.board.issues.push(ticket(1)); f.board.relations[ticketId(1)] = emptyRelations();
  const result = await f.run({ execute: false });
  assert.equal(result.status, 'ready'); assert.equal(result.selected, ticketId(1));
  f.zero(); assert.equal(f.acquireCalls, 0); assert.equal(existsSync(f.journal.path), false);
});

test('fresh shared lease refuses zero writes and preserves its owner', async t => {
  const f = fixture(t);
  const held = { owner: 'hermes:other', heartbeat_at: Date.now() / 1000, ttl: 1800 };
  writeFileSync(f.c.runtime.driver_lease, JSON.stringify(held));
  assert.equal((await f.run()).status, 'busy'); f.zero(); assert.equal(f.acquireCalls, 0);
  assert.deepEqual(JSON.parse(readFileSync(f.c.runtime.driver_lease)), held);
});

test('STALE driver TTL never frees implementation capacity claimed on the board', async t => {
  const f = fixture(t, [ticket(1), ticket(79, { state: 'started' })]);
  const held = { owner: 'hermes:33god-pm:bmad-bridge', heartbeat_at: Date.now() / 1000 - 27498, ttl: 1800 };
  writeFileSync(f.c.runtime.driver_lease, JSON.stringify(held));
  assert.equal((await f.run()).status, 'busy'); f.zero(); assert.equal(f.acquireCalls, 0);
  assert.deepEqual(JSON.parse(readFileSync(f.c.runtime.driver_lease)), held);
});

test('fresh runtime implementation and working-label WIP independently fence dispatch', async t => {
  for (const kind of ['runtime', 'label']) {
    const f = fixture(t);
    if (kind === 'runtime') f.workers.active.push({ ticket_id: ticketId(9) });
    else f.board.issues[1].labels.push('working');
    assert.equal((await f.run()).status, 'busy'); f.zero();
  }
});

test('direct-in-Todo selects exactly one and preserves every unrelated field', async t => {
  const f = fixture(t);
  const second = clone(f.board.issues[1]); const first = clone(f.board.issues[0]);
  const result = await f.run();
  assert.equal(result.status, 'started'); assert.equal(result.live_execution_proof, false);
  assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 1);
  assert.deepEqual(f.patches[0].fields, { state: 'started', start_date: '2026-10-05' });
  assert.deepEqual(f.board.issues[1], second);
  assert.deepEqual(f.board.issues[0], { ...first, state: 'started', start_date: '2026-10-05' });
  const j = f.journal.load(); assert.equal(j.phase, 'active'); assert.ok(j.selected.score);
  assert.equal(statSync(f.journal.path).mode & 0o777, 0o600);
  assert.equal(existsSync(f.c.runtime.driver_lease), false);
});

test('existing start date is never reset, labels and assignees are never PATCHed', async t => {
  const f = fixture(t, [ticket(1, { start_date: '2026-08-15' })]);
  assert.equal((await f.run()).status, 'started'); assert.deepEqual(f.patches[0].fields, { state: 'started' });
  assert.equal(f.board.issues[0].start_date, '2026-08-15');
});

test('ranking is priority, cycle fit, critical dependency path, age, stable ID', t => {
  const f = fixture(t, [ticket(1, { priority: 'medium' }), ticket(2), ticket(3)]);
  f.board.cycle_view = true;
  f.board.cycles = [{ id: 'cycle', start_date: '2026-10-01T00:00:00Z', end_date: '2026-10-20T00:00:00Z' }];
  f.board.cycle_members = { cycle: [ticketId(3)] };
  assert.equal(rankCandidates(f.board, f.clock).ranked[0].ticket_id, ticketId(3));
  f.board.cycle_view = false;
  f.board.relations[ticketId(3)].blocking.push({ project_id: boardId, issue_id: ticketId(1) });
  f.board.relations[ticketId(1)].blocked_by.push({ project_id: boardId, issue_id: ticketId(3) });
  assert.equal(rankCandidates(f.board, f.clock).ranked[0].ticket_id, ticketId(3));
  f.board.relations[ticketId(3)].blocking = [];
  f.board.relations[ticketId(1)].blocked_by = [];
  f.board.issues[2].created_at = '2026-09-01T00:00:00Z';
  assert.equal(rankCandidates(f.board, f.clock).ranked[0].ticket_id, ticketId(3));
  f.board.issues[2].created_at = f.board.issues[1].created_at;
  assert.equal(rankCandidates(f.board, f.clock).ranked[0].ticket_id, ticketId(2));
});

test('thin, untriaged, refining, blocked, unknown dependency, cancelled dependency and parent epic are excluded', async t => {
  const scenarios = ['thin', 'untriaged', 'refining', 'blocked', 'unknown', 'pending-dependency', 'cancelled-dependency', 'parent', 'written', 'relations'];
  for (const kind of scenarios) {
    const f = fixture(t, [ticket(1)]);
    const i = f.board.issues[0];
    if (kind === 'thin') i.description_html = 'please fix it';
    if (kind === 'untriaged') i.labels = [];
    if (kind === 'refining') i.state = 'refine';
    if (kind === 'blocked') i.labels.push('blocked-label');
    if (['unknown', 'pending-dependency', 'cancelled-dependency'].includes(kind)) {
      f.board.relations[i.id].blocked_by.push({ project_id: boardId, issue_id: ticketId(9) });
      if (kind !== 'unknown') f.board.issues.push(ticket(9, { state: kind === 'cancelled-dependency' ? 'cancelled' : 'blocked' }));
    }
    if (kind === 'parent') f.board.issues.push(ticket(9, { state: 'refine', parent: i.id }));
    if (kind === 'written') i.description_html += '<h2>Dependencies</h2><p>Blocked by an unresolved service.</p>';
    if (kind === 'relations') f.board.relations[i.id] = null;
    assert.equal((await f.run()).status, 'idle', kind); f.zero();
  }
});

test('completed native dependency is eligible; future cycle and duplicate Todo lanes refuse', async t => {
  const f = fixture(t, [ticket(1), ticket(9, { state: 'done' })]);
  f.board.relations[ticketId(1)].blocked_by.push({ project_id: boardId, issue_id: ticketId(9) });
  assert.equal((await f.run({ execute: false })).status, 'ready');
  f.board.cycle_view = true; f.board.cycles = [{ id: 'future', start_date: '2026-11-01', end_date: '2026-11-30' }];
  f.board.cycle_members = { future: [ticketId(1)] };
  assert.equal((await f.run()).status, 'idle'); f.zero();
  f.board.states.push({ id: 'todo-other', name: 'Todo', group: 'unstarted' });
  assert.equal((await f.run()).status, 'refused'); f.zero();
});

test('dispatch failure retains exact uncertain intent, never touches the ready ticket', async t => {
  const f = fixture(t); f.publishFails = true;
  const before = clone(f.board.issues);
  assert.equal((await f.run()).status, 'uncertain');
  assert.deepEqual(f.board.issues, before); assert.equal(f.patches.length, 0);
  assert.equal(f.journal.load().phase, 'uncertain');
  f.ports.journal = new Journal(f.dir, boardId); // process restart
  f.publishFails = false;
  assert.equal((await f.run({ replay: true })).status, 'started');
  assert.equal(f.commands.length, 1, 'a stored matching started receipt needs no republish');
});

test('unacknowledged restart replay reuses command ID AND exact envelope bytes', async t => {
  const f = fixture(t); f.acknowledge = false;
  assert.equal((await f.run()).status, 'uncertain');
  const original = JSON.stringify(f.commands[0]);
  f.ports.journal = new Journal(f.dir, boardId);
  assert.equal((await f.run()).status, 'uncertain'); assert.equal(f.commands.length, 1);
  assert.equal((await f.run({ replay: true })).status, 'uncertain');
  assert.equal(JSON.stringify(f.commands[1]), original); assert.equal(f.patches.length, 0);
  f.acknowledge = true;
  assert.equal((await f.run()).status, 'started'); assert.equal(f.commands.length, 2);
  assert.equal((await f.run()).status, 'busy'); assert.equal(f.commands.length, 2);
});

test('transport ACK, wrong target, command, causation, profile, context and service never count as started', async t => {
  for (const key of ['missing', 'target', 'command', 'causation', 'profile', 'context', 'service']) {
    const f = fixture(t);
    if (key === 'missing') f.acknowledge = false;
    else f.alterReceipt = pair => {
      if (key === 'target') pair[1].data.target_agent_id = 'wrong-pm';
      if (key === 'command') pair[1].data.command_id = crypto.randomUUID();
      if (key === 'causation') pair[0].causationid = crypto.randomUUID();
      if (key === 'profile') pair[1].data.profile_name = 'other-profile';
      if (key === 'context') pair[1].data.context = { ...pair[1].data.context, ticket_id: ticketId(88) };
      if (key === 'service') pair[1].service = 'unrelated-producer';
    };
    assert.equal((await f.run()).status, 'uncertain', key); assert.equal(f.patches.length, 0);
    assert.equal(f.board.issues[0].state, 'todo');
  }
});

test('ambiguous PATCH applied fully is confirmed by readback without repeating writes', async t => {
  const f = fixture(t); f.patchFails = true;
  assert.equal((await f.run()).status, 'started'); assert.equal(f.patches.length, 1);
  assert.ok(f.journal.load().receipts.some(r => r.kind === 'mutation' && r.status === 'uncertain'));
  assert.equal((await f.run()).status, 'busy'); assert.equal(f.patches.length, 1);
});

test('partial write is journaled honestly and never overwritten or compensated blindly', async t => {
  const f = fixture(t); f.partial = true; f.patchFails = true;
  assert.equal((await f.run()).status, 'uncertain');
  assert.equal(f.board.issues[0].state, 'started'); assert.equal(f.board.issues[0].start_date, null);
  assert.equal(f.journal.load().phase, 'mutation_conflict');
  f.board.issues[0].state = 'blocked'; f.board.issues[0].start_date = '2026-08-15';
  assert.equal((await f.run({ replay: true })).status, 'busy'); assert.equal(f.patches.length, 1);
  assert.equal(f.board.issues[0].state, 'blocked'); assert.equal(f.board.issues[0].start_date, '2026-08-15');
});

test('crash after PATCH with no readback recovers from stored fields and never PATCHes again', async t => {
  const f = fixture(t); f.readbackFails = true;
  assert.equal((await f.run()).status, 'uncertain'); assert.equal(f.journal.load().phase, 'mutation_uncertain');
  f.ports.journal = new Journal(f.dir, boardId); f.readbackFails = false;
  assert.equal((await f.run()).status, 'started'); assert.equal(f.patches.length, 1); assert.equal(f.commands.length, 1);
});

test('human changes immediately before PATCH are preserved with zero writes', async t => {
  const f = fixture(t);
  f.onTicket = () => { if (f.journal.load()?.phase === 'mutation_uncertain' && !f.patches.length) Object.assign(f.board.issues[0],
    { state: 'blocked', start_date: '2026-09-01', updated_at: '2026-10-05T10:30:00Z' }); };
  assert.equal((await f.run()).status, 'uncertain'); assert.equal(f.patches.length, 0);
  assert.equal(f.board.issues[0].state, 'blocked'); assert.equal(f.board.issues[0].start_date, '2026-09-01');
});

test('a conflicting readback date remains uncertain and is never corrected automatically', async t => {
  const f = fixture(t);
  f.onTicket = () => { if (f.patches.length) f.board.issues[0].start_date = '2026-09-01'; };
  assert.equal((await f.run()).status, 'uncertain');
  assert.equal(f.journal.load().phase, 'mutation_conflict');
  assert.equal((await f.run({ replay: true })).status, 'busy');
  assert.equal(f.board.issues[0].start_date, '2026-09-01'); assert.equal(f.patches.length, 1);
});

test('eligibility is reloaded immediately before publication and after acknowledgement', async t => {
  for (const at of ['before-publish', 'after-start']) {
    const f = fixture(t); f.onRuntime = () => {
      if (at === 'before-publish' && f.journal.load()?.phase === 'uncertain' && !f.commands.length ||
        at === 'after-start' && f.journal.load()?.phase === 'started') f.route.eligible = false;
    };
    assert.equal((await f.run()).status, 'uncertain'); assert.equal(f.patches.length, 0);
    assert.equal(f.commands.length, at === 'before-publish' ? 0 : 1);
  }
});

test('WIP appearing after acquire aborts before journal or dispatch', async t => {
  const f = fixture(t); f.onBoard = n => { if (n === 2) f.board.issues[1].state = 'started'; };
  assert.equal((await f.run()).status, 'refused'); f.zero();
});

test('managed/shadow, disabled, missing prerequisites, stale worker status and reviewer aliasing refuse', async t => {
  for (const kind of ['managed', 'shadow', 'disabled', 'prerequisite', 'stale', 'reviewer', 'stateless', 'memory']) {
    const f = fixture(t);
    if (['managed', 'shadow'].includes(kind)) f.mode = kind;
    if (kind === 'disabled') f.c.enabled = false;
    if (kind === 'prerequisite') f.deployment.gateway_command_journal = false;
    if (kind === 'stale') f.workers.observed_at = '2026-10-01T10:00:00Z';
    if (kind === 'reviewer') f.c.contractor.roles.spec_reviewer = f.c.contractor.roles.implementer;
    if (kind === 'stateless') f.c.contractor.mode = 'stateless-contractor';
    if (kind === 'memory') delete f.c.contractor.memory_policy;
    assert.equal((await f.run()).status, 'refused', kind); f.zero(); assert.equal(f.acquireCalls, 0);
  }
});

test('expired TTL and process restart cannot start a second worker with durable active journal', async t => {
  const f = fixture(t);
  assert.equal((await f.run()).status, 'started');
  f.board.issues[0].state = 'done'; f.clock += 3600000;
  f.workers.observed_at = new Date(f.clock).toISOString();
  f.ports.journal = new Journal(f.dir, boardId);
  assert.equal((await f.run()).status, 'busy'); assert.equal(f.commands.length, 1);
});

test('two concurrent processes share the actual WIP lease and dispatch one command', async t => {
  const f = fixture(t);
  const result = await Promise.all([f.run(), f.run()]);
  assert.equal(result.filter(r => r.status === 'started').length, 1);
  assert.equal(result.filter(r => r.status === 'busy').length, 1);
  assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 1);
});

test('journal created after a contender reads null and before lease acquisition is never overwritten', async t => {
  const f = fixture(t); f.acknowledge = false;
  let resume, paused;
  const gate = new Promise(resolve => { resume = resolve; });
  const reached = new Promise(resolve => { paused = resolve; });
  const delayed = { ...f.ports, async leaseBusy(path) { paused(); await gate; return f.ports.leaseBusy(path); } };
  const contender = crank(f.c, delayed, { execute: true });
  await reached; // contender already loaded null, but has not acquired
  assert.equal((await f.run()).status, 'uncertain');
  const preserved = readFileSync(f.journal.path, 'utf8');
  resume();
  assert.equal((await contender).status, 'uncertain');
  assert.equal(readFileSync(f.journal.path, 'utf8'), preserved);
  assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 0);
  assert.equal(f.board.issues[0].state, 'todo');
});

test('changed contractor policy and corrupt journals fail closed after restart', async t => {
  const f = fixture(t); f.acknowledge = false;
  await f.run(); f.c.contractor.version = '2'; f.deployment.version = '2';
  assert.equal((await f.run({ replay: true })).status, 'uncertain'); assert.equal(f.commands.length, 1);
  const journal = f.journal.load(); journal.intent.envelope.data.prompt += ' altered';
  writeFileSync(f.journal.path, JSON.stringify(journal));
  assert.equal((await f.run({ replay: true })).status, 'refused'); assert.equal(f.commands.length, 1);
});

test('deployment attestation binds journal, worker supervision and control lease handoff', async t => {
  for (const field of ['state_dir', 'worker_status_file', 'control_lease_handoff']) {
    const f = fixture(t); delete f.deployment[field];
    assert.equal((await f.run()).status, 'refused', field); f.zero();
  }
  const f = fixture(t);
  f.deployment.memory_policy = { recall_banks: ['test'], write_bank: 'test' };
  f.deployment.roles = { quality_reviewer: 'quality-reviewer', spec_reviewer: 'spec-reviewer', implementer: 'worker' };
  assert.equal((await f.run()).status, 'started', 'object key order does not change attested policy');
});

test('pending execution refuses changed worker path or broker even with renewed attestation', async t => {
  for (const field of ['worker_status_file', 'nats_server']) {
    const f = fixture(t); f.acknowledge = false; await f.run();
    const before = readFileSync(f.journal.path, 'utf8');
    f.c.runtime[field] = field === 'nats_server' ? 'nats://other-fixture.invalid:4222' : join(f.dir, 'other-workers.json');
    if (field === 'worker_status_file') f.deployment[field] = f.c.runtime[field];
    assert.equal((await f.run({ replay: true })).status, 'uncertain', field);
    assert.equal(readFileSync(f.journal.path, 'utf8'), before); assert.equal(f.commands.length, 1);
    assert.equal(f.patches.length, 0);
  }
});

test('two configurations cannot reuse one deployment receipt with different journal directories', async t => {
  const f = fixture(t); f.acknowledge = false;
  assert.equal((await f.run()).status, 'uncertain');
  const preserved = readFileSync(f.journal.path, 'utf8');
  const other = clone(f.c); other.runtime.state_dir = join(f.dir, 'alternate-state');
  mkdirSync(other.runtime.state_dir);
  const secondJournal = new Journal(other.runtime.state_dir, boardId);
  assert.equal((await crank(other, { ...f.ports, journal: secondJournal }, { execute: true })).status, 'refused');
  assert.equal(existsSync(secondJournal.path), false);
  assert.equal(readFileSync(f.journal.path, 'utf8'), preserved);
  assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 0);
});

test('a completed journal marker without matching completion evidence cannot retire uncertainty', async t => {
  const f = fixture(t); f.acknowledge = false; await f.run();
  const corrupt = f.journal.load(); corrupt.phase = 'completed';
  writeFileSync(f.journal.path, JSON.stringify(corrupt));
  const preserved = readFileSync(f.journal.path, 'utf8');
  assert.equal((await f.run()).status, 'refused');
  assert.equal(readFileSync(f.journal.path, 'utf8'), preserved);
  assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 0);
});

test('production route reuses canonical activation rules and refuses duplicate board owners', t => {
  const f = fixture(t);
  const row = { profile_name: 'test-pm', project_path: f.c.project.workdir, plane: {
    board_id: boardId, workspace: '33god', identifier: 'TEST' },
  bloodbank: { gateway_scope: 'fleet', target_agent_id: 'test-pm' } };
  const registry = { schema_version: 1, agents: { 'test-pm': row } };
  assert.equal(resolveRoute(bb, registry, f.c).eligible, true);
  row.bloodbank.enabled = 'true'; assert.equal(resolveRoute(bb, registry, f.c).eligible, false);
  row.bloodbank.enabled = false; assert.equal(resolveRoute(bb, registry, f.c).eligible, false);
  registry.agents['other-pm'] = clone(row);
  assert.throws(() => resolveRoute(bb, registry, f.c), /exactly one/);
});

test('canonical command is schema valid and carries version, memory policy and independent normal pipeline', async t => {
  const f = fixture(t); await f.run();
  const e = f.commands[0]; bb.nats.validateEnvelope(e.type, e);
  assert.equal(e.data.context.contractor_version, '1'); assert.equal(e.data.context.pipeline, 'momo-per-ticket');
  assert.equal(e.data.context.reason, 'ticket-delegation'); assert.equal(e.data.context.origin, 'board_crank_ready_pickup');
  assert.equal(e.data.context.driver_lease, f.c.runtime.driver_lease);
  assert.deepEqual(e.data.context.memory_policy, f.c.contractor.memory_policy);
  assert.match(e.data.prompt, /PM writes no product code/); assert.match(e.data.prompt, /Never self-accept/);
  assert.match(e.data.prompt, /Preserve ALL existing assignees/);
  assert.match(e.data.prompt, /Wait for the control adapter to release it/);
  assert.equal(matchStarted(e, receipts(e, f.route), f.route), true);
});

test('canonical publisher uses official durable client; PubAck is transport-only and exact bytes replay', async t => {
  const f = fixture(t), chosen = rankCandidates(f.board, clock).ranked[0];
  const e = commandFor(bb, f.c, chosen, f.route, clock);
  const sent = []; let closes = 0;
  const fake = { ...bb, transport: { async connect() { return { flush: async () => {}, close: async () => { closes++; } }; } },
    js: { jetstream() { return { async publish(subject, payload, opts) {
      sent.push({ subject, bytes: payload.toString(), opts }); return { stream: 'BLOODBANK_COMMANDS', seq: 23, duplicate: false };
    } }; } } };
  const ack = await publishExact(fake, f.c, e);
  assert.equal(ack.status, 'stored'); assert.equal(closes, 1);
  assert.equal(sent[0].bytes, JSON.stringify(e)); assert.equal(sent[0].opts.msgID, e.command_id);
  assert.equal(sent[0].opts.expect.streamName, 'BLOODBANK_COMMANDS');
  assert.equal(sent[0].subject, bb.nats.subjectFor(e.type, 'command'));
});

test('versioned input/runtime/worker/receipt schemas validate fixture contracts', async t => {
  const f = fixture(t), schema = JSON.parse(readFileSync(join(scripts, '../contracts/board.crank.v1.json')));
  const ajv = new bb.Ajv({ strict: false }); bb.formats(ajv); ajv.addSchema(schema);
  for (const [name, value] of [['input', f.c], ['runtime', f.deployment], ['workers', f.workers], ['receipt', await f.run()]]) {
    const validate = ajv.getSchema(`${schema.$id}#/$defs/${name}`);
    assert.equal(validate(value), true, `${name}: ${JSON.stringify(validate.errors)}`);
  }
});

test('reconciliation needs matching completion AND final Done AND fresh post-completion no-worker truth', async t => {
  for (const absent of ['completion', 'done', 'workers', 'observation-after-terminal']) {
    const f = fixture(t); await f.run(); f.completed = absent !== 'completion';
    if (absent !== 'done') f.board.issues[0].state = 'done';
    if (absent === 'workers') f.workers.active.push({ ticket_id: ticketId(1), status: 'review' });
    if (absent === 'observation-after-terminal') f.workers.observed_at = new Date(clock - 1000).toISOString();
    assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'busy', absent);
    assert.equal(f.journal.load().phase, 'active'); assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 1);
  }
});

test('completed causation, command, target, profile and context mismatches preserve active fence', async t => {
  for (const wrong of ['causation', 'command', 'target', 'profile', 'context', 'failed']) {
    const f = fixture(t); await f.run(); f.completed = true; f.board.issues[0].state = 'done';
    f.alterCompleted = e => {
      if (wrong === 'causation') e.causationid = crypto.randomUUID();
      if (wrong === 'command') e.data.command_id = crypto.randomUUID();
      if (wrong === 'target') e.data.target_agent_id = 'other-pm';
      if (wrong === 'profile') e.data.profile_name = 'other';
      if (wrong === 'context') e.data.context = { ...e.data.context, ticket_id: ticketId(2) };
      if (wrong === 'failed') e.type = 'bloodbank.agent.invocation.failed';
    };
    assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'busy', wrong);
    assert.equal(f.journal.load().phase, 'active'); assert.equal(f.commands.length, 1);
  }
});

test('explicit reconciliation archives proof, then a later hourly pass dispatches exactly one later ticket', async t => {
  const f = fixture(t); await f.run();
  const first = f.journal.load(), originalTicket = clone(f.board.issues[0]);
  f.completed = true; f.board.issues[0].state = 'done';
  assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'reconciled');
  assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 1);
  const retired = f.journal.load(); assert.equal(retired.phase, 'completed');
  assert.ok(matchCompleted(retired, retired.completion.terminal, f.route));
  assert.equal(existsSync(join(f.dir, 'completed', `${first.intent.envelope.command_id}.json`)), true);
  assert.deepEqual(f.board.issues[0], { ...originalTicket, state: 'done' });
  f.ports.journal = new Journal(f.dir, boardId);
  assert.equal((await f.run()).status, 'started'); assert.equal(f.commands.length, 2);
  assert.equal(f.journal.load().ticket_id, ticketId(2));
  assert.notEqual(f.commands[0].command_id, f.commands[1].command_id);
});

test('normal execute reconciles a proven completed fence and advances one later ticket', async t => {
  const f = fixture(t); await f.run(); f.completed = true; f.board.issues[0].state = 'done';
  assert.equal((await f.run()).status, 'started');
  assert.equal(f.commands.length, 2); assert.equal(f.journal.load().ticket_id, ticketId(2));
});

test('inspect cannot retire completion; mutation uncertainty cannot be cleared by completion', async t => {
  const f = fixture(t); await f.run(); f.completed = true; f.board.issues[0].state = 'done';
  assert.equal((await reconcile(f.c, f.ports)).status, 'busy'); assert.equal(f.journal.load().phase, 'active');
  const j = f.journal.load(); j.phase = 'mutation_conflict'; f.journal.save(j);
  assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'busy');
  assert.equal(f.journal.load().phase, 'mutation_conflict'); assert.equal(f.commands.length, 1);
});

test('runtime changes or occupied shared lease prevent completion retirement', async t => {
  const f = fixture(t); await f.run(); f.completed = true; f.board.issues[0].state = 'done';
  writeFileSync(f.c.runtime.driver_lease, JSON.stringify({ owner: 'hermes:other', heartbeat_at: Date.now() / 1000, ttl: 1800 }));
  assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'busy');
  rmSync(f.c.runtime.driver_lease);
  f.workers.observed_at = '2026-10-01T00:00:00Z';
  assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'uncertain');
  assert.equal(f.journal.load().phase, 'active'); assert.equal(f.commands.length, 1);
});

test('completion archive failure fences new dispatch and restart repairs the original evidence', async t => {
  const f = fixture(t); await f.run(); f.completed = true; f.board.issues[0].state = 'done';
  const first = f.journal.load();
  f.journal.archive = () => { throw new Error('fixture storage unavailable'); };
  assert.equal((await f.run()).status, 'uncertain');
  assert.equal(f.commands.length, 1); assert.equal(f.journal.load().phase, 'completed');
  assert.equal((await f.run()).status, 'uncertain'); assert.equal(f.commands.length, 1);
  const restarted = new Journal(f.dir, boardId); f.ports.journal = restarted;
  assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'reconciled');
  const archived = JSON.parse(readFileSync(join(f.dir, 'completed', `${first.intent.envelope.command_id}.json`)));
  assert.deepEqual(archived.intent, first.intent); assert.deepEqual(archived.started, first.started);
  assert.ok(matchCompleted(archived, archived.completion.terminal, f.route));
  assert.equal((await f.run()).status, 'started'); assert.equal(f.commands.length, 2);
});

test('worker activity discovered after terminal lookup preserves the completion fence', async t => {
  const f = fixture(t); await f.run(); f.completed = true; f.board.issues[0].state = 'done';
  const lookup = f.ports.completed;
  f.ports.completed = async (...args) => {
    const terminal = await lookup(...args);
    f.workers.active.push({ ticket_id: ticketId(1), command_id: terminal.data.command_id, status: 'review' });
    return terminal;
  };
  const before = readFileSync(f.journal.path, 'utf8');
  assert.equal((await f.run()).status, 'busy');
  assert.equal(readFileSync(f.journal.path, 'utf8'), before); assert.equal(f.commands.length, 1);
});

async function productionFixture(t, issues, bloodbank) {
  const f = fixture(t, issues);
  const sourceRoot = resolve(scripts, '../..');
  const oldCwd = process.cwd(), oldFetch = globalThis.fetch;
  const keys = ['PILOT_CONFIG_DIR', 'PLANE_API_KEY', 'KREBS_MANIFESTS'];
  const previous = keys.map(k => process.env[k]);
  t.after(() => { process.chdir(oldCwd); globalThis.fetch = oldFetch;
    keys.forEach((k, n) => previous[n] === undefined ? delete process.env[k] : process.env[k] = previous[n]); });
  const state = mkdtempSync(join(tmpdir(), 'board-crank-production-fixture-'));
  t.after(() => rmSync(state, { recursive: true, force: true }));
  f.c.runtime.state_dir = state; f.c.runtime.driver_lease = join(f.dir, 'agents/hermes/pm/runtime/wip-driver.lock');
  f.c.runtime.registry_file = join(state, 'registry.yaml'); f.c.runtime.deployment_receipt = join(state, 'deployed.json');
  f.c.runtime.worker_status_file = join(state, 'workers.json'); f.c.runtime.profile_root = join(state, 'profiles');
  f.c.contractor.skill_root = join(sourceRoot, 'skill'); f.c.contractor.skill_sha256 = skillDigest(f.c.contractor.skill_root);
  Object.assign(f.deployment, { driver_lease: f.c.runtime.driver_lease, skill_sha256: f.c.contractor.skill_sha256,
    state_dir: f.c.runtime.state_dir, worker_status_file: f.c.runtime.worker_status_file });
  mkdirSync(join(f.dir, 'agents/hermes/pm/runtime'), { recursive: true });
  mkdirSync(join(state, 'profiles/test-pm'), { recursive: true });
  writeFileSync(join(state, 'profiles/test-pm/config.yaml'), '{}'); writeFileSync(join(state, 'profiles/test-pm/SOUL.md'), 'Fixture');
  writeFileSync(join(f.dir, '.project.json'), JSON.stringify({ project_id: 'test', ticket_provider: {
    type: 'plane', board_id: boardId, workspace: '33god', identifier: 'TEST' }, agents: { 'test-pm': { role_dir: 'agents/hermes/pm' } } }));
  writeFileSync(f.c.runtime.deployment_receipt, JSON.stringify(f.deployment));
  writeFileSync(f.c.runtime.worker_status_file, JSON.stringify(f.workers));
  const registry = { schema_version: 1, agents: { 'test-pm': { profile_name: 'test-pm', project_path: f.dir,
    plane: { board_id: boardId, workspace: '33god', identifier: 'TEST' },
    bloodbank: { gateway_scope: 'fleet', target_agent_id: 'test-pm' } } } };
  writeFileSync(f.c.runtime.registry_file, JSON.stringify(registry));
  process.env.PILOT_CONFIG_DIR = state; process.env.PLANE_API_KEY = 'fixture';
  process.env.KREBS_MANIFESTS = JSON.stringify([join(f.dir, '.project.json')]); process.chdir(f.dir);
  const calls = [];
  globalThis.fetch = async (url, options) => {
    assert.equal(options.headers['X-API-Key'], 'fixture');
    calls.push({ url: String(url), method: options.method, body: options.body });
    await f.onHTTP?.(String(url), options);
    let value;
    if (options.method === 'PATCH') {
      const body = JSON.parse(options.body); Object.assign(f.board.issues[0], body); value = f.board.issues[0];
    } else if (String(url).endsWith('/states/')) value = f.board.states;
    else if (String(url).endsWith('/issues/')) value = { results: f.board.issues, next: null };
    else if (String(url).endsWith('/labels/')) value = f.board.labels;
    else if (String(url).endsWith('/relations/')) value = f.board.relations[String(url).match(/\/work-items\/([^/]+)/)[1]];
    else if (String(url).endsWith('/cycle-issues/')) value = { results: f.httpMembers ?? [], next: null };
    else if (String(url).endsWith('/cycles/')) value = f.board.cycles ?? [];
    else if (String(url).includes('/issues/')) value = f.board.issues[0];
    else value = { cycle_view: f.board.cycle_view };
    return new Response(JSON.stringify(value), { status: 200 });
  };
  const ports = await loadProductionPorts({ pilotRoot: process.env.PILOT_SOURCE_ROOT,
    bloodbankRoot: process.env.BLOODBANK_SOURCE_ROOT, sourceRoot, bloodbank });
  return { f, ports, calls, state };
}

test('actual Pilot and Bloodbank production boundary uses exported APIs with fixture-only HTTP', async t => {
  const { f, ports, calls, state } = await productionFixture(t);
  const alias = join(f.dir, 'state-alias'); symlinkSync(state, alias);
  const aliased = clone(f.c); aliased.runtime.state_dir = alias;
  await assert.rejects(() => ports.runtime(aliased), /journal directory must be canonical/);
  assert.equal((await ports.runtime(f.c)).route.eligible, true);
  const board = await ports.board(f.c);
  assert.equal(board.issues.length, 2);
  assert.ok(calls.some(c => c.url.includes('/work-items/') && c.url.endsWith('/relations/')));
  await ports.patch(f.c, ticketId(1), { state: 'started', start_date: '2026-10-05' });
  const patch = calls.filter(c => c.method === 'PATCH'); assert.equal(patch.length, 1);
  assert.deepEqual(JSON.parse(patch[0].body), { state: 'started', start_date: '2026-10-05' });
  assert.deepEqual(f.board.issues[0].assignees, ['existing-person']); assert.deepEqual(f.board.issues[0].labels, ['triaged']);
});

test('production hydration carries nonempty native sequencing relations and string/object cycle memberships into selection', async t => {
  const { f, ports } = await productionFixture(t, [ticket(1), ticket(2), ticket(9, { state: 'blocked' })]);
  f.board.relations[ticketId(1)].start_after = [{ project_id: boardId, issue_id: ticketId(9) }];
  f.board.relations[ticketId(2)].finish_after = [{ project_id: boardId, issue_id: ticketId(9) }];
  assert.equal(rankCandidates(await ports.board(f.c), clock).ranked.length, 0);
  f.board.issues[2].state = 'done';
  f.board.cycle_view = true;
  f.board.cycles = [{ id: 'current', start_date: '2026-10-01', end_date: '2026-10-20' }];
  for (const member of [ticketId(2), { issue: ticketId(2) }, { issue: { id: ticketId(2) } }]) {
    f.httpMembers = [member];
    const hydrated = await ports.board(f.c);
    assert.equal(hydrated.relations[ticketId(2)].finish_after[0].issue_id, ticketId(9));
    assert.deepEqual(hydrated.cycle_members.current, [ticketId(2)]);
    assert.equal(rankCandidates(hydrated, clock).ranked[0].ticket_id, ticketId(2));
  }
});

test('production relation hydration bounds concurrency and retains dispatch/readback budget', async t => {
  const { f, ports } = await productionFixture(t, Array.from({ length: 100 }, (_, n) => ticket(n + 1)));
  let active = 0, maximum = 0;
  f.onHTTP = async url => {
    if (!url.endsWith('/relations/')) return;
    maximum = Math.max(maximum, ++active);
    await new Promise(resolve => setTimeout(resolve, 150)); active--;
  };
  const begin = Date.now(), board = await ports.board(f.c);
  assert.equal(Object.keys(board.relations).length, 100);
  assert.ok(maximum > 1 && maximum <= 8, `observed concurrency ${maximum}`);
  assert.ok(Date.now() - begin < 5000);
});

test('production receipt ports use canonical direct-get traversal through dense history to dispatch and reconcile', async t => {
  const history = [], requests = [];
  const append = envelope => history.push({ seq: history.length + 1, subject: bb.nats.subjectFor(envelope.type, 'event'), envelope });
  const connect = async () => ({
    async request(subject, payload) {
      assert.equal(subject, '$JS.API.DIRECT.GET.BLOODBANK_EVENTS');
      const query = JSON.parse(payload); requests.push(query);
      const rows = history.filter(row => row.subject === (query.last_by_subj ?? query.next_by_subj));
      const row = query.last_by_subj ? rows.at(-1) : rows.find(row => row.seq >= query.seq);
      if (!row) return { headers: { code: 404 } };
      return { headers: { get: key => key === 'Nats-Sequence' ? String(row.seq) : key === 'Nats-Subject' ? row.subject : '' },
        data: Buffer.from(JSON.stringify(row.envelope)) };
    }, async close() {},
  });
  const bloodbank = { ...bb, replay: { ...bb.replay,
    withDirectGet: (options, work) => bb.replay.withDirectGet(options, work, connect) } };
  const { f, ports } = await productionFixture(t, [ticket(1)], bloodbank);
  const terminalFixture = f.ports.completed;
  const dense = event => {
    const foreign = clone(event); foreign.data.command_id = crypto.randomUUID();
    for (let n = 0; n < 4200; n++) append(foreign);
    append(event); append(foreign); // the second-newest matching event must be reachable
  };
  f.onPublish = envelope => { for (const event of receipts(envelope, f.route)) dense(event); };
  f.ports.started = ports.started; f.ports.completed = ports.completed;
  assert.equal((await f.run()).status, 'started');
  assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 1);
  f.completed = true; f.board.issues[0].state = 'done';
  dense(await terminalFixture(f.c, f.journal.load(), f.route));
  const before = requests.length;
  assert.equal((await reconcile(f.c, f.ports, { execute: true })).status, 'reconciled');
  assert.ok(requests.length - before < 100);
  assert.ok(requests.some(query => query.next_by_subj));
  assert.equal(f.journal.load().phase, 'completed');
});

test('same-ticket foreign or unidentified workers fence pending replay and post-start writes', async t => {
  for (const command of ['foreign', null, undefined]) {
    const f = fixture(t); f.acknowledge = false; await f.run();
    f.workers.active = [{ ticket_id: ticketId(1), command_id: command }];
    assert.equal((await f.run({ replay: true })).status, 'busy');
    assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 0);
    const post = fixture(t);
    post.onPublish = () => { post.workers.active = [{ ticket_id: ticketId(1), command_id: command }]; };
    assert.equal((await post.run()).status, 'uncertain');
    assert.equal(post.commands.length, 1); assert.equal(post.patches.length, 0);
  }
  const own = fixture(t); own.acknowledge = false; await own.run();
  own.workers.active = [{ ticket_id: ticketId(1), command_id: own.commands[0].command_id }];
  own.acknowledge = true; assert.equal((await own.run()).status, 'started');
  assert.equal(own.commands.length, 1);
});

test('every written prerequisite must match completed native truth, including TEST-10 beside completed TEST-9', async t => {
  const f = fixture(t, [ticket(1), ticket(9, { state: 'done' }), ticket(10, { state: 'blocked' })]);
  f.board.relations[ticketId(1)].blocked_by = [{ project_id: boardId, issue_id: ticketId(9) }];
  const base = f.board.issues[0].description_html;
  f.board.issues[0].description_html += '<h2>Dependencies</h2><p>TEST-9 and TEST-10</p>';
  assert.equal((await f.run()).status, 'idle'); f.zero();
  for (const prose of ['None.', 'No dependencies.', 'Not applicable.']) {
    f.board.issues[0].description_html = base + `<h2>Prerequisites</h2><p>${prose}</p>`;
    assert.equal((await f.run({ execute: false })).status, 'ready', prose);
  }
  f.board.issues[0].description_html = base + '<h2>Dependencies</h2><p>TEST-9 and operator approval</p>';
  assert.equal((await f.run()).status, 'idle');
});

test('start_after and finish_after each independently require completed predecessors', async t => {
  for (const relationship of ['start_after', 'finish_after']) {
    const f = fixture(t, [ticket(1), ticket(9, { state: 'blocked' })]);
    f.board.relations[ticketId(1)][relationship] = [{ project_id: boardId, issue_id: ticketId(9) }];
    assert.equal((await f.run()).status, 'idle', relationship); f.zero();
    f.board.issues[1].state = 'done';
    assert.equal((await f.run()).status, 'started', relationship);
  }
});

test('cycle configuration and every enabled membership must be explicit and trustworthy', async t => {
  for (const cycle of [undefined, null, 'false']) {
    const f = fixture(t); f.board.cycle_view = cycle;
    assert.equal((await f.run()).status, 'refused'); f.zero();
  }
  for (const malformed of ['missing', 'object', 'date']) {
    const f = fixture(t); f.board.cycle_view = true;
    f.board.cycles = [{ id: 'cycle', start_date: '2026-10-01', end_date: '2026-10-20' }];
    f.board.cycle_members = malformed === 'missing' ? {} : { cycle: [ticketId(1)] };
    if (malformed === 'object') f.board.cycle_members.cycle = [{}];
    if (malformed === 'date') f.board.cycles[0].end_date = null;
    assert.equal((await f.run()).status, 'refused'); f.zero();
  }
});

test('downstream credit requires this ticket to resolve all observed remaining blockers', t => {
  const f = fixture(t, [ticket(2), ticket(3), ticket(8, { labels: [] }), ticket(9, { state: 'blocked' })]);
  f.board.relations[ticketId(3)].blocking = [{ project_id: boardId, issue_id: ticketId(8) }];
  f.board.relations[ticketId(8)].blocked_by = [3, 9].map(n => ({ project_id: boardId, issue_id: ticketId(n) }));
  assert.equal(rankCandidates(f.board, clock).ranked.find(r => r.ticket_id === ticketId(3)).rationale.unblocks, 0);
  f.board.issues[3].state = 'done';
  assert.equal(rankCandidates(f.board, clock).ranked.find(r => r.ticket_id === ticketId(3)).rationale.unblocks, 1);
  delete f.board.relations[ticketId(8)];
  assert.equal(rankCandidates(f.board, clock).ranked.find(r => r.ticket_id === ticketId(3)).rationale.unblocks, 0);
});

test('null thin rows do not abort a mixed board; acceptance excludes Notes and includes criteria after prose', async t => {
  const mixed = fixture(t, [ticket(1, { labels: [], description_html: null }), ticket(2)]);
  assert.equal((await mixed.run()).status, 'started'); assert.equal(mixed.journal.load().ticket_id, ticketId(2));
  const empty = fixture(t, [ticket(1, { description_html: '<h2>Acceptance criteria</h2><h2>Notes</h2>' +
    '<ol><li>FR-1: Must preserve a note.</li></ol>' })]);
  assert.equal((await empty.run()).status, 'idle'); empty.zero();
  const f = fixture(t, [ticket(1, { description_html: '<h2>Acceptance criteria</h2>' +
    '<ol><li>FR-1: Must preserve data.</li></ol><p>Additional context.</p>' +
    '<ol><li>Unspecified behavior without requirement coverage.</li></ol>' })]);
  assert.equal((await f.run()).status, 'idle'); f.zero();
  f.board.issues[0].description_html = f.board.issues[0].description_html.replace(
    'Unspecified behavior without requirement coverage.', 'FR-2: Must reject invalid data.');
  assert.equal((await f.run()).status, 'started');
  assert.match(f.commands[0].data.prompt, /FR-2: Must reject invalid data/);
});

test('ticket-only, project and route journal corruption cannot reuse a saved command for recovery', async t => {
  for (const identity of ['ticket', 'project', 'route']) {
    const f = fixture(t); f.acknowledge = false; await f.run();
    const j = f.journal.load();
    if (identity === 'ticket') j.ticket_id = ticketId(2);
    if (identity === 'project') j.project.id = 'other';
    if (identity === 'route') j.route.profileName = 'other-pm';
    writeFileSync(f.journal.path, JSON.stringify(j));
    const bytes = readFileSync(f.journal.path, 'utf8'); f.acknowledge = true;
    assert.equal((await f.run({ replay: true })).status, 'refused');
    assert.equal(readFileSync(f.journal.path, 'utf8'), bytes); assert.equal(f.commands.length, 1); assert.equal(f.patches.length, 0);
  }
});

test('equivalent configuration key reorder recovers the exact original envelope', async t => {
  const f = fixture(t); f.acknowledge = false; await f.run();
  const envelope = JSON.stringify(f.journal.load().intent.envelope);
  const reorder = value => value && typeof value === 'object' && !Array.isArray(value) ?
    Object.fromEntries(Object.entries(value).reverse().map(([key, item]) => [key, reorder(item)])) : value;
  for (const key of ['project', 'runtime', 'contractor']) f.c[key] = reorder(f.c[key]);
  f.acknowledge = true;
  assert.equal((await f.run()).status, 'started'); assert.equal(f.commands.length, 1);
  assert.equal(JSON.stringify(f.journal.load().intent.envelope), envelope);
});

test('changed eligible AC fences saved prompts before publication, replay and post-start claim', async t => {
  for (const phase of ['before-publication', 'pending-replay', 'post-start']) {
    const f = fixture(t); const change = () => { f.board.issues[0].description_html +=
      '<ol><li>FR-27: Must reject additional invalid input.</li></ol>'; };
    if (phase === 'before-publication') f.onBoard = n => { if (n === 3) change(); };
    if (phase === 'post-start') f.onPublish = change;
    if (phase === 'pending-replay') { f.acknowledge = false; await f.run(); change(); }
    assert.equal((await f.run({ replay: true })).status, 'uncertain', phase);
    const original = JSON.stringify(f.journal.load().intent.envelope);
    const commands = f.commands.length;
    assert.equal((await f.run({ replay: true })).status, 'uncertain');
    assert.equal(JSON.stringify(f.journal.load().intent.envelope), original);
    assert.equal(f.commands.length, commands); assert.equal(f.patches.length, 0);
  }
});

test('55-to-65-second hydration cannot use expired worker or deployment truth for publication or claim', async t => {
  for (const phase of ['publication', 'claim']) for (const truth of ['workers', 'deployment']) {
    const f = fixture(t); f.clock += 55000;
    if (truth === 'deployment') {
      f.workers.observed_at = new Date(f.clock).toISOString();
      f.deployment.expires_at = new Date(clock + 60000).toISOString();
    }
    f.onBoard = n => { if (n === (phase === 'publication' ? 3 : 4)) f.clock += 10000; };
    assert.equal((await f.run()).status, 'uncertain', `${phase}/${truth}`);
    assert.equal(f.commands.length, phase === 'publication' ? 0 : 1); assert.equal(f.patches.length, 0);
  }
});

test('receipt renewal cannot relocate a per-board journal binding beside the shared lease', async t => {
  const f = fixture(t); f.acknowledge = false; await f.run();
  const original = readFileSync(f.journal.path, 'utf8');
  const bindingPath = `${f.c.runtime.driver_lease}.board-crank.json`;
  const binding = readFileSync(bindingPath, 'utf8');
  assert.equal(statSync(bindingPath).mode & 0o777, 0o600);
  const renewed = clone(f.c); renewed.runtime.state_dir = join(f.dir, 'renewed'); mkdirSync(renewed.runtime.state_dir);
  f.deployment.state_dir = renewed.runtime.state_dir;
  const second = new Journal(renewed.runtime.state_dir, boardId);
  assert.equal((await crank(renewed, { ...f.ports, journal: second }, { execute: true })).status, 'refused');
  assert.equal(existsSync(second.path), false); assert.equal(readFileSync(f.journal.path, 'utf8'), original);
  assert.equal(readFileSync(bindingPath, 'utf8'), binding); assert.equal(f.commands.length, 1);
});

test('dangling, corrupt or mismatched persistent bindings fail closed without replacement', async t => {
  for (const kind of ['dangling', 'corrupt', 'mismatched']) {
    const f = fixture(t), bindingPath = `${f.c.runtime.driver_lease}.board-crank.json`;
    if (kind === 'dangling') symlinkSync(join(f.dir, 'absent'), bindingPath);
    else writeFileSync(bindingPath, kind === 'corrupt' ? '{invalid' : JSON.stringify({ contract: 'other' }));
    assert.equal((await f.run()).status, 'refused', kind); f.zero();
    assert.equal(f.acquireCalls, 0); assert.equal(existsSync(f.journal.path), false);
    if (kind === 'dangling') assert.ok(lstatSync(bindingPath).isSymbolicLink(), 'dangling binding must survive');
    else assert.equal(readFileSync(bindingPath, 'utf8'), kind === 'corrupt' ? '{invalid' : JSON.stringify({ contract: 'other' }));
  }
});

test('accepted bundle fingerprint includes executable, schema and relative file identity', async t => {
  const f = fixture(t), root = join(f.dir, 'installed');
  cpSync(join(scripts, '..'), root, { recursive: true });
  const accepted = skillDigest(root); f.c.contractor.skill_sha256 = accepted; f.deployment.skill_sha256 = accepted;
  const facts = await f.ports.runtime();
  for (const path of ['scripts/momo-board-crank.mjs', 'contracts/board.crank.v1.json']) {
    const file = join(root, path), before = readFileSync(file);
    writeFileSync(file, Buffer.concat([before, Buffer.from('\n ')]));
    const changed = skillDigest(root); assert.notEqual(changed, accepted);
    assert.throws(() => validateRuntime(f.c, { ...facts, skillSha256: changed }, clock), /contractor source differs/);
    writeFileSync(file, before);
  }
  writeFileSync(join(root, 'scripts/new-file.mjs'), '// identity');
  assert.notEqual(skillDigest(root), accepted);
});
