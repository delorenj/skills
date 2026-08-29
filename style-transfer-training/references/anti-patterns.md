# Anti-Patterns in Image Style Training

Each of these was observed in a real pipeline. Each looked like progress at the
time. Each is listed with its mechanism and a detection method, because these
failures are invisible from the outside — the job completes, an image comes
back, and everything reports green.

---

## 1. Identity Pairs

**What it looks like:** an edit-model trainer expects `{slug}_start.jpg` and
`{slug}_end.jpg`. You have unpaired style exemplars. So each image is written
twice, once as `_start` and once as `_end`, with a caption describing the
transformation you *want*.

Justification usually offered: *"this teaches the model to preserve identity
while absorbing the style."*

**Why it fails:** the training objective is "given `_start` as clean
conditioning plus the caption, reconstruct `_end`." When `_start == _end`, the
loss-minimizing solution is to **copy the input**. That is not a subtle bias —
it is the global optimum of the objective. You are paying to teach the model
that your instruction phrase means *do nothing*, and it gets worse with more
steps, not better.

There is a weak counter-current: because every target shares the style, the LoRA
absorbs some style prior into its output distribution, the way a t2i style LoRA
would. So the result is not pure passthrough. But two gradients are fighting and
the copy signal is stronger.

**The rule:** a pair teaches identity preservation when the two images show the
same subject and *differ in style*. Zero style delta means zero learnable
transformation.

**Detection:**
```bash
# hash the two halves of each pair — any match is a bug
find dataset -name '*_start.jpg' | while read s; do
  e="${s%_start.jpg}_end.jpg"
  [ "$(md5sum < "$s")" = "$(md5sum < "$e")" ] && echo "IDENTICAL: $s"
done
```
Add this as a test that fails the build.

**The actual fix:** do not use an edit-model trainer for unpaired data. Train a
style LoRA on a t2i base instead. Manufacturing pairs is treating the symptom.

---

## 2. The Rigged Evaluation

**What it looks like:**
```python
test_img = random.choice(images)   # `images` is the training corpus
```
The model is fed a training-corpus image and asked to make it look like the
style it is already in. It succeeds. The pipeline logs `✅ SUCCESS`.

**Why it fails:** the test cannot fail. It has never once exercised the
transformation the product actually needs (deployment-domain input → target
style). It measures nothing.

**Detection:** trace the eval input back to its source. If it comes from the
same directory, glob, or list as the training data, the eval is invalid. Assert
this in code — the eval input path must be outside the training corpus.

---

## 3. API Success Reported as Model Success

**What it looks like:** `if response.images: log("✅ Test inference SUCCEEDED")`.

**Why it fails:** conflates "the HTTP call returned a well-formed payload" with
"the model did the thing." Diffusion endpoints essentially always return an
image. The check is measuring uptime.

**Detection:** any success determination made from response *shape* rather than
response *content*. Success requires a human looking at a side-by-side.

---

## 4. Fabricated Data via Non-Equivalent Operations

**What it looks like:** needing synthetic "modern photo" inputs from historical
grayscale targets, and implementing the colorize step with Pillow because the
real models are not installed.

**Why it fails:** Pillow has no colorization operation. It can gradient-map a
grayscale image to a tint ramp, which is categorically not the same as neural
colorization. The synthetic inputs end up as tinted period scans — nowhere near
the domain of a real phone photo. The LoRA learns *tint → sepia*, then a real
user upload arrives from a completely different distribution and the model falls
over.

This one is insidious because the code is often *honest in its comments* ("do
not silently pretend this equals neural restoration") and then ships as the
runnable default anyway.

**Detection:** for any synthetic data stage, ask "does the synthetic side
actually land in the domain my real inputs come from?" If a human can tell
synthetic inputs from real ones at a glance, so can the model.

**Also:** if you do synthesize pairs, vary the synthesis parameters per image.
Otherwise the LoRA learns to invert your specific pipeline's artifacts rather
than the general transformation.

---

## 5. Skipping the Zero-Shot Baseline

**What it looks like:** going straight to a training run because training is
"only $4."

**Why it fails:** you now have no floor. When the LoRA output looks plausible
you cannot tell whether the LoRA did it or the base model would have done it
anyway. Every subsequent decision is made blind, and the sunk cost makes the
architecture harder to question.

**Detection:** no baseline artifact exists in the eval output directory.

---

## 6. Volume Mistaken for Quality

**What it looks like:** "we have 2,500 images, this should be easy."

**Why it fails:** style LoRAs converge on 20–150 curated images. Large
uncurated corpora drag the learned style toward whatever is most *common* rather
than most *representative* — typically background, border, mount, and margin
rather than the aesthetic you care about. Training on everything is both more
expensive and worse.

**Detection:** was any image ever rejected? If the dataset size equals the
corpus size, no curation happened.

---

## Meta: Why Agents Produce These

Every failure above survived review because the *layer above* accepted a
downstream report at face value. An architecture choice made in a three-sentence
answer became a fixed premise; subsequent workers optimized within it rather
than questioning it.

When reviewing an agent-built training pipeline, audit the **premise**, not just
the implementation. The code is usually fine. The thing it was told to build is
the problem.
