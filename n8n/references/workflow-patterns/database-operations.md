# Database Operations Pattern

Cross-refs: see [patterns.md](./patterns.md) for batch processing and idempotency; see [gotchas.md](./gotchas.md) for SQL injection, unbounded queries, and transaction traps.

**Use Case**: Read, write, sync, and manage database data in workflows.

## Pattern Structure

```
Trigger → [Query/Read] → [Transform] → [Write/Update] → [Verify/Log]
```

**Key Characteristic**: Data persistence and synchronization.

## Use Cases

- Cross-database synchronization (Postgres to MySQL, etc.).
- ETL pipelines combining multiple sources into a warehouse.
- Data validation and cleanup.
- Backup and archive jobs.
- Real-time writes driven by webhook events.

## Core Components

### 1. Trigger

- **Schedule**: periodic sync or maintenance (most common).
- **Webhook**: event-driven writes.
- **Manual**: one-time operations.

### 2. Database Read Nodes

Supported databases:

- Postgres
- MySQL
- MongoDB
- Microsoft SQL
- SQLite
- Redis
- Community nodes for others

### 3. Transform

- **Set**: field mapping.
- **Code**: complex transformations.
- **Merge**: combine data from multiple sources.

### 4. Database Write Nodes

Operations:

- INSERT: create new records.
- UPDATE: modify existing records.
- UPSERT: insert or update.
- DELETE: remove records.

### 5. Verification

- Query to verify records.
- Count rows affected.
- Log results.

## Variants

### Variant: Data Synchronization (Postgres to MySQL)

```
1. Schedule (every 15 minutes)
2. Postgres (SELECT * FROM users WHERE updated_at > {{$json.last_sync}})
3. IF (records exist)
4. Set (map Postgres schema to MySQL schema)
5. MySQL (INSERT or UPDATE users)
6. Postgres (UPDATE sync_log SET last_sync = NOW())
7. Slack (notify: "Synced X users")
```

Incremental sync query:

```sql
SELECT *
FROM users
WHERE updated_at > $1
ORDER BY updated_at ASC
LIMIT 1000
```

Parameters:

```javascript
{ "parameters": ["={{$node['Get Last Sync'].json.last_sync}}"] }
```

### Variant: ETL Pipeline

```
1. Schedule (daily at 2 AM)
2. [Parallel branches]
   - Postgres (SELECT orders)
   - MySQL (SELECT customers)
   - MongoDB (SELECT products)
3. Merge (combine all data)
4. Code (transform to warehouse schema)
5. Postgres (warehouse - INSERT into fact_sales)
6. Email (summary report)
```

### Variant: Validation and Cleanup

```
1. Schedule (weekly)
2. Postgres (SELECT users WHERE email IS NULL OR email = '')
3. IF (invalid records exist)
4. Postgres (UPDATE users SET status='inactive' WHERE email IS NULL)
5. Postgres (DELETE inactive users older than 1 year)
6. Slack (alert: "Cleaned X invalid records")
```

### Variant: Backup and Archive

```
1. Schedule (monthly)
2. Postgres (SELECT * FROM orders WHERE created_at < NOW() - INTERVAL '2 years')
3. Code (convert to JSON)
4. Write File (save archive.json)
5. Google Drive (upload archive)
6. Postgres (DELETE archived rows)
```

### Variant: Real-Time Update

```
1. Webhook (receive status update)
2. Postgres (UPDATE users SET status = {{$json.body.status}} WHERE id = {{$json.body.user_id}})
3. IF (rows affected > 0)
4. Redis (SET user:{{$json.body.user_id}}:status {{$json.body.status}})
5. Respond to Webhook ({"success": true})
```

## Database Node Configuration

### Postgres

#### SELECT

```javascript
{
  operation: "executeQuery",
  query: "SELECT id, name, email FROM users WHERE created_at > $1 LIMIT $2",
  parameters: ["={{$json.since_date}}", "100"]
}
```

#### INSERT

```javascript
{
  operation: "insert",
  table: "users",
  columns: "id, name, email, created_at",
  values: [{
    id: "={{$json.id}}",
    name: "={{$json.name}}",
    email: "={{$json.email}}",
    created_at: "={{$now}}"
  }]
}
```

#### UPDATE

```javascript
{
  operation: "update",
  table: "users",
  updateKey: "id",
  columns: "name, email, updated_at",
  values: {
    id: "={{$json.id}}",
    name: "={{$json.name}}",
    email: "={{$json.email}}",
    updated_at: "={{$now}}"
  }
}
```

#### UPSERT

```javascript
{
  operation: "executeQuery",
  query: `
    INSERT INTO users (id, name, email)
    VALUES ($1, $2, $3)
    ON CONFLICT (id)
    DO UPDATE SET name = $2, email = $3, updated_at = NOW()
  `,
  parameters: ["={{$json.id}}", "={{$json.name}}", "={{$json.email}}"]
}
```

### MySQL

#### SELECT with JOIN

```javascript
{
  operation: "executeQuery",
  query: `
    SELECT u.id, u.name, o.order_id, o.total
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.created_at > ?
  `,
  parameters: ["={{$json.since_date}}"]
}
```

#### Bulk INSERT

```javascript
{
  operation: "insert",
  table: "orders",
  columns: "user_id, total, status",
  values: $json.orders
}
```

### MongoDB

#### Find

```javascript
{
  operation: "find",
  collection: "users",
  query: JSON.stringify({
    created_at: { $gt: new Date($json.since_date) },
    status: "active"
  }),
  limit: 100
}
```

#### Insert

```javascript
{
  operation: "insert",
  collection: "users",
  document: JSON.stringify({
    name: $json.name,
    email: $json.email,
    created_at: new Date()
  })
}
```

#### Update

```javascript
{
  operation: "update",
  collection: "users",
  query: JSON.stringify({ _id: $json.user_id }),
  update: JSON.stringify({
    $set: { status: $json.status, updated_at: new Date() }
  })
}
```

## Batch Processing

### SplitInBatches

```
Postgres (SELECT 10000 records)
  → Split In Batches (100 items per batch)
  → Transform
  → MySQL (write batch)
  → Loop
```

### Paginated Queries (Offset)

```
Set (initialize: offset=0, limit=1000)
  → Loop Start
  → Postgres (SELECT * FROM large_table LIMIT {{$json.limit}} OFFSET {{$json.offset}})
  → IF (records returned)
    → Process records
    → Set (offset += 1000)
    → Loop back
  → [No records] → End
```

```sql
SELECT * FROM large_table
ORDER BY id
LIMIT $1 OFFSET $2
```

### Cursor-Based Pagination (Better)

```
Set (initialize: last_id=0)
  → Loop Start
  → Postgres (SELECT * FROM table WHERE id > {{$json.last_id}} ORDER BY id LIMIT 1000)
  → IF (records returned)
    → Process records
    → Code (get max id from batch)
    → Loop back
  → [No records] → End
```

```sql
SELECT * FROM table
WHERE id > $1
ORDER BY id ASC
LIMIT 1000
```

## Transaction Handling

### BEGIN / COMMIT / ROLLBACK

```javascript
// Node 1
{ operation: "executeQuery", query: "BEGIN" }

// Nodes 2..N
{ operation: "executeQuery", query: "INSERT INTO ...", continueOnFail: true }

// Node N+1
{
  operation: "executeQuery",
  query: "={{$node['Operation'].json.error ? 'ROLLBACK' : 'COMMIT'}}"
}
```

### Atomic UPSERT

```sql
INSERT INTO inventory (product_id, quantity)
VALUES ($1, $2)
ON CONFLICT (product_id)
DO UPDATE SET quantity = inventory.quantity + $2
```

### Error Rollback via Error Trigger

```
Try operations:
  Postgres (INSERT orders)
  MySQL (INSERT order_items)

Error Trigger:
  Postgres (DELETE FROM orders WHERE id = {{$json.order_id}})
  MySQL (DELETE FROM order_items WHERE order_id = {{$json.order_id}})
```

## Data Transformation

### Schema Mapping

```javascript
// Code node
const sourceData = $input.all();
return sourceData.map(item => ({
  json: {
    user_id: item.json.id,
    full_name: `${item.json.first_name} ${item.json.last_name}`,
    email_address: item.json.email,
    registration_date: new Date(item.json.created_at).toISOString(),
    is_premium: item.json.plan_type === 'pro',
    status: item.json.status || 'active'
  }
}));
```

### Data Type Conversions

```javascript
return $input.all().map(item => ({
  json: {
    user_id: parseInt(item.json.user_id),
    created_at: new Date(item.json.created_at),
    is_active: item.json.active === 1,
    metadata: JSON.parse(item.json.metadata || '{}'),
    email: item.json.email || null
  }
}));
```

### Aggregation

```javascript
const items = $input.all();
const summary = items.reduce((acc, item) => {
  const date = item.json.created_at.split('T')[0];
  if (!acc[date]) acc[date] = { count: 0, total: 0 };
  acc[date].count++;
  acc[date].total += item.json.amount;
  return acc;
}, {});

return Object.entries(summary).map(([date, data]) => ({
  json: {
    date,
    count: data.count,
    total: data.total,
    average: data.total / data.count
  }
}));
```

## Performance Optimization

### Use Indexes

```sql
CREATE INDEX idx_users_updated_at ON users(updated_at);
CREATE INDEX idx_orders_user_id ON orders(user_id);
```

### Always LIMIT

```sql
-- ✅ GOOD
SELECT * FROM large_table WHERE created_at > $1 LIMIT 1000

-- ❌ BAD (unbounded)
SELECT * FROM large_table WHERE created_at > $1
```

### Prepared Statements

```javascript
// ✅ GOOD
{ query: "SELECT * FROM users WHERE id = $1", parameters: ["={{$json.id}}"] }

// ❌ BAD
{ query: "SELECT * FROM users WHERE id = '={{$json.id}}'" }
```

### Batch Writes

```javascript
// ✅ GOOD: one INSERT, 100 rows
{ operation: "insert", table: "orders", values: $json.items }

// ❌ BAD: 100 separate INSERT statements
```

### Connection Pooling

```javascript
{
  host: "db.example.com",
  database: "mydb",
  user: "user",
  password: "pass",
  min: 2,
  max: 10,
  idleTimeoutMillis: 30000
}
```

## Error Handling

### Check Rows Affected

```
Database Operation (UPDATE users...)
  → IF ({{$json.rowsAffected === 0}})
    → Alert: "No rows updated, record not found"
```

### Constraint Violations

```javascript
{ operation: "insert", continueOnFail: true }
```

```
IF ({{$json.error !== undefined}})
  → IF ({{$json.error.includes('duplicate key')}})
    → Log: "Record already exists, skipping"
  → ELSE
    → Alert: "Database error: {{$json.error}}"
```

### Rollback on Error (Error Trigger)

```
Try operations:
  → Database Write 1
  → Database Write 2
  → Database Write 3

Error Trigger:
  → Rollback Operations
  → Alert Admin
```

## Security Best Practices

### Parameterized Queries (SQL Injection Prevention)

```javascript
// ✅ SAFE
{ query: "SELECT * FROM users WHERE email = $1", parameters: ["={{$json.email}}"] }

// ❌ DANGEROUS
{ query: "SELECT * FROM users WHERE email = '={{$json.email}}'" }
```

### Least Privilege Access

```sql
-- ✅ GOOD
CREATE USER n8n_workflow WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON orders TO n8n_workflow;
GRANT SELECT ON users TO n8n_workflow;

-- ❌ BAD
GRANT ALL PRIVILEGES TO n8n_workflow;
```

### Input Validation

```javascript
const email = $json.email;
const name = $json.name;

if (!email || !email.includes('@')) throw new Error('Invalid email');
if (!name || name.length < 2)        throw new Error('Invalid name');

return [{ json: { email: email.toLowerCase().trim(), name: name.trim() } }];
```

### Encrypt Sensitive Data

```javascript
const crypto = require('crypto');
const algorithm = 'aes-256-cbc';
const key = Buffer.from($credentials.encryptionKey, 'hex');
const iv = crypto.randomBytes(16);

const cipher = crypto.createCipheriv(algorithm, key, iv);
let encrypted = cipher.update($json.sensitive_data, 'utf8', 'hex');
encrypted += cipher.final('hex');

return [{ json: { encrypted_data: encrypted, iv: iv.toString('hex') } }];
```

## Complete Worked Example: Hourly Postgres-to-MySQL User Sync

```
1. Schedule Trigger
   - mode: interval
   - interval: 1
   - unit: hours
   - timezone: UTC

2. Postgres (Get Last Sync)
   - operation: executeQuery
   - query: SELECT MAX(synced_at) AS last_sync FROM sync_log WHERE source='users'

3. Postgres (Read Source)
   - operation: executeQuery
   - query: SELECT id, name, email, updated_at FROM users WHERE updated_at > $1 ORDER BY updated_at ASC LIMIT 1000
   - parameters: ["={{$node['Get Last Sync'].json.last_sync}}"]

4. IF (records returned)
   - True branch continues
   - False branch → end (no-op)

5. SplitInBatches (100 items per batch)

6. Code (map schema)
   - source.id     → target.user_id
   - source.name   → target.full_name
   - source.email  → target.email_address
   - lowercase, trim, validate

7. MySQL (Bulk Upsert)
   - executeQuery with INSERT ... ON DUPLICATE KEY UPDATE
   - continueOnFail: true

8. IF ({{$json.error}} is empty)
   - True → continue
   - False → Error Trigger workflow

9. (Loop back to SplitInBatches main[1])

10. SplitInBatches main[0] → Limit 1 → Postgres (Update Sync Log)
    - INSERT INTO sync_log (source, synced_at) VALUES ('users', NOW())

11. Slack (#data-team)
    - "User sync complete: {{$json.total}} records"

Error workflow:
  Error Trigger
    → Slack (#alerts)
    → Postgres (INSERT INTO workflow_errors ...)
```

## Workflow Checklist

**Planning**
- Identify source and target databases.
- Understand schema differences.
- Plan transformation logic.
- Consider batch size for large datasets.
- Design error handling strategy.

**Implementation**
- Use parameterized queries (never concatenate).
- Add LIMIT to all SELECT queries.
- Use appropriate operation (INSERT / UPDATE / UPSERT).
- Configure credentials properly.
- Test with a small dataset first.

**Performance**
- Add database indexes for query columns.
- Use batch operations.
- Implement pagination for large datasets.
- Configure connection pooling.
- Monitor query execution times.

**Security**
- Parameterized queries (SQL injection prevention).
- Least-privilege database user.
- Validate and sanitize input.
- Encrypt sensitive data.
- Never log sensitive data.

**Reliability**
- Add transaction handling if needed.
- Check rows affected.
- Handle constraint violations.
- Implement retry logic.
- Add an Error Trigger workflow.

## See Also

- [patterns.md](./patterns.md) for batch processing, idempotency, and retries.
- [gotchas.md](./gotchas.md) for SQL injection, unbounded query, and transaction failure modes.
- [configuration.md](./configuration.md) for database credentials and connection pooling.
- [http-api-integration.md](./http-api-integration.md) for fetching data to store in DB.
- [scheduled-tasks.md](./scheduled-tasks.md) for periodic database maintenance.
- [../code-javascript/](../code-javascript/) for accumulator patterns when looping.
