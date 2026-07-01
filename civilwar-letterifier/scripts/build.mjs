#!/usr/bin/env node
/**
 * build.mjs — the multimodal pipeline for the Civil War Letterifier.
 *
 * The ONLY creative/agentic input is the note text itself — the period prose
 * (including its own cohesive closing sign-off and signature) written by
 * translating the source message. Everything else — the date line, title,
 * narrator voice, music, ambient bed, and render — is deterministic and handled
 * here. Given that note text, this:
 *   1. narrates it with ElevenLabs            -> remotion/public/narration.mp3
 *   2. resolves a music bed (drop-in or auto) -> remotion/public/music.mp3
 *   2b. resolves the ambient bed (assets/sfx) -> remotion/public/ambient.mp3
 *   3. writes render props                    -> remotion/props.json
 *   4. renders the Ken Burns documentary clip -> out/<name>.mp4
 *
 * The narrator voice is hardcoded (the custom "Civil War Veteran"); it is not
 * parameterized — see scripts/narrate.mjs. The ambient bed (assets/sfx) is an
 * always-on field-atmosphere layer beneath everything for the whole film,
 * independent of the optional music bed.
 *
 * Usage — pass the note as text, a text file, or a spec's letterText:
 *   node scripts/build.mjs --text "My dear colleagues, ..." --out out/letter.mp4
 *   node scripts/build.mjs --file note.txt
 *   node scripts/build.mjs --spec letter.json            (uses only .letterText)
 *   node scripts/build.mjs --text "..." --auto-music
 *   node scripts/build.mjs --text "..." --music assets/music/ashokan.mp3
 *   node scripts/build.mjs --text "..." --font dispatch  (script is the default)
 *
 * The date line ("From the Encampment, this Nth day of <Month>") is generated
 * from today's date; the title is a fixed constant below. The signature is NOT
 * added here — it is part of the letterified note (the model writes its own).
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

// --- Deterministic scaffolding --------------------------------------------
// The title card + date line never come from the agent. The signature is NOT
// here — it's part of the letterified note (the model writes its own cohesive
// sign-off), so it matches the letter's content instead of being a fixed string.
const TITLE = 'A Letter from the Front';

// "From the Encampment, this 30th day of June" — derived from today's date.
function periodDateLine() {
  const d = new Date();
  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];
  const day = d.getDate();
  const j = day % 10;
  const k = day % 100;
  const suffix =
    j === 1 && k !== 11 ? 'st' :
    j === 2 && k !== 12 ? 'nd' :
    j === 3 && k !== 13 ? 'rd' : 'th';
  return `From the Encampment, this ${day}${suffix} day of ${months[d.getMonth()]}`;
}

// --- Inputs (the note is the ONLY creative input) -------------------------
// Accept the period prose as --text, --file <txt>, or --spec <json>.letterText.
function readNoteText() {
  const t = arg('text');
  if (t && t !== true) return t;
  const f = arg('file');
  if (f && f !== true) return fs.readFileSync(path.resolve(f), 'utf8').trim();
  const s = arg('spec');
  if (s && s !== true) {
    const spec = JSON.parse(fs.readFileSync(path.resolve(s), 'utf8'));
    if (spec.letterText) return String(spec.letterText).trim();
  }
  return null;
}
const letterText = readNoteText();
if (!letterText) {
  console.error('Error: provide the note via --text "...", --file <txt>, or --spec <letter.json> (with letterText).');
  process.exit(1);
}

const musicPath = arg('music'); // explicit drop-in track
const autoMusic = arg('auto-music', false);
const noMusic = arg('no-music', false); // force voice-only (overrides drop-in/auto)
const ambientPath = arg('ambient'); // explicit ambient track (else assets/sfx)
const ambientVolume = parseFloat(arg('ambient-volume', '0.16'));
const noAmbient = arg('no-ambient', false); // force-skip the ambient layer

function pickRandomTrack(dir) {
  const files = fs.readdirSync(dir).filter((f) => /\.(mp3|wav|ogg|m4a|flac)$/i.test(f));
  if (files.length === 0) return null;
  return path.join(dir, files[Math.floor(Math.random() * files.length)]);
}
// The ambient bed lives in assets/sfx. Prefer a track literally named
// "ambient.*"; otherwise fall back to any audio file (random if several).
function pickAmbientTrack(dir) {
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir).filter((f) => /\.(mp3|wav|ogg|m4a|flac)$/i.test(f));
  if (files.length === 0) return null;
  const named = files.find((f) => /^ambient\.(mp3|wav|ogg|m4a|flac)$/i.test(f));
  const chosen = named || files[Math.floor(Math.random() * files.length)];
  return path.join(dir, chosen);
}
const outFile = path.resolve(arg('out', path.join(ROOT, 'out', 'letter.mp4')));
const introPad = parseFloat(arg('intro-pad', '3.5'));
const outroPad = parseFloat(arg('outro-pad', '4'));
const accentColor = arg('accent', '#5a2a16');
const fontStyle = arg('font') === 'dispatch' ? 'dispatch' : 'script';

fs.mkdirSync(PUBLIC, {recursive: true});

// --- 1. Narration ---------------------------------------------------------
// narrate.mjs uses the hardcoded "Civil War Veteran" voice; no voice argument.
const letterTxt = path.join(PUBLIC, '.letter.txt');
fs.writeFileSync(letterTxt, letterText);
run('node', [
  path.join(ROOT, 'scripts', 'narrate.mjs'),
  '--file', letterTxt,
  '--out', path.join(PUBLIC, 'narration.mp3'),
]);

// --- 2. Music bed ---------------------------------------------------------
const musicDest = path.join(PUBLIC, 'music.mp3');
let hasMusic = false;
if (noMusic) {
  console.log('\nMusic disabled (--no-music). Voice only.');
} else if (musicPath && musicPath !== true) {
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

// --- 2b. Ambient bed ------------------------------------------------------
// Always-on field atmosphere, layered beneath everything for the whole film,
// independent of whether a music bed was selected. Resolved from --ambient or,
// by default, from assets/sfx/.
const ambientDest = path.join(PUBLIC, 'ambient.mp3');
let hasAmbient = false;
if (noAmbient) {
  console.log('\nAmbient bed disabled (--no-ambient).');
} else if (ambientPath && ambientPath !== true) {
  fs.copyFileSync(path.resolve(ambientPath), ambientDest);
  hasAmbient = true;
  console.log(`\nUsing drop-in ambient bed: ${ambientPath}`);
} else {
  const ambientTrack = pickAmbientTrack(path.join(ROOT, 'assets', 'sfx'));
  if (ambientTrack) {
    fs.copyFileSync(ambientTrack, ambientDest);
    hasAmbient = true;
    console.log(`\nUsing ambient bed: ${ambientTrack}`);
  } else {
    console.log('\nNo ambient bed found in assets/sfx (skipping ambient layer).');
  }
}

// --- 3. Props -------------------------------------------------------------
const props = {
  letterText,
  dateLine: periodDateLine(),
  signature: '', // the sign-off is written into letterText by letterify
  title: TITLE,
  fontStyle,
  hasMusic,
  hasAmbient,
  narrationFile: 'narration.mp3',
  musicFile: 'music.mp3',
  ambientFile: 'ambient.mp3',
  ambientVolume,
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
