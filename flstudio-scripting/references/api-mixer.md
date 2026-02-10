# Mixer Module API Reference

## Table of Contents

**Total Functions:** 69

### Track Management
- [afterRoutingChanged](#afterroutingchanged)
- [trackCount](#trackcount)
- [trackNumber](#tracknumber)

### Volume/Pan/Stereo
- [getTrackVolume](#gettrackvolume)
- [setTrackVolume](#settrackvolume)
- [getTrackPan](#gettrackpan)
- [setTrackPan](#settrackpan)
- [getTrackStereoSep](#gettrackstereosep)
- [setTrackStereoSep](#settrackstereosep)

### Mute/Solo/Arm
- [muteTrack](#mutetrack)
- [soloTrack](#solotrack)
- [armTrack](#armtrack)
- [enableTrack](#enabletrack)
- [isTrackMuted](#istrackmuted)
- [isTrackSolo](#istracksolo)
- [isTrackArmed](#istrackarmed)
- [isTrackEnabled](#istrackenabled)
- [isTrackMuteLock](#isTrackmutelock)

### EQ
- [getEqBandCount](#geteqbandcount)
- [getEqBandwidth](#geteqbandwidth)
- [getEqFrequency](#geteqfrequency)
- [getEqGain](#geteqgain)
- [setEqBandwidth](#seteqbandwidth)
- [setEqFrequency](#seteqfrequency)
- [setEqGain](#seteqgain)

### Routing
- [getRouteSendActive](#getroutesendactive)
- [getRouteToLevel](#getroutetolevel)
- [setRouteTo](#setrouteto)
- [setRouteToLevel](#setroutetolevel)
- [linkChannelToTrack](#linkchanneltotrack)
- [linkTrackToChannel](#linktracktochannel)

### Effects/Plugins
- [enableTrackSlots](#enabletrackslots)
- [isTrackSlotsEnabled](#istrackslotsenabled)
- [focusEditor](#focuseditor)
- [getTrackPluginId](#gettrackpluginid)
- [isTrackPluginValid](#istrackpluginvalid)
- [isTrackAutomationEnabled](#istrackautomationenabled)
- [getActiveEffectIndex](#getactiveeffectindex)

### Selection
- [selectAll](#selectall)
- [deselectAll](#deselectall)
- [selectTrack](#selecttrack)
- [setActiveTrack](#setactivetrack)
- [isTrackSelected](#istrackselected)
- [setTrackNumber](#settracknumber)

### Track Properties
- [getTrackName](#gettrackname)
- [setTrackName](#settrackname)
- [getTrackColor](#gettrackcolor)
- [setTrackColor](#settrackcolor)
- [getTrackDockSide](#gettrackdockside)
- [getTrackInfo](#gettrackinfo)
- [isTrackRevPolarity](#istrackrevpolarity)
- [revTrackPolarity](#revtrackpolarity)
- [isTrackSwapChannels](#istrackswapchannels)
- [swapTrackChannels](#swaptrackchannels)
- [getSlotColor](#getslotcolor)
- [setSlotColor](#setslotcolor)

### Peaks/Meters
- [getTrackPeaks](#gettrackpeaks)
- [getLastPeakVol](#getlastpeakvol)
- [getRecPPS](#getrecpps)
- [getSongStepPos](#getsongsteppos)
- [getSongTickPos](#getsongtickpos)

### Recording
- [getTrackRecordingFileName](#gettrackrecordingfilename)

### Events
- [automateEvent](#automateevent)
- [getEventValue](#geteventvalue)
- [getEventIDName](#geteventidname)
- [getEventIDValueString](#geteventidvaluestring)
- [getAutoSmoothEventValue](#getautosmootheventvalue)
- [remoteFindEventValue](#remotefindeventvalue)

### Tempo
- [getCurrentTempo](#getcurrenttempo)

---

## MIXER Module

### `afterRoutingChanged`

```python
afterRoutingChanged() -> None
```

*Notify FL Studio that channel routings have changed.*

### `armTrack`

```python
armTrack(index: int) -> None
```

*Toggles whether the track at index is armed for recording.*

### `automateEvent`

```python
automateEvent(index: int,
    value: int,
    flags: int,
    speed: int = 0,
    isIncrement: int = 0,
    res: float = midi.EKRes,) -> int
```

*Automate event.*

### `deselectAll`

```python
deselectAll() -> None
```

*Deselects all tracks.*

### `enableTrack`

```python
enableTrack(index: int) -> None
```

*Toggles whether the track at `index` is enabled.*

### `enableTrackSlots`

```python
enableTrackSlots(index: int, value: bool = False) -> None
```

*Toggle whether all effects are enabled on a track.*

### `focusEditor`

```python
focusEditor(index: int, plugIndex: int) -> None
```

*Focus the editor the effect plugin at the given location.*

### `getActiveEffectIndex`

```python
getActiveEffectIndex() -> tuple[int, int] | None
```

*Returns the index of the active effects plugin, or None if there isn't one.*

### `getAutoSmoothEventValue`

```python
getAutoSmoothEventValue(index: int, locked: int = 1) -> int
```

*Returns auto smooth event value.*

### `getCurrentTempo`

```python
getCurrentTempo(asInt: Literal[True]) -> int:
    ...


@overload
def getCurrentTempo(asInt: Literal[False] = False) -> float:
    ...


def getCurrentTempo(asInt: bool = False) -> 'int | float'
```

*Returns the current tempo of the song.*

### `getEqBandCount`

```python
getEqBandCount() -> int
```

*Returns the number of bands in the built-in EQ.*

### `getEqBandwidth`

```python
getEqBandwidth(index: int, band: int) -> float
```

*Returns the bandwidth of the given band on the given track for the built-in*

### `getEqFrequency`

```python
getEqFrequency(index: int, band: int, mode: int = 0) -> float
```

*Returns the frequency of the given band on the given track for the built-in*

### `getEqGain`

```python
getEqGain(index: int, band: int, mode: int = 0) -> float
```

*Returns the gain of the given band on the given track for the built-in EQ.*

### `getEventIDName`

```python
getEventIDName(index: int, shortname: int = 0) -> str
```

*Returns event name for event at `index`.*

### `getEventIDValueString`

```python
getEventIDValueString(index: int, value: int) -> str
```

*Returns event value as a string.*

### `getEventValue`

```python
getEventValue(index: int,
    value: int = midi.MaxInt,
    smoothTarget: int = 1,) -> int
```

*Returns event value from MIDI.*

### `getLastPeakVol`

```python
getLastPeakVol(section: int) -> float
```

*Returns last peak volume.*

### `getRecPPS`

```python
getRecPPS() -> int
```

*Returns the recording PPS.*

### `getRouteSendActive`

```python
getRouteSendActive(index: int, destIndex: int) -> bool
```

*Return whether the track at `index` is routed to the track at `destIndex`*

### `getRouteToLevel`

```python
getRouteToLevel(index: int, destIndex: int) -> float
```

*Get the send level for the route between `index` and `destIndex`.*

### `getSlotColor`

```python
getSlotColor(index: int, slot: int) -> int
```

*Returns the color of a mixer track FX slot.*

### `getSongStepPos`

```python
getSongStepPos() -> int
```

*Returns the current position in the song, measured in steps.*

### `getSongTickPos`

```python
getSongTickPos(mode: Literal[0] = 0) -> int:
    ...


@overload
def getSongTickPos(mode: Literal[1, 2]) -> float:
    ...


def getSongTickPos(mode: int = midi.ST_Int) -> 'int | float'
```

*Returns the current position in the song, measured in ticks.*

### `getTrackColor`

```python
getTrackColor(index: int) -> int
```

*Returns the color of the track at `index`.*

### `getTrackDockSide`

```python
getTrackDockSide(index: int) -> int
```

*Returns the dock side of the mixer for track at `index`.*

### `getTrackInfo`

```python
getTrackInfo(mode: int) -> int
```

*Returns the index of a special mixer track depending on `mode`.*

### `getTrackName`

```python
getTrackName(index: int) -> str
```

*Returns the name of the track at `index`.*

### `getTrackPan`

```python
getTrackPan(index: int) -> float
```

*Returns the pan of the track at `index`. Pan lies within the range*

### `getTrackPeaks`

```python
getTrackPeaks(index: int, mode: int) -> float
```

*Returns the current audio peak value for the track at `index`.*

### `getTrackPluginId`

```python
getTrackPluginId(index: int, plugIndex: int) -> int
```

*Returns the plugin ID of the plugin on track `index` in slot `plugIndex`.*

### `getTrackRecordingFileName`

```python
getTrackRecordingFileName(index: int) -> str
```

*Returns the file name for audio being recorded on the track at `index`.*

### `getTrackStereoSep`

```python
getTrackStereoSep(index: int) -> float
```

*Returns the stereo separation of the track at `index`. Stereo separation*

### `getTrackVolume`

```python
getTrackVolume(index: int, mode: int = 0) -> float
```

*Returns the volume of the track at `index`. Volume lies within the range*

### `isTrackArmed`

```python
isTrackArmed(index: int) -> bool
```

*Returns whether the track at `index` is armed for recording.*

### `isTrackAutomationEnabled`

```python
isTrackAutomationEnabled(index: int, plugIndex: int) -> bool
```

*Returns whether the plugin at `plugIndex` on track at `index` has*

### `isTrackEnabled`

```python
isTrackEnabled(index: int) -> bool
```

*Returns whether the track at `index` is enabled*

### `isTrackMuteLock`

```python
isTrackMuteLock(index: int) -> bool
```

*Returns whether the mute state of the track at `index` is locked.*

### `isTrackMuted`

```python
isTrackMuted(index: int) -> bool
```

*Returns whether the track at `index` is muted.*

### `isTrackPluginValid`

```python
isTrackPluginValid(index: int, plugIndex: int) -> bool
```

*Returns whether a plugin on track `index` in slot `plugIndex` is valid*

### `isTrackRevPolarity`

```python
isTrackRevPolarity(index: int) -> bool
```

*Returns whether the polarity is reversed for the track at `index`.*

### `isTrackSelected`

```python
isTrackSelected(index: int) -> bool
```

*Returns whether the track at `index` is selected.*

### `isTrackSlotsEnabled`

```python
isTrackSlotsEnabled(index: int) -> bool
```

*Returns whether effects are enabled for a particular track, using the*

### `isTrackSolo`

```python
isTrackSolo(index: int) -> bool
```

*Returns whether the track at `index` is solo.*

### `isTrackSwapChannels`

```python
isTrackSwapChannels(index: int) -> bool
```

*Returns whether left and right channels are inverted for a particular*

### `linkChannelToTrack`

```python
linkChannelToTrack(channel: int,
    track: int,
    select: bool = False,) -> None
```

*Link the given channel to the given mixer track.*

### `linkTrackToChannel`

```python
linkTrackToChannel(mode: int) -> None
```

*Link a mixer track to a channel.*

### `muteTrack`

```python
muteTrack(index: int, value: int = -1) -> None
```

*Toggles whether the track at index is muted.*

### `remoteFindEventValue`

```python
remoteFindEventValue(index: int, flags: int = 0, /) -> float
```

*Returns event value.*

### `revTrackPolarity`

```python
revTrackPolarity(index: int, value: bool = False) -> None
```

*Inverts the polarity for a particular track.*

### `selectAll`

```python
selectAll() -> None
```

*Selects all tracks.*

### `selectTrack`

```python
selectTrack(index: int) -> None
```

*Toggles whether the track at `index` is selected.*

### `setActiveTrack`

```python
setActiveTrack(index: int) -> None
```

*Exclusively selects the mixer track at index.*

### `setEqBandwidth`

```python
setEqBandwidth(index: int, band: int, value: float) -> None
```

*Sets the bandwidth of the given band on the given track for the built-in*

### `setEqFrequency`

```python
setEqFrequency(index: int, band: int, value: float) -> None
```

*Sets the frequency of the given band on the given track for the built-in*

### `setEqGain`

```python
setEqGain(index: int, band: int, value: float) -> None
```

*Sets the gain of the given band on the given track for the built-in EQ.*

### `setRouteTo`

```python
setRouteTo(index: int,
    destIndex: int,
    value: bool,
    updateUI: bool = False,) -> None
```

*Route the track at `index` to the track at `destIndex`.*

### `setRouteToLevel`

```python
setRouteToLevel(index: int, destIndex: int, level: float) -> None
```

*Route the track at `index` to the track at `destIndex`, with the level*

### `setSlotColor`

```python
setSlotColor(index: int, slot: int, color: int) -> None
```

*Sets the color of a mixer track FX slot.*

### `setTrackColor`

```python
setTrackColor(index: int, color: int) -> None
```

*Sets the color of the track at `index`.*

### `setTrackName`

```python
setTrackName(index: int, name: str) -> None
```

*Sets the name of track at `index`*

### `setTrackNumber`

```python
setTrackNumber(trackNumber: int, flags: int = 0) -> None
```

*Selects the mixer track at `trackNumber`.*

### `setTrackPan`

```python
setTrackPan(index: int,
    pan: float,
    pickupMode: int = midi.PIM_None,) -> None
```

*Sets the pan of the track at `index`. Pan lies within the range*

### `setTrackStereoSep`

```python
setTrackStereoSep(index: int,
    pan: float,
    pickupMode: int = midi.PIM_None,) -> None
```

*Sets the stereo separation of the track at `index`. Stereo separation*

### `setTrackVolume`

```python
setTrackVolume(index: int,
    volume: float,
    pickupMode: int = midi.PIM_None,) -> None
```

*Sets the volume of the track at `index`. Volume lies within the range*

### `soloTrack`

```python
soloTrack(index: int, value: int = -1, mode: int = -1) -> None
```

*Toggles whether the track at index is solo.*

### `swapTrackChannels`

```python
swapTrackChannels(index: int, value: bool = False) -> None
```

*Toggle whether left and right channels are swapped for the mixer track at*

### `trackCount`

```python
trackCount() -> int
```

*Returns the number of tracks available on the mixer.*

### `trackNumber`

```python
trackNumber() -> int
```

*Returns the index of the first currently selected mixer track.*
