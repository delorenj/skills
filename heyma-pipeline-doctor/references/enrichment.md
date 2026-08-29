# Enrichment passes — playbook

Symptoms that land here: transcripts keep bare timestamp filenames instead of
summary slugs; no `title`/`summary` in frontmatter; the vault taxonomy is missing;
`wax.passes.<slug>.state: failed`; the S3 sidecar has no transcript projection.

## How the stage actually works

`worker.process()` calls `passes.run_auto(item_id)` **once**, right after a
successful transcription. The runner:

1. loads the registry from `components/wax/config/passes.d/*.yaml`
   (**not** repo-root `passes.d/`);
2. for each `enabled: true, auto: true` pass whose registered `version` has not
   already completed for this item, expands `{component_root}`, `{md_path}`,
   `{item_id}`, `{home}` and runs `command` as a subprocess with the yaml's `env:`
   injected;
3. on `rc == 0`, parses the child's stdout as a declarative result
   (`frontmatter` to merge, `transcript.slug` to rename to, `link_audio`);
4. records a `passes` row and emits a `task.completed` / `task.failed` event.

Passes are **independent by contract** — `requires:` exists in the schema but a
non-empty value is refused. A pass must never block another pass.

Enabled today: `frontmatter-stamp` (local, deterministic) and `title-slug`
(remote LLM). The other four yaml files are `enabled: false` placeholders with no
scripts. **They are unbuilt, not broken.**

## Triage order

### 1. What does the ledger say, in its own words?

```bash
sqlite3 -readonly "file:$HOME/HeyMa/var/wax.db?mode=ro" \
  "SELECT item_id, ep_slug, attempt, state, reason_code, substr(detail,1,160), updated_at
     FROM passes WHERE state<>'completed' ORDER BY updated_at DESC LIMIT 15;"
```

`detail` is the child's stderr. It is almost always the whole answer. If
`reason_code` is `nonzero_exit` with an unhelpful detail, the pass is not
classifying its own failures — fix that before debugging further, or you will do
this twice.

### 2. Is the right registry loaded?

```bash
bin/wax ep list
```

`title-slug` must be present. If it is not, the runner is reading the wrong
`passes.d` — check `WAX_PASSES_DIR` and `component.ROOT`. Repo-root `passes.d/` is
a decoy that lacks `title-slug.yaml` entirely.

### 3. Run the pass by hand — this is the fastest signal available

The pass scripts are side-effect free by design: they read one transcript and
print a JSON result. Running one directly costs nothing and shows you the real
error.

```bash
components/wax/config/passes.d/bin/title-slug ~/d/Transcripts/<newest>.md test-item; echo "rc=$?"
```

### 4. Re-drive after fixing

`run_auto` is called from exactly one place — during processing. An item already
parked to `complete` is **never retried**, so a fixed dependency does not heal the
backlog on its own.

```bash
bin/wax ep run title-slug <item_id>     # one item
bin/wax ep run-all <item_id>            # every auto pass for one item
bin/wax ep sweep --dry-run              # everything stranded, preview
bin/wax ep sweep --max-attempts 3       # actually re-drive
```

Bumping a pass's `version:` in its yaml also makes previously-failed items
eligible again, because the runner's skip gate is per (item, slug, version).

## title-slug specifically

It calls a hosted **OpenAI-compatible** endpoint. Provider is pure configuration
in `title-slug.yaml`; switching providers is a three-value edit, never a code
change.

| Env | Default | Meaning |
|---|---|---|
| `WAX_TITLE_API_BASE` | `https://openrouter.ai/api/v1` | any OpenAI-compatible base |
| `WAX_TITLE_MODEL` | `google/gemini-3.7-flash` | must appear in `{base}/models` |
| `WAX_TITLE_API_KEY_OP` | `op://DeLoSecrets/yydsybdlpernq5j5tcf42hmtsi/credential` | dedicated HeyMa key, resolved at call time |
| `WAX_TITLE_API_KEY_OP_FALLBACK` | `op://DeLoSecrets/OpenRouter/hermes` | borrowed key; warns loudly |
| `WAX_TITLE_REQUEST_TIMEOUT_S` | `120` | |

**Context length is not a selection criterion.** The pass truncates to
`MAX_CONTEXT_CHARS` (24,000 chars, ~6k tokens) before anything leaves the process,
keeping the head and tail because meetings state their purpose early and their
decisions late. Even a 3-hour meeting fits. Choose on titling quality and price.

To switch to Pokee-Isaac (10M context, `$0.15`/`$1.00` per M):
`WAX_TITLE_API_BASE: https://api.pokee.ai/v1`, `WAX_TITLE_MODEL: pokee-isaac`,
and an `op://` path to a `pk-...` key from `console.pokee.ai/keys`.

### Failure modes, by `reason_code`

| `reason_code` | Means | Do |
|---|---|---|
| `missing_model` | the pinned model is not served | `curl -s $BASE/models \| python3 -m json.tool \| grep -i <name>`, then repin in the yaml |
| `no_api_key` | neither op:// reference resolved | `op whoami`; confirm `OP_SERVICE_ACCOUNT_TOKEN` is in waxd's environ (`tr '\0' '\n' < /proc/$(systemctl --user show -p MainPID --value waxd)/environ \| grep OP_`) |
| `provider_http_error` | 4xx/5xx with a body | read the body in `detail` — it is the provider's own words |
| `provider_unreachable` | DNS/TCP/TLS | network, or a wrong base URL |
| `timeout` | exceeded the request budget | usually a model too large for the host, or a stalled provider |
| `provider_bad_response` | 200 but unusable JSON | the model ignored the schema; try one with real structured-output support |
| `run_error` | the script itself blew up | run it by hand (step 3) |

**If the key resolved from the fallback**, the pass warns on every run. That is
deliberate: Wax is riding another consumer's key and will break the hour it is
rotated, with nothing pointing at Wax. Mint a dedicated field and repoint
`WAX_TITLE_API_KEY_OP`.

## Things that look like enrichment failures but are not

- **A transcript with a real title and summary already** — the pass short-circuits
  and never calls the provider. Grounded values a human or an earlier pass set are
  never clobbered. That is correct.
- **A slug collision** — the rename is collision-safe; a suffixed filename is the
  design working.
- **The four `enabled: false` passes** — unbuilt placeholders.
- **`frontmatter-stamp` completed but `title-slug` failed** — expected. Passes are
  independent; one failing must not stop the other.
