# Zellij Plugin API Commands Reference

Complete reference of all available plugin API commands organized by category.

## Core Plugin Lifecycle

- **subscribe** - Register for specific events
- **unsubscribe** - Remove event subscriptions
- **request_permission** - Ask user to grant permissions in the `load` method
- **set_selectable** - Toggle whether users can interact with the plugin
- **get_plugin_ids** - Retrieve plugin's pane ID and process ID
- **get_zellij_version** - Check running Zellij instance version

## File Operations

Requires `OpenFiles` permission. Commands for opening files in `$EDITOR`:

- **open_file** - New pane
- **open_file_floating** - Floating pane
- **open_file_in_place** - Replace focused pane
- **open_file_with_line** - Open at specific line
- **open_file_with_line_floating** - Floating at line
- **open_file_near_plugin** - Same tab as plugin
- **open_file_floating_near_plugin** - Floating in plugin's tab
- **open_file_in_place_of_plugin** - Replace plugin

## Terminal Management

Requires `OpenTerminalsOrPlugins` permission:

- **open_terminal** - New terminal pane
- **open_terminal_floating** - Floating terminal
- **open_terminal_in_place** - Replace focused pane
- **open_terminal_near_plugin** - In plugin's tab
- **open_terminal_floating_near_plugin** - Floating in plugin's tab
- **open_terminal_in_place_of_plugin** - Replace plugin

## Command Panes

Requires `RunCommands` permission. Execute commands with UI control:

- **open_command_pane** - New command pane
- **open_command_pane_floating** - Floating version
- **open_command_pane_in_place** - Replace focused pane
- **open_command_pane_near_plugin** - In plugin's tab
- **open_command_pane_floating_near_plugin** - Floating in plugin's tab
- **open_command_pane_in_place_of_plugin** - Replace plugin
- **open_command_pane_background** - Hidden pane
- **run_command** - Execute background command
- **rerun_command_pane** - Re-execute command pane

## Navigation & Focus

Requires `ChangeApplicationState` permission:

**Tab Navigation:**
- **switch_tab_to** - Focus specific tab by index
- **go_to_next_tab** / **go_to_previous_tab** - Sequential navigation
- **toggle_tab** - Return to previously focused tab
- **go_to_tab_name** - Focus by name
- **focus_or_create_tab** - Focus or create named tab

**Pane Navigation:**
- **focus_next_pane** / **focus_previous_pane** - Sequential pane navigation
- **move_focus** - Move in specified direction
- **move_focus_or_tab** - Move focus or switch tabs at edges

## Pane Management

Requires `ChangeApplicationState` permission.

**Resizing:**
- **resize_focused_pane** - Increase/decrease size
- **resize_focused_pane_with_direction** - Directional resize
- **resize_pane_with_id** - Resize specific pane

**Movement:**
- **move_pane** - Swap pane positions
- **move_pane_with_direction** - Directional swap
- **move_pane_with_pane_id** - Swap specific panes
- **move_pane_with_pane_id_in_direction** - Directional swap by ID

**Display & State:**
- **toggle_focus_fullscreen** - Fullscreen toggle
- **toggle_pane_frames** - UI frame visibility
- **toggle_pane_embed_or_eject** - Float/embed toggle

**Closing:**
- **close_focus** - Close focused pane
- **close_terminal_pane** - Close by ID
- **close_plugin_pane** - Close by ID
- **close_multiple_panes** - Close list of panes

## Pane Visibility & Display

- **hide_self** - Suppress plugin pane
- **show_self** - Unsuppress and focus plugin
- **hide_pane_with_id** - Suppress pane by ID
- **show_pane_with_id** - Show pane by ID
- **focus_terminal_pane** - Focus terminal by ID
- **focus_plugin_pane** - Focus plugin by ID
- **rename_terminal_pane** - Change terminal title
- **rename_plugin_pane** - Change plugin title
- **rename_tab** - Change tab title

## Scrollback Management

Requires `ChangeApplicationState` permission:

**Scrolling:**
- **scroll_up** / **scroll_down** - Single line scroll
- **scroll_up_in_pane_id** / **scroll_down_in_pane_id** - By ID
- **scroll_to_top** / **scroll_to_bottom** - Jump to ends
- **scroll_to_top_in_pane_id** / **scroll_to_bottom_in_pane_id** - By ID
- **page_scroll_up** / **page_scroll_down** - Page scrolling
- **page_scroll_up_in_pane_id** / **page_scroll_down_in_pane_id** - By ID

**Buffer Management:**
- **clear_screen** - Clear focused pane buffer
- **clear_screen_for_pane_id** - Clear specific pane
- **edit_scrollback** - Edit in `$EDITOR`
- **edit_scrollback_for_pane_with_id** - Edit specific pane

## Input & Output

Requires `WriteToStdin` permission:

- **write** - Send bytes to focused pane stdin
- **write_chars** - Send characters to focused pane
- **write_to_pane_id** - Write bytes to specific pane
- **write_chars_to_pane_id** - Write characters to specific pane

## Layout & Tabs

Requires `ChangeApplicationState` permission:

- **new_tabs_with_layout** - Apply stringified layout
- **new_tabs_with_layout_info** - Apply layout by name/path
- **new_tab** - Create with default layout
- **close_focused_tab** - Close tab
- **close_tab_with_index** - Close by index
- **toggle_active_tab_sync** - Toggle stdin sync
- **previous_swap_layout** / **next_swap_layout** - Swap layout navigation
- **break_panes_to_new_tab** - Create tab from pane IDs
- **break_panes_to_tab_with_index** - Move panes to tab
- **stack_panes** - Convert panes to stack

## Floating Panes

Requires `ChangeApplicationState` permission:

- **float_multiple_panes** - Make floating
- **embed_multiple_panes** - Remove float
- **set_floating_pane_pinned** - Toggle always-on-top
- **change_floating_panes_coordinates** - Set position/size

## Pane Selection & Grouping

Requires `ChangeApplicationState` permission:

- **group_and_ungroup_panes** - Manage multiple-select
- **highlight_and_unhighlight_panes** - Cosmetic marking

## Session Management

Requires `ChangeApplicationState` permission:

- **switch_session** - Switch or create session
- **switch_session_with_focus** - Switch with focus control
- **switch_session_with_layout** - Switch with layout and cwd
- **rename_session** - Change session name
- **delete_dead_session** - Remove inactive session
- **delete_all_dead_sessions** - Remove all inactive
- **kill_sessions** - Kill session list
- **disconnect_other_clients** - Disconnect other users
- **quit_zellij** - Exit all clients

## Application State

**Mode Control (ChangeApplicationState permission):**
- **switch_to_input_mode** - Change mode (Normal, Tab, Pane)
- **detach** - Detach from session
- **dump_session_layout** - Export layout as KDL

**Information (ReadApplicationState permission):**
- **list_clients** - Get connected client info

## Remote Execution

Requires `RunCommands` permission:

- **run_command** - Background command with notifications
- **web_request** - HTTP requests (requires `WebAccess` permission)

## Plugin Workers & Communication

- **post_message_to** - Send to plugin worker
- **post_message_to_plugin** - Send to self/worker
- **pipe_message_to_plugin** - Send to launched plugin (requires `MessageAndLaunchOtherPlugins`)

## CLI Pipes

Requires `ReadCliPipes` permission:

- **block_cli_pipe_input** - Block pipe input
- **unblock_cli_pipe_input** - Unblock pipe input
- **cli_pipe_output** - Send pipe output

## Configuration & Plugins

Requires `Reconfigure` permission:

- **reconfigure** - Merge configuration settings
- **rebind_keys** - Update keybindings

Requires `ChangeApplicationState` permission:

- **reload_plugin** - Reload plugin
- **load_new_plugin** - Load new plugin

## Web Server

Requires `StartWebServer` permission:

- **start_web_server** - Activate web client
- **stop_web_server** - Deactivate web client
- **share_current_session** - Enable session sharing
- **stop_sharing_current_session** - Disable sharing
- **query_web_server_status** - Check server status
- **generate_web_login_token** - Create auth token
- **revoke_web_login_token** - Revoke by name
- **revoke_all_web_login_tokens** - Revoke all
- **list_web_login_tokens** - View token list
- **rename_web_login_token** - Rename token

## Input Interception

Requires `InterceptInput` permission:

- **intercept_key_presses** - Capture user input
- **clear_key_presses_intercepts** - Release capture

## Advanced Operations

**Pane Replacement (ChangeApplicationState permission):**
- **replace_pane_with_existing_pane** - Swap pane contents
- **close_self** - Close plugin pane

**Timing:**
- **set_timeout** - Trigger Timer event (seconds)

## File System Access

Requires `FullHdAccess` permission:

- **scan_host_folder** - List host directory contents
- **change_host_folder** - Redirect `/host` filesystem
