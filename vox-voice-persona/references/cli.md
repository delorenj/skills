# CLI reference (verified against `voxxy ... --help`, 2026-10-22)

```
voxxy voice persona [OPTIONS] VOICE [PERSONA]      --clear   --json/-j
voxxy persona list [--json/-j]
voxxy persona show [--raw] ID
voxxy persona rewrite [--voice/-v V] [--json/-j] [ID] [TEXT]...   (stdin when TEXT omitted)
voxxy persona path
voxxy speak [--persona ID|auto] ...                 (env VOX_PERSONA; off|none|false|0|no|empty disable)
```

Exit codes: `voice persona` bad slug 5, unknown voice 4; `persona rewrite` rejected 1, unknown id / voice with no persona 4.

Install / refresh: `mise x -- uv tool install --force /home/delorenj/code/voxxy/cli`. The CLI finds the plugin through
`project_root` in `~/.config/voxxy/config.toml` (`voxxy.config.discover_project_root`); without it persona commands
error clearly and `voice persona` set still works with a warning.

Example (real output):

```
$ voxxy persona rewrite peter-griffin "The build finished in 42 seconds and all 118 tests passed." --json
{ "original": "...", "rewrite": "Holy crap, the build finished in 42 seconds and all 118 tests passed. Freakin' sweet!",
  "accepted": true, "reason": null, "persona": "peter-griffin",
  "model": "automaticai/personal/glm-5.3-flash", "prompt_version": "voice-persona/3", "elapsed_s": 5.956 }
$ voxxy voice persona peter
voice:     peter
persona:   peter-griffin (voxxy record)
effective: peter-griffin (voxxy)
```

Effective source values: `voxxy`, `frontmatter`, `none` (explicit), `unknown` (plugin could not be loaded).

Config keys (`~/.config/voxxy/config.toml`, written only when non-default): `persona_base_url`, `persona_model`,
`persona_api_key_ref`. Token minting for the key: `python3 ops/gateway-tokens.py mint <consumer> --models <route>` in
`~/code/client-portal/gateway` (see `automaticai-provider-gateway`); store only the `op://<vault>/<item-uuid>/<field>` reference.
