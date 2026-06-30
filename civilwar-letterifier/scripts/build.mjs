#!/usr/bin/env node
/**
 * build.mjs — the multimodal pipeline for the Civil War Letterifier.
 *
 * Given a finished letter (already rewritten by Claude into period prose), this:
 *   1. narrates it with ElevenLabs            -> remotion/public/narration.mp3
 *   2. resolves a music bed (drop-in or auto) -> remotion/public/music.mp3
 *   3. writes render props                    -> remotion/props.json
 *   4. renders the Ken Burns documentary clip -> out/<name>.mp4
 *
 * Usage:
 *   node scripts/build.mjs --spec letter.json --voice Adam --out out/letter.mp4
 *   node scripts/build.mjs --spec letter.json --music assets/music/ashokan.mp3
 *   node scripts/build.mjs --spec letter.json --auto-music --out out/letter.mp4
 *
 * letter.json shape (all but letterText optional):
 *   {
 *     "letterText": "My dear colleagues,\n\n...",
 *     "dateLine":   "Camp near Antietam, September 1862",
 *     "signature":  "Your obedient servant, J.",
 *     "title":      "A Letter from the Front",
 *     "fontStyle":  "script"          // "script" | "dispatch"
 *   }
 *
 * Auth: ELEVENLABS_API_KEY (or ELEVEN_API_KEY). Requires Node 18+ (fetch) and,
 * for rendering, the remotion/ project deps (auto-installed on first run).
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const REMOTION = path.join(ROOT, 'remotion');
const PUBLIC = path.join(REMOTION, 'public');

// Load .env.local (cwd + skill root, quotes stripped) and propagate to the
// child scripts via the inherited environment, so `--auto-music` and narration
// authenticate even when the key lives only in .env.local.
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
loadEnvLocal();

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  if (i === -1) return def;
  const v = process.argv[i + 1];
  return v && !v.startsWith('--') ? v : true; // bare flag -> true
}
function run(cmd, args, cwd) {
  console.log(`\n$ ${cmd} ${args.join(' ')}`);
  execFileSync(cmd, args, {cwd: cwd || ROOT, stdio: 'inherit'});
}

// --- Inputs ---------------------------------------------------------------
const specPath = arg('spec');
if (!specPath) {
  console.error('Error: --spec <letter.json> is required.');
  process.exit(1);
}
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
if (!spec.letterText) {
  console.error('Error: letter.json must contain "letterText".');
  process.exit(1);
}

const voice = arg('voice', process.env.CIVILWAR_VOICE || 'Adam');
const musicPath = arg('music'); // explicit drop-in track
const autoMusic = arg('auto-music', false);

function pickRandomTrack(dir) {
  const files = fs.readdirSync(dir).filter((f) => /\.(mp3|wav|ogg|m4a|flac)$/i.test(f));
  if (files.length === 0) return null;
  return path.join(dir, files[Math.floor(Math.random() * files.length)]);
}
const outFile = path.resolve(arg('out', path.join(ROOT, 'out', 'letter.mp4')));
const introPad = parseFloat(arg('intro-pad', '3.5'));
const outroPad = parseFloat(arg('outro-pad', '4'));
const accentColor = arg('accent', '#5a2a16');
const fontStyle = spec.fontStyle === 'dispatch' ? 'dispatch' : 'script';

fs.mkdirSync(PUBLIC, {recursive: true});

// --- 1. Narration ---------------------------------------------------------
const letterTxt = path.join(PUBLIC, '.letter.txt');
fs.writeFileSync(letterTxt, spec.letterText);
run('node', [
  path.join(ROOT, 'scripts', 'narrate.mjs'),
  '--file', letterTxt,
  '--voice', voice,
  '--out', path.join(PUBLIC, 'narration.mp3'),
]);

// --- 2. Music bed ---------------------------------------------------------
const musicDest = path.join(PUBLIC, 'music.mp3');
let hasMusic = false;
if (musicPath && musicPath !== true) {
  fs.copyFileSync(path.resolve(musicPath), musicDest);
  hasMusic = true;
  console.log(`\nUsing drop-in music: ${musicPath}`);
} else if (autoMusic) {
  run('node', [
    path.join(ROOT, 'scripts', 'make-music.mjs'),
    '--out', musicDest,
    '--seconds', '22',
  ]);
  hasMusic = true;
} else {
  const randomTrack = pickRandomTrack(path.join(ROOT, 'assets', 'music'));
  if (randomTrack) {
    fs.copyFileSync(randomTrack, musicDest);
    hasMusic = true;
    console.log(`\nUsing random music: ${randomTrack}`);
  } else {
    console.log('\nNo music selected (pass --music <file> or --auto-music). Voice only.');
  }
}

// --- 3. Props -------------------------------------------------------------
const props = {
  letterText: spec.letterText,
  dateLine: spec.dateLine || '',
  signature: spec.signature || '',
  title: spec.title || 'A Letter from the Front',
  fontStyle,
  hasMusic,
  narrationFile: 'narration.mp3',
  musicFile: 'music.mp3',
  introPad,
  outroPad,
  accentColor,
};
const propsPath = path.join(REMOTION, 'props.json');
fs.writeFileSync(propsPath, JSON.stringify(props, null, 2));
console.log(`\nWrote props -> ${propsPath}`);

// --- 4. Render ------------------------------------------------------------
if (!fs.existsSync(path.join(REMOTION, 'node_modules'))) {
  console.log('\nInstalling Remotion deps (first run only)…');
  run('npm', ['install'], REMOTION);
}
fs.mkdirSync(path.dirname(outFile), {recursive: true});
run('npx', ['remotion', 'render', 'CivilWarLetter', outFile, `--props=${propsPath}`], REMOTION);

console.log(`\n✅ Done. Your dispatch awaits: ${outFile}`);
