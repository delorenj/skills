import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {isDecodableMp3, narrate, resolveConfig} from '../scripts/narrate.mjs';

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

function jsonResponse(status, body, requestId = 'safe-request-id') {
  return new Response(JSON.stringify(body), {
    status,
    headers: {'content-type': 'application/json', 'x-request-id': requestId},
  });
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
  const receipt = await narrate({
    text: 'A solemn dispatch.', out, operationId: 'primary', config: config(), log: () => {},
    fetchImpl: async (url) => { calls.push(url); return audioResponse(); },
  });
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(receipt.selection.provider, 'eleven');
  assert.equal(isDecodableMp3(out), true);
  assert.ok(fs.statSync(out).size > 0);
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

test('Eleven auth/input failure is nonretryable and never calls Cartesia', async () => {
  const calls = [];
  const out = path.join(runDir('nonretryable'), 'narration.mp3');
  const providerMessage = 'PRIVATE PROVIDER MESSAGE MUST NOT PERSIST';
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out, operationId: 'nonretryable', config: config(), log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return elevenErrorResponse(401, {type: 'authentication_error', code: 'invalid_api_key', message: providerMessage});
      },
    }),
    (error) => error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(fs.existsSync(out), false);
  assert.doesNotMatch(fs.readFileSync(`${out}.receipt.json`, 'utf8'), new RegExp(providerMessage));
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
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out, operationId: 'cartesia-failure', config: config(), log: () => {},
      fetchImpl: async (url) => {
        calls.push(url);
        return calls.length === 1
          ? elevenErrorResponse(503, {type: 'service_unavailable', code: 'service_unavailable'})
          : cartesiaErrorResponse(401, 'unauthorized');
      },
    }),
    (error) => error.provider === 'cartesia',
  );
  assert.equal(calls.length, 2);
  assert.equal(fs.existsSync(out), false);
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
