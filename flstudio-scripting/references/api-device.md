# Device Module API Reference

**Total Functions:** 34

## Table of Contents

### Device Info
- [getName](#getname)
- [getDeviceID](#getdeviceid)
- [getPortNumber](#getportnumber)
- [isAssigned](#isassigned)
- [isMidiOutAssigned](#ismidioutassigned)

### MIDI Output
- [midiOutMsg](#midioutmsg)
- [midiOutNewMsg](#midioutnewmsg)
- [midiOutSysex](#midioutsysex)
- [directFeedback](#directfeedback)

### Sysex/Text
- [sendMsgGeneric](#sendmsggeneric)

### Dispatch
- [dispatch](#dispatch)
- [dispatchReceiverCount](#dispatchreceivercount)
- [dispatchGetReceiverPortNumber](#dispatchgetreceiverportnumber)

### Event Linking
- [findEventID](#findeventid)
- [getLinkedValue](#getlinkedvalue)
- [getLinkedInfo](#getlinkedinfo)
- [getLinkedParamName](#getlinkedparamname)
- [getLinkedValueString](#getlinkedvaluestring)
- [getLinkedChannel](#getlinkedchannel)
- [linkToLastTweaked](#linktolasttweaked)

### Refresh
- [fullRefresh](#fullrefresh)
- [createRefreshThread](#createrefreshthread)
- [destroyRefreshThread](#destroyrefreshthread)
- [hardwareRefreshMixerTrack](#hardwarerefreshmixertrack)

### Utilities
- [isDoubleClick](#isdoubleclick)
- [repeatMidiEvent](#repeatmidievent)
- [stopRepeatMidiEvent](#stoprepeatevent)
- [getIdleElapsed](#getidleelapsed)

### Track
- [baseTrackSelect](#basetrackselect)
- [setHasMeters](#sethasmeters)

### Sync
- [getMasterSync](#getmastersync)
- [setMasterSync](#setmastersync)

### MIDI Processing
- [processMIDICC](#processmidicc)
- [forwardMIDICC](#forwardmidicc)

---

## Device Info

### `getName`

```python
getName() -> str
```

*Returns the name of the device.*

### `getDeviceID`

```python
getDeviceID() -> bytes
```

*Returns the unique device identifier of the connected device, as determined*

### `getPortNumber`

```python
getPortNumber() -> int
```

*Returns the port number for the input device that the script is attached*

### `isAssigned`

```python
isAssigned() -> bool
```

*Returns `True` if an output interface is linked to the script, meaning that*

### `isMidiOutAssigned`

```python
isMidiOutAssigned() -> bool
```

*???*

---

## MIDI Output

### `midiOutMsg`

```python
midiOutMsg(message: int) -> None:
    ...


@overload
def midiOutMsg(message: int, channel: int, data1: int, data2: int) -> None:
    ...


def midiOutMsg(
    message: int,
    channel: int = -1,
    data1: int = -1,
    data2: int = -1,) -> None
```

*Sends a MIDI message to the linked output device.*

### `midiOutNewMsg`

```python
midiOutNewMsg(slotIndex: int, message: int) -> None
```

*Sends a MIDI message to the linked output device, but only if the*

### `midiOutSysex`

```python
midiOutSysex(message: bytes) -> None
```

*Send a sysex message to the (linked) output device.*

### `directFeedback`

```python
directFeedback(eventData: FlMidiMsg, /) -> None
```

*Send a received message to the linked output device.*

---

## Sysex/Text

### `sendMsgGeneric`

```python
sendMsgGeneric(id: int,
    message: str,
    lastMsg: str,
    offset: int = 0,
    /,) -> str
```

*Send a text string as a sysex message to the linked output device.*

---

## Dispatch

### `dispatch`

```python
dispatch(ctrlIndex: int,
    message: Literal[0xF0],
    sysex: bytes,
) -> None:
    ...


@overload
def dispatch(
    ctrlIndex: int,
    message: int,
) -> None:
    ...


def dispatch(
    ctrlIndex: int,
    message: int,
    sysex: bytes | None = None,) -> None
```

*Dispatch a MIDI message (either via a standard MIDI Message or through a*

### `dispatchReceiverCount`

```python
dispatchReceiverCount() -> int
```

*Returns the number of device scripts that this script can dispatch to.*

### `dispatchGetReceiverPortNumber`

```python
dispatchGetReceiverPortNumber(ctrlIndex: int) -> int
```

*Returns the port of the receiver device specified by `ctrlIndex`.*

---

## Event Linking

### `findEventID`

```python
findEventID(controlId: int, flags: int = 0) -> int
```

*Given a hardware control ID, returns the eventId of the software control*

### `getLinkedValue`

```python
getLinkedValue(eventID: int) -> float
```

*Returns value of the software control associated with `eventID` between*

### `getLinkedInfo`

```python
getLinkedInfo(eventID: int) -> int
```

*Returns information about a linked control via `eventID`.*

### `getLinkedParamName`

```python
getLinkedParamName(eventID: int) -> str
```

*Returns the parameter name of the REC event at `eventID`.*

### `getLinkedValueString`

```python
getLinkedValueString(eventID: int) -> str
```

*Returns text value of the REC event at `eventID`.*

### `getLinkedChannel`

```python
getLinkedChannel(eventId: int) -> int
```

*Returns the MIDI channel associated with a linked control.*

### `linkToLastTweaked`

```python
linkToLastTweaked(controlIndex: int,
    channel: int,
    global_link: bool = False,
    eventId: int = midi.REC_None,) -> int
```

*Links the control with the given index to the last tweaked parameter.*

---

## Refresh

### `fullRefresh`

```python
fullRefresh() -> None
```

*Trigger a previously started threaded refresh. If there is none, the*

### `createRefreshThread`

```python
createRefreshThread() -> None
```

*Start a threaded refresh of the entire MIDI device.*

### `destroyRefreshThread`

```python
destroyRefreshThread() -> None
```

*Stop a previously started threaded refresh.*

### `hardwareRefreshMixerTrack`

```python
hardwareRefreshMixerTrack(index: int) -> None
```

*Hardware refresh mixer track at `index`.*

---

## Utilities

### `isDoubleClick`

```python
isDoubleClick(index: int) -> bool
```

*Returns whether the function was called with the same index shortly*

### `repeatMidiEvent`

```python
repeatMidiEvent(eventData: FlMidiMsg,
    delay: int = 300,
    rate: int = 300,) -> None
```

*Start repeatedly sending out the message in `eventData` every `rate` ms*

### `stopRepeatMidiEvent`

```python
stopRepeatMidiEvent() -> None
```

*Stop sending a currently repeating MIDI event.*

### `getIdleElapsed`

```python
getIdleElapsed() -> float
```

*???*

---

## Track

### `baseTrackSelect`

```python
baseTrackSelect(index: int, step: int) -> None
```

*Base track selection (for control surfaces). Set `step` to `MaxInt` to*

### `setHasMeters`

```python
setHasMeters() -> None
```

*Registers the controller as having peak meters, meaning that the*

---

## Sync

### `getMasterSync`

```python
getMasterSync() -> bool
```

*Returns the value of the "send master sync" option in FL Studio's MIDI*

### `setMasterSync`

```python
setMasterSync(value: bool) -> None
```

*Control the value of the "send master sync" option in FL Studio's MIDI*

---

## MIDI Processing

### `processMIDICC`

```python
processMIDICC(eventData: FlMidiMsg) -> None
```

*Let FL Studio process a MIDI CC message.*

### `forwardMIDICC`

```python
forwardMIDICC(message: int, mode: int = 1) -> None
```

*Forwards a MIDI CC message to the currently focused plugin.*
