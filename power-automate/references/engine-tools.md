# FlowAgent engine tools

Generated from `pa tools --json` against FlowAgent 3.2.1 (62 tools). Regenerate after `pa engine update`;
for a tool's full schema run `pa tools <name>`. "Required" lists the schema's required arguments; `env`
defaults to `PA_DEFAULT_ENVIRONMENT` when omitted.

## Identity and auth

| Tool | Required | What it does |
| --- | --- | --- |
| `whoami` | - | Show which identity FlowAgent is authenticated as: the active Azure CLI account, the Azure CLI profile directory (honours AZURE_CONFIG_DIR), the re... |
| `doctor` | - | Run FlowAgent's auth and connectivity checklist: Azure CLI present, az signed in, AZURE_CONFIG_DIR scoping, resolved cloud, token acquisition, toke... |
| `reconnect` | - | Clear FlowAgent's cached tokens — both the Azure CLI token cache and the separate MSAL cache used for Connectivity (connection) commands — and re-a... |
| `list_accounts` | - | List cached Connectivity accounts separately from the effective account used by the running provider or selected cache partition |
| `switch_account` | - | Clear the cached Connectivity sign-in and save a username preference for the next interactive sign-in |

## Environments

| Tool | Required | What it does |
| --- | --- | --- |
| `list_environments` | - | List all Power Automate environments |
| `resolve_environment` | - | Check which environment the current user resolves to via environment routing |
| `get_current_env` | - | Show the current working environment that env-less tool calls (and the dashboard) target |
| `set_current_env` | env | Set the current working environment that env-less tool calls (and the dashboard) target |

## Flows

| Tool | Required | What it does |
| --- | --- | --- |
| `list_flows` | - | List cloud flows |
| `get_flow` | flow | Get a flow's full definition + connection refs + metadata |
| `get_flow_context` | flow | Resolve a flow's solution-membership: workflowId (Dataverse), workflowIdUnique (pre-publish), inSolution, solutionUniqueName, isManaged, isCustomiz... |
| `create_flow` | name | Create a new cloud flow from a JSON definition |
| `preflight_flow` | - | Pre-save sanity check: validate the definition + check connection-ref status + detect solution-wrap-will-block-publish risk |
| `validate_flow` | - | Pre-validate a flow definition against PA rules |
| `preview_update` | flow | Read-only: compute a diff between the live flow and the proposed update body, and return a short-lived single-use token |
| `update_flow` | flow | Update an existing flow's definition or properties |
| `edit_flow` | flow, operations | Apply targeted ('surgical') edits to an existing flow's definition without resending the whole thing — ideal for changing one action, parameter, or... |
| `copy_flow` | flow | Copy a flow within the same environment or to another environment |
| `publish_flow` | flow | Enable (start) a flow |
| `disable_flow` | flow | Disable (stop) a flow |
| `delete_flow` | flow | Permanently delete a flow |
| `set_current_flow` | flow | Pin a flow as the session's current flow |
| `get_current_flow` | - | Get the session's pinned current flow (or null if none) |
| `clear_current_flow` | - | Unpin the session's current flow |

## Runs

| Tool | Required | What it does |
| --- | --- | --- |
| `run_flow` | flow | Trigger a manual flow run |
| `get_run_history` | flow | Get recent run history for a flow |
| `get_run_details` | flow, run | Get details for a specific flow run |
| `get_run_actions` | flow, run | Get action-level execution details for a specific flow run |
| `get_run_action_content` | run, action, which | Fetch what an action in a run actually received (inputs) or produced (outputs) |
| `get_run_action_repetitions` | run, action | List iteration-level details for an action that runs inside a loop (Apply_to_each / Do_until) within a run — the only way to see WHICH iteration fa... |
| `get_past_trigger_inputs` | flow | Fetch trigger input envelopes from past flow runs — same primitive the PA designer uses for 'Test with previous run data' |
| `cancel_run` | run | Cancel a single in-progress (Running/Waiting) flow run |
| `cancel_all_runs` | - | Bulk-cancel every in-progress run of a flow — for incident response when many erroneous runs are queued |
| `resubmit_run` | run | Resubmit a past run using its original trigger inputs (the trigger is auto-detected from the run) |
| `diagnose_run` | run | Diagnose a flow run: classify each failed/timed-out action with an actionable remediation |
| `list_trigger_emulators` | - | List the trigger types FlowAgent can emulate via direct connector calls (SharePoint NewItem → CreateItem etc.) |

## Connections and connectors

| Tool | Required | What it does |
| --- | --- | --- |
| `list_connections` | - | List connections in an environment, optionally filtered by connector |
| `resolve_refs` | connectors | Auto-discover connections for connectors and output connection references JSON |
| `pick_or_create_connection` | connector | Idempotent: get a Connected connectionName for the requested connector |
| `test_connection` | connector, connection | Check whether a specific connection is currently Connected |
| `fix_connection` | connector, connection | Re-authenticate a broken connection (e.g |
| `delete_connection` | connector, connection, confirm | Delete a connection |
| `list_connectors` | - | List available connectors |
| `get_connector` | connector | Get connector operation index |
| `search_operations` | - | Search connector operations by keyword |
| `get_operation_details` | connector, operation | Get exact param names, types, enums, and required action type for a connector operation |
| `resolve_params` | connector, operation | Designer-emulating dropdown resolver: returns every parameter for a connector operation with its dynamic values (lists, trees, dynamic-schemas) alr... |
| `resolve_entity` | connector, entityType, query | Resolve display names to IDs for dynamic connector parameters (folders, teams, channels, lists, tables) |
| `invoke_operation` | connector, connection, operation | Call a connector's dynamic resolver (dropdowns, tree browsing, dynamic schemas) |
| `list_datasets` | connector, connection | List available datasets for a tabular connector (SharePoint sites, SQL servers, Excel locations, etc.) |
| `list_tables` | connector, connection, dataset | List tables/lists in a dataset for a tabular connector (SharePoint lists, SQL tables, Excel tables, etc.) |

## Templates, expressions, testing

| Tool | Required | What it does |
| --- | --- | --- |
| `list_templates` | - | List built-in flow templates |
| `scaffold_flow` | template | Generate flow definition from template |
| `get_expression_help` | - | Look up Power Automate (Logic Apps WDL) expression functions — name, signature, description, and a copy-pasteable example |
| `smoke_test` | - | End-to-end connectivity test: create, run, verify, cleanup |

## Desktop flows

| Tool | Required | What it does |
| --- | --- | --- |
| `list_desktop_flows` | - | List desktop flows (RPA) in an environment |
| `run_desktop_flow` | flow | Trigger a desktop flow and wait for completion |
| `list_machine_groups` | - | List machine groups in an environment |

## Backups

| Tool | Required | What it does |
| --- | --- | --- |
| `list_backups` | flow | List pre-mutation backup snapshots captured for a flow |
| `get_backup` | flow, file | Read a specific backup snapshot's full contents (flow definition, connectionReferences, optional context) |
| `restore_backup` | flow | Restore a flow from a backup snapshot |

