# Plugin Examples: UI and Navigation

Real-world examples demonstrating UI rendering, search, and navigation patterns.

## Monocle: Fuzzy File Finder

**Repository:** https://github.com/imsnif/monocle
**Category:** File Discovery & Navigation
**Language:** Rust/WASM

### Overview

Monocle implements fuzzy search for file names and contents, demonstrating advanced UI patterns and file system integration.

### Key Features

**File Discovery:**
- Fuzzy find file names and contents
- Automatically ignores hidden files
- Respects `.gitignore` patterns
- Project boundary detection

**Result Handling:**
- Opens files in `$EDITOR` at matching line numbers
- Supports floating and tiled panes
- Can launch new terminal sessions at file locations

**User Experience:**
- Dismisses via ESC or Ctrl+C
- Stays hidden until explicitly invoked
- Non-intrusive workflow integration

### Implementation Patterns

**Kiosk Mode:**
```kdl
zellij plugin --in-place -- file:~/.config/zellij/plugins/monocle.wasm \
  --configuration kiosk=true
```

Enables stacked file viewing where files open atop the search interface.

**Configuration Options:**
- `--floating` - Render as overlay
- `--in-place` - Replace current pane
- `kiosk=true` - Stack files on search UI

### Technical Insights

**Architecture:**
- Pure Rust implementation compiled to WASM
- File system scanning via WASM runtime
- Search algorithm optimized for terminal rendering
- State management for search results and selection

**Known Limitations:**
- Crashes on device files and non-file entities (WASM runtime constraint)
- Unsuitable for system directory scanning

### Development Workflow

Uses `dev.kdl` layout for iterative development:
```bash
zellij -l dev.kdl
```

### Patterns to Learn

1. **Fuzzy Search Implementation** - Text matching and ranking algorithms
2. **File System Integration** - WASM-based file access patterns
3. **Result Presentation** - Terminal UI for search results
4. **Modal Interaction** - Hide/show patterns for non-intrusive tools
5. **Configuration Flexibility** - Support for multiple display modes

---

## Room: Tab Search and Switcher

**Repository:** https://github.com/rvcas/room
**Category:** Tab Navigation
**Language:** Rust/WASM (78.3%), Nix (21.1%)

### Overview

Room streamlines tab navigation through fuzzy search, demonstrating practical modal UI and state management patterns.

### Key Features

**Navigation:**
- Tab/Up/Down arrow keys cycle through results
- Enter key switches to selected tab
- Real-time filtering on tab names
- Numeric quick jump (optional)
- Escape/Ctrl+C to exit

**Search Mechanism:**
- Filters on renamed tabs (not numbers)
- Addresses core pain point of tab memorization
- Type partial names to narrow results

### Configuration

**Basic Setup:**
```kdl
plugin location="file:~/.config/zellij/plugins/room.wasm" {
    floating true
    ignore_case true
    quick_jump false
}
```

**Options:**
- `floating true` - Renders as overlay window
- `ignore_case true` - Case-insensitive matching
- `quick_jump true` - Enables numeric direct selection

**Quick Jump Tradeoff:**
When enabled, numeric keys directly select tabs, but prevents proper filtering of tabs with numbers in their names.

### Implementation Patterns

**State Management:**
- Maintains filtered tab list
- Tracks selection index
- Preserves tab metadata (names, positions)

**Modal Interaction:**
- Launches via `LaunchOrFocusPlugin` action
- Stateful session management
- Hides when not in use

**Keybinding Configuration:**
```kdl
bind "Ctrl t" {
    LaunchOrFocusPlugin "file:~/.config/zellij/plugins/room.wasm" {
        floating true
        ignore_case true
    }
}
```

### Technical Stack

**Composition:**
- 78.3% Rust (core logic)
- 21.1% Nix (development environment)
- KDL for configuration

### Patterns to Learn

1. **Fuzzy Filtering** - Real-time search on dynamic data
2. **Modal UI Design** - Overlay interfaces with focused interaction
3. **State Preservation** - Maintaining selection across invocations
4. **Configuration Tradeoffs** - Feature flags with documented implications
5. **Keybinding Integration** - Plugin launch via global shortcuts

---

## Common UI Patterns

### Overlay/Floating Windows

Both plugins demonstrate floating window patterns:

```kdl
plugin location="file:path/to/plugin.wasm" {
    floating true
}
```

Benefits:
- Non-destructive to existing layout
- Quick access and dismissal
- Focus preservation

### Keyboard-First Navigation

Standard navigation patterns:
- Arrow keys for movement
- Enter for selection
- Escape/Ctrl+C for dismissal
- Tab for alternative navigation

### State Management

Pattern for maintaining plugin state:

```rust
#[derive(Default)]
struct State {
    items: Vec<Item>,
    selected_index: usize,
    filter_text: String,
}

impl State {
    fn filter_items(&self) -> Vec<&Item> {
        self.items.iter()
            .filter(|item| item.matches(&self.filter_text))
            .collect()
    }

    fn move_selection(&mut self, delta: isize) {
        let filtered = self.filter_items();
        let len = filtered.len() as isize;
        self.selected_index = ((self.selected_index as isize + delta)
            .rem_euclid(len)) as usize;
    }
}
```

### Rendering Filtered Lists

```rust
fn render(&mut self, rows: usize, cols: usize) {
    let filtered = self.filter_items();
    let start_row = 2;

    for (i, item) in filtered.iter().enumerate() {
        let row = start_row + i;
        let is_selected = i == self.selected_index;

        let text = if is_selected {
            Text::new(&format!("> {}", item.name))
                .color_range(1, ..)
        } else {
            Text::new(&format("  {}", item.name))
        };

        print_text_with_coordinates(text, row, 0, None, None);
    }
}
```

### Configuration Patterns

Both plugins support KDL-based configuration with sensible defaults and documented tradeoffs for feature flags.

```kdl
plugin location="file:path/to/plugin.wasm" {
    // Display options
    floating true

    // Behavior options
    option_name default_value
}
```
