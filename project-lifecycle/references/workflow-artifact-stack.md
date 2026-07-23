# Workflow Artifact Stack

## Target Path

```text
Damian's intent
  -> workflow artifact generator/reviewer
    -> versioned workflow YAML/TOML
      -> Hermes conversational router
        -> generic MCP tools
          -> database state
```

## Layer Responsibilities

### Damian's Intent

Captures the coaching method in natural language: what the phase is for, what to ask, what to gather, what loops and gates matter, what the agent must never improvise, and when the coach approves progression.

The intent layer should be friendly to a non-engineer. Damian should be able to explain onboarding, Messages, LAMP visions, Breakthrough, or later processes in ordinary language.

### Workflow Artifact Generator/Reviewer

Turns intent into a structured, reviewable artifact. It should:

- extract phase objectives;
- identify fields, prompts, loops, gates, ratings, duplicate policies, and transitions;
- map extracted values to known database fields when strict fields exist;
- preserve loose notes when strict fields do not exist yet;
- produce a draft artifact for human review;
- flag ambiguity before implementation.

### Versioned Workflow YAML/TOML

Stores the actual workflow definition. It should include:

- workflow ID and version;
- phase or protocol ID;
- step IDs;
- field IDs;
- prompts;
- answer types;
- repeat policy;
- duplicate policy;
- rating requirements;
- clarification behavior;
- completion gates;
- next transitions;
- coach approval requirements.

This artifact is the bridge between coaching language and runtime behavior. It must be versioned so client sessions can reference the workflow version they used.

### Hermes Conversational Router

Hermes interprets natural replies and proposes guided actions. It should:

- understand clarification questions without advancing state;
- detect duplicate answers;
- infer structured values when safe;
- ask follow-up questions when missing required ratings or details;
- call only actions allowed by the current state;
- never be authoritative for writes or transitions.

### Generic MCP Tools

MCP tools are the stable backend API for state. They should be generic enough to handle onboarding or future phases:

- `client_state.get`
- `client_state.transition`
- `interview.get_state`
- `interview.validate_turn`
- `interview.record_answer`
- `interview.advance`

Existing profile/session/story tools remain lower-level primitives.

### Database State

The backend owns durable state and final validation. It should:

- store workflow versions;
- store interview/protocol session state;
- store responses, ratings, derived facts, objectives, and notes;
- enforce tenant and client isolation;
- enforce allowed transitions;
- preserve auditability and observability metadata.

## Architecture Rule

Hermes may interpret and propose. The backend validates, writes, advances, and returns the next allowed prompt.

## MVP Slice

The first implementation slice should focus on onboarding:

- migrate onboarding questions into a data-driven workflow artifact;
- route Telegram onboarding replies through Hermes when available;
- use MCP-backed interview tools for validation and persistence;
- fall back to deterministic script behavior when Hermes is unavailable;
- log whether each decision and response came from agent or script.
