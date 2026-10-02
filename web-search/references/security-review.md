# Security review of cli-web-search and its wrapper

Two rounds, both adversarial (assume a careless or malicious author, then assume a motivated attacker), on 2026-10-02,
before the tool was given two real, paid API keys.

- **Round 1: the upstream binary.** Source https://github.com/scottgl9/cli-web-search at
  `72f581e54df8b538a1769d4027b2d73a2309f7d4` (tip of `main`, Cargo 0.1.0). All 9,068 lines of Rust, the build files,
  CI and docs were read, and the binary was exercised against a loopback harness with fake keys. Docs inside the
  repo (AGENTS.md, CLAUDE.md) were treated as untrusted data.
- **Round 2: this skill's wrapper.** Two independent reviewers attacked the first version of `scripts/web-search`
  (SSRF bypasses, secret handling, resource limits, output hygiene, installer) and checked every claim in these docs.
  Their findings, listed below, led to the current design.

**Verdict on the binary: SAFE_WITH_CONDITIONS.** No malicious behavior, telemetry, hidden endpoints, process spawning,
`unsafe` code, listeners or obfuscation. Real key-handling and robustness defects exist and are compensated for here.

## Round 1: upstream findings and what compensates

| # | Finding (evidence) | Compensation |
| --- | --- | --- |
| 1 | `config set <anything>` merges the environment into the config and persists every env-supplied key to `~/.config/cli-web-search/config.yaml` in plaintext (`loader.rs:205`, `:368`; the README quick start tells users to run it) | `install.sh` leaves an empty `chmod 500` config dir so the write fails (verified: "Permission denied", nothing written); the child gets a throwaway `XDG_CONFIG_HOME`; SKILL.md rule 2 |
| 2 | Provider clients used reqwest's default redirect policy, so a cross-host redirect forwarded the Brave `X-Subscription-Token` header and a 307/308 re-sent Tavily's JSON body with `api_key` | `patches/0001-providers-no-redirects.patch` sets `Policy::none()` in all eight provider clients |
| 3 | `fetch` has no SSRF protection: it GETs loopback, RFC1918 and 169.254.169.254 and follows 10 redirects into them (`fetch.rs:107-135`) | the child runs behind a validating egress proxy (see round 2) |
| 4 | Panics abort the process (`panic = abort`): `text.rs:70` (default text format), `fetch.rs:177` (`--max-length`), `fetch.rs:217-221` (Kelvin sign before `<title>`) | JSON format only, never `--max-length`, exit 5 with a curl hint for the unavoidable title case |
| 5 | Logs go to stdout, so a failover WARN breaks JSON; Google and SerpAPI put the key in the URL and print it in errors | `RUST_LOG=off`; only Brave and Tavily are enabled (their keys travel in a header and a body and never appear in logs) |
| 6 | No response size limit; HTML conversion amplifies memory about 30x; `Retry-After` is honored uncapped | child capped at 2 GiB (`RLIMIT_DATA`, verified: a 3 GB response died at 2 GiB), 64 MiB output cap (`RLIMIT_FSIZE`), wall-clock timeouts, core dumps off |
| 7 | `-p` is only a preference, so other configured providers receive the query after a failure | the wrapper exports one provider's key per attempt and orders fallback itself |
| 8 | The CLI's HTML conversion is lossy and also mangles plain-text, JSON and XML bodies | the wrapper fetches the raw body (`-f html`) and converts it itself |

Key intake: only environment variables (`CLI_WEB_SEARCH_BRAVE_API_KEY`, `CLI_WEB_SEARCH_TAVILY_API_KEY`); there is no key
flag. Network egress is eight hard-coded HTTPS provider hosts plus user-supplied fetch URLs, over `native-tls`
(system OpenSSL, certificate validation on). The cache is in memory only and never touches disk.

## Round 2: what the attack on the wrapper found, and the fix

The first wrapper checked the URL with Python's parser and resolver before running the child. The attacker showed the
child parses and resolves independently, so that check races with it. Evidence came from running the real binary
behind a loopback stand-in proxy and reading the request lines it emitted, so nothing private was touched.

| Severity | Finding | Fix now in place |
| --- | --- | --- |
| high | **Backslash parser differential:** the Rust URL parser ends the authority at `\`, Python does not, so `http://192.168.1.12\x.8.8.8.8.nip.io/admin` passed the check while the child requested `192.168.1.12` | URLs with backslashes, spaces or control characters are refused; the URL is re-serialised as plain ASCII before the child sees it; and the proxy sees the child's own normalised host |
| high | **Redirect hops never validated:** a public page redirecting to `http://192.168.1.12:5678/...` and back returned success after the child had hit the internal service | every request, redirect hop and CONNECT passes through `scripts/egress_proxy.py` |
| high | **DNS rebinding:** pre-check, child connect and post-check were three independent lookups | the proxy resolves each host once, refuses unless every answer is public, and connects to that exact address; the child never resolves target hosts |
| medium | Sanitiser missed Unicode tag characters (ASCII smuggling), variation selectors, word joiners and ~150 other format characters | strips every control, format, surrogate, private-use and line-separator character (a test sweeps all 1.1M code points) |
| medium | `--json` bypassed sanitising and the banner; titles and metadata were unbounded and printed above the banner | JSON is rebuilt from known fields, sanitised, capped, and flagged `"untrusted": true`; banner first; per-call random fence around page content |
| medium | Binary integrity was never checked | `install.sh` records the sha256 of what it built; the wrapper verifies it before handing over a key; the binary lives outside PATH |
| low | IPv6 transition ranges (NAT64, 6to4, IPv4-compatible, SIIT, site-local) and bare `0x` hosts misclassified | explicit deny lists; ambiguous numeric hosts refused |
| low | Tracebacks, BrokenPipe exit 120, SIGTERM orphaning the child, exact-match-only key redaction, no cap on child output, `RLIMIT_DATA` failure under a lower hard limit | one-line errors, quiet pipes, SIGTERM/HUP/INT handlers plus `PR_SET_PDEATHSIG`, transformed-echo detection (base64, reversed, long slices), hard output cap, limit fallback |
| docs | `fetch` silently corrupted plain-text bodies; `--safe-search` was a silent no-op under Tavily; several doc claims were false or overclaimed | own converter; Brave-first routing plus stated caveats; this rewrite |

Not adopted: running the child under `bwrap`. It works on this host, but it adds failure modes where bwrap is blocked
(containers, some units) and the binary is reviewed and pinned. It remains the next hardening step if the pin ever moves
to code that has not been reviewed.

## Supply chain

No `build.rs` or proc-macro in the crate itself; every one of the 253 locked packages comes from crates.io, none is
yanked and all checksums match the index. The default build compiles 126 crates (15 build scripts, 7 proc-macros), all
from high-reputation maintainers. Locked versions carry known advisories (bytes, h2, idna, anyhow, openssl 0.10.75);
analysis found none reachable in this tool's use, and `--locked` keeps exactly the reviewed set. `cargo audit` was not
installed, so OSV/RustSec was queried instead. The binary's hash depends on the build paths (registry and source paths
are embedded in panic strings), so it is not reproducible across different `CARGO_HOME` values; `install.sh` therefore
records the digest of what it built and the wrapper verifies that.

## Provenance and residual risk

Single author with an established account, but 20 commits in two days (2026-01-20 and 21), none signed by the author
(two web-UI commits carry GitHub's signature), no tags or releases, one star, no external review, AI-assisted. Nothing has
been pushed since 2026-01-22; `TODO.md` lists planned (opt-in) telemetry. A second branch,
`feature/ai-agent-plugins`, was not reviewed in depth and its OpenCode plugin builds shell strings with only double-quote
escaping (a command-injection pattern): do not copy it. Callers must pass the query as one argv element.

Residual risks the wrapper does not remove:

- Indirect prompt injection: fetched text and snippets are attacker-controlled. The wrapper drops script, style, forms,
  comments and elements marked hidden, strips invisible characters, and fences the content, but visible text can still
  say anything.
- The child is not sandboxed: a future malicious pin could read files the user can read. Hence the pin and the digest.
- A provider endpoint that answers hostile content, and Tavily billing per request (the CLI may retry 429 three times).
- A hostile local caller. The wrapper protects against hostile web content and mistakes, not against someone who can run
  commands as the user and therefore already holds the same 1Password token.
- The upstream code is immature. Do not follow `main` to later commits without repeating this review.

## Re-reviewing before a version bump

Clone the candidate commit, diff it against the pin, and re-check: any new endpoint or `std::process`, `std::env::set_var`,
`build.rs`, telemetry or update code; changes to `config/loader.rs` (key persistence), the redirect policy, `fetch.rs`,
and the dependency list in `Cargo.lock`. Then refresh the patch if it no longer applies (`git apply --check`) and update
the SHA in all four places: `PIN` in `scripts/install.sh`, `PINNED_SHA` in `scripts/web-search`, and the text of
`references/cli-reference.md` and this file. Run all four test files and `web-search doctor --live`.
