---
name: remotion-elevenlabs-voiceover
description: Generate professional AI voiceovers for Remotion videos using ElevenLabs. Use when the user needs to create voiceovers, audio narration, or text-to-speech for video content. Features scene-based generation with request stitching, character presets (narrator, salesperson, expert, dramatic, calm), single scene regeneration, automatic timing validation, and pronunciation dictionaries.
allowed-tools: Bash(node:*), Bash(npx:*), Bash(ffprobe:*), Bash(ffmpeg:*), Read, Glob, Grep, WebFetch
---

# ElevenLabs Voiceover Generation

Generate professional AI voiceovers for Remotion videos using ElevenLabs API.

## Prerequisites

- `ELEVENLABS_API_KEY` in `.env.local`

## Design System Integration

This skill automatically applies design rules when creating Remotion video compositions. The design system controls colors, typography, animations, and component styles.

### Design File Priority

When creating videos, Claude will look for design rules in this order:

1. **Project-specific design file**: `design.md` or `design-system.md` in project root
2. **Skill default**: `.claude/skills/remotion-elevenlabs-voiceover/design-system.md`
3. **Auto-extraction**: Extract from existing codebase (see below)

### Before Creating Videos

**IMPORTANT**: Before generating any Remotion video composition, Claude MUST:

1. **Check for design file**:
   ```bash
   # Look for design files in project
   ls design.md design-system.md 2>/dev/null || echo "No design file found"
   ```

2. **If no design file exists, extract from project**:
   - Read `app/globals.css` or `styles/globals.css` for CSS variables
   - Read `tailwind.config.js` or `tailwind.config.ts` for theme colors
   - Check existing Remotion components in `remotion/` for established patterns
   - Look for brand assets in `public/` (logo, fonts)

3. **If no project context, check website**:
   - If user provides a website URL, fetch and extract:
     - Color palette from CSS/computed styles
     - Typography (font families, sizes)
     - Logo and brand elements
   - Create a `design.md` based on extracted values

### Design Extraction Workflow

When no design file exists:

```
1. Glob for: globals.css, tailwind.config.*, design.md
2. Read found files to extract:
   - CSS custom properties (--primary, --background, etc.)
   - Tailwind theme extensions (colors, fonts)
   - Existing component patterns
3. Check remotion/ folder for existing video components
4. If user mentions a website:
   - WebFetch the URL
   - Extract visible design tokens
5. Synthesize into consistent design system
6. Optionally create design.md for future use
```

### Design System Contents

See `design-system.md` in this skill folder for the full specification including:

- **Colors**: Primary palette, accents, gradients
- **Typography**: Font families, sizes, weights, text styles
- **Layout**: Spacing scale, safe zones, video dimensions
- **Animation**: Timing, springs, easing functions
- **Components**: Cards, buttons, icons
- **Scene Types**: Hero, content, feature, CTA patterns

## Quick Start

```bash
# Generate voiceover from text
node .claude/skills/elevenlabs/generate.js --text "Your text here" --output public/audio/voiceover.mp3

# Generate with narrator style (more natural)
node .claude/skills/elevenlabs/generate.js --text "Your text" --character narrator --output voiceover.mp3

# Generate scenes with request stitching
node .claude/skills/elevenlabs/generate.js --scenes remotion/scenes.json --output-dir public/audio/project/

# Regenerate a single scene
node .claude/skills/elevenlabs/generate.js --scenes scenes.json --scene scene2 --new-text "Updated text"

# List available voices and character presets
node .claude/skills/elevenlabs/generate.js --list-voices
node .claude/skills/elevenlabs/generate.js --list-characters
```

## Character Presets

Use character presets for more natural voiceovers instead of literal screen text reading:

| Character | Description | Best For |
|-----------|-------------|----------|
| `literal` | Reads text exactly as written | Screen text, quotes |
| `narrator` | Professional storyteller, smooth, engaging | Explainers, documentaries |
| `salesperson` | Enthusiastic, persuasive, energetic | Marketing, ads |
| `expert` | Authoritative, confident, knowledgeable | Legal content, tutorials |
| `conversational` | Casual, friendly, natural | Social media, casual content |
| `dramatic` | Intense, emotional, impactful | Hooks, problem statements |
| `calm` | Soothing, reassuring, gentle | Trust-building, conclusions |

```bash
# Use narrator style globally
node .claude/skills/elevenlabs/generate.js --scenes scenes.json --character narrator --output-dir public/audio/

# Or set per-scene in scenes.json
{
  "scenes": [
    { "id": "scene1", "text": "Problem statement", "character": "dramatic" },
    { "id": "scene2", "text": "Solution", "character": "calm" }
  ]
}
```

## Scene-Based Generation with Request Stitching

Generate multiple scenes with consistent prosody using ElevenLabs request stitching:

### scenes.json Format

```json
{
  "name": "product-demo",
  "voice": "Antoni",
  "character": "narrator",
  "scenes": [
    {
      "id": "scene1",
      "text": "Welcome to our product demo. This will change everything.",
      "duration": 4.5,
      "character": "dramatic"
    },
    {
      "id": "scene2",
      "text": "Simple setup. Powerful features. Instant results.",
      "duration": 5.5
    },
    {
      "id": "scene3",
      "text": "Get started today with our free trial. No credit card required.",
      "duration": 8,
      "delay": 0.3
    }
  ]
}
```

### Generate All Scenes

```bash
node .claude/skills/elevenlabs/generate.js \
  --scenes remotion/product-demo-scenes.json \
  --output-dir public/audio/product-demo/
```

This creates:
- `product-demo-scene1.mp3` through `sceneN.mp3`
- `product-demo-combined.mp3` (all scenes stitched)
- `product-demo-info.json` (metadata with durations)

### Single Scene Regeneration

If a scene starts too early, has wrong timing, or needs different text:

```bash
# Regenerate scene2 with new text
node .claude/skills/elevenlabs/generate.js \
  --scenes remotion/scenes.json \
  --scene scene2 \
  --new-text "Updated scene 2 text" \
  --output-dir public/audio/project/

# Regenerate scene3 with different character
node .claude/skills/elevenlabs/generate.js \
  --scenes remotion/scenes.json \
  --scene scene3 \
  --character salesperson \
  --output-dir public/audio/project/

# Just regenerate (same text, same character)
node .claude/skills/elevenlabs/generate.js \
  --scenes remotion/scenes.json \
  --scene scene1 \
  --output-dir public/audio/project/
```

The tool automatically:
- Uses request stitching from previous scenes for consistent prosody
- Updates the info.json file with new metadata
- Updates scenes.json if `--new-text` is provided

## Timing Validation

The skill automatically validates timing after generation using `ffprobe`:

### What It Checks

| Check | Threshold | Description |
|-------|-----------|-------------|
| Duration mismatch | >15% | Warns if actual differs from expected duration |
| Leading silence | >200ms | Audio starts late (voiceover delayed) |
| Trailing silence | >500ms | Unnecessary silence at end |
| Speaking rate | 2-4.5 wps | Optimal ~3 words/second for German |

### Validate Existing Audio

```bash
# Validate all scenes in a project
node .claude/skills/elevenlabs/generate.js --validate public/audio/product-demo/
```

Output example:
```
🔍 Validating product-demo (6 scenes)

❌ scene1: 3.00s (expected: 4.5s)
   ❌ Audio 1.50s shorter than expected
   👍 8 words @ 3.1 words/sec
⚠️ scene2: 6.35s (expected: 5.5s)
   ⚠️ Leading silence: 235ms (may start late)
   🐢 10 words @ 1.8 words/sec
✅ scene4: 4.36s (expected: 4s)
   👍 9 words @ 2.3 words/sec

📊 Total duration: 30.80s (expected: 30.00s)
```

### Updated info.json

After validation, the info.json includes actual measurements:
```json
{
  "scenes": [
    {
      "id": "scene1",
      "duration": 4.5,
      "actualDuration": 3.0,
      "leadingSilence": 0.05,
      "wordsPerSecond": 3.1
    }
  ]
}
```

Use `actualDuration` in your Remotion composition for precise sync.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--text`, `-t` | Text to convert to speech | Required (or --file/--scenes) |
| `--file`, `-f` | Read text from file | - |
| `--output`, `-o` | Output file path | `output.mp3` |
| `--output-dir` | Output directory for scenes | `public/audio` |
| `--voice`, `-v` | Voice name or ID | `Antoni` |
| `--model`, `-m` | Model ID | `eleven_multilingual_v2` |
| `--character`, `-c` | Character preset | `literal` |
| `--scenes` | JSON file with scenes | - |
| `--scene` | Regenerate single scene ID | - |
| `--new-text` | New text for scene regen | - |
| `--validate` | Validate existing audio dir | - |
| `--skip-validation` | Skip auto-validation | false |
| `--stability` | Voice stability (0-1) | varies by character |
| `--similarity` | Voice similarity (0-1) | varies by character |
| `--style` | Style exaggeration (0-1) | varies by character |
| `--no-combined` | Skip combined file | false |

## Models

ElevenLabs offers different TTS models. Use `--model` to select:

| Model | ID | Best For |
|-------|-----|----------|
| **Multilingual v2** | `eleven_multilingual_v2` | Default. Great for German, stable, reliable |
| **Multilingual v3** | `eleven_multilingual_v3` | Newer model, potentially better quality |
| **Turbo v2.5** | `eleven_turbo_v2_5` | Faster generation, English-optimized |

```bash
# Use v3 model for higher quality
node .claude/skills/remotion-elevenlabs-voiceover/generate.js \
  --scenes remotion/scenes.json \
  --model eleven_multilingual_v3 \
  --output-dir public/audio/project/

# Or set in scenes.json
{
  "name": "my-project",
  "model": "eleven_multilingual_v3",
  "scenes": [...]
}
```

## Recommended Voices

| Voice | Style | Best For |
|-------|-------|----------|
| `Antoni` | Professional, warm | Legal content, explainers |
| `Arnold` | Authoritative, deep | Corporate, serious topics |
| `Josh` | Friendly, conversational | Marketing, casual content |

## Integration with Remotion

After generating scene voiceovers, use them in your composition:

```tsx
import { Audio, Sequence, staticFile } from "remotion";

// Use individual scene audio files for precise sync
const SCENE_DURATIONS = {
  scene1: 4.5,  // From info.json
  scene2: 5.5,
  scene3: 8.0,
};

export const VideoWithVoiceover: React.FC = () => {
  const { fps } = useVideoConfig();

  const scene1Frames = Math.round(SCENE_DURATIONS.scene1 * fps);
  const scene2Frames = Math.round(SCENE_DURATIONS.scene2 * fps);

  return (
    <>
      <Sequence from={0} durationInFrames={scene1Frames}>
        <Audio src={staticFile("audio/project/project-scene1.mp3")} />
        <Scene1Visual />
      </Sequence>

      <Sequence from={scene1Frames} durationInFrames={scene2Frames}>
        <Audio src={staticFile("audio/project/project-scene2.mp3")} />
        <Scene2Visual />
      </Sequence>
    </>
  );
};
```

## Tips for Best Results

1. **Use character presets**: Don't read screen text literally - use `narrator` or `expert` for natural flow
2. **Punctuation matters**: Use periods for pauses, commas for brief breaks
3. **Numbers**: Write out numbers ("fünfhundert" not "500")
4. **Abbreviations**: Write full words ("vierundzwanzig Stunden" not "24h")
5. **Scene-by-scene**: Different scenes can have different characters (dramatic intro, calm CTA)
6. **Fine-tune**: Use `--scene` to regenerate individual scenes without redoing everything
7. **Request stitching**: Keeps voice consistent across all scenes

## Workflow Example

```bash
# 1. Create scenes.json with your script
# 2. Generate all scenes with narrator style
node .claude/skills/elevenlabs/generate.js \
  --scenes remotion/my-video-scenes.json \
  --character narrator \
  --output-dir public/audio/my-video/

# 3. Preview in Remotion, notice scene2 starts too early
# 4. Regenerate just scene2 with updated text
node .claude/skills/elevenlabs/generate.js \
  --scenes remotion/my-video-scenes.json \
  --scene scene2 \
  --new-text "Slightly longer text to fill the visual timing" \
  --output-dir public/audio/my-video/

# 5. Update video composition with new duration from info.json
# 6. Repeat until timing is perfect
```

## Complete Video Creation Workflow

When asked to create a promo video or any Remotion video, follow this workflow:

### Step 1: Gather Design Context

```
1. Check for design.md in project root
2. Read globals.css for CSS variables
3. Read tailwind.config.* for theme colors
4. Check existing remotion/ components for patterns
5. Note logo path in public/ folder
```

### Step 2: Create Scene Content

Write a scenes.json file with:
- Compelling voiceover script (not literal screen text)
- Character presets per scene (dramatic intro, calm CTA)
- Appropriate duration estimates

### Step 3: Generate Voiceovers

```bash
node .claude/skills/remotion-elevenlabs-voiceover/generate.js \
  --scenes remotion/promo-scenes-{name}.json \
  --output-dir public/audio/promo-{name}/
```

### Step 4: Create Remotion Composition

Apply design system to the TSX component:

```tsx
// ALWAYS define colors from design system
const COLORS = {
  navy: "#1E3A5F",      // Primary dark
  primary: "#2C5282",   // Primary
  sky: "#A3C4E8",       // Light accent
  ice: "#E8F1F8",       // Very light
  white: "#FFFFFF",
  offWhite: "#FAFAFA",
  gray: "#6B7280",      // Muted text
  // Accent colors based on treatment type
  rose: "#F43F5E",
  gold: "#D4A574",
};

// ALWAYS use transition delay for scenes 2+
const TRANSITION_FRAMES = 18;

const Scene2Content: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // CRITICAL: Delay animations until after transition
  const animFrame = Math.max(0, frame - TRANSITION_FRAMES);

  return (
    <AbsoluteFill>
      {/* Use animFrame for all animations in scenes 2-5 */}
      <div style={{
        opacity: spring({ frame: animFrame, fps, config: { damping: 15 } }),
      }}>
        {/* Content */}
      </div>
    </AbsoluteFill>
  );
};
```

### Step 5: Audio Placement

**CRITICAL**: Place audio OUTSIDE TransitionSeries to avoid overlap:

```tsx
export const PromoVideo: React.FC = () => {
  const { fps } = useVideoConfig();

  // Calculate audio start times accounting for transitions
  const audio1Start = 0;
  const audio2Start = scene1Frames - TRANSITION_FRAMES;
  const audio3Start = audio2Start + scene2Frames - TRANSITION_FRAMES;

  return (
    <AbsoluteFill>
      {/* Audio sequences OUTSIDE TransitionSeries */}
      <Sequence from={audio1Start} durationInFrames={Math.ceil(DURATIONS.scene1 * fps)}>
        <Audio src={staticFile("audio/promo/scene1.mp3")} />
      </Sequence>
      <Sequence from={audio2Start} durationInFrames={Math.ceil(DURATIONS.scene2 * fps)}>
        <Audio src={staticFile("audio/promo/scene2.mp3")} />
      </Sequence>

      {/* Visual TransitionSeries */}
      <TransitionSeries>
        {/* Scenes without audio */}
      </TransitionSeries>
    </AbsoluteFill>
  );
};
```

### Step 6: Register & Render

```bash
# Add composition to Root.tsx
# Then render
npx remotion render CompositionName public/video/output.mp4 --codec h264
```

## Design System Checklist

Before creating any video, ensure you have:

- [ ] Identified primary brand colors
- [ ] Identified heading and body fonts
- [ ] Located logo file path
- [ ] Noted any accent colors for the content type
- [ ] Reviewed existing video components for patterns
- [ ] Set TRANSITION_FRAMES constant (usually 18)
- [ ] Created animFrame delay for scenes 2+
