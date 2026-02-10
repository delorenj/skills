#!/usr/bin/env node
/**
 * Intelligent Memory Workflow using Claude Flow MCP Tools
 * This script orchestrates session memory management with actual MCP integration
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const MEMORY_NAMESPACE = 'intelliforia-dev';
const PROJECT_ROOT = process.cwd();

// Helper to execute claude-flow commands
function claudeFlow(command, args = {}) {
  // Handle memory commands with positional arguments
  if (command.startsWith('memory store')) {
    const { key, value, ...options } = args;
    if (key && value) {
      // Write value to temporary file to avoid shell escaping issues
      const tempFile = path.join(PROJECT_ROOT, '.tmp_memory_value');
      fs.writeFileSync(tempFile, value, 'utf8');

      try {
        let cmdString = `npx claude-flow@alpha memory store "${key}" "$(cat ${tempFile})"`;

        // Add remaining options
        const optionsString = Object.entries(options)
          .map(([k, v]) => `--${k} "${v}"`)
          .join(' ');
        if (optionsString) cmdString += ` ${optionsString}`;

        const result = execSync(cmdString, { encoding: 'utf8', stdio: 'pipe' });

        // Clean up temp file
        fs.unlinkSync(tempFile);

        return handleResult(result);
      } catch (error) {
        // Clean up temp file on error
        if (fs.existsSync(tempFile)) fs.unlinkSync(tempFile);
        console.error(`Error executing: ${command}`, error.message);
        return { results: [], value: null };
      }
    }
  } else if (command.startsWith('memory query')) {
    const { pattern, ...options } = args;
    let cmdString = `npx claude-flow@alpha memory query`;
    if (pattern) {
      cmdString += ` "${pattern}"`;
    }
    // Add remaining options
    const optionsString = Object.entries(options)
      .map(([k, v]) => `--${k} "${v}"`)
      .join(' ');
    if (optionsString) cmdString += ` ${optionsString}`;

    try {
      const result = execSync(cmdString, { encoding: 'utf8', stdio: 'pipe' });
      return handleResult(result);
    } catch (error) {
      console.error(`Error executing: ${command}`, error.message);
      return { results: [], value: null };
    }
  } else {
    // Default behavior for other commands
    let cmdString = `npx claude-flow@alpha ${command}`;
    const argsString = Object.entries(args)
      .map(([key, value]) => `--${key} "${value}"`)
      .join(' ');
    if (argsString) cmdString += ` ${argsString}`;

    try {
      const result = execSync(cmdString, { encoding: 'utf8', stdio: 'pipe' });
      return handleResult(result);
    } catch (error) {
      console.error(`Error executing: ${command}`, error.message);
      return { results: [], value: null };
    }
  }
}

// Helper to handle command results
function handleResult(result) {
  const trimmedResult = result.trim();

  // If it's a warning or error message, return empty result
  if (trimmedResult.startsWith('❌') || trimmedResult.startsWith('⚠️')) {
    console.log(`Info: ${trimmedResult}`);
    return { results: [], value: null };
  }

  // Handle claude-flow memory query results (formatted text)
  if (trimmedResult.startsWith('✅ Found')) {
    // Parse the formatted memory results
    const lines = trimmedResult.split('\n');
    const results = [];
    let currentItem = null;

    for (const line of lines) {
      if (line.startsWith('📌 ')) {
        if (currentItem) results.push(currentItem);
        currentItem = { key: line.replace('📌 ', '').trim() };
      } else if (line.includes('Value: ') && currentItem) {
        const valueMatch = line.match(/Value: (.+)/);
        if (valueMatch) {
          try {
            currentItem.value = JSON.parse(valueMatch[1]);
          } catch {
            currentItem.value = valueMatch[1];
          }
        }
      }
    }
    if (currentItem) results.push(currentItem);

    // Return the first result's value for compatibility
    return {
      results,
      value: results.length > 0 ? JSON.stringify(results[0].value) : null
    };
  }

  // Try to parse as JSON, fallback to text parsing
  try {
    return JSON.parse(trimmedResult || '{}');
  } catch {
    // For simple text responses, wrap in expected format
    return { results: [], value: trimmedResult || null };
  }
}

// ============================================
// SESSION START: Intelligent Memory Recall
// ============================================
async function sessionStart() {
  console.log('🧠 Initializing Intelligent Memory Workflow');

  // Get current git context
  const currentBranch = execSync('git branch --show-current', { encoding: 'utf8' }).trim();
  const modifiedFiles = execSync('git diff --name-only', { encoding: 'utf8' }).trim().split('\n').filter(Boolean);
  const recentCommits = execSync('git log --oneline -5', { encoding: 'utf8' }).trim();

  // 1. Search for relevant past sessions
  console.log('📚 Recalling relevant sessions...');
  const relevantMemories = claudeFlow('memory query', {
    pattern: `session-*`,
    namespace: MEMORY_NAMESPACE
  });

  // 2. Find memories related to current branch/files
  console.log('🎯 Finding context-relevant memories...');
  const contextMemories = [];

  // Search for branch-related memories
  if (currentBranch) {
    const branchMemories = claudeFlow('memory query', {
      pattern: `*${currentBranch}*`,
      namespace: MEMORY_NAMESPACE
    });
    contextMemories.push(...(branchMemories.results || []));
  }

  // Search for file-related memories
  for (const file of modifiedFiles.slice(0, 3)) { // Limit to first 3 files
    const fileName = path.basename(file, path.extname(file));
    const fileMemories = claudeFlow('memory query', {
      pattern: `*${fileName}*`,
      namespace: MEMORY_NAMESPACE
    });
    contextMemories.push(...(fileMemories.results || []));
  }

  // 3. Load critical project patterns
  console.log('💡 Loading project patterns and decisions...');
  const criticalPatterns = claudeFlow('memory query', {
    pattern: 'patterns/critical',
    namespace: MEMORY_NAMESPACE
  });

  const knownIssues = claudeFlow('memory query', {
    pattern: 'issues/active',
    namespace: MEMORY_NAMESPACE
  });

  // 4. Create session ID and context
  const sessionId = `session-${Date.now()}`;
  const sessionContext = {
    id: sessionId,
    started: new Date().toISOString(),
    branch: currentBranch,
    modifiedFiles,
    recentCommits,
    relevantMemories: relevantMemories.results || [],
    contextMemories: contextMemories.slice(0, 5), // Limit context memories
    patterns: criticalPatterns.value || {},
    knownIssues: knownIssues.value || []
  };

  // 5. Store session initialization
  claudeFlow('memory store', {
    key: `session-active`,
    value: JSON.stringify({
      id: sessionId,
      branch: currentBranch,
      started: sessionContext.started
    }),
    namespace: MEMORY_NAMESPACE,
    ttl: 86400 // 1 day
  });

  // 6. Store full session context
  claudeFlow('memory store', {
    key: `${sessionId}/context`,
    value: JSON.stringify(sessionContext),
    namespace: MEMORY_NAMESPACE,
    ttl: 604800 // 7 days
  });

  console.log(`✅ Session ${sessionId} initialized with intelligent context`);

  // Output context summary for Claude to see
  console.log('\n📋 Context Loaded:');
  console.log(`- Branch: ${currentBranch}`);
  console.log(`- Modified Files: ${modifiedFiles.length} files`);
  console.log(`- Relevant Memories: ${relevantMemories.results?.length || 0} found`);
  console.log(`- Context Memories: ${contextMemories.length} found`);

  if (knownIssues.value?.length > 0) {
    console.log(`- ⚠️  Known Issues: ${knownIssues.value.length}`);
  }

  return sessionContext;
}

// ============================================
// QUERY PROCESSING: Smart Memory Storage
// ============================================
async function afterQuery(query, response) {
  console.log('💭 Analyzing query for memory storage...');

  // Get active session
  const activeSession = claudeFlow('memory query', {
    pattern: 'session-active',
    namespace: MEMORY_NAMESPACE
  });

  if (!activeSession.value) {
    console.log('No active session found, skipping memory storage');
    return;
  }

  const sessionData = JSON.parse(activeSession.value);
  const sessionId = sessionData.id;

  // Determine importance based on keywords and patterns
  const importanceKeywords = {
    critical: ['error', 'fix', 'bug', 'broken', 'crash', 'failed'],
    high: ['implement', 'create', 'design', 'architecture', 'refactor'],
    medium: ['update', 'modify', 'add', 'change', 'improve'],
    low: ['format', 'style', 'comment', 'rename', 'move']
  };

  let importance = 'low';
  const queryLower = query.toLowerCase();

  for (const [level, keywords] of Object.entries(importanceKeywords)) {
    if (keywords.some(keyword => queryLower.includes(keyword))) {
      importance = level;
      break;
    }
  }

  // Store query record
  const queryRecord = {
    timestamp: new Date().toISOString(),
    query: query.substring(0, 200), // Limit query length
    importance,
    hasCode: response?.includes('```') || false,
    filesModified: response?.match(/\.(ts|tsx|rs|js|jsx)/g)?.length || 0
  };

  claudeFlow('memory store', {
    key: `${sessionId}/queries/${Date.now()}`,
    value: JSON.stringify(queryRecord),
    namespace: MEMORY_NAMESPACE
  });

  // For high importance queries, extract and store patterns
  if (importance === 'high' || importance === 'critical') {
    console.log(`📝 Storing ${importance} importance information...`);

    // Extract key decisions or solutions
    const decisionPattern = /(?:decided|solution|approach|fixed by|resolved)/i;
    if (decisionPattern.test(response)) {
      const decision = {
        type: 'decision',
        context: query,
        solution: response.substring(0, 500),
        timestamp: new Date().toISOString(),
        sessionId
      };

      claudeFlow('memory store', {
        key: `decisions/${Date.now()}`,
        value: JSON.stringify(decision),
        namespace: MEMORY_NAMESPACE,
        ttl: 2592000 // 30 days
      });
    }

    // Extract code patterns if present
    const codeBlocks = response.match(/```[\s\S]*?```/g);
    if (codeBlocks && codeBlocks.length > 0) {
      const pattern = {
        type: 'code-pattern',
        context: query,
        code: codeBlocks[0].substring(0, 1000),
        language: codeBlocks[0].match(/```(\w+)/)?.[1] || 'unknown',
        timestamp: new Date().toISOString(),
        sessionId
      };

      claudeFlow('memory store', {
        key: `patterns/${Date.now()}`,
        value: JSON.stringify(pattern),
        namespace: MEMORY_NAMESPACE,
        ttl: 1209600 // 14 days
      });
    }
  }

  console.log(`✅ Query processed (importance: ${importance})`);
}

// ============================================
// SESSION END: Intelligent Summarization
// ============================================
async function sessionEnd() {
  console.log('📊 Creating intelligent session summary...');

  // Get active session
  const activeSession = claudeFlow('memory query', {
    pattern: 'session-active',
    namespace: MEMORY_NAMESPACE
  });

  if (!activeSession.value) {
    console.log('No active session to end');
    return;
  }

  const sessionData = JSON.parse(activeSession.value);
  const sessionId = sessionData.id;

  // Retrieve session queries
  const queries = claudeFlow('memory query', {
    pattern: `${sessionId}/queries`,
    namespace: MEMORY_NAMESPACE
  });

  // Get git changes
  const filesChanged = execSync('git diff --name-only', { encoding: 'utf8' }).trim().split('\n').filter(Boolean);
  const commitsMade = parseInt(execSync('git rev-list --count HEAD@{1day.ago}..HEAD', { encoding: 'utf8' }).trim()) || 0;

  // Create session summary
  const summary = {
    id: sessionId,
    started: sessionData.started,
    ended: new Date().toISOString(),
    branch: sessionData.branch,
    filesChanged: filesChanged.length,
    commitsMade,
    queriesProcessed: queries.value ? JSON.parse(queries.value).length : 0,
    achievements: [],
    nextSteps: [],
    patterns: []
  };

  // Analyze achievements from git commits
  if (commitsMade > 0) {
    const recentCommits = execSync('git log --oneline --since="1 day ago"', { encoding: 'utf8' }).trim();
    summary.achievements = recentCommits.split('\n').filter(Boolean).slice(0, 5);
  }

  // Store session summary
  claudeFlow('memory store', {
    key: `session-summary-${sessionId}`,
    value: JSON.stringify(summary),
    namespace: MEMORY_NAMESPACE,
    ttl: 2592000 // 30 days
  });

  // Clear active session - using clear command for namespace cleanup
  console.log('🧹 Cleaning up session data...');
  // Note: claude-flow doesn't have individual key deletion, so we'll let TTL handle cleanup

  console.log('🧹 Memory cleanup completed via TTL expiration...');

  console.log(`✅ Session ${sessionId} completed and indexed`);
  console.log(`📈 Summary: ${filesChanged.length} files changed, ${commitsMade} commits, ${summary.queriesProcessed} queries`);
}

// ============================================
// CONTEXT SWITCH: Adaptive Memory Loading
// ============================================
async function contextSwitch(newContext) {
  console.log(`🔄 Switching context to: ${newContext}`);

  // Search for context-relevant memories
  const relevantMemories = claudeFlow('memory query', {
    pattern: `*${newContext}*`,
    namespace: MEMORY_NAMESPACE
  });

  console.log(`Found ${relevantMemories.results?.length || 0} relevant memories for context: ${newContext}`);

  // Update active session with new context
  const activeSession = claudeFlow('memory query', {
    pattern: 'session-active',
    namespace: MEMORY_NAMESPACE
  });

  if (activeSession.value) {
    const sessionData = JSON.parse(activeSession.value);
    sessionData.currentContext = newContext;

    claudeFlow('memory store', {
      key: 'session-active',
      value: JSON.stringify(sessionData),
      namespace: MEMORY_NAMESPACE,
      ttl: 86400
    });
  }

  return relevantMemories.results || [];
}

// ============================================
// MAIN EXECUTION
// ============================================
const command = process.argv[2] || 'start';
const args = process.argv.slice(3);

async function main() {
  switch (command) {
    case 'start':
      await sessionStart();
      break;

    case 'query':
      await afterQuery(args[0] || '', args[1] || '');
      break;

    case 'end':
      await sessionEnd();
      break;

    case 'switch':
      await contextSwitch(args[0] || 'default');
      break;

    default:
      console.log('Usage: node memory-workflow-mcp.js {start|query|end|switch} [args...]');
      console.log('  start              - Initialize session with memory recall');
      console.log('  query <q> <r>      - Process query and response for memory storage');
      console.log('  end                - End session and create summary');
      console.log('  switch <context>   - Switch to new context');
      process.exit(1);
  }
}

main().catch(console.error);