# Plugin Examples: External Integration

Real-world example demonstrating external process management and system integration.

## zj-docker: Docker Container Management

**Repository:** https://github.com/dj95/zj-docker
**License:** MIT (© 2023 Lev Perschin, Daniel Jankowski)
**Category:** System Integration
**Language:** Rust/WASM (wasm32-wasi)

### Overview

zj-docker integrates Docker container management into Zellij, demonstrating patterns for external process execution and system integration. Emphasizes operational convenience for common workflows rather than comprehensive API coverage.

### Core Capabilities

**Container Operations:**
- Enumerate available Docker containers
- Display containers within Zellij interface
- Start and stop containers through UI
- Stream container logs to new Zellij panes

**Design Philosophy:**
Prioritizes usability for common workflows over exposing full Docker API surface.

### Integration Architecture

**External Command Execution:**
The plugin invokes Docker commands through system execution rather than direct Docker API communication.

**Separation of Concerns:**
- Plugin UI runs in plugin pane
- Docker commands execute in separate panes
- Log streaming creates persistent pane processes
- Clear boundary between UI and command execution

### Implementation Patterns

#### Container Enumeration

**Pattern:**
```rust
use zellij_tile::prelude::*;

fn list_containers(&mut self) {
    let context = BTreeMap::from([
        ("operation".to_string(), "list_containers".to_string())
    ]);

    run_command(
        vec!["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}"],
        context
    );
}

fn update(&mut self, event: Event) -> bool {
    match event {
        Event::RunCommandResult(exit_code, stdout, stderr, context) => {
            if context.get("operation") == Some(&"list_containers".to_string()) {
                self.parse_container_list(&stdout);
                true
            } else {
                false
            }
        }
        _ => false
    }
}

fn parse_container_list(&mut self, output: &[u8]) {
    let output_str = String::from_utf8_lossy(output);
    self.containers = output_str
        .lines()
        .filter_map(|line| {
            let parts: Vec<&str> = line.split('\t').collect();
            if parts.len() >= 3 {
                Some(Container {
                    id: parts[0].to_string(),
                    name: parts[1].to_string(),
                    status: parts[2].to_string(),
                })
            } else {
                None
            }
        })
        .collect();
}
```

#### Container State Management

**Start Container:**
```rust
fn start_container(&self, container_id: &str) {
    let context = BTreeMap::from([
        ("operation".to_string(), "start".to_string()),
        ("container_id".to_string(), container_id.to_string()),
    ]);

    run_command(
        vec!["docker", "start", container_id],
        context
    );
}
```

**Stop Container:**
```rust
fn stop_container(&self, container_id: &str) {
    let context = BTreeMap::from([
        ("operation".to_string(), "stop".to_string()),
        ("container_id".to_string(), container_id.to_string()),
    ]);

    run_command(
        vec!["docker", "stop", container_id],
        context
    );
}
```

**Handling Results:**
```rust
Event::RunCommandResult(exit_code, stdout, stderr, context) => {
    match context.get("operation").map(String::as_str) {
        Some("start") | Some("stop") => {
            if exit_code == Some(0) {
                self.refresh_containers(); // Reload container list
            } else {
                self.show_error(stderr);
            }
            true
        }
        _ => false
    }
}
```

#### Log Streaming

**Pattern: Create Log Pane**
```rust
fn tail_logs(&self, container_name: &str) {
    // Opens new pane running docker logs command
    open_command_pane(
        CommandToRun {
            path: "docker".into(),
            args: vec![
                "logs".into(),
                "-f".into(),
                container_name.into()
            ],
            cwd: None,
        },
        false, // Don't float
        None,  // No custom name
    );
}
```

**Alternative: Floating Log Pane**
```rust
fn tail_logs_floating(&self, container_name: &str) {
    open_command_pane_floating(
        CommandToRun {
            path: "docker".into(),
            args: vec!["logs", "-f", container_name].into_iter().map(String::from).collect(),
            cwd: None,
        },
        Some(format!("Logs: {}", container_name)),
    );
}
```

### State Management Patterns

**Minimal State Tracking:**
Container state reflects current Docker daemon state. Plugin doesn't maintain persistent state beyond current view.

**Event-Driven Updates:**
- Operations trigger immediate Docker commands
- Results trigger UI refresh
- Log operations spawn independent processes

**State Structure:**
```rust
#[derive(Default)]
struct State {
    containers: Vec<Container>,
    selected_index: usize,
    error_message: Option<String>,
}

struct Container {
    id: String,
    name: String,
    status: String,
}
```

### UI Rendering

**Container List Display:**
```rust
fn render(&mut self, rows: usize, cols: usize) {
    let title = Text::new("Docker Containers")
        .color_range(1, ..);
    print_text_with_coordinates(title, 0, 0, None, None);

    let headers = Text::new("NAME           STATUS")
        .color_range(2, ..);
    print_text_with_coordinates(headers, 1, 0, None, None);

    for (i, container) in self.containers.iter().enumerate() {
        let row = i + 2;
        let is_selected = i == self.selected_index;

        let status_color = match container.status.as_str() {
            s if s.contains("Up") => 3, // Green
            s if s.contains("Exited") => 1, // Red
            _ => 0, // Default
        };

        let prefix = if is_selected { "> " } else { "  " };
        let line = format!(
            "{}{:<15} {}",
            prefix,
            container.name,
            container.status
        );

        let text = if is_selected {
            Text::new(&line).color_range(1, ..)
        } else {
            Text::new(&line).color_range(status_color, container.name.len() + 2..)
        };

        print_text_with_coordinates(text, row, 0, None, None);
    }
}
```

### User Interaction

**Keyboard Navigation:**
```rust
fn handle_key(&mut self, key: Key) -> bool {
    match key.bare_key {
        BareKey::Down if key.has_no_modifiers() => {
            self.move_selection(1);
            true
        }
        BareKey::Up if key.has_no_modifiers() => {
            self.move_selection(-1);
            true
        }
        BareKey::Char('s') if key.has_no_modifiers() => {
            if let Some(container) = self.selected_container() {
                if container.status.contains("Up") {
                    self.stop_container(&container.id);
                } else {
                    self.start_container(&container.id);
                }
            }
            true
        }
        BareKey::Char('l') if key.has_no_modifiers() => {
            if let Some(container) = self.selected_container() {
                self.tail_logs(&container.name);
            }
            true
        }
        BareKey::Char('r') if key.has_no_modifiers() => {
            self.refresh_containers();
            true
        }
        _ => false
    }
}
```

### Permission Requirements

**Required Permissions:**
```rust
fn load(&mut self, _configuration: BTreeMap<String, String>) {
    request_permission(&[
        PermissionType::RunCommands,
        PermissionType::OpenTerminalsOrPlugins,
    ]);

    subscribe(&[
        EventType::Key,
        EventType::RunCommandResult,
    ]);

    self.refresh_containers();
}
```

### Error Handling

**Command Failure Pattern:**
```rust
Event::RunCommandResult(exit_code, stdout, stderr, context) => {
    if let Some(code) = exit_code {
        if code != 0 {
            let error = String::from_utf8_lossy(&stderr);
            self.error_message = Some(format!(
                "Docker command failed (exit {}): {}",
                code,
                error
            ));
            return true;
        }
    }

    // Handle success case
    match context.get("operation").map(String::as_str) {
        Some("list_containers") => self.parse_container_list(&stdout),
        Some("start") | Some("stop") => self.refresh_containers(),
        _ => {}
    }

    true
}
```

### Key Integration Patterns

#### 1. Command Context Pattern

Use context map to track operation type and associated data:

```rust
let context = BTreeMap::from([
    ("operation".to_string(), "operation_name".to_string()),
    ("resource_id".to_string(), resource_id.to_string()),
    ("metadata".to_string(), additional_data.to_string()),
]);

run_command(args, context);
```

Then match on context in event handler:

```rust
Event::RunCommandResult(exit_code, stdout, stderr, context) => {
    match context.get("operation").map(String::as_str) {
        Some("operation_name") => {
            let resource_id = context.get("resource_id").unwrap();
            self.handle_result(resource_id, stdout);
        }
        _ => {}
    }
}
```

#### 2. Process Spawning Pattern

Create persistent command panes for long-running processes:

```rust
// Background process in new pane
open_command_pane(CommandToRun { /* ... */ }, false, None);

// Floating process overlay
open_command_pane_floating(CommandToRun { /* ... */ }, Some("Title"));

// Background process (no UI)
open_command_pane_background(CommandToRun { /* ... */ }, context);
```

#### 3. State Refresh Pattern

Keep plugin state synchronized with external system:

```rust
fn refresh_state(&mut self) {
    let context = BTreeMap::from([
        ("operation".to_string(), "refresh".to_string())
    ]);

    run_command(self.get_state_command(), context);
}

// Call refresh after mutations
fn perform_action(&mut self) {
    self.execute_action();
    self.refresh_state(); // Reload to reflect changes
}
```

#### 4. Asynchronous Operation Pattern

Handle operations that complete asynchronously:

```rust
struct State {
    pending_operations: HashMap<String, Operation>,
}

fn start_operation(&mut self, op_id: String, operation: Operation) {
    self.pending_operations.insert(op_id.clone(), operation);

    let context = BTreeMap::from([
        ("op_id".to_string(), op_id),
    ]);

    run_command(/* ... */, context);
}

Event::RunCommandResult(exit_code, stdout, stderr, context) => {
    if let Some(op_id) = context.get("op_id") {
        if let Some(operation) = self.pending_operations.remove(op_id) {
            self.complete_operation(operation, exit_code, stdout);
        }
    }
}
```

### Best Practices

**1. Use Context Maps:**
Always include operation type and relevant IDs in command contexts for proper result routing.

**2. Handle Failures Gracefully:**
Check exit codes and provide user feedback on errors.

**3. Separate UI from Execution:**
Use command panes for long-running processes rather than blocking the plugin.

**4. Refresh After Mutations:**
Reload state after operations that modify external systems.

**5. Provide User Feedback:**
Show loading states, success/error messages, and operation progress.

**6. Permission Awareness:**
Request all necessary permissions during `load()` and handle permission denial gracefully.

### Technical Considerations

**WASM Limitations:**
- No direct socket/network access
- Must use Zellij's command execution API
- All system interaction via spawned processes

**State Synchronization:**
- External system is source of truth
- Plugin state is a cached view
- Refresh mechanism keeps views consistent

**Process Independence:**
- Log streaming creates autonomous panes
- Plugin doesn't manage spawned process lifecycle
- Clean separation reduces plugin complexity

### Key Takeaways

1. **Command Context** - Use context maps to route command results to appropriate handlers
2. **Process Separation** - Leverage Zellij's pane system for long-running operations
3. **State Synchronization** - Implement refresh patterns to stay synchronized with external systems
4. **Error Handling** - Always check exit codes and provide user feedback
5. **WASM Constraints** - Work within WASM limitations using Zellij's process execution APIs
