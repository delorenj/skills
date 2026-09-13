# Lights

Two technologies, one domain. Hue is live and does the work today; Z-Wave has a healthy
controller and four switches that are physically on the wall but not yet paired to it.

```bash
delohome lights                      # the 7 tools
delohome lights list-lights          # what exists and its current state
```

## Hue

Paired 2026-09-10. Eight rooms on the bridge at `192.168.1.13`, twelve bulbs, 129 scenes.

```bash
delohome lights set-lights bedroom --on -b 40 -k 2200
delohome lights list-scenes --room bedroom
delohome lights activate-scene 'Savanna sunset' --room bedroom
```

**Act on the room, not the bulbs.** A Hue room owns a `grouped_light` *service*, and that
is what `set_lights` writes to. Addressing bulbs individually works but is N calls, is not
atomic, and leaves the room's own reported state stale — so the next read disagrees with
what you just did.

**Units are Hue's, not yours.** Brightness is 0–100, not 0–255. Colour temperature is
mired (mirek), clamped 153–500; the CLI takes kelvin and converts, so 2200 is candlelight
and 6500 is daylight.

**Always pass `room` to a scene.** Scene names repeat across rooms — "Relax" exists in
most of them — and without a room the first match wins, which will be the wrong room.

### Scene names lie; read the values

Measured on the bedroom set, because a name is not a description:

| Scene | What it actually is | Default brightness |
|---|---|---|
| Relax | flat warm white, 2237K — the warmest CT in the room | 57% |
| Savanna sunset | true amber/orange on 3 of 5 lights | 78% |
| Chill Janglers | warm white 2278K but full blast | 100% |
| Dimmed | 2725K — *cooler* than it sounds | 30% |
| Tropical twilight | gold with one white light mixed in | 48% |
| **Hot Toddy** | **not warm** — contains two magenta lights, `rgb(255,8,255)` | 40–74% |
| Movie Janglers | three lights off, two at 2257K | 34% |

For "warm and cozy", activating `Savanna sunset` then dimming to ~45% reads better than
any single scene: the scene supplies amber depth, the dim supplies cosiness.

To check a scene before trusting its name, read `.actions[].action.color.xy` off
`/clip/v2/resource/scene` and convert to RGB.

### Rooms with zero bulbs

`Chase's Room`, `Playroom` and `Living Room` are defined on the bridge but currently hold
no lights. `list-lights` reports them with `light_count: 0` — that is real, not an error.

## Z-Wave

Controller: a 700-series stick on `/dev/serial/by-id/usb-Silicon_Labs_CP2102N_...`,
reached through a `zwave-js-server` sidecar. `delohome lights zwave-status` returns
`{available: false, ...}` when the sidecar is down, which is the normal state unless
`mise run up` has been run.

**The four switches must be EXCLUDED before they can be INCLUDED.** They are still bonded
to a dead controller (HomeID `0x0184EC30`), and a device that believes it already belongs
to a network refuses to join another. Any controller can exclude any device regardless of
which network owns it — and for the GE ZW4001 that is the *only* route, because it has no
local factory-reset gesture at the switch.

```
delohome lights zwave-recover-device 'Garage Spotlight' --step exclude
delohome lights zwave-recover-device 'Garage Spotlight' --step include
```

Pending: Garage Spotlight (driveway), Front Porch, Foyer Lamp, Bedroom Ceiling Fan Lights.

**Tap the paddle once, quickly — press and release.** Holding is the dim/brighten gesture
and pairs nothing. This is the same action for both steps and all four devices.

These are pre-Z-Wave-Plus devices (300-series stacks) supporting neither S2 nor, in
practice, S0, so zwave-js completes an insecure pair silently: the security-grant and
DSK-PIN callbacks never fire. That is expected here, not a failure.

**Do not regenerate the S2 keys.** They are baked into every securely-paired device at
pairing time; rotating them orphans everything secure in the house. `mise run zwave:keys`
refuses if the 1Password item already exists, for exactly this reason.

Once a device is recovered there is still no tool to toggle it — `ZWave.set_switch()` and
`set_dimmer()` are implemented on the client but not yet exposed as MCP tools.

## When it goes wrong

| Symptom | Cause |
|---|---|
| `list-lights` notes the bridge is not paired | The app key is missing. `mise run hue:pair`, press the round button. |
| Hue call raises a JSON decode error | An unauthorized CLIP v2 call returns **HTML**. Check status before parsing; the key was probably revoked in the Hue app. |
| Pairing "succeeds" but there is no key | Pairing failure returns **HTTP 200** with `error.type == 101`. Branch on that integer, never on status or the localizable description. |
| A room turns on but reports the old state | Something wrote to bulbs instead of the room's `grouped_light`. |
| `zwave-status` says unavailable | The sidecar is not running. `mise run up`. |
