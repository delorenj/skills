# Tailscale Audio Forwarding (PulseAudio over Tailnet)

## Problem

When SSH'd into a remote machine (e.g., `big-chungus`), audio from TTS engines (AgentVibes), system sounds, or any PulseAudio client needs to play on the local laptop speakers.

## Solution: PulseAudio TCP over Tailscale

Direct PulseAudio TCP connection over the Tailscale mesh network. No SSH tunnel needed.

### Architecture

```
big-chungus (PipeWire/PulseAudio)
  |
  | PULSE_SERVER=tcp:<tailscale-hostname>:4713
  |
  v
carries-macbook-air.burro-salmon.ts.net:4713
  |
  v
MacBook Air Speakers (sink: 1__2)
```

### Prerequisites

**On the Mac (audio receiver):**

1. Install PulseAudio via Homebrew:
   ```bash
   brew install pulseaudio
   ```

2. Start PulseAudio with TCP module:
   ```bash
   pulseaudio --load="module-native-protocol-tcp port=4713 auth-anonymous=1"
   ```
   Or if already running:
   ```bash
   pactl load-module module-native-protocol-tcp port=4713 auth-anonymous=1
   ```

3. Verify listening:
   ```bash
   lsof -i :4713
   ```

**On the remote machine (audio sender):**

1. Set environment variables (add to `$ZC/aliases.zsh` or `.zshrc`):
   ```bash
   export PULSE_SERVER=tcp:carries-macbook-air.burro-salmon.ts.net:4713
   export PULSE_SINK=1__2
   ```

2. Set default sink to MacBook speakers:
   ```bash
   PULSE_SERVER=tcp:carries-macbook-air.burro-salmon.ts.net:4713 pactl set-default-sink "1__2"
   ```

### Verification

```bash
# Check connection
PULSE_SERVER=tcp:carries-macbook-air.burro-salmon.ts.net:4713 pactl info

# List available sinks
PULSE_SERVER=tcp:carries-macbook-air.burro-salmon.ts.net:4713 pactl list short sinks

# Play test sound
PULSE_SERVER=tcp:carries-macbook-air.burro-salmon.ts.net:4713 paplay --device="1__2" /usr/share/sounds/freedesktop/stereo/bell.oga
```

### Known Sinks on Mac

| Sink ID | Name | Description |
|---------|------|-------------|
| 0 | Channel_1__Channel_2 | Background Music (virtual, no output) |
| 1 | Channel_1__Channel_2.3 | Background Music (UI Sounds) |
| 2 | 1__2 | MacBook Air Speakers (USE THIS) |
| 3 | Channel_1 | Microsoft Teams Audio |

### Gotchas

1. **Default sink matters**: Without `PULSE_SINK=1__2`, audio routes to sink #0 ("Background Music"), a virtual device with no audible output.
2. **`xcb_connection_has_error`**: This is an X11/display error, not an audio error. Ignore it.
3. **Port confusion**: PulseAudio uses `4713`, not `4173`. Easy typo.
4. **Tailscale direct > SSH tunnel**: Skip `-R` reverse tunnel complexity. Tailscale gives direct host-to-host connectivity.
5. **Auth**: Use `auth-anonymous=1` for Tailnet-only access. Tailscale ACLs provide the security boundary.

### Why Tailscale Direct (not SSH tunnel)

| Approach | Pros | Cons |
|----------|------|------|
| SSH `-R` tunnel | Works without Tailscale | Extra port mapping, reconnect breaks tunnel |
| Tailscale direct | Persistent, no tunnel management | Requires both machines on tailnet |

Tailscale direct wins because both machines are already on the tailnet, and the connection survives SSH disconnects.

### Related

- AgentVibes TTS: Uses PulseAudio for playback, benefits automatically from this setup
- Shell context independence: `PULSE_SERVER` must be set in the execution environment, not just interactive shell
