#!/usr/bin/env node
/**
 * letterify.mjs — turn ordinary modern text into a solemn, slightly absurd
 * 19th-century Civil War field dispatch (the Ken Burns letter voice).
 *
 * This is the one creative step of the SlowBurns pipeline that used to be done
 * by hand. Given raw text, it asks an LLM (via OpenRouter) to rewrite the *tone*
 * into a mournful period dispatch while preserving every fact, then returns the
 * complete letter — salutation, body, and the model's own cohesive closing
 * sign-off + signature (the signature is part of the writing, not appended, so
 * it matches the letter's content). Sign as --signer (default "J.").
 *
 * Usable two ways:
 *   import { letterify } from './letterify.mjs'
 *     const note = await letterify(text, { mode: 'standard' })
 *   node scripts/letterify.mjs --file note.txt           # prints prose to stdout
 *   node scripts/letterify.mjs --text "..." --mode full
 *
 * Provider: OpenRouter (https://openrouter.ai), OpenAI-compatible chat API —
 * matches the raw-fetch, dependency-free pattern of narrate.mjs / make-music.mjs
 * (no SDK install required).
 *
 * Auth: SLOWBURNS_OPENROUTER_API_KEY (the app's dedicated key) — falls back to
 * OPENROUTER_API_KEY. Read from the environment or a .env.local file in the
 * current dir or the skill root, using an app-specific var so the generic global
 * OPENROUTER_API_KEY can't shadow it. The value may be a literal key OR a
 * 1Password reference ("op://DeLoSecrets/OpenRouter/SLOWBURNS_OPENROUTER_API_KEY"),
 * which is resolved at runtime via `op read` — so no plaintext need live on disk.
 *
 * Model: anthropic/claude-sonnet-5 by default; override with --model or
 * $SLOWBURNS_MODEL (any OpenRouter slug, e.g. anthropic/claude-opus-4.8,
 * google/gemini-2.5-pro, openai/gpt-5.1).
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

// Resolve a secret that may be a 1Password reference ("op://vault/item/field").
// Plain values pass through unchanged, so a literal key still works.
function resolveSecret(value) {
  if (!value || !value.startsWith('op://')) return value;
  try {
    return execFileSync('op', ['read', value], {encoding: 'utf8'}).trim();
  } catch (e) {
    throw new Error(
      `Could not resolve ${value} via 1Password. Is the op CLI installed and signed in? (${e.message})`
    );
  }
}

// Load .env.local (cwd + skill root), stripping surrounding quotes, so a key in
// KEY="sk-or-..." doesn't smuggle quotes into the request.
function loadEnvLocal() {
  for (const p of [path.join(process.cwd(), '.env.local'), path.join(ROOT, '.env.local')]) {
    if (!fs.existsSync(p)) continue;
    for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
      const i = line.indexOf('=');
      if (i > 0 && !line.trim().startsWith('#')) {
        const k = line.slice(0, i).trim();
        let v = line.slice(i + 1).trim();
        if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
          v = v.slice(1, -1);
        }
        if (!process.env[k]) process.env[k] = v;
      }
    }
  }
}

const DEFAULT_MODEL = 'anthropic/claude-sonnet-5';
const ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions';

const SYSTEM_PROMPT = `You are the SlowBurns letterifier. Rewrite the user's text as a solemn, slightly
absurd 19th-century American Civil War field dispatch — the mournful register of
a Ken Burns documentary letter, read over fiddle and candlelight.

INVIOLABLE RULES:
- Preserve every fact exactly: names, dates, numbers, deadlines, ticket IDs,
  requests, and logistics. Translate the tone, never the content. A blocked Jira
  ticket stays a blocked Jira ticket; the 3 p.m. standup stays the 3 p.m. standup.
- Invent no new facts — no new dates, promises, casualties, or details. Period
  metaphor is welcome; new commitments are not.
- Keep it usable: after the theatrics the reader must still know the status, the
  blocker, and the ask.
- Address a recipient (e.g. "My dear colleagues,").
- Close the letter yourself with a mournful sign-off line, then the signature on
  its own line. Weave the letter's affliction or sentiment naturally into the
  sign-off using ordinary period phrasing — e.g. "Your obedient and much-delayed
  servant,", "Your faithful and fever-worn servant,", "Yours in weary devotion,".
  Use only real, well-formed words; never bolt a literal "'d" onto a word that
  does not take it. Do NOT write a date line; one is placed separately.

OUTPUT: respond with ONLY the complete letter — salutation, body, closing
sign-off, and signature. No preamble, no explanation, no commentary, no
markdown, no code fences, no title.`;

const MODE_GUIDANCE = {
  standard: 'Write one or two sepia paragraphs. Tasteful tragedy.',
  'field-note':
    'Write one or two sentences, short enough for a text message. No stage cues.',
  full:
    'Maximum melodrama. Open with an italic stage cue such as *faint fiddle over distant thunder*. Heavier weather, more affliction — still factually exact.',
  executive:
    'A grave dispatch a manager can act on: lead with costume, but make the status, blocker, owner, and ask unmistakable.',
};

/**
 * Rewrite `text` as a Civil War dispatch. Returns the letter prose (no signature).
 * @param {string} text  the raw modern text
 * @param {{mode?: string, model?: string}} [opts]
 */
export async function letterify(text, opts = {}) {
  loadEnvLocal();
  const input = String(text || '').trim();
  if (!input) throw new Error('letterify: empty input text.');

  const mode = MODE_GUIDANCE[opts.mode] ? opts.mode : 'standard';
  const model = opts.model || process.env.SLOWBURNS_MODEL || DEFAULT_MODEL;
  const signer = (opts.signer || 'J.').trim();

  const key = resolveSecret(
    process.env.SLOWBURNS_OPENROUTER_API_KEY || process.env.OPENROUTER_API_KEY
  );
  if (!key) {
    throw new Error(
      'Set SLOWBURNS_OPENROUTER_API_KEY (or OPENROUTER_API_KEY) in the environment or .env.local.'
    );
  }

  const userMessage =
    `Mode: ${mode}. ${MODE_GUIDANCE[mode]}\n\n` +
    `Sign the letter as: ${signer}\n\n` +
    `Rewrite the following text as the dispatch:\n\n---\n${input}\n---`;

  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      // Attribution headers (used by OpenRouter for app ranking; harmless).
      'HTTP-Referer': 'https://slowburns.app',
      'X-Title': 'SlowBurns',
    },
    body: JSON.stringify({
      model,
      max_tokens: 2048,
      temperature: 0.8,
      messages: [
        {role: 'system', content: SYSTEM_PROMPT},
        {role: 'user', content: userMessage},
      ],
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Letterify failed: ${res.status} ${body}`);
  }

  const data = await res.json();
  if (data.error) {
    throw new Error(`Letterify failed: ${data.error.message || JSON.stringify(data.error)}`);
  }
  const content = data.choices && data.choices[0] && data.choices[0].message
    ? data.choices[0].message.content
    : null;
  if (!content || !content.trim()) throw new Error('Letterify returned no text.');

  // Strip any stray markdown fences and trim.
  let prose = content.trim();
  prose = prose.replace(/^```[a-z]*\n?/i, '').replace(/\n?```$/, '').trim();
  return prose;
}

// --- CLI ------------------------------------------------------------------
function isMain() {
  return process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
}

if (isMain()) {
  const arg = (name, def) => {
    const i = process.argv.indexOf(`--${name}`);
    if (i === -1) return def;
    const v = process.argv[i + 1];
    return v && !v.startsWith('--') ? v : true;
  };
  const file = arg('file');
  const text = file && file !== true ? fs.readFileSync(path.resolve(file), 'utf8') : arg('text');
  if (!text || text === true) {
    console.error('Usage: node scripts/letterify.mjs (--file <txt> | --text "...") [--mode standard|field-note|full|executive] [--model <slug>] [--signer "J."]');
    process.exit(1);
  }
  const mode = arg('mode', 'standard');
  const model = arg('model');
  const signer = arg('signer');
  letterify(text, {
    mode: mode === true ? 'standard' : mode,
    model: model === true ? undefined : model,
    signer: signer === true ? undefined : signer,
  })
    .then((prose) => {
      process.stdout.write(prose + '\n');
    })
    .catch((e) => {
      console.error(e.message);
      process.exit(1);
    });
}
