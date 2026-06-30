#!/usr/bin/env node
/**
 * narrate.mjs — turn a finished Civil War letter into a single, continuous
 * narration track via ElevenLabs. A letter is read in one solemn breath, so
 * (unlike the elevenlabs-remotion scene tool) no stitching is needed.
 *
 *   node narrate.mjs --file letter.txt --out ../remotion/public/narration.mp3
 *
 * The narrator is the hardcoded custom "Civil War Veteran" voice (VOICE_ID
 * below). This is deliberately NOT parameterized — there is one narrator.
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

// The one and only narrator: the custom "Civil War Veteran" voice, with its
// fixed mournful, deliberate field-dispatch delivery. All of this is hardcoded
// on purpose — the voice is never parameterized. To change narrators, design a
// new voice (see references/voice-and-music.md) and replace these constants.
const VOICE_ID = 'HvjKMFO0rjuPaM2f997g';
const model = 'eleven_multilingual_v2';
const voiceSettings = {
  stability: 0.45,
  similarity_boost: 0.8,
  style: 0.4,
  use_speaker_boost: true,
};

async function main() {
  console.log(`Narrating ${text.length} chars with the Civil War Veteran voice (${model})…`);
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`, {
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
