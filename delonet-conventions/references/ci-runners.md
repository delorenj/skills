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
| delonet-dsid-r1 | repo `delorenj/docsidian` (private) | big-chungus, `~/actions-runner/dsid1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-docsidian.delonet-dsid-r1.service` |
| big-chungus-earshot | repo `delorenj/earshot` | big-chungus, `~/actions-runner/earshot1` (started through `runsvc-op.sh`) | `self-hosted, Linux, X64, earshot, delonet` | `actions.runner.delorenj-earshot.big-chungus-earshot.service` |
| big-chungus-gruvato, big-chungus (pile-of-dumb-things) | repos `delorenj/gruvato`, `delorenj/pile-of-dumb-things` | big-chungus, `~/actions-runner/gruvato1` (others not inventoried here) | see `gh api repos/<repo>/actions/runners` | `actions.runner.delorenj-gruvato.big-chungus-gruvato.service` |
| (none) | macOS | -- | -- | planned; iOS builds wait on it |

`delorenj/pjangler` (public) runs all CI on free GitHub-hosted runners since PJAN-164, 2026-10-01; its repo runner delonet-pjan-r1 is retired.

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

Then add a row to the inventory above. Moving the repo into an org that already
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
