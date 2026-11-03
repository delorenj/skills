#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { fork } from 'node:child_process';
import { crank, reconcile } from './lib/board_crank.mjs';
import { loadProductionPorts } from './lib/board_crank_ports.mjs';

const args = process.argv.slice(2);
if (args.includes('--help') || !args.length) {
  console.log(`Usage: momo-board-crank.mjs inspect|execute|reconcile --config /runtime/board-crank.json
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank [--replay]

inspect is read-only (also --dry-run). execute requires an enabled input contract,
an accepted deployment receipt, fresh worker truth, and the existing shared lease.
--replay publishes ONLY the previously journaled exact command after revalidation.
reconcile retires only a completed fence with matching receipt, fresh no-worker
truth and final Done state. execute also reconciles an active prior execution.
No cron is installed. Runtime/contractor prerequisites are never enabled here.`);
  process.exit(0);
}
const operation = args.shift();
const flags = {};
// The supervising process performs no vault/provider operations. A detached
// child owns the pass and its synchronous subprocesses; kill their entire group
// on timeout. The test knob can only SHORTEN the production wall-clock budget.
if (!process.send) {
  const requested = Number(process.env.MOMO_BOARD_CRANK_BUDGET_MS);
  const budget = Number.isFinite(requested) && requested > 0 ? Math.min(requested, 45000) : 45000;
  const child = fork(fileURLToPath(import.meta.url), process.argv.slice(2), { detached: true, silent: true });
  let output = '', finished = false;
  const finish = (receipt, code) => {
    if (finished) return;
    finished = true; clearTimeout(timer);
    try { process.kill(-child.pid, 'SIGKILL'); } catch {}
    console.log(JSON.stringify(receipt)); process.exitCode = code;
  };
  const refusal = { contract: 'board.crank.v1', status: 'refused',
    reason: 'invalid input or unavailable dependency/runtime; no activation performed', live_execution_proof: false };
  const timer = setTimeout(() => finish({ ...refusal, status: 'uncertain',
    reason: 'control pass wall-clock budget exhausted; durable intent preserved' }, 124), budget);
  child.stdout.on('data', bytes => {
    output += bytes.toString();
    if (Buffer.byteLength(output) > 262144) finish(refusal, 78);
  });
  child.stderr.resume(); // dependency diagnostics may contain credentials
  child.on('error', () => finish(refusal, 78));
  child.on('close', code => {
    try {
      const receipt = JSON.parse(output);
      if (receipt.contract !== 'board.crank.v1' || receipt.live_execution_proof !== false) throw new Error();
      finish(receipt, code ?? 78);
    } catch { finish(refusal, 78); }
  });
} else {
try {
  if (!['inspect', 'execute', 'reconcile'].includes(operation)) throw new Error('unknown operation');
  while (args.length) {
    const key = args.shift();
    if (['--replay', '--dry-run'].includes(key)) flags[key] = true;
    else if (['--config', '--pilot-root', '--bloodbank-root'].includes(key) && args.length) flags[key] = args.shift();
    else throw new Error('invalid arguments');
  }
  if (!flags['--config'] || !flags['--pilot-root'] || !flags['--bloodbank-root']) throw new Error('explicit config and dependency source roots required');
  const config = JSON.parse(readFileSync(resolve(flags['--config']), 'utf8'));
  if (!config.project?.workdir) throw new Error('explicit workdir required');
  process.chdir(config.project.workdir);
  const ports = await loadProductionPorts({ pilotRoot: resolve(flags['--pilot-root']),
    bloodbankRoot: resolve(flags['--bloodbank-root']), sourceRoot: resolve(dirname(fileURLToPath(import.meta.url)), '../..') });
  const result = operation === 'reconcile' ? await reconcile(config, ports, { execute: !flags['--dry-run'] }) :
    await crank(config, ports, { execute: operation === 'execute' && !flags['--dry-run'], replay: flags['--replay'] === true });
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = ['refused', 'uncertain'].includes(result.status) ? 78 : 0;
} catch {
  // Dependency, vault and provider diagnostics may carry resolved credentials.
  console.log(JSON.stringify({ contract: 'board.crank.v1', status: 'refused',
    reason: 'invalid input or unavailable dependency/runtime; no activation performed', live_execution_proof: false }));
  process.exitCode = 78;
}
}
