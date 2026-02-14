# GOD Docs
### Guaranteed Organizational Documents

> *Documentation that knows when it's lying to you.*

---

## The Problem

Documentation rots. Everyone knows it. You write an architecture doc on Monday, ship a breaking change on Thursday, and by Friday the doc is a historical fiction that actively misleads anyone who reads it.

The industry response has been resignation. "Docs are always stale." "Just read the code." "We'll update it next sprint." (Nobody updates it next sprint.)

**GOD Docs reject this.** Not with better intentions or stronger culture — with *determinism*. If the system can detect when documentation is stale the same way it detects when tests fail, you can enforce freshness at the same layer you enforce everything else: the commit.

---

## What It Is

A GOD Doc is a **developer-facing architectural reference** that is:

- **Guaranteed to exist** at every level of the system hierarchy
- **Template-based** — consistent structure, no freeform drift
- **Dependency-tracked** — documents declare which other documents they depend on
- **Deterministically verifiable** — staleness is computed, not guessed

GOD Docs are NOT READMEs. READMEs are user-facing ("how to install"). GOD Docs are developer-facing ("what events does this emit, what does it consume, where does it sit in the pipeline, what contracts does it honor").

---

## Pre-Requisite: Domain Decomposition

Before writing a single GOD Doc, your repository must be partitioned into **non-overlapping domains**. Every source file belongs to exactly one domain. No exceptions.

```
repo/
├── auth-service/        # Domain: Identity
├── payment-gateway/     # Domain: Billing
├── notification-hub/    # Domain: Comms
├── event-bus/           # Domain: Infrastructure
└── docs/
    └── domains/         # One GOD Doc per domain
```

This isn't just organizational tidiness — it's what makes dirty-checking work. When files in `auth-service/` change, only the Identity domain's GOD Docs are flagged. Ambiguous ownership means ambiguous staleness, which means the whole system collapses into the same "maybe it's stale, maybe not" uncertainty you had before.

**If you can't cleanly decompose your repo into non-overlapping domains, GOD Docs aren't ready for you yet.** Fix that first.

---

## Three-Level Hierarchy

GOD Docs form a drill-down:

```
Level 0 — System        docs/GOD.md
Level 1 — Domain        docs/domains/{domain}/GOD.md
Level 2 — Component     {component}/GOD.md
```

**Level 0 (System)** is the 30,000-foot view. System topology diagram, domain reference table, component registry, cross-domain dependency graph. You read this when you're new, or when you need to understand how everything connects.

**Level 1 (Domain)** scopes to a single concern. Component map, intra-domain event contracts, cross-domain interfaces. You read this when you're working within a domain and need to know what talks to what.

**Level 2 (Component)** is the deep dive. Architecture position diagram, events emitted and consumed (with routing keys and payload schemas), CLI/API interface documentation, technical implementation notes. You read this when you're about to touch the code.

Each level links down to the next. Progressive disclosure. Never dump everything at one level.

---

## Templates, Not Prose

Every GOD Doc is created from a template:

```
docs/templates/
├── COMPONENT-GOD-TEMPLATE.md
└── DOMAIN-GOD-TEMPLATE.md
```

Templates use `{{PLACEHOLDER}}` tokens:

```markdown
# {{COMPONENT_NAME}} — GOD Document

> **Domain**: {{DOMAIN}}
> **Status**: {{STATUS}}

## Events Emitted

| Event | Routing Key | Payload Schema | Trigger |
|-------|-------------|----------------|---------|
| `{{EVENT_NAME}}` | `{{ROUTING_KEY}}` | `{{SCHEMA_REF}}` | {{TRIGGER}} |
```

This does two things:

1. **Structural consistency.** Every component GOD Doc has the same sections in the same order. A developer who's read one has read them all structurally — only the content changes.

2. **Lintability.** Unfilled placeholders are detectable:
   ```bash
   grep -r "{{" components/*/GOD.md && echo "FAIL: unfilled placeholders" && exit 1
   ```

Templates aren't suggestions. They're the schema.

---

## Inter-GOD Dependencies

This is the critical innovation that separates GOD Docs from "just more markdown files."

Every GOD Doc declares which other GOD Docs it depends on:

```markdown
<!-- GOD-DEPS:
  - event-bus/GOD.md
  - schema-registry/GOD.md
  - docs/domains/infrastructure/GOD.md
-->
```

These dependencies are semantic, not random: they mean "this component consumes events from that one" or "this component references schemas defined by that one."

When `schema-registry/GOD.md` changes (new types, removed fields, renamed events), every GOD Doc that declared it as a dependency is **transitively flagged stale**. Not because someone remembered to check — because the dependency graph made it automatic.

```
schema-registry/GOD.md changes
    → event-bus/GOD.md flagged (declares dep)
        → payment-gateway/GOD.md flagged (declares dep on event-bus)
    → auth-service/GOD.md flagged (declares dep)
```

The dependency graph is a DAG. Staleness propagates through it like a signal through a circuit.

---

## Deterministic Dirty-Check

The dirty-check answers one question: **"Which GOD Docs are stale given the current diff?"**

### The Algorithm

```
1. Collect changed files (git diff, staged or branch)
2. Map each file to its owning component
3. For each affected component:
   a. If source files changed but GOD.md didn't → DIRTY
   b. Flag parent domain GOD.md → DIRTY
   c. If component added/removed → flag system GOD.md
4. Walk the dependency graph:
   a. For each DIRTY GOD Doc D
   b. Find every GOD Doc declaring D as a dependency
   c. Flag those → TRANSITIVELY DIRTY
5. Output: DIRTY ∪ TRANSITIVELY DIRTY
```

### Enforcement Layers

**Layer 1 — Git Hook (local, pre-commit)**

Catches staleness before it leaves the developer's machine:

```bash
#!/bin/bash
CHANGED=$(git diff --cached --name-only --diff-filter=ACM)
STALE=()

for file in $CHANGED; do
    component=$(echo "$file" | cut -d'/' -f1)
    [ -f "$component/GOD.md" ] || continue
    echo "$CHANGED" | grep -q "^$component/GOD.md$" && continue
    STALE+=("$component/GOD.md")
done

if [ ${#STALE[@]} -gt 0 ]; then
    echo "⚠️  Stale GOD Docs: ${STALE[*]}"
    echo "[1] Update now  [2] Skip  [3] Abort"
    read -p "Choice: " c
    [ "$c" = "3" ] && exit 1
fi
```

Interactive. Lets the developer update now or defer (with a warning).

**Layer 2 — CI Action (PR gate)**

Blocks merge if GOD Docs are stale:

```yaml
name: GOD Doc Freshness
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Check staleness
        run: |
          CHANGED=$(git diff --name-only origin/main...HEAD)
          STALE=""
          for f in $CHANGED; do
            comp=$(echo "$f" | cut -d'/' -f1)
            [ -f "$comp/GOD.md" ] || continue
            echo "$CHANGED" | grep -q "^$comp/GOD.md$" && continue
            STALE="$STALE $comp/GOD.md"
          done
          [ -z "$STALE" ] || { echo "::error::Stale:$STALE"; exit 1; }
```

Non-negotiable. Stale docs = red CI = no merge.

**Layer 3 — Drift Detection CLI (deep audit)**

For transitive dependency resolution and drift severity analysis, you need more than a shell script. This is where a dedicated tool comes in.

We built one. It's called **Degenerate**.

---

## Degenerate: The Drift Detector

> *"Fight the entropy of documentation."*

[Degenerate](https://github.com/delorenj/33GOD/tree/main/degenerate) is a Rust CLI that implements the full GOD Doc dirty-check algorithm with transitive dependency resolution, git history analysis, and drift severity scoring.

### Why a Dedicated Tool?

The shell-script hooks handle the common case (source changed, GOD Doc didn't). But they can't:

- Resolve transitive dependencies (A depends on B depends on C; C changed)
- Score drift severity (is it 2 commits behind or 200?)
- Show *which* commits caused the drift
- Track sync state across sessions (when was this GOD Doc last verified fresh?)
- Handle submodule repos where components live in separate git histories

Degenerate does all of that.

### How It Works

Degenerate maintains a **sync state file** (`docs/sync/last-sync.json`) that records, for each component, the last git commit at which its GOD Doc was verified fresh:

```json
{
  "version": "0.1.0",
  "last_sync": "2026-02-11T12:00:00Z",
  "domains": {
    "infrastructure": {
      "services": ["bloodbank", "holyfields", "candystore"],
      "last_commit": "a3f8c91",
      "last_sync_date": "2026-02-11T12:00:00Z"
    }
  }
}
```

When you run `degenerate sync --dry-run`, it:

1. Loads the sync state
2. For each component, queries git for commits since `last_commit`
3. If there are commits touching source files but not GOD.md → **drift detected**
4. Walks the `GOD-DEPS` graph to find transitive staleness
5. Reports severity (commit count), affected files, and authors

```
$ degenerate sync --dry-run

🔍 Checking for documentation drift...

⚠ Infrastructure (12 commits behind)
    → bloodbank (8 commits)
    → holyfields (4 commits)

⚠ Agent Orchestration (3 commits behind)
    → flume (3 commits) [transitive: depends on bloodbank/GOD.md]

✓ Workspace Management (up to date)
✓ Dashboards & Voice (up to date)

Summary: 2 domain(s) with 15 total commits of drift.
Run `degenerate sync` to update documentation state.
```

### Core Commands

```bash
degenerate sync --dry-run          # Check drift without updating state
degenerate sync                    # Update all GOD Docs and mark as fresh
degenerate sync --domain infra     # Sync a single domain

degenerate drift                   # Quick drift report
degenerate drift --commits         # Include commit details per drifted service

degenerate report                  # Full health report (JSON or text)
degenerate report --format json    # Machine-readable for CI integration

degenerate init                    # Initialize GOD Doc structure in a new repo
```

### Architecture

Degenerate is built in Rust with:

- **git2** (libgit2 bindings) for commit history traversal without shelling out
- **walkdir** for file discovery across the repo tree
- **serde/serde_yaml** for sync state and registry.yaml parsing
- **pulldown-cmark** for parsing GOD Doc markdown (sync markers, dependency declarations)
- **colored + indicatif** for terminal output

It's fast. A full drift check across a 20-component monorepo runs in under 200ms.

---

## Lifecycle

### Creating a New Component

```bash
# 1. Copy the template
cp docs/templates/COMPONENT-GOD-TEMPLATE.md my-service/GOD.md

# 2. Fill every {{PLACEHOLDER}}
$EDITOR my-service/GOD.md

# 3. Declare dependencies
#    Add <!-- GOD-DEPS: ... --> with upstream GOD Docs

# 4. Register in parent domain GOD Doc
$EDITOR docs/domains/{domain}/GOD.md

# 5. Register in system GOD Doc component registry
$EDITOR docs/GOD.md

# 6. Verify
grep -c "{{" my-service/GOD.md    # Must be 0
degenerate sync --dry-run          # Must pass
```

### Normal Development Flow

```bash
# Write code
vim auth-service/src/handler.py

# Commit triggers hook
git add auth-service/src/handler.py
git commit -m "Add refresh token rotation"

# Hook fires:
# ⚠️ Stale GOD Docs: auth-service/GOD.md
# [1] Update now  [2] Skip  [3] Abort

# Developer updates GOD Doc, stages it
vim auth-service/GOD.md
git add auth-service/GOD.md
git commit --amend
```

### When to Update (Cheat Sheet)

| Change | Urgency | Enforcement |
|--------|---------|-------------|
| New/removed events | **Immediately** | CI blocks merge |
| API endpoint changes | **Immediately** | CI blocks merge |
| CLI interface changes | **Immediately** | CI blocks merge |
| New component added | **Immediately** | CI blocks merge |
| Internal refactor (no contract change) | Within sprint | Hook warns |
| Config/env changes | Within sprint | Hook warns |
| Performance optimization | Best effort | None |

---

## Why This Works (And Why READMEs Don't)

| | READMEs | Wiki | ADRs | GOD Docs |
|---|---|---|---|---|
| **Freshness** | ❌ Rots silently | ❌ Decoupled from code | ⚠️ Point-in-time snapshots | ✅ Deterministic dirty-check |
| **Structure** | ❌ Freeform | ⚠️ Varies by author | ✅ Template-based | ✅ Template-enforced |
| **Dependencies** | ❌ None | ❌ Manual cross-links | ❌ None | ✅ Declared, transitive |
| **Enforcement** | ❌ Honor system | ❌ Honor system | ❌ Honor system | ✅ Hook + CI + CLI |
| **Audience** | Users | Mixed | Architects | Developers |

The fundamental difference: GOD Docs make staleness **observable and enforceable**. Everything else relies on humans noticing and caring. Humans are bad at both.

---

## Design Principles

1. **Documentation is a build artifact.** If it can't be verified, it can't be trusted.

2. **Non-overlapping domains are the foundation.** Ambiguous file ownership makes dirty-checking impossible. Partition first, document second.

3. **Templates prevent structural drift.** Every GOD Doc looks the same. The tenth component doc you read is navigated the same way as the first.

4. **Dependencies are explicit and tracked.** "This component uses events from that one" isn't tribal knowledge — it's a declared, machine-readable relationship.

5. **Three enforcement layers beat one.** Hooks for local dev. CI for PRs. Degenerate for deep audits. Any single layer can be bypassed; all three together make staleness harder than freshness.

6. **Progressive disclosure.** System → Domain → Component. Never dump everything at one level. Let the reader drill down to the depth they need.

7. **Dev-facing, not user-facing.** GOD Docs exist for people building the system. READMEs exist for people using it. Different audiences, different documents, different update triggers.

---

## Getting Started

```bash
# Initialize GOD Doc structure
degenerate init

# Creates:
#   docs/GOD.md (system level)
#   docs/templates/COMPONENT-GOD-TEMPLATE.md
#   docs/templates/DOMAIN-GOD-TEMPLATE.md
#   docs/sync/last-sync.json
#   .githooks/pre-commit

# Enable the git hook
git config core.hooksPath .githooks

# Create your first domain
mkdir -p docs/domains/my-domain
cp docs/templates/DOMAIN-GOD-TEMPLATE.md docs/domains/my-domain/GOD.md

# Create your first component GOD Doc
cp docs/templates/COMPONENT-GOD-TEMPLATE.md my-service/GOD.md

# Fill it in, verify, commit
degenerate sync --dry-run
```

---

*GOD Docs were developed for [33GOD](https://github.com/delorenj/33GOD), an event-driven agentic pipeline. Degenerate is the reference implementation of the dirty-check system, written in Rust.*
