---
name: pipecat-init
description: Scaffold a new Pipecat project with guided setup
---

Scaffold a new Pipecat project by collecting configuration from the user and running `pipecat init` in non-interactive mode.

## Arguments

```
/init [<target-dir>]
```

- `<target-dir>` (optional): Directory to create the project in. Defaults to a new directory named after the project. Use `.` for the current directory.

## Prerequisites

Check if `pipecat` is installed by running `pipecat --version`. If not installed, tell the user to install it with `uv tool install pipecat-ai-cli` and stop.

## Discover Available Options

Before asking the user any questions, run `pipecat init --list-options` to get the current valid values for all fields. The output is JSON:

```json
{
  "bot_type": ["web", "telephony"],
  "transports": {
    "web": ["daily", "smallwebrtc"],
    "telephony": ["twilio", "telnyx", ...]
  },
  "stt": ["deepgram_stt", "openai_stt", ...],
  "llm": ["openai_llm", "anthropic_llm", ...],
  "tts": ["cartesia_tts", "elevenlabs_tts", ...],
  "realtime": ["openai_realtime", "gemini_live_realtime", ...],
  "video": ["heygen_video", "tavus_video", "simli_video"]
}
```

Use this data to populate the choices in every question below. Do NOT hardcode service lists — always use the values from `--list-options`.

## Configuration Flow

Walk through the following questions to build the project configuration. After collecting all answers, show a summary and run the command.

**Choosing the right interaction method:**
- **AskUserQuestion** — Use for questions with a small, fixed set of options (bot type, pipeline mode, client framework, yes/no questions). This gives a clean clickable UI.
- **Show list as text** — Use for questions with many options (STT, LLM, TTS, realtime, video, transports). Display the full list of available options from `--list-options` formatted as a readable list, then let the user reply with their choice in chat.

### Step 1: Project Name

Ask the user for a project name. This is passed as the target directory (positionally) — the project is scaffolded in place in a directory of that name, and the project identifier is derived from it.

### Step 2: Bot Type

Ask the user to choose a bot type:
- **Web/Mobile** (`web`) - Browser or mobile app
- **Telephony** (`telephony`) - Phone calls

### Step 3: Client Framework (web only)

If the bot type is `web`, ask the user to choose a client framework:
- **React** (`react`)
- **Vanilla JS** (`vanilla`)
- **None** (`none`) - Server only, no client generated

If the user chose React, ask which dev server:
- **Vite** (`vite`)
- **Next.js** (`nextjs`)

Skip this step entirely for telephony bots.

### Step 4: Transport

Show the user the full list of available transports from `--list-options`, filtered by the selected bot type. Let the user reply with their choice.

If the user chose a `daily_pstn` transport, ask for mode:
- Dial-in (receive calls) → use `--daily-pstn-mode dial-in`
- Dial-out (make calls) → use `--daily-pstn-mode dial-out`

If the user chose a `twilio_daily_sip` transport, ask for mode:
- Dial-in (receive calls) → use `--twilio-daily-sip-mode dial-in`
- Dial-out (make calls) → use `--twilio-daily-sip-mode dial-out`

Then ask if they want to add an additional transport for local testing. This is common — e.g. a telephony bot that also supports WebRTC for development.

### Step 5: Pipeline Mode

Ask the user to choose a pipeline architecture:
- **Cascade** (`cascade`) - STT → LLM → TTS pipeline
- **Realtime** (`realtime`) - Speech-to-speech model

### Step 6: AI Services

**If cascade mode**, show the full list of available options from `--list-options` for each service and let the user reply with their choice:

1. **Speech-to-Text (STT)** — Show all available STT services
2. **Language Model (LLM)** — Show all available LLM services
3. **Text-to-Speech (TTS)** — Show all available TTS services

**If realtime mode**, show all available realtime services and let the user reply with their choice.

For each service question, display the options as a numbered vertical list (one per line) so the user can easily scan and pick one.

### Step 7: Features

Show the user the default feature settings and ask if they want to customize:

**Defaults:**
- Audio recording: No
- Transcription logging: No
- Video avatar service: None
- Video input: No (web only)
- Video output: No (web only)
- Observability: No

If they want to customize, ask about each feature. For video avatar service (web bots only), use the video options from `--list-options`.

If a video avatar service is selected, video output is automatically enabled.

### Step 8: Deployment

Ask if they want to generate Pipecat Cloud deployment files (Dockerfile, pcc-deploy.toml). Default is yes.

If deploying to cloud, ask if they want to enable Krisp noise cancellation. Default is no.

## Building the Command

After collecting all answers, build the `pipecat init` command using non-interactive flags. Lead with the project name as the positional target directory — the project is scaffolded in place there:

```
pipecat init <project_name> \
  --bot-type <web|telephony> \
  --transport <transport> \
  --mode <cascade|realtime> \
  [--stt <service>] \
  [--llm <service>] \
  [--tts <service>] \
  [--realtime <service>] \
  [--video <service>] \
  [--client-framework <react|vanilla|none>] \
  [--client-server <vite|nextjs>] \
  [--daily-pstn-mode <dial-in|dial-out>] \
  [--twilio-daily-sip-mode <dial-in|dial-out>] \
  [--recording | --no-recording] \
  [--transcription | --no-transcription] \
  [--video-input | --no-video-input] \
  [--video-output | --no-video-output] \
  [--deploy-to-cloud | --no-deploy-to-cloud] \
  [--enable-krisp | --no-enable-krisp] \
  [--observability | --no-observability] \
  [--eval | --no-eval]
```

Passing scaffold flags makes `pipecat init` run non-interactively (no prompts) and scaffold the runnable bot in place, alongside the coding-agent guide files it writes (AGENTS.md, CLAUDE.md).

Use `.` as the target to scaffold into the current directory instead of a new one.

For multiple transports, repeat the `--transport` flag (e.g. `--transport twilio --transport smallwebrtc`).

## Confirmation

Before running the command, show the user a summary of their choices:
- Project name
- Bot type
- Client framework (if web)
- Transport(s)
- Pipeline mode and services
- Features enabled
- Deployment target

Ask the user to confirm before proceeding. If they want to change something, go back and re-ask that specific question.

## Running the Command

Run the `pipecat init` command. The positional target directory controls where the project is created — use the `<target-dir>` argument if the user provided one, otherwise default to a new directory named after the project.

If the command succeeds, show the user what was generated and suggest next steps:
1. `cd <project_name>/server`
2. Copy `.env.example` to `.env` and fill in API keys
3. Run the bot

If deploying to cloud, also mention they can use `/pipecat-cloud:deploy` to deploy.

## Error Handling

- If `pipecat init` fails with validation errors, show the error and help the user fix their choices.
- If the target directory already exists and is not empty, warn the user before proceeding.
