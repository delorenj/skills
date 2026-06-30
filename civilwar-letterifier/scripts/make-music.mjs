#!/usr/bin/env node
/**
 * make-music.mjs — synthesize a short, mournful instrumental bed with the
 * ElevenLabs Sound Generation API when you don't have a real period track to
 * drop in. The composition loops this clip under the narration, so a ~22s bed
 * is plenty.
 *
 *   node make-music.mjs --out ../remotion/public/music.mp3 --seconds 22
 *
 * Auth: ELEVENLABS_API_KEY (or ELEVEN_API_KEY).
 *
 * NOTE: This is an *original synthesized* bed, not a recording of a copyrighted
 * arrangement. For the real thing, drop a licensed/public-domain track into
 * assets/music/ instead (see references/voice-and-music.md).
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

// Load .env.local from the current dir and the skill root (stripping quotes) so
// this script works when run directly, not just via build.mjs.
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

const out = arg('out', 'music.mp3');
const seconds = Math.min(22, Math.max(5, parseFloat(arg('seconds', '22'))));
const prompt =
  arg('prompt') ||
  'Solemn, mournful American Civil War era instrumental score: a lone fiddle ' +
    'and soft fingerpicked banjo, slow and sparse, distant and melancholic, ' +
    'candlelit parlor, no drums, no vocals, gentle and reverent like a ' +
    'documentary underscore.';

async function main() {
  console.log(`Generating ${seconds}s ambient bed…`);
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
  console.log(`Saved music bed -> ${out}`);
}
main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
