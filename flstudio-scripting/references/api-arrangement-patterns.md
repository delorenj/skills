# Arrangement & Patterns Module API Reference

## Table of Contents

- [Arrangement Module (9 functions)](#arrangement-module-9-functions)
  - [addAutoTimeMarker](#addautotimemarker)
  - [currentTime](#currenttime)
  - [currentTimeHint](#currenttimehint)
  - [getMarkerName](#getmarkername)
  - [jumpToMarker](#jumptomarker)
  - [liveSelection](#liveselection)
  - [liveSelectionStart](#liveselectionstart)
  - [selectionEnd](#selectionend)
  - [selectionStart](#selectionstart)
- [Patterns Module (25 functions)](#patterns-module-25-functions)
  - [burnLoop](#burnloop)
  - [clonePattern](#clonepattern)
  - [deselectAll](#deselectall)
  - [ensureValidNoteRecord](#ensurevalidnoterecord)
  - [findFirstNextEmptyPat](#findfirstnextemptypat)
  - [getActivePatternGroup](#getactivepatterngroup)
  - [getBlockSetStatus](#getblocksetstatus)
  - [getChannelLoopStyle](#getchannelloopstyle)
  - [getPatternColor](#getpatterncolor)
  - [getPatternGroupCount](#getpatterngroupcount)
  - [getPatternGroupName](#getpatterngroupname)
  - [getPatternLength](#getpatternlength)
  - [getPatternName](#getpatternname)
  - [getPatternsInGroup](#getpatternsingroup)
  - [isPatternDefault](#ispatterndefault)
  - [isPatternSelected](#ispatternselected)
  - [jumpToPattern](#jumptopattern)
  - [patternCount](#patterncount)
  - [patternMax](#patternmax)
  - [patternNumber](#patternnumber)
  - [selectAll](#selectall)
  - [selectPattern](#selectpattern)
  - [setChannelLoop](#setchannelloop)
  - [setPatternColor](#setpatterncolor)
  - [setPatternName](#setpatternname)

## Arrangement Module (9 functions)

**Total Functions:** 9

### `addAutoTimeMarker`

```python
addAutoTimeMarker(time: int, name: str) -> None
```

*Add an automatic time marker at the given `time`.*

### `currentTime`

```python
currentTime(snap: int) -> int
```

*Returns the current time in the current arrangement, in terms of ticks.*

### `currentTimeHint`

```python
currentTimeHint(mode: int,
    time: int,
    setRecPPB: int = 0,
    isLength: int = 0,) -> str
```

*Returns a hint string for the given time, formatted as: `"Bar:Step:Tick"`.*

### `getMarkerName`

```python
getMarkerName(index: int) -> str
```

*Returns the name of the marker at `index`.*

### `jumpToMarker`

```python
jumpToMarker(delta: int, select: bool) -> None
```

*Jumps to the marker at the given delta index.*

### `liveSelection`

```python
liveSelection(time: int, stop: bool) -> None
```

*Set a live selection point at `time`.*

### `liveSelectionStart`

```python
liveSelectionStart() -> int
```

*Returns the start time of the current live selection.*

### `selectionEnd`

```python
selectionEnd() -> int
```

*Returns the returns the end time of the current selection.*

### `selectionStart`

```python
selectionStart() -> int
```

*Returns the returns the start time of the current selection.*

## Patterns Module (25 functions)

**Total Functions:** 25

### `burnLoop`

```python
burnLoop(index: int, storeUndo: int = 1, updateUi: int = 1) -> None
```

*For a pattern where looping of step sequenced channels is enabled, disable*

### `clonePattern`

```python
clonePattern(index: int | None = None) -> None
```

*Clones the pattern at the given index*

### `deselectAll`

```python
deselectAll() -> None
```

*Deselects all patterns.*

### `ensureValidNoteRecord`

```python
ensureValidNoteRecord(index: int, playNow: int = 0, /) -> int
```

*Ensures valid note on the pattern at `index`.*

### `findFirstNextEmptyPat`

```python
findFirstNextEmptyPat(flags: int, x: int = -1, y: int = -1) -> None
```

*Selects the first or next empty pattern.*

### `getActivePatternGroup`

```python
getActivePatternGroup() -> int
```

*Returns the index of the currently-selected pattern group.*

### `getBlockSetStatus`

```python
getBlockSetStatus(left: int, top: int, right: int, bottom: int) -> int
```

*Returns the status of the live block.*

### `getChannelLoopStyle`

```python
getChannelLoopStyle(pattern: int, channel: int, /) -> int
```

*Return the loop point of the given channel for the pattern at the given*

### `getPatternColor`

```python
getPatternColor(index: int) -> int
```

*Returns the color of the pattern at `index`.*

### `getPatternGroupCount`

```python
getPatternGroupCount() -> int
```

*Returns the number of user-defined pattern groups.*

### `getPatternGroupName`

```python
getPatternGroupName(index: int, /) -> str
```

*Returns the name of the pattern group at index.*

### `getPatternLength`

```python
getPatternLength(index: int) -> int
```

*Returns the length of the pattern at `index` in beats.*

### `getPatternName`

```python
getPatternName(index: int) -> str
```

*Returns the name of the pattern at `index`.*

### `getPatternsInGroup`

```python
getPatternsInGroup(index: int, /) -> tuple[int, ...]
```

*Returns a tuple containing all the patterns in the group at index.*

### `isPatternDefault`

```python
isPatternDefault(index: int) -> bool
```

*Returns whether the pattern at the given index has changed from the default*

### `isPatternSelected`

```python
isPatternSelected(index: int) -> bool
```

*Returns whether the pattern at `index` is selected.*

### `jumpToPattern`

```python
jumpToPattern(index: int) -> None
```

*Scroll the patterns list to the pattern at `index`, then activate it and*

### `patternCount`

```python
patternCount() -> int
```

*Returns the number of patterns in the project which have been modified from*

### `patternMax`

```python
patternMax() -> int
```

*Returns the maximum number of patterns that can be created. In FL Studio*

### `patternNumber`

```python
patternNumber() -> int
```

*Returns the index for the currently active pattern.*

### `selectAll`

```python
selectAll() -> None
```

*Selects all patterns.*

### `selectPattern`

```python
selectPattern(index: int,
    value: int = -1,
    preview: bool = False,) -> None
```

*Selects the pattern at `index`.*

### `setChannelLoop`

```python
setChannelLoop(channel: int, loopPoint: int, /) -> str
```

*Set the loop point of the given channel for the current pattern.*

### `setPatternColor`

```python
setPatternColor(index: int, color: int) -> None
```

*Sets the color of the pattern at `index`.*

### `setPatternName`

```python
setPatternName(index: int, name: str) -> None
```

*Sets the name of pattern at `index`.*
