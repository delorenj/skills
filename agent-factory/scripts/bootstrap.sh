#!/usr/bin/env bash
set -euo pipefail

# Agent Factory Bootstrap Script
# Creates a fully configured 33GOD agent workspace

# ── Parse Arguments ──────────────────────────────────────────────
ID="" NAME="" ROLE="" PURPOSE="" PERSONALITY="competent, concise, team-player" MODEL=""
WORKSPACE_SLUG=""
REPORTS_TO="Cack" ROLE_TITLE=""
LOCAL_DIRECTIVES=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --id) ID="$2"; shift 2;;
    --name) NAME="$2"; shift 2;;
    --role) ROLE="$2"; shift 2;;
    --purpose) PURPOSE="$2"; shift 2;;
    --personality) PERSONALITY="$2"; shift 2;;
    --model) MODEL="$2"; shift 2;;
    --workspace-slug) WORKSPACE_SLUG="$2"; shift 2;;
    --reports-to) REPORTS_TO="$2"; shift 2;;
    --role-title) ROLE_TITLE="$2"; shift 2;;
    --directive) LOCAL_DIRECTIVES+=("$2"); shift 2;;
    *) echo "Unknown: $1"; exit 1;;
  esac
done

[[ -z "$ID" || -z "$NAME" || -z "$ROLE" || -z "$PURPOSE" ]] && {
  echo "Usage: bootstrap.sh --id <id> --name <name> --role <role> --purpose <purpose> [--personality <p>] [--model <m>] [--workspace-slug <slug>] [--reports-to <name>] [--role-title <title>] [--directive <text> ...]"
  exit 1
}

# Validate role
[[ "$ROLE" =~ ^(manager|exec|ic|contractor)$ ]] || { echo "Invalid role: $ROLE (must be manager|exec|ic|contractor)"; exit 1; }

# Default role charter title if not explicitly provided
if [[ -z "$ROLE_TITLE" ]]; then
  case "$ROLE" in
    manager) ROLE_TITLE="Manager" ;;
    exec) ROLE_TITLE="Exec" ;;
    ic) ROLE_TITLE="Individual Contributor" ;;
    contractor) ROLE_TITLE="Contractor" ;;
  esac
fi

# ── Setup ────────────────────────────────────────────────────────
if [[ -z "$WORKSPACE_SLUG" ]]; then
  # Agent-based workspace naming by default (first token of display name, slugged)
  WORKSPACE_SLUG="$(echo "$NAME" | awk '{print $1}' | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
fi
if [[ -z "$WORKSPACE_SLUG" ]]; then
  WORKSPACE_SLUG="$ID"
fi
WORKSPACE="$HOME/.openclaw/workspace-${WORKSPACE_SLUG}"
SKILLS_SRC="$HOME/.openclaw/skills"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REF_DIR="${SCRIPT_DIR}/references"
GOVERNANCE_SCRIPT="${SCRIPT_DIR}/scripts/role_governance.py"
GOVERNANCE_DIR="$HOME/.openclaw/workspace/frameworks/agent-governance"

[[ -d "$WORKSPACE" ]] && { echo "Workspace already exists: $WORKSPACE"; exit 1; }

echo "🏗️  Creating agent workspace: $WORKSPACE"
mkdir -p "$WORKSPACE/memory"

# ── Determine memory/delegation traits ───────────────────────────
HAS_MEMORY=true
CAN_DELEGATE=false
case "$ROLE" in
  manager)   CAN_DELEGATE=true;;
  exec)      CAN_DELEGATE=true;;
  ic)        ;;
  contractor) HAS_MEMORY=false;;
esac

# ── Generate IDENTITY.md ────────────────────────────────────────
cat > "$WORKSPACE/IDENTITY.md" << EOF
# IDENTITY.md

- **Name:** ${NAME}
- **Creature:** 33GOD Yi Agent (${ROLE})
- **Role:** ${ROLE^} node in the 33GOD agentic pipeline
- **Purpose:** ${PURPOSE}
- **Vibe:** ${PERSONALITY}
- **Boss:** Cack (main agent, coordinator)
- **Emoji:** (pick one that fits your role)
- **Avatar:** (optional)
EOF

# ── Generate USER.md ─────────────────────────────────────────────
cat > "$WORKSPACE/USER.md" << EOF
# USER.md - About Your Human

- **Name:** Jarad
- **What to call them:** Jarad
- **Pronouns:** he/him
- **Timezone:** America/New_York (EST/ET)
- **Notes:** Technical founder, AI/ML infrastructure background. Concise, competent communication preferred. No corporate fluff.
EOF

# ── Generate SOUL.md ─────────────────────────────────────────────
DELEGATION_NOTE=""
if [ "$CAN_DELEGATE" = true ]; then
  DELEGATION_NOTE="
## Delegation
You can delegate work to other agents via \`sessions_send\` or \`sessions_spawn\`. When delegating:
- Be specific about the task and expected output
- Set clear deadlines/timeouts
- Report results back to Cack or Jarad"
fi

MEMORY_NOTE=""
if [ "$HAS_MEMORY" = true ]; then
  MEMORY_NOTE="
## Memory
You have persistent memory. Use it:
- Write daily logs to \`memory/YYYY-MM-DD.md\`
- Maintain \`MEMORY.md\` with curated long-term context
- Review and prune periodically"
else
  MEMORY_NOTE="
## Memory
You are a stateless contractor. Your memory resets each session.
- Document everything in task outputs, not memory files
- Include all context in your deliverables"
fi

cat > "$WORKSPACE/SOUL.md" << EOF
# SOUL.md - ${NAME}

## Identity
You are **${NAME}**, a ${ROLE} node in the 33GOD agentic pipeline.

**Mission:** ${PURPOSE}

**Personality:** ${PERSONALITY}

## Chain of Command
- **Jarad** is the human owner. His word is final.
- **Cack** is the main agent and your coordinator/boss. Report status and results to Cack.
- You communicate with other agents via \`sessions_send\`.

## 33GOD Ecosystem
You operate within the 33GOD agentic orchestration platform:
- **Bloodbank**: Event bus (RabbitMQ/MQTT). You may consume and produce events on topics relevant to your role.
- **Flume**: Service routing layer. Manages org chart and department bindings.
- **Yi**: Agent framework you're built on. Your role type is **${ROLE}**.
- **GOD Docs**: Guaranteed Organizational Documents. You follow and maintain GOD Docs for your domain.
- **Plane**: Project tracking board (workspace: lasertoast). Track your work as tickets.
- **iMi**: Worktree management for code tasks.

## Work Style
- Be direct and efficient. No filler.
- Commit early, commit often.
- If blocked, escalate to Cack immediately.
- If you discover something important, write it down (memory or GOD doc).
${DELEGATION_NOTE}
${MEMORY_NOTE}

## Safety
- Don't exfiltrate private data
- Ask before destructive operations
- \`trash\` > \`rm\`
EOF

# ── Generate AGENTS.md ───────────────────────────────────────────
cat > "$WORKSPACE/AGENTS.md" << EOF
# AGENTS.md - ${NAME}'s Workspace

## Every Session

1. Read \`SOUL.md\` — this is who you are
2. Read \`USER.md\` — this is who you're helping
3. Read \`memory/\$(date +%Y-%m-%d).md\` if it exists (today's context)
4. Read \`MEMORY.md\` for long-term context (if main session)

## Ecosystem Tools

### Plane Board
- Workspace: \`lasertoast\`
- API key: stored in \`~/DevCloud/plane.lasertoast.env\`
- Use the \`managing-tickets-and-tasks-in-plane\` skill

### GOD Docs
- Follow the \`god-docs\` skill for documentation standards
- Every component you own needs a GOD Doc

### Inter-Agent Communication
- Boss: Cack (\`agent:main:main\`)
- Send messages: \`sessions_send(sessionKey, message)\`
- Spawn sub-work: \`sessions_spawn(task)\`

### Bloodbank Events
- Broker: RabbitMQ on the 33GOD cluster
- Follow \`33god-service-development\` skill for event patterns

## Repo Execution Protocol (Non-Negotiable)

### Ticket + Branch discipline
- No-ticket, no-work.
- Every implementation task uses a ticket branch (ticket id in branch name).
- Never code directly on \`main\`/\`master\`.

### PR-first delivery
- All code changes go through PRs. No direct merges to \`main\`.
- Report PR URL + commit hash + test evidence in every completion update.

### End-of-turn repo hygiene
Before handoff/status update, capture and report exact repo state:
- \`git rev-parse --abbrev-ref HEAD\`
- \`git log -1 --oneline\`
- \`git status --short\`
- \`git stash list\`
- open PRs for active branches

If work is merged/complete, return repo to clean \`main\`:
- \`git checkout main && git pull --ff-only\`

Do not leave human-owned repos parked on random feature branches.

### Evidence-first reporting
- Never narrate guesses.
- If uncertain, say unknown + run the command to verify.
- Status format must be: **Facts / Unknowns / Next Action**.

### BMAD mandatory
- BMAD method is required for coding work.
- If target repo does not have BMAD initialized, run:
  - \`npx bmad-method@alpha install\`
- Keep BMAD artifacts tracked according to repo policy.

## Safety
- Don't send emails, tweets, or public messages without Jarad's approval
- Internal operations (read, build, test, commit) are free to do
- When in doubt, ask Cack
EOF

# ── Generate MEMORY.md ───────────────────────────────────────────
if [ "$HAS_MEMORY" = true ]; then
  cat > "$WORKSPACE/MEMORY.md" << EOF
# MEMORY.md — ${NAME}

## Identity
- **Role:** ${ROLE} in 33GOD pipeline
- **Purpose:** ${PURPOSE}
- **Boss:** Cack (main agent)
- **Human:** Jarad (America/New_York)

## Ecosystem
- **33GOD**: 17-microservice agentic orchestration platform
- **Bloodbank**: Event bus (RabbitMQ/MQTT)
- **Flume**: Service routing + org chart
- **Yi**: Agent framework (Manager/Exec/IC/Contractor flavors)
- **Plane workspace**: lasertoast
- **GOD Docs**: Deterministic documentation freshness enforcement

## Key Lessons
(Append lessons learned here as you work)
EOF
else
  echo "# No persistent memory — contractor role" > "$WORKSPACE/MEMORY.md"
fi

# ── Generate TOOLS.md ────────────────────────────────────────────
cat > "$WORKSPACE/TOOLS.md" << EOF
# TOOLS.md - ${NAME}'s Local Notes

Add environment-specific notes here as you discover them.
EOF

# ── Generate HEARTBEAT.md ────────────────────────────────────────
cat > "$WORKSPACE/HEARTBEAT.md" << EOF
# HEARTBEAT.md
# Add periodic tasks below. Keep it small to limit token burn.
EOF

# ── Role Governance (matrix + inherited directives) ─────────────
if [[ -x "$GOVERNANCE_SCRIPT" ]]; then
  GOV_ARGS=(
    --governance-dir "$GOVERNANCE_DIR"
    upsert-and-apply
    --workspace "$WORKSPACE"
    --agent "$NAME"
    --role "$ROLE_TITLE"
    --reports-to "$REPORTS_TO"
    --mission "$PURPOSE"
  )
  for directive in "${LOCAL_DIRECTIVES[@]}"; do
    GOV_ARGS+=(--directive "$directive")
  done

  echo "🧭 Syncing role governance..."
  python3 "$GOVERNANCE_SCRIPT" "${GOV_ARGS[@]}" || {
    echo "⚠️  Governance sync failed (continuing workspace bootstrap)."
  }
else
  echo "⚠️  Governance script missing: $GOVERNANCE_SCRIPT"
fi

# ── Symlink Skills ───────────────────────────────────────────────
echo "🔗 Symlinking skills..."

# Base skills for all agents
BASE_SKILLS=(
  "github"
  "installing-apps-tools-and-services"
  "hindsight"
)

# Extended skills for non-contractors
EXTENDED_SKILLS=(
  "33god-creating-and-working-with-projects"
  "33god-service-development"
  "33god-workflow-generator"
  "god-docs"
  "managing-tickets-and-tasks-in-plane"
  "ecosystem-patterns"
)

# Create skills dir in workspace if the agent needs local skills
# (We don't — skills are global in ~/.openclaw/skills/)
# But we log what this agent should have access to

if [ "$ROLE" = "contractor" ]; then
  AGENT_SKILLS=("${BASE_SKILLS[@]}")
else
  AGENT_SKILLS=("${BASE_SKILLS[@]}" "${EXTENDED_SKILLS[@]}")
fi

echo "  Skills for ${NAME} (${ROLE}):"
for skill in "${AGENT_SKILLS[@]}"; do
  if [ -d "${SKILLS_SRC}/${skill}" ]; then
    echo "    ✅ ${skill}"
  else
    echo "    ⚠️  ${skill} (not installed)"
  fi
done

# ── Summary ──────────────────────────────────────────────────────
echo ""
echo "✅ Agent workspace created: $WORKSPACE"
echo ""
echo "📋 Next steps:"
echo "  1. Verify role governance row in $GOVERNANCE_DIR/AGENT_ROLE_MATRIX.json"
echo "  2. Add agent to openclaw.json agents.list"
echo "  3. Add channel binding (if needed)"
echo "  4. Restart gateway"
echo "  5. Send onboarding briefing via sessions_send"
echo ""
echo "Agent config JSON:"
cat << EOF
{
  "id": "${ID}",
  "name": "${NAME}",
  "workspace": "${WORKSPACE}",
  "identity": { "name": "${NAME}" }
}
EOF

# ── Git Init + GitHub Repo ──────────────────────────────────────
echo "📦 Initializing git repository..."

# Write .gitignore
cat > "$WORKSPACE/.gitignore" << 'GITEOF'
# Agent workspace
*.jsonl
*.tmp
.openclaw/
node_modules/
__pycache__/
.env
.env.*
!.env.example
GITEOF

cd "$WORKSPACE"
git init -b main
git add -A
git commit -m "Initial workspace setup for ${NAME}"

REPO_NAME="agent-oc-$(echo "${NAME}" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"
echo "🔗 Creating GitHub repo: delorenj/${REPO_NAME}"
gh repo create "delorenj/${REPO_NAME}" --private --source . --push 2>/dev/null || {
  echo "⚠️  GitHub repo creation failed (may already exist). Add remote manually:"
  echo "  git remote add origin git@github.com:delorenj/${REPO_NAME}.git && git push -u origin main"
}

echo ""
echo "📦 Git repo: https://github.com/delorenj/${REPO_NAME}"
