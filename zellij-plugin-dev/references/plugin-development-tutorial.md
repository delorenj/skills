# Zellij Plugin Development Tutorial

Complete guide to developing Zellij plugins in Rust/WASM.

## Prerequisites and Setup

Requirements:
- Basic Rust knowledge (helpful but not mandatory)
- Rust development tools from [rustup.rs](https://rustup.rs/)
- Zellij 0.41 and above
- Terminal or graphical code editor

## Project Scaffolding

Use the `create-rust-plugin` tool to auto-generate project structure:

```bash
zellij plugin -f -- https://github.com/zellij-org/create-rust-plugin/releases/latest/download/create-rust-plugin.wasm
```

This generates a skeleton repository and launches the `develop-rust-plugin` tool for real-time iteration. Press `Ctrl Shift r` to compile and reload changes.

## Core Plugin Architecture

### Plugin State Structure

```rust
#[derive(Default)]
struct State {
    marked_panes: Vec<PaneId>,
    selected_index: usize,
    pane_titles: HashMap<PaneId, String>,
    focused_pane_id: Option<PaneId>,
}

impl ZellijPlugin for State {
    fn load(&mut self, configuration: BTreeMap<String, String>) { }
    fn update(&mut self, event: Event) -> bool { }
    fn render(&mut self, rows: usize, cols: usize) { }
    fn pipe(&mut self, pipe_message: PipeMessage) -> bool { }
}
```

## Key Functions

### Rendering UI

The `render` function receives dimensions and constructs the visual interface using Zellij's UI components:

```rust
fn render(&mut self, rows: usize, cols: usize) {
    let title = Text::new("CAROUSEL").color_range(2, ..);
    print_text_with_coordinates(title, 0, 0, None, None);
}
```

Color indices (0-3) ensure theme compatibility without explicit color specification.

### Handling User Input

Subscribe to events during `load`:

```rust
subscribe(&[EventType::Key, EventType::PaneUpdate]);
```

React to keypresses in `update`:

```rust
match event {
    Event::Key(key) => {
        match key.bare_key {
            BareKey::Down if key.has_no_modifiers() => {
                self.selected_index += 1;
            }
            _ => {}
        }
    }
    _ => {}
}
```

### Receiving Piped Messages

First, request and bind a keybinding globally:

```rust
request_permission(&[PermissionType::Reconfigure]);
```

Then handle piped messages:

```rust
fn pipe(&mut self, pipe_message: PipeMessage) -> bool {
    if pipe_message.source == PipeSource::Keybind {
        if pipe_message.name == "mark_pane" {
            self.mark_focused_pane();
        }
    }
    false
}
```

### Accessing Zellij State

Subscribe to state updates:

```rust
subscribe(&[EventType::PaneUpdate, EventType::TabUpdate]);
```

Extract focused pane information:

```rust
fn update_panes(&mut self) {
    for pane in panes_in_tab {
        if pane.is_focused {
            self.focused_pane_id = Some(pane_id);
        }
        self.pane_titles.insert(pane_id, pane.title.to_owned());
    }
}
```

## Building and Distribution

### Release Build

```bash
cargo build --release
```

This generates a WASM binary at: `target/wasm32-wasi/release/<PLUGIN_NAME>.wasm`

### Loading the Plugin

```bash
zellij plugin -- file://<PATH_TO_FILE>
```

### Publishing

Use GitHub Actions to automate releases, then share via the [awesome-zellij](https://github.com/zellij-org/awesome-zellij) repository.

## Important Resources

- **Plugin Documentation:** [zellij.dev/documentation/plugins](https://zellij.dev/documentation/plugins)
- **Rust API Reference:** [docs.rs/zellij-tile](https://docs.rs/zellij-tile/latest/zellij_tile/index.html)
- **Community:** Discord channel for developer support

## Example Project: Carousel Plugin

The tutorial builds a "Carousel" plugin demonstrating:
- Rendering custom UI
- Event handling (keyboard input)
- State management (marked panes)
- Inter-plugin communication (pipe messages)
- Navigation between marked panes
