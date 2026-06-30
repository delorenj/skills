#!/usr/bin/env node
/**
 * make-ambient.mjs — synthesize an always-on field-atmosphere bed (crickets,
 * night wind, a far-off encampment) via the ElevenLabs Sound Generation API,
 * for when you don't have a real ambience recording to drop into assets/sfx.
 *
 *   node make-ambient.mjs --out ../assets/sfx/ambient.mp3 --seconds 22
 *
 * The composition loops this quietly beneath the narration and music, so a
 * ~22s bed is plenty. SlowBurns caches the result in assets/sfx/ambient.mp3 so
 * repeat runs reuse it instead of regenerating (delete it to re-roll).
 *
 * Auth: ELEVENLABS_API_KEY (or ELEVEN_API_KEY).
 *
 * NOTE: this is an *original synthesized* texture, not a copyrighted recording —
 * safe to publish. For the real thing, drop a field recording into assets/sfx/.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

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

const out = arg('out', 'ambient.mp3');
const seconds = Math.min(22, Math.max(5, parseFloat(arg('seconds', '22'))));
const prompt =
  arg('prompt') ||
  'Quiet nighttime field ambience from the American Civil War era: distant ' +
    'crickets, soft night wind through grass, a faint and far-off encampment, ' +
    'an occasional very distant low rumble of thunder. Continuous and ' +
    'unobtrusive, no melody, no instruments, no music — a low documentary ' +
    'background texture beneath a narration.';

async function main() {
  console.log(`Generating ${seconds}s ambient field bed…`);
  const res = await fetch('https://api.elevenlabs.io/v1/sound-generation', {
    method: 'POST',
    headers: {
      'xi-api-key': KEY,
      'Content-Type': 'application/json',
      Accept: 'audio/mpeg',
    },
    body: JSON.stringify({
      text: prompt,
      duration_seconds: seconds,
      prompt_influence: 0.3,
    }),
  });
  if (!res.ok) {
    console.error(`Sound generation failed: ${res.status} ${await res.text()}`);
    process.exit(1);
  }
  fs.mkdirSync(path.dirname(path.resolve(out)), {recursive: true});
  fs.writeFileSync(out, Buffer.from(await res.arrayBuffer()));
  console.log(`Saved ambient bed -> ${out}`);
}
main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
