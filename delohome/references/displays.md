# Displays — the TV panels themselves

Panel control: power, volume, HDMI input, and launching apps *on the set*. To play a
specific title, use [media.md](./media.md) instead.

```bash
delohome displays                               # the 11 tools
delohome displays list-displays                 # protocol + paired state per panel
delohome displays display-status bedroom
```

## The four panels

| Panel | Room | Model | Protocol | State |
|---|---|---|---|---|
| `samsung_bedroom` | bedroom | UN65RU8000FXZA | `samsung_ws` | **paired, live** |
| `lg_office` | office | OLED48CXPUB (CX 48" OLED, fw 5.6.2) | `lg_webos` | not paired |
| `lg_ava` | ava | 43UP8000PUA (fw 6.5.3) | `lg_webos` | not paired |
| `firetv_living` | living_room | Hisense Fire TV | `firetv_adb` | not authorized |

Pairing procedures are in [setup.md](./setup.md).

## Samsung (bedroom) — working

A **2019 RU8000**, not the UN65KS8500 the old Home Assistant config claimed; that was a
different television and the claim is simply stale. At `192.168.1.4`, Developer Mode on,
Tizen SDB open on 26101.

`TokenAuthSupport` is true, so it is **port 8002 (wss) with a token** — not the legacy
8001 path, where the handshake is unauthenticated and silently issues no token at all,
which looks fine right up until nothing is authorised.

```bash
delohome displays display-launch-app bedroom netflix
delohome displays display-key bedroom INFO          # KEY_* names
delohome displays display-power bedroom --no-on
```

Reads (`display-status`) use unauthenticated REST on :8001 and work before pairing.

**Samsung TV Plus is not an app on this set.** It lives in the tuner as virtual channels
and cannot be launched with `run_app`. The only route is selecting the TV source and
sending digits:

```bash
delohome displays tune-channel bedroom 1013
```

That is **open-loop** — the TV reports nothing back about what ended up on screen, so
there is no way to confirm the channel took. Say so rather than asserting success.

**Wake-on-LAN is the only way to turn it on.** In deep standby it leaves the LAN entirely:
no ARP, no SSDP, no open port. The MAC (`24:fc:e5:05:d8:4b`) is therefore only obtainable
while it is awake, which is why `mise run samsung:capture` exists. It reports
`networkType: wired` while also reporting that address as `wifiMac`; ARP confirmed it *is*
the address on the wire here, but on a genuinely wired Samsung `wifiMac` is the idle
wireless NIC and a magic packet aimed at it does nothing.

17 Tizen app ids are recorded, and they are **per-model** — do not copy them to another
Samsung.

## LG webOS (office, Ava's room)

**Never pin the port.** The office CX *accepts* a TCP connection on 3000 and then kills the
WebSocket upgrade — it is wss-only on 3001. Ava's UP8000 serves a working socket on both.
A port scan reporting "3000 open" on both sets is therefore actively misleading.
`aiowebostv` negotiates per-TV; let it.

**TLS cannot be verified.** The cert comes from a private LG CA with CN `LGE TV SSG`, not
the IP, so even a pinned CA fails hostname verification against an address. The library
uses `ssl=False`. On a LAN to a known address that is the honest ceiling.

`set_volume` has no upper clamp upstream (`max(0, volume)` only) — 300 would be sent to the
TV verbatim. The client clamps both ends.

`system/getSystemInfo` is the one endpoint answered *before* registration; everything else
returns `401 insufficient permissions (not registered)`.

LG is the only panel that reports its inputs, which makes it the discovery route for the
`hdmi_input` values that are currently null:

```bash
delohome displays list-display-inputs office
```

`display-key` raises for LG — it has no raw key channel here. Use `display-input`,
`display-launch-app` or `display-volume`.

## Fire TV (living room)

Fire OS over ADB on `192.168.1.3:5555`. The RSA keypair **is** the credential: whoever
holds the private key can run arbitrary shell on that TV forever with no further prompt.

**Power on is `KEYCODE_WAKEUP`, not `KEYCODE_POWER`.** POWER is a toggle — sending it to a
set that is already awake turns it *off*, which is the opposite of what "turn it on" should
ever do. WAKEUP is idempotent.

`mWakefulness` from `dumpsys power` is the reliable awake signal.

Package names are store-verified, not device-verified — what is actually installed can only
be confirmed with `delohome displays list-display-apps 'living room'` once ADB is
authorized. Fire OS differs from stock Android TV; Prime Video is preinstalled and primary.

## Two surfaces, one screen

The living room has the Hisense panel **and** the SHIELD plugged into it. They are separate
control surfaces:

- the **panel** (`firetv_adb`) owns power and HDMI input
- the **SHIELD** (cast + Android TV remote) owns content

The bedroom is the same shape with the Samsung and the PS5.

## HDMI sources are modelled but not wired

Xbox One (living room), PS5 (bedroom) and the SHIELD are in the house map as
`sources_hdmi`, with aliases, IPs and MACs. **`hdmi_input` is `null` for all three**, and
deliberately so: which port a box sits on can only be read off a panel we can talk to, and
guessing switches the TV to a dead input.

So "put on the Xbox" is **not yet satisfiable**. It needs two things that do not exist yet:
the panel paired so inputs can be enumerated, and a tool that exposes `House.find_source()`
(the model and resolution are implemented and tested; nothing calls them). Neither the Xbox
(`xbox_smartglass`, UDP 5050) nor the PS5 (`ps5_remoteplay`, UDP 9302, wake needs PSN
registration and a PIN) has a client implemented.

The PS5 answers discovery even in rest mode — `HTTP/1.1 620 Server Standby` — which is how
it was found while the TV it is plugged into was powered off.
