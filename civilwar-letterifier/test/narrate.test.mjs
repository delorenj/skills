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

test.after(() => fs.rmSync(tempRoot, {recursive: true, force: true}));

function runDir(name) {
  return fs.mkdtempSync(path.join(tempRoot, `${name}-`));
}

function config() {
  return {
    elevenKey: 'eleven-test-key',
    cartesiaKey: 'sk_car_1234567890abcdefghij',
    cartesiaVoiceId: 'verified-by-runtime-config',
    elevenUrl: 'https://eleven.test/tts',
    cartesiaUrl: 'https://cartesia.test/tts/bytes',
  };
}

function jsonResponse(status, body, requestId = 'safe-request-id') {
  return new Response(JSON.stringify(body), {
    status,
    headers: {'content-type': 'application/json', 'x-request-id': requestId},
  });
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
        ? jsonResponse(429, {error_code: 'quota_exceeded', request_id: 'eleven-capacity'})
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
  await assert.rejects(
    narrate({
      text: 'A solemn dispatch.', out, operationId: 'nonretryable', config: config(), log: () => {},
      fetchImpl: async (url) => { calls.push(url); return jsonResponse(401, {error_code: 'unauthorized'}); },
    }),
    (error) => error.fallbackClass === 'nonretryable',
  );
  assert.deepEqual(calls, ['https://eleven.test/tts']);
  assert.equal(fs.existsSync(out), false);
});

test('auth, config, input, and other 4xx errors never fall back even with capacity-looking codes', async () => {
  for (const [status, code] of [[400, 'quota_exceeded'], [401, 'quota_exceeded'], [403, 'concurrency_limited'], [404, 'service_unavailable']]) {
    const calls = [];
    const out = path.join(runDir(`contradictory-${status}`), 'narration.mp3');
    await assert.rejects(
      narrate({
        text: 'A solemn dispatch.', out, operationId: `contradictory-${status}`, config: config(), log: () => {},
        fetchImpl: async (url) => { calls.push(url); return jsonResponse(status, {error_code: code}); },
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
        ? jsonResponse(429, {error_code: 'concurrency_limited'})
        : audioResponse();
    },
  });
  assert.deepEqual(recognizedCalls, ['https://eleven.test/tts', 'https://cartesia.test/tts/bytes']);
  assert.equal(recognized.selection.provider, 'cartesia');

  const rejectedCases = [
    () => jsonResponse(429, {error_code: 'auth_error'}),
    () => jsonResponse(429, {error_code: 'unknown_provider_error'}),
    () => jsonResponse(429, {}),
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

test('malformed or unclassified 5xx errors fail closed, while structured availability falls back once', async () => {
  const malformedCases = [
    () => new Response('gateway exploded', {status: 503, headers: {'content-type': 'text/plain'}}),
    () => new Response('{not json', {status: 503, headers: {'content-type': 'application/json'}}),
    () => jsonResponse(503, {error_code: 'something_else'}),
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
      return calls.length === 1 ? jsonResponse(503, {error_code: 'service_unavailable'}) : audioResponse();
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
          ? jsonResponse(503, {error_code: 'service_unavailable'})
          : jsonResponse(401, {error_code: 'unauthorized'});
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
  assert.equal(fs.existsSync(`${out}.receipt.json.lock`), true);
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
      ? jsonResponse(429, {error_code: 'quota_exceeded'})
      : unreadableAudioResponse();
  };
  await assert.rejects(
    narrate({text: 'A solemn dispatch.', out, operationId: 'first', config: config(), log: () => {}, fetchImpl: fallbackWithUnreadableBody}),
    (error) => error.provider === 'cartesia' && error.fallbackClass === 'ambiguous_transport',
  );
  const receipt = JSON.parse(fs.readFileSync(`${out}.receipt.json`, 'utf8'));
  assert.equal(receipt.state, 'failed');
  assert.equal(receipt.attempts[1].fallback_class, 'ambiguous_transport');
  assert.equal(fs.existsSync(`${out}.receipt.json.lock`), true);
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

test('runtime config rejects admin and malformed Cartesia keys before network use', () => {
  assert.throws(() => resolveConfig({ELEVENLABS_API_KEY: 'eleven', CARTESIA_API_KEY: 'sk_car_admin_dont-use-me'}), /not an admin key/);
  assert.throws(() => resolveConfig({ELEVENLABS_API_KEY: 'eleven', CARTESIA_API_KEY: 'legacy-key'}), /standard Cartesia/);
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
