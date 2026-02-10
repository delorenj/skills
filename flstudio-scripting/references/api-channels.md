# Channels Module API Reference

## Table of Contents

**Total Functions:** 48

### Channel Query & Counting
- [`channelCount`](#channelcount) - Returns the number of channels on the channel rack
- [`channelNumber`](#channelnumber) - Returns the global index of the first selected channel
- [`getChannelIndex`](#getchannelindex) - Returns the global index of a channel given the group index
- [`getChannelType`](#getchanneltype) - Returns the type of instrument loaded into the channel rack
- [`getRecEventId`](#getreceventid) - Return the starting point of REC event IDs for the channel

### Channel Selection
- [`deselectAll`](#deselectall) - Deselects all channels in the current channel group
- [`isChannelSelected`](#ischannelselected) - Returns whether the channel at index is selected
- [`selectAll`](#selectall) - Selects all channels in the current channel group
- [`selectChannel`](#selectchannel) - Select the channel at index (respecting groups)
- [`selectOneChannel`](#selectonechannel) - Exclusively select the channel at index
- [`selectedChannel`](#selectedchannel) - Returns the index of the first selected channel
- [`isHighLighted`](#ishighlighted) - Returns True when a red highlight rectangle is displayed

### Channel Properties (Get)
- [`getChannelColor`](#getchannelcolor) - Returns the color of the channel
- [`getChannelMidiInPort`](#getchannelmidiinport) - Returns the MIDI-in port associated with the channel
- [`getChannelName`](#getchannelname) - Returns the name of the channel
- [`getChannelPan`](#getchannelpan) - Returns the normalized pan of the channel
- [`getChannelPitch`](#getchannelpitch) - Returns the current pitch bend (or range) of the channel
- [`getChannelVolume`](#getchannelvolume) - Returns the normalized volume of the channel
- [`getActivityLevel`](#getactivitylevel) - Return the note activity level for channel

### Channel Properties (Set)
- [`setChannelColor`](#setchannelcolor) - Sets the color of the channel
- [`setChannelName`](#setchannelname) - Sets the name of the channel
- [`setChannelPan`](#setchannelpan) - Sets the normalized pan of the channel
- [`setChannelPitch`](#setchannelpitch) - Sets the pitch of the channel
- [`setChannelVolume`](#setchannelvolume) - Sets the normalized volume of the channel

### Channel State
- [`isChannelMuted`](#ischannelmuted) - Returns whether channel is muted
- [`isChannelSolo`](#ischannelsolo) - Returns whether channel is solo
- [`muteChannel`](#mutechannel) - Toggles the mute state of the channel
- [`soloChannel`](#solochannel) - Toggles the solo state of the channel

### Grid Bit / Step Sequencer
- [`getGridBit`](#getgridbit) - Returns whether the grid bit on channel is set
- [`getGridBitWithLoop`](#getgridbitwithloop) - Get value of grid bit accounting for loop
- [`isGridBitAssigned`](#isgridbitassigned) - Returns True when the grid bit is assigned
- [`setGridBit`](#setgridbit) - Sets the value of the grid bit on channel
- [`getCurrentStepParam`](#getcurrentstepparam) - Get current step parameter for channel
- [`getStepParam`](#getstepparam) - Get the values of properties associated with a step
- [`setStepParameterByIndex`](#setstepparameterbyindex) - Set the value of a step parameter
- [`quickQuantize`](#quickquantize) - Perform a quick quantize operation on the channel

### Mixer Routing
- [`getTargetFxTrack`](#gettargetfxtrack) - Returns the mixer track that the channel is linked to
- [`setTargetFxTrack`](#settargetfxtrack) - Sets the mixer track that the channel is linked to

### MIDI & Events
- [`midiNoteOn`](#midinoteon) - Set a MIDI Note for the channel
- [`incEventValue`](#inceventvalue) - Get event value increased by step
- [`processRECEvent`](#processrecevent) - Processes a recording event

### Editor & UI
- [`closeGraphEditor`](#closegrapheditor) - Close the graph editor
- [`focusEditor`](#focuseditor) - Focus the plugin window for the channel
- [`isGraphEditorVisible`](#isgrapheditorvisible) - Returns whether the graph editor is currently visible
- [`showCSForm`](#showcsform) - Show the channel settings window
- [`showEditor`](#showeditor) - Toggle whether the plugin window is shown
- [`showGraphEditor`](#showgrapheditor) - Show the graph editor for a step parameter
- [`updateGraphEditor`](#updategrapheditor) - Update the graph editor

---

## CHANNELS Module

**Total Functions:** 48

### `channelCount`

```python
channelCount(globalCount: bool = False) -> int
```

*Returns the number of channels on the channel rack. Respect for groups is*

### `channelNumber`

```python
channelNumber(canBeNone: bool = False, offset: int = 0) -> int
```

*Returns the global index of the first selected channel, otherwise the nth*

### `closeGraphEditor`

```python
closeGraphEditor(index: int, /) -> None
```

*???*

### `deselectAll`

```python
deselectAll() -> None
```

*Deselects all channels in the current channel group.*

### `getGridBit`

```python
def getGridBit(
    index: int,
    position: int,
    useGlobalIndex: bool = False,
) -> bool
```

*Returns whether the grid bit on channel at `index` in `position` is set.*

### `focusEditor`

```python
focusEditor(index: int, useGlobalIndex: bool = False) -> None
```

*Focus the plugin window for the channel at `index`.*

### `getActivityLevel`

```python
getActivityLevel(index: int, useGlobalIndex: bool = False) -> float
```

*Return the note activity level for channel at `index`. Activity level*

### `getChannelColor`

```python
getChannelColor(index: int, useGlobalIndex: bool = False) -> int
```

*Returns the color of the channel at `index`.*

### `getChannelIndex`

```python
getChannelIndex(index: int) -> int
```

*Returns the global index of a channel given the group `index`.*

### `getChannelMidiInPort`

```python
getChannelMidiInPort(index: int, useGlobalIndex: bool = False) -> int
```

*Returns the MIDI-in port associated with the channel at `index`.*

### `getChannelName`

```python
getChannelName(index: int, useGlobalIndex: bool = False) -> str
```

*Returns the name of the channel at `index`.*

### `getChannelPan`

```python
getChannelPan(index: int, useGlobalIndex: bool = False) -> float
```

*Returns the normalized pan of the channel at `index`, where `-1.0` is 100%*

### `getChannelPitch`

```python
getChannelPitch(index: int,
    mode: Literal[1, 2],
    useGlobalIndex: bool = False,
) -> int:
    ...


@overload
def getChannelPitch(
    index: int,
    mode: Literal[0] = 0,
    useGlobalIndex: bool = False,
) -> float:
    ...


def getChannelPitch(
    index: int,
    mode: int = 0,
    useGlobalIndex: bool = False,) -> 'float | int'
```

*Returns the current pitch bend (or range) of the channel at `index`. The*

### `getChannelType`

```python
getChannelType(index: int, useGlobalIndex: bool = False) -> int
```

*Returns the type of instrument loaded into the channel rack at `index`.*

### `getChannelVolume`

```python
getChannelVolume(index: int,
    mode: bool = False,
    useGlobalIndex: bool = False,) -> float
```

*Returns the normalized volume of the channel at `index`, where `0.0` is the*

### `getCurrentStepParam`

```python
getCurrentStepParam(index: int,
    step: int,
    param: int,
    useGlobalIndex: bool = False,) -> int
```

*Get current step parameter for channel at `index` and for step at `step`.*

### `getGridBitWithLoop`

```python
getGridBitWithLoop(index: int,
    position: int,
    useGlobalIndex: bool = False,) -> bool
```

*Get value of grid bit on channel `index` in `position` accounting for*

### `getRecEventId`

```python
getRecEventId(index: int, useGlobalIndex: bool = False) -> int
```

*Return the starting point of REC event IDs for the channel at `index`.*

### `getStepParam`

```python
getStepParam(step: int,
    param: int,
    index: int,
    startPos: int,
    padsStride: int = 16,
    useGlobalIndex: bool = False,) -> int
```

*Get the values of properties associated with a step in the step sequencer.*

### `getTargetFxTrack`

```python
getTargetFxTrack(index: int, useGlobalIndex: bool = False) -> int
```

*Returns the mixer track that the channel at `index` is linked to.*

### `incEventValue`

```python
incEventValue(eventId: int, step: int, res: float = 1 / 24) -> int
```

*Get event value increased by step.*

### `isChannelMuted`

```python
isChannelMuted(index: int, useGlobalIndex: bool = False) -> bool
```

*Returns whether channel is muted (`True`) or not (`False`).*

### `isChannelSelected`

```python
isChannelSelected(index: int, useGlobalIndex: bool = False) -> bool
```

*Returns whether the channel at `index` is selected.*

### `isChannelSolo`

```python
isChannelSolo(index: int, useGlobalIndex: bool = False) -> bool
```

*Returns whether channel is solo (`True`) or not (`False`).*

### `isGraphEditorVisible`

```python
isGraphEditorVisible() -> bool
```

*Returns whether the graph editor is currently visible.*

### `isGridBitAssigned`

```python
isGridBitAssigned(index: int, useGlobalIndex: bool = False) -> bool
```

*Returns `True` when the grid bit at `index` is assigned.*

### `isHighLighted`

```python
isHighLighted() -> bool
```

*Returns `True` when a red highlight rectangle is displayed on the channel*

### `midiNoteOn`

```python
midiNoteOn(indexGlobal: int,
    note: int,
    velocity: int,
    channel: int = -1,) -> None
```

*Set a MIDI Note for the channel at `indexGlobal` (not respecting groups).*

### `muteChannel`

```python
muteChannel(index: int,
    value: int = -1,
    useGlobalIndex: bool = False,) -> None
```

*Toggles the mute state of the channel at `index`.*

### `processRECEvent`

```python
processRECEvent(eventId: int, value: int, flags: int, /) -> int
```

*Processes a recording event.*

### `quickQuantize`

```python
quickQuantize(index: int,
    startOnly: int = 1,
    useGlobalIndex: bool = False,) -> None
```

*Perform a quick quantize operation on the channel at index*

### `selectAll`

```python
selectAll() -> None
```

*Selects all channels in the current channel group.*

### `selectChannel`

```python
selectChannel(index: int,
    value: int = -1,
    useGlobalIndex: bool = False,) -> None
```

*Select the channel at `index` (respecting groups).*

### `selectOneChannel`

```python
selectOneChannel(index: int, useGlobalIndex: bool = False) -> None
```

*Exclusively select the channel at `index` (deselecting any other selected*

### `selectedChannel`

```python
selectedChannel(canBeNone: bool = False,
    offset: int = 0,
    indexGlobal: bool = False,) -> int
```

*Returns the index of the first selected channel, otherwise the nth selected*

### `setChannelColor`

```python
setChannelColor(index: int,
    color: int,
    useGlobalIndex: bool = False,) -> None
```

*Sets the color of the channel at `index`.*

### `setChannelName`

```python
setChannelName(index: int,
    name: str,
    useGlobalIndex: bool = False,) -> None
```

*Sets the name of the channel at `index`.*

### `setChannelPan`

```python
setChannelPan(index: int,
    pan: float,
    pickupMode: int = midi.PIM_None,
    useGlobalIndex: bool = False,) -> None
```

*Sets the normalized pan of the channel at `index`, where `-1.0` is 100%*

### `setChannelPitch`

```python
setChannelPitch(index: int,
    value: float,
    mode: int = 0,
    pickupMode: int = midi.PIM_None,
    useGlobalIndex: bool = False,) -> None
```

*Sets the pitch of the channel at `index` to value. The `mode` parameter is*

### `setChannelVolume`

```python
setChannelVolume(index: int,
    volume: float,
    pickupMode: int = midi.PIM_None,
    useGlobalIndex: bool = False,) -> None
```

*Sets the normalized volume of the channel at `index`, where `0.0` is the*

### `setGridBit`

```python
setGridBit(index: int,
    position: int,
    value: bool,
    useGlobalIndex: bool = False,) -> None
```

*Sets the value of the grid bit on channel at `index` in `position`.*

### `setStepParameterByIndex`

```python
setStepParameterByIndex(index: int,
    patNum: int,
    step: int,
    param: int,
    value: int,
    useGlobalIndex: bool = False,) -> None
```

*Set the value of a step parameter at the given location.*

### `setTargetFxTrack`

```python
setTargetFxTrack(channelIndex: int,
    mixerIndex: int,
    useGlobalIndex: bool = False,) -> None
```

*Sets the mixer track that the channel at `index` is linked to.*

### `showCSForm`

```python
showCSForm(index: int,
    state: int = 1,
    useGlobalIndex: bool = False,) -> None
```

*Show the channel settings window (or plugin window for plugins) for channel*

### `showEditor`

```python
showEditor(index: int,
    value: int = -1,
    useGlobalIndex: bool = False,) -> None
```

*Toggle whether the plugin window for the channel at `index` is shown. The*

### `showGraphEditor`

```python
showGraphEditor(temporary: bool,
    param: int,
    step: int,
    index: int,
    useGlobalIndex: bool = True,) -> None
```

*Show the graph editor for a step parameter on the channel at `index`.*

### `soloChannel`

```python
soloChannel(index: int, useGlobalIndex: bool = False) -> None
```

*Toggles the solo state of the channel at `index`.*

### `updateGraphEditor`

```python
updateGraphEditor() -> None
```

*???*
