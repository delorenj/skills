---
name: beat-map-experiment-ledger
description: |
  Gruvato's running record of beat/bar/meter analysis experiments. One page per
  real observation: what the owner heard, the frozen observation, rival
  hypotheses, the discriminating experiment, the result, and the decision.
  Started 2026-11-08 with Stan's Blues Live. Consult before proposing any new
  analysis research; extend after every owner listening session.
license: internal
metadata:
  version: "1.0"
  skill-author: "Gruvato"
---

# Beat-map experiment ledger

The running scientific record for Gruvato beat/bar/meter analysis. Load this
whenever a beat map looks or sounds wrong, before proposing any research, and
after every owner listening session. Method: `scientific-track-analysis`.

## Active experiment: Stan's Blues Live (started 2026-11-08)

**Frozen observation (owner's words, 2026-11-08):**
"The beat bars for Stan's Blues Live are abysmally incorrect. When I switched
to drums, I had an epiphany; there's hardly any downbeat detected. It's not
always a kick drum our ears use to locate the downbeat. In this particular
recording, the only thing I can use personally with my human ears — the only
thing that feels natural — is that the downbeat is only detectable by paying
close attention to Stan Getz's driving saxophone melody."

**Recording:** Stan's Blues Live (jazz, live, sax-led). Channel used when the
observation was made: Solo Drums. Tracker: beat-track/5.

**Rival hypotheses (generated before testing):**
1. H1 — **Source-evidence failure.** The downbeat signal lives in the melody,
   not the kit; drums-only inference cannot find it. Discriminating test:
   GRUV-152 source switcher → Full mix analysis of the same recording should
   produce bars that feel right to the owner; drums analysis stays wrong.
   Falsifier: full mix is no better, or differently wrong.
2. H2 — **Tempo octave or bar-phase error**, independent of source: the tracker
   found the beats but counted from the wrong one. Test: meter chips (½×/2×
   and phase) fix the feel without changing analysis source.
3. H3 — **Ambiguous ensemble**: even the full mix's strong beats conflict with
   the sax line; no onset-based method will agree with the human count.
   Test: full mix still wrong → the gap is representational (phrase-level),
   not acoustic.
4. H4 — **Decode/placement bug**: the analysis core is right but the decode
   or rendering shifts bars (cf. the pickup44 class of bugs, fixed
   2026-11-06). Test: compare stored core beats against rendered bars at the
   wrong passage.

**Experiment running:** GRUV-152 (shipped 2026-11-08 as v0.2.41-pending):
in-player Drums / Full mix analysis choice with isolated maps and corrections.
Owner A/B listening on the S26 is the decision step. No benchmark campaign.

**Decision rule:** If H1 confirmed → full-mix becomes the default analysis
source where the drums stem is sparse, and the phrase-map grid
(2026-10-22 decision) uses ensemble evidence for bar location while keeping
drum-stem identity for phrase equivalence — exactly the owner's framing:
"whole ensemble locates bars; drum stem decides phrase equivalence."

## Resolved / historical

- **Performance is the clock** (decision 2026-11-06): beats follow actual
  performance timing, local corrections not global shift. Verified against
  synthetic fixtures and Funkorama/Rosanna; see
  `docs/decisions/2026-11-06-the-performance-is-the-clock.md`.
- **Beat This! benchmark** (2026-11): 68/70 on GMD vs 41/70 default on the
  reviewed set — recorded as a screening result only. GMD is click-locked,
  correlated, drums-only; it does not settle live-band drift. Full-size float32
  ONNX ≈ 83 MB; phone renderer ~1 GiB PSS. Decision pending: on-device /
  during-split / neither.

## Known instrument limits (do not re-discover)

- Kick-as-hard-on-3-as-1 is a documented tracker limit (KNOWN LIMIT test).
- A bar that isn't four beats must fail the gate, not claim ready.
- S26 full-audio benchmark attempt (2026-11-08) failed to return timings —
  adb dropped; ~1.13 GiB across app+WebView observed. Memory reduction for
  the Beat This! path is unproven.
