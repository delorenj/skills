import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {fileURLToPath} from 'node:url';
import {resolveJobNarrationPaths} from '../scripts/narrate.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');

function fixture(name) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `slowburns-${name}-`));
}

function copy(from, to) {
  fs.mkdirSync(path.dirname(to), {recursive: true});
  fs.copyFileSync(from, to);
}

test('CLI threads the canonical job and claim identity into build', () => {
  const root = fixture('cli-identity');
  try {
    copy(path.join(ROOT, 'bin', 'slowburns.mjs'), path.join(root, 'bin', 'slowburns.mjs'));
    fs.mkdirSync(path.join(root, 'scripts'), {recursive: true});
    fs.writeFileSync(path.join(root, 'scripts', 'letterify.mjs'), 'export async function letterify() { throw new Error("letterify must remain skipped"); }\n');
    fs.writeFileSync(path.join(root, 'scripts', 'build.mjs'), 'import fs from "node:fs"; fs.writeFileSync(process.env.SLOWBURNS_TEST_CAPTURE, JSON.stringify(process.argv.slice(2)));\n');
    const capture = path.join(root, 'cli-argv.json');
    const out = path.join(root, 'job-alpha.mp4');

    execFileSync(process.execPath, [
      path.join(root, 'bin', 'slowburns.mjs'),
      '--text', 'Public source text.',
      '--letter', 'The finished dispatch.',
      '--no-music',
      '--no-ambient',
      '--out', out,
      '--job-id', 'job-alpha',
      '--claim-operation-id', 'claim-one',
    ], {
      cwd: root,
      env: {...process.env, SLOWBURNS_TEST_CAPTURE: capture},
      stdio: 'pipe',
    });

    const argv = JSON.parse(fs.readFileSync(capture, 'utf8'));
    assert.deepEqual(argv.slice(argv.indexOf('--job-id'), argv.indexOf('--job-id') + 4), [
      '--job-id', 'job-alpha', '--claim-operation-id', 'claim-one',
    ]);

    const localCapture = path.join(root, 'local-cli-argv.json');
    execFileSync(process.execPath, [
      path.join(root, 'bin', 'slowburns.mjs'),
      '--text', 'A direct human invocation.',
      '--raw',
      '--no-music',
      '--no-ambient',
      '--out', path.join(root, 'local.mp4'),
    ], {
      cwd: root,
      env: {...process.env, SLOWBURNS_TEST_CAPTURE: localCapture},
      stdio: 'pipe',
    });
    const localArgv = JSON.parse(fs.readFileSync(localCapture, 'utf8'));
    assert.equal(localArgv.includes('--job-id'), false);
    assert.equal(localArgv.includes('--claim-operation-id'), false);
  } finally {
    fs.rmSync(root, {recursive: true, force: true});
  }
});

test('build keeps narration and Remotion inputs inside the job runtime namespace', () => {
  const root = fixture('build-identity');
  try {
    copy(path.join(ROOT, 'scripts', 'build.mjs'), path.join(root, 'scripts', 'build.mjs'));
    copy(path.join(ROOT, 'scripts', 'narrate.mjs'), path.join(root, 'scripts', 'narrate.mjs'));
    fs.mkdirSync(path.join(root, 'remotion', 'node_modules'), {recursive: true});
    const legacyRoot = path.join(root, 'remotion', 'public');
    fs.mkdirSync(legacyRoot, {recursive: true});
    const legacy = new Map([
      [path.join(legacyRoot, 'narration.mp3'), Buffer.from('legacy-audio-byte-sentinel')],
      [path.join(legacyRoot, 'narration.mp3.receipt.json'), Buffer.from('{"schema_version":1,"operation":"legacy","state":"primary_failed","attempts":[]}\n')],
      [path.join(legacyRoot, 'narration.mp3.narration.lock'), Buffer.from('{"schema_version":2,"phase":"claimed_pre_provider","owner_pid":1,"owner_host":"legacy-host"}\n')],
    ]);
    for (const [file, bytes] of legacy) fs.writeFileSync(file, bytes);

    const fakeBin = path.join(root, 'fake-bin');
    fs.mkdirSync(fakeBin);
    const capture = path.join(root, 'child-calls.jsonl');
    const fakeNode = path.join(fakeBin, 'node');
    fs.writeFileSync(fakeNode, `#!${process.execPath}\nimport fs from 'node:fs';\nconst args = process.argv.slice(2);\nfs.appendFileSync(process.env.SLOWBURNS_TEST_CAPTURE, JSON.stringify({command: 'node', args}) + '\\n');\nconst out = args[args.indexOf('--out') + 1];\nif (out && !fs.existsSync(out)) { fs.mkdirSync(new URL('.', 'file://' + out).pathname, {recursive: true}); fs.writeFileSync(out, 'fake-audio'); }\n`);
    fs.chmodSync(fakeNode, 0o755);
    const fakeNpx = path.join(fakeBin, 'npx');
    fs.writeFileSync(fakeNpx, `#!${process.execPath}\nimport fs from 'node:fs';\nconst args = process.argv.slice(2);\nfs.appendFileSync(process.env.SLOWBURNS_TEST_CAPTURE, JSON.stringify({command: 'npx', args}) + '\\n');\nfs.mkdirSync(new URL('.', 'file://' + args[3]).pathname, {recursive: true});\nfs.writeFileSync(args[3], 'fake-video');\n`);
    fs.chmodSync(fakeNpx, 0o755);

    const workRoot = path.join(root, 'runtime');
    fs.mkdirSync(workRoot);
    const out = path.join(workRoot, 'job-alpha.mp4');
    execFileSync(process.execPath, [
      path.join(root, 'scripts', 'build.mjs'),
      '--text', 'The same finished dispatch.',
      '--out', out,
      '--job-id', 'job-alpha',
      '--claim-operation-id', 'claim-one',
      '--no-music',
      '--no-ambient',
    ], {
      cwd: root,
      env: {...process.env, PATH: `${fakeBin}:${process.env.PATH}`, SLOWBURNS_TEST_CAPTURE: capture},
      stdio: 'pipe',
    });

    const calls = fs.readFileSync(capture, 'utf8').trim().split('\n').map((line) => JSON.parse(line));
    const narration = calls.find(({command}) => command === 'node');
    const render = calls.find(({command}) => command === 'npx');
    const narrationOut = narration.args[narration.args.indexOf('--out') + 1];
    const receipt = narration.args[narration.args.indexOf('--receipt') + 1];
    const operationId = narration.args[narration.args.indexOf('--operation-id') + 1];
    const relative = path.relative(workRoot, narrationOut);
    assert.ok(relative && !relative.startsWith('..') && !path.isAbsolute(relative));
    assert.match(relative, /^\.slowburns-narration[/\\]v1[/\\][a-f0-9]{64}[/\\]public[/\\]narration\.mp3$/);
    assert.equal(receipt, `${narrationOut}.receipt.json`);
    assert.match(operationId, /^slowburns-job-v1-[a-f0-9]{64}$/);
    assert.ok(narration.args.includes('--stdin'), 'the transcript must not persist in an input file or argv');
    assert.equal(narration.args.includes('--file'), false);
    assert.ok(render.args.includes(`--public-dir=${path.dirname(narrationOut)}`));
    const propsArg = render.args.find((value) => value.startsWith('--props='));
    assert.ok(propsArg.startsWith(`--props=${path.dirname(path.dirname(narrationOut))}${path.sep}`));
    assert.equal(fs.existsSync(propsArg.slice('--props='.length)), false, 'ephemeral transcript-bearing props are removed');

    const localOut = path.join(workRoot, 'local-human.mp4');
    execFileSync(process.execPath, [
      path.join(root, 'scripts', 'build.mjs'),
      '--text', 'A direct human dispatch.',
      '--out', localOut,
      '--no-music',
      '--no-ambient',
    ], {
      cwd: root,
      env: {...process.env, PATH: `${fakeBin}:${process.env.PATH}`, SLOWBURNS_TEST_CAPTURE: capture},
      stdio: 'pipe',
    });
    const allCalls = fs.readFileSync(capture, 'utf8').trim().split('\n').map((line) => JSON.parse(line));
    const localNarration = allCalls.slice(calls.length).find(({command}) => command === 'node');
    const localNarrationOut = localNarration.args[localNarration.args.indexOf('--out') + 1];
    const localRelative = path.relative(workRoot, localNarrationOut);
    assert.match(localRelative, /^\.slowburns-narration[/\\]v1[/\\][a-f0-9]{64}[/\\]public[/\\]narration\.mp3$/);
    assert.notEqual(localNarrationOut, narrationOut, 'direct outputs receive deterministic output-bound local namespaces');
    for (const [file, bytes] of legacy) assert.deepEqual(fs.readFileSync(file), bytes);
  } finally {
    fs.rmSync(root, {recursive: true, force: true});
  }
});

test('direct build refuses changed text for completed output-bound narration without rendering or provider use', () => {
  const root = fixture('build-transcript-integrity');
  try {
    copy(path.join(ROOT, 'scripts', 'build.mjs'), path.join(root, 'scripts', 'build.mjs'));
    copy(path.join(ROOT, 'scripts', 'narrate.mjs'), path.join(root, 'scripts', 'narrate.mjs'));
    fs.mkdirSync(path.join(root, 'remotion', 'node_modules'), {recursive: true});

    const workRoot = path.join(root, 'runtime');
    fs.mkdirSync(workRoot);
    const out = path.join(workRoot, 'fixed-direct-output.mp4');
    const outputIdentity = crypto.createHash('sha256').update(path.resolve(out)).digest('hex');
    const narration = resolveJobNarrationPaths({
      workRoot,
      jobId: 'local-render',
      claimOperationId: `output-${outputIdentity}`,
    });
    fs.mkdirSync(narration.publicDir, {recursive: true});
    execFileSync('ffmpeg', [
      '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.15',
      '-q:a', '9', '-acodec', 'libmp3lame', narration.out,
    ]);
    const textA = 'Transcript A owns this direct output narration.';
    const textB = 'Transcript B must not render over narration A.';
    const audio = fs.readFileSync(narration.out);
    fs.writeFileSync(narration.receiptPath, `${JSON.stringify({
      schema_version: 1,
      operation: crypto.createHash('sha256').update(`${narration.operationId}\0${textA}`).digest('hex'),
      state: 'complete',
      attempts: [],
      selection: {provider: 'eleven', model: 'eleven_multilingual_v2', voice_id: 'fixture', reason: 'primary'},
      audio_sha256: crypto.createHash('sha256').update(audio).digest('hex'),
    })}\n`);

    const fakeBin = path.join(root, 'fake-bin');
    fs.mkdirSync(fakeBin);
    const renderCapture = path.join(root, 'render-calls.jsonl');
    const providerCapture = path.join(root, 'provider-calls.jsonl');
    const fakeNpx = path.join(fakeBin, 'npx');
    fs.writeFileSync(fakeNpx, `#!${process.execPath}\nimport fs from 'node:fs';\nconst args = process.argv.slice(2);\nfs.appendFileSync(process.env.SLOWBURNS_RENDER_CAPTURE, JSON.stringify(args) + '\\n');\nfs.writeFileSync(args[3], 'fake-video');\n`);
    fs.chmodSync(fakeNpx, 0o755);
    const fetchGuard = path.join(root, 'provider-fetch-guard.mjs');
    fs.writeFileSync(fetchGuard, `import fs from 'node:fs';\nglobalThis.fetch = async (url) => { fs.appendFileSync(process.env.SLOWBURNS_PROVIDER_CAPTURE, String(url) + '\\n'); throw new Error('provider calls are forbidden in this fixture'); };\n`);
    const env = {
      ...process.env,
      PATH: `${fakeBin}:${process.env.PATH}`,
      NODE_OPTIONS: `${process.env.NODE_OPTIONS || ''} --import=${fetchGuard}`.trim(),
      ELEVENLABS_API_KEY: 'eleven-test-key',
      CARTESIA_API_KEY: 'sk_car_1234567890abcdefghij',
      CARTESIA_VOICE_ID: 'fixture-cartesia-voice',
      SLOWBURNS_RENDER_CAPTURE: renderCapture,
      SLOWBURNS_PROVIDER_CAPTURE: providerCapture,
    };
    const buildArgs = (text) => [
      path.join(root, 'scripts', 'build.mjs'),
      '--text', text,
      '--out', out,
      '--no-music',
      '--no-ambient',
    ];

    execFileSync(process.execPath, buildArgs(textA), {cwd: root, env, stdio: 'pipe'});
    assert.equal(fs.readFileSync(renderCapture, 'utf8').trim().split('\n').length, 1);
    assert.equal(fs.existsSync(providerCapture), false, 'exact-text recovery must not call a provider');
    const audioBeforeMismatch = fs.readFileSync(narration.out);
    const receiptBeforeMismatch = fs.readFileSync(narration.receiptPath);

    assert.throws(
      () => execFileSync(process.execPath, buildArgs(textB), {cwd: root, env, stdio: 'pipe'}),
      (error) => error.status !== 0,
    );
    assert.equal(fs.existsSync(providerCapture), false, 'changed text must fail before provider dispatch');
    assert.equal(fs.readFileSync(renderCapture, 'utf8').trim().split('\n').length, 1, 'changed text must not render');
    assert.deepEqual(fs.readFileSync(narration.out), audioBeforeMismatch);
    assert.deepEqual(fs.readFileSync(narration.receiptPath), receiptBeforeMismatch);
    assert.equal(fs.existsSync(narration.lockPath), false);
  } finally {
    fs.rmSync(root, {recursive: true, force: true});
  }
});
