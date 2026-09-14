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
| `firetv_living` | living_room | Hisense Fire TV (AFTHA001) | `firetv_adb` | **authorized, live** |

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

ADB is authorized (2026-09-13). The device reports `model AFTHA001`, name `hailey`.

**Power on is `KEYCODE_WAKEUP`, not `KEYCODE_POWER`.** POWER is a toggle — sending it to a
set that is already awake turns it *off*, which is the opposite of what "turn it on" should
ever do. WAKEUP is idempotent.

`mWakefulness` from `dumpsys power` is the reliable awake signal.

Package names are **device-verified** as of 2026-09-13, read off this set's own
`pm list packages`. Two store-verified guesses were wrong here, which is why the list is
now taken from the device: `com.wbd.stream` (the current Max package everywhere else) is
not installed — this TV ships the older `com.hbo.hbonow` — and Spotify is an
Amazon-wrapped `com.amazon.spotify.mediabrowserservice`, not `com.spotify.tv.android`.

**Prime Video has no package at all on this device.** It is served through the launcher
rather than as an app, so there is deliberately no `prime` entry; adding one would produce
a launch that silently does nothing.

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

What the panel reports over CEC (`dumpsys hdmi_control`), read 2026-09-13:

| Port | Device |
|---|---|
| 1 (ARC) | `Bose TV Spkr` — a soundbar, not otherwise in the house map |
| 4 | `Living Room S…` — a playback device, almost certainly the SHIELD |
| 2, 3 | nothing reporting; the Xbox was presumably off |

`dumpsys tv_input` separately exposes `HW4`–`HW7` plus `HDMI300004` and `HDMI400008`.
The `HDMI<n>0000x` ids encode the CEC physical address — `HDMI400008` is `0x4000` (port 4),
`HDMI300004` is `0x3000` (port 3).

**The Xbox is on `HDMI400008` (port 4). Confirmed by observation, and it contradicted the
obvious inference.** Powering the Xbox on made `HDMI300004` appear in `tv_input`, which
looked like a clean signal that it sat on port 3. It did not. With the owner switching to
the Xbox on the remote, the panel's own logcat named the live input as
`HDMIInputService/HDMI400008` — port 4 — three times and nothing else. The `HDMI300004`
appearance was coincidence.

CEC labels port 4 `Living Room S`, a Playback device, which reads like the SHIELD and is
misleading. Trust the observation over the label: when the Xbox was the live input, the
SHIELD was simultaneously unresponsive to a cast connect, and the Xbox was up and pinging.

The SHIELD's port is still unknown. Repeat the exercise with it awake and the Xbox off.

**Do NOT try to switch inputs with a TIF passthrough intent on Fire OS.** The obvious

    am start -a android.intent.action.VIEW -d 'content://android.media.tv/passthrough/<inputId>'

does not reach the HDMI input. Amazon claims that URI —
`cmd package resolve-activity` shows it resolving to
`com.amazon.tv.livetv.TvChannelsPlayerActivityAlias` — so it opens Amazon's Live TV
surface and lands on whatever live-TV provider is configured. Tried once on the real set:
it launched Fubo instead of switching inputs. Restore with `KEYCODE_BACK` then
`KEYCODE_HOME`.

The reliable read is `mCurrentInputId` from `dumpsys tv_input` — so the cheapest way to
map a port is to have someone select the input on the remote and then read it back, rather
than switching blind.

"Put on the Xbox" is now **one step from working**: the input is known and the panel is
authorized, but no tool exposes `House.find_source()` yet — the model and resolution are
implemented and tested, and nothing calls them. Note that switching still cannot use a TIF
passthrough intent (above); the working mechanism has not been established. Neither the Xbox
(`xbox_smartglass`, UDP 5050) nor the PS5 (`ps5_remoteplay`, UDP 9302, wake needs PSN
registration and a PIN) has a client implemented.

The PS5 answers discovery even in rest mode — `HTTP/1.1 620 Server Standby` — which is how
it was found while the TV it is plugged into was powered off.
