# Playlist Module API Reference

**Total Functions:** 41

## Table of Contents

### Track Info
- [trackCount](#trackcount)
- [getTrackName](#gettrackname)
- [setTrackName](#settrackname)
- [getTrackColor](#gettrackcolor)
- [setTrackColor](#settrackcolor)

### Selection
- [selectAll](#selectall)
- [deselectAll](#deselectall)
- [selectTrack](#selecttrack)
- [isTrackSelected](#istrackselected)

### Mute/Solo
- [muteTrack](#mutetrack)
- [isTrackMuted](#istrackmuted)
- [soloTrack](#solotrack)
- [isTrackSolo](#istracksolo)
- [muteTrackLock](#mutetracklock)
- [isTrackMuteLock](#istrackmuteLock)

### Live Mode
- [getLiveStatus](#getlivestatus)
- [getLiveBlockStatus](#getliveblockstatus)
- [getLiveBlockColor](#getliveblockcolor)
- [triggerLiveClip](#triggerliveclip)
- [refreshLiveClips](#refreshliveclips)

### Loop/Trigger
- [getLiveLoopMode](#getliveloopmode)
- [incLiveLoopMode](#incliveloopmode)
- [getLiveTriggerMode](#getlivetriggermode)
- [incLiveTrigMode](#inclivetrigmode)
- [getLiveTrigSnap](#getlivetrigsnap)
- [incLiveTrigSnap](#inclivetrigsnap)
- [getLivePosSnap](#getlivepossnap)
- [incLivePosSnap](#inclivepossnap)

### Position/Display
- [getVisTimeBar](#getvistimebar)
- [getVisTimeStep](#getvistimestep)
- [getVisTimeTick](#getvistimetick)
- [getDisplayZone](#getdisplayzone)
- [liveDisplayZone](#livedisplayzone)
- [lockDisplayZone](#lockdisplayzone)
- [scrollTo](#scrollto)

### Performance
- [getPerformanceModeState](#getperformancemodestate)
- [getTrackActivityLevel](#gettrackactivitylevel)
- [getTrackActivityLevelVis](#gettrackactivitylevelvis)

### Time
- [getSongStartTickPos](#getsongstarttickpos)
- [liveBlockNumToTime](#liveblocknumtotime)
- [liveTimeToBlockNum](#livetimetoblocknum)

---

## Track Info

### `trackCount`

```python
trackCount() -> int
```

*Returns the number of tracks on the playlist.*

### `getTrackName`

```python
getTrackName(index: int) -> str
```

*Returns the name of the track at `index`*

### `setTrackName`

```python
setTrackName(index: int, name: str) -> None
```

*Sets the name of the track at `index`*

### `getTrackColor`

```python
getTrackColor(index: int) -> int
```

*Returns the color of the track at `index`*

### `setTrackColor`

```python
setTrackColor(index: int, color: int) -> None
```

*Sets the color of the track at `index`*

---

## Selection

### `selectAll`

```python
selectAll() -> None
```

*Select all tracks on the playlist*

### `deselectAll`

```python
deselectAll() -> None
```

*Deselect all tracks on the playlist*

### `selectTrack`

```python
selectTrack(index: int) -> None
```

*Toggle whether the track at `index` is selected. A deselected track will*

### `isTrackSelected`

```python
isTrackSelected(index: int) -> bool
```

*Returns whether the track at `index` is selected*

---

## Mute/Solo

### `muteTrack`

```python
muteTrack(index: int, value: int = -1) -> None
```

*Toggle whether the track at `index` is muted. An unmuted track will become*

### `isTrackMuted`

```python
isTrackMuted(index: int,) -> bool
```

*Returns whether the track at `index` is muted*

### `soloTrack`

```python
soloTrack(index: int, value: int = -1, inGroup: bool = False) -> None
```

*Toggle whether the track at `index` is solo. An unsolo track will become*

### `isTrackSolo`

```python
isTrackSolo(index: int) -> bool
```

*Returns whether the track at `index` is solo*

### `muteTrackLock`

```python
muteTrackLock(index: int) -> None
```

*Toggle whether the track at `index`'s mute status is locked (meaning that*

### `isTrackMuteLock`

```python
isTrackMuteLock(index: int) -> bool
```

*Returns whether the mute status of the track at `index` is locked (meaning*

---

## Live Mode

### `getLiveStatus`

```python
getLiveStatus(index: int, mode: int = midi.LB_Status_Default) -> int
```

*Returns the live status for track at `index`.*

### `getLiveBlockStatus`

```python
getLiveBlockStatus(index: int,
    blockNum: int,
    mode: int = midi.LB_Status_Default,) -> int
```

*Returns the live block status for block `blockNum` within the track at*

### `getLiveBlockColor`

```python
getLiveBlockColor(index: int, blockNum: int) -> int
```

*Returns the color for block `blockNum` within the track at `index`.*

### `triggerLiveClip`

```python
triggerLiveClip(index: int,
    subNum: int,
    flags: int,
    velocity: int = -1,) -> None
```

*Triggers live clip for track at `index` and for block `subNum`.*

### `refreshLiveClips`

```python
refreshLiveClips(*args) -> None
```

*Refresh live clips for track at `index`.*

---

## Loop/Trigger

### `getLiveLoopMode`

```python
getLiveLoopMode(index: int) -> int
```

*Get the loop mode of the given track.*

### `incLiveLoopMode`

```python
incLiveLoopMode(index: int, value: int) -> None
```

*Increase live loop mode for track at `index`.*

### `getLiveTriggerMode`

```python
getLiveTriggerMode(index: int) -> int
```

*Get the trigger mode of the given track.*

### `incLiveTrigMode`

```python
incLiveTrigMode(index: int, value: int) -> None
```

*Increase live trigger mode for track at `index`.*

### `getLiveTrigSnap`

```python
getLiveTrigSnap(index: int) -> int
```

*Get the trigger sync mode of the given track.*

### `incLiveTrigSnap`

```python
incLiveTrigSnap(index: int, value: int) -> None
```

*Increase live trigger snap for track at `index`.*

### `getLivePosSnap`

```python
getLivePosSnap(index: int) -> int
```

*Get the position sync mode of the given track.*

### `incLivePosSnap`

```python
incLivePosSnap(index: int, value: int) -> None
```

*Increase live position snap for track at `index`.*

---

## Position/Display

### `getVisTimeBar`

```python
getVisTimeBar() -> int
```

*Returns the current bar number, as shown in the song position panel. See*

### `getVisTimeStep`

```python
getVisTimeStep() -> int
```

*Returns the step number within the song, as shown in the song position*

### `getVisTimeTick`

```python
getVisTimeTick() -> int
```

*Returns the tick number within the song, as shown in the song position*

### `getDisplayZone`

```python
getDisplayZone() -> int
```

*Returns the current display zone in the playlist or zero if none.*

### `liveDisplayZone`

```python
liveDisplayZone(left: int,
    top: int,
    right: int,
    bottom: int,
    duration: int = 0,) -> None
```

*Set the display zone in the playlist to the specified co-ordinates. Use the*

### `lockDisplayZone`

```python
lockDisplayZone(index: int, value: int) -> None
```

*Lock display zone at `index`.*

### `scrollTo`

```python
scrollTo(a: int, b: int, c: int, d: int) -> None
```

*Scroll to the given location?*

---

## Performance

### `getPerformanceModeState`

```python
getPerformanceModeState() -> bool
```

*Returns whether FL Studio's performance mode is enabled.*

### `getTrackActivityLevel`

```python
getTrackActivityLevel(index: int) -> float
```

*Returns the activity level of the track at `index`. This value is either*

### `getTrackActivityLevelVis`

```python
getTrackActivityLevelVis(index: int) -> float
```

*Returns the visual activity level of the track at `index`. This value is a*

---

## Time

### `getSongStartTickPos`

```python
getSongStartTickPos() -> int
```

*Returns the number of ticks before the "song start" marker (which marks the*

### `liveBlockNumToTime`

```python
liveBlockNumToTime(index: int) -> int
```

*Returns the number of ticks before the live block marker at `index`.*

### `liveTimeToBlockNum`

```python
liveTimeToBlockNum(time: int) -> int
```

*Returns the block number that a time (in ticks) is associated with in live*
