# Under the engine: REST, Dataverse and pac

Prefer the engine's tools: they add validation, backups, the managed-solution guard and
structured errors. Use these only when the engine is missing or lacks an operation.
`pa rest` gets an Azure CLI token for the right audience, keeps it in memory, and prints only
the HTTP status and the JSON body.

## Flow service (Microsoft.ProcessSimple), audience `https://service.flow.microsoft.com/`

`pa rest METHOD <path>` prefixes `https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/`
and appends `api-version=2016-11-01`.

| Call | Purpose |
| --- | --- |
| `pa rest GET environments` | environments the caller can see |
| `pa rest GET environments/<env>/flows` | the caller's flows in one environment |
| `pa rest GET environments/<env>/flows/<flow>` | one flow; `properties.definition` and `properties.connectionReferences` for flows the caller owns or co-owns |
| `pa rest PATCH environments/<env>/flows/<flow> --data @body.json` | update; body `{"properties": {"definition": ..., "connectionReferences": ..., "displayName": ...}}`. Export first: there is no undo here. |
| `pa rest POST environments/<env>/flows/<flow>/start` / `.../stop` | turn on / off |
| `pa rest GET environments/<env>/flows/<flow>/runs` | run history |
| `pa rest POST environments/<env>/flows/<flow>/triggers/manual/listCallbackUrl` | a webhook trigger's URL. **The URL is a credential**: store it in the vault, never print or commit it. |

## Dataverse (`workflow` table), audience `https://<org>.crm.dynamics.com`

Solution-aware cloud flows, and in environments with Dataverse most others, are rows of the
`workflow` table with `category eq 5` (modern flow). `clientdata` is a JSON STRING holding
`{"properties": {"definition": ..., "connectionReferences": ...}}`; `statecode` 0 = off, 1 = on.

```bash
pa rest GET "https://<org>.crm.dynamics.com/api/data/v9.2/workflows?\$filter=category eq 5&\$select=name,workflowid,statecode,modifiedon"
pa rest GET "https://<org>.crm.dynamics.com/api/data/v9.2/workflows(<id>)?\$select=clientdata"
```

Find `<org>` with `pa call list_environments` (linked Dataverse instance URL). The tenant's
default environment, where Teams Workflows live, often has no Dataverse; then only the Flow
service path applies. `get_flow_context` says whether a flow is in a solution and whether that
solution is managed.

## Graph, audience `https://graph.microsoft.com`

The Azure CLI's Graph token carries the CLI's own fixed delegated scopes, which do not include
`Chat.Read` or `ChannelMessage.Read.All`; reading Teams messages needs an app registration
(see [teams-events-and-licensing.md](teams-events-and-licensing.md)).

## Power Platform CLI (`pac`), optional

Only for solution ALM (export, import, pack) and Dataverse admin. Install with
`dotnet tool install --global Microsoft.PowerApps.CLI.Tool`; sign in with
`pac auth create --deviceCode --tenant <tenant>` (its own device code, its own token cache under
`~/.local/share/Microsoft/PowerAppsCli/`). FlowAgent does not need it.
