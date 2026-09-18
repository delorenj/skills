---
name: delonet-parental-controls
description: Parental control enforcement, DNS filtering, and device network blocking across DeLoNET and DeLoHome. Covers AdGuard Home client binding and service blocks, Netgear RS700 router Access Control, Tailscale offline traps, and managing restrictions on kids' devices (Chase's TV, Chase's Phone, Ava's TV, Bedroom TV).
---

# DeLoNET Parental Controls & Device Access

Enforces content filtering, screen time limits, and hardware-level network blocks across the DeLorenzo homelab network (`DeLoNET`).

## Two Enforcement Layers

Parental controls operate on two distinct layers. When a restriction fails or is bypassed, it is almost always because the enforcement was applied only at the DNS layer while the device was using a direct or unmanaged network path.

```
Device Request
  │
  ├─ Layer 1: Hardware / MAC Access Control (Netgear RS700 Router)
  │    └─ State = Block -> 100% packet loss at the Wi-Fi/switch layer (total internet cut)
  │    └─ State = Allow -> Traffic passes to LAN / WAN
  │
  └─ Layer 2: DNS & Content Filtering (AdGuard Home + Tailscale MagicDNS)
       ├─ Tailnet query (100.x.x.x) -> Tailscale MagicDNS -> AdGuard Home (100.66.29.76:53)
       └─ LAN query (192.168.1.x)  -> AdGuard Home (192.168.1.12:53)
            └─ Matched by Client ID (IP, MAC, hostname) -> Blocked Services & Custom User Rules
```

---

## Layer 1: Netgear RS700 Router Access Control

When a device must be locked out immediately or when it bypasses local DNS (e.g. via hardcoded Google DNS `8.8.8.8`), block it at the router hardware layer.

- **Router**: Netgear RS700 (firmware V1.0.11.8) at `192.168.1.1`.
- **Credentials**: `op://DeLoSecrets/Wireless Router/base station password` (username `admin`).
- **Mechanism**: `DeviceConfig:1` SOAP action `SetBlockDeviceByMAC` with `NewAllowOrBlock: Block|Allow`.

### Quick Access Control CLI
Use [`~/docker/scripts/chase-tv.sh`](file:///home/delorenj/docker/scripts/chase-tv.sh):

```bash
# Check status:
~/docker/scripts/chase-tv.sh status

# Block the TV at the router (cuts all Wi-Fi traffic):
~/docker/scripts/chase-tv.sh block

# Restore network access:
~/docker/scripts/chase-tv.sh allow
```

---

## Layer 2: AdGuard Home DNS & Service Filtering

- **Container**: `adguard` running on `big-chungus` (`192.168.1.12:53` / `100.66.29.76:53`).
- **Config & Work**: `/home/delorenj/docker/stacks/utils/adguard/` (`conf/AdGuardHome.yaml`).
- **Admin API**: `http://172.19.0.51:6767` (internal container port).
  - Auth: `admin` / `tailscale-adguard-2024` (see `setup-adguard-tailscale.sh`).
- **Blocked Services**: Supports granular category blocking (`youtube`, `roblox`, `tiktok`, `twitch`, etc.).

### Managing Client Bindings via API
To update or verify a client in AdGuard:

```bash
# Query clients:
curl -s -u admin:tailscale-adguard-2024 http://172.19.0.51:6767/control/clients | jq .

# Update client:
curl -s -u admin:tailscale-adguard-2024 -X POST http://172.19.0.51:6767/control/clients/update \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chase'\''s Android TV",
    "data": {
      "name": "Chase'\''s Android TV",
      "ids": ["100.82.60.86", "chase-tv", "192.168.1.29", "38:c8:04:51:08:41", "android-3"],
      "tags": ["device_tv", "device_other"],
      "blocked_services": ["youtube", "roblox"],
      "filtering_enabled": true,
      "use_global_blocked_services": false,
      "use_global_settings": false
    }
  }'
```

---

## Known Child Device Inventory

| Device | Room / User | Identifiers (IP / MAC / Tailscale) | Active Restrictions | Enforcement Method |
|---|---|---|---|---|
| **Chase's TV** | Chase's Room | `192.168.1.29`<br>`38:C8:04:51:08:41`<br>`100.82.60.86` (`chase-tv`) | YouTube, Roblox | Router MAC block (`chase-tv.sh`) + AdGuard client block |
| **Chase's Phone** | Chase | `100.76.87.44` (`chase-phone`) | YouTube, Roblox | AdGuard client block |
| **Ava's TV** | Ava's Room | `192.168.1.42`<br>`a4:ce:da:5c:ad:c8`<br>`ava-tv`, `lgwebostv` | YouTube, Roblox | AdGuard client block |
| **Bedroom TV** | Master Bedroom | `192.168.1.26` | Roblox | AdGuard client block |

---

## Critical Gotchas

1. **The Tailscale Disconnect Trap**:
   Android TVs and phones can disconnect from Tailscale or have the VPN toggle switched off. When disconnected, the device uses local DHCP Wi-Fi directly. If an AdGuard rule only names the Tailscale node (`100.x.x.x` or hostname), all restrictions are completely bypassed. **Always bind both the LAN IP and MAC address** in AdGuard Home.

2. **Hardcoded Google DNS on Smart TVs**:
   Android TV / Google TV devices have Google DNS (`8.8.8.8`, `8.8.4.4`) hardcoded in Google Play Services. If local DNS blocks YouTube, the YouTube app often silently falls back to 8.8.8.8 over port 53 or uses DoT/QUIC. If DNS-level blocking fails, use the **Router Hardware/MAC Block** (`chase-tv.sh block`).

3. **Parent Whitelists in AdGuard**:
   AdGuard's `user_rules` contains explicit bypass rules for parent devices:
   - `pottybarron` / `pottybarron-s26` (`Jarad's S26 Ultra`)
   - `carries-macbook-air`
   - `mommys-iphone`
   - `big-chungus` (`192.168.1.12`, `100.66.29.76`, `127.0.0.1`)
   Global block rules (e.g. `||youtube.com^`) will block children and unmapped devices without breaking parent access as long as the `@@||*^$client=...` rules remain in place without being overridden by `$important`.
