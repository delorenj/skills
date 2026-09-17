# CLI operation reference

## Core Operations

### Retain (store knowledge)

```bash
hindsight memory retain $BANK "npm test requires --experimental-vm-modules" \
  --context "debugging"
```

Context categories: `architecture`, `conventions`, `debugging`, `deployment`, `dependencies`, `preferences`, `session-summary`, `code-edit`

With document tracking (same `doc-id` = upsert, replacing old facts):

```bash
hindsight memory retain $BANK "Project deadline extended to April 15" \
  --context "conventions" --doc-id "sprint-notes-2026-03"
```

### Recall (retrieve context)

```bash
hindsight memory recall $BANK "What testing patterns does this project use?"
```

With options:

```bash
hindsight memory recall $BANK "How are auth and session management connected?" \
  --budget high --max-tokens 8192 --fact-type world,observation
```

Budget levels: `low` (fast, shallow), `mid` (balanced, default), `high` (deep graph traversal)

JSON output for programmatic use:

```bash
hindsight memory recall $BANK "query" -o json | jq '.results[].text'
```

### Reflect (synthesize with agentic reasoning)

Reflect runs an agentic loop: autonomously searches memories, applies bank disposition, generates grounded response with citations.

```bash
hindsight memory reflect $BANK "What architectural decisions have shaped this project?"
```

With context and higher budget:

```bash
hindsight memory reflect $BANK "Should we migrate to event sourcing?" \
  --context "architecture review" --budget high
```

Response includes `based_on.memories`, `based_on.mental_models`, `based_on.directives` for citation traceability.

## Mental Models (pre-computed reflect responses)

Mental models are curated summaries checked first during reflect. Faster, more consistent answers for recurring topics. Top of the retrieval hierarchy.

Name and source-query are **positional**, not flags (`--name` / `--source-query`
do not exist and error out):

```bash
hindsight mental-model create $BANK "Project Architecture" \
  "What is the overall system architecture?" --id project-architecture

hindsight mental-model list $BANK
hindsight mental-model get $BANK <id>
hindsight mental-model refresh $BANK <id>     # re-runs the source query
hindsight mental-model history $BANK <id>
hindsight mental-model delete $BANK <id>
```

Content generates asynchronously — a fresh model shows `Generating content...`
for a few seconds. Pass `--id` so the model has a stable, memorable handle.

**When to create one.** A mental model earns its place when a question recurs
*and* its answer is assembled from many scattered facts — "how does X work
here", "where do I add Y", "what fails silently". Retain the underlying facts
first; the model is computed *from* the bank, so an empty bank yields an empty
model. `refresh` after retaining new facts on that topic, or the model quietly
serves a stale answer with full confidence — the one real failure mode here.

## Directives (hard rules for reflect)

Always-enforced rules during reflect. Unlike disposition (soft personality influence), directives are strict behavioral constraints.

```bash
hindsight directive create $BANK \
  --name "Code Style" \
  --content "Always recommend Python type hints and strict typing"

hindsight directive list $BANK
hindsight directive update $BANK <directive_id> --active false
hindsight directive delete $BANK <directive_id>
```

## Documents (source tracking)

Documents track where memories came from. Re-retaining with the same `doc-id` replaces old facts (upsert). Deleting a document removes all its extracted memories.

```bash
hindsight document list $BANK
hindsight document get $BANK <document_id>
hindsight document delete $BANK <document_id>
```

## Bank Management

```bash
hindsight bank list
hindsight bank stats $BANK
hindsight bank disposition $BANK
hindsight bank disposition $BANK --skepticism 4 --literalism 3 --empathy 2
hindsight bank mission $BANK "Extract technical facts, conventions, and decisions."
```

## Disposition (Personality Traits)

Three traits (1-5 scale) that influence reflect behavior:

| Trait | Low (1) | High (5) |
|-------|---------|----------|
| **Skepticism** | Trusting, accepts claims | Questions and doubts claims |
| **Literalism** | Flexible interpretation | Exact, literal interpretation |
| **Empathy** | Detached, fact-focused | Considers emotional context |

## Retrieval Hierarchy (during reflect)

1. **Mental Models** - User-curated summaries (highest priority)
2. **Observations** - Consolidated knowledge (auto-generated from retained facts)
3. **Raw Facts** - Ground truth memories (world, experience, observation types)

## Fact Types

- **world** - Objective facts ("Alice works at Google")
- **experience** - Conversational events ("User asked about deployment")
- **observation** - Consolidated patterns (auto-synthesized from multiple facts)

