# Evaluation Protocol

The purpose of evaluation is to be **capable of disproving** that the model
works. If a test cannot fail, delete it — it is worse than no test, because it
manufactures false confidence.

## Held-Out Input Requirements

The eval input must satisfy all of:

1. **Deployment domain.** It looks like what real users will actually upload.
   For a "restyle my photo" product, that means a modern color photograph, not a
   sample from the style corpus.
2. **Outside the corpus.** Programmatically verify the file is not in the
   training set — by path, and by content hash against the corpus manifest.
3. **Stable across runs.** Use the same fixed input for every comparison so
   results are comparable over time. Freely-licensed images work well; record
   the attribution alongside it.
4. **Multiple subjects.** One image is enough to catch a passthrough. Three to
   five varied inputs (different lighting, skin tone, framing, age) are needed
   before believing a result generalizes.

## The Base-vs-LoRA Comparison

This is the core experiment. Run both arms with **identical** everything except
the LoRA:

| Held constant | Varied |
|---|---|
| input image, prompt, seed, guidance scale, inference steps, output format, resolution | LoRA present / absent |

Arm A: base model, no LoRA.
Arm B: same call plus `loras: [{path: <url>, scale: 1.0}]`.

Save for each arm: the output image, the exact request payload, the seed
actually used, the response URL, and wall-clock timing. Write a side-by-side
HTML or contact sheet.

**Then a human looks at it.** Not the agent. The interpretation step is where
motivated reasoning enters, and an agent that just built the pipeline is the
worst possible judge of it.

### Reading the result

- **Outputs near-identical** → the LoRA is doing nothing. Do not spend more on
  training until you understand why. Suspect identity-pair supervision first.
- **LoRA output changed but wrong** → supervision signal exists but is
  mistargeted. Check dataset curation and caption strategy.
- **LoRA output changed and better** → now sweep LoRA scale (0.6 / 0.8 / 1.0)
  and check for identity drift.
- **Base alone is already good enough** → ship it. Do not train.

### Scale sweep

Once the LoRA does something, run scale 0.6 / 0.8 / 1.0 / 1.2 on the same input
and seed. Style LoRAs frequently overpower the subject at 1.0. The best setting
is usually not the default.

## Identity Drift Check

If the product promises "you, but in this style," verify the output still looks
like the person. Options, cheapest first:

1. **Eyeball it** against the input, side by side.
2. **Face embedding cosine similarity** (ArcFace/InsightFace) between input and
   output. Track it as a number across experiments.
3. Add an identity adapter (IP-Adapter / InstantID / PuLID) only if 1 and 2 show
   real drift. Do not add it preemptively — it constrains the style.

Track the tension explicitly: **style strength and identity fidelity trade off
against each other.** Pick your operating point deliberately rather than
discovering it by accident.

## Regression Tests

Encode these so the failures cannot silently return:

```
test_pairs_not_identical        # no _start byte-identical to its _end
test_eval_input_not_in_corpus   # eval path/hash absent from training manifest
test_manifest_pair_integrity    # every _start has exactly one _end
test_mount_policy_consistent    # one crop policy per dataset, never mixed
test_split_deterministic        # same seed produces same train/val split
test_baseline_exists            # a no-LoRA artifact exists before any LoRA claim
test_success_not_from_shape     # success flag never set from response shape alone
```

## Reporting

An honest report states:

- what was actually run (commands, endpoints, seeds, cost)
- what the outputs looked like, including when they looked bad
- what remains unverified
- what it cost

An honest report never says "SUCCESS" on the basis that a well-formed response
came back. If the transformation was not visually confirmed on a held-out
deployment-domain input, the correct status is **unverified**.
