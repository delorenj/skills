# Examples, Patterns & Templates

**Table of Contents**

**Script Templates:**
- [Complete MIDI Controller Template (class-based)](#complete-midi-controller-template-class-based)

**MIDI Controller Patterns:**
- [MIDI Learn with Hardware Feedback](#midi-learn-with-hardware-feedback)
- [Hardware LED Feedback Display](#hardware-led-feedback-display)
- [Pattern-based Track Routing](#pattern-based-track-routing)
- [Two-Way Sync with Hardware](#two-way-sync-with-hardware)
- [Custom Sysex Handling](#custom-sysex-handling)

**Piano Roll & Step Sequencer Patterns:**
- [Scale Enforcer](#scale-enforcer)
- [Batch Note Quantization](#batch-note-quantization)
- [Grid Beat Filler (step sequencer)](#grid-beat-filler-step-sequencer)

**Advanced Patterns:**
- [Performance Monitoring](#performance-monitoring)
- [Pattern-Based Automation Engine](#pattern-based-automation-engine)

**Debugging and Testing:**
- [ScriptLogger Class](#scriptlogger-class)
- [Testing MIDI Input](#testing-midi-input)

---

## Script Templates

### Complete MIDI Controller Template (class-based)

A professional class-based MIDI controller script template. Wraps FL Studio's
global callback functions into a controller class for cleaner state management
and separation of concerns.

```python
# name=My Professional Controller
# description=Complete MIDI controller template

import device
import mixer
import transport
import channels
import ui
import general

class MIDIController:
    def __init__(self):
        self.initialized = False
        self.cc_map = {}

    def on_init(self):
        if not device.isAssigned():
            print("No MIDI device assigned!")
            return

        print(f"Initialized: {device.getName()}")
        self.initialized = True

        # Send welcome message
        device.midiOutMsg(0xB0, 0, 121, 0)

    def on_deinit(self):
        print("Script shutting down")

    def on_midi_cc(self, cc_num, value):
        """Handle CC messages"""

        # Volume CC (CC 7)
        if cc_num == 7:
            volume = value / 127.0
            mixer.setTrackVolume(mixer.trackNumber(), volume)
            return True

        # Pan CC (CC 10)
        if cc_num == 10:
            pan = (value / 127.0) * 2.0 - 1.0
            mixer.setTrackPan(mixer.trackNumber(), pan)
            return True

        return False

    def on_midi_note(self, note_num, velocity):
        """Handle note messages"""
        # Map pads to tracks
        track = note_num % 8
        mixer.setActiveTrack(track)
        return True

# Global controller instance
controller = MIDIController()

def OnInit():
    controller.on_init()

def OnDeInit():
    controller.on_deinit()

def OnControlChange(msg):
    controller.on_midi_cc(msg.data1, msg.data2)

def OnNoteOn(msg):
    controller.on_midi_note(msg.note, msg.velocity)
```

---

## MIDI Controller Patterns

### MIDI Learn with Hardware Feedback

Implements a MIDI learn mode where CC 122 toggles learn mode, stores mappings,
and sends confirmation back to the hardware controller.

```python
import device
import mixer

# Store learned CCs
cc_map = {}

def processMIDICC(eventData):
    # If CC 122 (local control) = learn mode
    if eventData.controllerNumber == 122:
        # Store CC to track mapping
        cc_map[eventData.controllerNumber] = 0

        # Send back confirmation to hardware
        device.midiOutMsg(0xB0, 0, 122, 127)
    else:
        # Use learned mapping
        if eventData.controllerNumber in cc_map:
            track = cc_map[eventData.controllerNumber]
            value = eventData.value / 127.0
            mixer.setTrackVolume(track, value)

def onInit():
    if device.isAssigned():
        print(f"Device: {device.getName()}")
```

### Hardware LED Feedback Display

Drives hardware LEDs and displays based on FL Studio transport and mixer state.
Sends note-on messages for LED control and CC messages for display values.

```python
import device
import transport
import mixer

def updateLEDs():
    # Turn on LED 1 if playing
    if transport.isPlaying():
        device.midiOutMsg(0x90, 0, 60, 127)
    else:
        device.midiOutMsg(0x90, 0, 60, 0)

    # Show current track on display
    track = mixer.trackNumber()
    device.midiOutMsg(0xB0, 0, 20, track)

def processMIDICC(eventData):
    if eventData.controllerNumber == 123:
        updateLEDs()

def onInit():
    updateLEDs()
```

### Pattern-based Track Routing

Routes patterns to specific mixer tracks using a dictionary mapping. Useful for
organizing multi-pattern projects with consistent mixer routing.

```python
import patterns
import mixer
import arrangement

# Route patterns to different mixer tracks
pattern_routing = {
    0: 1,   # Pattern 0 -> Track 1
    1: 2,   # Pattern 1 -> Track 2
    2: 3,   # Pattern 2 -> Track 3
}

def onInit():
    # Set up routing when script starts
    for pattern_idx, track_idx in pattern_routing.items():
        if patterns.isPatternValid(pattern_idx):
            # Logic to route pattern output
            pass
```

### Two-Way Sync with Hardware

Tracks hardware state to prevent feedback loops when syncing values between
FL Studio and a hardware controller. Only processes a CC if its value differs
from the last known hardware state.

```python
# Track hardware state to avoid feedback loops
hardware_state = {}

def OnControlChange(msg):
    cc = msg.data1
    value = msg.data2

    # Only act if different from last hardware value
    if hardware_state.get(cc) != value:
        hardware_state[cc] = value

        # Process CC
        if cc == 7:
            mixer.setTrackVolume(0, value / 127.0)

        # Send back to hardware for confirmation
        device.midiOutMsg(0xB0, 0, cc, value)
```

### Custom Sysex Handling

Parses incoming System Exclusive messages by checking the manufacturer ID bytes
and responds with an identity reply. Useful for device handshake and
configuration exchange.

```python
def OnSysEx(msg):
    # Parse sysex message
    data = bytes(msg.sysex_data)  # Full sysex message

    # Manufacturer ID check (first 3 bytes after F0)
    if data[1:4] == bytes([0x7E, 0x00, 0x09]):  # Universal inquiry
        # Send identity reply
        reply = bytes([0xF0, 0x7E, 0x00, 0x09, 0x02, 0x00, 0x00, 0x00, 0xF7])
        device.midiOutSysex(reply)
```

---

## Piano Roll & Step Sequencer Patterns

### Scale Enforcer

Snaps all notes in a piano roll selection to the nearest note within a given
scale. Modify `scale_intervals` for different scales (e.g., minor, pentatonic).

```python
import flpianoroll

# Define a scale (C major: C, D, E, F, G, A, B)
scale_intervals = [0, 2, 4, 5, 7, 9, 11]

score = flpianoroll.score

# Snap all notes to scale
for note in score.notes:
    octave = note.number // 12
    note_in_octave = note.number % 12

    # Find closest note in scale
    closest_interval = min(
        scale_intervals,
        key=lambda x: abs(x - note_in_octave)
    )

    note.number = octave * 12 + closest_interval
```

### Batch Note Quantization

Quantizes all note start times in a piano roll selection to the nearest grid
position. Adjust `grid_size` for different quantization resolutions (e.g.,
`480 // 8` for 32nd notes).

```python
import flpianoroll

# Quantize notes to 16th notes (assuming PPQ = 480)
grid_size = 480 // 4  # 16th note

score = flpianoroll.score

for note in score.notes:
    # Round to nearest grid
    quantized_time = round(note.time / grid_size) * grid_size
    note.time = quantized_time
```

### Grid Beat Filler (step sequencer)

Fills a channel's 16-step sequencer grid at regular intervals with an offset.
Useful for quickly programming drum patterns programmatically.

```python
import channels

def fill_channel(idx: int, interval: int, offset: int):
    """Fill a channel's step sequencer at regular intervals."""
    for i in range(16):
        if (i - offset) % interval == 0:
            channels.setGridBit(idx, i, True)

# Kick on every beat
fill_channel(0, 4, 0)
# Clap on beat 2 and 4
fill_channel(1, 8, 4)
# Hi-hat on every 8th note
fill_channel(2, 2, 0)
# Snare on beat 2 and 4
fill_channel(3, 8, 4)
```

---

## Advanced Patterns

### Performance Monitoring

A decorator-based performance monitor that measures callback execution time and
warns when any callback exceeds 10ms. Accumulates timing history for profiling.

```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.callback_times = {}

    def measure(self, callback_name):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start

                if callback_name not in self.callback_times:
                    self.callback_times[callback_name] = []
                self.callback_times[callback_name].append(elapsed)

                # Warn if slow
                if elapsed > 0.01:  # 10ms
                    print(f"WARNING: {callback_name} took {elapsed*1000:.1f}ms")

                return result
            return wrapper
        return decorator

monitor = PerformanceMonitor()

@monitor.measure("OnControlChange")
def OnControlChange(msg):
    # Your code here
    pass
```

### Pattern-Based Automation Engine

Triggers MIDI CC messages at specific song positions within a pattern. Define
automation sequences as lists of `(position, cc_message)` tuples per pattern.

```python
import patterns
import transport
import device

class AutomationEngine:
    def __init__(self):
        self.pattern_automations = {}

    def set_automation(self, pattern_id, sequence):
        """Set automation sequence for a pattern"""
        self.pattern_automations[pattern_id] = sequence

    def on_timer(self):
        """Called periodically (implement with refresh thread)"""
        current_pattern = patterns.patternNumber()

        if current_pattern in self.pattern_automations:
            pos = transport.getSongPos()
            automation = self.pattern_automations[current_pattern]

            # Trigger automation at specific points
            for trigger_pos, cc_msg in automation:
                if abs(pos - trigger_pos) < 0.01:
                    device.midiOutMsg(*cc_msg)

automator = AutomationEngine()
automator.set_automation(0, [
    (0.0, (0xB0, 0, 7, 64)),   # CC 7 to 64 at beat 1
    (1.0, (0xB0, 0, 7, 100)),  # CC 7 to 100 at beat 2
])
```

---

## Debugging and Testing

### ScriptLogger Class

A reusable logger that prefixes messages with the device name. Includes
dedicated methods for MIDI message inspection and error logging with tracebacks.

```python
import device
import sys

class ScriptLogger:
    def __init__(self):
        self.log_file = None

    def log(self, message):
        """Log to console and file"""
        print(f"[{device.getName()}] {message}")
        # Could also write to file for debugging

    def log_midi(self, msg):
        """Log MIDI message details"""
        self.log(f"MIDI: Status=0x{msg.status:02X} Data1={msg.data1} Data2={msg.data2}")

    def log_error(self, error):
        """Log error with traceback"""
        self.log(f"ERROR: {str(error)}")
        import traceback
        traceback.print_exc()

logger = ScriptLogger()
```

### Testing MIDI Input

Uses the ScriptLogger to dump all incoming CC messages for debugging. Includes a
test trigger on CC 127 to verify that the script is loaded and responding.

```python
def OnControlChange(msg):
    # Log all CCs for debugging
    logger.log_midi(msg)

    # Test: Print CC map
    if msg.data1 == 127:  # Test CC
        print("Received test message - script is working!")
```
