---
pipeline-status:
  - new
---
# Silent Failure Detection Patterns

**Problem**: Process managers, task runners, and build tools often return success exit codes even when the underlying operation failed.

**Impact**: Workflows proceed with broken builds, corrupted artifacts, or failed services, leading to:
- False positives in CI/CD
- Runtime failures in production
- Wasted debugging time
- Cascading failures in subsequent steps

---

## Common Silent Failures

### 1. Mise Task Runner

**Problem**: `mise start` returns 0 even when Rust compilation fails

**Behavior**:
```bash
$ mise start
✓ Task completed  # <-- LIE! Compilation failed
$ echo $?
0  # <-- Success exit code despite failure
```

**Solution**: Monitor logs for explicit success indicator

```bash
# Start in background
mise start > /tmp/backend.log 2>&1 &

# Wait for success pattern
timeout=30
elapsed=0

while [[ $elapsed -lt $timeout ]]; do
  # Look for service-specific success message
  if grep -q "Accepted new IPC connection" /tmp/backend.log; then
    echo "✓ Service started successfully"
    exit 0
  fi

  # Check for error patterns
  if grep -qi "error|compilation failed|panic" /tmp/backend.log; then
    echo "✗ Service failed to start"
    cat /tmp/backend.log
    exit 1
  fi

  sleep 1
  elapsed=$((elapsed + 1))
done

# Timeout = failure
echo "✗ Service startup timed out"
cat /tmp/backend.log
exit 1
```

### 2. Webpack/Vite Builds

**Problem**: Build tool exits 0 but generates incomplete artifacts

**Behavior**:
```bash
$ npm run build
✓ Build completed  # <-- Output exists but broken
$ echo $?
0
$ node dist/app.js
ReferenceError: module not found  # <-- Runtime failure
```

**Solution**: Validate artifact contents after build

```bash
# Run build
npm run build

# Verify required files exist
required_files=(
  "dist/index.html"
  "dist/assets/index-*.js"
  "dist/assets/index-*.css"
)

for file in "${required_files[@]}"; do
  # Use glob matching for hashed filenames
  if ! ls $file 2>/dev/null 1>&2; then
    echo "✗ Required file missing: $file"
    exit 1
  fi
done

# Verify JS isn't empty or malformed
js_file=$(ls dist/assets/index-*.js | head -1)
js_size=$(wc -c < "$js_file")

if [[ $js_size -lt 1000 ]]; then
  echo "✗ JS bundle suspiciously small: ${js_size} bytes"
  cat "$js_file"
  exit 1
fi

# Check for common error markers in output
if grep -q "Uncaught|ReferenceError|Cannot find module" "$js_file"; then
  echo "✗ Build output contains runtime errors"
  grep -A 5 "Uncaught|ReferenceError|Cannot find module" "$js_file"
  exit 1
fi

echo "✓ Build artifacts validated"
```

### 3. Docker Compose

**Problem**: `docker-compose up` returns success even when services crash

**Behavior**:
```bash
$ docker-compose up -d
✓ Started  # <-- Container started but immediately crashed
$ echo $?
0
$ docker-compose ps
NAME    STATUS
db      Restarting (1) Less than a second ago  # <-- Crash loop
```

**Solution**: Wait for service health checks

```bash
# Start services
docker-compose up -d

# Wait for healthy status
timeout=60
elapsed=0

while [[ $elapsed -lt $timeout ]]; do
  # Check all services are healthy
  unhealthy=$(docker-compose ps --format json | jq -r '. | select(.Health != "healthy") | .Name' | wc -l)

  if [[ $unhealthy -eq 0 ]]; then
    echo "✓ All services healthy"
    exit 0
  fi

  # Check for crash loops
  restarting=$(docker-compose ps --format json | jq -r '. | select(.State == "restarting") | .Name')
  if [[ -n "$restarting" ]]; then
    echo "✗ Services in crash loop: $restarting"
    docker-compose logs "$restarting"
    exit 1
  fi

  sleep 2
  elapsed=$((elapsed + 2))
done

echo "✗ Services failed to become healthy within ${timeout}s"
docker-compose ps
exit 1
```

### 4. Database Migrations

**Problem**: Migration tool returns success but migrations didn't apply

**Behavior**:
```bash
$ migrate up
Applying migrations...  # <-- Pretends to work
$ echo $?
0
$ psql -c "SELECT COUNT(*) FROM users;"
ERROR:  relation "users" does not exist  # <-- Migration didn't run
```

**Solution**: Verify schema changes were applied

```bash
# Run migrations
migrate up

# Verify specific tables exist
required_tables=("users" "sessions" "posts")

for table in "${required_tables[@]}"; do
  if ! psql -d mydb -tAc "SELECT to_regclass('public.$table');" | grep -q "public.$table"; then
    echo "✗ Migration failed: table '$table' doesn't exist"
    psql -d mydb -c "\dt"  # Show what tables DO exist
    exit 1
  fi
done

# Verify schema version
current_version=$(psql -d mydb -tAc "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;")
expected_version=$(ls migrations/*.sql | sort -V | tail -1 | grep -oP '\d+')

if [[ "$current_version" != "$expected_version" ]]; then
  echo "✗ Migration version mismatch: current=$current_version, expected=$expected_version"
  exit 1
fi

echo "✓ Migrations applied successfully"
```

### 5. Test Runners

**Problem**: Test runner exits 0 despite test failures

**Behavior**:
```bash
$ npm test
Running tests...  # <-- Tests failing but exit code still 0
Test suite: 10 passed, 5 failed
$ echo $?
0  # <-- Success despite failures
```

**Solution**: Parse test output for failure markers

```bash
# Run tests and capture output
test_output=$(npm test 2>&1)
test_exit=$?

echo "$test_output"

# Check exit code first
if [[ $test_exit -ne 0 ]]; then
  echo "✗ Tests failed with exit code $test_exit"
  exit 1
fi

# Check for failure keywords in output (belt and suspenders)
if echo "$test_output" | grep -qiE "failed|error|FAIL|✗"; then
  echo "✗ Tests reported failures despite exit code 0"
  echo "$test_output" | grep -iE "failed|error|FAIL|✗"
  exit 1
fi

# Verify minimum test count
test_count=$(echo "$test_output" | grep -oP '\d+ passed' | grep -oP '\d+')
if [[ $test_count -lt 10 ]]; then
  echo "✗ Suspiciously low test count: $test_count (expected ≥10)"
  exit 1
fi

echo "✓ All tests passed"
```

---

## General Patterns

### Pattern 1: Log Monitoring with Timeout

**Template**:
```bash
# Start process in background
$YOUR_COMMAND > /tmp/process.log 2>&1 &
process_pid=$!

# Monitor logs
timeout=30
elapsed=0
success=false

while [[ $elapsed -lt $timeout ]]; do
  # Check for success pattern (service-specific)
  if grep -q "$SUCCESS_PATTERN" /tmp/process.log 2>/dev/null; then
    success=true
    echo "✓ Process started successfully"
    break
  fi

  # Check for error patterns
  if grep -qiE "$ERROR_PATTERN" /tmp/process.log 2>/dev/null; then
    echo "✗ Process failed"
    cat /tmp/process.log
    exit 1
  fi

  # Check if process died
  if ! kill -0 $process_pid 2>/dev/null; then
    echo "✗ Process exited unexpectedly"
    cat /tmp/process.log
    exit 1
  fi

  sleep 1
  elapsed=$((elapsed + 1))
done

if [[ "$success" == "false" ]]; then
  echo "✗ Process startup timed out"
  cat /tmp/process.log
  exit 1
fi
```

### Pattern 2: Artifact Validation

**Template**:
```bash
# Run build command
$BUILD_COMMAND

# Define required artifacts
required_artifacts=(
  "path/to/artifact1"
  "path/to/artifact2"
)

# Verify all artifacts exist
for artifact in "${required_artifacts[@]}"; do
  if [[ ! -f "$artifact" ]]; then
    echo "✗ Missing artifact: $artifact"
    exit 1
  fi

  # Verify non-zero size
  size=$(wc -c < "$artifact")
  if [[ $size -eq 0 ]]; then
    echo "✗ Artifact is empty: $artifact"
    exit 1
  fi

  # Verify specific content patterns (if applicable)
  if [[ "$artifact" == *.json ]]; then
    if ! jq empty "$artifact" 2>/dev/null; then
      echo "✗ Invalid JSON: $artifact"
      exit 1
    fi
  fi
done

echo "✓ All artifacts validated"
```

### Pattern 3: Health Check Polling

**Template**:
```bash
# Start service
$START_COMMAND

# Poll health endpoint
timeout=60
elapsed=0

while [[ $elapsed -lt $timeout ]]; do
  # HTTP health check
  if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ Service is healthy"
    exit 0
  fi

  # Alternative: Check for process listening on port
  if lsof -i :8080 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "✓ Service listening on port 8080"
    exit 0
  fi

  sleep 2
  elapsed=$((elapsed + 2))
done

echo "✗ Service failed to become healthy"
exit 1
```

### Pattern 4: Database State Verification

**Template**:
```bash
# Run database operation
$DB_COMMAND

# Verify expected state
expected_count=10
actual_count=$(psql -d mydb -tAc "SELECT COUNT(*) FROM $TABLE;")

if [[ $actual_count -ne $expected_count ]]; then
  echo "✗ Database state mismatch: expected $expected_count rows, got $actual_count"
  exit 1
fi

# Verify specific records exist
if ! psql -d mydb -tAc "SELECT id FROM $TABLE WHERE id = '$EXPECTED_ID';" | grep -q "$EXPECTED_ID"; then
  echo "✗ Expected record not found: $EXPECTED_ID"
  exit 1
fi

echo "✓ Database state verified"
```

---

## Success Patterns by Tool

| Tool           | Success Pattern                      | Error Pattern                        |
| -------------- | ------------------------------------ | ------------------------------------ |
| **Tauri**      | `Accepted new IPC connection`        | `error\|compilation failed\|panic`   |
| **Webpack**    | Artifact size > 1KB                  | `Uncaught\|ReferenceError`           |
| **Docker**     | Health status: `healthy`             | State: `restarting`                  |
| **PostgreSQL** | Query returns expected rows          | `ERROR:\|FATAL:`                     |
| **Rust**       | `Finished release [optimized] `      | `error:\|could not compile`          |
| **Node.js**    | Process listening on port            | `EADDRINUSE\|ECONNREFUSED`           |
| **Python**     | `Server running on http://`          | `Traceback\|Exception`               |
| **Go**         | `Server started on :`                | `panic:\|fatal error:`               |
| **Ruby**       | `Listening on tcp://`                | `LoadError\|RuntimeError`            |
| **Java**       | `Started Application in`             | `Exception in thread\|java.lang`     |

---

## Testing Silent Failure Detection

### Test 1: Intentional Compilation Error

```bash
# Introduce syntax error
echo "fn broken() { invalid syntax" >> src/lib.rs

# Run workflow
./workflow.sh --phase 2

# Expected: Detects compilation error within 30s
# Expected: Shows relevant error logs
# Expected: Exits with non-zero code
```

### Test 2: Service Crash After Start

```bash
# Introduce crash after 5 seconds
echo "setTimeout(() => { throw new Error('crash'); }, 5000);" >> src/app.js

# Run workflow
./workflow.sh --phase 2

# Expected: Detects service crash
# Expected: Shows crash logs
# Expected: Exits with non-zero code
```

### Test 3: Incomplete Artifacts

```bash
# Corrupt build output
rm dist/critical-asset.js

# Run workflow
./workflow.sh --phase 2

# Expected: Detects missing artifact
# Expected: Lists missing files
# Expected: Exits with non-zero code
```

---

## Best Practices

1. **Never Trust Exit Codes Alone**
   - Always validate actual state
   - Check logs for success patterns
   - Verify artifacts were created correctly

2. **Use Service-Specific Success Indicators**
   - Each tool has unique "ready" messages
   - Research the success pattern for your stack
   - Document patterns in workflow script comments

3. **Implement Timeouts**
   - Set reasonable timeout limits (30-60s for services)
   - Show progress during wait (dots, spinner, timer)
   - Provide helpful timeout messages

4. **Log Everything**
   - Redirect stdout/stderr to files
   - Show logs on failure
   - Preserve logs for debugging

5. **Test Failure Scenarios**
   - Intentionally break builds/services
   - Verify detection works
   - Ensure error messages are helpful

---

**Reference Version**: 1.0.0
**Maintainer**: Jarad DeLorenzo
**Last Updated**: 2025-10-28
