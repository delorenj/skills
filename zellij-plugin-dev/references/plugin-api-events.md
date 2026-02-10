# Zellij Plugin Event System

Complete reference for Zellij plugin events and subscription patterns.

## Overview

Plugins subscribe to events and receive them through the `update` method. Full specifications available in the [`zellij-tile` API documentation](https://docs.rs/zellij-tile/latest/zellij_tile/).

## Event Subscription

Subscribe to events during plugin initialization:

```rust
fn load(&mut self, _configuration: BTreeMap<String, String>) {
    subscribe(&[
        EventType::Key,
        EventType::Mouse,
        EventType::PaneUpdate,
        EventType::TabUpdate,
    ]);
}
```

## Application State Events

Requires `ReadApplicationState` permission.

### ModeUpdate
Provides information about Zellij input modes (Normal, Locked, Pane, Tab, etc.). Includes bound keys and style information.

```rust
Event::ModeUpdate(mode_info) => {
    // mode_info.mode: InputMode
    // mode_info.keybinds: HashMap of mode keybindings
    // mode_info.style: ColorPalette
}
```

### TabUpdate
Details on active tabs including positioning, names, fullscreen status, and swap layouts.

```rust
Event::TabUpdate(tab_info) => {
    // tab_info.position: usize
    // tab_info.name: String
    // tab_info.active: bool
    // tab_info.is_fullscreen_active: bool
    // tab_info.swap_layouts: Vec<String>
}
```

### PaneUpdate
Information about active panes including titles, commands, and exit codes.

```rust
Event::PaneUpdate(pane_manifest) => {
    // pane_manifest.panes: HashMap<PaneId, PaneInfo>
    // PaneInfo contains: title, command, exit_code, is_focused, etc.
}
```

### SessionUpdate
Data on active sessions currently running on the machine.

```rust
Event::SessionUpdate(session_infos, resurrectable_sessions) => {
    // session_infos: Vec<SessionInfo>
    // resurrectable_sessions: Vec<String>
}
```

## User Interaction Events

### Key
Triggered when a user presses a key while focused on the plugin.

```rust
Event::Key(key) => {
    match key.bare_key {
        BareKey::Char('q') if key.has_no_modifiers() => {
            // Handle 'q' key
        }
        BareKey::Down if key.has_no_modifiers() => {
            // Handle down arrow
        }
        _ => {}
    }
}
```

**Key Modifiers:**
- `key.has_no_modifiers()` - No modifier keys
- `key.has_modifiers(&[KeyModifier::Ctrl])` - Ctrl pressed
- `key.has_modifiers(&[KeyModifier::Alt])` - Alt pressed
- `key.has_modifiers(&[KeyModifier::Shift])` - Shift pressed

### Mouse
Activated by mouse actions (clicking, scrolling) on the plugin.

```rust
Event::Mouse(mouse_event) => {
    match mouse_event {
        Mouse::ScrollUp(row) => {
            // Handle scroll up at row position
        }
        Mouse::LeftClick(row, col) => {
            // Handle click at row, col
        }
        _ => {}
    }
}
```

### PastedText
Fired when users paste text while plugin is focused.

```rust
Event::PastedText(text) => {
    // Handle pasted text: String
}
```

## System and Clipboard Events

### CopyToClipboard
Fired when user copies a String to clipboard.

```rust
Event::CopyToClipboard(clipboard_type) => {
    // clipboard_type: CopyToClipboard enum
}
```

### SystemClipboardFailure
Triggered when clipboard operations fail.

```rust
Event::SystemClipboardFailure => {
    // Handle clipboard failure
}
```

## Lifecycle and Communication Events

### Timer
Corresponds to `set_timeout` plugin commands.

```rust
Event::Timer(elapsed) => {
    // elapsed: f64 (seconds since set_timeout)
}
```

Example usage:
```rust
set_timeout(5.0); // Trigger Timer event in 5 seconds
```

### CustomMessage
Enables inter-plugin and plugin-worker communication.

```rust
Event::CustomMessage(message, payload) => {
    // message: String
    // payload: String
}
```

### Visible
Fires when plugins become visible or hidden (e.g., tab switches).

```rust
Event::Visible(is_visible) => {
    // is_visible: bool
}
```

### BeforeClose
Called before plugin is unloaded (if subscribed).

```rust
Event::BeforeClose => {
    // Cleanup before plugin closes
}
```

## File System Events

Requires monitoring file system changes.

### FileSystemCreate
Fired when user creates a file.

```rust
Event::FileSystemCreate(paths) => {
    // paths: Vec<PathBuf>
}
```

### FileSystemRead
Fired when user reads a file.

```rust
Event::FileSystemRead(paths) => {
    // paths: Vec<PathBuf>
}
```

### FileSystemUpdate
Fired when user updates a file.

```rust
Event::FileSystemUpdate(paths) => {
    // paths: Vec<PathBuf>
}
```

### FileSystemDelete
Fired when user deletes a file.

```rust
Event::FileSystemDelete(paths) => {
    // paths: Vec<PathBuf>
}
```

## Command and Pane Management Events

### RunCommandResult
Returns exit status, STDIN, and STDOUT from executed commands.

```rust
Event::RunCommandResult(exit_code, stdout, stderr, context) => {
    // exit_code: Option<i32>
    // stdout: Vec<u8>
    // stderr: Vec<u8>
    // context: BTreeMap<String, String>
}
```

### CommandPaneOpened
Notification that command pane was created.

```rust
Event::CommandPaneOpened(terminal_pane_id, context) => {
    // terminal_pane_id: u32
    // context: BTreeMap<String, String>
}
```

### CommandPaneExited
Notification that command pane exited.

```rust
Event::CommandPaneExited(terminal_pane_id, exit_code, context) => {
    // terminal_pane_id: u32
    // exit_code: Option<i32>
    // context: BTreeMap<String, String>
}
```

### CommandPaneReRun
Notification that command pane was re-run.

```rust
Event::CommandPaneReRun(terminal_pane_id, context) => {
    // terminal_pane_id: u32
    // context: BTreeMap<String, String>
}
```

### EditPaneOpened
File editor pane was opened.

```rust
Event::EditPaneOpened(terminal_pane_id, context) => {
    // terminal_pane_id: u32
    // context: BTreeMap<String, String>
}
```

### EditPaneExited
File editor pane exited.

```rust
Event::EditPaneExited(terminal_pane_id, exit_code, context) => {
    // terminal_pane_id: u32
    // exit_code: Option<i32>
    // context: BTreeMap<String, String>
}
```

### PaneClosed
Indicates pane closure with pane ID.

```rust
Event::PaneClosed(pane_id) => {
    // pane_id: u32
}
```

## Configuration Events

### FailedToWriteConfigToDisk
Sent after failed configuration write attempt.

```rust
Event::FailedToWriteConfigToDisk(error_message) => {
    // error_message: String
}
```

### ConfigWasWrittenToDisk
Confirms successful configuration save.

```rust
Event::ConfigWasWrittenToDisk => {
    // Configuration successfully written
}
```

## Web Events

### WebRequestResult
Returns HTTP status and response body.

```rust
Event::WebRequestResult(status_code, headers, body, context) => {
    // status_code: u16
    // headers: Vec<(String, String)>
    // body: Vec<u8>
    // context: BTreeMap<String, String>
}
```

### WebServerStatus
Web server state notification.

```rust
Event::WebServerStatus(is_running, address) => {
    // is_running: bool
    // address: Option<String>
}
```

### FailedToStartWebServer
Web server failed to start.

```rust
Event::FailedToStartWebServer(error_message) => {
    // error_message: String
}
```

## Advanced Events

### InputReceived
Fired whenever any input is received in Zellij.

```rust
Event::InputReceived => {
    // Any input activity detected
}
```

### InterceptedKeyPress
Represents keypresses captured after `intercept_key_presses` command.

```rust
Event::InterceptedKeyPress(key_with_modifiers, raw_bytes) => {
    // key_with_modifiers: Key
    // raw_bytes: Vec<u8>
}
```

### ListClients
Lists connected session clients with properties.

```rust
Event::ListClients(clients) => {
    // clients: Vec<ClientInfo>
}
```

## Event Pattern Examples

### Pattern: State Synchronization

```rust
fn load(&mut self, _configuration: BTreeMap<String, String>) {
    subscribe(&[EventType::PaneUpdate, EventType::TabUpdate]);
}

fn update(&mut self, event: Event) -> bool {
    match event {
        Event::PaneUpdate(panes) => {
            self.update_pane_state(panes);
            true // Request re-render
        }
        Event::TabUpdate(tabs) => {
            self.update_tab_state(tabs);
            true
        }
        _ => false
    }
}
```

### Pattern: User Input Handling

```rust
fn load(&mut self, _configuration: BTreeMap<String, String>) {
    subscribe(&[EventType::Key]);
}

fn update(&mut self, event: Event) -> bool {
    match event {
        Event::Key(key) => {
            self.handle_keypress(key);
            true
        }
        _ => false
    }
}

fn handle_keypress(&mut self, key: Key) {
    match key.bare_key {
        BareKey::Enter => self.select_current(),
        BareKey::Esc => hide_self(),
        BareKey::Down => self.move_selection_down(),
        BareKey::Up => self.move_selection_up(),
        _ => {}
    }
}
```

### Pattern: Background Command Execution

```rust
fn load(&mut self, _configuration: BTreeMap<String, String>) {
    request_permission(&[PermissionType::RunCommands]);
    subscribe(&[EventType::RunCommandResult]);

    let context = BTreeMap::from([
        ("operation".to_string(), "git_status".to_string())
    ]);
    run_command(vec!["git", "status", "--short"], context);
}

fn update(&mut self, event: Event) -> bool {
    match event {
        Event::RunCommandResult(exit_code, stdout, stderr, context) => {
            if context.get("operation") == Some(&"git_status".to_string()) {
                self.process_git_output(stdout);
                true
            } else {
                false
            }
        }
        _ => false
    }
}
```
