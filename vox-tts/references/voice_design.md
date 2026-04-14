# Voice design without cloning

VoxCPM2 accepts an inline description at the **start** of the text, wrapped in parentheses. The model uses the description to pick vocal qualities (age, gender, pace, emotion, accent) without any reference audio. This is strictly more flexible than cloning for one-off or per-line voices.

## Shape

```
(description)actual text to speak
```

The parenthetical is consumed by the model and does not appear in the output audio.

## Examples by axis

### Age + gender

```
(A young woman with a bright, musical voice)Good morning!
(An elderly man speaking slowly and thoughtfully)Well, back in my day...
(A small child, excited)I found a frog!
```

### Emotion

```
(A woman speaking through tears)I can't believe you said that.
(An angry, gravelly voice)Enough. You've crossed a line.
(A warm, reassuring tone)It's going to be okay.
(A conspiratorial whisper)Don't tell anyone, but...
```

### Pace + rhythm

```
(Slow, deliberate narration)The door... creaked open.
(Rapid-fire, barely taking a breath)Okay-so-then-he-said-and-I-was-like-what
(Measured and clinical)The subject exhibits standard behavior.
```

### Accent / style

```
(A laid-back California surfer dude)Dude, that wave was gnarly.
(A refined British accent, crisp consonants)Indeed, rather quite pleasant.
(A gruff Brooklyn accent)You talkin' to me?
(A theatrical Shakespearean flourish)To be, or not to be.
```

### Compound traits

Stack descriptors. The model handles multiple constraints reasonably well, especially when they're non-contradictory.

```
(A tired middle-aged man, sarcastic and deadpan)Oh, fantastic. Another Monday.
(A cheerful young barista, fast-paced and friendly)Hi there! What can I get started for you today?
(A nervous teenager, voice cracking occasionally)Um... so... about the test...
```

## When description beats cloning

- **Per-line persona changes** (dialogue, multiple characters)
- **Unique emotion that a saved voice doesn't carry** (a normally-calm character suddenly panicking)
- **No good reference audio available**
- **A/B testing voice styles for a new project**
- **Accessibility / screen-reader style voices** that should be neutral

## When cloning beats description

- **A named recurring character/brand** (consistency matters more than flexibility)
- **The user provided a specific audio sample** to match
- **The output needs to be indistinguishable from a specific person** (this is the only path that preserves timbre)

## Parameter interplay

When using descriptions:

- **`cfg` 2.0-3.0** works well. Higher cfg makes the model cling harder to the description's constraints; go up if the voice drifts.
- **`steps` 10-15** is the sweet spot. Higher for dramatic/emotional reads, lower for short utterances.
- **`normalize: true`** helps when the text contains numbers, abbreviations, or punctuation that should be spoken (e.g. "vs.", "$100").

## Combining description with a clone

You can stack a style description on top of a voice clone. The clone sets the speaker timbre; the description shifts the prosody:

```json
{
  "text": "(slightly faster, cheerful tone)This is rick being uncharacteristically upbeat.",
  "voice": "rick"
}
```

Useful for reusing one voice across moods without maintaining multiple clones.

## Anti-patterns

- **Descriptions in the middle or end of the text** get spoken as dialogue. Always place at the start.
- **Descriptions longer than ~20 words** degrade output quality. Keep terse.
- **Contradictory constraints** (e.g. "a whispering, shouting voice") produce unpredictable output. Pick a lane.
- **Named impressions** ("like Morgan Freeman") are unreliable and may be filtered. Describe the qualities instead.
