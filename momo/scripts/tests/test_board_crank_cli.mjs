import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import { Journal, canonicalJSON, digest, ticketRevision } from '../lib/board_crank.mjs';
import { loadBloodbank, commandFor, skillDigest } from '../lib/board_crank_ports.mjs';

const sourceRoot = resolve(fileURLToPath(new URL('../../..', import.meta.url)));
const cli = join(sourceRoot, 'skill/scripts/momo-board-crank.mjs');
const bb = loadBloodbank(process.env.BLOODBANK_SOURCE_ROOT);
const boardId = '15258893-0206-4e8f-aea6-340eb217988c';
const issueId = n => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`;

function fixture(t, { active = false, large = false } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'board-crank-cli-fixture-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const repo = join(dir, 'repo'), state = join(dir, 'state');
  const leaseDir = join(repo, 'agents/hermes/pm/runtime');
  for (const path of [leaseDir, state, join(state, 'profiles/test-pm'), join(dir, 'bin')]) mkdirSync(path, { recursive: true });
  const now = Date.now();
  const c = { contract: 'board.crank.v1', enabled: true,
    project: { id: 'test', workspace: '33god', board_id: boardId, workdir: repo },
    contractor: { name: 'momo', version: '1', mode: 'hermes-profile', skill_root: join(sourceRoot, 'skill'),
      skill_sha256: skillDigest(join(sourceRoot, 'skill')), memory_policy: { write_bank: 'test', recall_banks: ['test'] },
      roles: { implementer: 'worker', spec_reviewer: 'spec-reviewer', quality_reviewer: 'quality-reviewer' } },
    runtime: { state_dir: state, driver_lease: join(leaseDir, 'wip-driver.lock'), registry_file: join(state, 'registry.yaml'),
      worker_status_file: join(state, 'workers.json'), deployment_receipt: join(state, 'deployed.json'),
      profile_root: join(state, 'profiles'), nats_server: 'nats://fixture.invalid:4222', ack_timeout_ms: 1000 } };
  const issue = { id: issueId(1), name: 'Fixture work', sequence_id: 1, state: active ? 'started' : 'todo',
    priority: 'high', labels: ['triaged'], assignees: ['fixture-person'], start_date: active ? '2026-10-05' : null,
    created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-02T00:00:00Z', parent: null,
    description_html: '<h2>Acceptance criteria</h2><ol><li>FR-25: Must preserve existing data.</li></ol>' };
  const board = { cycle_view: false,
    states: [{ id: 'todo', name: 'Todo', group: 'unstarted' }, { id: 'started', name: 'In Progress', group: 'started' },
      { id: 'done', name: 'Done', group: 'completed' }, { id: 'backlog', name: 'Backlog', group: 'backlog' }],
    labels: [{ id: 'triaged', name: 'lifecycle:triaged' }], issues: [issue] };
  if (large) board.issues.push(...Array.from({ length: 1400 }, (_, n) => ({ ...issue, id: issueId(n + 2), state: 'backlog' })));
  writeFileSync(join(repo, '.project.json'), JSON.stringify({ project_id: 'test', ticket_provider: {
    type: 'plane', board_id: boardId, workspace: '33god', identifier: 'TEST' }, agents: { 'test-pm': { role_dir: 'agents/hermes/pm' } } }));
  writeFileSync(c.runtime.registry_file, JSON.stringify({ schema_version: 1, agents: { 'test-pm': {
    profile_name: 'test-pm', project_path: repo, plane: { board_id: boardId, workspace: '33god', identifier: 'TEST' },
    bloodbank: { gateway_scope: 'fleet', target_agent_id: 'test-pm' } } } }));
  writeFileSync(join(state, 'profiles/test-pm/config.yaml'), '{}');
  writeFileSync(join(state, 'profiles/test-pm/SOUL.md'), 'Fixture profile');
  writeFileSync(c.runtime.deployment_receipt, JSON.stringify({ contract: 'board.crank.runtime.v1', accepted: true,
    pipeline: 'momo-per-ticket', contractor: 'momo', version: '1', project_id: 'test', board_id: boardId, workdir: repo,
    profile_name: 'test-pm', driver_lease: c.runtime.driver_lease, state_dir: state,
    worker_status_file: c.runtime.worker_status_file, skill_sha256: c.contractor.skill_sha256,
    memory_policy: c.contractor.memory_policy, roles: c.contractor.roles,
    single_driver: true, gateway_command_journal: true, independent_reviews: true, control_lease_handoff: true,
    verified_at: new Date(now - 60000).toISOString(), expires_at: new Date(now + 3600000).toISOString() }));
  writeFileSync(c.runtime.worker_status_file, JSON.stringify({ contract: 'board.crank.workers.v1', board_id: boardId,
    observed_at: new Date(now).toISOString(), active: [] }));
  const configPath = join(state, 'input.json'), boardPath = join(dir, 'board.json');
  writeFileSync(configPath, JSON.stringify(c)); writeFileSync(boardPath, JSON.stringify(board));
  writeFileSync(join(state, 'config.json'), JSON.stringify({ base: 'https://plane.fixture.invalid', apiKey: 'op://Fixture/Plane/credential' }));
  const audit = join(dir, 'audit.jsonl'), hook = join(dir, 'fixture-hook.mjs');
  // Imported by both the supervisor and fork. All HTTP is served here; broker
  // connections and lease mutations fail before they could escape the fixture.
  writeFileSync(hook, `
import { readFileSync, appendFileSync } from 'node:fs';
import net from 'node:net';
import childProcess from 'node:child_process';
import { syncBuiltinESMExports } from 'node:module';
const audit = value => appendFileSync(process.env.BOARD_FIXTURE_AUDIT, JSON.stringify(value) + '\\n');
const execFileSync = childProcess.execFileSync;
childProcess.execFileSync = (file, args, ...rest) => {
  if (args?.some(arg => String(arg).endsWith('momo-wip-lock.py'))) {
    audit({ kind: 'lease', operation: args[1] }); throw new Error('fixture lease mutation refused');
  }
  return execFileSync(file, args, ...rest);
};
net.Socket.prototype.connect = function () { audit({ kind: 'broker' }); throw new Error('fixture network refused'); };
syncBuiltinESMExports();
globalThis.fetch = async (url, options = {}) => {
  audit({ kind: 'http', method: options.method });
  if (options.method !== 'GET' || new URL(url).hostname !== 'plane.fixture.invalid') throw new Error('fixture provider mutation refused');
  const board = JSON.parse(readFileSync(process.env.BOARD_FIXTURE_BOARD));
  let data;
  if (String(url).endsWith('/states/')) data = board.states;
  else if (String(url).endsWith('/issues/')) data = { results: board.issues, next: null };
  else if (String(url).endsWith('/labels/')) data = board.labels;
  else if (String(url).endsWith('/relations/')) data = { blocked_by: [], blocking: [], start_after: [], finish_after: [] };
  else if (String(url).includes('/issues/')) data = board.issues[0];
  else data = { cycle_view: board.cycle_view };
  return new Response(JSON.stringify(data), { status: 200 });
};
`);
  const env = { PATH: `${join(dir, 'bin')}:/usr/bin:/bin`, HOME: dir, XDG_CONFIG_HOME: join(dir, 'config'),
    PILOT_CONFIG_DIR: state, PLANE_API_KEY: 'fixture', KREBS_MANIFESTS: JSON.stringify([join(repo, '.project.json')]),
    BOARD_FIXTURE_BOARD: boardPath, BOARD_FIXTURE_AUDIT: audit };
  const journal = new Journal(state, boardId);
  const seed = phase => {
    const route = { agentId: 'test-pm', profileName: 'test-pm', workspace: '33god', identifier: 'TEST', projectPath: repo };
    const envelope = commandFor(bb, c, { ticket_id: issue.id, ticket: issue,
      criteria: ['1. FR-25: Must preserve existing data.'] }, route, now);
    journal.save({ contract: 'board.crank.v1', phase, project: c.project, route, ticket_id: issue.id,
      ticket_content_sha256: ticketRevision(issue), contractor_digest: digest(canonicalJSON(c.contractor)),
      runtime_digest: digest(canonicalJSON(c.runtime)), intent: { envelope, sha256: digest(JSON.stringify(envelope)) }, receipts: [] });
    writeFileSync(`${c.runtime.driver_lease}.board-crank.json`, JSON.stringify({ contract: 'board.crank.binding.v1',
      project: c.project, driver_lease: c.runtime.driver_lease, state_dir: state }));
  };
  return { dir, repo, state, c, configPath, hook, env, audit, journal, seed, boardPath };
}

function storageSnapshot(...roots) {
  const files = {};
  const walk = path => {
    for (const entry of readdirSync(path, { withFileTypes: true })) {
      const file = join(path, entry.name);
      if (entry.isDirectory()) walk(file);
      else files[file] = { content: readFileSync(file).toString('base64'), mtime: statSync(file).mtimeMs };
    }
  };
  roots.forEach(walk); return files;
}

async function run(f, args, env = {}) {
  const child = spawn(process.execPath, ['--import', f.hook, cli, ...args, '--config', f.configPath,
    '--pilot-root', process.env.PILOT_SOURCE_ROOT, '--bloodbank-root', process.env.BLOODBANK_SOURCE_ROOT],
  { cwd: f.repo, env: { ...f.env, ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  let stdout = '', stderr = '';
  child.stdout.on('data', bytes => { stdout += bytes.toString(); });
  child.stderr.on('data', bytes => { stderr += bytes.toString(); });
  const code = await new Promise((resolve, reject) => { child.on('error', reject); child.on('close', resolve); });
  return { code, stdout, stderr, result: JSON.parse(stdout) };
}

for (const args of [['inspect'], ['execute', '--dry-run'], ['reconcile', '--dry-run']]) {
  test(`public ${args.join(' ')} leaves lease, binding, journal, broker and provider unwritten`, async t => {
    for (const saved of [false, true]) {
      const f = fixture(t, { active: saved });
      if (saved) f.seed('active');
      const before = storageSnapshot(f.repo, f.state);
      const r = await run(f, args);
      assert.equal(r.code, 0, r.stdout); assert.equal(r.stderr, '');
      assert.equal(r.result.live_execution_proof, false);
      assert.equal(r.result.status, saved ? 'busy' : args[0] === 'reconcile' ? 'idle' : 'ready');
      assert.deepEqual(storageSnapshot(f.repo, f.state), before);
      const events = existsSync(f.audit) ? readFileSync(f.audit, 'utf8').trim().split('\n').map(JSON.parse) : [];
      assert.ok(events.every(event => event.kind === 'http' && event.method === 'GET'), JSON.stringify(events));
      if (args[0] !== 'reconcile') assert.ok(events.length > 0, 'actual Pilot reads must run');
    }
  });
}

test('successful supervisor output drains completely before parsing a large JSON receipt', async t => {
  const f = fixture(t, { large: true });
  const r = await run(f, ['inspect']);
  assert.equal(r.code, 0, r.stdout); assert.equal(r.result.status, 'ready');
  assert.ok(Buffer.byteLength(r.stdout) > 65536, 'receipt must exceed a pipe buffer');
  assert.equal(r.result.excluded.length, 1400); assert.equal(r.stderr, '');
});

test('external watchdog terminates a real stalled Pilot op process group and preserves fsynced intent', async t => {
  const f = fixture(t); f.seed('uncertain');
  const pids = join(f.dir, 'op-pids'), op = join(f.dir, 'bin/op');
  writeFileSync(op, `#!/usr/bin/python3
import os, signal, sys
child = os.fork()
if child == 0:
    signal.pause()
else:
    with open(os.environ['BOARD_FIXTURE_PIDS'], 'w') as output:
        output.write(str(os.getpid()) + '\\n' + str(child))
    sys.stderr.write('fixture-private-diagnostic\\n')
    sys.stderr.flush()
    signal.pause()
`, { mode: 0o755 });
  const before = storageSnapshot(f.repo, f.state), started = Date.now();
  const r = await run(f, ['execute', '--replay'], { PLANE_API_KEY: '', BOARD_FIXTURE_PIDS: pids,
    MOMO_BOARD_CRANK_BUDGET_MS: '1500' });
  assert.equal(r.code, 124, r.stdout); assert.equal(r.result.status, 'uncertain');
  assert.match(r.result.reason, /wall-clock budget exhausted; durable intent preserved/);
  assert.equal(r.result.live_execution_proof, false); assert.equal(r.stderr, '');
  assert.doesNotMatch(r.stdout, /fixture-private-diagnostic|op:\/\/|credential/);
  assert.ok(Date.now() - started < 5000); assert.ok(existsSync(pids), 'Pilot must actually enter stalled op');
  const alive = pid => {
    try { return !/^State:\s+Z/m.test(readFileSync(`/proc/${pid}/status`, 'utf8')); }
    catch { return false; }
  };
  const descendants = readFileSync(pids, 'utf8').trim().split('\n').map(Number);
  t.after(() => { for (const pid of descendants) if (alive(pid)) { try { process.kill(pid, 'SIGKILL'); } catch {} } });
  for (let n = 0; n < 20 && descendants.some(alive); n++) await sleep(25);
  assert.ok(descendants.every(pid => !alive(pid)), 'whole op process group must be terminated');
  assert.deepEqual(storageSnapshot(f.repo, f.state), before);
  assert.equal(f.journal.load().phase, 'uncertain');
});
