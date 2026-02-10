# Claude-Flow Commands Reference

**Version**: claude-flow@alpha v2.7.26+
**Last Updated**: 2025-10-28

## Critical Information

**DO NOT USE**: `workflow execute` command - Does not exist in v2.7.26

**ALWAYS VERIFY** available commands with:
```bash
npx claude-flow@alpha --help
npx claude-flow@alpha <command> --help
```

---

## Available Commands

### 1. swarm - Multi-Agent Coordination

**Best for**: Implementation workflows with parallel agents

```bash
npx claude-flow@alpha swarm <objective> [options]
```

**Options**:
- `--strategy <type>` - Execution strategy
  - `research` - Research with web access and data analysis
  - `development` - Code development with neural patterns
  - `analysis` - Performance analysis and optimization
  - `testing` - Comprehensive testing with automation
  - `optimization` - Performance and efficiency improvements
  - `maintenance` - Code maintenance and refactoring
- `--mode <type>` - Coordination mode
  - `centralized` - Single coordinator
  - `distributed` - Peer-to-peer
  - `hierarchical` - Queen-led structure
  - `mesh` - Full connectivity
  - `hybrid` - Mixed approach
- `--max-agents <n>` - Maximum concurrent agents (default: 5)
- `--parallel` - Enable parallel execution (2.8-4.4x speedup)
- `--monitor` - Real-time swarm monitoring
- `--background` - Run in background with progress tracking
- `--claude` - Open Claude Code CLI (default: built-in executor)
- `--executor` - Use built-in executor instead of Claude Code
- `--analysis` - Enable read-only mode (no code changes)
- `--read-only` - Alias for --analysis

**Examples**:
```bash
# Development workflow (opens Claude Code CLI)
npx claude-flow@alpha swarm "Build authentication system" \
  --strategy development \
  --parallel \
  --max-agents 5 \
  --claude

# Research workflow (read-only)
npx claude-flow@alpha swarm "Analyze security vulnerabilities" \
  --strategy research \
  --analysis

# Testing workflow with monitoring
npx claude-flow@alpha swarm "Create test suite for API" \
  --strategy testing \
  --parallel \
  --monitor
```

---

### 2. sparc - SPARC Methodology Phases

**Best for**: Structured development phases

```bash
npx claude-flow@alpha sparc <mode> [task] [options]
```

**Modes**:
- `spec` - Specification mode (requirements analysis)
- `architect` - Architecture mode (system design)
- `tdd` - Test-driven development mode
- `integration` - Integration mode (component connection)
- `refactor` - Refactoring mode (code improvement)
- `modes` - List all available modes

**Options**:
- `--file <path>` - Input/output file path
- `--format <type>` - Output format (markdown, json, yaml)
- `--verbose` - Detailed output

**Examples**:
```bash
# Requirements analysis
npx claude-flow@alpha sparc spec "User authentication system"

# Architecture design
npx claude-flow@alpha sparc architect "Microservices architecture"

# TDD implementation
npx claude-flow@alpha sparc tdd "Payment processing module"

# List available modes
npx claude-flow@alpha sparc modes
```

---

### 3. stream-chain - Sequential Context Preservation

**Best for**: Multi-step workflows with full context

```bash
npx claude-flow@alpha stream-chain <subcommand> [options]
```

**Subcommands**:
- `run <p1> <p2> [...]` - Execute custom chain (min 2 prompts)
- `demo` - Run 3-step demo chain
- `pipeline <type>` - Run predefined pipeline
  - `analysis` - Analyze → Identify issues → Generate report
  - `refactor` - Find opportunities → Create plan → Apply changes
  - `test` - Analyze coverage → Design cases → Generate tests
  - `optimize` - Profile code → Find bottlenecks → Apply optimizations
- `test` - Test stream connection
- `help` - Show comprehensive documentation

**Options**:
- `--verbose` - Show detailed execution info
- `--timeout <seconds>` - Timeout per step (default: 30)
- `--debug` - Enable debug mode

**Examples**:
```bash
# Custom chain
npx claude-flow@alpha stream-chain run \
  "analyze requirements" \
  "design architecture" \
  "implement solution"

# Predefined pipeline
npx claude-flow@alpha stream-chain pipeline analysis

# Test connection
npx claude-flow@alpha stream-chain test
```

---

### 4. agent - Agent Management

**Best for**: Direct agent control

```bash
npx claude-flow@alpha agent <action> [options]
```

**Actions**:
- `spawn` - Create new agent
- `list` - List active agents
- `terminate` - Stop agent
- `booster` - Ultra-fast code editing (352x faster, $0 cost)
  - `edit <file>` - Edit single file
  - `batch <pattern>` - Batch edit multiple files
  - `benchmark` - Validate performance claims
- `memory` - ReasoningBank learning memory (46% faster)
  - `init` - Initialize memory database
  - `status` - Show memory statistics
  - `list` - List stored memories

**Examples**:
```bash
# Spawn agent
npx claude-flow@alpha agent spawn --type researcher

# Ultra-fast edit
npx claude-flow@alpha agent booster edit src/app.ts

# Batch edit
npx claude-flow@alpha agent booster batch "src/**/*.ts"

# Memory operations
npx claude-flow@alpha agent memory init
npx claude-flow@alpha agent memory status
```

---

### 5. memory - Persistent Memory System

**Best for**: Cross-session knowledge retention

```bash
npx claude-flow@alpha memory <action> [options]
```

**Actions**:
- `store` - Store information
- `retrieve` - Retrieve information
- `search` - Search memory
- `list` - List all memories
- `clear` - Clear memory

**Examples**:
```bash
# Store context
npx claude-flow@alpha memory store "swarm/context" "Working on auth system"

# Retrieve context
npx claude-flow@alpha memory retrieve "swarm/context"

# Search memories
npx claude-flow@alpha memory search "authentication"
```

---

### 6. task - Task Management

**Best for**: Task tracking and workflow management

```bash
npx claude-flow@alpha task <action> [options]
```

**Actions**:
- `create` - Create new task
- `list` - List tasks
- `update` - Update task
- `complete` - Mark task complete

---

### 7. github - GitHub Workflow Automation

**Best for**: PR management, issue tracking

```bash
npx claude-flow@alpha github <mode> [options]
```

**Modes**: Various GitHub integration modes (6 available)

---

### 8. proxy - OpenRouter Proxy Server

**Best for**: Cost optimization (85-98% savings)

```bash
npx claude-flow@alpha proxy <action>
```

**Actions**:
- `start` - Start proxy server
- `status` - Check proxy status
- `config` - Configuration guide

---

### 9. hive-mind - Hive Mind System (NEW)

**Best for**: Intelligent swarm orchestration

```bash
npx claude-flow@alpha hive-mind <command> [options]
```

**Commands**:
- `wizard` - Interactive setup wizard (RECOMMENDED)
- `init` - Initialize Hive Mind with SQLite
- `spawn <task>` - Create intelligent swarm
- `status` - View active swarms and metrics
- `metrics` - Advanced performance analytics

**Examples**:
```bash
# Interactive setup
npx claude-flow@alpha hive-mind wizard

# Spawn intelligent swarm
npx claude-flow@alpha hive-mind spawn "Build REST API"

# View status
npx claude-flow@alpha hive-mind status
```

---

## MCP Tools

Available via Claude Code after installing:

```bash
claude mcp add claude-flow npx claude-flow@alpha mcp start
```

**Tools**:
- `mcp__claude-flow__agents_spawn_parallel` - Spawn agents in parallel (10-20x faster)
- `mcp__claude-flow__query_control` - Control running queries in real-time
- `mcp__claude-flow__query_list` - List active queries with status

---

## Performance Metrics

**Expected Performance Gains**:
- Parallel execution: 2.8-4.4x speedup
- Agent booster: 352x faster editing
- ReasoningBank memory: 46% faster, 88% success rate
- OpenRouter proxy: 85-98% cost savings

---

## Version Compatibility

**This reference is for**: claude-flow@alpha v2.7.26+

**Always verify** your version:
```bash
npx claude-flow@alpha --version
```

**If commands don't work**:
1. Update to latest alpha: `npm install -g claude-flow@alpha`
2. Check available commands: `npx claude-flow@alpha --help`
3. Consult latest docs: https://github.com/ruvnet/claude-flow

---

## Common Patterns

### Pattern 1: Development Workflow with Swarm

```bash
# Read task from file
TASK=$(cat TASK.md)

# Execute with swarm
npx claude-flow@alpha swarm "$TASK" \
  --strategy development \
  --parallel \
  --max-agents 5 \
  --claude
```

### Pattern 2: Research + Development Pipeline

```bash
# Phase 1: Research
npx claude-flow@alpha swarm "Research authentication patterns" \
  --strategy research \
  --analysis

# Phase 2: Design
npx claude-flow@alpha sparc architect "OAuth2 implementation"

# Phase 3: Implement
npx claude-flow@alpha sparc tdd "OAuth2 endpoints"
```

### Pattern 3: Stream-Chain for Sequential Work

```bash
npx claude-flow@alpha stream-chain run \
  "Analyze current implementation" \
  "Identify refactoring opportunities" \
  "Create refactoring plan" \
  "Apply changes incrementally"
```

---

## Troubleshooting

### Command Not Found

**Error**: `Unknown command: workflow`

**Solution**: The `workflow` command doesn't exist. Use `swarm`, `sparc`, or `stream-chain` instead.

### Version Mismatch

**Problem**: Documentation mentions commands that don't exist

**Solution**:
```bash
# Check your version
npx claude-flow@alpha --version

# Update to latest alpha
npm install -g claude-flow@alpha

# Verify available commands
npx claude-flow@alpha --help
```

### Execution Failures

**Problem**: Workflow fails silently

**Solution**: Use `--verbose` and `--debug` flags:
```bash
npx claude-flow@alpha swarm "task" --verbose --debug
```

---

**Reference Version**: 1.0.0
**Maintainer**: Jarad DeLorenzo
**Last Updated**: 2025-10-28
