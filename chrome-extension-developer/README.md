# Chrome Extension Developer Skill

Expert Chrome extension development from ideation to Chrome Web Store deployment.

## What This Skill Provides

This skill transforms Claude into an expert Chrome extension developer with comprehensive knowledge of:

- **Manifest V3** architecture and best practices
- **Security-first development** (XSS prevention, CSP compliance)
- **Chrome APIs** (tabs, runtime, storage, downloads, etc.)
- **Complete workflow** from ideation to store submission
- **Real-world patterns** from production extensions

## When to Use This Skill

Invoke this skill when you need help with:

- 🚀 Starting a new Chrome extension project
- 🏗️ Architecting extension components (content script, background, popup)
- 🔒 Security hardening (XSS prevention, input validation)
- 📦 Preparing for Chrome Web Store submission
- 🐛 Debugging extension issues
- 📚 Understanding Chrome extension APIs
- ⚡ Optimizing extension performance
- 🔄 Migrating from Manifest V2 to V3

## Quick Start

### Invoke the Skill
```
Hey Claude, use the chrome-extension-developer skill
```

### Example Requests

**Starting a new extension:**
```
I want to build a Chrome extension that highlights all links on a page.
Can you help me set up the project structure and implement the core functionality?
```

**Security review:**
```
Can you review my extension code for security vulnerabilities,
especially XSS and CSP compliance issues?
```

**Store submission:**
```
I'm ready to submit my extension to the Chrome Web Store.
What do I need to prepare?
```

**Debugging:**
```
My content script isn't running on the target pages.
Can you help me troubleshoot?
```

## Files in This Skill

### SKILL.md
Core skill definition with:
- Competencies and expertise areas
- Development principles
- Common pitfalls to avoid
- Communication patterns

### WORKFLOW_REFERENCE.md
Complete phase-by-phase guide:
1. **Ideation & Specification** - Problem definition, scoping, architecture
2. **Project Setup** - Directory structure, manifest.json, icons
3. **Core Implementation** - Content scripts, background, popup
4. **Testing & QA** - Manual testing, security audit, edge cases
5. **Packaging & Assets** - Icons, screenshots, privacy policy
6. **Chrome Web Store Submission** - Registration, listing, review
7. **Post-Launch Maintenance** - Monitoring, updates, deprecation

Includes:
- Templates for all file types
- Security patterns
- Common code snippets
- Troubleshooting guide

## Key Strengths

### 1. Security-First Approach
Every code example follows security best practices:
- ✅ `textContent` instead of `innerHTML`
- ✅ Input validation and sanitization
- ✅ CSP-compliant code structure
- ✅ Minimal permissions principle

### 2. Real-World Knowledge
Based on actual extension development:
- Skill Scalper implementation (GitHub skill installer)
- Production-tested patterns
- Common pitfalls from experience
- Chrome Web Store submission process

### 3. Complete Workflow Coverage
End-to-end guidance from:
- Initial idea validation
- Technical architecture decisions
- Implementation with templates
- Testing and QA protocols
- Store submission and launch

### 4. Modern Best Practices
- Manifest V3 compliance
- Service worker patterns
- Async/await usage
- Modern JavaScript (ES2024+)
- Performance optimization

## Architecture Knowledge

### Content Scripts
- DOM manipulation and querying
- Event listener management
- Message passing to background/popup
- SPA support with MutationObserver
- Run timing (`document_idle`, `document_end`)

### Background Service Workers
- Event-driven architecture
- API integration and data fetching
- Rate limiting and retry logic
- State persistence with chrome.storage
- Download coordination

### Popup Interface
- Responsive UI patterns
- Tab querying and messaging
- Loading states and error handling
- Settings management
- User feedback mechanisms

## Security Expertise

### XSS Prevention
```javascript
// ❌ VULNERABLE
element.innerHTML = userInput;

// ✅ SECURE
element.textContent = userInput;
```

### CSP Compliance
- No inline scripts
- No inline event handlers
- No eval() or Function()
- External scripts via <script src="">

### Input Validation
- URL validation
- Filename sanitization
- Email validation
- Data type checking

## Chrome Web Store Knowledge

### Submission Requirements
- 16x16, 48x48, 128x128px icons
- 3-5 screenshots (1280x800 or 640x400)
- Privacy policy (if collecting data)
- Permission justifications
- Single purpose statement

### Common Rejection Reasons
1. Excessive keywords
2. Misleading functionality
3. Insufficient permission justification
4. Policy violations
5. Security vulnerabilities

### Review Timeline
- First submission: 1 day to 2 weeks
- Updates: 1-3 days typically
- Complex permissions: longer review

## Example Workflows

### Create Basic Extension
```
User: I want to make an extension that changes the background color of websites

Skill Response:
1. Creates manifest.json with activeTab permission
2. Sets up content script to modify background
3. Adds popup with color picker
4. Implements message passing
5. Provides load instructions
6. Suggests enhancements
```

### Security Audit
```
User: Review this code for security issues

Skill Response:
1. Scans for innerHTML usage
2. Checks CSP compliance
3. Validates input handling
4. Reviews permission scope
5. Identifies XSS vectors
6. Provides secure refactored code
```

### Store Submission
```
User: Help me submit to Chrome Web Store

Skill Response:
1. Verifies all assets ready
2. Reviews manifest completeness
3. Generates permission justifications
4. Provides privacy policy template
5. Creates submission checklist
6. Explains review process
```

## Technical Patterns

### Message Passing
```javascript
// Send message
chrome.runtime.sendMessage({ action: 'getData' }, (response) => {
  console.log(response.data);
});

// Receive message
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getData') {
    sendResponse({ data: fetchData() });
  }
  return true; // Keep channel open for async
});
```

### Storage Operations
```javascript
// Save
await chrome.storage.local.set({ key: value });

// Load
const result = await chrome.storage.local.get('key');

// Remove
await chrome.storage.local.remove('key');
```

### Tab Queries
```javascript
// Get active tab
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

// Send message to tab
await chrome.tabs.sendMessage(tab.id, { action: 'doSomething' });
```

## Limitations

This skill does NOT cover:
- Chrome Apps (deprecated)
- Legacy Manifest V2 (use V3)
- Firefox-specific WebExtensions
- Native binary modules
- Chrome-internal pages (chrome://)

## Updates & Maintenance

This skill is based on:
- Chrome Extensions Manifest V3 (current)
- Chrome 88+ compatibility
- Knowledge cutoff: January 2025

For the latest Chrome extension updates:
- [Chrome Extensions Docs](https://developer.chrome.com/docs/extensions/)
- [Manifest V3 Guide](https://developer.chrome.com/docs/extensions/mv3/intro/)

## Troubleshooting

### Skill Not Activating
```bash
# Verify skill installation
ls ~/.claude/skills/chrome-extension-developer/

# Expected files:
# - SKILL.md
# - README.md
# - WORKFLOW_REFERENCE.md
```

### Getting Help
If the skill doesn't address your needs:
1. Provide specific error messages
2. Share relevant code snippets
3. Describe expected vs. actual behavior
4. Mention Chrome version
5. Include console errors

## Contributing

Found an issue or have an improvement?
1. Document the problem/suggestion
2. Provide examples if applicable
3. Note Chrome version and OS
4. Share error messages or logs

## License

This skill is provided as-is for educational and development purposes.

---

## Quick Reference Card

### Manifest V3 Basics
```json
{
  "manifest_version": 3,
  "name": "Extension Name",
  "version": "1.0.0",
  "action": { "default_popup": "popup.html" },
  "permissions": ["storage", "activeTab"],
  "host_permissions": ["https://example.com/*"],
  "background": { "service_worker": "background.js" },
  "content_scripts": [{
    "matches": ["https://example.com/*"],
    "js": ["content.js"]
  }]
}
```

### Essential APIs
| API | Purpose | Example |
|-----|---------|---------|
| chrome.runtime | Messaging, lifecycle | `sendMessage()`, `onMessage` |
| chrome.tabs | Tab management | `query()`, `sendMessage()` |
| chrome.storage | Data persistence | `local.set()`, `local.get()` |
| chrome.downloads | File downloads | `download()`, `onChanged` |
| chrome.scripting | Dynamic injection | `executeScript()` |

### Security Rules
- ✅ Use `textContent` not `innerHTML`
- ✅ Validate all user input
- ✅ Minimal permissions only
- ✅ HTTPS for external requests
- ❌ No inline scripts/handlers
- ❌ No eval() or Function()

### File Sizes
- 16x16px - Toolbar icon
- 48x48px - Management page
- 128x128px - Chrome Web Store
- 1280x800 or 640x400 - Screenshots

### Load Extension
1. chrome://extensions/
2. Enable Developer mode
3. Load unpacked
4. Select directory

### Message Pattern
```javascript
// Send
chrome.runtime.sendMessage({ action: 'x' }, callback);

// Receive
chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  respond({ data: 'y' });
  return true; // for async
});
```

### Common Errors
| Error | Cause | Fix |
|-------|-------|-----|
| Extension not loading | manifest.json syntax | Validate JSON |
| Content script not running | Wrong matches pattern | Check URL pattern |
| Messages not passing | No return true | Add return true |
| Service worker dying | No persistence | Use chrome.storage |

---

**Version**: 1.0.0
**Last Updated**: 2025-10-22
**Manifest**: V3
**Chrome**: 88+
