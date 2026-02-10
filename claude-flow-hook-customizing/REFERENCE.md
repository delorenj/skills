# Hooks System - Automated Workflow Orchestration

The Claude-Flow Hooks System provides automated workflow orchestration through pre and post operation hooks, enabling seamless integration of custom logic into the development lifecycle. This powerful system allows for automatic task tracking, memory persistence, agent coordination, and performance optimization.

## Overview

The Hooks System intercepts key operations in your workflow, executing custom logic before and after critical actions. This enables:

- **Automated Task Management**: Track all operations with unique IDs
- **Memory Persistence**: Store context and results for future reference
- **Agent Coordination**: Synchronize multi-agent workflows
- **Performance Monitoring**: Track execution times and resource usage
- **Custom Integrations**: Add your own automation logic

## Available Hooks

### Core Operation Hooks

#### pre-task
Executes before starting any task, initializing tracking and context.

```bash
npx claude-flow@alpha hooks pre-task --description "Implement user authentication"
```

**Parameters:**
- `--description`: Task description (required)
- `--priority`: Task priority (low/medium/high/critical)
- `--metadata`: Additional JSON metadata

**Example Output:**
```
🔄 Executing pre-task hook...
📋 Task: Implement user authentication
🆔 Task ID: task-1753483207250-u7wbmsetj
💾 Saved to .swarm/memory.db
```

#### post-task
Executes after task completion, storing results and metrics.

```bash
npx claude-flow@alpha hooks post-task --task-id "task-1753483207250-u7wbmsetj" --status "completed"
```

**Parameters:**
- `--task-id`: Task identifier (required)
- `--status`: Task status (completed/failed/partial)
- `--results`: JSON results data
- `--metrics`: Performance metrics

### File Operation Hooks

#### pre-edit
Executes before file modifications, creating backups and tracking changes.

```bash
npx claude-flow@alpha hooks pre-edit --file "src/auth.js" --operation "update authentication logic"
```

**Parameters:**
- `--file`: File path (required)
- `--operation`: Operation description
- `--backup`: Create backup (true/false)

#### post-edit
Executes after file modifications, validating changes and updating memory.

```bash
npx claude-flow@alpha hooks post-edit --file "src/auth.js" --memory-key "auth/implementation"
```

**Parameters:**
- `--file`: File path (required)
- `--memory-key`: Memory storage key
- `--validate`: Run validation (true/false)
- `--sync-agents`: Notify other agents

### Session Management Hooks

#### session-start
Initializes a new development session with context restoration.

```bash
npx claude-flow@alpha hooks session-start --restore-context --load-agents
```

**Parameters:**
- `--restore-context`: Restore previous session context
- `--load-agents`: Initialize configured agents
- `--workspace`: Set workspace directory

#### session-end
Finalizes session, saving state and generating reports.

```bash
npx claude-flow@alpha hooks session-end --save-state --generate-report
```

**Parameters:**
- `--save-state`: Save current session state
- `--generate-report`: Create session summary
- `--cleanup`: Remove temporary files

### Agent Coordination Hooks

#### agent-spawn
Executes when creating new agents, configuring their environment.

```bash
npx claude-flow@alpha hooks agent-spawn --type "coder" --config '{"language":"typescript"}'
```

**Parameters:**
- `--type`: Agent type (required)
- `--config`: Agent configuration JSON
- `--parent-task`: Parent task ID

#### agent-complete
Executes when agents finish their tasks, collecting results.

```bash
npx claude-flow@alpha hooks agent-complete --agent-id "agent-123" --merge-results
```

**Parameters:**
- `--agent-id`: Agent identifier (required)
- `--merge-results`: Merge with parent task
- `--propagate`: Send results to other agents

### Performance Optimization Hooks

#### perf-start
Begins performance monitoring for an operation.

```bash
npx claude-flow@alpha hooks perf-start --operation "database-query" --track-memory
```

**Parameters:**
- `--operation`: Operation name (required)
- `--track-memory`: Monitor memory usage
- `--track-cpu`: Monitor CPU usage

#### perf-end
Completes performance monitoring and stores metrics.

```bash
npx claude-flow@alpha hooks perf-end --operation "database-query" --alert-threshold 1000
```

**Parameters:**
- `--operation`: Operation name (required)
- `--alert-threshold`: Alert if ms exceeds threshold
- `--store-metrics`: Save to metrics database

## Hook Configuration

Configure hooks in `.claude/settings.json`:

```json
{
  "hooks": {
    "enabled": true,
    "autoExecute": {
      "preTask": true,
      "postTask": true,
      "preEdit": true,
      "postEdit": true,
      "sessionStart": true,
      "sessionEnd": true
    },
    "customHooks": {
      "beforeCommit": {
        "command": "npm test && npm run lint",
        "failOnError": true
      },
      "afterDeploy": {
        "command": "npx claude-flow@alpha notify --channel deployment",
        "async": true
      }
    },
    "memory": {
      "persistence": true,
      "location": ".swarm/memory.db",
      "syncInterval": 30000
    },
    "performance": {
      "tracking": true,
      "alertThresholds": {
        "task": 300000,
        "edit": 5000,
        "agent": 60000
      }
    }
  }
}
```

## Automation Patterns

### 1. Continuous Integration Pattern
Automatically run tests and validation on file changes:

```json
{
  "hooks": {
    "customHooks": {
      "postEdit": {
        "pattern": "*.test.js",
        "command": "npm test -- --findRelatedTests ${file}",
        "continueOnError": false
      }
    }
  }
}
```

### 2. Multi-Agent Coordination Pattern
Synchronize work across multiple agents:

```bash
# Master coordinator
npx claude-flow@alpha hooks pre-task --description "Refactor authentication system" --metadata '{"agents":["architect","coder","tester"]}'

# Each agent registers
npx claude-flow@alpha hooks agent-spawn --type "architect" --parent-task "task-123"
npx claude-flow@alpha hooks agent-spawn --type "coder" --parent-task "task-123"
npx claude-flow@alpha hooks agent-spawn --type "tester" --parent-task "task-123"

# Coordination through hooks
npx claude-flow@alpha hooks post-edit --file "architecture.md" --sync-agents --memory-key "refactor/architecture"
```

### 3. Performance Monitoring Pattern
Track and optimize critical operations:

```javascript
// Before operation
await executeHook('perf-start', { operation: 'data-processing' });

// Your operation
const results = await processLargeDataset();

// After operation
await executeHook('perf-end', { 
  operation: 'data-processing',
  alertThreshold: 5000,
  storeMetrics: true
});
```

### 4. Memory-Driven Development Pattern
Maintain context across sessions:

```bash
# Start session with context
npx claude-flow@alpha hooks session-start --restore-context

# Work with automatic memory updates
npx claude-flow@alpha hooks post-edit --file "feature.js" --memory-key "feature/implementation"

# Query memory during development
npx claude-flow@alpha memory search --pattern "feature/*"

# End session with state preservation
npx claude-flow@alpha hooks session-end --save-state
```

## Performance Optimization

### Hook Execution Optimization

1. **Parallel Execution**: Enable concurrent hook execution
```json
{
  "hooks": {
    "parallel": true,
    "maxConcurrent": 4
  }
}
```

2. **Selective Hooks**: Only run necessary hooks
```json
{
  "hooks": {
    "filters": {
      "preEdit": {
        "include": ["src/**/*.js"],
        "exclude": ["**/*.test.js"]
      }
    }
  }
}
```

3. **Async Operations**: Non-blocking hook execution
```json
{
  "hooks": {
    "customHooks": {
      "backgroundSync": {
        "command": "npx claude-flow@alpha sync --remote",
        "async": true,
        "timeout": 30000
      }
    }
  }
}
```

### Metrics Collection

Hooks automatically collect performance metrics:

```bash
# View hook performance
npx claude-flow@alpha hooks metrics --last 24h

# Output:
┌─────────────┬──────────┬─────────┬─────────┐
│ Hook        │ Calls    │ Avg (ms)│ Max (ms)│
├─────────────┼──────────┼─────────┼─────────┤
│ pre-task    │ 156      │ 23      │ 145     │
│ post-task   │ 156      │ 67      │ 234     │
│ pre-edit    │ 423      │ 12      │ 89      │
│ post-edit   │ 423      │ 45      │ 187     │
└─────────────┴──────────┴─────────┴─────────┘
```

## Integration with Agent Coordination

Hooks provide seamless integration with the agent system:

### Agent Lifecycle Hooks

```javascript
// Agent creation with hooks
const agent = await spawnAgent({
  type: 'coder',
  hooks: {
    onStart: 'agent-start',
    onComplete: 'agent-complete',
    onError: 'agent-error'
  }
});

// Automatic hook execution during agent operations
agent.on('taskComplete', async (result) => {
  await executeHook('post-task', {
    taskId: result.taskId,
    agentId: agent.id,
    results: result.data
  });
});
```

### Cross-Agent Communication

```bash
# Agent A completes analysis
npx claude-flow@alpha hooks post-task --task-id "analysis-123" --sync-agents --broadcast "analysis-complete"

# Agent B receives notification through hook
# Automatically triggered: pre-task hook with context from Agent A
```

### Swarm Coordination Hooks

```json
{
  "hooks": {
    "swarmHooks": {
      "onSwarmInit": {
        "command": "npx claude-flow@alpha swarm prepare --topology hierarchical"
      },
      "onConsensus": {
        "command": "npx claude-flow@alpha memory store --key 'consensus/${timestamp}'"
      },
      "onSwarmComplete": {
        "command": "npx claude-flow@alpha report generate --type swarm-summary"
      }
    }
  }
}
```

## Best Practices

1. **Always use pre/post pairs**: Ensure operations are properly tracked
2. **Store context in memory**: Use memory keys for cross-session persistence
3. **Monitor performance**: Set appropriate thresholds for alerts
4. **Handle errors gracefully**: Use `continueOnError` for non-critical hooks
5. **Document custom hooks**: Maintain clear documentation for team members
6. **Test hook configurations**: Validate hooks work as expected
7. **Use appropriate timeouts**: Prevent hooks from blocking operations
8. **Leverage parallel execution**: Optimize for concurrent operations

## Troubleshooting

### Common Issues

1. **Hook not executing**
   - Check if hooks are enabled in settings
   - Verify hook pattern matches
   - Ensure claude-flow@alpha is installed

2. **Performance degradation**
   - Review hook execution metrics
   - Consider async execution
   - Optimize hook commands

3. **Memory synchronization issues**
   - Check database connectivity
   - Verify memory keys are unique
   - Review sync intervals

### Debug Mode

Enable detailed hook logging:

```bash
# Set debug environment variable
export CLAUDE_FLOW_DEBUG=hooks

# Or in settings.json
{
  "hooks": {
    "debug": true,
    "logLevel": "verbose"
  }
}
```

## Advanced Usage

### Custom Hook Development

Create custom hooks in `.claude/hooks/`:

```javascript
// .claude/hooks/security-scan.js
module.exports = async function securityScan({ file, operation }) {
  const results = await runSecurityAnalysis(file);
  
  if (results.vulnerabilities.length > 0) {
    await executeHook('alert', {
      level: 'critical',
      message: `Security vulnerabilities found in ${file}`,
      details: results
    });
  }
  
  return results;
};
```

Register in settings:

```json
{
  "hooks": {
    "customHooks": {
      "securityScan": {
        "handler": ".claude/hooks/security-scan.js",
        "triggers": ["post-edit"],
        "filePattern": "**/*.js"
      }
    }
  }
}
```

### Hook Chaining

Create complex workflows by chaining hooks:

```json
{
  "hooks": {
    "chains": {
      "deploymentPipeline": [
        { "hook": "pre-deploy", "params": { "environment": "staging" } },
        { "hook": "run-tests", "params": { "suite": "integration" } },
        { "hook": "security-scan", "params": { "deep": true } },
        { "hook": "deploy", "params": { "strategy": "blue-green" } },
        { "hook": "post-deploy", "params": { "notify": true } }
      ]
    }
  }
}
```

Execute chain:
```bash
npx claude-flow@alpha hooks chain --name deploymentPipeline
```

## Conclusion

The Hooks System is a cornerstone of Claude-Flow's automation capabilities, providing the foundation for sophisticated workflow orchestration. By leveraging hooks effectively, you can create self-documenting, self-optimizing development workflows that scale with your project's complexity.