---
name: style-transfer-training
description: >-
  Route an image style-transfer task to the correct training architecture before
  any money is spent. Use when a user has a corpus of images in a target style
  (art style, historical photos, product shots, illustration) and wants to apply
  that look to new user-supplied photos. Covers the paired-vs-unpaired decision
  gate, style LoRA vs edit-model LoRA, dataset curation, identity preservation,
  and mandatory cheap-baseline evaluation. Trigger on "train a style LoRA",
  "apply my corpus style to a photo", "image to image style transfer",
  "reimagine this portrait as X", "fine-tune on my image dataset", or any
  request to train a diffusion model on a private image collection.
version: 1.0.0
author: delorenj
license: MIT
metadata:
  hermes:
    tags: [image-generation, lora, style-transfer, diffusion, fal.ai, flux, qwen, evaluation, fine-tuning]
    category: mlops
---

# Style Transfer Training

Getting a private image corpus to restyle user photos is a **solved, commodity
problem**. It goes wrong almost exclusively at the architecture-selection step,
in the first thirty seconds, and everything downstream becomes heroic effort to
rescue a choice that was never questioned.

**Your job is the decision gate, not the pipeline.** Work the gate before you
write a line of training code.

## The Decision Gate

Answer these three in order. Do not skip ahead.

### 1. Do you have PAIRED data?

A pair is **the same subject, twice, differing only in style** — a "before" and
an "after" of the identical scene.

| You have | Train | Do NOT train |
|---|---|---|
| Unpaired style exemplars (a folder of images that all *look* like the target) | **Style LoRA** on a text-to-image base (Flux, Qwen-Image, SDXL) | An edit-model LoRA |
| Genuine before/after pairs of the same subject | **Edit-model LoRA** (Qwen-Image-Edit, Flux Kontext) | — |

Almost everyone has the first row and thinks they need the second.

> **The single most common failure:** reaching for an *edit* model
> (Qwen-Image-Edit, Flux Kontext) because it markets itself as
> "content-preserving style transfer," then discovering it requires paired
> supervision you do not have, then manufacturing fake pairs to feed it.
> If you find yourself fabricating the missing half of a dataset, **stop** —
> you picked the wrong trainer. Go back to row one.

### 2. Have you tested zero-shot?

Modern base edit models are strong. Before training anything, run the plain base
model on a representative input with your target prompt. One inference,
~$0.02–0.05. You may need no training at all, and either way you now have the
floor your LoRA must beat.

**Never skip this.** It is the cheapest decisive experiment available and it
costs less than 1% of a training run.

### 3. Where does identity preservation come from?

**Inference time, not training time.** This trips people up constantly.

- Edit models condition on the input image in latent space — subject
  preservation is inherent to the architecture. You do not teach it.
- For a t2i style LoRA, identity comes from the *inference* mode: img2img at
  moderate denoise (~0.5–0.7), or a face-identity adapter (IP-Adapter, InstantID,
  PuLID) layered on top.

If someone proposes a training-data trick to "teach identity preservation," they
have misdiagnosed the problem. See `references/anti-patterns.md`.

## Dataset Curation

**Volume is not the asset you think it is.** Style LoRAs converge on 20–150
well-curated images. A corpus of thousands of mixed-quality images will train a
*worse* style LoRA than 100 hand-picked ones, because the model averages toward
whatever is most common — usually background, margin, and scan artifact.

Curation checklist:

- **Consistent framing.** Pick one crop convention and hold it.
- **Subject dominates the frame.** If the subject occupies 25% of the image and
  the rest is border, mount, or margin, the LoRA learns the border.
- **Decide about frames, mounts, and borders explicitly.** If the physical
  artifact (card mount, deckled edge, polaroid frame) *is* part of the style
  goal, keep it consistently. If not, crop it out consistently. **Never mix
  policies within one dataset.**
- **Cull aggressively.** Damaged, off-style, badly exposed, or atypical images
  hurt more than they help.
- **Captioning.** For style-only training, a single trigger token often beats
  detailed captions. Many trainers expose an `is_style` flag that disables
  subject segmentation and auto-captioning — use it.

## Cost Ladder

Always run the cheapest decisive experiment first.

| Step | Cost | Purpose |
|---|---|---|
| 1. Zero-shot base, held-out input | ~$0.02 | Establishes the floor. May end the project. |
| 2. Existing LoRA (if any), same seed/settings | ~$0.02 | Proves whether the LoRA does anything at all. |
| 3. Curate 100–150 images | free | Highest-leverage step in the whole process. |
| 4. Style LoRA training run | ~$2–4 | Only after 1–3. |
| 5. Identity adapter, if drift observed | ~$0.03/img | Add only if needed. |

Do not proceed to a step until the previous one has actually run and been
looked at by a human.

## Evaluation

Evaluation discipline is where agent-built pipelines fail silently. Read
`references/evaluation-protocol.md` before writing any eval code. The
non-negotiables:

1. Eval input must come from the **deployment domain** (what real users will
   upload), never from the training corpus.
2. Always compare **base vs. LoRA** on identical input, seed, and settings.
3. An API returning an image is **not** success. A human must look at it.

## Provider Notes

Verify current endpoints and pricing before quoting — this space moves fast.
As of early-to-mid 2026 on fal.ai:

- `fal-ai/flux-lora-fast-training` — unpaired style LoRA, has an explicit
  `is_style` flag that disables segmentation/auto-captioning. ~$2/run.
- `fal-ai/flux-lora-portrait-trainer` — portrait-tuned variant.
- `fal-ai/qwen-image-trainer` — Qwen-Image (t2i) LoRA.
- `fal-ai/qwen-image-edit-trainer` / `-2509-trainer` — **edit** model, requires
  real `_start`/`_end` pairs. Only reach for this if the gate says row two.

Managed API (fal, Replicate) for prototyping; serverless GPU (Modal) once
traffic justifies keeping something warm.

## Hard Guardrails

These are prohibitions, not preferences. Full rationale in
`references/anti-patterns.md`.

1. **Never construct identity pairs** (`_start` byte-identical to `_end`). The
   global optimum of that objective is "copy the input" — you are paying to
   train a no-op.
2. **Never evaluate on training-corpus images.** A test that cannot fail has
   told you nothing.
3. **Never report API success as model success.**
4. **Never fabricate missing training data with non-equivalent operations.**
   Pillow cannot colorize a grayscale image — it can gradient-map a tint, which
   is a different thing. Synthetic data that does not land in the real
   deployment domain creates a domain gap that surfaces at inference.
5. **Never skip the zero-shot baseline** before a paid training run.

## Reference Files

- `references/anti-patterns.md` — the failure modes above, with the mechanism
  behind each and how to detect them in an existing pipeline.
- `references/evaluation-protocol.md` — the base-vs-LoRA comparison procedure
  and the regression checks that keep an eval honest.
