# The house map

`~/code/DeLoHome/config/home.yaml` is the single source of truth for what exists and what
a person means when they name it. Everything — lights, casting, panels — resolves through
it. A malformed map raises at server start rather than at first tool call, so a typo shows
up when you start it, not when someone wants the lights.

**The old `~/code/HomeAssistant` config is stale and actively misleading.** It has the Hue
bridge at `.125` (it is `.13`), Z-Wave on `ttyUSB1` (it is `ttyUSB0`), and a `zwcfg`
describing a controller that no longer exists. Do not reconcile against it.

## Sections

```yaml
rooms:            # what a person says -> a room key
cast_devices:     # things media can be pushed TO
displays:         # the panels themselves (not cast targets)
sources_hdmi:     # boxes plugged into a panel (consoles, streamers)
zwave_pending:    # installed but unpaired switches
sources:          # media sources (Jellyfin/DeLoFlix)
```

Twelve rooms: bedroom, dommy, chase, ava, playroom, piano_room, living_room, office,
kitchen, foyer, driveway, front_porch.

## Room resolution

The ladder, in order: normalize → exact alias → filler-stripped alias → substring (longest
wins) → fuzzy at cutoff 0.72. This is what makes speech work — `"bedrom"`, `"chace's
room"` and `"dommeys tv"` all land correctly.

**Machine-supplied names must pass `fuzzy=False`.** A name that comes off a device is a
canonical string, not something a person said. The Hue bridge's "Piano Room" scored close
enough to "playroom" to fuzzy-match it, which would have pointed the playroom's lights at
the piano. `resolve_room()` takes the flag; the Hue mapping passes `False`.

Add an alias whenever the household says something the map does not know. That is the fix,
not loosening the cutoff — a looser cutoff is how "Piano Room" became "playroom".

## `name` vs `mdns_name`

A cast device's name lives in its *own settings* and is what it advertises over mDNS. It
goes stale when a device moves. The SHIELD moved from the bedroom to the living room and
still calls itself "Bedroom Shield":

```yaml
- name: Shield              # what we and the household call it
  mdns_name: Bedroom Shield # what the device still claims
```

`discover` matches on the advertised name and prints
`Shield (advertises 'Bedroom Shield')`. Renaming without `mdns_name` would make discovery
report one device missing and a stranger one new, on every run, forever.

## Discovery and drift

```bash
mise run discover
```

Uses `avahi-browse`, not python-zeroconf — the bundled zeroconf returns zero devices on
this host because the system avahi daemon already holds the mDNS socket.

It prints a **diff and does not rewrite the map**. The map carries hand-written aliases and
room assignments no scan can infer, so a human decides what to apply. `NEW`, `CHANGED` and
`MISSING` are all reported; `MISSING` usually just means a device is powered off.

## Adding a device

1. Find it. `mise run discover` for cast devices; for panels, scan control ports —
   3000/3001 is LG webOS, 8001/8002 is Samsung Tizen, 5555 is ADB (Fire TV / Android TV).
   SSDP (`ssdp:all` on 239.255.255.250:1900) gives friendly names and manufacturers without
   any auth.
2. Add the entry with its IP **and** UUID (cast) or IP and MAC (panel). The MAC is needed
   for wake-on-LAN and, for a Samsung, is only obtainable while the set is awake.
3. Give it aliases people actually use.
4. `delohome list-rooms` to confirm resolution.

**ARP does not work on big-chungus.** A bogus static route wins over the kernel link route:

```
192.168.1.0/24 via 192.168.1.1 dev enp12s0 proto static metric 100
192.168.1.0/24 dev enp12s0 proto kernel scope link src 192.168.1.12 metric 100
```

`ip route get 192.168.1.11` returns `via 192.168.1.1` — the host sends traffic for its own
subnet to the gateway and never populates the neighbour table. `ping` then `ip neigh`
silently returns nothing, and so does `nmap -sn -PR`. Use a raw scapy ARP broadcast pinned
to `enp12s0` instead, and include a host with a known-good MAC as a control.

## Validation

`House._validate()` fails at load on any dangling reference: a room pointing at a cast
device or display that does not exist, or an HDMI source pointing at a room or panel that
does not. Tests also assert every cast device has both an IP and a UUID, since without
mDNS there is no other way to connect.
