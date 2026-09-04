#!/usr/bin/env node
/**
 * Produce exactly one durable narration artifact. ElevenLabs is primary; the
 * explicitly bounded Cartesia /tts/bytes path is a capacity-only fallback.
 * Credentials are read from the process environment (for example, `op run`).
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
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
const SHA256_HEX = /^[a-f0-9]{64}$/;
const LOCK_SCHEMA_VERSION = 2;
const LOCK_PHASE_HISTORY_LIMIT = 32;
const NARRATION_LIMIT_SPECS = Object.freeze({
  requestTimeoutMs: {env: 'SLOWBURNS_NARRATION_REQUEST_TIMEOUT_MS', defaultValue: 30_000, min: 1, max: 120_000},
  bodyReadTimeoutMs: {env: 'SLOWBURNS_NARRATION_BODY_TIMEOUT_MS', defaultValue: 30_000, min: 1, max: 120_000},
  maxAudioBytes: {env: 'SLOWBURNS_NARRATION_MAX_AUDIO_BYTES', defaultValue: 64 * 1024 * 1024, min: 1_024, max: 128 * 1024 * 1024},
  maxErrorBodyBytes: {env: 'SLOWBURNS_NARRATION_MAX_ERROR_BODY_BYTES', defaultValue: 64 * 1024, min: 128, max: 1024 * 1024},
  ffprobeTimeoutMs: {env: 'SLOWBURNS_NARRATION_FFPROBE_TIMEOUT_MS', defaultValue: 5_000, min: 1, max: 30_000},
  ffprobeMaxBufferBytes: {env: 'SLOWBURNS_NARRATION_FFPROBE_MAX_BUFFER_BYTES', defaultValue: 64 * 1024, min: 1_024, max: 1024 * 1024},
});
export const DEFAULT_NARRATION_LIMITS = Object.freeze(Object.fromEntries(
  Object.entries(NARRATION_LIMIT_SPECS).map(([key, spec]) => [key, spec.defaultValue]),
));
// Fallback is intentionally a positive provider-specific status, type, and
// code allowlist. A status alone, a provider-shaped error from the wrong
// service, or an auth/config/input-shaped contradiction is not enough to risk
// a second synthesis request.
const ELEVEN_FALLBACK_BY_STATUS = new Map([
  [402, {type: 'payment_required', codes: new Set(['insufficient_credits'])}],
  [429, {type: 'rate_limit_error', codes: new Set([
    'rate_limit_exceeded', 'concurrent_limit_exceeded', 'too_many_concurrent_requests', 'system_busy',
  ])}],
  [503, {type: 'service_unavailable', codes: new Set(['service_unavailable', 'maintenance'])}],
]);
const ELEVEN_LEGACY_QUOTA_STATUSES = new Set([400, 401]);
const CARTESIA_FALLBACK_CODES_BY_STATUS = new Map([
  [429, new Set(['quota_exceeded', 'concurrency_limited', 'capacity_exceeded'])],
  [500, new Set(['capacity_exceeded', 'concurrency_limited', 'service_unavailable'])],
  [502, new Set(['capacity_exceeded', 'concurrency_limited', 'service_unavailable'])],
  [503, new Set(['capacity_exceeded', 'concurrency_limited', 'service_unavailable'])],
  [504, new Set(['capacity_exceeded', 'concurrency_limited', 'service_unavailable'])],
]);
const RETAINED_LOCK_REASONS = new Set(['ambiguous_transport', 'receipt_integrity', 'invalid_audio', 'ambiguous_retry']);

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

class NarrationTimeoutError extends Error {}
class BodyLimitError extends Error {}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function safeAudioSha256(value) {
  return typeof value === 'string' && SHA256_HEX.test(value) ? value : undefined;
}

function safeByteCount(value) {
  return Number.isSafeInteger(value) && value >= 0 ? value : undefined;
}

function safeRequestId(value) {
  if (typeof value !== 'string' || value.length > MAX_RECEIPT_REQUEST_ID_LENGTH) return undefined;
  return /^[A-Za-z0-9:._-]+$/.test(value) ? value : undefined;
}

function safeErrorToken(value) {
  return typeof value === 'string' && /^[a-z][a-z0-9_]{0,127}$/.test(value) ? value : undefined;
}

function responseHeader(response, name) {
  return typeof response?.headers?.get === 'function' ? response.headers.get(name) : undefined;
}

function providerErrorDetails(provider, body) {
  if (provider === 'eleven') {
    const detail = body?.detail;
    if (!detail || typeof detail !== 'object' || Array.isArray(detail)) return {};
    // A present-but-malformed current `code` must fail closed rather than
    // silently falling back to the legacy field.
    const hasType = Object.prototype.hasOwnProperty.call(detail, 'type');
    const hasCurrentCode = Object.prototype.hasOwnProperty.call(detail, 'code');
    const hasLegacyStatus = Object.prototype.hasOwnProperty.call(detail, 'status');
    const currentCode = safeErrorToken(detail.code);
    const legacyCode = safeErrorToken(detail.status);
    return {
      type: safeErrorToken(detail.type),
      typePresent: hasType,
      code: hasCurrentCode ? currentCode : legacyCode,
      legacyStatus: !hasCurrentCode && typeof detail.status === 'string',
      // Current envelopes may retain `status` for backwards compatibility, but
      // it must agree exactly with `code`. A malformed or contradictory hybrid
      // must never borrow eligibility from either envelope generation.
      contradictory: hasCurrentCode && hasLegacyStatus && currentCode !== legacyCode,
      requestId: safeRequestId(detail.request_id),
    };
  }
  return {
    code: safeErrorToken(body?.error_code),
    requestId: safeRequestId(body?.request_id || body?.requestId),
  };
}

function requestIdFrom(response, provider, body) {
  return providerErrorDetails(provider, body).requestId
    || safeRequestId(responseHeader(response, 'x-request-id'))
    || safeRequestId(responseHeader(response, 'request-id'));
}

function classifiedProviderError(provider, response, body) {
  const details = providerErrorDetails(provider, body);
  const status = Number.isInteger(response.status) ? response.status : undefined;
  const fallbackClass = isCapacityFailure(
    provider, status, details.code, details.type, details.legacyStatus, details.contradictory, details.typePresent,
  )
    ? 'capacity_or_availability'
    : 'nonretryable';
  return new NarrationError(`${provider} narration request failed${status ? ` (${status})` : ''}.`, {
    provider,
    status,
    code: details.code,
    fallbackClass,
    requestId: details.requestId || requestIdFrom(response, provider, body),
  });
}

export function isCapacityFailure(
  provider, status, code, type, legacyStatus = false, contradictory = false, typePresent = false,
) {
  if (!Number.isInteger(status) || !safeErrorToken(code)) return false;
  // A legacy envelope may omit `type`, but it cannot make a malformed present
  // type look absent. This keeps all malformed provider shapes fail-closed.
  if (typePresent && !safeErrorToken(type)) return false;
  if (provider === 'eleven') {
    if (contradictory) return false;
    // ElevenLabs' legacy 400/401 quota envelope uses `detail.status` rather
    // than current `detail.code`. The field may omit `type`; if it supplies a
    // type, it must be the modern payment classification, never auth/input.
    if (legacyStatus) {
      if (ELEVEN_LEGACY_QUOTA_STATUSES.has(status)) {
        return code === 'quota_exceeded'
          && (!type || type === 'payment_required');
      }
      // Legacy availability/capacity envelopes retain distinct 429 and 503
      // status/code forms. Credit exhaustion remains current-envelope-only at
      // 402, and any other legacy 5xx stays nonfallback.
      const legacyRule = (status === 429 || status === 503)
        ? ELEVEN_FALLBACK_BY_STATUS.get(status)
        : undefined;
      return Boolean(legacyRule?.codes.has(code))
        && (!type || type === legacyRule.type);
    }
    const rule = ELEVEN_FALLBACK_BY_STATUS.get(status);
    if (!rule || !rule.codes.has(code)) return false;
    // Current `detail.code` responses must identify the matching type.
    return type === rule.type;
  }
  return CARTESIA_FALLBACK_CODES_BY_STATUS.get(status)?.has(code) === true;
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

export function resolveNarrationLimits(overrides = {}) {
  const limits = {};
  for (const [key, spec] of Object.entries(NARRATION_LIMIT_SPECS)) {
    const raw = overrides?.[key];
    const value = raw === undefined
      ? spec.defaultValue
      : (typeof raw === 'string' && /^\d+$/.test(raw) ? Number(raw) : raw);
    if (!Number.isSafeInteger(value) || value < spec.min || value > spec.max) {
      throw new NarrationError(`${spec.env} must be an integer between ${spec.min} and ${spec.max}.`, {
        fallbackClass: 'configuration',
      });
    }
    limits[key] = value;
  }
  return limits;
}

function normalizeNarrationConfig(config) {
  if (!config?.elevenKey) {
    throw new NarrationError('Set ELEVENLABS_API_KEY (or ELEVEN_API_KEY).', {provider: 'eleven', fallbackClass: 'configuration'});
  }
  validateCartesiaKey(config.cartesiaKey);
  return {...config, limits: resolveNarrationLimits(config.limits)};
}

export function resolveConfig(env = process.env) {
  return normalizeNarrationConfig({
    elevenKey: env.ELEVENLABS_API_KEY || env.ELEVEN_API_KEY,
    cartesiaKey: env.CARTESIA_API_KEY,
    cartesiaVoiceId: env.CARTESIA_VOICE_ID,
    elevenUrl: env.ELEVENLABS_TTS_URL || ELEVEN_TTS_URL,
    cartesiaUrl: env.CARTESIA_TTS_URL || CARTESIA_TTS_URL,
    limits: Object.fromEntries(Object.entries(NARRATION_LIMIT_SPECS).map(([key, spec]) => [key, env[spec.env]])),
  });
}

function assertCartesiaReady(config) {
  if (!config.cartesiaKey || !config.cartesiaVoiceId) {
    throw new NarrationError('Cartesia fallback is unavailable: set standard CARTESIA_API_KEY and CARTESIA_VOICE_ID.', {
      provider: 'cartesia', fallbackClass: 'configuration',
    });
  }
}

function withTimeout(work, timeoutMs, onTimeout) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (callback, value) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      callback(value);
    };
    const timer = setTimeout(() => {
      try { onTimeout?.(); } catch {}
      finish(reject, new NarrationTimeoutError());
    }, timeoutMs);
    Promise.resolve().then(work).then(
      (value) => finish(resolve, value),
      (error) => finish(reject, error),
    );
  });
}

function discardCleanupResult(work) {
  // Never await provider cleanup: a broken stream implementation can leave
  // cancel() pending forever. Attach a rejection handler immediately so a
  // late cleanup failure cannot become an unhandled rejection or replace the
  // provider result that caused cleanup.
  try {
    Promise.resolve(work()).catch(() => {});
  } catch {}
}

function releaseProviderResponse(transport, {reader = transport.reader, fullyConsumed = transport.bodyFullyConsumed} = {}) {
  if (transport.released) return;
  transport.released = true;
  // Abort synchronously and independently of body cleanup. Once headers have
  // arrived, preserving the original semantic outcome and returning control
  // cannot depend on a reader/body cancel promise ever settling.
  try { transport.controller?.abort(); } catch {}
  if (fullyConsumed) return;
  try {
    let unreadReader = reader;
    if (!unreadReader && typeof transport.response?.body?.getReader === 'function') {
      try { unreadReader = transport.response.body.getReader(); } catch {}
    }
    if (typeof unreadReader?.cancel === 'function') {
      discardCleanupResult(() => unreadReader.cancel());
    } else if (typeof transport.response?.body?.cancel === 'function') {
      discardCleanupResult(() => transport.response.body.cancel());
    }
  } catch {
    // Resource cleanup is best-effort and never replaces the provider error.
  }
}

async function readProviderBody(transport, provider, config, lock, kind) {
  const {response} = transport;
  const limit = kind === 'audio' ? config.limits.maxAudioBytes : config.limits.maxErrorBodyBytes;
  const phaseBase = `${provider}_${kind === 'audio' ? 'audio_body' : 'error_body'}_read`;
  let reader;
  let fullyConsumed = false;
  try {
    advanceOperationLock(lock, `${phaseBase}_started`);
    const bytes = await withTimeout(async () => {
      const declaredLength = Number(responseHeader(response, 'content-length'));
      if (Number.isSafeInteger(declaredLength) && declaredLength > limit) throw new BodyLimitError();
      if (typeof response.body?.getReader === 'function') {
        reader = response.body.getReader();
        transport.reader = reader;
        const chunks = [];
        let total = 0;
        while (true) {
          const {done, value} = await reader.read();
          if (done) {
            fullyConsumed = true;
            transport.bodyFullyConsumed = true;
            break;
          }
          const chunk = Buffer.from(value);
          total += chunk.length;
          if (total > limit) throw new BodyLimitError();
          chunks.push(chunk);
        }
        return Buffer.concat(chunks, total);
      }
      if (typeof response.arrayBuffer !== 'function') throw new Error('response body is unavailable');
      const bytes = Buffer.from(await response.arrayBuffer());
      fullyConsumed = true;
      transport.bodyFullyConsumed = true;
      if (bytes.length > limit) throw new BodyLimitError();
      return bytes;
    }, config.limits.bodyReadTimeoutMs);
    advanceOperationLock(lock, `${phaseBase}_completed`);
    return bytes;
  } catch (error) {
    await releaseProviderResponse(transport, {reader, fullyConsumed});
    if (error instanceof BodyLimitError && kind === 'audio') {
      throw new NarrationError(`${provider} narration audio exceeded the configured byte limit.`, {
        provider, fallbackClass: 'invalid_audio',
      });
    }
    // Error bodies and successful audio streams can both cross a provider
    // billing boundary. An unreadable/oversized error body is not reliable
    // evidence that no synthesis occurred, so neither outcome is retried.
    throw new NarrationError(`${provider} narration response body could not be read within configured bounds; refusing retry.`, {
      provider, fallbackClass: 'ambiguous_transport',
    });
  }
}

async function safeErrorBody(transport, provider, config, lock) {
  const {response} = transport;
  if (!(responseHeader(response, 'content-type') || '').toLowerCase().includes('application/json')) {
    await releaseProviderResponse(transport);
    return {};
  }
  const bytes = await readProviderBody(transport, provider, config, lock, 'error');
  try {
    return JSON.parse(bytes.toString('utf8'));
  } catch (error) {
    // A completed malformed JSON body is a definitive provider failure. Do
    // not promote it to a capacity outcome or parse its message for policy.
    if (error instanceof SyntaxError || error?.name === 'SyntaxError') return {};
    throw new NarrationError(`${provider} narration error response could not be classified; refusing retry.`, {
      provider, fallbackClass: 'ambiguous_transport',
    });
  }
}

async function requestProviderResponse(provider, url, init, config, fetchImpl, lock) {
  advanceOperationLock(lock, `${provider}_request_started`);
  const controller = typeof AbortController === 'function' ? new AbortController() : undefined;
  let response;
  try {
    response = await withTimeout(
      () => fetchImpl(url, controller ? {...init, signal: controller.signal} : init),
      config.limits.requestTimeoutMs,
      () => controller?.abort(),
    );
  } catch {
    throw new NarrationError(`${provider} narration transport outcome is ambiguous; refusing fallback or retry.`, {
      provider, fallbackClass: 'ambiguous_transport',
    });
  }
  const transport = {response, controller, released: false, bodyFullyConsumed: false};
  try {
    if (!response || typeof response.ok !== 'boolean' || typeof responseHeader(response, 'content-type') === 'undefined') {
      throw new NarrationError(`${provider} narration response was incomplete; refusing fallback or retry.`, {
        provider, fallbackClass: 'ambiguous_transport',
      });
    }
    advanceOperationLock(lock, `${provider}_headers_received`);
    return transport;
  } catch (error) {
    await releaseProviderResponse(transport);
    throw error;
  }
}

async function requestEleven(config, text, fetchImpl, lock) {
  const transport = await requestProviderResponse('eleven', config.elevenUrl, {
    method: 'POST',
    headers: {'xi-api-key': config.elevenKey, 'Content-Type': 'application/json', Accept: 'audio/mpeg'},
    body: JSON.stringify({
      text,
      model_id: ELEVEN_MODEL,
      voice_settings: {stability: 0.45, similarity_boost: 0.8, style: 0.4, use_speaker_boost: true},
    }),
  }, config, fetchImpl, lock);
  const {response} = transport;
  if (!response.ok) {
    let body;
    try {
      body = await safeErrorBody(transport, 'eleven', config, lock);
    } finally {
      await releaseProviderResponse(transport);
    }
    throw classifiedProviderError('eleven', response, body);
  }
  return {
    audio: await readProviderBody(transport, 'eleven', config, lock, 'audio'),
    requestId: requestIdFrom(response, 'eleven'),
  };
}

async function requestCartesia(config, text, fetchImpl, lock) {
  assertCartesiaReady(config);
  const transport = await requestProviderResponse('cartesia', config.cartesiaUrl, {
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
  }, config, fetchImpl, lock);
  const {response} = transport;
  if (!response.ok) {
    let body;
    try {
      body = await safeErrorBody(transport, 'cartesia', config, lock);
    } finally {
      await releaseProviderResponse(transport);
    }
    throw classifiedProviderError('cartesia', response, body);
  }
  return {
    audio: await readProviderBody(transport, 'cartesia', config, lock, 'audio'),
    requestId: requestIdFrom(response, 'cartesia'),
  };
}

function tempPathFor(out) {
  return path.join(path.dirname(out), `.${path.basename(out)}.${crypto.randomUUID()}.tmp.mp3`);
}

export function isDecodableMp3(file, limits = DEFAULT_NARRATION_LIMITS, ffprobeImpl = execFileSync) {
  const bounded = resolveNarrationLimits(limits);
  try {
    const stat = fs.statSync(file);
    // This guard applies to both freshly written provider bytes and recovered
    // artifacts. Never let a file outside the configured storage envelope
    // reach ffprobe (or a later full-file hash) merely because it exists.
    if (!stat.isFile() || !safeByteCount(stat.size) || stat.size > bounded.maxAudioBytes) return false;
    const format = ffprobeImpl('ffprobe', [
      '-v', 'error', '-show_entries', 'format=format_name', '-of', 'default=noprint_wrappers=1:nokey=1', file,
    ], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: bounded.ffprobeTimeoutMs,
      maxBuffer: bounded.ffprobeMaxBufferBytes,
    }).trim();
    return format.split(',').includes('mp3');
  } catch {
    return false;
  }
}

function publishAudio(audio, out, config, ffprobeImpl, lock, provider) {
  advanceOperationLock(lock, `${provider}_audio_validation_started`);
  if (!audio?.length) {
    throw new NarrationError('Provider returned an empty narration artifact.', {provider, fallbackClass: 'invalid_audio'});
  }
  fs.mkdirSync(path.dirname(out), {recursive: true});
  const temp = tempPathFor(out);
  try {
    fs.writeFileSync(temp, audio, {mode: 0o600});
    if (!isDecodableMp3(temp, config.limits, ffprobeImpl)) {
      throw new NarrationError('Provider returned audio incompatible with the MP3 render pipeline.', {
        provider, fallbackClass: 'invalid_audio',
      });
    }
    fs.renameSync(temp, out);
    advanceOperationLock(lock, `${provider}_audio_published`);
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

function canonicalizePath(file) {
  if (typeof file !== 'string' || !file) {
    throw new NarrationError('Narration output and receipt paths must be nonempty strings.', {fallbackClass: 'configuration'});
  }
  const absolute = path.resolve(file);
  if (!path.basename(absolute)) {
    throw new NarrationError('Narration output must name a file.', {fallbackClass: 'configuration'});
  }
  const suffix = [path.basename(absolute)];
  let directory = path.dirname(absolute);
  while (!fs.existsSync(directory)) {
    const parent = path.dirname(directory);
    if (parent === directory) return absolute;
    suffix.unshift(path.basename(directory));
    directory = parent;
  }
  try {
    return path.join(fs.realpathSync(directory), ...suffix);
  } catch {
    return absolute;
  }
}

function resolveNarrationPaths(out, receiptPath) {
  const finalOut = canonicalizePath(out);
  const finalReceipt = canonicalizePath(receiptPath);
  const lockPath = `${finalOut}.narration.lock`;
  if (finalReceipt === finalOut || finalReceipt === lockPath) {
    throw new NarrationError('Narration receipt path may not collide with the output or its canonical claim.', {
      fallbackClass: 'configuration',
    });
  }
  return {finalOut, finalReceipt, lockPath};
}

function lockRecord(lock) {
  return Object.fromEntries(Object.entries({
    schema_version: LOCK_SCHEMA_VERSION,
    operation: lock.operation,
    output_identity: lock.outputIdentity,
    phase: lock.phase,
    created_at: lock.createdAt,
    updated_at: lock.updatedAt,
    owner_pid: lock.ownerPid,
    owner_host: lock.ownerHost,
    phase_history: lock.phaseHistory,
    operator_intervention_required: lock.operatorInterventionRequired || undefined,
    retained_reason: lock.retainedReason,
    expected_audio_sha256: safeAudioSha256(lock.expectedAudioSha256),
    actual_audio_sha256: safeAudioSha256(lock.actualAudioSha256),
    artifact_size_bytes: safeByteCount(lock.artifactSizeBytes),
    max_audio_bytes: safeByteCount(lock.maxAudioBytes),
  }).filter(([, value]) => value !== undefined));
}

function updateLock(lock) {
  writeJsonAtomic(lock.lockPath, lockRecord(lock));
}

function advanceOperationLock(lock, phase, {
  operatorInterventionRequired = false,
  expectedAudioSha256,
  actualAudioSha256,
  artifactSizeBytes,
  maxAudioBytes,
} = {}) {
  const now = new Date().toISOString();
  lock.phase = phase;
  lock.updatedAt = now;
  lock.phaseHistory = [...lock.phaseHistory, {phase, at: now}].slice(-LOCK_PHASE_HISTORY_LIMIT);
  if (operatorInterventionRequired) lock.operatorInterventionRequired = true;
  if (safeAudioSha256(expectedAudioSha256)) lock.expectedAudioSha256 = expectedAudioSha256;
  if (safeAudioSha256(actualAudioSha256)) lock.actualAudioSha256 = actualAudioSha256;
  if (safeByteCount(artifactSizeBytes) !== undefined) lock.artifactSizeBytes = artifactSizeBytes;
  if (safeByteCount(maxAudioBytes) !== undefined) lock.maxAudioBytes = maxAudioBytes;
  updateLock(lock);
}

function retainOperationLock(lock, reason) {
  lock.updatedAt = new Date().toISOString();
  lock.operatorInterventionRequired = true;
  lock.retainedReason = RETAINED_LOCK_REASONS.has(reason) ? reason : 'ambiguous_retry';
  updateLock(lock);
}

function acquireOperationLock(finalOut, lockPath, operation) {
  fs.mkdirSync(path.dirname(lockPath), {recursive: true});
  const now = new Date().toISOString();
  const lock = {
    lockPath,
    operation,
    outputIdentity: sha256(finalOut),
    phase: 'claimed_pre_provider',
    createdAt: now,
    updatedAt: now,
    ownerPid: process.pid,
    ownerHost: os.hostname(),
    phaseHistory: [{phase: 'claimed_pre_provider', at: now}],
  };
  let fd;
  try {
    fd = fs.openSync(lockPath, 'wx', 0o600);
    fs.writeFileSync(fd, `${JSON.stringify(lockRecord(lock), null, 2)}\n`);
    return lock;
  } catch (error) {
    if (error?.code === 'EEXIST') {
      throw new NarrationError('Narration output is already active or ambiguous; refusing a second provider call.', {
        fallbackClass: 'operation_locked',
      });
    }
    throw error;
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
}

function releaseOperationLock(lock) {
  fs.rmSync(lock.lockPath, {force: true});
}

function receiptIntegrityFailure(lock, state, expectedAudioSha256, actualAudioSha256, {
  artifactSizeBytes,
  maxAudioBytes,
} = {}) {
  // Keep the completed receipt immutable: the lock records only sanitized
  // diagnosis data while preventing implicit replacement. No raw output,
  // receipt, provider body, header, secret, or transcript is serialized.
  advanceOperationLock(lock, state, {
    operatorInterventionRequired: true,
    expectedAudioSha256,
    actualAudioSha256,
    artifactSizeBytes,
    maxAudioBytes,
  });
  throw new NarrationError('Completed narration receipt failed artifact-integrity verification; operator intervention is required.', {
    fallbackClass: 'receipt_integrity',
  });
}

function verifyReceiptAudioSha256(existing, out, lock) {
  let actualAudioSha256;
  try {
    actualAudioSha256 = sha256(fs.readFileSync(out));
  } catch {
    receiptIntegrityFailure(lock, 'receipt_integrity_unreadable_artifact', existing.audio_sha256);
  }
  const expectedAudioSha256 = safeAudioSha256(existing.audio_sha256);
  if (!expectedAudioSha256) {
    receiptIntegrityFailure(lock, 'receipt_integrity_missing_hash', undefined, actualAudioSha256);
  }
  if (expectedAudioSha256 !== actualAudioSha256) {
    receiptIntegrityFailure(lock, 'receipt_integrity_hash_mismatch', expectedAudioSha256, actualAudioSha256);
  }
  return actualAudioSha256;
}

function verifyReceiptArtifactSize(existing, out, lock, limits) {
  const maxAudioBytes = resolveNarrationLimits(limits).maxAudioBytes;
  let stat;
  try {
    stat = fs.statSync(out);
  } catch {
    receiptIntegrityFailure(lock, 'receipt_integrity_missing_or_invalid_artifact', existing.audio_sha256);
  }
  if (!stat.isFile() || !safeByteCount(stat.size)) {
    receiptIntegrityFailure(lock, 'receipt_integrity_missing_or_invalid_artifact', existing.audio_sha256);
  }
  if (stat.size > maxAudioBytes) {
    receiptIntegrityFailure(lock, 'receipt_integrity_artifact_too_large', safeAudioSha256(existing.audio_sha256), undefined, {
      artifactSizeBytes: stat.size,
      maxAudioBytes,
    });
  }
}

function verifyReceiptArtifactIntegrity(existing, out, lock, limits, ffprobeImpl) {
  // Stat first: a completed receipt never authorizes decoding or hashing a
  // file outside the current byte limit. The retained lock is the sole
  // diagnostic mutation; the durable receipt stays byte-for-byte intact.
  verifyReceiptArtifactSize(existing, out, lock, limits);
  if (!isDecodableMp3(out, limits, ffprobeImpl)) {
    receiptIntegrityFailure(lock, 'receipt_integrity_missing_or_invalid_artifact', existing.audio_sha256);
  }
  return verifyReceiptAudioSha256(existing, out, lock);
}

/**
 * Generate or recover one narration operation. A matching incomplete receipt
 * is intentionally terminal: an unknown previous provider outcome must never
 * be retried implicitly and risk duplicate synthesis.
 */
function writeCompletedReceipt(receiptPath, receipt) {
  try {
    writeJsonAtomic(receiptPath, receipt);
  } catch {
    throw new NarrationError('Narration artifact could not be durably receipted; refusing automatic recovery.', {
      fallbackClass: 'ambiguous_transport',
    });
  }
}

export async function narrate({
  text,
  out,
  operationId = 'default',
  receiptPath = `${out}.receipt.json`,
  config,
  fetchImpl = fetch,
  ffprobeImpl = execFileSync,
  log = console.log,
}) {
  const resolvedConfig = normalizeNarrationConfig(config || resolveConfig());
  const {finalOut, finalReceipt, lockPath} = resolveNarrationPaths(out, receiptPath);
  const operation = sha256(`${operationId}\0${text}`);
  const lock = acquireOperationLock(finalOut, lockPath, operation);
  let preserveLock = false;
  try {
    const existing = readReceipt(finalReceipt);
    if (!existing && fs.existsSync(finalReceipt)) {
      throw new NarrationError('Narration receipt is unreadable; refusing implicit retry.', {fallbackClass: 'ambiguous_retry'});
    }
    const completedAudioSha256 = existing?.state === 'complete'
      ? verifyReceiptArtifactIntegrity(existing, finalOut, lock, resolvedConfig.limits, ffprobeImpl)
      : undefined;
    if (existing?.operation === operation) {
      if (fs.existsSync(finalOut)) {
        const actualAudioSha256 = completedAudioSha256
          || verifyReceiptArtifactIntegrity(existing, finalOut, lock, resolvedConfig.limits, ffprobeImpl);
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
          audio_sha256: actualAudioSha256,
          recovered: true,
        };
        writeCompletedReceipt(finalReceipt, recovered);
        advanceOperationLock(lock, 'recovery_receipt_written');
        logReceipt(recovered, log);
        return recovered;
      }
      throw new NarrationError('This narration operation already started without a verified final artifact; refusing implicit retry.', {
        fallbackClass: 'ambiguous_retry',
      });
    }
    if (existing && existing.state !== 'complete') {
      throw new NarrationError('An unfinished narration receipt already exists for this output; refusing implicit retry.', {
        fallbackClass: 'ambiguous_retry',
      });
    }
    removeStaleOperation(finalOut, finalReceipt);
    const receipt = {schema_version: 1, operation, state: 'primary_started', attempts: []};
    writeJsonAtomic(finalReceipt, receipt);
    try {
      const primary = await requestEleven(resolvedConfig, text, fetchImpl, lock);
      const audioSha256 = publishAudio(primary.audio, finalOut, resolvedConfig, ffprobeImpl, lock, 'eleven');
      receipt.state = 'complete';
      receipt.selection = providerReceipt('eleven', ELEVEN_MODEL, ELEVEN_VOICE_ID, 'primary', primary.requestId);
      receipt.audio_sha256 = audioSha256;
      writeCompletedReceipt(finalReceipt, receipt);
      advanceOperationLock(lock, 'complete_receipt_written');
      logReceipt(receipt, log);
      return receipt;
    } catch (error) {
      const primaryError = error instanceof NarrationError
        ? error
        : new NarrationError('ElevenLabs narration failed.', {provider: 'eleven', fallbackClass: 'nonretryable'});
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
        const fallback = await requestCartesia(resolvedConfig, text, fetchImpl, lock);
        const audioSha256 = publishAudio(fallback.audio, finalOut, resolvedConfig, ffprobeImpl, lock, 'cartesia');
        receipt.state = 'complete';
        receipt.selection = providerReceipt('cartesia', CARTESIA_MODEL, resolvedConfig.cartesiaVoiceId, 'capacity_or_availability', fallback.requestId);
        receipt.audio_sha256 = audioSha256;
        writeCompletedReceipt(finalReceipt, receipt);
        advanceOperationLock(lock, 'complete_receipt_written');
        logReceipt(receipt, log);
        return receipt;
      } catch (fallbackError) {
        const cartesiaError = fallbackError instanceof NarrationError
          ? fallbackError
          : new NarrationError('Cartesia narration failed.', {provider: 'cartesia', fallbackClass: 'nonretryable'});
        receipt.attempts.push(providerReceipt('cartesia', CARTESIA_MODEL, resolvedConfig.cartesiaVoiceId, cartesiaError.fallbackClass, cartesiaError.requestId));
        receipt.state = 'failed';
        writeJsonAtomic(finalReceipt, receipt);
        fs.rmSync(finalOut, {force: true});
        throw cartesiaError;
      }
    }
  } catch (error) {
    preserveLock = error instanceof NarrationError && RETAINED_LOCK_REASONS.has(error.fallbackClass);
    if (preserveLock) retainOperationLock(lock, error.fallbackClass);
    throw error;
  } finally {
    if (!preserveLock) releaseOperationLock(lock);
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
