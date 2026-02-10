# Callbacks & FlMidiMsg Reference

## Table of Contents

- [Event Processing Flow](#event-processing-flow)
- [FlMidiMsg Class](#flmidimsg-class)
  - [Properties](#properties)
  - [Status Byte Reference](#status-byte-reference)
- [Lifecycle Callbacks](#lifecycle-callbacks)
  - [OnInit](#oninit)
  - [OnDeInit](#ondeinit)
  - [OnFirstConnect](#onfirstconnect)
- [MIDI Input Callbacks](#midi-input-callbacks)
  - [OnMidiIn](#onmidiin)
  - [OnMidiMsg](#onmidimsg)
  - [OnSysEx](#onsysex)
  - [OnMidiOutMsg](#onmidioutmsg)
- [Note Callbacks](#note-callbacks)
  - [OnNoteOn](#onnoteon)
  - [OnNoteOff](#onnoteoff)
- [Control Callbacks](#control-callbacks)
  - [OnControlChange](#oncontrolchange)
  - [OnProgramChange](#onprogramchange)
  - [OnChannelPressure](#onchannelpressure)
  - [OnKeyPressure](#onkeypressure)
  - [OnPitchBend](#onpitchbend)
- [State Change Callbacks](#state-change-callbacks)
  - [OnRefresh](#onrefresh)
  - [OnDoFullRefresh](#ondofullrefresh)
  - [OnIdle](#onidle)
  - [OnDirtyChannel](#ondirtychannel)
  - [OnDirtyMixerTrack](#ondirtymixertrack)
  - [OnProjectLoad](#onprojectload)
  - [OnDisplayZone](#ondisplayzone)
  - [OnUpdateBeatIndicator](#onupdatebeatindicator)
  - [OnUpdateLiveMode](#onupdatelivemode)
  - [OnUpdateMeters](#onupdatemeters)
  - [OnSendTempMsg](#onsendtempmsg)
  - [OnWaitingForInput](#onwaitingforinput)
- [API Version History](#api-version-history)

---

## Event Processing Flow

When a MIDI message arrives, FL Studio dispatches it through callbacks in the following order. If a callback sets `msg.handled = True`, processing stops and later callbacks are not called.

```
OnMidiIn -> OnMidiMsg -> OnNoteOn | OnNoteOff | OnControlChange | OnPitchBend | OnProgramChange | OnChannelPressure | OnKeyPressure | OnSysEx
```

For simple scripts, the specialized callbacks (`OnNoteOn`, `OnControlChange`, etc.) can be used as an alternative to writing more complex event handling code inside `OnMidiMsg`. If an event is not handled by an earlier callback, it is passed to later callbacks.

---

## FlMidiMsg Class

All MIDI callbacks receive an `FlMidiMsg` object. Set `msg.handled = True` to prevent further processing.

### Properties

```python
class FlMidiMsg:
    status: int          # MIDI status byte (0x80-0xFF)
    data1: int           # First data byte
    data2: int           # Second data byte
    port: int            # MIDI port number
    handled: bool        # Set to True to prevent further processing
    timestamp: int       # Event timestamp

    # Convenience properties:
    note: int            # Decoded note number (for note messages)
    velocity: int        # Decoded velocity (for note messages)
    controllerNumber: int # CC number (for CC messages)
    value: int           # CC value (for CC messages)
```

### Status Byte Reference

```python
NOTEOFF = 0x80-0x8F          # Note off
NOTEON = 0x90-0x9F           # Note on
POLYAFTERTOUCH = 0xA0-0xAF   # Polyphonic key pressure
CONTROLCHANGE = 0xB0-0xBF    # CC
PROGRAMCHANGE = 0xC0-0xCF    # Program change
CHANNELAFTERTOUCH = 0xD0-0xDF # Channel pressure
PITCHBEND = 0xE0-0xEF        # Pitch bend
SYSTEMMESSAGE = 0xF0-0xFF    # System messages
```

---

## Lifecycle Callbacks

### `OnInit`

```python
OnInit() -> None
```

*Called when FL Studio initializes the script.*

### `OnDeInit`

```python
OnDeInit() -> None
```

*Called before FL Studio de-initializes the script.*

### `OnFirstConnect`

```python
OnFirstConnect() -> None
```

*Called when the device is connected for the first time ever.*

---

## MIDI Input Callbacks

### `OnMidiIn`

```python
OnMidiIn(msg: FlMidiMsg) -> None
```

*Called when any MIDI message is received.*

### `OnMidiMsg`

```python
OnMidiMsg(msg: FlMidiMsg) -> None
```

*Called after OnMidiIn if the event was not handled.*

### `OnSysEx`

```python
OnSysEx(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for system-exclusive MIDI messages.*

### `OnMidiOutMsg`

```python
OnMidiOutMsg(msg: FlMidiMsg) -> None
```

*Called when MIDI messages are sent from the host.*

---

## Note Callbacks

### `OnNoteOn`

```python
OnNoteOn(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for note-on MIDI events.*

### `OnNoteOff`

```python
OnNoteOff(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for note-off MIDI events.*

---

## Control Callbacks

### `OnControlChange`

```python
OnControlChange(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for control change (CC) events.*

### `OnProgramChange`

```python
OnProgramChange(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for program change MIDI events.*

### `OnChannelPressure`

```python
OnChannelPressure(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for channel pressure events.*

### `OnKeyPressure`

```python
OnKeyPressure(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for key pressure (note aftertouch) events.*

### `OnPitchBend`

```python
OnPitchBend(msg: FlMidiMsg) -> None
```

*Called after OnMidiMsg for pitch bend MIDI events.*

---

## State Change Callbacks

### `OnRefresh`

```python
OnRefresh(flags: int) -> None
```

*Called when certain events occur within FL Studio. Scripts should use the flags parameter to determine what changed.*

### `OnDoFullRefresh`

```python
OnDoFullRefresh() -> None
```

*Similar to OnRefresh, but everything should be refreshed.*

### `OnIdle`

```python
OnIdle() -> None
```

*Called frequently (roughly once every 20ms). Scripts can use this callback for periodic tasks.*

### `OnDirtyChannel`

```python
OnDirtyChannel(index: int) -> None
```

*Called when a channel on the channel rack has changed status.*

### `OnDirtyMixerTrack`

```python
OnDirtyMixerTrack(index: int) -> None
```

*Called when a mixer track has changed status.*

### `OnProjectLoad`

```python
OnProjectLoad(status: Literal[0, 100, 101]) -> None
```

*Called when a project is loaded.*

### `OnDisplayZone`

```python
OnDisplayZone() -> None
```

*Called when the playlist zone has changed.*

### `OnUpdateBeatIndicator`

```python
OnUpdateBeatIndicator(value: Literal[0, 1, 2]) -> None
```

*Called when the beat indicator should be updated.*

### `OnUpdateLiveMode`

```python
OnUpdateLiveMode(lastTrack: int) -> None
```

*Called when something about performance mode has changed.*

### `OnUpdateMeters`

```python
OnUpdateMeters() -> None
```

*Called when peak meters need to be updated.*

### `OnSendTempMsg`

```python
OnSendTempMsg(message: str, duration: int) -> None
```

*Called when a hint message should be displayed on the controller.*

### `OnWaitingForInput`

```python
OnWaitingForInput() -> None
```

*Called when FL Studio is in [waiting mode](https://www.image-line.com/support/flstudio_online_manual/html/toolbar_panels.htm#panel_shortcuticons_wait).*

---

## API Version History

The FL Studio Python API has evolved significantly:

- **v1** - Initial release with basic transport/mixer control
- **v18** - Added setMasterSync/getMasterSync
- **v19** - Enhanced device synchronization
- **v20** - Expanded UI module capabilities
- **v25** - Added getDeviceID for sysex handling
- **v32** - Slot color manipulation

Check your API version with:
```python
import general
print(f"API v{general.getVersion()}")
```
