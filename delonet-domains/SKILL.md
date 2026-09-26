---
name: delonet-domains
description: Manage domain registration, transfers, locks, and renewals across Cloudflare Registrar and external registrars (Namecheap) for DeLoNET and homelab domains.
---

# DeLoNET Domain Management

This skill covers inspecting, transferring, renewing, and locking domains across Cloudflare Registrar and external registrars (such as Namecheap) for DeLoNET infrastructure.

## Tooling & Credentials

Domain operations use the bundled CLI tool:
`.agents/skills/delonet-domains/scripts/domain_ctl.py`

Credentials are read on demand from 1Password (`DeLoSecrets` vault):
- Email / Username: `op://DeLoSecrets/Cloudflare/username`
- API Key: `op://DeLoSecrets/Cloudflare/globalAPIToken`
- Default Account: `DeLoNET` (`f68a196c5c84014bb85f8ab97b386994`)

No credentials or plaintext tokens are ever stored in files.

## CLI Usage

From the `infra` repo root:

```bash
# List all domains registered with Cloudflare Registrar
.agents/skills/delonet-domains/scripts/domain_ctl.py list

# Get detailed Cloudflare registrar status and live registry WHOIS
.agents/skills/delonet-domains/scripts/domain_ctl.py info delo.sh

# Initiate a domain transfer into Cloudflare Registrar
.agents/skills/delonet-domains/scripts/domain_ctl.py transfer-in delo.sh <AUTH_CODE>

# Check pending transfer progress
.agents/skills/delonet-domains/scripts/domain_ctl.py transfer-status delo.sh

# Lock or unlock a domain registered with Cloudflare
.agents/skills/delonet-domains/scripts/domain_ctl.py lock <domain>
.agents/skills/delonet-domains/scripts/domain_ctl.py unlock <domain>
```

## Transfer Workflow (e.g., Namecheap to Cloudflare)

To transfer an external domain (e.g. from Namecheap) into Cloudflare Registrar:

### 1. Verification & Pre-flight
- Run `.agents/skills/delonet-domains/scripts/domain_ctl.py info <domain>`.
- **TLD Support Verification**:
  - Cloudflare Registrar supports ~370+ TLDs (including `.com`, `.net`, `.org`, `.app`, `.ai`, and `.io`).
  - **`.sh` is NOT supported by Cloudflare Registrar** (even though Cloudflare DNS supports it). Transfers for `.sh` will fail with `Transfer not supported by the API for this TLD`.
  - Check the active TLD policies at `https://www.cloudflare.com/tld-policies/` before attempting transfers.
- **Nameservers**: Cloudflare requires the domain to be an active zone pointing to Cloudflare nameservers first.
- **Timing & Auto-Renew Grace Period**:
  - The domain should not be within 15 days of expiration or expired.
  - If a domain expired and entered the 45-day `autoRenewPeriod`, **do not transfer yet**. Renew at the losing registrar first, wait 45 days for the renewal credit to settle, then transfer. Otherwise, the registry cancels the renewal year and the transfer may fail or forfeit the year.
- **Domain Lock**: The domain must be unlocked at the current registrar (must not have `clientTransferProhibited`).
- **DNSSEC**: If DNSSEC is enabled or pending, disable it before initiating the transfer.

### 2. Obtain Auth Code
- Log in to Namecheap (or losing registrar).
- Navigate to Domain List → Manage Domain → **Sharing & Transfer**.
- Turn **Domain Lock** to **OFF**.
- Click **AUTH CODE** to retrieve the EPP/authorization code.

### 3. Initiate Transfer
Run:
```bash
.agents/skills/delonet-domains/scripts/domain_ctl.py transfer-in <domain> <AUTH_CODE>
```
*Note: The CLI automatically base64-encodes the auth code as required by Cloudflare's API (`RFC 4648 §4`).*

Cloudflare will charge the account payment method for 1 year at at-cost registry price and extend the domain expiration by 1 year.

### 4. Expedite Transfer Out
- By default, ICANN allows losing registrars up to 5–6 days to release a domain.
- Namecheap sends an email with a transfer approval link.
- Click **Approve** in the Namecheap confirmation email or dashboard to release the domain immediately (completes within ~15–20 minutes).

### 5. Confirm Transfer
Run:
```bash
.agents/skills/delonet-domains/scripts/domain_ctl.py transfer-status <domain>
.agents/skills/delonet-domains/scripts/domain_ctl.py info <domain>
```
Verify that `current_registrar` updates to `Cloudflare` and the lock status is re-enabled.
