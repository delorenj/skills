---
name: pipecat-deploy
description: Deploy an agent to Pipecat Cloud
---

Deploy an agent to Pipecat Cloud. This skill walks through the full deployment process interactively, confirming each step with the user.

## Arguments

```
/deploy [--config <PATH>] [--env <PATH>]
```

- `--config` (optional): Path to `pcc-deploy.toml`. Defaults to `pcc-deploy.toml` in the current directory.
- `--env` (optional): Path to `.env` file for creating secrets. If not provided, the skill will look for a `.env` file in the same directory as the config file.

Examples:
- `/deploy`
- `/deploy --config examples/mybot/pcc-deploy.toml`
- `/deploy --config examples/mybot/pcc-deploy.toml --env examples/mybot/.env`

## Prerequisites

Before starting, verify these prerequisites and inform the user about any that are missing:

1. **Pipecat CLI**: Check if `pipecat` is installed by running `pipecat --version`. If not installed, tell the user to install it with `uv tool install pipecat-ai-cli` and stop.

2. **Pipecat Cloud authentication**: Check if `pipecat cloud auth whoami` succeeds. If not authenticated, do **not** try to run login yourself — `pipecat cloud auth login` opens a browser for an OAuth flow that Claude can't complete. Instead, tell the user to authenticate by running `pipecat cloud auth login` in their terminal (suggest the `! pipecat cloud auth login` form so the output lands in the session). Wait for them to confirm, then re-run `pipecat cloud auth whoami` to verify before proceeding.

3. **Configuration file**: Read the `pcc-deploy.toml` file (from `--config` argument or current directory). If it doesn't exist, tell the user they need a `pcc-deploy.toml` and stop. Parse and display the configuration to the user (agent_name, image, secret_set, etc.).

If any prerequisite fails, stop and clearly explain what needs to be fixed. Do not proceed to the next steps.

## Deployment Method

After prerequisites pass, ask the user how they want to deploy using AskUserQuestion:

- **Cloud Build (Recommended)**: Pipecat Cloud builds your Docker image from source. No local Docker required.
- **Self-managed image**: Build and push your own Docker image from your machine, then deploy.

## Important: Running Commands

All `pipecat cloud` commands must be run from the directory containing the `pcc-deploy.toml` file. Use `cd <dir> && <command>` to ensure the correct working directory.

Several `pipecat cloud` commands prompt for interactive confirmation which doesn't work in this environment. Skip the prompts with these flags:
- **`pipecat cloud deploy`**: Use `--force` (e.g., `pipecat cloud deploy --force`)
- **`pipecat cloud secrets set`**: Use the `--skip` flag (e.g., `pipecat cloud secrets set NAME --file .env --skip`)

`pipecat cloud docker build-push` runs non-interactively and has no confirmation prompt, so no extra flag is needed.

---

## Cloud Build Path

This path uses Pipecat Cloud to build your Docker image from source. No local Docker installation is required.

### Step 1: Verify Dockerfile and Lockfile

Check that a `Dockerfile` exists in the build context directory (the directory containing `pcc-deploy.toml`, or the `context_dir` from the `[build]` section of the config). If no Dockerfile is found, tell the user they need one and stop.

If the Dockerfile references `uv` (e.g., `uv sync`, `uv pip install`, `COPY uv.lock`), check that a `uv.lock` file exists in the build context directory. If it doesn't exist, run `uv lock` to generate it. If it already exists, run `uv lock` to ensure it's up to date. The lockfile must be present and current because cloud builds run remotely and cannot generate it.

### Step 2: Secrets Setup

Ask the user if they need to create or update secrets for this deployment.

- If yes, determine the env file path (from `--env` argument, or look for `.env` in the same directory as the config file, or ask the user).
- Read the `secret_set` name from the `pcc-deploy.toml` configuration.
- Run: `pipecat cloud secrets set {SECRET_SET_NAME} --file {ENV_FILE_PATH} --skip`
- Show the output to the user.

- If no, skip this step.

### Step 3: Deploy

Ask the user to confirm they want to deploy the agent.

- Show a summary of what will be deployed (agent_name, secret_set from the config).
- Run from the config directory: `pipecat cloud deploy --force`
- Use a generous timeout (10 minutes) as the cloud build and deployment can take a while.
- This command handles both the cloud build and the deployment automatically.
- If the command times out but no error occurred, retrieve the build ID from the command output and run `pipecat cloud build logs {BUILD_ID}` to check build progress. Share the output with the user.
- If the build succeeds but deployment times out, check agent logs with `pipecat cloud agent logs {AGENT_NAME}` and share with the user.
- Show the deployment output and status to the user.

### Cloud Build Error Handling

- If the build fails, retrieve the build ID from the command output and run `pipecat cloud build logs {BUILD_ID}` to show the user what went wrong.
- Common cloud build issues:
  - Missing or invalid Dockerfile
  - Build context too large (500MB limit) — check for large files that should be in `.dockerignore`
  - Build timeout — the build exceeded the maximum duration

---

## Self-Managed Image Path

This path builds and pushes the Docker image from your machine. Requires Docker to be installed and running.

### Step 1: Docker Prerequisites

Check these additional prerequisites:

- **Docker**: Check if `docker info` succeeds (daemon running). If not, tell the user to start Docker and stop.
- **Docker login**: Check if `docker login` succeeds. If not logged in, tell the user to run `docker login` and stop.

### Step 2: Secrets Setup

Ask the user if they need to create or update secrets for this deployment.

- If yes, determine the env file path (from `--env` argument, or look for `.env` in the same directory as the config file, or ask the user).
- Read the `secret_set` name from the `pcc-deploy.toml` configuration.
- Run: `pipecat cloud secrets set {SECRET_SET_NAME} --file {ENV_FILE_PATH} --skip`
- Show the output to the user.

- If no, skip this step.

### Step 3: Build and Push Docker Image

Ask the user if they want to build and push the Docker image.

- If yes:
  - First, check if `uv.lock` exists in the config directory. If so, run `uv lock` to ensure it's up to date before building.
  - Run from the config directory: `pipecat cloud docker build-push`
  - Use a generous timeout (5 minutes) as builds can take a while.
  - If the build fails due to a stale lockfile, run `uv lock` in the config directory and retry.
  - If the build fails for other reasons, show the error and ask the user how to proceed.

- If no, skip this step (image may already be pushed).

### Step 4: Deploy

Ask the user to confirm they want to deploy the agent.

- Show a summary of what will be deployed (agent_name, image, secret_set from the config).
- Run from the config directory: `pipecat cloud deploy --force`
- Use a generous timeout (5 minutes) as deployment may take time to reach ready state.
- If deployment times out but no error occurred, check logs with `pipecat cloud agent logs {AGENT_NAME}` and share with the user — the deployment may still be starting up.
- Show the deployment output and status to the user.

### Self-Managed Image Error Handling

- Common issues:
  - Docker not logged in to the image registry (`docker login`)
  - Missing `image` field in `pcc-deploy.toml`
  - Stale `uv.lock` file — run `uv lock` to fix

---

## General Error Handling

- If any `pipecat cloud` command fails, show the full error output and explain what might have gone wrong.
- Common issues for both paths:
  - Invalid or expired Pipecat Cloud authentication
  - Missing or malformed `pcc-deploy.toml`
  - Secret set name mismatch between config and what exists in Pipecat Cloud

## Completion

After a successful deployment, summarize what was done:
- Deployment method used (cloud build or self-managed image)
- Secrets created/updated (if applicable)
- Image built and pushed (if applicable)
- Agent deployed with name from config
