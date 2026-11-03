import { createHash, randomUUID } from 'node:crypto';
import { existsSync, lstatSync, mkdirSync, openSync, closeSync, fsyncSync,
  readFileSync, realpathSync, renameSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { isDeepStrictEqual } from 'node:util';

export const CONTRACT = 'board.crank.v1';
export const PIPELINE = 'momo-per-ticket';
const PRIORITY = { urgent: 0, high: 1, medium: 2, low: 3, none: 4 };
const TERMINAL = new Set(['completed', 'cancelled']);
const idOf = value => typeof value === 'string' ? value : value?.id;
export const digest = value => createHash('sha256').update(value).digest('hex');
export const canonicalJSON = value => JSON.stringify(value, (_key, item) =>
  item && typeof item === 'object' && !Array.isArray(item) ?
    Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
const configDigest = value => digest(canonicalJSON(value));
export const ticketRevision = ticket => configDigest({ id: ticket.id, name: ticket.name,
  sequence_id: ticket.sequence_id, description_html: ticket.description_html ?? null });
export class ControlRefusal extends Error {}
const require = (condition, reason) => { if (!condition) throw new ControlRefusal(reason); };
const nonblank = value => typeof value === 'string' && value.trim().length > 0;
const absolute = value => nonblank(value) && value.startsWith('/');

export function validateInput(c) {
  require(c?.contract === CONTRACT && c.enabled === true, 'runtime configuration is absent or disabled');
  require(['id', 'workspace', 'board_id'].every(k => nonblank(c.project?.[k])) &&
    absolute(c.project.workdir), 'explicit project binding and workdir required');
  const contractor = c.contractor;
  require(contractor?.name === 'momo' && contractor.mode === 'hermes-profile' &&
    nonblank(contractor.version) && absolute(contractor.skill_root) &&
    /^[a-f0-9]{64}$/.test(contractor.skill_sha256 ?? ''), 'deployed, versioned Hermes Momo contractor required');
  require(nonblank(contractor.memory_policy?.write_bank) &&
    Array.isArray(contractor.memory_policy.recall_banks) &&
    contractor.memory_policy.recall_banks.length > 0 &&
    contractor.memory_policy.recall_banks.every(nonblank), 'explicit memory policy required');
  const roles = ['implementer', 'spec_reviewer', 'quality_reviewer'].map(k => contractor.roles?.[k]);
  require(roles.every(nonblank) && new Set(roles).size === 3, 'implementer and reviewers must be distinct actors');
  require(['state_dir', 'driver_lease', 'worker_status_file', 'registry_file', 'profile_root',
    'deployment_receipt'].every(k => absolute(c.runtime?.[k])), 'explicit shared runtime paths required');
  const server = new URL(c.runtime.nats_server);
  require(['nats:', 'tls:'].includes(server.protocol) && !server.username && !server.password,
    'NATS server must be a hostname endpoint without credentials');
  require(Number.isInteger(c.runtime.ack_timeout_ms) && c.runtime.ack_timeout_ms >= 1000 &&
    c.runtime.ack_timeout_ms <= 10000, 'started acknowledgement budget must be 1000..10000 ms');
  return c;
}

export function validateRuntime(c, facts, now) {
  validateInput(c);
  const { manifest, route, deployment, workers, skillSha256 } = facts;
  const tp = manifest?.ticket_provider;
  require((manifest?.execution?.mode ?? 'legacy') === 'legacy', 'managed/shadow or unknown mode: Krebs owns execution');
  require(tp?.type === 'plane' && tp.board_id === c.project.board_id &&
    tp.workspace === c.project.workspace && manifest.project_id === c.project.id,
  'project manifest no longer matches runtime binding');
  require(route?.eligible === true && route.matchedBy === 'board' &&
    route.workspace === c.project.workspace && route.projectPath === c.project.workdir &&
    nonblank(route.profileName), 'ambiguous, ineligible or mismatched board route');
  require(skillSha256 === c.contractor.skill_sha256, 'contractor source differs from deployment receipt');
  require(deployment?.contract === 'board.crank.runtime.v1' && deployment.accepted === true &&
    deployment.pipeline === PIPELINE && deployment.contractor === c.contractor.name &&
    deployment.version === c.contractor.version && deployment.project_id === c.project.id &&
    deployment.board_id === c.project.board_id && deployment.workdir === c.project.workdir &&
    deployment.profile_name === route.profileName && deployment.driver_lease === c.runtime.driver_lease &&
    deployment.state_dir === c.runtime.state_dir && deployment.worker_status_file === c.runtime.worker_status_file &&
    deployment.skill_sha256 === skillSha256 && deployment.single_driver === true &&
    deployment.gateway_command_journal === true && deployment.independent_reviews === true &&
    deployment.control_lease_handoff === true &&
    isDeepStrictEqual(deployment.memory_policy, c.contractor.memory_policy) &&
    isDeepStrictEqual(deployment.roles, c.contractor.roles) &&
    Object.values(c.contractor.roles).every(actor => actor !== route.agentId) &&
    Date.parse(deployment.expires_at) > now && Date.parse(deployment.verified_at) <= now,
  'missing, expired or mismatched contractor/runtime deployment receipt');
  require(workers?.contract === 'board.crank.workers.v1' && workers.board_id === c.project.board_id &&
    Array.isArray(workers.active) && now - Date.parse(workers.observed_at) >= 0 &&
    now - Date.parse(workers.observed_at) <= 60000,
  'worker status is missing, stale or ambiguous');
  return facts;
}

// Extract text by blocks, preserving enumerated HTML acceptance criteria.
export function descriptionText(html = '') {
  if (typeof html !== 'string') return '';
  return html.replace(/<h[1-6]\b[^>]*>/gi, '\n## ').replace(/<li\b[^>]*>/gi, '\n1. ')
    .replace(/<\/(?:p|div|li|h[1-6])>/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"');
}

function section(html, heading) {
  const lines = descriptionText(html).split('\n');
  const start = lines.findIndex(line => heading.test(line.replace(/^\s*#+\s*/, '').trim()));
  if (start < 0) return null;
  let end = start + 1;
  while (end < lines.length && !/^\s*#+\s+/.test(lines[end]) &&
    !/^\s*(?:Notes|Dependencies|Prerequisites|Business goal|Acceptance criteria)\b[^.!?]*$/i.test(lines[end])) end++;
  return lines.slice(start + 1, end).join('\n');
}

export function acceptance(html) {
  const body = section(html, /^Acceptance criteria\b/i);
  if (body === null) return { ok: false, reason: 'acceptance criteria heading missing' };
  const criteria = [];
  for (const line of body.split('\n')) {
    if (/^\s*(?:\d+[.)]|AC[- ]?\d+[:.])/i.test(line)) criteria.push(line.trim());
  }
  const rubric = {
    non_empty: criteria.length > 0,
    enumerated: criteria.length > 0,
    testable: criteria.length > 0 && criteria.every(s =>
      /\bgiven\b.+\bwhen\b.+\bthen\b|\b(?:returns?|rejects?|preserves?|refuses?|selects?|persists?|must|never|only|exactly|zero|verify|assert)\b/i.test(s)),
    fr_coverage: criteria.length > 0 && criteria.every(s => /\bFR[- ]?\d+\b/i.test(s)),
  };
  return { ok: Object.values(rubric).every(Boolean), rubric, criteria,
    reason: Object.entries(rubric).filter(([, pass]) => !pass).map(([k]) => k).join(', ') };
}

function exactLane(states, name) {
  const rows = states.filter(s => s.name === name);
  require(rows.length === 1, `board requires exactly one ${name} lane`);
  return rows[0].id;
}

export function boardWip(board, workers, execution = null) {
  const ownId = execution?.ticket_id;
  const commandId = execution?.intent?.envelope.command_id;
  const started = exactLane(board.states, 'In Progress');
  const working = new Set(board.labels.filter(l => l.name === 'agent:working').map(l => l.id));
  return workers.active.some(w => !ownId || !commandId || w.ticket_id !== ownId || w.command_id !== commandId) || board.issues.some(i =>
    i.id !== ownId && (idOf(i.state) === started || (i.labels ?? []).some(l => working.has(idOf(l)))));
}

const predecessorsOf = relations => relations && ['blocked_by', 'blocking', 'start_after', 'finish_after']
  .every(key => Array.isArray(relations[key])) ?
  [...relations.blocked_by, ...relations.start_after, ...relations.finish_after] : null;

function writtenReady(ticket, predecessors, board, byId, completed) {
  const body = section(ticket.description_html, /^(?:prerequisites\/dependencies|dependencies|prerequisites)\b/i);
  const inline = descriptionText(ticket.description_html).split('\n')
    .filter(line => /\b(?:blocked by|depends on|waiting on)\b/i.test(line));
  const obligations = [...(body === null ? [] : body.split('\n')), ...inline].map(line =>
    line.replace(/^\s*(?:\d+[.)]|[-*])\s*/, '').trim()).filter(Boolean);
  return obligations.every(line => {
    if (/^(?:none|no (?:dependencies|prerequisites)|not applicable)[.!]?$/i.test(line)) return true;
    const refs = line.match(/\b(?:[A-Z][A-Z0-9]*-\d+|[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})\b/gi) ?? [];
    if (!refs.length) return false;
    let prose = line;
    for (const ref of refs) prose = prose.replace(ref, '');
    prose = prose.replace(/\b(?:blocked by|depends on|waiting on|completion of|must be|requires?|and|or|after|completed?|done)\b/gi, '')
      .replace(/[\s.,:;()[\]/&+-]/g, '');
    if (prose) return false; // a non-ticket requirement cannot be inferred complete
    return refs.every(ref => predecessors.some(r => {
      const dependency = byId.get(r.issue_id);
      return r.project_id === board.id && dependency && completed(dependency.id) &&
        (ref === dependency.id || ref.toUpperCase() === `${board.identifier}-${dependency.sequence_id}`.toUpperCase());
    }));
  });
}

export function rankCandidates(board, now) {
  require(typeof board.cycle_view === 'boolean', 'cycle configuration is unknown');
  if (board.cycle_view) require(Array.isArray(board.cycles) && board.cycle_members &&
    new Set(board.cycles.map(c => c.id)).size === board.cycles.length && board.cycles.every(c =>
      nonblank(c.id) && Number.isFinite(Date.parse(c.start_date)) && Number.isFinite(Date.parse(c.end_date)) &&
      Date.parse(c.start_date) <= Date.parse(c.end_date) && Array.isArray(board.cycle_members[c.id]) &&
      board.cycle_members[c.id].every(nonblank)), 'cycle membership truth unavailable');
  const todo = exactLane(board.states, 'Todo');
  const started = exactLane(board.states, 'In Progress');
  const stateGroups = new Map(board.states.map(s => [s.id, s.group]));
  const labelNames = new Map(board.labels.map(l => [l.id, l.name]));
  const byId = new Map(board.issues.map(i => [i.id, i]));
  const parents = new Set(board.issues.map(i => idOf(i.parent)).filter(Boolean));
  const ranked = [], excluded = [];
  const refuse = (i, reason) => excluded.push({ ticket_id: i.id, reason });
  for (const i of board.issues) {
    if (idOf(i.state) !== todo) { refuse(i, 'outside exact Todo lane'); continue; }
    const labels = (i.labels ?? []).map(l => labelNames.get(idOf(l)) ?? l?.name);
    const rubric = acceptance(i.description_html);
    if (!labels.includes('lifecycle:triaged')) { refuse(i, 'untriaged'); continue; }
    if (labels.some(l => /^(?:lifecycle:(?:blocked|refining|needs-input)|type:epic)$/.test(l ?? '')) ||
      parents.has(i.id) || i.is_epic || i.type?.is_epic) { refuse(i, 'blocked/refining or parent epic'); continue; }
    if (i.is_draft || i.archived_at || i.deleted_at || !nonblank(i.name) || !rubric.ok) {
      refuse(i, `unfortified: ${rubric.reason || 'draft, archived or unnamed'}`); continue;
    }
    const relations = board.relations[i.id];
    if (!relations || !Array.isArray(relations.blocked_by) || !Array.isArray(relations.blocking) ||
      !Array.isArray(relations.start_after) || !Array.isArray(relations.finish_after)) {
      refuse(i, 'dependency truth unavailable'); continue;
    }
    const predecessors = predecessorsOf(relations);
    if (predecessors.some(r => r.project_id !== board.id || !byId.has(r.issue_id) ||
      stateGroups.get(idOf(byId.get(r.issue_id).state)) !== 'completed')) {
      refuse(i, 'unresolved or unknown dependency'); continue;
    }
    // A written dependency that is not a native relation cannot silently disappear.
    const completed = id => stateGroups.get(idOf(byId.get(id)?.state)) === 'completed';
    if (!writtenReady(i, predecessors, board, byId, completed)) {
      refuse(i, 'written dependency unresolved'); continue;
    }
    let cycle = 1;
    if (board.cycle_view) {
      if (!Array.isArray(board.cycles) || !board.cycle_members) { refuse(i, 'cycle truth unavailable'); continue; }
      const active = board.cycles.filter(c => Date.parse(c.start_date) <= now && Date.parse(c.end_date) >= now);
      const assigned = board.cycles.filter(c => (board.cycle_members[c.id] ?? []).includes(i.id));
      if (assigned.some(c => !active.some(a => a.id === c.id))) { refuse(i, 'ineligible cycle'); continue; }
      cycle = assigned.length ? 0 : 1;
    }
    if (!Object.hasOwn(PRIORITY, i.priority) || !Number.isFinite(Date.parse(i.created_at))) {
      refuse(i, 'unknown native priority or age'); continue;
    }
    const critical = relations.blocking.filter(r => {
      const target = byId.get(r.issue_id), remaining = predecessorsOf(board.relations[r.issue_id]);
      const wouldComplete = id => id === i.id || completed(id);
      return r.project_id === board.id && target && !TERMINAL.has(stateGroups.get(idOf(target.state))) &&
        remaining?.some(dep => dep.issue_id === i.id && dep.project_id === board.id) &&
        remaining.every(dep => dep.project_id === board.id && byId.has(dep.issue_id) && wouldComplete(dep.issue_id)) &&
        writtenReady(target, remaining, board, byId, wouldComplete);
    }).length;
    ranked.push({ ticket_id: i.id, ticket: i, criteria: rubric.criteria, rubric: rubric.rubric,
      score: [PRIORITY[i.priority], cycle, -critical, Date.parse(i.created_at), i.id],
      rationale: { priority: i.priority, eligible_cycle: cycle === 0, unblocks: critical,
        dependencies: predecessors.map(r => r.issue_id), created_at: i.created_at } });
  }
  ranked.sort((a, b) => {
    for (let n = 0; n < a.score.length; n++) {
      if (a.score[n] === b.score[n]) continue;
      return a.score[n] < b.score[n] ? -1 : 1;
    }
    return 0;
  });
  return { todo, started, ranked, excluded };
}

export class Journal {
  constructor(directory, boardId) { this.directory = directory; this.path = join(directory, `${boardId}.json`); }
  load() {
    if (!existsSync(this.path)) return null;
    require(!lstatSync(this.path).isSymbolicLink(), 'journal must not be a symlink');
    const j = JSON.parse(readFileSync(this.path, 'utf8'));
    require(j.contract === CONTRACT && j.intent?.envelope && ['uncertain', 'started', 'active', 'completed',
      'mutation_uncertain', 'mutation_conflict'].includes(j.phase), 'journal corrupt: explicit reconciliation required');
    require(digest(JSON.stringify(j.intent.envelope)) === j.intent.sha256, 'saved command body digest mismatch');
    journalIdentity(j);
    require(j.phase !== 'completed' || (matchCompleted(j, j.completion?.terminal, j.route) &&
      Date.parse(j.completion.worker_observed_at) >= Date.parse(j.completion.terminal.time) &&
      j.completion.final_ticket?.id === j.ticket_id && nonblank(j.completion.final_ticket.state)),
    'completed journal lacks matching evidence; explicit reconciliation required');
    return j;
  }
  save(j) {
    this.write(this.path, j);
  }
  archive(j) {
    const path = join(this.directory, 'completed', `${j.intent.envelope.command_id}.json`);
    if (existsSync(path)) {
      require(isDeepStrictEqual(JSON.parse(readFileSync(path, 'utf8')), j), 'completed archive differs from journal');
    } else this.write(path, j);
  }
  write(path, j) {
    const directory = path.slice(0, path.lastIndexOf('/'));
    mkdirSync(directory, { recursive: true, mode: 0o700 });
    const temp = join(directory, `.${randomUUID()}.tmp`);
    const fd = openSync(temp, 'wx', 0o600);
    try { writeFileSync(fd, JSON.stringify(j, null, 2)); fsyncSync(fd); } finally { closeSync(fd); }
    renameSync(temp, path);
    const dir = openSync(directory, 'r');
    try { fsyncSync(dir); } finally { closeSync(dir); }
  }
}

function journalIdentity(j) {
  const context = j.intent.envelope.data?.context;
  require(context?.contract === CONTRACT && context.pipeline === PIPELINE &&
    j.ticket_id === context.ticket_id && j.ticket_content_sha256 === context.ticket_content_sha256 &&
    j.project?.id === context.project_id && j.project.id === context.repo &&
    j.project.workspace === context.workspace && j.project.board_id === context.board_id &&
    j.project.workdir === context.workdir && j.route?.agentId === j.intent.envelope.data.target_agent_id &&
    j.route.profileName === context.profile_name && j.route.workspace === context.workspace &&
    j.route.projectPath === context.workdir, 'journal identity differs from saved command context');
}

// Persistent identity belongs beside the authoritative lease, never in a
// configurable journal directory. Creation is called only while owning that lease.
export function journalBinding(c, create = false) {
  require(realpathSync(c.runtime.state_dir) === c.runtime.state_dir &&
    realpathSync(dirname(c.runtime.driver_lease)) === dirname(c.runtime.driver_lease), 'runtime storage must be canonical');
  const path = `${c.runtime.driver_lease}.board-crank.json`;
  const binding = { contract: 'board.crank.binding.v1', project: c.project,
    driver_lease: c.runtime.driver_lease, state_dir: c.runtime.state_dir };
  const entry = lstatSync(path, { throwIfNoEntry: false });
  if (entry) {
    require(entry.isFile() && !entry.isSymbolicLink(), 'journal binding is not a regular file');
    require(isDeepStrictEqual(JSON.parse(readFileSync(path, 'utf8')), binding), 'persistent journal binding differs; owner reconciliation required');
  } else if (create) new Journal(c.runtime.state_dir, c.project.board_id).write(path, binding);
}

function sameExecution(c, j) {
  require(j.project.id === c.project.id && j.project.workspace === c.project.workspace &&
    j.project.board_id === c.project.board_id && j.project.workdir === c.project.workdir &&
    (j.phase === 'completed' || (j.contractor_digest === configDigest(c.contractor) &&
      j.runtime_digest === configDigest(c.runtime))),
  'pending execution configuration changed; reconcile it explicitly');
}

function gatewayIdentity(envelope, event, route) {
  return event?.kind === 'event' && event.service === 'bloodbank-hermes-gateway' &&
    event.source === 'urn:33god:service:bloodbank-hermes-gateway' &&
    event.correlationid === envelope.correlationid && event.data?.command_id === envelope.command_id &&
    event.data?.target_agent_id === envelope.data.target_agent_id &&
    event.actor?.agent_id === envelope.data.target_agent_id && event.data?.profile_name === route.profileName &&
    event.data?.idempotency_key === envelope.idempotency_key &&
    event.producer === `hermes-agent:${route.profileName}`;
}

function patchConfirmed(ticket, j, inProgress) {
  return idOf(ticket.state) === inProgress && Boolean(ticket.start_date) &&
    (!Object.hasOwn(j.patch.fields, 'start_date') || ticket.start_date === j.patch.fields.start_date);
}

export function matchStarted(envelope, pair, route) {
  const [turn, started] = pair ?? [];
  return Boolean(gatewayIdentity(envelope, turn, route) && gatewayIdentity(envelope, started, route) &&
    nonblank(turn.id) && nonblank(started.id) && nonblank(turn.data.thread_id) && nonblank(turn.data.turn_id) &&
    Date.parse(turn.time) >= Date.parse(envelope.time) && Date.parse(started.time) >= Date.parse(turn.time) &&
    turn.type === 'bloodbank.conversation.turn.started' && turn.causationid === envelope.id &&
    started.type === 'bloodbank.agent.invocation.started' && started.causationid === turn.id &&
    started.data.invocation_id === envelope.command_id && started.data.thread_id === turn.data.thread_id &&
    started.data.turn_id === turn.data.turn_id &&
    isDeepStrictEqual(started.data.context, envelope.data.context));
}

export function matchCompleted(j, event, route) {
  const envelope = j.intent.envelope, started = j.started?.[1];
  return Boolean(matchStarted(envelope, j.started, route) && gatewayIdentity(envelope, event, route) &&
    event.type === 'bloodbank.agent.invocation.completed' && event.causationid === started.id &&
    event.data.invocation_id === envelope.command_id && event.data.thread_id === started.data.thread_id &&
    event.data.turn_id === started.data.turn_id && isDeepStrictEqual(event.data.context, envelope.data.context) &&
    Date.parse(event.time) >= Date.parse(started.time));
}

/** The existing Momo runtime owner reconciles completion. Never retire a fence
 * on TTL, a PM turn's completion alone, an empty worker list alone, or a board
 * claim alone. All three observations must agree after terminal publication.
 */
export async function reconcile(c, ports, { execute = false } = {}) {
  let held = false;
  const owner = `momo:board-crank:reconcile:${randomUUID()}`;
  const result = (status, reason) => ({ contract: CONTRACT, status, reason, live_execution_proof: false });
  try {
    validateInput(c);
    let facts = validateRuntime(c, await ports.runtime(c), ports.now());
    journalBinding(c);
    const journal = ports.journal ?? new Journal(c.runtime.state_dir, c.project.board_id);
    const original = journal.load();
    if (!original) return result('idle', 'no execution fence to reconcile');
    sameExecution(c, original);
    if (!['active', 'completed'].includes(original.phase)) return result('busy', 'uncertain execution or mutation requires explicit investigation');
    if (await ports.leaseBusy(c.runtime.driver_lease)) return result('busy', 'shared driver lease occupied');
    if (!execute) return result('busy', 'inspect only; execution fence is preserved');
    if (!await ports.lease('acquire', c.runtime.driver_lease, owner)) return result('busy', 'shared driver lease occupied');
    held = true;
    journalBinding(c);
    const j = journal.load();
    require(isDeepStrictEqual(j, original), 'journal changed before reconciliation');
    if (j.phase === 'completed') {
      require(matchCompleted(j, j.completion?.terminal, j.route), 'saved completion proof is invalid');
      journal.archive(j); // recover a crash after completion fsync but before archival
      return result('reconciled', 'completion was already durably recorded; archive confirmed');
    }
    facts = validateRuntime(c, await ports.runtime(c), ports.now());
    require(facts.route.agentId === j.route.agentId && facts.route.profileName === j.route.profileName,
      'completion route differs from the dispatched route');
    const terminal = await ports.completed(c, j, facts.route);
    if (!matchCompleted(j, terminal, facts.route)) return result('busy', 'matching completed receipt unavailable; fence preserved');
    // Worker truth must have been observed AFTER terminal publication. Re-read
    // it and provider state after the receipt lookup, under the shared lease.
    facts = validateRuntime(c, await ports.runtime(c), ports.now());
    const board = await ports.board(c);
    const final = await ports.ticket(c, j.ticket_id);
    facts = validateRuntime(c, await ports.runtime(c), ports.now());
    require(board.id === c.project.board_id && final.id === j.ticket_id, 'completion board/ticket identity differs');
    const done = board.states.filter(s => s.name === 'Done' && s.group === 'completed');
    if (done.length !== 1 || idOf(final.state) !== done[0].id || facts.workers.active.length ||
      boardWip(board, facts.workers) || Date.parse(facts.workers.observed_at) < Date.parse(terminal.time)) {
      return result('busy', 'final Done state and post-completion no-worker truth do not agree; fence preserved');
    }
    require(facts.route.agentId === j.route.agentId && facts.route.profileName === j.route.profileName,
      'completion route changed during readback');
    require(await ports.lease('refresh', c.runtime.driver_lease, owner), 'shared driver lease lost');
    j.phase = 'completed';
    j.completion = { terminal, worker_observed_at: facts.workers.observed_at,
      final_ticket: { id: final.id, state: idOf(final.state), updated_at: final.updated_at },
      reconciled_at: new Date(ports.now()).toISOString(), owner };
    journal.save(j); journal.archive(j);
    return result('reconciled', 'matching completion, final Done state and fresh no-worker truth archived; fence retired');
  } catch (error) {
    return result('uncertain', error instanceof ControlRefusal ? error.message :
      `completion observation unavailable (${error.name}); fence preserved`);
  } finally {
    if (held) await ports.lease('release', c.runtime.driver_lease, owner);
  }
}

// Inject provider, registry, bus, clock and lease ports. Only the production ports
// may touch Plane/Bloodbank. Every unresolved journal is a durable WIP fence.
export async function crank(c, ports, { execute = false, replay = false } = {}) {
  let leaseHeld = false, owner = `momo:board-crank:${randomUUID()}`, journal, j, observedFence;
  const answer = (status, reason, extra = {}) => ({ contract: CONTRACT, status, reason,
    live_execution_proof: false, ...extra });
  const save = () => journal.save(j);
  const fresh = async () => validateRuntime(c, await ports.runtime(c), ports.now());
  const refresh = async () => require(await ports.lease('refresh', c.runtime.driver_lease, owner), 'shared driver lease lost');
  try {
    validateInput(c);
    let facts = await fresh();
    journalBinding(c);
    const board = await ports.board(c);
    facts = await fresh();
    require(board.id === c.project.board_id, 'provider board identity mismatch');
    const plan = rankCandidates(board, ports.now());
    journal = ports.journal ?? new Journal(c.runtime.state_dir, c.project.board_id);
    j = journal.load();
    observedFence = j;
    if (j) sameExecution(c, j);
    if (j?.phase === 'completed') j = null;
    if (await ports.leaseBusy(c.runtime.driver_lease) || boardWip(board, facts.workers, j) ||
      (!j && facts.workers.active.length)) return answer('busy', 'shared driver lease or implementation WIP occupied');
    if (j?.phase === 'active' && execute) {
      const completion = await reconcile(c, ports, { execute: true });
      if (completion.status === 'reconciled') return crank(c, ports, { execute, replay });
      return completion;
    }
    if (j && ['active', 'mutation_conflict'].includes(j.phase)) {
      return answer('busy', `durable execution ${j.phase}; pipeline reconciliation required`, { ticket_id: j.ticket_id });
    }
    const selection = j ? plan.ranked.find(r => r.ticket_id === j.ticket_id) : plan.ranked[0];
    if (!j && !selection) return answer('idle', 'no evidenced ready Todo candidate', { excluded: plan.excluded });
    if (!execute) return answer(j ? 'pending' : 'ready', j ? 'durable execution pending' : 'inspect only', {
      selected: selection?.ticket_id ?? j.ticket_id, ranked: plan.ranked.map(({ ticket, criteria, ...r }) => r), excluded: plan.excluded });
    if (!await ports.lease('acquire', c.runtime.driver_lease, owner)) return answer('busy', 'shared driver lease acquisition refused');
    leaseHeld = true;
    journalBinding(c);
    // A contender may have observed null before another driver saved an intent
    // and released its lease. Only THIS read under the acquired lease decides
    // whether a command may be created. Never overwrite that intervening fence.
    j = journal.load();
    observedFence = j ?? observedFence;
    if (j) sameExecution(c, j);
    if (j?.phase === 'active') {
      await ports.lease('release', c.runtime.driver_lease, owner);
      leaseHeld = false;
      const completion = await reconcile(c, ports, { execute: true });
      if (completion.status === 'reconciled') return crank(c, ports, { execute, replay });
      return completion;
    }
    if (j?.phase === 'mutation_conflict') {
      return answer('busy', 'durable execution mutation_conflict; pipeline reconciliation required', { ticket_id: j.ticket_id });
    }
    if (j?.phase === 'completed') { journal.archive(j); j = null; }
    // Re-read all mutable prerequisites after acquisition, and again before publication.
    let current = await fresh();
    let latest = await ports.board(c);
    current = await fresh(); await refresh();
    require(!boardWip(latest, current.workers, j), 'implementation WIP changed after acquisition');
    let currentPlan = rankCandidates(latest, ports.now());
    let chosen = j ? currentPlan.ranked.find(r => r.ticket_id === j.ticket_id) : currentPlan.ranked[0];
    if (!j && !chosen) return answer('idle', 'readiness changed after acquisition', { excluded: currentPlan.excluded });
    if (!j) {
      journalBinding(c, true);
      const intent = await ports.command(c, chosen, current.route);
      j = { contract: CONTRACT, phase: 'uncertain', project: c.project,
        contractor_digest: configDigest(c.contractor), ticket_id: chosen.ticket_id,
        runtime_digest: configDigest(c.runtime), ticket_content_sha256: ticketRevision(chosen.ticket),
        selected: { score: chosen.score, rationale: chosen.rationale, rubric: chosen.rubric },
        ranking: currentPlan.ranked.map(({ ticket, criteria, ...r }) => r), exclusions: currentPlan.excluded,
        intent: { envelope: intent, sha256: digest(JSON.stringify(intent)) },
        route: current.route, receipts: [], patch: null, created_at: new Date(ports.now()).toISOString() };
      save(); // fsync the exact command BEFORE any transport call.
    }
    require(current.route.agentId === j.route.agentId && current.route.profileName === j.route.profileName,
      'pending command route changed');
    let pair = j.started ?? await ports.started(c, j.intent.envelope, current.route);
    let matched = matchStarted(j.intent.envelope, pair, current.route);
    if (!matched) {
      if (j.publications && !replay) return answer('uncertain', 'no matching started receipt; use --replay to send the saved command', { ticket_id: j.ticket_id });
      require(chosen, 'pending ticket is no longer ready; refusing replay');
      await refresh();
      current = await fresh();
      latest = await ports.board(c);
      currentPlan = rankCandidates(latest, ports.now());
      const prompted = await ports.ticket(c, j.ticket_id);
      require(ticketRevision(prompted) === j.ticket_content_sha256, 'prompted ticket content changed; exact intent remains fenced');
      current = await fresh(); await refresh();
      require(!boardWip(latest, current.workers, j) && currentPlan.ranked.some(r => r.ticket_id === j.ticket_id),
        'board WIP/readiness changed before publication');
      require(current.route.agentId === j.route.agentId && current.route.profileName === j.route.profileName,
        'route changed before publication');
      j.publications = (j.publications ?? 0) + 1;
      save();
      try {
        const puback = await ports.publish(c, j.intent.envelope);
        j.receipts.push({ kind: 'transport', ...puback });
        save();
      } catch {
        j.receipts.push({ kind: 'transport', status: 'uncertain' }); save();
        return answer('uncertain', 'dispatch failed or timed out; exact durable intent retained', { ticket_id: j.ticket_id });
      }
      pair = await ports.started(c, j.intent.envelope, current.route, true);
      matched = matchStarted(j.intent.envelope, pair, current.route);
    }
    if (!matched) return answer('uncertain', 'transport acknowledgement is not a matching started receipt', { ticket_id: j.ticket_id });
    j.started = pair;
    j.phase = 'started'; save();
    await refresh();
    // The state/date write is guarded by fresh binding, lane, WIP and ticket reads.
    current = await fresh();
    latest = await ports.board(c);
    current = await fresh(); await refresh();
    require(current.route.agentId === j.route.agentId && current.route.profileName === j.route.profileName,
      'route changed after started acknowledgement');
    require(!boardWip(latest, current.workers, j), 'another implementation appeared after started receipt');
    const inProgress = exactLane(latest.states, 'In Progress');
    const todo = exactLane(latest.states, 'Todo');
    let ticket = await ports.ticket(c, j.ticket_id);
    require(ticket.id === j.ticket_id, 'ticket readback identity mismatch');
    require(ticketRevision(ticket) === j.ticket_content_sha256, 'prompted ticket content changed after start; claim remains fenced');
    if (j.patch) {
      // An ambiguous write is NEVER replayed. Inspect what is stored and leave
      // human changes intact. A missing part needs explicit reconciliation.
      const complete = patchConfirmed(ticket, j, inProgress);
      j.phase = complete ? 'active' : 'mutation_conflict';
      j.receipts.push({ kind: 'readback', state: idOf(ticket.state), start_date: ticket.start_date ?? null,
        status: complete ? 'confirmed' : 'partial_or_changed' }); save();
      return answer(complete ? 'started' : 'uncertain', complete ? 'started and provider readback confirmed' :
        'partial/ambiguous write; no automatic overwrite or compensation', { ticket_id: j.ticket_id });
    }
    if (![todo, inProgress].includes(idOf(ticket.state))) {
      j.phase = 'mutation_conflict'; save();
      return answer('uncertain', 'ticket moved by another actor after dispatch; preserved', { ticket_id: j.ticket_id });
    }
    if (idOf(ticket.state) === todo && !rankCandidates({ ...latest,
      issues: latest.issues.map(i => i.id === ticket.id ? ticket : i) }, ports.now()).ranked.some(r => r.ticket_id === ticket.id)) {
      j.phase = 'mutation_conflict'; save();
      return answer('uncertain', 'ticket readiness changed after dispatch; preserved', { ticket_id: j.ticket_id });
    }
    const fields = {};
    if (idOf(ticket.state) !== inProgress) fields.state = inProgress;
    if (!ticket.start_date) fields.start_date = new Date(ports.now()).toISOString().slice(0, 10);
    j.patch = { before: { state: idOf(ticket.state), start_date: ticket.start_date ?? null,
      updated_at: ticket.updated_at }, fields };
    j.phase = 'mutation_uncertain'; save(); // crash between PATCH and readback remains recoverable
    if (Object.keys(fields).length) {
      await refresh();
      const immediate = await ports.ticket(c, ticket.id);
      if (immediate.id !== ticket.id || immediate.updated_at !== ticket.updated_at ||
        idOf(immediate.state) !== idOf(ticket.state) || (immediate.start_date ?? null) !== (ticket.start_date ?? null) ||
        ticketRevision(immediate) !== j.ticket_content_sha256) {
        j.phase = 'mutation_conflict';
        j.receipts.push({ kind: 'mutation', status: 'concurrent_change_preserved' }); save();
        return answer('uncertain', 'ticket changed immediately before PATCH; preserved', { ticket_id: j.ticket_id });
      }
      current = await fresh(); await refresh();
      require(current.route.agentId === j.route.agentId && current.route.profileName === j.route.profileName &&
        !boardWip(latest, current.workers, j), 'execution eligibility changed immediately before PATCH');
      try { await ports.patch(c, ticket.id, fields); }
      catch { j.receipts.push({ kind: 'mutation', status: 'uncertain' }); save(); }
    }
    try { ticket = await ports.ticket(c, ticket.id); }
    catch { return answer('uncertain', 'provider readback unavailable; do not replay mutation', { ticket_id: j.ticket_id }); }
    require(ticket.id === j.ticket_id, 'ticket readback identity mismatch');
    const complete = patchConfirmed(ticket, j, inProgress);
    j.phase = complete ? 'active' : 'mutation_conflict';
    j.receipts.push({ kind: 'readback', state: idOf(ticket.state), start_date: ticket.start_date ?? null,
      status: complete ? 'confirmed' : 'partial_or_changed' }); save();
    return answer(complete ? 'started' : 'uncertain', complete ? 'matching started receipt and provider readback confirmed' :
      'partial mutation retained for reconciliation', { ticket_id: j.ticket_id,
      command_id: j.intent.envelope.command_id });
  } catch (error) {
    // Never persist provider diagnostics: they may contain credentials or ticket content.
    const fence = j ?? observedFence;
    return answer(fence ? 'uncertain' : 'refused', error instanceof ControlRefusal ? error.message :
      `prerequisite/provider operation unavailable (${error.name})`, fence ? { ticket_id: fence.ticket_id } : {});
  } finally {
    if (leaseHeld) await ports.lease('release', c.runtime.driver_lease, owner);
  }
}
