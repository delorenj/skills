#!/usr/bin/env node
/**
 * Produce exactly one durable narration artifact. ElevenLabs is primary; the
 * explicitly bounded Cartesia /tts/bytes path is a capacity-only fallback.
 * Credentials are read from the process environment (for example, `op run`).
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

export const ELEVEN_VOICE_ID = 'HvjKMFO0rjuPaM2f997g';
export const ELEVEN_MODEL = 'eleven_multilingual_v2';
export const CARTESIA_MODEL = 'sonic-3.6';
export const CARTESIA_VERSION = '2026-08-14';
const CARTESIA_TTS_URL = 'https://api.cartesia.ai/tts/bytes';
const ELEVEN_TTS_URL = `https://api.elevenlabs.io/v1/text-to-speech/${ELEVEN_VOICE_ID}`;
const MAX_RECEIPT_REQUEST_ID_LENGTH = 160;
const CAPACITY_CODES = new Set(['quota_exceeded', 'concurrency_limited', 'capacity_exceeded', 'service_unavailable']);
const NON_FALLBACK_CODES = new Set([
  'unauthorized', 'authentication_failed', 'invalid_api_key', 'forbidden',
  'invalid_request', 'validation_error', 'voice_model_mismatch', 'voice_not_found',
  'model_not_found', 'language_not_supported', 'file_too_large',
  'unsupported_audio_format', 'plan_upgrade_required',
]);

export class NarrationError extends Error {
  constructor(message, {provider, status, code, fallbackClass, requestId} = {}) {
    super(message);
    this.name = 'NarrationError';
    this.provider = provider;
    this.status = status;
    this.code = code;
    this.fallbackClass = fallbackClass;
    this.requestId = requestId;
  }
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function safeRequestId(value) {
  if (typeof value !== 'string' || value.length > MAX_RECEIPT_REQUEST_ID_LENGTH) return undefined;
  return /^[A-Za-z0-9:._-]+$/.test(value) ? value : undefined;
}

function requestIdFrom(response, body) {
  return safeRequestId(
    body?.request_id || body?.requestId || response.headers.get('x-request-id') || response.headers.get('request-id'),
  );
}

async function safeErrorBody(response) {
  if (!(response.headers.get('content-type') || '').includes('application/json')) return {};
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function classifiedProviderError(provider, response, body) {
  const code = typeof body.error_code === 'string' ? body.error_code : undefined;
  const fallbackClass = isCapacityFailure(response.status, code) ? 'capacity_or_availability' : 'nonretryable';
  return new NarrationError(`${provider} narration request failed (${response.status}).`, {
    provider, status: response.status, code, fallbackClass, requestId: requestIdFrom(response, body),
  });
}

export function isCapacityFailure(status, code) {
  // Never let a capacity-looking body override a definitive auth/config/input
  // status. A bare 429 is explicitly authorized; a 5xx needs an allowlisted,
  // structured provider code so malformed/unclassified failures fail closed.
  if (NON_FALLBACK_CODES.has(code) || status < 400 || status >= 500 && status <= 599 && !CAPACITY_CODES.has(code)) return false;
  if (status === 429) return true;
  return status >= 500 && status <= 599 && CAPACITY_CODES.has(code);
}

export function validateCartesiaKey(key) {
  if (!key) return;
  if (key.startsWith('sk_car_admin_')) {
    throw new NarrationError('CARTESIA_API_KEY must be a standard Cartesia runtime key, not an admin key.', {
      provider: 'cartesia', fallbackClass: 'configuration',
    });
  }
  if (!/^sk_car_[A-Za-z0-9_-]{16,}$/.test(key)) {
    throw new NarrationError('CARTESIA_API_KEY is not a valid standard Cartesia runtime-key format.', {
      provider: 'cartesia', fallbackClass: 'configuration',
    });
  }
}

export function resolveConfig(env = process.env) {
  const elevenKey = env.ELEVENLABS_API_KEY || env.ELEVEN_API_KEY;
  if (!elevenKey) throw new NarrationError('Set ELEVENLABS_API_KEY (or ELEVEN_API_KEY).', {provider: 'eleven'});
  const cartesiaKey = env.CARTESIA_API_KEY;
  validateCartesiaKey(cartesiaKey);
  return {
    elevenKey,
    cartesiaKey,
    cartesiaVoiceId: env.CARTESIA_VOICE_ID,
    elevenUrl: env.ELEVENLABS_TTS_URL || ELEVEN_TTS_URL,
    cartesiaUrl: env.CARTESIA_TTS_URL || CARTESIA_TTS_URL,
  };
}

function assertCartesiaReady(config) {
  if (!config.cartesiaKey || !config.cartesiaVoiceId) {
    throw new NarrationError('Cartesia fallback is unavailable: set standard CARTESIA_API_KEY and CARTESIA_VOICE_ID.', {
      provider: 'cartesia', fallbackClass: 'configuration',
    });
  }
}

async function requestEleven(config, text, fetchImpl) {
  let response;
  try {
    response = await fetchImpl(config.elevenUrl, {
      method: 'POST',
      headers: {'xi-api-key': config.elevenKey, 'Content-Type': 'application/json', Accept: 'audio/mpeg'},
      body: JSON.stringify({
        text,
        model_id: ELEVEN_MODEL,
        voice_settings: {stability: 0.45, similarity_boost: 0.8, style: 0.4, use_speaker_boost: true},
      }),
    });
  } catch {
    throw new NarrationError('ElevenLabs narration transport outcome is ambiguous; refusing fallback or retry.', {
      provider: 'eleven', fallbackClass: 'ambiguous_transport',
    });
  }
  if (!response.ok) throw classifiedProviderError('eleven', response, await safeErrorBody(response));
  return {audio: Buffer.from(await response.arrayBuffer()), requestId: requestIdFrom(response)};
}

async function requestCartesia(config, text, fetchImpl) {
  assertCartesiaReady(config);
  let response;
  try {
    response = await fetchImpl(config.cartesiaUrl, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${config.cartesiaKey}`,
        'Cartesia-Version': CARTESIA_VERSION,
        'Content-Type': 'application/json',
        Accept: 'audio/mpeg',
      },
      body: JSON.stringify({
        model_id: CARTESIA_MODEL,
        transcript: text,
        voice: config.cartesiaVoiceId,
        output_format: {container: 'mp3', sample_rate: 44100, bit_rate: 128000},
        locale: 'en-US',
        generation_config: {volume: 1, speed: 0.85},
      }),
    });
  } catch {
    throw new NarrationError('Cartesia narration transport outcome is ambiguous.', {
      provider: 'cartesia', fallbackClass: 'ambiguous_transport',
    });
  }
  if (!response.ok) throw classifiedProviderError('cartesia', response, await safeErrorBody(response));
  return {audio: Buffer.from(await response.arrayBuffer()), requestId: requestIdFrom(response)};
}

function tempPathFor(out) {
  return path.join(path.dirname(out), `.${path.basename(out)}.${crypto.randomUUID()}.tmp.mp3`);
}

export function isDecodableMp3(file) {
  try {
    if (!fs.statSync(file).size) return false;
    const format = execFileSync('ffprobe', [
      '-v', 'error', '-show_entries', 'format=format_name', '-of', 'default=noprint_wrappers=1:nokey=1', file,
    ], {encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']}).trim();
    return format.split(',').includes('mp3');
  } catch {
    return false;
  }
}

function publishAudio(audio, out) {
  if (!audio?.length) throw new NarrationError('Provider returned an empty narration artifact.', {fallbackClass: 'invalid_audio'});
  fs.mkdirSync(path.dirname(out), {recursive: true});
  const temp = tempPathFor(out);
  try {
    fs.writeFileSync(temp, audio, {mode: 0o600});
    if (!isDecodableMp3(temp)) throw new NarrationError('Provider returned audio incompatible with the MP3 render pipeline.', {fallbackClass: 'invalid_audio'});
    fs.renameSync(temp, out);
    return sha256(audio);
  } finally {
    fs.rmSync(temp, {force: true});
  }
}

function writeJsonAtomic(file, value) {
  fs.mkdirSync(path.dirname(file), {recursive: true});
  const temp = path.join(path.dirname(file), `.${path.basename(file)}.${crypto.randomUUID()}.tmp`);
  try {
    fs.writeFileSync(temp, `${JSON.stringify(value, null, 2)}\n`, {mode: 0o600});
    fs.renameSync(temp, file);
  } finally {
    fs.rmSync(temp, {force: true});
  }
}

function readReceipt(file) {
  try {
    const receipt = JSON.parse(fs.readFileSync(file, 'utf8'));
    return receipt && typeof receipt === 'object' ? receipt : undefined;
  } catch {
    return undefined;
  }
}

function providerReceipt(provider, model, voice, fallbackClass, requestId) {
  return Object.fromEntries(Object.entries({
    provider, model, voice, fallback_class: fallbackClass, request_id: safeRequestId(requestId),
  }).filter(([, value]) => value !== undefined));
}

function logReceipt(receipt, log) {
  log(`[narration-receipt] ${JSON.stringify(receipt)}`);
}

function removeStaleOperation(out, receiptPath) {
  fs.rmSync(out, {force: true});
  fs.rmSync(receiptPath, {force: true});
}

function acquireOperationLock(receiptPath, operation) {
  const lockPath = `${receiptPath}.lock`;
  fs.mkdirSync(path.dirname(lockPath), {recursive: true});
  let fd;
  try {
    fd = fs.openSync(lockPath, 'wx', 0o600);
    fs.writeFileSync(fd, `${JSON.stringify({schema_version: 1, operation, state: 'active'})}\n`);
    return lockPath;
  } catch (error) {
    if (error?.code === 'EEXIST') {
      throw new NarrationError('Narration operation is already active or ambiguous; refusing a second provider call.', {
        fallbackClass: 'operation_locked',
      });
    }
    throw error;
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
}

function releaseOperationLock(lockPath) {
  fs.rmSync(lockPath, {force: true});
}

/**
 * Generate or recover one narration operation. A matching incomplete receipt
 * is intentionally terminal: an unknown previous provider outcome must never
 * be retried implicitly and risk duplicate synthesis.
 */
export async function narrate({text, out, operationId = 'default', receiptPath = `${out}.receipt.json`, config, fetchImpl = fetch, log = console.log}) {
  const resolvedConfig = config || resolveConfig();
  // Direct callers must receive the same guard as the CLI path before any
  // state mutation or network call.
  validateCartesiaKey(resolvedConfig.cartesiaKey);
  const finalOut = path.resolve(out);
  const finalReceipt = path.resolve(receiptPath);
  const operation = sha256(`${operationId}\0${text}`);
  const lockPath = acquireOperationLock(finalReceipt, operation);
  let preserveLock = false;
  try {
    const existing = readReceipt(finalReceipt);
    if (existing?.operation === operation) {
      if (isDecodableMp3(finalOut)) {
        const provider = existing.selection?.provider || (existing.state === 'fallback_started' ? 'cartesia' : 'eleven');
        const recovered = {
          ...existing,
          state: 'complete',
          selection: existing.selection || providerReceipt(
            provider,
            provider === 'cartesia' ? CARTESIA_MODEL : ELEVEN_MODEL,
            provider === 'cartesia' ? resolvedConfig.cartesiaVoiceId : ELEVEN_VOICE_ID,
            'recovered_after_unfinished_receipt',
          ),
          audio_sha256: existing.audio_sha256 || sha256(fs.readFileSync(finalOut)),
          recovered: true,
        };
        writeJsonAtomic(finalReceipt, recovered);
        logReceipt(recovered, log);
        return recovered;
      }
      throw new NarrationError('This narration operation already started without a verified final artifact; refusing implicit retry.', {
        fallbackClass: 'ambiguous_retry',
      });
    }
    removeStaleOperation(finalOut, finalReceipt);
    const receipt = {schema_version: 1, operation, state: 'primary_started', attempts: []};
    writeJsonAtomic(finalReceipt, receipt);
    try {
      const primary = await requestEleven(resolvedConfig, text, fetchImpl);
      const audioSha256 = publishAudio(primary.audio, finalOut);
      receipt.state = 'complete';
      receipt.selection = providerReceipt('eleven', ELEVEN_MODEL, ELEVEN_VOICE_ID, 'primary', primary.requestId);
      receipt.audio_sha256 = audioSha256;
      writeJsonAtomic(finalReceipt, receipt);
      logReceipt(receipt, log);
      return receipt;
    } catch (error) {
      const primaryError = error instanceof NarrationError ? error : new NarrationError('ElevenLabs narration failed.', {provider: 'eleven'});
      receipt.attempts.push(providerReceipt('eleven', ELEVEN_MODEL, ELEVEN_VOICE_ID, primaryError.fallbackClass, primaryError.requestId));
      receipt.state = 'primary_failed';
      writeJsonAtomic(finalReceipt, receipt);
      if (primaryError.fallbackClass !== 'capacity_or_availability') {
        fs.rmSync(finalOut, {force: true});
        throw primaryError;
      }
      try {
        receipt.state = 'fallback_started';
        writeJsonAtomic(finalReceipt, receipt);
        const fallback = await requestCartesia(resolvedConfig, text, fetchImpl);
        const audioSha256 = publishAudio(fallback.audio, finalOut);
        receipt.state = 'complete';
        receipt.selection = providerReceipt('cartesia', CARTESIA_MODEL, resolvedConfig.cartesiaVoiceId, 'capacity_or_availability', fallback.requestId);
        receipt.audio_sha256 = audioSha256;
        writeJsonAtomic(finalReceipt, receipt);
        logReceipt(receipt, log);
        return receipt;
      } catch (fallbackError) {
        const cartesiaError = fallbackError instanceof NarrationError ? fallbackError : new NarrationError('Cartesia narration failed.', {provider: 'cartesia'});
        receipt.attempts.push(providerReceipt('cartesia', CARTESIA_MODEL, resolvedConfig.cartesiaVoiceId, cartesiaError.fallbackClass, cartesiaError.requestId));
        receipt.state = 'failed';
        writeJsonAtomic(finalReceipt, receipt);
        fs.rmSync(finalOut, {force: true});
        throw cartesiaError;
      }
    }
  } catch (error) {
    preserveLock = error instanceof NarrationError && error.fallbackClass === 'ambiguous_transport';
    throw error;
  } finally {
    if (!preserveLock) releaseOperationLock(lockPath);
  }
}

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : def;
}

async function main() {
  const file = arg('file');
  const text = file ? fs.readFileSync(file, 'utf8').trim() : arg('text');
  if (!text) throw new NarrationError('Pass --file <letter.txt> or --text "...".');
  const out = arg('out', 'narration.mp3');
  const receipt = await narrate({text, out, operationId: arg('operation-id', 'default'), receiptPath: arg('receipt', `${out}.receipt.json`)});
  console.log(`Saved narration -> ${out} (${receipt.selection.provider})`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    // Deliberately no provider response body, transcript, credentials, or headers.
    console.error(`Narration failed${error.fallbackClass ? ` (${error.fallbackClass})` : ''}: ${error.message}`);
    process.exit(1);
  });
}
