# Node-RED Flow Patterns

## Tab Organization

Each Node-RED flow file can contain multiple tabs (workflows). Organize by logical workflow stages:

```json
[
  {
    "id": "tab_ingest",
    "type": "tab",
    "label": "Ingest -> Bloodbank",
    "info": "Watch inbox, upload to MinIO, publish event"
  },
  {
    "id": "tab_webhook",
    "type": "tab",
    "label": "Webhook -> Ready Event",
    "info": "Receive webhook, fetch data, publish event"
  }
]
```

## Common Node Patterns

### File Watching

```json
{
  "id": "watch_node",
  "type": "watch",
  "name": "Watch directory",
  "files": "${WATCH_DIR}",
  "recursive": true,
  "wires": [["filter_node"]]
}
```

### File Type Filtering

```json
{
  "id": "filter_media",
  "type": "switch",
  "name": "Only media files",
  "property": "filename",
  "propertyType": "msg",
  "rules": [
    {"t": "regex", "v": "\\.(mp3|wav|m4a|mp4|mov)$", "vt": "str", "case": false},
    {"t": "else"}
  ],
  "outputs": 2,
  "wires": [["next_node"], []]
}
```

### Event Type Filtering

```json
{
  "id": "filter_events",
  "type": "switch",
  "name": "File update only",
  "property": "event",
  "propertyType": "msg",
  "rules": [{"t": "eq", "v": "update", "vt": "str"}],
  "outputs": 1,
  "wires": [["next_node"]]
}
```

### Delay/Debounce

```json
{
  "id": "delay_node",
  "type": "delay",
  "name": "Wait for file write",
  "pauseType": "delay",
  "timeout": "5",
  "timeoutUnits": "seconds",
  "wires": [["next_node"]]
}
```

### Python Script Execution

```json
{
  "id": "exec_script",
  "type": "exec",
  "name": "Run Python script",
  "command": "${SCRIPTS_DIR}/.venv/bin/python ${SCRIPTS_DIR}/script.py",
  "addpay": "filename",  // Append msg.filename as arg
  "timeout": "60",
  "wires": [["success_node"], ["error_node"], []]
}
```

### JSON Parsing

```json
{
  "id": "json_parse",
  "type": "json",
  "name": "Parse JSON",
  "property": "payload",
  "action": "",  // Auto-detect
  "wires": [["next_node"]]
}
```

### HTTP Request

```json
{
  "id": "http_request",
  "type": "http request",
  "name": "Call API",
  "method": "POST",
  "ret": "obj",
  "url": "https://api.example.com/endpoint",
  "wires": [["response_handler"]]
}
```

**Setting headers:**
```javascript
// In function node before HTTP request
msg.headers = {
  'content-type': 'application/json',
  'authorization': `Bearer ${env.get('API_KEY')}`
};
msg.payload = { data: "value" };
return msg;
```

### Function Node (Data Transformation)

```json
{
  "id": "transform",
  "type": "function",
  "name": "Transform data",
  "func": "const input = msg.payload;\nmsg.output = {\n  transformed: input.value\n};\nreturn msg;",
  "outputs": 1,
  "wires": [["next_node"]]
}
```

**Function node best practices:**
```javascript
// Access environment variables
const apiKey = env.get('API_KEY') || '';
const homeDir = env.get('HOME') || '/home/user';

// Generate UUIDs
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Error handling
if (!requiredValue) {
  node.error('Missing required value', msg);
  return null;  // Stop flow
}

// Store metadata across nodes
msg.meta = msg.meta || {};
msg.meta.custom_field = "value";
```

### File Write

```json
{
  "id": "file_write",
  "type": "file",
  "name": "Write file",
  "filename": "",  // Use msg.filename
  "filenameType": "msg",
  "appendNewline": false,
  "createDir": true,
  "overwriteFile": "true",
  "encoding": "utf8",
  "wires": [["next_node"]]
}
```

### Bloodbank Event Publishing

```json
{
  "id": "bb_publish",
  "type": "exec",
  "name": "bb publish event",
  "command": "bb publish domain.resource.action --envelope-file",
  "addpay": "filename",  // msg.filename contains envelope JSON path
  "timeout": "30",
  "wires": [["success_debug"], ["error_debug"], []]
}
```

### Webhook Receiver

```json
{
  "id": "webhook_in",
  "type": "http in",
  "name": "Webhook endpoint",
  "url": "/webhooks/service-name",
  "method": "post",
  "wires": [["parse_webhook", "ack_response"]]
}
```

**Webhook acknowledgment:**
```json
{
  "id": "webhook_ack",
  "type": "http response",
  "name": "Ack",
  "statusCode": "200",
  "wires": []
}
```

### Debug Nodes

```json
{
  "id": "debug_node",
  "type": "debug",
  "name": "Debug output",
  "active": true,
  "tosidebar": true,
  "console": false,
  "tostatus": true,
  "complete": "true",  // Show entire msg object
  "targetType": "full",
  "wires": []
}
```

## Complete Flow Example: File Watch → Process → Publish

```json
[
  {
    "id": "tab_main",
    "type": "tab",
    "label": "Main Workflow"
  },
  {
    "id": "watch",
    "type": "watch",
    "z": "tab_main",
    "name": "Watch inbox",
    "files": "${WATCH_DIR}",
    "recursive": true,
    "wires": [["filter"]]
  },
  {
    "id": "filter",
    "type": "switch",
    "z": "tab_main",
    "name": "Media files only",
    "property": "filename",
    "propertyType": "msg",
    "rules": [
      {"t": "regex", "v": "\\.(mp3|mp4)$", "vt": "str"},
      {"t": "else"}
    ],
    "outputs": 2,
    "wires": [["process"], []]
  },
  {
    "id": "process",
    "type": "exec",
    "z": "tab_main",
    "name": "Process file",
    "command": "${SCRIPTS_DIR}/.venv/bin/python ${SCRIPTS_DIR}/process.py",
    "addpay": "filename",
    "timeout": "60",
    "wires": [["json_parse"], ["debug_err"], []]
  },
  {
    "id": "json_parse",
    "type": "json",
    "z": "tab_main",
    "name": "Parse result",
    "property": "payload",
    "wires": [["build_envelope"]]
  },
  {
    "id": "build_envelope",
    "type": "function",
    "z": "tab_main",
    "name": "Build envelope",
    "func": "const result = msg.payload;\nconst envelope = {\n  event_type: 'domain.resource.action',\n  event_id: uuidv4(),\n  timestamp: new Date().toISOString(),\n  version: '1.0.0',\n  source: { host: 'node-red', type: 'file_watch', app: 'node-red' },\n  correlation_ids: [],\n  payload: result\n};\n\nfunction uuidv4() {\n  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {\n    const r = Math.random() * 16 | 0;\n    const v = c === 'x' ? r : (r & 0x3 | 0x8);\n    return v.toString(16);\n  });\n}\n\nconst path = `${env.get('HOME')}/.node-red/bb/event-${envelope.event_id}.json`;\nmsg.payload = JSON.stringify(envelope);\nmsg.filename = path;\nreturn msg;",
    "wires": [["write_envelope"]]
  },
  {
    "id": "write_envelope",
    "type": "file",
    "z": "tab_main",
    "name": "Write envelope",
    "filename": "",
    "filenameType": "msg",
    "createDir": true,
    "overwriteFile": "true",
    "encoding": "utf8",
    "wires": [["bb_publish"]]
  },
  {
    "id": "bb_publish",
    "type": "exec",
    "z": "tab_main",
    "name": "bb publish",
    "command": "bb publish domain.resource.action --envelope-file",
    "addpay": "filename",
    "timeout": "30",
    "wires": [["debug_success"], ["debug_err"], []]
  },
  {
    "id": "debug_success",
    "type": "debug",
    "z": "tab_main",
    "name": "Success",
    "active": true,
    "complete": "true",
    "wires": []
  },
  {
    "id": "debug_err",
    "type": "debug",
    "z": "tab_main",
    "name": "Error",
    "active": true,
    "complete": "true",
    "wires": []
  }
]
```

## Environment Variables

Node-RED flows use environment variables extensively:

```bash
export WATCH_DIR="/path/to/watch"
export SCRIPTS_DIR="/path/to/scripts"
export API_KEY="secret"
export HOME="/home/user"
```

Access in flows:
```javascript
const watchDir = env.get('WATCH_DIR') || '/default/path';
```

## Best Practices

1. **Use tabs** - Separate logical workflow stages
2. **Name nodes clearly** - Describe what each node does
3. **Add debug nodes** - Connect to all exec node error outputs
4. **Use environment variables** - Never hardcode paths or secrets
5. **Handle errors** - Always wire exec node output 2 (stderr) to debug
6. **Store metadata in msg.meta** - Preserve context across nodes
7. **Validate inputs** - Check for required fields before processing
8. **Use function nodes for complex logic** - But keep domain logic in Python
9. **Generate UUIDs** - Use uuidv4() function for event_id
10. **Write envelopes to disk** - Then publish via `bb` CLI for reliability

## Anti-Patterns

❌ **Domain logic in function nodes** - Keep complex transformations in Python
❌ **Hardcoded paths** - Always use environment variables
❌ **Missing error handling** - Every exec node needs error wire to debug
❌ **Synchronous waits** - Use delay nodes, not while loops
❌ **Large payloads in msg** - Write to files, pass file paths
