#!/usr/bin/env bash
set -euo pipefail

# Agent Factory Bootstrap Script
# Creates a fully configured 33GOD agent workspace

# ── Parse Arguments ──────────────────────────────────────────────
ID="" NAME="" ROLE="" PURPOSE="" PERSONALITY="competent, concise, team-player" MODEL=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --id) ID="$2"; shift 2;;
    --name) NAME="$2"; shift 2;;
    --role) ROLE="$2"; shift 2;;
    --purpose) PURPOSE="$2"; shift 2;;
    --personality) PERSONALITY="$2"; shift 2;;
    --model) MODEL="$2"; shift 2;;
    *) echo "Unknown: $1"; exit 1;;
  esac
done

[[ -z "$ID" || -z "$NAME" || -z "$ROLE" || -z "$PURPOSE" ]] && {
  echo "Usage: bootstrap.sh --id <id> --name <name> --role <role> --purpose <purpose> [--personality <p>] [--model <m>]"
  exit 1
}

# Validate role
[[ "$ROLE" =~ ^(manager|exec|ic|contractor)$ ]] || { echo "Invalid role: $ROLE (must be manager|exec|ic|contractor)"; exit 1; }

# ── Setup ────────────────────────────────────────────────────────
WORKSPACE="$HOME/.openclaw/workspace-${ID}"
SKILLS_SRC="$HOME/.openclaw/skills"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REF_DIR="${SCRIPT_DIR}/references"

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

# ── Symlink Skills ───────────────────────────────────────────────
echo "🔗 Symlinking skills..."

# Base skills for all agents
BASE_SKILLS=(
  "github"
  "installing-apps-tools-and-services"
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
echo "  1. Add agent to openclaw.json agents.list"
echo "  2. Add channel binding (if needed)"
echo "  3. Restart gateway"
echo "  4. Send onboarding briefing via sessions_send"
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
