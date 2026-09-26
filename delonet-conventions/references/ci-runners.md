# CI runners (GitHub Actions)

GitHub Actions runs on **self-hosted runners only**. Never write
`runs-on: ubuntu-latest`, `macos-*` or any other GitHub-hosted label. Hosted
minutes are billed, the budget is $0, and a hosted job just sits unstarted with
"recent account payments have failed or your spending limit needs to be
increased".

## Inventory (verified 2026-09-26)

| runner | scope | host | labels | service |
| --- | --- | --- | --- | --- |
| delonet-r1, r2, r3 | org `AutomaticAI-io` | big-chungus, `~/actions-runner/r{1,2,3}` | `self-hosted, Linux, X64, delonet` | `actions.runner.AutomaticAI-io.delonet-r{N}.service` |
| delonet-gib-r1 | repo `delorenj/green-in-between` | big-chungus, `~/actions-runner/gib1` | `self-hosted, Linux, X64, delonet` | `actions.runner.delorenj-green-in-between.delonet-gib-r1.service` |
| (none) | macOS | -- | -- | planned; iOS builds wait on it |

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
