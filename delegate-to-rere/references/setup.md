# Owner-local setup and operational limits

## Install / verify without authentication

Install this canonical definition through Skillex; do not copy it into agent roots by hand or activate a second shadow. The parent rollout owns selection, instruction sync, and Mac verification. From the resolved skill directory:

```sh
uv run --script scripts/delegate_to_rere.py --help
uv run --script scripts/delegate_to_rere.py status
uv run --script tests/test_delegate_to_rere.py
uv run --script tests/test_render_managed.py
uv run --script tests/test_telethon_adapter.py
```

PEP 723 pins `Telethon==1.42.0`, confirmed published on PyPI and installed during development. Python 3.11+ and `uv` are required; `fcntl`/POSIX permissions intentionally target macOS and Linux. Python alone can run help/status/core tests without importing Telethon. The script has no dependency on the surrounding catalog, Hermes, a repository checkout, or a project config. uv's initial dependency download requires public package-network access, not Telegram credentials. No authentication is done by the commands above.

## The one owner command

In **Damian's physical local interactive terminal**, from this skill directory:

```sh
uv run --script scripts/delegate_to_rere.py login
```

If credentials are absent, hidden prompts collect the Telegram application API ID and API hash from the owner. The owner obtains these from their own Telegram application settings at `https://my.telegram.org`; this is not a bot token. They are written only to `~/.local/state/delegate-to-rere/credentials.json` with mode 0600. API ID is not treated as a secret; API hash is. Do not paste either credential into an agent conversation, skill file, task file, terminal command argument, or source control. Never send OTP or 2FA password to an agent.

Alternative: provide `RERE_TELEGRAM_API_ID` and `RERE_TELEGRAM_API_HASH` in the process environment using `op run --env-file <owner-protected-env-reference-file> -- uv run --script scripts/delegate_to_rere.py login`, or another protected local source. The reference file contains owner-selected `op://...` references, never literal secrets in this catalog. This requires working local 1Password authentication. The CLI does not authenticate 1Password for the user. Environment credentials are not persisted. If using them, every subsequent online command needs the same protected environment. Do not enable shell tracing or print the environment. Partial or invalid supplied credentials fail closed.

Login accepts phone, Telegram code, and 2FA password only through hidden local TTY prompts. Owner typing and confirmation have no wall-clock timeout; each login network operation (connect, authorization check, code request, sign-in, identity/group resolution, and close) has its own 45-second deadline, independent of time spent at prompts. The owner sees the account's own name, username, user ID, group title, fixed chat ID, and bot ID, then confirms once. Config contains only public pins and `enabled`; credentials are separate. A failed/interrupted bootstrap may leave this client's unauthorized/authorized SQLite file locally for the owner to retry; pins remain disabled until explicit confirmation. There is no global logout, Desktop cloning, session import, or credential extraction. The code checks for a local TTY, but software cannot prove a TTY is physically local: do not run login via an agent/SSH/remote control terminal.

## Local private files

All under `~/.local/state/delegate-to-rere/` (0700), all files 0600:

- `credentials.json`: optional owner-entered application credentials, never emitted.
- `config.json`: enabled flag and pinned user/group/bot IDs; no hash or session.
- `session.session`: Telethon SQLite session (session stem is `session`); any SQLite journal/WAL companions are also private.
- `request-<uuid>.json`: durable request text, hash, random ID, send status, message ID, and only correlated bot responses. These are private even when the task itself is nonsecret.
- `lock`: POSIX advisory lock. Operations are serialized per client, including network reads, so a wait may hold it for up to 120 seconds.

The **underlying Telegram authorization grants broad user-account access**, not a group-limited capability. The fixed route is a restriction in this tool, not in Telegram's session. Keep the entire directory out of Git, backups with other readers, shared machines, agent exports, and logs. Someone who steals the session can bypass this CLI. Local agents authorized to use this account are consequently trusted with that risk. For stronger isolation use a separate OS user and an owner-approved account model, not a promise of MTProto scope isolation.

`disable` writes disabled pins. `disable --delete-session` additionally deletes only the fixed owned session filenames, and only when the owner requests it. It retains API credentials/receipts for deliberate owner cleanup and never revokes other clients. Revoking this authorization is an owner action in Telegram Devices. There is no arbitrary local path/session override in the CLI.

## Group identity and migration

The sole allowlisted chat is `-5422814811` from the supplied origin metadata; that is a candidate destination, **not proof of membership**. Setup resolves the group from this account's dialogs (bounded to 200), verifies it is the expected active basic group and both owner and bot are participants, resolves `@colrerererebot`, and pins numeric identities. Online operations recheck those identities and membership before use. Missing/migrated group, changed bot, identity mismatch, or a group beyond the bounded dialogs fails closed. Do not fall back to a username, alternate chat, arbitrary access hash, new gateway, or auto-migrated supergroup. A route change requires an explicit reviewed catalog change and new local owner pinning.

## Delivery and reply semantics

A task is limited to **3500 UTF-16 code units including the label**, below Telegram's 4096 limit. No truncation, splitting, attachment upload, or secret-file upload is implemented. The heuristic detector catches common raw keys/tokens/password assignments but is not a data-loss-prevention guarantee. Review payloads first.

Each receipt persists a stable Telegram `random_id`. A receipt in `delivery_unknown` is written and fsynced **before dispatch**. Any uncertain exception/cancellation/crash after that point is never automatically resent, even with the same request UUID; reconciliation scans at most the latest 100 messages for the exact own outgoing text and owner ID. This may conservatively leave an unsent request unknown after a crash just before dispatch. It may also miss an old message outside the window. Report uncertainty instead of blindly submitting another ask. Telegram random-ID deduplication is an extra guard, **not an exactly-once guarantee**. A Telegram FloodWait rejection is distinct: return `retry_after`, do not sleep, and permit only a deliberate later retry with the same random ID and payload.

`read`/`wait` require a known local receipt and its pinned owner/chat. A scan reads at most the latest 100 messages in the single group, but only persists/returns pinned bot messages with a reply path to the original request or previously correlated bot replies. Other members' messages are neither exposed nor stored. A bot response without `reply_to` is uncorrelated even if its text contains the UUID: it cannot be used as success evidence. A chain through a third party is not accepted. A response older than the scan window may not be found. Polling defaults to 60 seconds, max 120, at 3-second intervals. Network work has explicit timeouts; no daemon or resubmission loop exists.

`replied` is transport/correlation evidence only. `completion_status: not_asserted_review_correlated_response` deliberately avoids keyword-based success inference. Read the actual response and distinguish acknowledgment, progress, clarification, refusal, and Rererere's stated completion; independently verify any resulting changes. Telegram text never gains shell-execution authority.

CLI JSON uses exit 0 for a returned operational receipt (including unknown/waiting/rate-limited); consumers **must inspect `status`**. Exit 2 is a local refusal; exit 1 is a sanitized unexpected error. Exception text, API hash, phone/code/password/session are not logged. API hash is required only for online commands; offline status is not a live session check.

## Instruction policy deployment

`references/global-routing.md` is the managed-block source, and `scripts/render_managed.py` updates existing owner-owned instruction files without replacing surrounding policies. Parent deploys this after Skillex install; this skill does not run it automatically.

On the Mac, review the actual active paths. The canonical `~/.agents/AGENTS.md`, home `~/AGENTS.md`, `~/.codex/AGENTS.md`, and `~/.claude/CLAUDE.md` are separate policy files; do not assume symlinks or create a new competing root. Also include an additional actual active file only after discovery. Example preview from the installed skill directory:

```sh
uv run --script scripts/render_managed.py --source references/global-routing.md --target "$HOME/.agents/AGENTS.md" --target "$HOME/AGENTS.md" --target "$HOME/.codex/AGENTS.md" --target "$HOME/.claude/CLAUDE.md"
```

Exit 1 means drift without writes; exit 0 means converged; exit 2 means invalid input. Review, repeat with `--apply` under the approved rollout, then rerun without `--apply` to prove convergence and inspect Git changes. The helper resolves existing symlinks, preserves modes and surrounding bytes/newlines, refuses duplicate/malformed markers and duplicate resolved paths, preflights all targets, and avoids rewriting already converged files. It is not a multi-file transaction if an OS/write failure occurs mid-apply; inspect reported paths before retrying. It never activates a skill or authenticates Telegram.

## Acceptance boundary

Offline tests exercise mocked transport, not Telegram delivery. Deployment is **incomplete** until the owner-local login, a real request receipt, and a correlated Rererere reply have all been observed in the intended group. Record those real outcomes without exposing session files or unrelated group content. Authentication, actual Mac execution, and the live round trip are separate remaining rollout gates; never manufacture evidence for them.
