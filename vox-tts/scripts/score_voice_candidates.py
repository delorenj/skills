#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#   "numpy<2.3", "soundfile", "librosa", "jiwer", "httpx",
#   "faster-whisper", "speechbrain", "resemblyzer",
#   "torch==2.5.1", "torchaudio==2.5.1", "setuptools<81",
# ]
# [tool.uv]
# index-url = "https://download.pytorch.org/whl/cpu"
# extra-index-url = ["https://pypi.org/simple"]
# index-strategy = "unsafe-best-match"
# ///
"""A/B-score voxxy voices against the speaker they are meant to clone.

Synthesizes the same test lines through every voice named on the command line
(POST /synthesize on the live service), then scores each output against a
reference recording of the target speaker:

  ecapa  - speechbrain ECAPA speaker similarity (cosine). The primary metric.
  reSim  - resemblyzer similarity. A second opinion; it is less discriminative.
  wer    - faster-whisper word error rate vs the requested text (garbling check).
  f0     - median pitch; compare against the reference's f0 to spot drift.

Every response's X-Vox-Engine header is checked. A line served by elevenlabs is
NOT a clone (ElevenLabs ignores reference audio), so it is retried and, if it
keeps falling back, excluded and reported - never scored.

Measured on arnold (2026-10-28): old upload 0.59 ecapa, clean cut 0.72, clean
cut + prompt_text 0.82-0.85. A difference under ~0.03 over 6 lines is noise.

Usage:
  score_voice_candidates.py --reference src.wav arnold ztmp-arnold-a ztmp-arnold-b
  score_voice_candidates.py --reference src.wav --lines 6 --json out.json v1 v2

Run it through `heavy` on big-chungus: it loads two speaker models and whisper.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time

# A system libtorch on LD_LIBRARY_PATH (big-chungus has ~/libtorch/lib there)
# shadows the wheel's own libs and torch dies with "undefined symbol". The
# loader reads the variable at exec time, so scrub it and re-exec once.
_ld = os.environ.get("LD_LIBRARY_PATH", "")
if "libtorch" in _ld:
    os.environ["LD_LIBRARY_PATH"] = ":".join(p for p in _ld.split(":") if p and "libtorch" not in p)
    os.execv(sys.executable, [sys.executable, *sys.argv])

import httpx
import numpy as np
import soundfile as sf

LINES = [
    "The deployment finished, and all of the tests are passing. Now we take a short break.",
    "Listen to me very carefully. If you do not commit your code, you will lose everything.",
    "Your pull request has been merged into main. Good job.",
    "I have reviewed the logs, and the database is down. We need to restart the server immediately.",
    "Hey, what's up? It's been a long day, but we got a lot of work done.",
    "Three tickets are still open on the board. Let's finish them before lunch, okay?",
    "The backup ran at two in the morning and copied forty gigabytes without a single error.",
    "I don't know about you, but I think this is the best idea we've had all week.",
]


def load16(data: bytes | str) -> np.ndarray:
    import librosa

    y, sr = sf.read(io.BytesIO(data) if isinstance(data, bytes) else data, always_2d=True)
    y = y.mean(axis=1).astype(np.float32)
    return librosa.resample(y, orig_sr=sr, target_sr=16000) if sr != 16000 else y


def synth(client: httpx.Client, url: str, voice: str, text: str, retries: int) -> tuple[bytes | None, str]:
    engine = "?"
    for attempt in range(retries + 1):
        r = client.post(f"{url}/synthesize", json={"text": text, "voice": voice})
        if r.status_code != 200:
            engine = f"http{r.status_code}"
        else:
            engine = r.headers.get("x-vox-engine", "?")
            if engine not in ("elevenlabs", "?"):
                return r.content, engine
        time.sleep(3 * (attempt + 1))
    return None, engine


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("voices", nargs="+", help="voice slugs to compare (current voice + candidates)")
    ap.add_argument("--reference", required=True, help="recording of the TARGET speaker (ideally the full source, not the cut)")
    ap.add_argument("--lines", type=int, default=4, help=f"test lines per voice (max {len(LINES)})")
    ap.add_argument("--url", default=os.environ.get("VOX_URL", "https://vox.delo.sh"))
    ap.add_argument("--retries", type=int, default=2, help="retries when a line falls back to elevenlabs")
    ap.add_argument("--keep", help="directory to keep the synthesized WAVs in")
    ap.add_argument("--json", dest="json_out", help="write per-voice results here")
    args = ap.parse_args()

    import jiwer
    import librosa
    import torch
    from faster_whisper import WhisperModel
    from resemblyzer import VoiceEncoder, preprocess_wav
    from speechbrain.inference.speaker import EncoderClassifier

    lines = LINES[: max(1, min(args.lines, len(LINES)))]
    resem = VoiceEncoder("cpu", verbose=False)
    ecapa = EncoderClassifier.from_hparams(
        "speechbrain/spkrec-ecapa-voxceleb",
        savedir=os.path.expanduser("~/.cache/voxxy/ecapa"),
        run_opts={"device": "cpu"},
    )
    whisper = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8")

    def cos(a, b) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def ecapa_emb(y):
        return ecapa.encode_batch(torch.tensor(y)[None]).squeeze().numpy()

    def words(s: str) -> str:
        return " ".join(re.sub(r"[^a-z0-9' ]", " ", s.lower()).split())

    ref = load16(args.reference)
    r_ref, e_ref = resem.embed_utterance(preprocess_wav(ref, 16000)), ecapa_emb(ref)
    f0_ref = np.nanmedian(librosa.pyin(ref, fmin=55, fmax=500, sr=16000, frame_length=1024, hop_length=160)[0])
    print(f"reference {args.reference}: {len(ref) / 16000:.1f}s, median f0 {f0_ref:.1f} Hz", file=sys.stderr)

    if args.keep:
        os.makedirs(args.keep, exist_ok=True)
    results: dict[str, dict] = {}
    with httpx.Client(timeout=180) as client:
        for voice in args.voices:
            rows, fallbacks = [], []
            for i, text in enumerate(lines):
                wav, engine = synth(client, args.url, voice, text, args.retries)
                if wav is None:
                    fallbacks.append(engine)
                    print(f"  {voice} line {i}: NOT CLONED (engine={engine}), excluded", file=sys.stderr)
                    continue
                if args.keep:
                    with open(os.path.join(args.keep, f"{voice}-{i}.wav"), "wb") as fh:
                        fh.write(wav)
                y = load16(wav)
                hyp = " ".join(s.text for s in whisper.transcribe(y, language="en")[0])
                f0 = librosa.pyin(y, fmin=55, fmax=500, sr=16000, frame_length=1024, hop_length=160)[0]
                rows.append({
                    "ecapa": cos(ecapa_emb(y), e_ref),
                    "reSim": cos(resem.embed_utterance(preprocess_wav(y, 16000)), r_ref),
                    "wer": jiwer.wer(words(text), words(hyp)),
                    "f0": float(np.nanmedian(f0)),
                })
                print(f"  {voice} line {i}: ecapa {rows[-1]['ecapa']:.3f} wer {rows[-1]['wer']:.2f} engine {engine}", file=sys.stderr)
            agg = {k: float(np.mean([r[k] for r in rows])) for k in ("ecapa", "reSim", "wer", "f0")} if rows else {}
            results[voice] = {**agg, "lines": len(rows), "fallbacks": fallbacks, "per_line": rows}

    print(f"\n{'voice':28s} {'ecapa':>6s} {'reSim':>6s} {'wer':>5s} {'f0':>6s}  (ref f0 {f0_ref:.0f})")
    for voice, r in sorted(results.items(), key=lambda kv: -kv[1].get("ecapa", -1)):
        if not r["lines"]:
            print(f"{voice:28s} no cloned output ({', '.join(r['fallbacks'])})")
            continue
        warn = f"  ({len(r['fallbacks'])} line(s) fell back, excluded)" if r["fallbacks"] else ""
        print(f"{voice:28s} {r['ecapa']:6.3f} {r['reSim']:6.3f} {r['wer']:5.2f} {r['f0']:6.1f}{warn}")
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump({"reference": args.reference, "reference_f0": float(f0_ref), "voices": results}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
