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
3. H3 — **Ambiguous ensemble**: even the full mix's strong beats could conflict
   with the sax line. A poor full-mix result alone does not distinguish missing
   acoustic information, an incorrect pulse, a bar-phase error or a mixed-meter
   representation limit.
4. H4 — **Decode/placement bug**: the analysis core is right but the decode
   or rendering shifts bars (cf. the pickup44 class of bugs, fixed
   2026-11-06). Test: compare stored core beats against rendered bars at the
   wrong passage.

**Historical pre-listening plan:** GRUV-152 provides an in-player Drums / Full
mix analysis choice with isolated maps and corrections. No benchmark campaign.

**Owner listening result, 2026-11-08:** “It Kinda worked really good! It wasn't
perfect, but Ithink it was Acceptable. all of the tracks were pretty much
perfect except for The jazz And Tom Sawye because I don't think it understands
when it switches to 5/4”. Version 0.2.41 / 2041 was installed in place and read
back on the S26 via hub catch-up. This is positive qualitative product feedback,
not a numerical accuracy measure or a verified meter/source-per-track label.
The user suspects a switch to 5/4; exact transition and count remain unverified.

**Current finding:** The normal player stores one bar-count version for the
whole song and selected analysis source. Exact synthetic 4→5→4 and 4→7→4
fixtures, with every true one pinned, show that a single global count still
mislabels beats. A representation-only experiment with manually supplied
section boundaries and counts preserves the beat timestamps and returns the
planted labels. It detects neither meter nor transition; see
`scripts/analysis/mixed-meter-probe.mjs` and GRUV-155.

**Decision:** Keep the working source comparison. GRUV-156 proposes a bounded,
reversible manual local-count audition; it is a draft, not an approved change.
Whether to change the default source or add automatic meter-change detection
remains undecided. Do not treat the earlier proposed decision rule as adopted.

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
