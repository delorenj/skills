# Scheduled Tasks Pattern

Cross-refs: see [patterns.md](./patterns.md) for batch processing and error handling; see [gotchas.md](./gotchas.md) for timezone, overlap, and activation traps; see [configuration.md](./configuration.md) for cron syntax.

**Use Case**: Recurring automation workflows that run automatically on a schedule.

## Pattern Structure

```
Schedule Trigger → [Fetch Data] → [Process] → [Deliver] → [Log/Notify]
```

**Key Characteristic**: Time-based automated execution.

## Use Cases

- Daily / weekly reports.
- Data synchronization on a timer.
- Monitoring and uptime checks.
- Cleanup and maintenance jobs.
- Data enrichment passes.
- Backup automation.
- Content publishing on a calendar.

## Core Components

### 1. Schedule Trigger

Execute workflow at specified times. Modes:

- **Interval**: every X minutes / hours / days.
- **Cron**: specific times (advanced).
- **Days & Hours**: simple recurring schedule.

See [configuration.md](./configuration.md) for full syntax.

### 2. Data Source

Common sources:

- HTTP Request (APIs)
- Database queries
- File reads
- Service-specific nodes

### 3. Processing

Typical operations:

- Filter / transform data.
- Aggregate statistics.
- Generate reports.
- Check conditions.

### 4. Delivery

Output channels:

- Email
- Slack / Discord / Microsoft Teams
- File storage
- Database writes

### 5. Logging

Methods:

- Database log entries.
- File append.
- External monitoring service (Datadog, Prometheus).

## Variants

### Variant: Daily Sales Report

```
1. Schedule (daily at 9 AM)

2. Postgres (query yesterday's sales)
   SELECT date, SUM(amount) AS total, COUNT(*) AS orders
   FROM orders
   WHERE date = CURRENT_DATE - INTERVAL '1 day'
   GROUP BY date

3. Code (calculate metrics)
   - Total revenue
   - Order count
   - Average order value
   - Comparison to previous day

4. Set (format email body)

5. Email (send to team@company.com)

6. Slack (post summary to #sales)
```

### Variant: CRM to Warehouse Sync

```
1. Schedule (every hour)

2. Set (store last sync time)
   SELECT MAX(synced_at) FROM sync_log

3. HTTP Request (fetch new CRM contacts since last sync)
   GET /api/contacts?updated_since={{$json.last_sync}}

4. IF (records exist)

5. Set (transform CRM schema to warehouse schema)

6. Postgres (warehouse INSERT)

7. Postgres (UPDATE sync_log SET synced_at = NOW())

8. IF (error occurred)
   → Slack (#data-team)
```

### Variant: Uptime Monitor

```
1. Schedule (every 5 minutes)

2. HTTP Request (GET https://example.com/health)
   - timeout: 10 seconds
   - continueOnFail: true

3. IF (status !== 200 OR response_time > 2000ms)

4. Redis (check alert cooldown)
   - Key: alert:website_down
   - TTL: 30 minutes

5. IF (no recent alert sent)

6. [Alert actions]
   - Slack (#ops-team)
   - PagerDuty (create incident)
   - Email (alert@company.com)
   - Redis (set alert cooldown)

7. Postgres (log uptime check)
```

### Variant: Database Cleanup

```
1. Schedule (weekly Sunday 2 AM)

2. Postgres (find old records)
   SELECT * FROM logs
   WHERE created_at < NOW() - INTERVAL '90 days'
   LIMIT 10000

3. IF (records exist)

4. Code (export to JSON archive)

5. Google Drive (upload archive)
   - Filename: logs_archive_{{$now.format('YYYY-MM-DD')}}.json

6. Postgres (DELETE archived rows by id)

7. Slack ("Archived X, deleted Y")
```

### Variant: Nightly Contact Enrichment

```
1. Schedule (nightly 3 AM)

2. Postgres (contacts without company data)
   SELECT id, email, domain FROM contacts
   WHERE company_name IS NULL
     AND created_at > NOW() - INTERVAL '7 days'
   LIMIT 100

3. Split In Batches (10 contacts per batch)

4. HTTP Request (Clearbit per domain)
   - Wait 1 second between batches

5. Set (map response to schema)

6. Postgres (UPDATE contacts)

7. Wait (1 second)

8. Loop (back to step 4)

9. Email ("Enriched X contacts")
```

### Variant: Database Backup

```
1. Schedule (daily 2 AM)

2. Code (pg_dump)
   const { exec } = require('child_process');
   exec('pg_dump -h db.example.com mydb > backup.sql')

3. Code (compress)
   const zlib = require('zlib');

4. AWS S3 (upload backup-{{$now.format('YYYY-MM-DD')}}.sql.gz)

5. AWS S3 (list old backups; keep last 30 days)

6. AWS S3 (delete old backups)

7. IF (error)
   - PagerDuty (critical alert)
   - Email (failure)
   ELSE
   - Slack (#devops, "Backup completed")
```

### Variant: Automated Social Media Posts

```
1. Schedule (every 3 hours during business hours)
   Cron: 0 9,12,15,18 * * 1-5

2. Google Sheets (read content queue)
   Filter: status=pending AND publish_time <= NOW()

3. IF (posts available)

4. HTTP Request (shorten URLs)

5. HTTP Request (POST to Twitter API)

6. HTTP Request (POST to LinkedIn API)

7. Google Sheets (update status=published)

8. Slack (#marketing, "Posted: {{$json.title}}")
```

## Schedule Configuration

See [configuration.md](./configuration.md) for full syntax. Summary:

```javascript
// Interval
{ mode: "interval", interval: 15, unit: "minutes" }

// Days & Hours
{ mode: "daysAndHours", days: ["monday", "tuesday"], hour: 9, minute: 0 }

// Cron
{ mode: "cron", expression: "0 9 * * 1-5" }
```

## Timezone Considerations

Set workflow timezone explicitly:

```javascript
// Workflow settings
{ timezone: "America/New_York" }
```

Daylight saving: setting an IANA timezone (not UTC) makes the schedule DST-aware. 9 AM in `America/New_York` is 9 AM both in EST and EDT.

```javascript
// ❌ BAD: UTC schedule for "9 AM local" drifts during DST
// ✅ GOOD: set workflow timezone
{
  timezone: "America/New_York",
  schedule: { mode: "daysAndHours", hour: 9 }
}
```

## Error Handling

### Pattern 1: Error Trigger Workflow

Main:

```
Schedule → Fetch → Process → Deliver
```

Error:

```
Error Trigger (for main workflow)
  → Set (extract error details)
  → Slack (#ops-team)
  → Email (admin alert)
  → Postgres (log error)
```

### Pattern 2: Retry with Backoff

```
Schedule → HTTP Request (continueOnFail: true)
  → IF (error)
    → Wait (5 minutes)
    → HTTP Request (retry 1)
    → IF (still error)
      → Wait (15 minutes)
      → HTTP Request (retry 2)
      → IF (still error)
        → Alert admin
```

### Pattern 3: Partial Failure Handling

```
Schedule → Split In Batches
  → Process (continueOnFail: true)
  → Code (track successes and failures)
  → Report: "Processed: 95/100, Failed: 5/100"
```

## Performance Optimization

### Batch Processing

```
Schedule → Query (LIMIT 10000)
  → Split In Batches (100)
  → Process batch
  → Loop
```

### Parallel Processing

```
Schedule
  → [Branch 1: Update DB]
  → [Branch 2: Send emails]
  → [Branch 3: Generate report]
  → Merge → Final notification
```

### Skip if Already Running (Execution Lock)

```
Schedule → Redis (check lock)
  → IF (lock exists) → End
  → ELSE
    → Redis (set lock, TTL 30 min)
    → [Execute workflow]
    → Redis (delete lock)
```

### Early Exit on No Data

```
Schedule → Query (check if work exists)
  → IF (no results) → End
  → ELSE → Process data
```

## Monitoring and Logging

### Execution Log Table

```sql
CREATE TABLE workflow_executions (
  id SERIAL PRIMARY KEY,
  workflow_name VARCHAR(255),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status VARCHAR(50),
  records_processed INT,
  error_message TEXT
);
```

```
Schedule
  → Set (record start)
  → [Workflow logic]
  → Postgres (INSERT execution log)
```

### Metrics Collection

```
Schedule → [Execute]
  → Code (calculate metrics: duration, records processed, success rate)
  → HTTP Request (send to Datadog / Prometheus)
```

### Summary Notifications

```
Schedule (daily 6 PM) → Query execution logs
  → Code (aggregate today's executions)
  → Email summary:
    "Today's Workflow Executions:
     - 24/24 successful
     - 0 failures
     - Avg duration: 2.3 min"
```

## Testing Scheduled Workflows

1. Use a Manual Trigger during development; swap for Schedule Trigger before deploy.
2. Test with different simulated times via a Set node injecting `currentTime`.
3. Use a dry-run flag and an IF that branches between log-only and execute-real modes.
4. Use a shorter interval for testing (every 1 minute), then switch to production cadence.

## Advanced Patterns

### Dynamic Scheduling

Change behavior based on conditions inside an hourly trigger:

```
Schedule (hourly) → Code (check if it's time to run)
  → IF (business hours AND weekday)
    → Execute workflow
  → ELSE
    → Skip
```

### Dependent Schedules

Chain workflows:

```
Workflow A (daily 2 AM): Data sync
  → On completion → Trigger Workflow B

Workflow B: Generate report (depends on fresh data)
```

### Conditional Execution

```
Schedule → HTTP Request (check feature flag)
  → IF (feature enabled) → Execute
  → ELSE → Skip
```

## Complete Worked Example: Hourly Health-Check Monitor with Cooldown

```
1. Schedule Trigger
   - mode: cron
   - expression: "*/5 * * * *"      (every 5 minutes)
   - timezone: UTC

2. HTTP Request
   - method: GET
   - url: https://example.com/health
   - timeout: 10000
   - continueOnFail: true

3. Code (evaluate health)
   - down = $json.error || $json.statusCode !== 200 || $json.responseTime > 2000

4. IF (down === true)

5. Redis (GET alert:website_down)
   - returns null if no cooldown

6. IF (cooldown null)

7. [Parallel alert fan-out]
   - Slack (#ops-team, alert)
   - PagerDuty (create incident, severity high)
   - Email (oncall@company.com)
   - Redis (SET alert:website_down 1 EX 1800)

8. Postgres
   - INSERT INTO uptime_checks (checked_at, status, response_time_ms, error)

Error workflow:
  Error Trigger → Slack (#ops-platform, "monitor itself broke")
```

## Workflow Checklist

**Planning**
- Define schedule frequency (interval, cron, days and hours).
- Set workflow timezone explicitly.
- Estimate execution duration.
- Plan for failures and retries.
- Consider DST.

**Implementation**
- Configure Schedule Trigger.
- Set workflow timezone in settings.
- Add early exit for no-op cases.
- Implement batch processing for large data.
- Add execution logging.

**Error Handling**
- Create an Error Trigger workflow.
- Implement retry logic.
- Add alert notifications.
- Log errors for analysis.
- Handle partial failures.

**Monitoring**
- Log each execution.
- Track metrics (duration, records, success rate).
- Set up daily / weekly summaries.
- Alert on consecutive failures.
- Monitor resource usage.

**Testing**
- Test with Manual Trigger first.
- Verify timezone behavior.
- Test error scenarios.
- Check for overlapping executions.
- Validate output quality.

**Deployment**
- Document workflow purpose.
- Set up monitoring.
- Configure alerts.
- Activate the workflow in the n8n UI. **Manual activation required** (API / MCP cannot activate).
- Test in production (short interval first).
- Monitor first executions.

## See Also

- [patterns.md](./patterns.md) for batch processing, retries, idempotency.
- [gotchas.md](./gotchas.md) for timezone, overlapping execution, and activation traps.
- [configuration.md](./configuration.md) for cron expression details and trigger modes.
- [http-api-integration.md](./http-api-integration.md) for periodic API fetches.
- [database-operations.md](./database-operations.md) for scheduled database tasks.
- [webhook-processing.md](./webhook-processing.md) for an alternative event-driven model.
