#!/usr/bin/env node
/**
 * narrate.mjs — turn a finished Civil War letter into a single, continuous
 * narration track via ElevenLabs. A letter is read in one solemn breath, so
 * (unlike the elevenlabs-remotion scene tool) no stitching is needed.
 *
 *   node narrate.mjs --file letter.txt --voice Adam --out ../remotion/public/narration.mp3
 *
 * Auth: ELEVENLABS_API_KEY (or ELEVEN_API_KEY) in the environment or in a
 * .env.local file in the current working directory.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

// Load .env.local from the current dir and the skill root, stripping any
// surrounding quotes so KEY="sk_..." doesn't smuggle quotes into the API call.
function loadEnvLocal() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const candidates = [
    path.join(process.cwd(), '.env.local'),
    path.join(here, '..', '.env.local'),
  ];
  for (const p of candidates) {
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
loadEnvLocal();

const KEY = process.env.ELEVENLABS_API_KEY || process.env.ELEVEN_API_KEY;
if (!KEY) {
  console.error('Error: set ELEVENLABS_API_KEY (or ELEVEN_API_KEY).');
  process.exit(1);
}

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : def;
}

const file = arg('file');
const text = file ? fs.readFileSync(file, 'utf8').trim() : arg('text');
if (!text) {
  console.error('Error: pass --file <letter.txt> or --text "..."');
  process.exit(1);
}
const out = arg('out', 'narration.mp3');
const voiceArg = arg('voice', 'Adam');
const model = arg('model', 'eleven_multilingual_v2');

// A mournful, deliberate field-dispatch delivery.
const voiceSettings = {
  stability: parseFloat(arg('stability', '0.45')),
  similarity_boost: parseFloat(arg('similarity', '0.8')),
  style: parseFloat(arg('style', '0.4')),
  use_speaker_boost: true,
};

async function resolveVoiceId(name) {
  // A raw ElevenLabs voice id is ~20 chars with no spaces.
  if (/^[A-Za-z0-9]{20,}$/.test(name)) return name;
  const res = await fetch('https://api.elevenlabs.io/v1/voices', {
    headers: {'xi-api-key': KEY},
  });
  if (!res.ok) throw new Error(`voice lookup failed: ${res.status}`);
  const {voices} = await res.json();
  const v = voices.find((x) => x.name.toLowerCase() === name.toLowerCase());
  if (!v) throw new Error(`voice "${name}" not found (try --list or a voice id)`);
  return v.voice_id;
}

async function main() {
  const voiceId = await resolveVoiceId(voiceArg);
  console.log(`Narrating ${text.length} chars with "${voiceArg}" (${model})…`);
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
    method: 'POST',
    headers: {
      'xi-api-key': KEY,
      'Content-Type': 'application/json',
      Accept: 'audio/mpeg',
    },
    body: JSON.stringify({text, model_id: model, voice_settings: voiceSettings}),
  });
  if (!res.ok) {
    console.error(`TTS failed: ${res.status} ${await res.text()}`);
    process.exit(1);
  }
  fs.mkdirSync(path.dirname(path.resolve(out)), {recursive: true});
  fs.writeFileSync(out, Buffer.from(await res.arrayBuffer()));
  console.log(`Saved narration -> ${out}`);
}
main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
