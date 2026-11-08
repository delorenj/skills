---
name: scientific-track-analysis
description: Gruvato-specific scientific method for beat/bar/time-signature analysis research. Composes the K-Dense scientific skills (hypothesis-generation, scientific-brainstorming, experimental-design, scientific-critical-thinking, literature-review, paper-lookup) with the project's own evidence rules so that every analysis claim is a falsifiable, human-verifiable experiment — never a benchmark-anchored guess or a vibe. Use whenever forming, ranking, or testing theories about why a beat map, bar placement, or meter reading is wrong on a real recording.
license: MIT (derived composition; original skills by K-Dense Inc., MIT)
metadata:
  version: "1.0"
  skill-author: "Gruvato (composed from K-Dense Inc. scientific-agent-skills)"
---

# Scientific Track Analysis

Structured experimentation for Gruvato's beat / bar / meter analysis. The
product question is always the same: **does the map a drummer hears as "right"
come out right** — not whether a metric on a synthetic set moved.

## When to use

- A real recording's beat bars or downbeats look or sound wrong
  (e.g. Stan's Blues Live, where the downbeat lives in Stan Getz's sax line,
  not the kit).
- Choosing between tracker changes, model swaps (Beat This! vs hand-written
  tracker), analysis source (Drums vs Full mix), or meter hypotheses.
- Deciding whether a benchmark result generalizes to live-band drift.

## The rules that come first (project invariants)

1. **The drummer is the ground truth.** The owner is sitting right there and
   is the best judge of whether it works or sounds bad. No benchmark replaces
   a human listening pass. Metrics support; they never conclude alone.
2. **Use automatic model routing.** Do not pin provider or model IDs unless
   the user requests it. Treat generated claims as unverified until checked
   against primary sources, code, tests or the owner's listening evidence.
3. **GMD is not proof of live-band performance.** Groove MIDI Dataset clips
   are correlated, click-locked and drums-only. A result there is a hypothesis
   input, not evidence about a sax-led live recording.
4. **Cloud inference only for big models.** Never run big models on
   big-chungus; never silently fall back to local. On-device phone experiments
   (Beat This! ONNX) are the sanctioned exception.
5. **Gruvato accepts audio bytes, never addresses.** Experiments use local
   copies of recordings the user has, Creative Commons, self-recorded, or
   synthetic audio — never streaming-extraction fixtures.
6. **Python/TS parity tests must pass** for any tracker change (float32
   parity suite in `tests/`).

## Workflow

### 1. Freeze the observation (use `hypothesis-generation`)

Before any interpretation, write down what was actually observed:
- Which recording, which channel (Original / No Drums / Solo Drums), which
  analysis source (Drums / Full mix).
- What the map claims (beats, downbeats, meter) vs. what the owner hears.
- Tracker version (`beat-track/5`), gate status, cached vs. fresh.

Wrong: "the bars are wrong." Right: "on Stan's Blues Live at ~3:12, the drawn
downbeats land a beat early against the sax phrase's natural one; Solo Drums
stem has no kick on the one in the first 8 bars."

### 2. Generate rival explanations before touching code

List at least three rival hypotheses, including non-algorithmic ones:
- Drums-only inference can't see the downbeat (melody-driven) — testable via
  the GRUV-152 source switcher.
- Tempo octave error (half/double confusion) — testable via meter chips.
- Bar phase off-by-one in the decode, not the onset detection.
- The human count itself follows the sax and the kit is genuinely ambiguous.

Preserve minority views. Consensus between agents is not truth.

### 3. Design the cheapest discriminating experiment

Prefer, in order:
1. **A/B in the player** (GRUV-152 source switch, meter chips) — owner judges
   in seconds, zero benchmark cost.
2. **Synthetic fixture with a planted failure mode** — the existing
   drum-groove fixture style: known-truth WAV, assert exact beats.
3. **Held-out real recordings the owner has judged by ear** — keep a small
   labeled set; never expand into a broad benchmark campaign without explicit
   owner request.
4. **Public datasets (GMD)** — only as a screening step, labeled as such.

An experiment needs: a falsifiable prediction written *before* looking at the
result, a single changed variable, and a pass/fail rule.

### 4. Apply critical thinking before believing a result (use `scientific-critical-thinking`)

- Did we tune on the set we then measured on? (selection bias)
- Does the metric answer the product question (does the bar feel right) or a
  proxy (onset F-score)?
- Survivorship: are we only looking at songs that analyzed successfully?
- Confounds: did tempo, channel, or cache state change along with the thing
  we're testing?

### 5. Literature before reinvention (use `paper-lookup`, `literature-review`)

Before inventing a method, check the beat/downbeat tracking literature:
- Downbeat tracking from full mixes vs. drum stems is a published problem
  (MIREX downbeat tasks, Böck, Davies, Durand, Peter et al.).
- Melody/harmony-driven meter estimation exists precisely because percussion
  is sometimes absent from the strong beat.
- Search arXiv / ISMIR proceedings for: downbeat tracking, meter analysis,
  beat tracking without percussion, beat transformer (Beat This!).

Cite what you use; note access dates. Located evidence ≠ validated for
Gruvato's use case — it still needs the step-3 experiment.

### 6. Record the decision

Every experiment ends in the issue evidence file:
observation → hypotheses → experiment → result (with the actual numbers or
the owner's words) → decision → what we are NOT doing.

## Anti-patterns (all burned real time on this project)

- Running a broad benchmark campaign before a human has heard the current
  state.
- Claiming "68/70 on GMD" as evidence a live jazz recording will be right.
- Letting an LLM rank candidates for missing acoustic evidence it cannot
  hear.
- Iterating on the tracker for hours while the fix was "analyze the full mix
  instead of the stem."

## Handoffs

- Idea stage: `scientific-brainstorming`
- Hypothesis shaping: `hypothesis-generation`
- Experiment architecture (factorial, adaptive): `experimental-design`
- Prior art: `paper-lookup` → `literature-review`
- Believability check: `scientific-critical-thinking`
- Numerical claims (if a comparison is ever numeric): `statistical-analysis`
  and `statistical-power`
