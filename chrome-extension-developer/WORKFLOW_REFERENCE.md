# Chrome Extension Development Workflow Reference

Complete phase-by-phase guide for developing Chrome extensions from ideation to Chrome Web Store deployment.

---

## Phase 1: Ideation & Specification

### Objectives
- Define clear problem statement
- Scope MVP features
- Identify technical requirements
- Assess security and privacy implications

### Checklist
- [ ] User problem clearly articulated
- [ ] Target audience defined
- [ ] MVP features listed (what's in, what's out)
- [ ] Technical feasibility verified
- [ ] Permissions identified and justified
- [ ] Architecture approach chosen
- [ ] Security risks assessed
- [ ] Privacy policy requirements understood

### Key Questions
1. **What problem are we solving?**
   - User pain point
   - Frequency of occurrence
   - Current workarounds

2. **What pages/sites will the extension interact with?**
   - Specific domains or all sites?
   - What permissions are required?

3. **What data will we access/store/transmit?**
   - User data handling
   - Privacy policy requirements
   - GDPR/compliance considerations

4. **What's the minimum viable product?**
   - Core features only
   - Nice-to-have vs. must-have
   - V1 vs. future versions

### Deliverables
- **Brief PRD** (1-2 pages)
  - Problem statement
  - User stories (3-5 core scenarios)
  - Feature list
  - Out-of-scope items

- **Permissions List**
  ```
  Required:
  - activeTab (for current tab access)
  - storage (for user preferences)

  Optional:
  - downloads (if downloading files)

  Host Permissions:
  - https://example.com/* (specific sites only)
  ```

- **Architecture Sketch**
  ```
  [Content Script] <--messages--> [Background Service Worker]
                                            |
                                            v
                                    [External API]
       ^
       |
  [Popup UI]
  ```

### Example: Skill Scalper
```
Problem: Installing Claude Skills from GitHub is manual and tedious
Target: Claude users who want to discover and install skills easily
MVP Features:
  ✓ Scan GitHub repos for SKILL.md files
  ✓ Multi-skill selection UI
  ✓ Download skills as ZIP files
  ✗ Direct installation (not possible due to security)

Permissions:
  - activeTab (detect current GitHub page)
  - downloads (download skill ZIPs)
  - storage (cache discovered skills)
  - host_permissions: ["https://github.com/*", "https://api.github.com/*"]

Architecture:
  - Content script: GitHub page integration, visual badges
  - Background worker: GitHub API, skill discovery, ZIP creation
  - Popup: Skill selection UI, download coordination
```

---

## Phase 2: Project Setup

### Objectives
- Create organized project structure
- Configure manifest.json properly
- Set up development environment
- Prepare asset requirements

### Directory Structure
```
extension/
├── manifest.json          # Extension configuration
├── background.js          # Service worker (if needed)
├── content/
│   └── content.js        # Content script
├── popup/
│   ├── popup.html        # Popup UI
│   ├── popup.js          # Popup logic
│   └── popup.css         # Popup styles
├── icons/
│   ├── 16x16.png         # Extension icon (toolbar)
│   ├── 48x48.png         # Extension icon (management page)
│   └── 128x128.png       # Chrome Web Store icon
├── lib/                  # Third-party libraries (if any)
│   └── jszip.js
└── README.md             # Installation and usage
```

### Manifest.json Template
```json
{
  "manifest_version": 3,
  "name": "Extension Name",
  "version": "1.0.0",
  "description": "Brief description (max 132 chars for store listing)",

  "icons": {
    "16": "icons/16x16.png",
    "48": "icons/48x48.png",
    "128": "icons/128x128.png"
  },

  "action": {
    "default_popup": "popup/popup.html",
    "default_title": "Extension Name",
    "default_icon": {
      "16": "icons/16x16.png",
      "48": "icons/48x48.png",
      "128": "icons/128x128.png"
    }
  },

  "permissions": [
    "storage",
    "activeTab"
  ],

  "host_permissions": [
    "https://example.com/*"
  ],

  "background": {
    "service_worker": "background.js"
  },

  "content_scripts": [
    {
      "matches": ["https://example.com/*"],
      "js": ["content/content.js"],
      "run_at": "document_idle"
    }
  ],

  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### Icon Generation
**Tools:**
- [Hotpot.ai Icon Resizer](https://hotpot.ai/icon-resizer) - Select "Chrome" option
- Canvas API (create programmatically)
- Design tools: Figma, Sketch, Canva

**Requirements:**
- 16x16px - Extension toolbar icon
- 48x48px - Extension management page
- 128x128px - Chrome Web Store listing

**Best Practices:**
- Simple, recognizable design
- High contrast for visibility
- Scalable vector graphics preferred
- PNG format with transparency

### Load Extension for Development
1. Navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle top-right)
3. Click "Load unpacked"
4. Select your extension directory
5. Extension now appears in toolbar

**Refresh After Changes:**
- Click refresh icon on extension card
- Or use keyboard shortcut after changes
- Service worker restarts automatically

### Checklist
- [ ] Directory structure created
- [ ] manifest.json configured
- [ ] Icons created (16, 48, 128px)
- [ ] Extension loads without errors
- [ ] Development environment ready

---

## Phase 3: Core Implementation

### 3.1 Content Scripts

**Purpose**: Interact with web pages, manipulate DOM, extract data

**Template:**
```javascript
// content/content.js

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function init() {
  console.log('Content script initialized on:', window.location.href);

  // Listen for messages from popup/background
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'doSomething') {
      const result = performAction();
      sendResponse({ success: true, data: result });
    }
    return true; // Keep channel open for async response
  });

  // Your content script logic here
  setupEventListeners();
  observeDOMChanges();
}

function performAction() {
  // Query DOM elements
  const element = document.querySelector('.target-element');

  if (element) {
    // SECURE: Use textContent
    element.textContent = 'Safe text';

    // INSECURE: Never use innerHTML with external data
    // element.innerHTML = userInput; // ❌ XSS vulnerability
  }

  return { found: !!element };
}

function setupEventListeners() {
  document.addEventListener('click', (e) => {
    if (e.target.matches('.special-button')) {
      // Send message to background
      chrome.runtime.sendMessage({
        action: 'buttonClicked',
        data: e.target.dataset.value
      });
    }
  });
}

function observeDOMChanges() {
  // For SPAs that dynamically load content
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.addedNodes.length) {
        checkNewNodes(mutation.addedNodes);
      }
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}
```

**Key Patterns:**
1. **Wait for DOM**: Use DOMContentLoaded or check `document.readyState`
2. **Message Passing**: Communicate with background/popup via chrome.runtime
3. **Security**: Always use `textContent` or `createElement`, never `innerHTML`
4. **SPA Support**: Use MutationObserver for dynamic content
5. **Error Handling**: Wrap in try-catch, provide fallbacks

### 3.2 Background Service Worker

**Purpose**: Long-running operations, API calls, message routing

**Template:**
```javascript
// background.js

// Installation event - runs once when extension is installed
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('Extension installed');
    // Set default settings
    chrome.storage.local.set({ settings: { enabled: true } });
  } else if (details.reason === 'update') {
    console.log('Extension updated');
  }
});

// Message handling from content scripts and popups
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Message received:', request);

  // Handle async operations
  (async () => {
    try {
      if (request.action === 'fetchData') {
        const data = await fetchExternalData(request.url);
        sendResponse({ success: true, data });
      } else if (request.action === 'downloadFile') {
        const downloadId = await downloadFile(request.fileUrl);
        sendResponse({ success: true, downloadId });
      }
    } catch (error) {
      console.error('Error handling message:', error);
      sendResponse({ success: false, error: error.message });
    }
  })();

  return true; // Keep channel open for async response
});

// External API calls
async function fetchExternalData(url) {
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json();
}

// Download coordination
async function downloadFile(url) {
  return new Promise((resolve, reject) => {
    chrome.downloads.download({
      url: url,
      filename: 'download.zip',
      saveAs: false
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(downloadId);
      }
    });
  });
}

// Storage operations
async function getStoredData(key) {
  return new Promise((resolve) => {
    chrome.storage.local.get(key, (result) => {
      resolve(result[key]);
    });
  });
}

async function setStoredData(key, value) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [key]: value }, resolve);
  });
}

// Rate limiting helper
class RateLimiter {
  constructor(maxRequests, perMilliseconds) {
    this.maxRequests = maxRequests;
    this.perMilliseconds = perMilliseconds;
    this.requests = [];
  }

  async waitForSlot() {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.perMilliseconds);

    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = Math.min(...this.requests);
      const waitTime = this.perMilliseconds - (now - oldestRequest);
      await new Promise(resolve => setTimeout(resolve, waitTime));
      return this.waitForSlot();
    }

    this.requests.push(now);
  }
}
```

**Key Patterns:**
1. **Async/Await**: Use modern async patterns
2. **Error Handling**: Comprehensive try-catch
3. **Storage**: Persist state in chrome.storage
4. **Rate Limiting**: Respect external API limits
5. **Message Response**: Return true for async sendResponse

### 3.3 Popup Interface

**HTML Template:**
```html
<!-- popup/popup.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Extension Name</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="container">
    <header>
      <h1>Extension Name</h1>
    </header>

    <main>
      <div id="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>

      <div id="content" class="content" style="display: none;">
        <div id="current-site"></div>

        <button id="action-button" class="primary-button">
          Take Action
        </button>

        <div id="results"></div>
      </div>

      <div id="error" class="error" style="display: none;">
        <p class="error-message"></p>
        <button id="retry-button">Retry</button>
      </div>
    </main>

    <footer>
      <a href="#" id="settings-link">Settings</a>
    </footer>
  </div>

  <script src="popup.js"></script>
</body>
</html>
```

**JavaScript Template:**
```javascript
// popup/popup.js

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await init();
  } catch (error) {
    showError(error.message);
  }
});

async function init() {
  // Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (!tab) {
    showError('No active tab found');
    return;
  }

  // Display current site
  const siteDiv = document.getElementById('current-site');
  siteDiv.textContent = `Current site: ${new URL(tab.url).hostname}`;

  // Setup event listeners
  document.getElementById('action-button').addEventListener('click', async () => {
    await performAction(tab);
  });

  document.getElementById('retry-button').addEventListener('click', () => {
    hideError();
    init();
  });

  // Load stored data
  const stored = await chrome.storage.local.get('data');
  if (stored.data) {
    displayResults(stored.data);
  }

  hideLoading();
  showContent();
}

async function performAction(tab) {
  showLoading();

  try {
    // Send message to content script
    const response = await chrome.tabs.sendMessage(tab.id, {
      action: 'doSomething'
    });

    if (response.success) {
      displayResults(response.data);
      showContent();
    } else {
      throw new Error(response.error || 'Action failed');
    }
  } catch (error) {
    showError(error.message);
  }
}

function displayResults(data) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = ''; // Clear previous

  // SECURE: Create elements programmatically
  data.forEach(item => {
    const div = document.createElement('div');
    div.className = 'result-item';
    div.textContent = item.name;
    resultsDiv.appendChild(div);
  });
}

function showLoading() {
  document.getElementById('loading').style.display = 'flex';
  document.getElementById('content').style.display = 'none';
  document.getElementById('error').style.display = 'none';
}

function showContent() {
  document.getElementById('loading').style.display = 'none';
  document.getElementById('content').style.display = 'block';
  document.getElementById('error').style.display = 'none';
}

function showError(message) {
  document.getElementById('loading').style.display = 'none';
  document.getElementById('content').style.display = 'none';
  document.getElementById('error').style.display = 'block';
  document.querySelector('.error-message').textContent = message;
}

function hideError() {
  document.getElementById('error').style.display = 'none';
}
```

**CSS Template:**
```css
/* popup/popup.css */
body {
  width: 400px;
  min-height: 300px;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  color: #333;
}

.container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

header {
  background: #4285f4;
  color: white;
  padding: 16px;
  text-align: center;
}

header h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

main {
  flex: 1;
  padding: 16px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4285f4;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.primary-button {
  background: #4285f4;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  width: 100%;
  margin: 16px 0;
}

.primary-button:hover {
  background: #357ae8;
}

.primary-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error {
  text-align: center;
  color: #d93025;
}

.result-item {
  padding: 8px;
  border-bottom: 1px solid #eee;
}

.result-item:last-child {
  border-bottom: none;
}

footer {
  border-top: 1px solid #eee;
  padding: 12px;
  text-align: center;
}

footer a {
  color: #4285f4;
  text-decoration: none;
}

footer a:hover {
  text-decoration: underline;
}
```

### Security Checklist
- [ ] No `innerHTML` with user/external data
- [ ] Input validation on all user input
- [ ] CSP-compliant code (no inline scripts)
- [ ] External data sanitized before display
- [ ] HTTPS only for external requests
- [ ] Sensitive data not logged to console

---

## Phase 4: Testing & QA

### Manual Testing Protocol

#### 4.1 Basic Functionality
- [ ] Extension loads without errors
- [ ] Icons display correctly
- [ ] Popup opens and renders
- [ ] Content script injects on target pages
- [ ] Background service worker starts

#### 4.2 Core Features
- [ ] All user flows complete successfully
- [ ] Messages pass between scripts correctly
- [ ] Storage persists across sessions
- [ ] Downloads complete successfully
- [ ] API calls return expected data

#### 4.3 Error Scenarios
- [ ] Network failure handling
- [ ] Invalid user input handling
- [ ] Permission denied handling
- [ ] API rate limit handling
- [ ] Empty/null data handling

#### 4.4 Edge Cases
- [ ] Multiple tabs open simultaneously
- [ ] Extension disabled then re-enabled
- [ ] Service worker terminated and restarted
- [ ] Browser restart with extension enabled
- [ ] Rapid repeated actions

#### 4.5 Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Edge (latest)
- [ ] Brave (if applicable)
- [ ] Opera (if applicable)

### Security Audit

#### XSS Prevention
```javascript
// ❌ VULNERABLE
element.innerHTML = userInput;
element.innerHTML = apiResponse.content;

// ✅ SECURE
element.textContent = userInput;
element.appendChild(document.createTextNode(apiResponse.content));

// ✅ SECURE (creating elements)
const div = document.createElement('div');
div.textContent = userInput;
element.appendChild(div);
```

#### Input Validation
```javascript
// Validate URLs
function isValidUrl(string) {
  try {
    const url = new URL(string);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

// Sanitize filenames
function sanitizeFilename(filename) {
  return filename.replace(/[^a-z0-9.-]/gi, '_').substring(0, 255);
}

// Validate email
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
```

#### CSP Compliance Check
- [ ] No inline `<script>` tags in HTML
- [ ] No inline event handlers (`onclick`, etc.)
- [ ] No `eval()` or `Function()` constructors
- [ ] No inline styles (use classes)
- [ ] All scripts referenced via `src` attribute

### Performance Testing
- [ ] Popup opens in <500ms
- [ ] Content script loads without blocking page
- [ ] API calls complete in reasonable time
- [ ] Memory usage stays under 50MB
- [ ] No memory leaks on repeated operations

### Accessibility Testing
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Sufficient color contrast
- [ ] Focus indicators visible

---

## Phase 5: Packaging & Assets

### Icon Preparation
**Required Sizes:**
- 16x16px (toolbar, favicon)
- 48x48px (extension management)
- 128x128px (Chrome Web Store)

**Best Practices:**
- Simple, recognizable design
- High contrast
- Scalable (vector recommended)
- PNG with transparency
- Avoid text (use symbols/icons)

### Screenshots
**Requirements:**
- 1280x800 or 640x400 resolution
- PNG or JPEG format
- 3-5 screenshots minimum
- Show key features
- Clean, uncluttered
- Representative of actual use

**Tips:**
- Use browser screenshot tools
- Crop unnecessary chrome
- Highlight key UI elements
- Show before/after for transformations
- Include captions in store listing

### Privacy Policy
**Required if:**
- Collecting user data
- Using `<all_urls>` permission
- Accessing sensitive permissions
- Third-party analytics

**Template Structure:**
```
1. What data we collect
2. How we use data
3. How we store data
4. How we share data (if applicable)
5. User control and data deletion
6. Contact information
```

**Host Options:**
- GitHub Pages (free)
- Your website
- Google Docs (public link)

### ZIP Creation
```bash
# Exclude unnecessary files
zip -r extension.zip extension/ \
  -x "*.git*" \
  -x "*.DS_Store" \
  -x "*node_modules*" \
  -x "*.md" \
  -x "*.sh"
```

**What to include:**
- manifest.json
- All .js files
- All .html files
- All .css files
- icons/ directory
- Any lib/ dependencies

**What to exclude:**
- .git/
- node_modules/
- .DS_Store
- README.md
- Development scripts
- Test files

### Packaging Checklist
- [ ] Icons (16, 48, 128px) generated
- [ ] Screenshots (3-5) captured
- [ ] Privacy policy written and hosted
- [ ] manifest.json version incremented
- [ ] All files included in ZIP
- [ ] ZIP size under 5MB
- [ ] No development files in ZIP

---

## Phase 6: Chrome Web Store Submission

### 6.1 Developer Registration
1. Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole/register)
2. Pay $5 one-time registration fee
3. Complete developer profile
4. Verify email address

### 6.2 Store Listing Preparation

#### Basic Info
- **Name**: 45 characters max, clear and descriptive
- **Summary**: 132 characters max, concise value proposition
- **Description**: Detailed explanation of features and benefits
  - What it does
  - How to use it
  - Key features
  - Benefits
  - Support information

#### Category
Choose most appropriate:
- Productivity
- Developer Tools
- Communication
- Entertainment
- News & Weather
- Accessibility
- Etc.

#### Language
Select primary language (can add more later)

#### Screenshots & Promotional Images
- **Screenshots**: 3-5 images (1280x800 or 640x400)
- **Small promotional tile**: 440x280 (optional)
- **Marquee promotional tile**: 1400x560 (optional, for featured)

### 6.3 Privacy Practices

#### Single Purpose
Clearly state the extension's primary purpose:
```
Example: "This extension helps users discover and install Claude Skills
from GitHub repositories by scanning for SKILL.md files and facilitating
easy downloads."
```

#### Permission Justifications
For each permission, explain why it's needed:
```
- activeTab: To detect the current GitHub page URL
- downloads: To download skill ZIP files to user's Downloads folder
- storage: To cache discovered skills for better performance
- host_permissions (github.com): To scan repositories for SKILL.md files
```

#### Data Usage
- What data is collected (if any)
- How data is used
- Whether data is sold to third parties (usually: No)
- Privacy policy URL (if applicable)

### 6.4 Distribution

#### Visibility
- Public: Visible to all users in Chrome Web Store
- Unlisted: Only accessible via direct link
- Private: Only to specific users/domains

#### Regions
Select regions where extension will be available (default: all)

### 6.5 Upload & Submit

1. Click "New Item" in developer dashboard
2. Upload ZIP file
3. Complete all required fields:
   - Store listing tab
   - Privacy practices tab
   - Distribution tab
4. Review all information
5. Click "Submit for review"
6. Pay attention to "Why can't I submit?" button if blocked

### 6.6 Review Process

**Timeline:**
- First submission: 1 day to 2 weeks
- Updates: Usually faster (1-3 days)
- Complex permissions: Longer review

**Common Rejection Reasons:**
1. **Excessive keywords**: Don't repeat description in summary
2. **Misleading functionality**: Must match description
3. **Permission justification**: Explain each permission clearly
4. **Policy violations**: Review [Chrome Web Store policies](https://developer.chrome.com/docs/webstore/program-policies/)
5. **Broken functionality**: Must work as described
6. **Security vulnerabilities**: XSS, insecure practices
7. **Copyright issues**: Trademark violations, stolen content

**If Rejected:**
1. Read rejection reason carefully
2. Fix identified issues
3. Update version number
4. Re-submit with changes noted

### 6.7 Post-Approval

**After Approval:**
- Extension goes live on Chrome Web Store
- Users can install via store page
- Reviews and ratings start accumulating
- Download stats become available

**Store Page URL:**
```
https://chrome.google.com/webstore/detail/[extension-id]
```

### Submission Checklist
- [ ] Developer account registered and verified
- [ ] Extension name unique and descriptive
- [ ] Summary clear and under 132 characters
- [ ] Detailed description complete
- [ ] Category selected appropriately
- [ ] 3-5 screenshots uploaded
- [ ] Single purpose clearly stated
- [ ] All permissions justified
- [ ] Privacy policy provided (if required)
- [ ] Distribution settings configured
- [ ] ZIP file uploaded successfully
- [ ] All required fields completed
- [ ] Ready to submit for review

---

## Phase 7: Post-Launch Maintenance

### Monitoring

#### User Feedback
- Monitor reviews on Chrome Web Store
- Respond to user questions
- Track feature requests
- Identify common issues

#### Analytics (Optional)
```javascript
// Simple usage tracking (if privacy policy allows)
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ installDate: Date.now() });
});

chrome.runtime.onMessage.addListener((request) => {
  if (request.action === 'featureUsed') {
    trackFeatureUsage(request.feature);
  }
});
```

#### Error Tracking
```javascript
// Log errors to background console
window.addEventListener('error', (event) => {
  console.error('Error:', event.error);
  // Could send to error tracking service if privacy policy allows
});
```

### Updates

#### Version Numbering
Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes

Examples:
- 1.0.0 → 1.0.1 (bug fix)
- 1.0.1 → 1.1.0 (new feature)
- 1.1.0 → 2.0.0 (breaking change)

#### Update Process
1. Make changes to codebase
2. Test thoroughly
3. Update version in manifest.json
4. Create new ZIP
5. Upload to Chrome Web Store
6. Submit for review
7. Monitor rollout

#### Rollout Strategy
- Start with smaller percentage (if using staged rollout)
- Monitor for issues
- Gradually increase to 100%
- Keep previous version handy for rollback

### Deprecation

#### When to Deprecate
- Low usage (<100 users)
- High maintenance burden
- Replaced by better solution
- API/platform changes make it obsolete

#### Deprecation Process
1. Announce deprecation (update description)
2. Set timeline (e.g., 90 days)
3. Suggest alternatives
4. Stop accepting new users (unlisted)
5. Remove from store after timeline

### Post-Launch Checklist
- [ ] Monitor user reviews weekly
- [ ] Respond to user questions within 48 hours
- [ ] Track crash reports and errors
- [ ] Plan and release regular updates
- [ ] Keep manifest permissions minimal
- [ ] Maintain privacy policy (if applicable)
- [ ] Test updates before releasing
- [ ] Keep documentation up to date

---

## Quick Reference: Common Patterns

### Message Passing
```javascript
// From content script to background
chrome.runtime.sendMessage({ action: 'getData' }, (response) => {
  console.log(response);
});

// From popup to content script
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  chrome.tabs.sendMessage(tabs[0].id, { action: 'doSomething' });
});

// Listening for messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getData') {
    sendResponse({ data: 'some data' });
  }
  return true; // Keep channel open for async
});
```

### Storage Operations
```javascript
// Save data
await chrome.storage.local.set({ key: value });

// Get data
const result = await chrome.storage.local.get('key');
console.log(result.key);

// Remove data
await chrome.storage.local.remove('key');

// Clear all data
await chrome.storage.local.clear();
```

### Tab Operations
```javascript
// Get current tab
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

// Create new tab
await chrome.tabs.create({ url: 'https://example.com' });

// Update tab
await chrome.tabs.update(tabId, { url: 'https://example.com' });

// Close tab
await chrome.tabs.remove(tabId);
```

### Downloads
```javascript
// Start download
const downloadId = await chrome.downloads.download({
  url: 'https://example.com/file.zip',
  filename: 'myfile.zip',
  saveAs: false // true to show save dialog
});

// Monitor download progress
chrome.downloads.onChanged.addListener((delta) => {
  if (delta.state && delta.state.current === 'complete') {
    console.log('Download complete');
  }
});
```

---

## Troubleshooting Guide

### Extension Won't Load
- Check manifest.json syntax (valid JSON)
- Verify all file paths are correct
- Check console for errors
- Ensure icons exist at specified paths

### Content Script Not Running
- Verify `matches` pattern in manifest
- Check if host_permissions granted
- Reload extension after changes
- Check target page URL matches pattern

### Messages Not Passing
- Ensure `return true` for async sendResponse
- Check sender/receiver are active
- Verify message structure matches
- Check for typos in action names

### Service Worker Dying
- Design for ephemerality
- Use chrome.storage for persistence
- Don't rely on global variables
- Handle chrome.runtime.onStartup

### Store Rejection
- Read rejection reason carefully
- Check all permissions are justified
- Ensure description matches functionality
- Review Chrome Web Store policies
- Avoid keyword stuffing

---

## Resources

### Official Documentation
- [Chrome Extensions Docs](https://developer.chrome.com/docs/extensions/)
- [Manifest V3 Migration](https://developer.chrome.com/docs/extensions/migrating/)
- [Chrome Web Store Policies](https://developer.chrome.com/docs/webstore/program-policies/)
- [API Reference](https://developer.chrome.com/docs/extensions/reference/)

### Tools
- [Icon Resizer](https://hotpot.ai/icon-resizer)
- [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole/)
- [Extension Manifest Generator](https://manifest.crxpak.com/)

### Community
- [Stack Overflow - chrome-extension tag](https://stackoverflow.com/questions/tagged/google-chrome-extension)
- [Chrome Extensions Google Group](https://groups.google.com/a/chromium.org/g/chromium-extensions)
- [r/chrome_extensions](https://www.reddit.com/r/chrome_extensions/)

---

**Last Updated**: 2025-10-22
**Manifest Version**: V3
**Maintainer**: Claude Chrome Extension Developer Skill
