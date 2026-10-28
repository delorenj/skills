# CI runners (GitHub Actions)

The rule is **no PAID runners**; the budget is $0 (operator, 2026-10-01).

- **Private repos:** self-hosted runners only. Never write `runs-on:
  ubuntu-latest`, `macos-*` or any other GitHub-hosted label. Hosted minutes
  are billed, and a hosted job just sits unstarted with "recent account
  payments have failed or your spending limit needs to be increased".
- **Public repos:** standard GitHub-hosted runners are free, so `ubuntu-latest`
  is allowed. Use it where only a hosted runner works. npm OIDC trusted
  publishing and `--provenance` refuse self-hosted runners (E422 "Unsupported
  GitHub Actions runner environment: self-hosted"), so pjangler publishes from a
  hosted job (PJAN-163).

Check visibility first: `gh repo view <owner/repo> --json visibility`.

## Inventory (verified 2026-10-22)

| runner | scope | host | labels | service |
| --- | --- | --- | --- | --- |
| delonet-r1, r2, r3 | org `AutomaticAI-io` | big-chungus, `~/actions-runner/r{1,2,3}` | `self-hosted, Linux, X64, delonet` | `actions.runner.AutomaticAI-io.delonet-r{N}.service` |
| delonet-gib-r1 | repo `delorenj/green-in-between` | big-chungus, `~/actions-runner/gib1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-green-in-between.delonet-gib-r1.service` |
| delonet-holo-r1 | repo `delorenj/holocene` | big-chungus, `~/actions-runner/holo1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-holocene.delonet-holo-r1.service` |
| delonet-px-r1 | repo `delorenj/pilot` | big-chungus, `~/actions-runner/px1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-pilot.delonet-px-r1.service` |
| delonet-hmob-r1 | repo `delorenj/heyma-obsidian` | big-chungus, `~/actions-runner/hmob1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-heyma-obsidian.delonet-hmob-r1.service` |
| delonet-deck-r1 | repo `delorenj/deckard` (private) | big-chungus, `~/actions-runner/deck1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-deckard.delonet-deck-r1.service` |
| delonet-deck-r2 | repo `delorenj/deckard` (private) | big-chungus, `~/actions-runner/deck2` (`.env` copied from deck1 for the cargo PATH) | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-deckard.delonet-deck-r2.service` |
| delonet-dsid-r1 | repo `delorenj/docsidian` (private) | big-chungus, `~/actions-runner/dsid1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-docsidian.delonet-dsid-r1.service` |
| delonet-chsc-r1 | repo `delorenj/ChoreScore` (private) | big-chungus, `~/actions-runner/chsc1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-ChoreScore.delonet-chsc-r1.service` |
| delonet-dcom-r1 | repo `delorenj/delonet-company` (private) | big-chungus, `~/actions-runner/dcom1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-delonet-company.delonet-dcom-r1.service` |
| delonet-slbn-r1 | repo `delorenj/slowburns` (private) | big-chungus, `~/actions-runner/slbn1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-slowburns.delonet-slbn-r1.service` |
| delonet-svgm-r1 | repo `delorenj/svgme` (private) | big-chungus, `~/actions-runner/svgm1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-svgme.delonet-svgm-r1.service` |
| delonet-dlco-r1 | repo `delorenj/DeLoContainers` (private) | big-chungus, `~/actions-runner/dlco1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-DeLoContainers.delonet-dlco-r1.service` |
| delonet-zshz-r1 | repo `delorenj/zshyzsh` (private) | big-chungus, `~/actions-runner/zshz1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-zshyzsh.delonet-zshz-r1.service` |
| delonet-hjan-r1 | repo `delorenj/HairJangler` (private) | big-chungus, `~/actions-runner/hjan1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-HairJangler.delonet-hjan-r1.service` |
| delonet-cack-r1 | repo `delorenj/cack` (private) | big-chungus, `~/actions-runner/cack1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-cack.delonet-cack-r1.service` |
| delonet-dubc-r1 | repo `delorenj/dub-cue` (private) | big-chungus, `~/actions-runner/dubc1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-dub-cue.delonet-dubc-r1.service` |
| delonet-trin-r1 | repo `delorenj/trinote` (private) | big-chungus, `~/actions-runner/trin1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-trinote.delonet-trin-r1.service` |
| delonet-ivoa-r1 | repo `delorenj/intelliforia-voice-agent` (private) | big-chungus, `~/actions-runner/ivoa1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-intelliforia-voice-agent.delonet-ivoa-r1.service` |
| delonet-wing-r1 | repo `delorenj/Wingman` (private) | big-chungus, `~/actions-runner/wing1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-Wingman.delonet-wing-r1.service` |
| delonet-ltf-r1 | repo `delorenj/lost-things-forge` (private) | big-chungus, `~/actions-runner/ltf1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-lost-things-forge.delonet-ltf-r1.service` |
| big-chungus-earshot | repo `delorenj/earshot` | big-chungus, `~/actions-runner/earshot1` (started through `runsvc-op.sh`) | `self-hosted, Linux, X64, earshot, delonet` | `actions.runner.delorenj-earshot.big-chungus-earshot.service` |
| big-chungus-gruvato, big-chungus (pile-of-dumb-things) | repos `delorenj/gruvato`, `delorenj/pile-of-dumb-things` | big-chungus, `~/actions-runner/gruvato1` (others not inventoried here) | see `gh api repos/<repo>/actions/runners` | `actions.runner.delorenj-gruvato.big-chungus-gruvato.service` |
| (none) | macOS | -- | -- | planned; iOS builds wait on it |

`delorenj/pjangler` (public) runs all CI on free GitHub-hosted runners since PJAN-164, 2026-10-01; its repo runner delonet-pjan-r1 is retired.

Private repos deliberately left on hosted labels (2026-10-22 sweep):
- `delorenj/codex-desktop-linux`: hourly/daily cron workflows that `sudo apt-get install` and install Nix on the runner, plus `container:` matrix jobs. Not safe on this workstation; disable the workflows or move the repo off the schedule instead of giving it a runner.
- `delorenj/intelliForia-desktop`: one `macos-latest` Tauri release job; waits on the macOS runner.
- `delorenj/tower-of-lost-things`, `green-in-between`, `gruvato`: already on self-hosted labels (macOS jobs use their own mommymac runners).

Workflows target Linux with `runs-on: [self-hosted, Linux, delonet]`.

## A repo that the runners cannot see

Org runners serve only repos in their org. A repo under the personal account
(`delorenj/...`) cannot use them, because GitHub has no user-level runners. Give
it a repo-level runner on big-chungus:

```bash
D=~/actions-runner/<short>1; mkdir -p "$D" && cd "$D"
V=$(gh api repos/actions/runner/releases/latest --jq .tag_name | tr -d v)
curl -fsSL -o r.tgz "https://github.com/actions/runner/releases/download/v$V/actions-runner-linux-x64-$V.tar.gz" && tar xzf r.tgz && rm r.tgz
T=$(gh api -X POST repos/<owner>/<repo>/actions/runners/registration-token --jq .token)
./config.sh --unattended --url https://github.com/<owner>/<repo> --token "$T" \
  --name delonet-<short>-r1 --labels delonet --work _work
sudo ./svc.sh install delorenj && sudo ./svc.sh start
gh api repos/<owner>/<repo>/actions/runners --jq '.runners[] | [.name,.status] | @tsv'
```

Then add a row to the inventory above.

Gotchas on this host (found bringing up deckard, 2026-10-22):
- The service captures the installing shell's PATH, where mise shims precede
  `~/.cargo/bin` and `rustup` is a broken shim. A Rust repo's runner needs
  `PATH=$HOME/.cargo/bin:...` in its `.env` (see `~/actions-runner/deck1/.env`),
  then `sudo ./svc.sh stop && sudo ./svc.sh start`.
- svgme's runner has `~/.cargo/bin` first in its `.env` PATH (same Rust shim problem).
- mise refuses an untrusted `mise.toml`: set `MISE_TRUSTED_CONFIG_PATHS: ${{ github.workspace }}` in the workflow env.
- `actions/setup-python` has no CPython build for Ubuntu 25.10 ("version 3.11 ... was not found"). Provision Python with uv instead:
  `uv venv --seed --python 3.11 "$RUNNER_TEMP/venv"` then `echo "$RUNNER_TEMP/venv/bin" >> "$GITHUB_PATH"` (svgme, 2026-10-22).
- Docker's default address pools on big-chungus are fully subnetted, so `docker network create` fails. A
  `services:`/`container:` block cannot start; use a plain `docker run -p` step and remove it in an `if: always()` step. Moving the repo into an org that already
has runners also works, but that is the user's call.

## macOS (planned)

Register the osx-arm64 runner package on an always-on Mac. Give it labels
`self-hosted, macOS, ARM64, delonet-mac`, and install it with `./svc.sh install`
so launchd runs it. A laptop that sleeps makes a poor runner. iOS signing uses an
App Store Connect API key from 1Password, never a login keychain someone has to
unlock.

**Candidate: Damian's Mac Studio** (M3 Ultra, 96 GB, macOS 26.3).
- SSH: `ssh hellosubconscious@damians-mac-studio.tuxedo-morpho.ts.net`, the `damiconn` alias in
  `$ZC/remote-hosts.zsh`.
- The account is logged in at the console, so a user LaunchAgent works. It is an admin, but sudo
  needs a password.
- The Mac never sleeps and auto-restarts.
- **Blocked 2026-09-26: the Mac had no outbound TCP at all.** Ping worked, but TCP to every port
  (22/53/80/443, github.com and 1.1.1.1 alike) failed at once, from SSH and from a GUI LaunchAgent.
  The application firewall was off and no filter extension was loaded. There was a second default
  route through the Tailscale utun, so suspect a dead Tailscale exit node or a block at the gateway
  (192.168.12.1).
- Xcode is not installed, only the Command Line Tools.
