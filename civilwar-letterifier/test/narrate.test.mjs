import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {isDecodableMp3, narrate, resolveConfig, resolveJobNarrationPaths} from '../scripts/narrate.mjs';

const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'slowburns-narrate-test-'));
const sampleMp3 = path.join(tempRoot, 'sample.mp3');
execFileSync('ffmpeg', [
  '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.15', '-q:a', '9', '-acodec', 'libmp3lame', sampleMp3,
]);
const validAudio = fs.readFileSync(sampleMp3);
const alternateSampleMp3 = path.join(tempRoot, 'alternate-sample.mp3');
execFileSync('ffmpeg', [
  '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=660:duration=0.15', '-q:a', '9', '-acodec', 'libmp3lame', alternateSampleMp3,
]);
const alternateValidAudio = fs.readFileSync(alternateSampleMp3);
const largeSampleMp3 = path.join(tempRoot, 'large-sample.mp3');
execFileSync('ffmpeg', [
  '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=330:duration=1', '-q:a', '9', '-acodec', 'libmp3lame', largeSampleMp3,
]);
const largeValidAudio = fs.readFileSync(largeSampleMp3);

test.after(() => fs.rmSync(tempRoot, {recursive: true, force: true}));

function runDir(name) {
  return fs.mkdtempSync(path.join(tempRoot, `${name}-`));
}

function config(overrides = {}) {
  return {
    elevenKey: 'eleven-test-key',
    cartesiaKey: 'sk_car_1234567890abcdefghij',
    cartesiaVoiceId: 'verified-by-runtime-config',
    elevenUrl: 'https://eleven.test/tts',
    cartesiaUrl: 'https://cartesia.test/tts/bytes',
    ...overrides,
  };
}

function lockPathFor(out) {
  return `${path.resolve(out)}.narration.lock`;
}

test('job narration identities isolate identical text without touching legacy global state', async () => {
  const workRoot = runDir('job-identity-isolation');
  const legacyRoot = path.join(workRoot, 'remotion', 'public');
  fs.mkdirSync(legacyRoot, {recursive: true});
  const legacy = new Map([
    [path.join(legacyRoot, 'narration.mp3'), Buffer.from('legacy-audio-byte-sentinel')],
    [path.join(legacyRoot, 'narration.mp3.receipt.json'), Buffer.from('{"schema_version":1,"operation":"legacy","state":"primary_failed","attempts":[]}\n')],
    [path.join(legacyRoot, 'narration.mp3.narration.lock'), Buffer.from('{"schema_version":2,"phase":"claimed_pre_provider","owner_pid":1,"owner_host":"legacy-host"}\n')],
  ]);
  for (const [file, bytes] of legacy) fs.writeFileSync(file, bytes);

  const first = resolveJobNarrationPaths({
    workRoot,
    jobId: 'job-alpha',
    claimOperationId: 'claim-one',
  });
  const second = resolveJobNarrationPaths({
    workRoot,
    jobId: 'job-bravo',
    claimOperationId: 'claim-two',
  });

  for (const key of ['out', 'receiptPath', 'lockPath', 'operationId']) {
    assert.notEqual(first[key], second[key], `${key} must bind the admitted job and claim`);
  }
  for (const target of [first.out, first.receiptPath, first.lockPath, second.out, second.receiptPath, second.lockPath]) {
    const relative = path.relative(path.resolve(workRoot), target);
    assert.ok(relative && !relative.startsWith('..') && !path.isAbsolute(relative), `${target} must stay below the work root`);
  }
  const calls = [];
  for (const target of [first, second]) {
    await narrate({
      text: 'The same dispatch for two different jobs.',
      out: target.out,
      receiptPath: target.receiptPath,
      operationId: target.operationId,
      config: config(),
      log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return audioResponse();
      },
    });
  }
  assert.deepEqual(calls, ['https://eleven.test/tts', 'https://eleven.test/tts']);
  assert.notEqual(
    JSON.parse(fs.readFileSync(first.receiptPath, 'utf8')).operation,
    JSON.parse(fs.readFileSync(second.receiptPath, 'utf8')).operation,
  );
  assert.equal(fs.existsSync(first.out), true);
  assert.equal(fs.existsSync(second.out), true);
  assert.equal(fs.existsSync(first.lockPath), false);
  assert.equal(fs.existsSync(second.lockPath), false);

  const retry = resolveJobNarrationPaths({workRoot, jobId: 'job-alpha', claimOperationId: 'claim-one'});
  assert.deepEqual(retry, first, 'the same admitted claim must resolve the same durable identities');
  await narrate({
    text: 'The same dispatch for two different jobs.',
    out: retry.out,
    receiptPath: retry.receiptPath,
    operationId: retry.operationId,
    config: config(),
    log: () => {},
    fetchImpl: async () => { throw new Error('recovery must not call a provider'); },
  });
  assert.equal(calls.length, 2);
  for (const [file, bytes] of legacy) assert.deepEqual(fs.readFileSync(file), bytes);
});

test('a stale same-claim pre-provider lock remains a zero-call manual recovery boundary', async () => {
  const workRoot = runDir('stale-pre-provider-manual-boundary');
  const target = resolveJobNarrationPaths({workRoot, jobId: 'job-locked', claimOperationId: 'claim-locked'});
  fs.mkdirSync(path.dirname(target.lockPath), {recursive: true});
  const retained = Buffer.from('{"schema_version":2,"phase":"claimed_pre_provider","created_at":"2020-01-01T00:00:00.000Z","owner_pid":999999,"owner_host":"dead-host"}\n');
  fs.writeFileSync(target.lockPath, retained);
  let providerCalls = 0;
  await assert.rejects(
    narrate({
      text: 'This claim must remain locked for an operator.',
      out: target.out,
      receiptPath: target.receiptPath,
      operationId: target.operationId,
      config: config(),
      log: () => {},
      fetchImpl: async () => { providerCalls += 1; return audioResponse(); },
    }),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(providerCalls, 0);
  assert.deepEqual(fs.readFileSync(target.lockPath), retained);
});

test('job narration identity hashes path-like input and rejects noncanonical control data', () => {
  const workRoot = runDir('job-identity-path-safety');
  const first = resolveJobNarrationPaths({workRoot, jobId: '../job', claimOperationId: '../../claim'});
  const second = resolveJobNarrationPaths({workRoot, jobId: '..\\job', claimOperationId: '..\\..\\claim'});
  assert.notEqual(first.directory, second.directory, 'distinct raw identities must not collide after path normalization');
  for (const target of [first.directory, second.directory]) {
    const relative = path.relative(path.resolve(workRoot), target);
    assert.ok(relative && !relative.startsWith('..') && !path.isAbsolute(relative));
  }
  assert.throws(
    () => resolveJobNarrationPaths({workRoot, jobId: 'job\u0000escape', claimOperationId: 'claim'}),
    (error) => error.fallbackClass === 'configuration',
  );

  const outside = runDir('job-identity-symlink-outside');
  fs.mkdirSync(path.dirname(first.directory), {recursive: true});
  fs.symlinkSync(outside, first.directory, 'dir');
  assert.throws(
    () => resolveJobNarrationPaths({workRoot, jobId: '../job', claimOperationId: '../../claim'}),
    (error) => error.fallbackClass === 'configuration',
  );
});

function jsonResponse(status, body, requestId = 'safe-request-id') {
  return new Response(JSON.stringify(body), {
    status,
    headers: {'content-type': 'application/json', 'x-request-id': requestId},
  });
}

async function withInheritedObjectProperty(name, value, operation) {
  const previous = Object.getOwnPropertyDescriptor(Object.prototype, name);
  Object.defineProperty(Object.prototype, name, {
    configurable: true,
    enumerable: false,
    value,
    writable: true,
  });
  try {
    return await operation();
  } finally {
    if (previous) Object.defineProperty(Object.prototype, name, previous);
    else delete Object.prototype[name];
  }
}

function elevenErrorResponse(status, {type, code, legacyStatus, requestId = 'safe-request-id', message = 'provider message'} = {}) {
  const detail = {type, message, request_id: requestId};
  if (code !== undefined) detail.code = code;
  if (legacyStatus !== undefined) detail.status = legacyStatus;
  return jsonResponse(status, {detail}, requestId);
}

function cartesiaErrorResponse(status, errorCode, requestId = 'safe-request-id') {
  return jsonResponse(status, {error_code: errorCode, request_id: requestId}, requestId);
}

function audioResponse(audio = validAudio, requestId = 'safe-request-id') {
  return new Response(audio, {status: 200, headers: {'content-type': 'audio/mpeg', 'x-request-id': requestId}});
}

function streamedResponse({
  ok = true,
  status = 200,
  contentType = 'audio/mpeg',
  chunks = [],
  requestId = 'safe-request-id',
  cancelError,
  cancelNeverSettles = false,
  hang = false,
  readError,
} = {}) {
  const stats = {abortCalls: 0, cancelCalls: 0, abortCallsWhenCancelStarted: undefined, getReaderCalls: 0, readCalls: 0};
  let index = 0;
  const reader = {
    async read() {
      stats.readCalls += 1;
      if (hang) return new Promise(() => {});
      if (readError) throw readError;
      if (index >= chunks.length) return {done: true};
      return {done: false, value: chunks[index++]};
    },
    async cancel() {
      stats.cancelCalls += 1;
      stats.abortCallsWhenCancelStarted = stats.abortCalls;
      if (cancelNeverSettles) return new Promise(() => {});
      if (cancelError) throw cancelError;
    },
  };
  return {
    response: {
      ok,
      status,
      headers: new Headers({'content-type': contentType, 'x-request-id': requestId}),
      body: {getReader: () => { stats.getReaderCalls += 1; return reader; }},
    },
    stats,
    observeRequest(init) {
      init.signal?.addEventListener('abort', () => { stats.abortCalls += 1; }, {once: true});
    },
  };
}

function bodyCancelableResponse({
  status = 400,
  contentType = 'text/plain',
  requestId = 'safe-request-id',
  cancelError,
  cancelNeverSettles = false,
} = {}) {
  const stats = {abortCalls: 0, bodyCancelCalls: 0, abortCallsWhenCancelStarted: undefined};
  return {
    response: {
      ok: false,
      status,
      headers: new Headers({'content-type': contentType, 'x-request-id': requestId}),
      body: {
        cancel() {
          stats.bodyCancelCalls += 1;
          stats.abortCallsWhenCancelStarted = stats.abortCalls;
          if (cancelNeverSettles) return new Promise(() => {});
          if (cancelError) return Promise.reject(cancelError);
          return Promise.resolve();
        },
      },
    },
    stats,
    observeRequest(init) {
      init.signal?.addEventListener('abort', () => { stats.abortCalls += 1; }, {once: true});
    },
  };
}

async function rejectsPromptly(operation, assertion, timeoutMs = 250) {
  let timer;
  const deadline = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error('provider cleanup did not return within its bound')), timeoutMs);
  });
  try {
    await assert.rejects(Promise.race([operation, deadline]), assertion);
  } finally {
    clearTimeout(timer);
  }
}

function unreadableAudioResponse(requestId = 'safe-request-id') {
  return {
    ok: true,
    status: 200,
    headers: new Headers({'content-type': 'audio/mpeg', 'x-request-id': requestId}),
    arrayBuffer: async () => { throw new Error('response stream interrupted'); },
  };
}

function unreadableJsonResponse(status = 500, requestId = 'safe-request-id') {
  return {
    ok: false,
    status,
    headers: new Headers({'content-type': 'application/json', 'x-request-id': requestId}),
    arrayBuffer: async () => { throw new Error('error response stream interrupted'); },
  };
}

function hangingAudioResponse(requestId = 'safe-request-id') {
  return {
    ok: true,
    status: 200,
    headers: new Headers({'content-type': 'audio/mpeg', 'x-request-id': requestId}),
    body: {
      getReader() {
        return {
          read: async () => new Promise(() => {}),
          cancel: async () => {},
        };
      },
    },
  };
}

test('primary success makes one Eleven call, no Cartesia call, and a decodable MP3', async () => {
  const calls = [];
  const dir = runDir('primary');
  const out = path.join(dir, 'narration.mp3');
  const stream = streamedResponse({chunks: [validAudio]});
  const receipt = await narrate({
    text: 'A solemn dispatch.', out, operationId: 'primary', config: config(), log: () => {},
    fetchImpl: async (url, init) => { calls.push(url); stream.observeRequest(init); return stream.response; },
  });
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(receipt.selection.provider, 'eleven');
  assert.equal(isDecodableMp3(out), true);
  assert.ok(fs.statSync(out).size > 0);
  assert.equal(stream.stats.cancelCalls, 0);
  assert.equal(stream.stats.abortCalls, 0);
});

test('streamed oversized Eleven audio cancels its unread reader and retains the claim', async () => {
  const out = path.join(runDir('streamed-oversized-eleven-audio'), 'narration.mp3');
  const stream = streamedResponse({chunks: [Buffer.alloc(1025)]});
  const calls = [];
  const fetchImpl = async (url, init) => { calls.push(url); stream.observeRequest(init); return stream.response; };
  const limits = config({limits: {maxAudioBytes: 1024}});
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'first', config: limits, log: () => {}, fetchImpl}),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'invalid_audio',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(stream.stats.cancelCalls, 1);
  assert.equal(stream.stats.abortCalls, 1);
  assert.equal(JSON.parse(fs.readFileSync(lockPathFor(out), 'utf8')).phase, 'eleven_audio_body_read_started');
  await assert.rejects(
    narrate({text: 'A different dispatch.', out, operationId: 'second', config: limits, log: () => {}, fetchImpl}),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(calls.length, 1);
});

test('streamed oversized Cartesia error body cancels its unread reader and retains the claim', async () => {
  const out = path.join(runDir('streamed-oversized-cartesia-error'), 'narration.mp3');
  const stream = streamedResponse({ok: false, status: 503, contentType: 'application/json', chunks: [Buffer.alloc(129)]});
  const calls = [];
  const fetchImpl = async (url, init) => {
    calls.push(url);
    if (calls.length === 1) return elevenErrorResponse(429, {type: 'rate_limit_error', code: 'rate_limit_exceeded'});
    stream.observeRequest(init);
    return stream.response;
  };
  const limits = config({limits: {maxErrorBodyBytes: 128}});
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'first', config: limits, log: () => {}, fetchImpl}),
    (error) => error.provider === 'cartesia' && error.fallbackClass === 'ambiguous_transport',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
  assert.equal(stream.stats.cancelCalls, 1);
  assert.equal(stream.stats.abortCalls, 1);
  assert.equal(JSON.parse(fs.readFileSync(lockPathFor(out), 'utf8')).phase, 'cartesia_error_body_read_started');
  await assert.rejects(
    narrate({text: 'A different dispatch.', out, operationId: 'second', config: limits, log: () => {}, fetchImpl}),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(calls.length, 2);
});

test('streamed reader timeout and failure cancel unread Eleven response resources', async () => {
  const timeoutOut = path.join(runDir('streamed-reader-timeout'), 'narration.mp3');
  const timeoutStream = streamedResponse({hang: true});
  let timeoutCalls = 0;
  const timeoutConfig = config({limits: {bodyReadTimeoutMs: 10}});
  const timeoutFetch = async (url, init) => {
    timeoutCalls += 1;
    timeoutStream.observeRequest(init);
    return timeoutStream.response;
  };
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out: timeoutOut, operationId: 'first', config: timeoutConfig, log: () => {}, fetchImpl: timeoutFetch}),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'ambiguous_transport',
  );
  assert.equal(timeoutStream.stats.cancelCalls, 1);
  assert.equal(timeoutStream.stats.abortCalls, 1);
  await assert.rejects(
    narrate({text: 'A different dispatch.', out: timeoutOut, operationId: 'second', config: timeoutConfig, log: () => {}, fetchImpl: timeoutFetch}),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(timeoutCalls, 1);

  const errorOut = path.join(runDir('streamed-reader-error'), 'narration.mp3');
  const errorStream = streamedResponse({readError: new Error('PRIVATE STREAM READ FAILURE')});
  let errorCalls = 0;
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out: errorOut, operationId: 'first', config: config(), log: () => {},
      fetchImpl: async (url, init) => { errorCalls += 1; errorStream.observeRequest(init); return errorStream.response; },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'ambiguous_transport',
  );
  assert.equal(errorStream.stats.cancelCalls, 1);
  assert.equal(errorStream.stats.abortCalls, 1);
  assert.equal(fs.existsSync(lockPathFor(errorOut)), true);
  await assert.rejects(
    narrate({
      text: 'A different dispatch.', out: errorOut, operationId: 'second', config: config(), log: () => {},
      fetchImpl: async (url, init) => { errorCalls += 1; errorStream.observeRequest(init); return errorStream.response; },
    }),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(errorCalls, 1);
});

test('skipped non-JSON errors cancel unread streams without masking provider semantics', async () => {
  const elevenOut = path.join(runDir('streamed-nonjson-eleven'), 'narration.mp3');
  const elevenStream = streamedResponse({
    ok: false, status: 400, contentType: 'text/plain', chunks: [Buffer.from('PRIVATE PROVIDER BODY')],
    cancelError: new Error('PRIVATE CANCEL FAILURE'),
  });
  const elevenCalls = [];
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out: elevenOut, operationId: 'first', config: config(), log: () => {},
      fetchImpl: async (url, init) => { elevenCalls.push(url); elevenStream.observeRequest(init); return elevenStream.response; },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(elevenCalls, ['https://eleven.test/tts']);
  assert.equal(elevenStream.stats.readCalls, 0);
  assert.equal(elevenStream.stats.cancelCalls, 1);
  assert.equal(elevenStream.stats.abortCalls, 1);
  assert.equal(fs.existsSync(lockPathFor(elevenOut)), false);

  const cartesiaOut = path.join(runDir('streamed-nonjson-cartesia'), 'narration.mp3');
  const cartesiaStream = bodyCancelableResponse({
    status: 400,
    contentType: 'text/plain',
    cancelError: new Error('PRIVATE BODY CANCEL FAILURE'),
  });
  const cartesiaCalls = [];
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out: cartesiaOut, operationId: 'first', config: config(), log: () => {},
      fetchImpl: async (url, init) => {
        cartesiaCalls.push(url);
        if (cartesiaCalls.length === 1) return elevenErrorResponse(429, {type: 'rate_limit_error', code: 'rate_limit_exceeded'});
        cartesiaStream.observeRequest(init);
        return cartesiaStream.response;
      },
    }),
    (error) => error.provider === 'cartesia' && error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(cartesiaCalls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
  assert.equal(cartesiaStream.stats.bodyCancelCalls, 1);
  assert.equal(cartesiaStream.stats.abortCalls, 1);
  assert.equal(fs.existsSync(lockPathFor(cartesiaOut)), false);
});

test('never-settling reader and body cleanup cannot delay Eleven or Cartesia semantic failures', async () => {
  const elevenOut = path.join(runDir('never-settling-eleven-reader-cancel'), 'narration.mp3');
  const elevenStream = streamedResponse({
    ok: false,
    status: 400,
    contentType: 'text/plain',
    cancelNeverSettles: true,
  });
  const elevenCalls = [];
  await rejectsPromptly(
    narrate({
      text: 'A solemn dispatch.', out: elevenOut, operationId: 'first', config: config(), log: () => {},
      fetchImpl: async (url, init) => { elevenCalls.push(url); elevenStream.observeRequest(init); return elevenStream.response; },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(elevenCalls, ['https://eleven.test/tts']);
  assert.equal(elevenStream.stats.cancelCalls, 1);
  assert.equal(elevenStream.stats.abortCalls, 1);
  assert.equal(elevenStream.stats.abortCallsWhenCancelStarted, 1);
  assert.equal(fs.existsSync(lockPathFor(elevenOut)), false);

  const cartesiaOut = path.join(runDir('never-settling-cartesia-body-cancel'), 'narration.mp3');
  const cartesiaStream = bodyCancelableResponse({status: 400, cancelNeverSettles: true});
  const cartesiaCalls = [];
  await rejectsPromptly(
    narrate({
      text: 'A solemn dispatch.', out: cartesiaOut, operationId: 'first', config: config(), log: () => {},
      fetchImpl: async (url, init) => {
        cartesiaCalls.push(url);
        if (cartesiaCalls.length === 1) {
          return elevenErrorResponse(429, {type: 'rate_limit_error', code: 'rate_limit_exceeded'});
        }
        cartesiaStream.observeRequest(init);
        return cartesiaStream.response;
      },
    }),
    (error) => error.provider === 'cartesia' && error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(cartesiaCalls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
  assert.equal(cartesiaStream.stats.bodyCancelCalls, 1);
  assert.equal(cartesiaStream.stats.abortCalls, 1);
  assert.equal(cartesiaStream.stats.abortCallsWhenCancelStarted, 1);
  assert.equal(fs.existsSync(lockPathFor(cartesiaOut)), false);
});

test('definitive quota failure calls Cartesia once with the official bytes MP3 request', async () => {
  const calls = [];
  const dir = runDir('fallback');
  const out = path.join(dir, 'narration.mp3');
  const receipt = await narrate({
    text: 'A solemn dispatch.', out, operationId: 'fallback', config: config(), log: () => {},
    fetchImpl: async (url, init) => {
      calls.push({url, init});
      return calls.length === 1
        ? elevenErrorResponse(429, {type: 'rate_limit_error', code: 'rate_limit_exceeded', requestId: 'eleven-capacity'})
        : audioResponse(validAudio, 'cartesia-complete');
    },
  });
  assert.equal(calls.length, 2);
  assert.equal(calls[1].url, 'https://cartesia.test/tts/bytes');
  assert.equal(calls[1].init.headers.Authorization, 'Bearer sk_car_1234567890abcdefghij');
  assert.equal(calls[1].init.headers['Cartesia-Version'], '2026-08-14');
  const payload = JSON.parse(calls[1].init.body);
  assert.deepEqual(payload.output_format, {container: 'mp3', sample_rate: 44100, bit_rate: 128000});
  assert.equal(payload.voice, 'verified-by-runtime-config');
  assert.equal(receipt.selection.provider, 'cartesia');
  assert.equal(isDecodableMp3(out), true);
});

test('current Eleven 402 insufficient-credit envelope falls back once and recovers without another provider call', async () => {
  const calls = [];
  const out = path.join(runDir('current-insufficient-credits'), 'narration.mp3');
  const initial = await narrate({
    text: 'A solemn dispatch.', out, operationId: 'current-insufficient-credits', config: config(), log: () => {},
    fetchImpl: async (url) => {
      calls.push(url);
      return calls.length === 1
        ? elevenErrorResponse(402, {type: 'payment_required', code: 'insufficient_credits'})
        : audioResponse();
    },
  });
  assert.deepEqual(calls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
  assert.equal(initial.selection.provider, 'cartesia');
  assert.equal(isDecodableMp3(out), true);
  assert.deepEqual(initial.attempts[0], {
    provider: 'eleven',
    model: 'eleven_multilingual_v2',
    voice: 'HvjKMFO0rjuPaM2f997g',
    fallback_class: 'capacity_or_availability',
    request_id: 'safe-request-id',
    http_status: 402,
    error_type: 'payment_required',
    error_code: 'insufficient_credits',
  });

  const recovered = await narrate({
    text: 'A solemn dispatch.', out, operationId: 'current-insufficient-credits', config: config(), log: () => {},
    fetchImpl: async () => { throw new Error('recovery must not call a provider'); },
  });
  assert.equal(recovered.selection.provider, 'cartesia');
  assert.equal(calls.length, 2);
});

test('legacy Eleven 400/401 quota envelopes fall back only with the exact documented status form', async () => {
  for (const [status, type] of [[400, undefined], [400, 'payment_required'], [401, undefined], [401, 'payment_required']]) {
    const calls = [];
    const out = path.join(runDir(`legacy-quota-${status}-${type || 'no-type'}`), 'narration.mp3');
    const receipt = await narrate({
      text: 'A solemn dispatch.', out, operationId: `legacy-quota-${status}-${type || 'no-type'}`, config: config(), log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return calls.length === 1
          ? elevenErrorResponse(status, {type, legacyStatus: 'quota_exceeded'})
          : audioResponse();
      },
    });
    assert.deepEqual(calls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
    assert.equal(receipt.selection.provider, 'cartesia');
    assert.deepEqual(receipt.attempts[0], {
      provider: 'eleven',
      model: 'eleven_multilingual_v2',
      voice: 'HvjKMFO0rjuPaM2f997g',
      fallback_class: 'capacity_or_availability',
      request_id: 'safe-request-id',
      http_status: status,
      ...(type ? {error_type: type} : {}),
      error_code: 'quota_exceeded',
    });
  }
});

test('near-miss current and legacy Eleven envelopes fail closed without Cartesia', async () => {
  const rejectedCases = [
    () => elevenErrorResponse(400, {type: 'payment_required', code: 'insufficient_credits'}),
    () => elevenErrorResponse(401, {type: 'payment_required', code: 'insufficient_credits'}),
    () => elevenErrorResponse(402, {type: 'authentication_error', code: 'insufficient_credits'}),
    () => elevenErrorResponse(402, {type: 'payment_required', code: 'invalid_api_key'}),
    () => elevenErrorResponse(402, {type: 'payment_required'}),
    () => elevenErrorResponse(402, {type: 'payment_required', code: 'insufficient_credits', legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(402, {type: 'payment_required', code: 123, legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(402, {legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(400, {type: 'authentication_error', legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(401, {type: 'authentication_error', legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(401, {type: 123, legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(429, {legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(400, {legacyStatus: 'invalid_api_key'}),
    () => elevenErrorResponse(401, {code: 'invalid_api_key', legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(503, {legacyStatus: 'quota_exceeded'}),
    () => elevenErrorResponse(503, {type: 'authentication_error', legacyStatus: 'service_unavailable'}),
    () => elevenErrorResponse(503, {legacyStatus: 'not_available'}),
    () => elevenErrorResponse(503, {legacyStatus: 123}),
    () => elevenErrorResponse(503, {type: 'service_unavailable', code: 'service_unavailable', legacyStatus: 'maintenance'}),
    () => new Response('{not json', {status: 402, headers: {'content-type': 'application/json'}}),
  ];
  for (const [index, response] of rejectedCases.entries()) {
    const calls = [];
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out: path.join(runDir(`rejected-credit-envelope-${index}`), 'narration.mp3'),
        operationId: `rejected-credit-envelope-${index}`, config: config(), log: () => {},
        fetchImpl: async (url) => { calls.push(url); return response(); },
      }),
      (error) => error.provider === 'eleven' && error.fallbackClass === 'nonretryable',
    );
    assert.deepEqual(calls, ['https://eleven.test/tts']);
  }
});

test('Eleven fallback classification ignores inherited non-enumerable error fields', async () => {
  const inheritedCases = [
    {
      body: {detail: {code: 'insufficient_credits'}},
      name: 'type',
      status: 402,
      value: 'payment_required',
    },
    {
      body: {detail: {}},
      name: 'status',
      status: 400,
      value: 'quota_exceeded',
    },
    {
      body: {},
      name: 'detail',
      status: 401,
      value: {status: 'quota_exceeded'},
    },
  ];
  for (const [index, inherited] of inheritedCases.entries()) {
    const calls = [];
    const out = path.join(runDir(`inherited-envelope-${index}`), 'narration.mp3');
    await withInheritedObjectProperty(inherited.name, inherited.value, async () => {
      await assert.rejects(
        narrate({
          text: 'A solemn dispatch.', out,
          operationId: `inherited-envelope-${index}`, config: config(), log: () => {},
          fetchImpl: async (url) => { calls.push(url); return jsonResponse(inherited.status, inherited.body); },
        }),
        (error) => error.provider === 'eleven' && error.fallbackClass === 'nonretryable',
      );
    });
    assert.deepEqual(calls, ['https://eleven.test/tts']);
    const attempt = JSON.parse(fs.readFileSync(`${out}.receipt.json`, 'utf8')).attempts[0];
    assert.equal(attempt.http_status, inherited.status);
    assert.equal(Object.hasOwn(attempt, 'error_type'), false);
    assert.equal(Object.hasOwn(attempt, 'error_code'), index === 0);
    if (index === 0) assert.equal(attempt.error_code, 'insufficient_credits');
  }
});

test('failed-attempt diagnostics omit invalid status and malformed safe-token candidates', async () => {
  const malformedCases = [
    {name: 'cased', status: 402, type: 'Payment_Required', code: 'INSUFFICIENT_CREDITS'},
    {name: 'whitespace', status: 402, type: ' payment_required ', code: ' insufficient_credits '},
    {name: 'oversized', status: 402, type: `a${'b'.repeat(128)}`, code: `c${'d'.repeat(128)}`},
    {name: 'invalid-http-status', status: 99, type: 'payment_required', code: 'insufficient_credits'},
  ];
  for (const {name, status, type, code} of malformedCases) {
    const calls = [];
    const out = path.join(runDir(`malformed-diagnostics-${name}`), 'narration.mp3');
    const body = {detail: {type, code, request_id: 'safe-malformed-request'}};
    const response = status === 99
      ? {
        ok: false,
        status,
        headers: new Headers({'content-type': 'application/json', 'x-request-id': 'safe-malformed-request'}),
        arrayBuffer: async () => Buffer.from(JSON.stringify(body)),
      }
      : jsonResponse(status, body, 'safe-malformed-request');
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out, operationId: `malformed-diagnostics-${name}`,
        config: config(), log: () => {},
        fetchImpl: async (url) => { calls.push(url); return response; },
      }),
      (error) => error.provider === 'eleven' && error.fallbackClass === 'nonretryable',
    );
    assert.deepEqual(calls, ['https://eleven.test/tts']);
    const attempt = JSON.parse(fs.readFileSync(`${out}.receipt.json`, 'utf8')).attempts[0];
    assert.equal(Object.hasOwn(attempt, 'http_status'), status !== 99);
    assert.equal(Object.hasOwn(attempt, 'error_type'), status === 99);
    assert.equal(Object.hasOwn(attempt, 'error_code'), status === 99);
  }
});

test('Eleven auth/input failure is nonretryable and never calls Cartesia', async () => {
  const calls = [];
  const out = path.join(runDir('nonretryable'), 'narration.mp3');
  const text = 'PRIVATE DISPATCH MUST NOT PERSIST';
  const providerMessage = 'PRIVATE PROVIDER MESSAGE MUST NOT PERSIST';
  const nestedBody = 'PRIVATE RAW BODY MUST NOT PERSIST';
  const credentialShaped = `sk_${'live'}_${'x'.repeat(48)}`;
  await assert.rejects(
    narrate({
      text, out, operationId: 'nonretryable', config: config(), log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return jsonResponse(401, {
          detail: {
            type: 'authentication_error',
            code: 'invalid_api_key',
            request_id: 'unsafe request/id',
            message: providerMessage,
            body: {raw: nestedBody},
            api_key: credentialShaped,
          },
        }, 'eleven.auth-request-1');
      },
    }),
    (error) => error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(fs.existsSync(out), false);
  const receiptBody = fs.readFileSync(`${out}.receipt.json`, 'utf8');
  const receipt = JSON.parse(receiptBody);
  assert.equal(receipt.state, 'primary_failed');
  assert.deepEqual(receipt.attempts[0], {
    provider: 'eleven',
    model: 'eleven_multilingual_v2',
    voice: 'HvjKMFO0rjuPaM2f997g',
    fallback_class: 'nonretryable',
    request_id: 'eleven.auth-request-1',
    http_status: 401,
    error_type: 'authentication_error',
    error_code: 'invalid_api_key',
  });
  for (const forbidden of [text, providerMessage, nestedBody, credentialShaped]) {
    assert.equal(receiptBody.includes(forbidden), false);
  }
  assert.doesNotMatch(receiptBody, /"(?:message|body|api_key)":/);
});

test('auth, config, input, and other 4xx errors never fall back even with capacity-looking codes', async () => {
  for (const [status, code] of [[400, 'quota_exceeded'], [401, 'quota_exceeded'], [403, 'concurrency_limited'], [404, 'service_unavailable']]) {
    const calls = [];
    const out = path.join(runDir(`contradictory-${status}`), 'narration.mp3');
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out, operationId: `contradictory-${status}`, config: config(), log: () => {},
        fetchImpl: async (url) => {
          calls.push(url);
          return elevenErrorResponse(status, {type: 'authentication_error', code});
        },
      }),
      (error) => error.fallbackClass === 'nonretryable',
    );
    assert.deepEqual(calls, ['https://eleven.test/tts']);
    assert.equal(fs.existsSync(out), false);
  }
});

test('429 fallback requires a structured allowlisted capacity code', async () => {
  const recognizedCalls = [];
  const recognized = await narrate({
    text: 'A solemn dispatch.', out: path.join(runDir('recognized-429'), 'narration.mp3'), operationId: 'recognized-429', config: config(), log: () => {},
    fetchImpl: async (url) => {
      recognizedCalls.push(url);
      return recognizedCalls.length === 1
        ? elevenErrorResponse(429, {type: 'rate_limit_error', code: 'concurrent_limit_exceeded'})
        : audioResponse();
    },
  });
  assert.deepEqual(recognizedCalls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
  assert.equal(recognized.selection.provider, 'cartesia');

  const rejectedCases = [
    () => elevenErrorResponse(429, {type: 'authentication_error', code: 'rate_limit_exceeded'}),
    () => elevenErrorResponse(429, {type: 'rate_limit_error', code: 'unknown_provider_error'}),
    () => elevenErrorResponse(429, {type: 'rate_limit_error'}),
    () => elevenErrorResponse(429, {type: 'rate_limit_error', code: 123, legacyStatus: 'system_busy'}),
    () => new Response('{not json', {status: 429, headers: {'content-type': 'application/json'}}),
  ];
  for (const [index, response] of rejectedCases.entries()) {
    const calls = [];
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out: path.join(runDir(`rejected-429-${index}`), 'narration.mp3'), operationId: `rejected-429-${index}`,
        config: config(), log: () => {}, fetchImpl: async (url) => { calls.push(url); return response(); },
      }),
      (error) => error.fallbackClass === 'nonretryable',
    );
    assert.deepEqual(calls, ['https://eleven.test/tts']);
  }
});

test('malformed JSON SyntaxError is an ordinary nonfallback failure', async () => {
  const out = path.join(runDir('malformed-json'), 'narration.mp3');
  const calls = [];
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out, operationId: 'malformed-json', config: config(), log: () => {},
      fetchImpl: async (url) => { calls.push(url); return new Response('{not json', {status: 503, headers: {'content-type': 'application/json'}}); },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(fs.existsSync(lockPathFor(out)), false);
});

test('unclassified 5xx errors fail closed, while structured availability falls back once', async () => {
  const malformedCases = [
    () => new Response('gateway exploded', {status: 503, headers: {'content-type': 'text/plain'}}),
    () => elevenErrorResponse(503, {type: 'service_unavailable', code: 'something_else'}),
  ];
  for (const [index, response] of malformedCases.entries()) {
    const calls = [];
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out: path.join(runDir(`bad-5xx-${index}`), 'narration.mp3'), operationId: `bad-5xx-${index}`,
        config: config(), log: () => {}, fetchImpl: async (url) => { calls.push(url); return response(); },
      }),
      (error) => error.fallbackClass === 'nonretryable',
    );
    assert.deepEqual(calls, ['https://eleven.test/tts']);
  }

  const calls = [];
  const receipt = await narrate({
    text: 'A solemn dispatch.', out: path.join(runDir('structured-5xx'), 'narration.mp3'), operationId: 'structured-5xx',
    config: config(), log: () => {},
    fetchImpl: async (url) => {
      calls.push(url);
      return calls.length === 1
        ? elevenErrorResponse(503, {type: 'service_unavailable', code: 'service_unavailable'})
        : audioResponse();
    },
  });
  assert.deepEqual(calls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
  assert.equal(receipt.selection.provider, 'cartesia');
});

test('Cartesia failure fails closed and never leaves a final artifact', async () => {
  const calls = [];
  const out = path.join(runDir('cartesia-failure'), 'narration.mp3');
  const providerMessage = 'PRIVATE CARTESIA MESSAGE MUST NOT PERSIST';
  const credentialShaped = `sk_${'car'}_${'x'.repeat(48)}`;
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out, operationId: 'cartesia-failure', config: config(), log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return calls.length === 1
          ? elevenErrorResponse(503, {type: 'service_unavailable', code: 'service_unavailable'})
          : jsonResponse(401, {
            error_type: 'authentication_error',
            error_code: 'unauthorized',
            request_id: 'cartesia.failure-1',
            message: providerMessage,
            authorization: credentialShaped,
          }, 'cartesia.failure-1');
      },
    }),
    (error) => error.provider === 'cartesia',
  );
  assert.equal(calls.length, 2);
  assert.equal(fs.existsSync(out), false);
  const receiptBody = fs.readFileSync(`${out}.receipt.json`, 'utf8');
  const receipt = JSON.parse(receiptBody);
  assert.equal(receipt.state, 'failed');
  assert.deepEqual(receipt.attempts[1], {
    provider: 'cartesia',
    model: 'sonic-3.6',
    voice: 'verified-by-runtime-config',
    fallback_class: 'nonretryable',
    request_id: 'cartesia.failure-1',
    http_status: 401,
    error_type: 'authentication_error',
    error_code: 'unauthorized',
  });
  for (const forbidden of [providerMessage, credentialShaped]) {
    assert.equal(receiptBody.includes(forbidden), false);
  }
  assert.doesNotMatch(receiptBody, /"(?:message|authorization)":/);
});

test('Cartesia non-plain error bodies retain only safe header request IDs', async () => {
  const cases = [
    {name: 'safe', requestId: 'cartesia.header-1', expectedRequestId: 'cartesia.header-1'},
    {name: 'unsafe', requestId: 'cartesia header/secret', expectedRequestId: undefined},
  ];
  for (const {name, requestId, expectedRequestId} of cases) {
    const calls = [];
    const out = path.join(runDir(`cartesia-non-plain-${name}`), 'narration.mp3');
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out, operationId: `cartesia-non-plain-${name}`,
        config: config(), log: () => {},
        fetchImpl: async (url) => {
          calls.push(url);
          return calls.length === 1
            ? elevenErrorResponse(503, {type: 'service_unavailable', code: 'service_unavailable'})
            : jsonResponse(502, [], requestId);
        },
      }),
      (error) => error.provider === 'cartesia' && error.fallbackClass === 'nonretryable',
    );
    assert.deepEqual(calls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
    const receiptBody = fs.readFileSync(`${out}.receipt.json`, 'utf8');
    const attempt = JSON.parse(receiptBody).attempts[1];
    assert.equal(attempt.http_status, 502);
    assert.equal(attempt.request_id, expectedRequestId);
    if (expectedRequestId === undefined) assert.equal(receiptBody.includes(requestId), false);
  }
});

test('ambiguous transport keeps its operation lock and cannot double-generate', async () => {
  const dir = runDir('idempotency');
  const out = path.join(dir, 'narration.mp3');
  let calls = 0;
  const ambiguousFetch = async () => { calls += 1; throw new Error('socket reset'); };
  await assert.rejects(narrate({text: 'A solemn dispatch.', out, operationId: 'same', config: config(), log: () => {}, fetchImpl: ambiguousFetch}));
  await assert.rejects(narrate({text: 'A solemn dispatch.', out, operationId: 'same', config: config(), log: () => {}, fetchImpl: ambiguousFetch}), /already active or ambiguous/);
  assert.equal(calls, 1);
});

test('Eleven non-OK error-body read ambiguity retains the output claim', async () => {
  const out = path.join(runDir('eleven-error-body-read'), 'narration.mp3');
  let calls = 0;
  const unreadableFetch = async () => { calls += 1; return unreadableJsonResponse(500); };
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'first', config: config(), log: () => {}, fetchImpl: unreadableFetch}),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'ambiguous_transport',
  );
  const receipt = JSON.parse(fs.readFileSync(`${out}.receipt.json`, 'utf8'));
  assert.equal(receipt.state, 'primary_failed');
  assert.equal(receipt.attempts[0].fallback_class, 'ambiguous_transport');
  assert.equal(fs.existsSync(lockPathFor(out)), true);
  for (const [operationId, text] of [['first', 'A solemn dispatch.'], ['different', 'A different dispatch.']]) {
    await assert.rejects(
      narrate({text, out, operationId, config: config(), log: () => {}, fetchImpl: unreadableFetch}),
      (error) => error.fallbackClass === 'operation_locked',
    );
  }
  assert.equal(calls, 1);
});

test('Cartesia non-OK error-body read ambiguity retains the output claim', async () => {
  const out = path.join(runDir('cartesia-error-body-read'), 'narration.mp3');
  let calls = 0;
  const fallbackWithUnreadableErrorBody = async () => {
    calls += 1;
    return calls === 1
      ? elevenErrorResponse(503, {type: 'service_unavailable', code: 'service_unavailable'})
      : unreadableJsonResponse(500);
  };
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'first', config: config(), log: () => {}, fetchImpl: fallbackWithUnreadableErrorBody}),
    (error) => error.provider === 'cartesia' && error.fallbackClass === 'ambiguous_transport',
  );
  const receipt = JSON.parse(fs.readFileSync(`${out}.receipt.json`, 'utf8'));
  assert.equal(receipt.state, 'failed');
  assert.equal(receipt.attempts[1].fallback_class, 'ambiguous_transport');
  assert.equal(fs.existsSync(lockPathFor(out)), true);
  for (const [operationId, text] of [['first', 'A solemn dispatch.'], ['different', 'A different dispatch.']]) {
    await assert.rejects(
      narrate({text, out, operationId, config: config(), log: () => {}, fetchImpl: fallbackWithUnreadableErrorBody}),
      (error) => error.fallbackClass === 'operation_locked',
    );
  }
  assert.equal(calls, 2);
});

test('Eleven response-body read ambiguity retains the output claim for every operation', async () => {
  const out = path.join(runDir('eleven-body-read'), 'narration.mp3');
  let calls = 0;
  const unreadableFetch = async () => { calls += 1; return unreadableAudioResponse(); };
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'first', config: config(), log: () => {}, fetchImpl: unreadableFetch}),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'ambiguous_transport',
  );
  const receipt = JSON.parse(fs.readFileSync(`${out}.receipt.json`, 'utf8'));
  assert.equal(receipt.state, 'primary_failed');
  assert.equal(receipt.attempts[0].fallback_class, 'ambiguous_transport');
  assert.equal(fs.existsSync(lockPathFor(out)), true);
  for (const [operationId, text] of [['first', 'A solemn dispatch.'], ['different', 'A different dispatch.']]) {
    await assert.rejects(
      narrate({text, out, operationId, config: config(), log: () => {}, fetchImpl: unreadableFetch}),
      (error) => error.fallbackClass === 'operation_locked',
    );
  }
  assert.equal(calls, 1);
  assert.equal(fs.existsSync(out), false);
});

test('Cartesia response-body read ambiguity retains the output claim for every operation', async () => {
  const out = path.join(runDir('cartesia-body-read'), 'narration.mp3');
  let calls = 0;
  const fallbackWithUnreadableBody = async () => {
    calls += 1;
    return calls === 1
      ? elevenErrorResponse(429, {type: 'rate_limit_error', code: 'rate_limit_exceeded'})
      : unreadableAudioResponse();
  };
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'first', config: config(), log: () => {}, fetchImpl: fallbackWithUnreadableBody}),
    (error) => error.provider === 'cartesia' && error.fallbackClass === 'ambiguous_transport',
  );
  const receipt = JSON.parse(fs.readFileSync(`${out}.receipt.json`, 'utf8'));
  assert.equal(receipt.state, 'failed');
  assert.equal(receipt.attempts[1].fallback_class, 'ambiguous_transport');
  assert.equal(fs.existsSync(lockPathFor(out)), true);
  for (const [operationId, text] of [['first', 'A solemn dispatch.'], ['different', 'A different dispatch.']]) {
    await assert.rejects(
      narrate({text, out, operationId, config: config(), log: () => {}, fetchImpl: fallbackWithUnreadableBody}),
      (error) => error.fallbackClass === 'operation_locked',
    );
  }
  assert.equal(calls, 2);
  assert.equal(fs.existsSync(out), false);
});

test('completed artifact recovers from a partial receipt without another provider call', async () => {
  const out = path.join(runDir('recovery'), 'narration.mp3');
  let calls = 0;
  await narrate({text: 'A solemn dispatch.', out, operationId: 'new', config: config(), log: () => {}, fetchImpl: async () => { calls += 1; return audioResponse(); }});
  const receiptPath = `${out}.receipt.json`;
  const partialReceipt = JSON.parse(fs.readFileSync(receiptPath, 'utf8'));
  partialReceipt.state = 'primary_started';
  delete partialReceipt.selection;
  fs.writeFileSync(receiptPath, JSON.stringify(partialReceipt));
  const recovered = await narrate({text: 'A solemn dispatch.', out, operationId: 'new', config: config(), log: () => {}, fetchImpl: async () => { throw new Error('must not call'); }});
  assert.equal(recovered.recovered, true);
  assert.equal(calls, 1);
});

test('completed receipt hash mismatch retains the claim without blessing replacement audio', async () => {
  const out = path.join(runDir('receipt-hash-mismatch'), 'narration.mp3');
  const receiptPath = `${out}.receipt.json`;
  let calls = 0;
  const fetchImpl = async () => { calls += 1; return audioResponse(); };
  await narrate({text: 'A solemn dispatch.', out, operationId: 'original', config: config(), log: () => {}, fetchImpl});
  const originalReceipt = fs.readFileSync(receiptPath, 'utf8');
  const originalHash = JSON.parse(originalReceipt).audio_sha256;
  fs.writeFileSync(out, alternateValidAudio);
  assert.equal(isDecodableMp3(out), true);

  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'original', config: config(), log: () => {}, fetchImpl}),
    (error) => error.fallbackClass === 'receipt_integrity',
  );
  assert.equal(calls, 1);
  assert.equal(fs.readFileSync(receiptPath, 'utf8'), originalReceipt);
  assert.equal(JSON.parse(fs.readFileSync(receiptPath, 'utf8')).audio_sha256, originalHash);
  const lock = JSON.parse(fs.readFileSync(lockPathFor(out), 'utf8'));
  assert.equal(lock.phase, 'receipt_integrity_hash_mismatch');
  assert.equal(lock.expected_audio_sha256, originalHash);
  assert.match(lock.actual_audio_sha256, /^[a-f0-9]{64}$/);
  assert.notEqual(lock.actual_audio_sha256, originalHash);

  await assert.rejects(
    narrate({text: 'A different dispatch.', out, operationId: 'different', config: config(), log: () => {}, fetchImpl}),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(calls, 1);
  assert.equal(isDecodableMp3(out), true);
});

test('completed artifact over maxAudioBytes is rejected before ffprobe or hashing and retains its claim', async () => {
  const out = path.join(runDir('receipt-too-large'), 'narration.mp3');
  const receiptPath = `${out}.receipt.json`;
  const maxAudioBytes = 1024;
  assert.ok(largeValidAudio.length > maxAudioBytes);
  let calls = 0;
  const fetchImpl = async () => { calls += 1; return audioResponse(largeValidAudio); };
  await narrate({text: 'A solemn dispatch.', out, operationId: 'original', config: config(), log: () => {}, fetchImpl});
  const originalReceipt = fs.readFileSync(receiptPath, 'utf8');
  const originalHash = JSON.parse(originalReceipt).audio_sha256;
  let ffprobeCalls = 0;
  const noProbe = () => {
    ffprobeCalls += 1;
    throw new Error('ffprobe must not run for an oversized artifact');
  };
  const boundedConfig = config({limits: {maxAudioBytes}});

  assert.equal(isDecodableMp3(out, boundedConfig.limits, noProbe), false);
  assert.equal(ffprobeCalls, 0);
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'original', config: boundedConfig, log: () => {}, fetchImpl, ffprobeImpl: noProbe}),
    (error) => error.fallbackClass === 'receipt_integrity',
  );
  assert.equal(calls, 1);
  assert.equal(ffprobeCalls, 0);
  assert.equal(fs.readFileSync(receiptPath, 'utf8'), originalReceipt);
  const lock = JSON.parse(fs.readFileSync(lockPathFor(out), 'utf8'));
  assert.equal(lock.phase, 'receipt_integrity_artifact_too_large');
  assert.equal(lock.artifact_size_bytes, largeValidAudio.length);
  assert.equal(lock.max_audio_bytes, maxAudioBytes);
  assert.match(lock.output_identity, /^[a-f0-9]{64}$/);
  assert.equal(lock.expected_audio_sha256, originalHash);
  assert.equal(lock.actual_audio_sha256, undefined);
  const sanitized = JSON.stringify(lock);
  assert.equal(sanitized.includes(out), false);
  assert.equal(sanitized.includes('A solemn dispatch.'), false);

  for (const [operationId, text] of [['original', 'A solemn dispatch.'], ['different', 'A different dispatch.']]) {
    await assert.rejects(
      narrate({text, out, operationId, config: boundedConfig, log: () => {}, fetchImpl, ffprobeImpl: noProbe}),
      (error) => error.fallbackClass === 'operation_locked',
    );
  }
  assert.equal(calls, 1);
  assert.equal(ffprobeCalls, 0);
});

test('completed receipt missing its durable hash retains the claim without provider calls', async () => {
  const out = path.join(runDir('receipt-missing-hash'), 'narration.mp3');
  const receiptPath = `${out}.receipt.json`;
  let calls = 0;
  const fetchImpl = async () => { calls += 1; return audioResponse(); };
  await narrate({text: 'A solemn dispatch.', out, operationId: 'original', config: config(), log: () => {}, fetchImpl});
  const receipt = JSON.parse(fs.readFileSync(receiptPath, 'utf8'));
  delete receipt.audio_sha256;
  fs.writeFileSync(receiptPath, `${JSON.stringify(receipt, null, 2)}\n`);
  const missingHashReceipt = fs.readFileSync(receiptPath, 'utf8');

  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'original', config: config(), log: () => {}, fetchImpl}),
    (error) => error.fallbackClass === 'receipt_integrity',
  );
  assert.equal(calls, 1);
  assert.equal(fs.readFileSync(receiptPath, 'utf8'), missingHashReceipt);
  assert.equal(JSON.parse(fs.readFileSync(lockPathFor(out), 'utf8')).phase, 'receipt_integrity_missing_hash');

  await assert.rejects(
    narrate({text: 'A different dispatch.', out, operationId: 'different', config: config(), log: () => {}, fetchImpl}),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(calls, 1);
});

test('concurrent same and different operations share one exclusive output claim', async () => {
  const out = path.join(runDir('concurrent'), 'narration.mp3');
  let calls = 0;
  let releaseFirst;
  const first = narrate({
    text: 'First dispatch.', out, operationId: 'first', config: config(), log: () => {},
    fetchImpl: async () => {
      calls += 1;
      await new Promise((resolve) => { releaseFirst = resolve; });
      return audioResponse();
    },
  });
  while (!releaseFirst) await new Promise((resolve) => setImmediate(resolve));
  const [same, different] = await Promise.allSettled([
    narrate({text: 'First dispatch.', out, operationId: 'first', config: config(), log: () => {}, fetchImpl: async () => { throw new Error('must not call'); }}),
    narrate({text: 'Different dispatch.', out, operationId: 'different', config: config(), log: () => {}, fetchImpl: async () => { throw new Error('must not call'); }}),
  ]);
  assert.equal(same.status, 'rejected');
  assert.equal(different.status, 'rejected');
  assert.equal(same.reason.fallbackClass, 'operation_locked');
  assert.equal(different.reason.fallbackClass, 'operation_locked');
  assert.equal(calls, 1);
  releaseFirst();
  const completed = await first;
  assert.equal(completed.selection.provider, 'eleven');
  assert.equal(isDecodableMp3(out), true);
});

test('invalid successful audio does not trigger fallback and is not published', async () => {
  const calls = [];
  const out = path.join(runDir('invalid-audio'), 'narration.mp3');
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out, operationId: 'invalid', config: config(), log: () => {},
      fetchImpl: async (url) => { calls.push(url); return audioResponse(Buffer.from('not mp3')); },
    }),
    (error) => error.fallbackClass === 'invalid_audio',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(fs.existsSync(out), false);
});

test('runtime config rejects admin/malformed keys and invalid I/O limits before network use', async () => {
  assert.throws(() => resolveConfig({ELEVENLABS_API_KEY: 'eleven', CARTESIA_API_KEY: 'sk_car_admin_dont-use-me'}), /not an admin key/);
  assert.throws(() => resolveConfig({ELEVENLABS_API_KEY: 'eleven', CARTESIA_API_KEY: 'legacy-key'}), /standard Cartesia/);
  assert.throws(
    () => resolveConfig({ELEVENLABS_API_KEY: 'eleven', SLOWBURNS_NARRATION_REQUEST_TIMEOUT_MS: '0'}),
    /SLOWBURNS_NARRATION_REQUEST_TIMEOUT_MS/,
  );
  let calls = 0;
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out: path.join(runDir('invalid-limits'), 'narration.mp3'), operationId: 'invalid-limits',
      config: config({limits: {maxAudioBytes: 0}}), log: () => {},
      fetchImpl: async () => { calls += 1; return audioResponse(); },
    }),
    (error) => error.fallbackClass === 'configuration',
  );
  assert.equal(calls, 0);
});

test('receipt is sanitized and never contains transcript or raw provider body', async () => {
  const text = 'PRIVATE DISPATCH TEXT MUST NOT APPEAR';
  const dir = runDir('receipt');
  const out = path.join(dir, 'narration.mp3');
  await narrate({
    text, out, operationId: 'receipt', config: config(), log: () => {},
    fetchImpl: async () => audioResponse(validAudio, 'safe.receipt-1'),
  });
  const body = fs.readFileSync(`${out}.receipt.json`, 'utf8');
  assert.match(body, /"provider": "eleven"/);
  assert.match(body, /"request_id": "safe.receipt-1"/);
  assert.doesNotMatch(body, new RegExp(text));
  assert.doesNotMatch(body, /xi-api-key|Authorization|raw provider body/i);
});

test('legacy Eleven 429 detail.status capacity envelopes remain strictly eligible', async () => {
  for (const legacyStatus of ['too_many_concurrent_requests', 'system_busy']) {
    const calls = [];
    const out = path.join(runDir(`legacy-eleven-${legacyStatus}`), 'narration.mp3');
    const receipt = await narrate({
      text: 'A solemn dispatch.', out, operationId: legacyStatus, config: config(), log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return calls.length === 1
          ? elevenErrorResponse(429, {legacyStatus, requestId: `legacy-${legacyStatus}`})
          : audioResponse();
      },
    });
    assert.deepEqual(calls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
    assert.equal(receipt.selection.provider, 'cartesia');
  }
});

test('current and legacy Eleven 429 codes cannot cross error-envelope families', async () => {
  const rejectedCases = [
    () => elevenErrorResponse(429, {type: 'rate_limit_error', code: 'too_many_concurrent_requests'}),
    () => elevenErrorResponse(429, {type: 'rate_limit_error', code: 'system_busy'}),
    () => elevenErrorResponse(429, {type: 'rate_limit_error', legacyStatus: 'rate_limit_exceeded'}),
    () => elevenErrorResponse(429, {type: 'rate_limit_error', legacyStatus: 'concurrent_limit_exceeded'}),
  ];
  for (const [index, response] of rejectedCases.entries()) {
    const calls = [];
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out: path.join(runDir(`crossed-429-${index}`), 'narration.mp3'),
        operationId: `crossed-429-${index}`, config: config(), log: () => {},
        fetchImpl: async (url) => { calls.push(url); return response(); },
      }),
      (error) => error.provider === 'eleven' && error.fallbackClass === 'nonretryable',
    );
    assert.deepEqual(calls, ['https://eleven.test/tts']);
  }
});

test('legacy Eleven 503 detail.status availability envelopes remain strictly eligible', async () => {
  for (const [legacyStatus, type] of [
    ['service_unavailable', undefined],
    ['service_unavailable', 'service_unavailable'],
    ['maintenance', undefined],
    ['maintenance', 'service_unavailable'],
  ]) {
    const calls = [];
    const out = path.join(runDir(`legacy-eleven-503-${legacyStatus}-${type || 'no-type'}`), 'narration.mp3');
    const receipt = await narrate({
      text: 'A solemn dispatch.', out, operationId: `legacy-503-${legacyStatus}-${type || 'no-type'}`, config: config(), log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return calls.length === 1
          ? elevenErrorResponse(503, {type, legacyStatus})
          : audioResponse();
      },
    });
    assert.deepEqual(calls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
    assert.equal(receipt.selection.provider, 'cartesia');
  }
});

test('a canonical output claim blocks concurrent callers using different receipt paths', async () => {
  const dir = runDir('canonical-output-claim');
  const out = path.join(dir, 'narration.mp3');
  const firstReceipt = path.join(dir, 'first.receipt.json');
  const secondReceipt = path.join(dir, 'second.receipt.json');
  let calls = 0;
  let releaseFirst;
  const first = narrate({
    text: 'First dispatch.', out, receiptPath: firstReceipt, operationId: 'first', config: config(), log: () => {},
    fetchImpl: async () => {
      calls += 1;
      await new Promise((resolve) => { releaseFirst = resolve; });
      return audioResponse();
    },
  });
  while (!releaseFirst) await new Promise((resolve) => setImmediate(resolve));
  assert.equal(fs.existsSync(lockPathFor(out)), true);
  await assert.rejects(
    narrate({
      text: 'Second dispatch.', out, receiptPath: secondReceipt, operationId: 'second', config: config(), log: () => {},
      fetchImpl: async () => { calls += 1; return audioResponse(); },
    }),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(calls, 1);
  assert.equal(fs.existsSync(secondReceipt), false);
  releaseFirst();
  await first;
  assert.equal(isDecodableMp3(out), true);
  assert.equal(fs.existsSync(firstReceipt), true);
  assert.equal(fs.existsSync(secondReceipt), false);
});

test('receipt paths cannot collide with the canonical output claim', async () => {
  const out = path.join(runDir('receipt-path-collision'), 'narration.mp3');
  let calls = 0;
  for (const receiptPath of [out, lockPathFor(out)]) {
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out, receiptPath, operationId: `collision-${receiptPath}`, config: config(), log: () => {},
        fetchImpl: async () => { calls += 1; return audioResponse(); },
      }),
      (error) => error.fallbackClass === 'configuration',
    );
  }
  assert.equal(calls, 0);
  assert.equal(fs.existsSync(lockPathFor(out)), false);
});

test('request timeout retains a redacted phase-aware claim and blocks every later operation', async () => {
  const text = 'PRIVATE TRANSCRIPT MUST NOT ENTER THE LOCK';
  const out = path.join(runDir('request-timeout'), 'narration.mp3');
  let calls = 0;
  const timeoutConfig = config({limits: {requestTimeoutMs: 10}});
  const hangingFetch = async () => {
    calls += 1;
    return new Promise(() => {});
  };
  await assert.rejects(
    narrate({text, out, operationId: 'first', config: timeoutConfig, log: () => {}, fetchImpl: hangingFetch}),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'ambiguous_transport',
  );
  const rawLock = fs.readFileSync(lockPathFor(out), 'utf8');
  const lock = JSON.parse(rawLock);
  assert.equal(lock.schema_version, 2);
  assert.equal(lock.phase, 'eleven_request_started');
  assert.equal(lock.operator_intervention_required, true);
  assert.equal(lock.retained_reason, 'ambiguous_transport');
  assert.match(lock.operation, /^[a-f0-9]{64}$/);
  assert.match(lock.output_identity, /^[a-f0-9]{64}$/);
  assert.equal(typeof lock.owner_pid, 'number');
  assert.equal(typeof lock.owner_host, 'string');
  assert.ok(lock.owner_host.length > 0);
  assert.ok(Date.parse(lock.created_at));
  assert.ok(Date.parse(lock.updated_at));
  assert.deepEqual(lock.phase_history.map(({phase}) => phase), ['claimed_pre_provider', 'eleven_request_started']);
  assert.equal(rawLock.includes(text), false);
  assert.equal(rawLock.includes(out), false);
  assert.doesNotMatch(rawLock, /eleven-test-key|xi-api-key|Authorization|provider message/i);
  await assert.rejects(
    narrate({text: 'A different dispatch.', out, operationId: 'second', config: timeoutConfig, log: () => {}, fetchImpl: hangingFetch}),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(calls, 1);
});

test('bounded response bodies fail closed on timeout or oversize without a second provider call', async () => {
  const timeoutOut = path.join(runDir('body-timeout'), 'narration.mp3');
  let timeoutCalls = 0;
  const timeoutConfig = config({limits: {bodyReadTimeoutMs: 10}});
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out: timeoutOut, operationId: 'timeout', config: timeoutConfig, log: () => {},
      fetchImpl: async () => { timeoutCalls += 1; return hangingAudioResponse(); },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'ambiguous_transport',
  );
  assert.equal(JSON.parse(fs.readFileSync(lockPathFor(timeoutOut), 'utf8')).phase, 'eleven_audio_body_read_started');
  await assert.rejects(
    narrate({
      text: 'A different dispatch.', out: timeoutOut, operationId: 'second', config: timeoutConfig, log: () => {},
      fetchImpl: async () => { timeoutCalls += 1; return audioResponse(); },
    }),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(timeoutCalls, 1);

  const oversizedErrorOut = path.join(runDir('oversized-error-body'), 'narration.mp3');
  let oversizedErrorCalls = 0;
  const oversizedErrorConfig = config({limits: {maxErrorBodyBytes: 128}});
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out: oversizedErrorOut, operationId: 'oversized-error', config: oversizedErrorConfig, log: () => {},
      fetchImpl: async () => {
        oversizedErrorCalls += 1;
        return {
          ok: false,
          status: 503,
          headers: new Headers({'content-type': 'application/json', 'content-length': '1024'}),
          arrayBuffer: async () => Buffer.from('{"detail":{"type":"service_unavailable","code":"service_unavailable"}}'),
        };
      },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'ambiguous_transport',
  );
  assert.equal(JSON.parse(fs.readFileSync(lockPathFor(oversizedErrorOut), 'utf8')).phase, 'eleven_error_body_read_started');
  await assert.rejects(
    narrate({
      text: 'A different dispatch.', out: oversizedErrorOut, operationId: 'second', config: oversizedErrorConfig, log: () => {},
      fetchImpl: async () => { oversizedErrorCalls += 1; return audioResponse(); },
    }),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(oversizedErrorCalls, 1);

  const oversizedOut = path.join(runDir('oversized-audio'), 'narration.mp3');
  let oversizedCalls = 0;
  const oversizedConfig = config({limits: {maxAudioBytes: validAudio.length - 1}});
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out: oversizedOut, operationId: 'oversized', config: oversizedConfig, log: () => {},
      fetchImpl: async () => { oversizedCalls += 1; return audioResponse(); },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'invalid_audio',
  );
  assert.equal(fs.existsSync(oversizedOut), false);
  assert.equal(JSON.parse(fs.readFileSync(lockPathFor(oversizedOut), 'utf8')).phase, 'eleven_audio_body_read_started');
  await assert.rejects(
    narrate({
      text: 'A different dispatch.', out: oversizedOut, operationId: 'second', config: oversizedConfig, log: () => {},
      fetchImpl: async () => { oversizedCalls += 1; return audioResponse(); },
    }),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.equal(oversizedCalls, 1);
});

test('bounded ffprobe failure keeps the claim and passes its timeout and buffer limits', async () => {
  const out = path.join(runDir('ffprobe-timeout'), 'narration.mp3');
  const limits = {ffprobeTimeoutMs: 9, ffprobeMaxBufferBytes: 4096};
  const calls = [];
  let ffprobeOptions;
  const timedOutFfprobe = (...args) => {
    ffprobeOptions = args[2];
    const error = new Error('ffprobe timeout');
    error.code = 'ETIMEDOUT';
    throw error;
  };
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out, operationId: 'ffprobe', config: config({limits}), log: () => {}, ffprobeImpl: timedOutFfprobe,
      fetchImpl: async (url) => { calls.push(url); return audioResponse(); },
    }),
    (error) => error.provider === 'eleven' && error.fallbackClass === 'invalid_audio',
  );
  assert.equal(ffprobeOptions.timeout, limits.ffprobeTimeoutMs);
  assert.equal(ffprobeOptions.maxBuffer, limits.ffprobeMaxBufferBytes);
  assert.equal(JSON.parse(fs.readFileSync(lockPathFor(out), 'utf8')).phase, 'eleven_audio_validation_started');
  await assert.rejects(
    narrate({
      text: 'A different dispatch.', out, operationId: 'second', config: config({limits}), log: () => {}, ffprobeImpl: timedOutFfprobe,
      fetchImpl: async (url) => { calls.push(url); return audioResponse(); },
    }),
    (error) => error.fallbackClass === 'operation_locked',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts']);
});
