# Plugin Examples: Status Bars and Theming

Real-world example demonstrating configuration systems, theming, and rendering patterns.

## zjstatus: Configurable Status Bar

**Repository:** https://github.com/dj95/zjstatus
**Category:** Status Bar / UI Framework
**Language:** Rust/WASM

### Overview

zjstatus is a highly customizable status bar plugin demonstrating sophisticated configuration architecture and theming capabilities. Consists of two components:
- Core status bar plugin
- zjframes (pane frame visibility manager)

### Configuration Architecture

Uses KDL (Zellij's configuration language) for declarative setup within layout definitions.

**Basic Configuration:**
```kdl
plugin location="path/to/zjstatus.wasm" {
    format_left   "{mode} {session}"
    format_center "{tabs}"
    format_right  "{command_git_branch} {datetime}"
}
```

### Format System

**Template-Based Formatting:**
Uses named placeholders allowing users to define sections without code changes.

Available placeholders:
- `{mode}` - Current Zellij mode
- `{tabs}` - Open tab information
- `{session}` - Session details
- `{datetime}` - Time/date display
- `{command_*}` - Command output
- `{notifications}` - System alerts
- `{pipe}` - External data streams

### Widget System

**Architecture:**
Extensible widget-based structure where each widget accepts configuration parameters.

**Available Widgets:**

1. **Command** - Execute shell commands and display output
2. **DateTime** - Formatted time/date information
3. **Mode** - Current Zellij mode (normal/tmux)
4. **Tabs** - Open tab rendering
5. **Session** - Session details
6. **Notifications** - System alerts
7. **Pipe** - Stream external data
8. **Swap Layout** - Layout switching controls

### Command Widget Configuration

**Pattern:**
```kdl
command_{name}_command     "shell command"
command_{name}_format      "format string with {stdout}"
command_{name}_interval    "update interval in seconds"
command_{name}_rendermode  "static|dynamic"
```

**Example:**
```kdl
plugin location="path/to/zjstatus.wasm" {
    format_right "{command_git_branch}"

    command_git_branch_command     "git rev-parse --abbrev-ref HEAD"
    command_git_branch_format      "#[fg=blue] {stdout} "
    command_git_branch_interval    "10"
    command_git_branch_rendermode  "static"
}
```

### Theming System

**Color and Formatting Syntax:**
Uses `#[...]` annotations for styling.

**Attributes:**
- `fg=#RRGGBB` or `fg=color_name` - Foreground color
- `bg=#RRGGBB` or `bg=color_name` - Background color
- `bold` - Bold text
- `italic` - Italic text
- `dim` - Dimmed text

**Tab Styling Example:**
```kdl
plugin location="path/to/zjstatus.wasm" {
    format_center "{tabs}"

    tab_normal   "#[fg=#6C7086] {name} "
    tab_active   "#[fg=#9399B2,bold,italic] {name} "
}
```

**Mode Styling Example:**
```kdl
mode_normal  "#[bg=blue] "
mode_tmux    "#[bg=#ffc387] "
mode_locked  "#[bg=#ee5396] "
mode_pane    "#[bg=#89b4fa] "
mode_tab     "#[bg=#89dceb] "
```

### Border Configuration

**Full Border Control:**
```kdl
plugin location="path/to/zjstatus.wasm" {
    border_enabled  "false"
    border_char     "─"
    border_format   "#[fg=#6C7086]{char}"
    border_position "top"
}
```

**Options:**
- `border_enabled` - true/false
- `border_char` - Character to use for border
- `border_format` - Formatting with `{char}` placeholder
- `border_position` - top/bottom/both/none

### Rendering Modes

**Static vs Dynamic:**

**Static Mode:**
- Periodic updates based on interval
- Lower resource usage
- Suitable for slow-changing data (git branch, date)

**Dynamic Mode:**
- Real-time updates
- Higher resource usage
- Suitable for rapidly changing data

```kdl
command_cpu_rendermode "dynamic"
command_git_rendermode "static"
```

### Layout Integration

**Full Layout Example:**
```kdl
layout {
    pane size=1 borderless=true {
        plugin location="file:/path/to/zjstatus.wasm" {
            format_left   "{mode}#[bg=#181825] {tabs}"
            format_center ""
            format_right  "#[bg=#181825,fg=#89dceb]#[bg=#89dceb,fg=#181825,bold] {session} #[bg=#181825] "
            format_space  ""
            format_hide_on_overlength "false"
            format_precedence "crl"

            border_enabled  "false"

            mode_normal        "#[bg=#89b4fa] "
            mode_locked        "#[bg=#89b4fa] "
            mode_resize        "#[bg=#89b4fa] "
            mode_pane          "#[bg=#89b4fa] "
            mode_tab           "#[bg=#89b4fa] "
            mode_scroll        "#[bg=#89b4fa] "
            mode_enter_search  "#[bg=#89b4fa] "
            mode_search        "#[bg=#89b4fa] "
            mode_rename_tab    "#[bg=#89b4fa] "
            mode_rename_pane   "#[bg=#89b4fa] "
            mode_session       "#[bg=#89b4fa] "
            mode_move          "#[bg=#89b4fa] "
            mode_prompt        "#[bg=#89b4fa] "
            mode_tmux          "#[bg=#ffc387] "

            tab_normal   "#[bg=#181825,fg=#89dceb]#[bg=#89dceb,fg=#181825,bold]{index} #[bg=#363a4f,fg=#89dceb,bold] {name}{floating_indicator}#[bg=#181825,fg=#363a4f]"
            tab_active   "#[bg=#181825,fg=#fab387]#[bg=#fab387,fg=#181825,bold]{index} #[bg=#363a4f,fg=#fab387,bold] {name}{floating_indicator}#[bg=#181825,fg=#363a4f]"

            tab_floating_indicator "󰉈 "
            tab_sync_indicator     " "
            tab_fullscreen_indicator "󰊓 "

            command_git_branch_command     "git rev-parse --abbrev-ref HEAD"
            command_git_branch_format      "#[fg=blue] {stdout} "
            command_git_branch_interval    "10"
            command_git_branch_rendermode  "static"
        }
    }
}
```

### Widget Development Pattern

**Creating New Widgets:**

1. Define widget interface
2. Implement configuration parsing
3. Add rendering logic
4. Register widget with format system

**Example Widget Structure:**
```rust
pub struct CustomWidget {
    config: WidgetConfig,
    state: WidgetState,
}

impl Widget for CustomWidget {
    fn update(&mut self, event: &Event) {
        // Update widget state based on events
    }

    fn render(&self, context: &RenderContext) -> String {
        // Return formatted string based on config and state
        format!(
            "{}{}{}",
            self.config.prefix,
            self.render_content(),
            self.config.suffix
        )
    }
}
```

### Configuration Parsing Pattern

**Parameter Naming Convention:**
```
{widget_type}_{widget_name}_{parameter}
```

Examples:
- `command_git_branch_interval`
- `tab_normal`
- `mode_locked`

**Parsing Logic:**
```rust
fn parse_config(config: BTreeMap<String, String>) -> WidgetConfig {
    let prefix = config.get("format_prefix").cloned().unwrap_or_default();
    let suffix = config.get("format_suffix").cloned().unwrap_or_default();
    let interval = config.get("interval")
        .and_then(|s| s.parse().ok())
        .unwrap_or(60);

    WidgetConfig {
        prefix,
        suffix,
        interval,
    }
}
```

### Theming Best Practices

**1. Respect User Themes:**
Use Zellij's built-in color palette when possible rather than hardcoded hex values.

**2. Provide Sensible Defaults:**
```kdl
mode_normal "#[bg=blue]"  // Falls back to theme's blue
```

**3. Support Customization:**
Allow users to override all styling via configuration.

**4. Consistent Patterns:**
Use similar formatting patterns across widgets for visual cohesion.

### Performance Considerations

**Static Rendering:**
- Use for infrequently changing data
- Reduces CPU usage
- Better battery life on laptops

**Dynamic Rendering:**
- Reserve for truly dynamic data
- Consider update frequency
- Balance responsiveness with performance

**Command Execution:**
- Cache command results
- Use appropriate intervals
- Handle command failures gracefully

### Extensibility Patterns

**Declarative Configuration:**
- No code changes for customization
- Configuration-driven behavior
- Clear separation of logic and presentation

**Widget Modularity:**
- Independent widget implementations
- Composable widget system
- Easy to add new widgets

**Format String Flexibility:**
- Users control layout
- Widgets expose placeholders
- Complex layouts via simple strings

### Key Takeaways

1. **Configuration Architecture** - Declarative KDL-based configuration enables deep customization without code changes
2. **Widget System** - Modular, composable widgets support extensibility
3. **Theming Flexibility** - Format string syntax allows sophisticated visual customization
4. **Performance Modes** - Static vs dynamic rendering balances responsiveness with resource usage
5. **Separation of Concerns** - Clear boundaries between configuration, state, and rendering
