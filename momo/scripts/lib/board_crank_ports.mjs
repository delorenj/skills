import { createRequire } from 'node:module';
import { readFileSync, readdirSync, realpathSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import { CONTRACT, PIPELINE, ControlRefusal, canonicalJSON, digest, ticketRevision, matchStarted, matchCompleted } from './board_crank.mjs';

const read = path => JSON.parse(readFileSync(path, 'utf8'));
const assert = (ok, message) => { if (!ok) throw new ControlRefusal(message); };
const within = (path, root) => path === root || path.startsWith(root + '/');

export function loadBloodbank(root) {
  const library = join(root, 'integrations/n8n-nodes-bloodbank');
  const require = createRequire(join(library, 'package.json'));
  return { nats: require(join(library, 'dist/nats.js')),
    fleet: require(join(library, 'dist/fleet.js')),
    registry: require(join(library, 'dist/registry.js')),
    replay: require(join(library, 'dist/jetstream.js')),
    transport: require('@nats-io/transport-node'), js: require('@nats-io/jetstream'),
    Ajv: require('ajv/dist/2020').default, formats: require('ajv-formats').default };
}

export function skillDigest(root) {
  const files = [];
  const walk = path => {
    for (const entry of readdirSync(join(root, path), { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      if (['tests', '__pycache__'].includes(entry.name)) continue;
      const name = `${path}/${entry.name}`;
      assert(!entry.isSymbolicLink(), 'installed bundle contains a symlink');
      if (entry.isDirectory()) walk(name);
      else { assert(entry.isFile(), 'installed bundle contains a non-file'); files.push(name); }
    }
  };
  for (const path of ['references', 'scripts', 'contracts']) walk(path);
  files.push('SKILL.md');
  return digest(canonicalJSON(files.sort().map(path => [path, digest(readFileSync(join(root, path)))])));
}

export function resolveRoute(bb, registry, c) {
  assert(registry?.schema_version === 1 && registry.agents && !Array.isArray(registry.agents), 'registry schema invalid');
  const matches = Object.entries(registry.agents).filter(([, row]) =>
    [row?.plane?.board_id, row?.plane?.project_id].includes(c.project.board_id));
  assert(matches.length === 1, 'board must have exactly one registry route');
  // Eligibility stays owned by Bloodbank, including strict boolean activation.
  return bb.fleet.resolveFleetAgentForBoard(registry, c.project.board_id, c.project.id);
}

export function commandFor(bb, c, chosen, route, now = Date.now()) {
  const commandId = crypto.randomUUID();
  const facts = { repo: c.project.id, boardId: c.project.board_id, workspace: c.project.workspace,
    ticketId: chosen.ticket_id, ticketKey: `${route.identifier}-${chosen.ticket.sequence_id}`,
    title: chosen.ticket.name, phase: 'ready', previousPhase: '', providerEventType: 'current_board_truth', url: '' };
  const context = { contract: CONTRACT, reason: 'ticket-delegation', origin: 'board_crank_ready_pickup', pipeline: PIPELINE,
    contractor: c.contractor.name, contractor_version: c.contractor.version,
    project_id: c.project.id, repo: c.project.id, workspace: c.project.workspace,
    board_id: c.project.board_id, ticket_id: chosen.ticket_id, ticket_key: facts.ticketKey,
    workdir: c.project.workdir, memory_policy: c.contractor.memory_policy, roles: c.contractor.roles,
    driver_lease: c.runtime.driver_lease, profile_name: route.profileName,
    ticket_content_sha256: ticketRevision(chosen.ticket) };
  const prompt = bb.fleet.delegationPrompt(facts, c.project.workdir) + '\n\n' +
    'BOARD.CRANK INVOCATION OVERRIDES for this existing ticket:\n' +
    `Contractor ${c.contractor.name}, version ${c.contractor.version}, pipeline ${PIPELINE}.\n` +
    `Read ${join(c.contractor.skill_root, 'SKILL.md')} and its delegation and board-clearing-loop references.\n` +
    'Run the existing Momo per-ticket implementation, spec compliance and quality review pipeline.\n' +
    'Delegate exactly one implementer; the PM writes no product code. Spec and quality reviewers are fresh,\n' +
    'distinct actors from the implementer and each other. Never self-accept work. Do not select another ticket.\n' +
    'The control adapter owns the initial In Progress/start-date write after the gateway started receipt.\n' +
    'Preserve ALL existing assignees, start date, labels and unrelated content; the earlier empty-assignee\n' +
    'instruction does not apply to this invocation.\n' +
    `Shared driver lease: ${c.runtime.driver_lease}. Wait for the control adapter to release it, then\n` +
    'acquire it with a unique PM owner before driving implementation or review. Never steal a fresh lease.\n' +
    `Explicit memory policy: ${JSON.stringify(c.contractor.memory_policy)}.\n` +
    `Distinct delegation roles: ${JSON.stringify(c.contractor.roles)}.\n` +
    `Ticket acceptance criteria, verbatim:\n${chosen.criteria.join('\n')}\n`;
  const opts = { type: 'bloodbank.agent.invocation.start', kind: 'command', data: { target_agent_id: route.agentId,
    prompt, context, thread_id: null, turn_id: null }, commandId, eventId: commandId,
    observedAt: new Date(now).toISOString(), correlationId: bb.fleet.ticketCorrelationId(c.project.board_id, facts.ticketKey),
    source: 'urn:33god:agent:momo', producer: 'momo', service: 'momo-board-crank',
    actor: { type: 'agent_cli', agent_id: 'momo', cli: 'momo' }, validate: true };
  const { envelope } = bb.nats.buildEnvelope(opts);
  bb.nats.validateEnvelope(opts.type, envelope);
  return envelope;
}

/** Adapt the canonical Bloodbank publisher's connection seam to its installed
 * official JetStream library. The normal core publisher waits only for PONG;
 * this connection's flush waits for PubAck before reporting transport storage.
 * Neither acknowledgement is execution acceptance.
 */
export async function publishExact(bb, c, envelope) {
  bb.nats.validateEnvelope(envelope.type, envelope);
  const opts = { type: envelope.type, kind: 'command', data: envelope.data, eventId: envelope.id,
    commandId: envelope.command_id, idempotencyKey: envelope.idempotency_key, observedAt: envelope.time,
    correlationId: envelope.correlationid, causationId: envelope.causationid, source: envelope.source,
    producer: envelope.producer, service: envelope.service, actor: envelope.actor, validate: true,
    host: c.runtime.nats_server, timeoutMs: 3000 };
  assert(JSON.stringify(bb.nats.buildEnvelope(opts).envelope) === JSON.stringify(envelope),
    'canonical publisher would change the saved command');
  let puback;
  await bb.nats.publish(opts, async options => {
    const connection = await bb.transport.connect(options);
    const js = bb.js.jetstream(connection);
    let publication;
    return {
      publish(subject, payload, options) {
        publication = js.publish(subject, payload, { msgID: options.headers.get('Nats-Msg-Id'),
          expect: { streamName: 'BLOODBANK_COMMANDS' }, timeout: 3000 });
      },
      async flush() { puback = await publication; await connection.flush(); },
      async drain() { await connection.close(); },
    };
  });
  assert(puback?.stream === 'BLOODBANK_COMMANDS' && Number.isInteger(puback.seq) && puback.seq > 0,
    'no durable command storage acknowledgement');
  return { status: 'stored', stream: puback.stream, sequence: puback.seq,
    duplicate: Boolean(puback.duplicate), command_id: envelope.command_id };
}

export async function loadProductionPorts({ pilotRoot, bloodbankRoot, sourceRoot, bloodbank }) {
  const config = await import(pathToFileURL(join(pilotRoot, 'src/config.js')));
  const { Plane } = await import(pathToFileURL(join(pilotRoot, 'src/plane.js')));
  const bb = bloodbank ?? loadBloodbank(bloodbankRoot);
  const schema = read(join(sourceRoot, 'skill/contracts/board.crank.v1.json'));
  const ajv = new bb.Ajv({ strict: false, allErrors: true }); bb.formats(ajv);
  ajv.addSchema(schema);
  const validate = (name, value) => assert(ajv.getSchema(`${schema.$id}#/$defs/${name}`)(value), `invalid ${name} contract`);
  // Bound Pilot's existing HTTP client; no second credential/HTTP implementation.
  const fetch = globalThis.fetch;
  let hydrationSignal;
  globalThis.fetch = (url, options = {}) => fetch(url, { ...options,
    signal: AbortSignal.any([options.signal, hydrationSignal, AbortSignal.timeout(2500)].filter(Boolean)) });
  let plane;
  const provider = c => {
    const cfg = config.requireBoard(config.loadConfig({ workspace: c.project.workspace, board: c.project.board_id }));
    assert(cfg.projectId === c.project.id && realpathSync(cfg.projectJson) ===
      realpathSync(join(c.project.workdir, '.project.json')) && (cfg.execution?.mode ?? 'legacy') === 'legacy',
    'Pilot binding differs or belongs to Krebs');
    if (!plane || plane.cfg.keyRef !== cfg.keyRef) plane = new Plane(cfg); else plane.cfg = cfg;
    return plane;
  };
  const leaseScript = join(sourceRoot, 'skill/scripts/momo-wip-lock.py');
  const lease = async (operation, path, owner) => {
    try { execFileSync('python3', [leaseScript, operation, path, owner,
      ...(operation === 'acquire' ? ['--ttl', '120'] : [])], { stdio: 'pipe', timeout: 3000 }); return true; }
    catch { return false; }
  };
  return {
    now: Date.now, lease,
    async leaseBusy(path) {
      if (!existsSync(path)) return false;
      const l = read(path);
      assert(typeof l.owner === 'string' && Number.isFinite(l.heartbeat_at) &&
        Number.isFinite(l.ttl) && l.ttl > 0, 'shared lease is malformed');
      return Date.now() / 1000 - l.heartbeat_at < l.ttl;
    },
    async runtime(c) {
      validate('input', c);
      assert(realpathSync(c.project.workdir) === c.project.workdir, 'workdir must be canonical');
      assert(realpathSync(c.runtime.state_dir) === c.runtime.state_dir, 'journal directory must be canonical');
      const manifest = read(join(c.project.workdir, '.project.json'));
      assert((manifest.execution?.mode ?? 'legacy') === 'legacy', 'managed/shadow board is owned by Krebs');
      const registry = await bb.registry.loadHermesRegistry(c.runtime.registry_file);
      const route = resolveRoute(bb, registry, c);
      const roleDir = manifest.agents?.[route.agentId]?.role_dir;
      assert(roleDir && resolve(c.project.workdir, roleDir, 'runtime/wip-driver.lock') === c.runtime.driver_lease,
        'driver lease must be the existing manifest-bound shared lease');
      for (const directory of [sourceRoot, c.project.workdir]) {
        const state = realpathSync(c.runtime.state_dir), root = realpathSync(directory);
        if (within(state, root)) {
          try { execFileSync('git', ['-C', directory, 'check-ignore', '-q', state], { stdio: 'pipe' }); }
          catch { throw new ControlRefusal('journal directory must be outside source or already ignored'); }
        }
      }
      const profile = join(c.runtime.profile_root, route.profileName ?? '');
      assert(existsSync(join(profile, 'config.yaml')) && existsSync(join(profile, 'SOUL.md')), 'Hermes profile is missing');
      provider(c); // Pilot owns credential resolution; resolved secrets remain in memory.
      const deployment = read(c.runtime.deployment_receipt), workers = read(c.runtime.worker_status_file);
      validate('runtime', deployment); validate('workers', workers);
      const skillSha256 = skillDigest(c.contractor.skill_root);
      assert(skillDigest(join(sourceRoot, 'skill')) === skillSha256, 'executing adapter differs from accepted installed bundle');
      return { manifest, route, deployment, workers, skillSha256 };
    },
    async board(c) {
      const p = provider(c);
      const [project, states, issues, labels] = await Promise.all([p.project(), p.states(), p.issues(), p.collection('labels')]);
      assert(typeof project.cycle_view === 'boolean', 'cycle configuration is unknown');
      const todos = new Set(states.filter(s => s.name === 'Todo').map(s => s.id));
      const candidates = issues.filter(i => todos.has(i.state));
      assert(candidates.length <= 100, 'too many Todo items for a bounded pass');
      const relations = {};
      let cycles = [], cycle_members = {};
      const controller = new AbortController(); hydrationSignal = controller.signal;
      let timer;
      const map = async (items, work) => {
        let next = 0;
        await Promise.all(Array.from({ length: Math.min(8, items.length) }, async () => {
          while (next < items.length) { assert(!controller.signal.aborted, 'board hydration budget exhausted'); await work(items[next++]); }
        }));
      };
      const hydrate = async items => map(items, async i => {
        try { relations[i.id] = await p.get(`${p.boardUrl()}/work-items/${i.id}/relations/`); }
        catch { relations[i.id] = null; } // missing truth excludes; never invent []
      });
      try {
        await Promise.race([(async () => {
          await hydrate(candidates);
          const targets = new Set(candidates.flatMap(i => (relations[i.id]?.blocking ?? [])
            .filter(r => r.project_id === c.project.board_id).map(r => r.issue_id)));
          await hydrate(issues.filter(i => targets.has(i.id) && !Object.hasOwn(relations, i.id)));
          if (project.cycle_view) {
            cycles = await p.collection('cycles');
            await map(cycles, async cycle => {
              cycle_members[cycle.id] = (await p.pages(`${p.boardUrl()}/cycles/${cycle.id}/cycle-issues/`))
                .map(row => typeof row === 'string' ? row : typeof row.issue === 'object' ? row.issue?.id : row.issue ?? row.issue_id);
              assert(cycle_members[cycle.id].every(id => typeof id === 'string' && id.length), 'cycle membership is malformed');
            });
          }
        })(), new Promise((_, reject) => { timer = setTimeout(() => {
          controller.abort(); reject(new ControlRefusal('board hydration budget exhausted'));
        }, 5000); })]);
      } finally {
        clearTimeout(timer); controller.abort(); hydrationSignal = undefined;
      }
      return { id: c.project.board_id, states, issues, labels, relations,
        identifier: p.cfg.identifier, cycle_view: project.cycle_view, cycles, cycle_members };
    },
    async ticket(c, id) { return provider(c).get(`${provider(c).boardUrl()}/issues/${id}/`); },
    async patch(c, id, fields) { return provider(c).editIssue(id, { fields }); },
    async command(c, chosen, route) { return commandFor(bb, c, chosen, route); },
    async publish(c, envelope) { return publishExact(bb, c, envelope); },
    async completed(c, j, route) {
      const type = 'bloodbank.agent.invocation.completed';
      return bb.replay.withDirectGet({ host: c.runtime.nats_server, timeoutMs: 1500 }, async get => {
        const found = await bb.replay.findLatestMatching(get, 'BLOODBANK_EVENTS', bb.nats.subjectFor(type, 'event'),
          event => matchCompleted(j, event, route), { budgetMs: 1000, maxRequests: 100, initialWindow: 16 });
        if (found) bb.nats.validateEnvelope(type, found.envelope);
        return found?.envelope;
      });
    },
    async started(c, envelope, route, wait = false) {
      const deadline = Date.now() + (wait ? c.runtime.ack_timeout_ms : 1500);
      return bb.replay.withDirectGet({ host: c.runtime.nats_server, timeoutMs: 1500 }, async get => {
        do {
          const pair = [];
          for (const type of ['bloodbank.conversation.turn.started', 'bloodbank.agent.invocation.started']) {
            const found = await bb.replay.findLatestMatching(get, 'BLOODBANK_EVENTS', bb.nats.subjectFor(type, 'event'),
              event => event.data?.command_id === envelope.command_id && event.data?.target_agent_id === route.agentId,
              { budgetMs: Math.max(1, Math.min(deadline - Date.now(), 500)), maxRequests: 100, initialWindow: 16 });
            if (found) bb.nats.validateEnvelope(type, found.envelope);
            pair.push(found?.envelope);
          }
          if (matchStarted(envelope, pair, route)) return pair;
          if (!wait || Date.now() >= deadline) return [];
          await sleep(100);
        } while (Date.now() < deadline);
        return [];
      });
    },
  };
}
