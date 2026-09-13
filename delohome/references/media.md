# Media and casting

Getting a specific thing playing on a specific screen.

```bash
delohome media                                  # the 8 tools
delohome media list-media-targets               # what each room can actually do
delohome media play 'The Big Lebowski' dommy
delohome media now-playing
```

## What each room can actually do

This is the part that determines whether a request is satisfiable at all.

| Room | Cast target | Title control |
|---|---|---|
| living_room | NVIDIA SHIELD | full, and it is an Android TV so apps can be navigated once paired |
| chase | Google TV | full, same |
| dommy, playroom, office | Chromecast | DeLoFlix / YouTube / Plex exact; commercial apps **launch-only** |
| bedroom, ava | *none* | display control only — see [displays.md](./displays.md) |
| kitchen | Google Home | audio only |

**A plain Chromecast has no input channel.** We can open Netflix on Dommy's TV; we cannot
then pick a title inside it, because there is no remote protocol to navigate with. Say so
rather than implying the title will start playing. `list-media-targets` reports
`title_control` per room precisely so an agent never over-promises.

**The bedroom has no cast target at all** since the SHIELD moved to the living room. The
Samsung is a panel, not a cast device. `cast_target()` says this plainly instead of
failing obscurely.

## DeLoFlix (Jellyfin)

The one source we own, and therefore the only one where an exact title can be put on any
screen in one shot — we hand the device a direct stream URL and the Default Media Receiver
plays it. 331 titles.

```bash
delohome media search-library lebowski
delohome media play 'The Big Lebowski' dommy
```

`play` tries the library first; a bare service name ("netflix") launches that app instead,
and the result says which happened.

Streams use the **LAN** URL (`http://192.168.1.12:8096`), never `https://movies.delo.sh` —
a Chromecast fetching the stream should not hairpin out through Cloudflare and Traefik to
reach a box on its own switch.

Jellyfin answers **401 for any auth problem**, including a valid token written into the
wrong database. On 10.11 the running server reads `config/data/data/jellyfin.db`; the
un-nested `config/data/jellyfin.db` is a 10.10 leftover the server ignores entirely, so
editing it looks like it worked and does nothing.

## Cast app ids

**Never invent one, and never trust `GET_APP_AVAILABILITY` to identify one.** Availability
proves an id is registered *somewhere* — not which service it belongs to, nor whether it is
still current. Two checks are needed:

1. `https://clients3.google.com/cast/chromecast/device/app?a=<APPID>` → `.display_name`
   (strip the `)]}'` prefix before parsing).
2. Membership in `enabled_app_ids` from
   `https://clients3.google.com/cast/chromecast/device/baseconfig`.

`mise run verify:appids` does both for all 16 and fails on a mismatch.

| App | Verified id |
|---|---|
| Netflix | `EF67CA5A` |
| Hulu | `3EC252A5` |
| Max | `C5B95AD4` (fallback after a rebrand: `3A2AA214`) |
| Disney+ | `C3DE6BC2` |
| Prime Video | `17608BC8` |
| YouTube | `233637DE` |
| Plex | `9AC194DC` |
| Jellyfin | `F007D354` |
| Default Media Receiver | `CC1AD845` |

Three ids in wide circulation are wrong and will silently do the wrong thing:

- `A9BCCB7C` — cited everywhere as HBO Max, actually **Yle Areena**, a Finnish broadcaster.
- `B3DCF968` — cited as Hulu, actually **Twitch**. Asking for Hulu would launch Twitch.
- `CA5E8412` — genuinely resolves to "Netflix" but is **deprecated and absent from
  `enabled_app_ids`**. It reports available on older Chromecasts and unavailable on both
  Android TV devices, which reads convincingly as "Chase's TV doesn't have Netflix". It does.

## Cast protocol gotchas

**No mDNS discovery.** `get_chromecasts()` returns zero devices on big-chungus — the
bundled python-zeroconf loses to the system avahi daemon that already holds the socket. We
connect directly by `(ip, uuid)` from the house map, which is faster and deterministic.
Run `mise run discover` when a lease moves.

**Never gate a cast on availability.** The Kitchen speaker answers `APP_UNAVAILABLE` for
*every* app id — including `CC1AD845`, immediately after successfully playing through
`CC1AD845`. Using availability as a precondition would silently refuse to play in the
kitchen.

**Do not filter on `cast_type`.** Chase's TV reports `cast_type=None` over mDNS; the
obvious `if cast_type == "cast"` check drops a fully working device.

**`stream_type` must be set to `BUFFERED`.** pychromecast defaults to `LIVE`, which makes
the receiver hide the scrubber and refuse to seek on a finite file.

Log noise: the receiver replies to availability probes with `responseType` where
pychromecast expects `type`, so its `ReceiverController` raises a handled `KeyError` and
prints a full traceback per call. Suppressed by `_quiet_socket_logs`; if you see it, it is
cosmetic.
