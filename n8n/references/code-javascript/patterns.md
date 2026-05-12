# Code Node JavaScript: Patterns

Named, copy-paste-ready patterns drawn from production n8n workflows. Each pattern includes the use case, the key technique(s), a complete working example, and common variations.

For the underlying API surface used in these examples (`$input`, `$helpers`, `DateTime`, `$jmespath`, `$getWorkflowStaticData`), see [api.md](./api.md). For the error symptoms each pattern protects against, see [gotchas.md](./gotchas.md).

---

## Pattern Index

**Data ingest and aggregation**

1. Multi-source data aggregation
2. Filter active items / basic batch transform
3. Group by category
4. Deduplicate by id

**Text / content processing**

5. Regex filtering and pattern matching
6. Markdown parsing and structured extraction
7. String aggregation and reporting

**Data validation and comparison**

8. JSON comparison and validation

**Data transformation**

9. CRM data transformation
10. Array transformation with computed context
11. GitHub release / version processing

**Output formatting**

12. Slack Block Kit formatting

**Filtering and ranking**

13. Top N filtering and ranking

**Loop control (SplitInBatches)**

14. Cross-iteration data accumulation
15. `pairedItem` for new output items

**HTTP**

16. HTTP calls via `$helpers.httpRequest`

---

## Pattern 1: Multi-Source Data Aggregation

**Use case**: Combining data from multiple APIs, RSS feeds, webhooks, or databases.

**When to use**:

- Collecting data from multiple services
- Normalizing different API response formats
- Merging data sources into a unified structure
- Building aggregated reports

**Key techniques**: loop iteration, conditional parsing, data normalization.

```javascript
// Process and structure data collected from multiple sources
const allItems = $input.all();
let processedArticles = [];

for (const item of allItems) {
  const sourceName = item.json.name || 'Unknown';
  const sourceData = item.json;

  // Hacker News
  if (sourceName === 'Hacker News' && sourceData.hits) {
    for (const hit of sourceData.hits) {
      processedArticles.push({
        title: hit.title,
        url: hit.url,
        summary: hit.story_text || 'No summary',
        source: 'Hacker News',
        score: hit.points || 0,
        fetchedAt: new Date().toISOString()
      });
    }
  }
  // Reddit
  else if (sourceName === 'Reddit' && sourceData.data?.children) {
    for (const post of sourceData.data.children) {
      processedArticles.push({
        title: post.data.title,
        url: post.data.url,
        summary: post.data.selftext || 'No summary',
        source: 'Reddit',
        score: post.data.score || 0,
        fetchedAt: new Date().toISOString()
      });
    }
  }
  // RSS feed
  else if (sourceName === 'RSS' && sourceData.items) {
    for (const rssItem of sourceData.items) {
      processedArticles.push({
        title: rssItem.title,
        url: rssItem.link,
        summary: rssItem.description || 'No summary',
        source: 'RSS Feed',
        score: 0,
        fetchedAt: new Date().toISOString()
      });
    }
  }
}

processedArticles.sort((a, b) => b.score - a.score);

return processedArticles.map(article => ({ json: article }));
```

### Variations

```javascript
// Variation: source weighting
for (const article of processedArticles) {
  const weights = { 'Hacker News': 1.5, 'Reddit': 1.0, 'RSS Feed': 0.8 };
  article.weightedScore = article.score * (weights[article.source] || 1.0);
}

// Variation: minimum score threshold
processedArticles = processedArticles.filter(a => a.score >= 10);

// Variation: deduplicate by URL
const seen = new Set();
processedArticles = processedArticles.filter(a => {
  if (seen.has(a.url)) return false;
  seen.add(a.url);
  return true;
});
```

---

## Pattern 2: Filter Active Items / Basic Batch Transform

**Use case**: The most common Code-node shape: take all items, filter some, reshape the rest.

```javascript
const allItems = $input.all();

const valid = allItems.filter(item => item.json.status === 'active');

const mapped = valid.map(item => ({
  json: {
    id: item.json.id,
    name: item.json.name,
    processedAt: new Date().toISOString()
  }
}));

return mapped;
```

### Variation: aggregate totals

```javascript
const items = $input.all();
const total = items.reduce((sum, i) => sum + (i.json.amount || 0), 0);

return [{
  json: {
    total,
    count: items.length,
    average: total / items.length,
    timestamp: new Date().toISOString()
  }
}];
```

---

## Pattern 3: Group By Category

```javascript
const allItems = $input.all();
const grouped = {};

for (const item of allItems) {
  const category = item.json.category || 'Uncategorized';
  if (!grouped[category]) grouped[category] = [];
  grouped[category].push(item.json);
}

return Object.entries(grouped).map(([category, items]) => ({
  json: { category, items, count: items.length }
}));
```

---

## Pattern 4: Deduplicate By ID

```javascript
const allItems = $input.all();
const seen = new Set();
const unique = [];

for (const item of allItems) {
  const id = item.json.id;
  if (!seen.has(id)) {
    seen.add(id);
    unique.push(item);
  }
}

return unique;
```

---

## Pattern 5: Regex Filtering and Pattern Matching

**Use case**: Content analysis, keyword extraction, mention tracking, text parsing.

**When to use**:

- Extracting mentions, tags, or symbols from text
- Finding patterns in unstructured data
- Counting keyword occurrences
- Validating formats (emails, phone numbers, URLs)

**Key techniques**: regex matching, object aggregation, sorting / ranking.

```javascript
// Extract and track mentions using regex
const etfPattern = /\b([A-Z]{2,5})\b/g;
const knownETFs = ['VOO', 'VTI', 'VT', 'SCHD', 'QYLD', 'VXUS', 'SPY', 'QQQ'];

const etfMentions = {};

for (const item of $input.all()) {
  const data = item.json.data;
  if (!data?.children) continue;

  for (const post of data.children) {
    const title = post.data.title || '';
    const body  = post.data.selftext || '';
    const combinedText = (title + ' ' + body).toUpperCase();

    const matches = combinedText.match(etfPattern);
    if (!matches) continue;

    for (const match of matches) {
      if (!knownETFs.includes(match)) continue;

      if (!etfMentions[match]) {
        etfMentions[match] = { count: 0, totalScore: 0, posts: [] };
      }
      etfMentions[match].count++;
      etfMentions[match].totalScore += post.data.score || 0;
      etfMentions[match].posts.push({
        title: post.data.title,
        url: post.data.url,
        score: post.data.score
      });
    }
  }
}

return Object.entries(etfMentions)
  .map(([etf, data]) => ({
    json: {
      etf,
      mentions: data.count,
      totalScore: data.totalScore,
      averageScore: data.totalScore / data.count,
      topPosts: data.posts.sort((a, b) => b.score - a.score).slice(0, 3)
    }
  }))
  .sort((a, b) => b.json.mentions - a.json.mentions);
```

### Variations

```javascript
// Email extraction
const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
const emails = text.match(emailPattern) || [];

// Phone number extraction
const phonePattern = /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g;
const phones = text.match(phonePattern) || [];

// Hashtag extraction (capture groups)
const hashtagPattern = /#(\w+)/g;
const hashtags = [];
let match;
while ((match = hashtagPattern.exec(text)) !== null) {
  hashtags.push(match[1]);
}

// URL extraction
const urlPattern = /https?:\/\/[^\s]+/g;
const urls = text.match(urlPattern) || [];
```

---

## Pattern 6: Markdown Parsing and Structured Extraction

**Use case**: Parsing formatted text, extracting structured fields, content transformation.

**When to use**:

- Parsing markdown or HTML
- Extracting data from structured text
- Converting formatted content to JSON
- Processing documentation or articles

**Key techniques**: regex grouping, helper functions, while-loop iteration with `RegExp.exec`.

```javascript
// Parse markdown into a list of job postings
const markdown = $input.first().json.data.markdown;
const adRegex = /##\s*(.*?)\n(.*?)(?=\n##|\n---|$)/gs;

const ads = [];
let match;

function parseTimeToMinutes(timeStr) {
  if (!timeStr) return 999999;

  const hourMatch = timeStr.match(/(\d+)\s*hour/);
  const dayMatch  = timeStr.match(/(\d+)\s*day/);
  const minMatch  = timeStr.match(/(\d+)\s*min/);

  let totalMinutes = 0;
  if (dayMatch)  totalMinutes += parseInt(dayMatch[1])  * 1440;
  if (hourMatch) totalMinutes += parseInt(hourMatch[1]) * 60;
  if (minMatch)  totalMinutes += parseInt(minMatch[1]);
  return totalMinutes;
}

while ((match = adRegex.exec(markdown)) !== null) {
  const title   = match[1]?.trim() || 'No title';
  const content = match[2]?.trim() || '';

  const districtMatch = content.match(/\*\*District:\*\*\s*(.*?)(?:\n|$)/);
  const salaryMatch   = content.match(/\*\*Salary:\*\*\s*(.*?)(?:\n|$)/);
  const timeMatch     = content.match(/Posted:\s*(.*?)\*/);

  ads.push({
    title,
    district: districtMatch?.[1].trim() || 'Unknown',
    salary:   salaryMatch?.[1].trim() || 'Not specified',
    postedTimeAgo:  timeMatch?.[1] || 'Unknown',
    timeInMinutes:  parseTimeToMinutes(timeMatch?.[1]),
    fullContent:    content,
    extractedAt:    new Date().toISOString()
  });
}

ads.sort((a, b) => a.timeInMinutes - b.timeInMinutes);

return ads.map(ad => ({ json: ad }));
```

### Variations

```javascript
// Parse HTML table rows
const tableRegex = /<tr>(.*?)<\/tr>/gs;
const cellRegex  = /<td>(.*?)<\/td>/g;
const rows = [];
let tableMatch;
while ((tableMatch = tableRegex.exec(htmlTable)) !== null) {
  const cells = [];
  let cellMatch;
  while ((cellMatch = cellRegex.exec(tableMatch[1])) !== null) {
    cells.push(cellMatch[1].trim());
  }
  if (cells.length > 0) rows.push(cells);
}

// Extract code blocks from markdown
const codeBlockRegex = /```(\w+)?\n(.*?)```/gs;
const codeBlocks = [];
let m;
while ((m = codeBlockRegex.exec(markdown)) !== null) {
  codeBlocks.push({ language: m[1] || 'plain', code: m[2].trim() });
}

// Parse YAML frontmatter
const frontmatterRegex = /^---\n(.*?)\n---/s;
const frontmatterMatch = content.match(frontmatterRegex);
if (frontmatterMatch) {
  const yamlLines = frontmatterMatch[1].split('\n');
  const metadata = {};
  for (const line of yamlLines) {
    const [key, ...valueParts] = line.split(':');
    if (key && valueParts.length > 0) {
      metadata[key.trim()] = valueParts.join(':').trim();
    }
  }
}
```

---

## Pattern 7: String Aggregation and Reporting

**Use case**: Report generation, log aggregation, content concatenation, summary creation.

**Key techniques**: array joining, template literals, timestamp handling.

```javascript
const allItems = $input.all();
const messages = allItems.map(item => item.json.message);

const header  = `Daily Summary Report\n${new Date().toLocaleString()}\nTotal Items: ${messages.length}\n\n`;
const divider = '\n\n---\n\n';
const footer  = `\n\n---\n\nReport generated at ${new Date().toISOString()}`;

const finalReport = header + messages.join(divider) + footer;

return [{
  json: {
    report: finalReport,
    messageCount: messages.length,
    generatedAt: new Date().toISOString(),
    reportLength: finalReport.length
  }
}];
```

### Variations

```javascript
// Numbered list
const numbered = allItems
  .map((i, idx) => `${idx + 1}. ${i.json.title}\n   ${i.json.description}`)
  .join('\n\n');

// Markdown table
const headers = '| Name | Status | Score |\n|------|--------|-------|\n';
const rows = allItems
  .map(i => `| ${i.json.name} | ${i.json.status} | ${i.json.score} |`)
  .join('\n');
const table = headers + rows;

// HTML report
const htmlReport = `
<!DOCTYPE html>
<html>
<head><title>Report</title></head>
<body>
  <h1>Report ${new Date().toLocaleDateString()}</h1>
  <ul>
    ${allItems.map(i => `<li>${i.json.title}: ${i.json.value}</li>`).join('\n    ')}
  </ul>
</body>
</html>`;

// JSON summary with statistics
const summary = {
  generated: new Date().toISOString(),
  totalItems: allItems.length,
  items: allItems.map(i => i.json),
  statistics: {
    total:   allItems.reduce((s, i) => s + (i.json.value || 0), 0),
    average: allItems.reduce((s, i) => s + (i.json.value || 0), 0) / allItems.length,
    max:     Math.max(...allItems.map(i => i.json.value || 0)),
    min:     Math.min(...allItems.map(i => i.json.value || 0))
  }
};
```

---

## Pattern 8: JSON Comparison and Validation

**Use case**: Workflow versioning, configuration validation, change detection, data integrity.

**Key techniques**: JSON ordering for stable comparison, base64 decoding, deep diff.

```javascript
// Compare two JSON objects, one base64-encoded, one current
const orderJsonKeys = (obj) => {
  const ordered = {};
  Object.keys(obj).sort().forEach(key => { ordered[key] = obj[key]; });
  return ordered;
};

const allItems = $input.all();
const origWorkflow    = JSON.parse(Buffer.from(allItems[0].json.content, 'base64').toString());
const currentWorkflow = allItems[1].json;

const orderedOriginal = orderJsonKeys(origWorkflow);
const orderedCurrent  = orderJsonKeys(currentWorkflow);

const isSame = JSON.stringify(orderedOriginal) === JSON.stringify(orderedCurrent);

const differences = [];
for (const key of Object.keys(orderedOriginal)) {
  if (JSON.stringify(orderedOriginal[key]) !== JSON.stringify(orderedCurrent[key])) {
    differences.push({
      field: key,
      original: orderedOriginal[key],
      current:  orderedCurrent[key]
    });
  }
}
for (const key of Object.keys(orderedCurrent)) {
  if (!(key in orderedOriginal)) {
    differences.push({
      field: key,
      original: null,
      current: orderedCurrent[key],
      status: 'new'
    });
  }
}

return [{
  json: {
    identical: isSame,
    differenceCount: differences.length,
    differences,
    original: orderedOriginal,
    current:  orderedCurrent,
    comparedAt: new Date().toISOString()
  }
}];
```

### Variations

```javascript
// Simple equality
const isEqual = JSON.stringify(obj1) === JSON.stringify(obj2);

// Deep diff with detailed changes
function deepDiff(obj1, obj2, path = '') {
  const changes = [];
  for (const key in obj1) {
    const currentPath = path ? `${path}.${key}` : key;
    if (!(key in obj2)) {
      changes.push({ type: 'removed', path: currentPath, value: obj1[key] });
    } else if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
      changes.push(...deepDiff(obj1[key], obj2[key], currentPath));
    } else if (obj1[key] !== obj2[key]) {
      changes.push({ type: 'modified', path: currentPath, from: obj1[key], to: obj2[key] });
    }
  }
  for (const key in obj2) {
    if (!(key in obj1)) {
      const currentPath = path ? `${path}.${key}` : key;
      changes.push({ type: 'added', path: currentPath, value: obj2[key] });
    }
  }
  return changes;
}

// Schema validation
function validateSchema(data, schema) {
  const errors = [];
  for (const field of schema.required || []) {
    if (!(field in data)) errors.push(`Missing required field: ${field}`);
  }
  for (const [field, type] of Object.entries(schema.types || {})) {
    if (field in data && typeof data[field] !== type) {
      errors.push(`Field ${field} should be ${type}, got ${typeof data[field]}`);
    }
  }
  return { valid: errors.length === 0, errors };
}
```

---

## Pattern 9: CRM Data Transformation

**Use case**: Lead enrichment, data normalization, API preparation, form-data processing.

**Key techniques**: destructuring, field splitting, format normalization.

```javascript
const item = $input.all()[0];
const { name, email, phone, company, course_interest, message, timestamp } = item.json;

const nameParts = name.split(' ');
const firstName = nameParts[0] || '';
const lastName  = nameParts.slice(1).join(' ') || 'Unknown';

const cleanPhone = phone.replace(/[^\d]/g, '');

const crmData = {
  data: {
    type: 'Contact',
    attributes: {
      first_name:    firstName,
      last_name:     lastName,
      email1:        email,
      phone_work:    cleanPhone,
      account_name:  company,
      description:   `Course Interest: ${course_interest}\n\nMessage: ${message}\n\nSubmitted: ${timestamp}`,
      lead_source:   'Website Form',
      status:        'New'
    }
  },
  metadata: {
    original_submission: timestamp,
    processed_at: new Date().toISOString()
  }
};

return [{ json: { ...item.json, crmData, processed: true } }];
```

### Variations

```javascript
// Batch contact processing
const contacts = $input.all();
return contacts.map(item => {
  const data = item.json;
  const [firstName, ...lastNameParts] = data.name.split(' ');
  return {
    json: {
      firstName,
      lastName: lastNameParts.join(' ') || 'Unknown',
      email: data.email.toLowerCase(),
      phone: data.phone.replace(/[^\d]/g, ''),
      tags: [data.source, data.interest_level].filter(Boolean)
    }
  };
});

// Contact normalization helper
function normalizeContact(raw) {
  return {
    first_name: raw.firstName?.trim() || '',
    last_name:  raw.lastName?.trim()  || 'Unknown',
    email:      raw.email?.toLowerCase().trim() || '',
    phone:      raw.phone?.replace(/[^\d]/g, '') || '',
    company:    raw.company?.trim() || 'Unknown',
    title:      raw.title?.trim() || '',
    valid:      Boolean(raw.email && raw.firstName)
  };
}

// Lead scoring
function calculateLeadScore(data) {
  let score = 0;
  if (data.email)   score += 10;
  if (data.phone)   score += 10;
  if (data.company) score += 15;
  if (data.title?.toLowerCase().includes('director')) score += 20;
  if (data.title?.toLowerCase().includes('manager'))  score += 15;
  if (data.message?.length > 100) score += 10;
  return score;
}
```

---

## Pattern 10: Array Transformation With Computed Context

**Use case**: Quick data transformation, field mapping, adding computed fields, simple pluralization.

```javascript
const releases = $input.first().json
  .filter(r => !r.prerelease && !r.draft)
  .slice(0, 10)
  .map(r => ({
    version:           r.tag_name,
    assetCount:        r.assets.length,
    assetsCountText:   r.assets.length === 1 ? 'file' : 'files',
    downloadUrl:       r.html_url,
    isRecent:          new Date(r.published_at) > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    age:               Math.floor((Date.now() - new Date(r.published_at)) / (24 * 60 * 60 * 1000)),
    ageText:           `${Math.floor((Date.now() - new Date(r.published_at)) / (24 * 60 * 60 * 1000))} days ago`
  }));

return releases.map(r => ({ json: r }));
```

### Variations

```javascript
// Add ranking with medal emoji
const ranked = $input.all()
  .sort((a, b) => b.json.score - a.json.score)
  .map((item, idx) => ({
    json: {
      ...item.json,
      rank: idx + 1,
      medal: idx < 3 ? ['1st', '2nd', '3rd'][idx] : ''
    }
  }));

// Add percentage calculations
const total = $input.all().reduce((s, i) => s + i.json.value, 0);
const withPct = $input.all().map(item => ({
  json: {
    ...item.json,
    percentage: ((item.json.value / total) * 100).toFixed(2) + '%'
  }
}));

// Add category labels
const categorize = (v) => v > 100 ? 'High' : v > 50 ? 'Medium' : 'Low';
const categorized = $input.all().map(item => ({
  json: { ...item.json, category: categorize(item.json.value) }
}));
```

---

## Pattern 11: GitHub Release / Version Processing

**Use case**: Release notes generation, changelog parsing, version comparison.

```javascript
// Extract and filter stable releases from GitHub API output
const allReleases = $input.first().json;

const stableReleases = allReleases
  .filter(r => !r.prerelease && !r.draft)
  .slice(0, 10)
  .map(r => {
    const body = r.body || '';
    let highlights = 'No highlights available';

    if (body.includes('## Highlights:')) {
      highlights = body.split('## Highlights:')[1]?.split('##')[0]?.trim();
    } else {
      highlights = body.substring(0, 500) + '...';
    }

    return {
      tag:            r.tag_name,
      name:           r.name,
      published:      r.published_at,
      publishedDate:  new Date(r.published_at).toLocaleDateString(),
      author:         r.author.login,
      url:            r.html_url,
      changelog:      body,
      highlights,
      assetCount:     r.assets.length,
      assets: r.assets.map(a => ({
        name:           a.name,
        size:           a.size,
        downloadCount:  a.download_count,
        downloadUrl:    a.browser_download_url
      }))
    };
  });

return stableReleases.map(r => ({ json: r }));
```

### Variations

```javascript
// Semantic version comparison
function compareVersions(v1, v2) {
  const p1 = v1.replace('v', '').split('.').map(Number);
  const p2 = v2.replace('v', '').split('.').map(Number);
  for (let i = 0; i < Math.max(p1.length, p2.length); i++) {
    const a = p1[i] || 0;
    const b = p2[i] || 0;
    if (a > b) return 1;
    if (a < b) return -1;
  }
  return 0;
}

// Breaking change detection
function hasBreakingChanges(changelog) {
  const breaking = ['BREAKING CHANGE', 'breaking change', 'BC:'];
  return breaking.some(k => changelog.includes(k));
}

// Extract version components
const versionPattern = /v?(\d+)\.(\d+)\.(\d+)/;
const match = tagName.match(versionPattern);
if (match) {
  const [, major, minor, patch] = match;
  const version = { major: parseInt(major), minor: parseInt(minor), patch: parseInt(patch) };
}
```

---

## Pattern 12: Slack Block Kit Formatting

**Use case**: Chat notifications, rich messages, interactive elements, status reports.

```javascript
const date = new Date().toISOString().split('T')[0];
const data = $input.first().json;

return [{
  json: {
    text: `Daily Report ${date}`,   // fallback
    blocks: [
      {
        type: 'header',
        text: { type: 'plain_text', text: `Daily Security Report ${date}` }
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Status:* ${data.status === 'ok' ? 'All Clear' : 'Issues Detected'}\n*Alerts:* ${data.alertCount || 0}\n*Updated:* ${new Date().toLocaleString()}`
        }
      },
      { type: 'divider' },
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Failed Logins:*\n${data.failedLogins || 0}` },
          { type: 'mrkdwn', text: `*API Errors:*\n${data.apiErrors || 0}` },
          { type: 'mrkdwn', text: `*Uptime:*\n${data.uptime || '100%'}` },
          { type: 'mrkdwn', text: `*Response Time:*\n${data.avgResponseTime || 'N/A'}ms` }
        ]
      },
      {
        type: 'context',
        elements: [{ type: 'mrkdwn', text: 'Report generated automatically by n8n workflow' }]
      }
    ]
  }
}];
```

### Variations

```javascript
// Interactive button
const blocksWithButton = [{
  type: 'section',
  text: { type: 'mrkdwn', text: 'Would you like to approve this request?' },
  accessory: {
    type: 'button',
    text: { type: 'plain_text', text: 'Approve' },
    style: 'primary',
    value: 'approve',
    action_id: 'approve_button'
  }
}];

// Status emoji mapping
function statusIndicator(status) {
  return ({ success: '[ok]', warning: '[warn]', error: '[err]', info: '[i]' })[status] || '•';
}

// Truncate long messages
function truncate(text, max = 3000) {
  if (text.length <= max) return text;
  return text.substring(0, max - 3) + '...';
}
```

---

## Pattern 13: Top N Filtering and Ranking

**Use case**: RAG pipelines, ranking algorithms, result filtering, leaderboards.

```javascript
const ragResponse = $input.item.json;
const chunks = ragResponse.chunks || [];

const topChunks = chunks
  .sort((a, b) => (b.similarity || 0) - (a.similarity || 0))
  .slice(0, 6);

return [{
  json: {
    query: ragResponse.query,
    topChunks,
    count: topChunks.length,
    maxSimilarity: topChunks[0]?.similarity || 0,
    minSimilarity: topChunks[topChunks.length - 1]?.similarity || 0,
    averageSimilarity:
      topChunks.reduce((s, c) => s + (c.similarity || 0), 0) / topChunks.length
  }
}];
```

### Variations

```javascript
// Top N with minimum threshold
const threshold = 0.7;
const top = $input.all()
  .filter(i => i.json.score >= threshold)
  .sort((a, b) => b.json.score - a.json.score)
  .slice(0, 10);

// Bottom N
const bottom = $input.all()
  .sort((a, b) => a.json.score - b.json.score)
  .slice(0, 5);

// Composite scoring
const ranked = $input.all()
  .map(i => ({
    ...i,
    compositeScore: (i.json.relevance * 0.6) + (i.json.recency * 0.4)
  }))
  .sort((a, b) => b.compositeScore - a.compositeScore)
  .slice(0, 10);

// Percentile filtering
const allScores = $input.all().map(i => i.json.score).sort((a, b) => b - a);
const p95 = allScores[Math.floor(allScores.length * 0.05)];
const topPercentile = $input.all().filter(i => i.json.score >= p95);
```

---

## Pattern 14: Cross-Iteration Data Accumulation (SplitInBatches)

**Use case**: A SplitInBatches loop that needs to aggregate results from every batch, not just the last one.

**The trap**: After a SplitInBatches loop, `$('Node Inside Loop').all()` returns **only the last iteration's items**, not the cumulative set. This silently drops data from every batch except the final one. The fix is workflow static data.

**SplitInBatches loop semantics** (mandatory background):

- `main[0]` = **done**: fires once after all batches are processed
- `main[1]` = **each batch**: fires for every batch (this is the loop body)

Always add a **Limit 1** node downstream of the **done** output as a safety net.

### Three-stage pattern

```javascript
// Stage 1: BEFORE the loop (reset accumulator)
const staticData = $getWorkflowStaticData('global');
staticData.results = [];
return $input.all();
```

```javascript
// Stage 2: INSIDE the loop body (accumulate)
const staticData = $getWorkflowStaticData('global');
const results = [];

for (const item of $input.all()) {
  const processed = {
    /* per-item transform */
  };
  results.push({ json: processed });
  staticData.results.push(processed);
}

return results;
```

```javascript
// Stage 3: AFTER the loop, on the "done" output (read accumulated data)
const staticData = $getWorkflowStaticData('global');
const allResults = staticData.results || [];
// Now aggregate across ALL iterations
return [{ json: { allResults, total: allResults.length } }];
```

### Float precision when comparing prices

Floating-point noise causes false positives when comparing currency. Round to cents:

```javascript
// Unreliable
if (newPrice !== oldPrice) { /* false positive risk */ }

// Reliable: compare at cent level
if (Math.round(newPrice * 100) !== Math.round(oldPrice * 100)) {
  // Real price change
}
```

---

## Pattern 15: `pairedItem` for New Output Items

**Use case**: A Code node creates new items that don't map 1:1 to input items. Without `pairedItem`, downstream Set / Edit Fields nodes throw `paired_item_no_info`.

```javascript
const results = [];
for (let i = 0; i < $input.all().length; i++) {
  const item = $input.all()[i];
  results.push({
    json: { /* new data */ },
    pairedItem: { item: i }
  });
}
return results;
```

When generating items unrelated to input rows (for example, splitting one input into many outputs), set `pairedItem: { item: <source-index> }` on each output. n8n uses this to resolve `$('UpstreamNode').item.json.field` expressions in downstream nodes.

---

## Pattern 16: HTTP Calls via `$helpers.httpRequest`

**Use case**: Calling an unauthenticated HTTP endpoint from inside the Code node, or using a token that arrived as runtime data.

**Reminder**: For authenticated APIs, prefer an **HTTP Request node with a credential attached**. `$helpers.httpRequestWithAuthentication` is blocked in the task runner sandbox. See [gotchas.md](./gotchas.md) Error #6.

```javascript
// Simple GET
const response = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/data',
  qs: { page: 1, limit: 50 }
});
return [{ json: { data: response } }];
```

### Error-safe POST with full response inspection

```javascript
try {
  const response = await $helpers.httpRequest({
    method: 'POST',
    url: 'https://api.example.com/users',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${$('Get Token').first().json.access_token}`
    },
    body: { name: 'Alice', email: 'alice@example.com' },
    simple: false,
    resolveWithFullResponse: true
  });

  if (response.statusCode >= 200 && response.statusCode < 300) {
    return [{ json: { success: true, data: response.body, rateLimit: response.headers['x-ratelimit-remaining'] } }];
  }
  return [{ json: { success: false, status: response.statusCode, error: response.body } }];
} catch (err) {
  return [{ json: { success: false, error: err.message } }];
}
```

### Sub-workflow delegation (the canonical pattern for auth)

When you need to do code-level logic around an authenticated call, the **sub-workflow** pattern is the supported way:

```javascript
// Parent Code node: prepare payloads, then delegate
return $input.all().map(i => ({
  json: {
    url:    'https://api.example.com/things',
    method: 'POST',
    body:   { sku: i.json.sku }
  }
}));
```

Wire to **Execute Workflow** → child workflow with **Execute Workflow Trigger** → **HTTP Request** node using `={{ $json.url }}`, `={{ $json.body }}`, with the credential attached natively.

---

## Combining Patterns

Real workflows compose patterns. Example: multi-source aggregation, top-N filtering, then string-aggregation report.

```javascript
const allItems = $input.all();
const aggregated = [];

// Pattern 1: aggregate from different sources
for (const item of allItems) {
  // ... source-specific parsing
  aggregated.push(normalizedItem);
}

// Pattern 13: top 10 by score
const top10 = aggregated
  .sort((a, b) => b.score - a.score)
  .slice(0, 10);

// Pattern 7: generate report
const report = `Top 10 Items:\n\n${top10.map((it, i) => `${i + 1}. ${it.title} (${it.score})`).join('\n')}`;

return [{ json: { report, items: top10 } }];
```

---

## Pattern Selection Cheat Sheet

| Goal | Pattern |
|------|---------|
| Combine multiple API responses | 1: Multi-source aggregation |
| Filter then transform a batch | 2: Active items / basic batch |
| Group items by a field | 3: Group by category |
| Drop duplicates by id | 4: Deduplicate |
| Extract keywords / mentions / emails | 5: Regex filtering |
| Parse markdown / HTML / YAML | 6: Markdown parsing |
| Generate a text or HTML report | 7: String aggregation |
| Detect changes / validate schema | 8: JSON comparison |
| Prepare form data for CRM | 9: CRM transformation |
| Add computed fields (rank, pct, age) | 10: Array transformation with context |
| Process GitHub releases | 11: Release processing |
| Format a Slack message | 12: Block Kit |
| Get top results | 13: Top N filtering |
| Accumulate inside a SplitInBatches loop | 14: Cross-iteration accumulation |
| Emit items that don't map 1:1 to input | 15: `pairedItem` |
| Hit an HTTP endpoint from inside code | 16: `$helpers.httpRequest` |

---

## See Also

- [README.md](./README.md), [api.md](./api.md), [gotchas.md](./gotchas.md), [configuration.md](./configuration.md) (this topic)
- [../code-python/](../code-python/) for equivalent patterns in Python
- [../expressions/](../expressions/) for `{{ }}` patterns used in other nodes
- [../workflow-patterns/](../workflow-patterns/) for SplitInBatches loop, sub-workflow delegation, and error-handling patterns at the workflow level
- [../node-configuration/](../node-configuration/) for HTTP Request node, Set node, and Execute Workflow node configuration
