# Screen & LaunchMapPages Module API Reference

## Table of Contents

### Screen Module (9 functions) - AKAI Fire Display
- [init](#init) / [setup](#setup) / [deInit](#deinit) / [update](#update)
- [addMeter](#addmeter) / [addTextLine](#addmeter) / [animateText](#animatetext) / [blank](#animatetext) / [displayBar](#animatetext)
- [displayText](#displaytext) / [displayTimedText](#displaytimedtext)
- [drawRect](#drawrect) / [drawText](#drawrect) / [eraseRect](#drawrect) / [fillRect](#drawrect)

### LaunchMapPages Module (12 functions)
- [init](#init-1) / [length](#length)
- [checkMapForHiddenItem](#checkmapforhiddenitem) / [createOverlayMap](#createoverlaymap)
- [getMapCount](#getmapcount) / [getMapItemAftertouch](#getmapitemaftertouch) / [getMapItemChannel](#getmapitemchannel) / [getMapItemColor](#getmapitemcolor)
- [processMapItem](#processmapitem) / [releaseMapItem](#releasemapitem)
- [setMapItemTarget](#setmapitemtarget) / [updateMap](#updatemap)

---

## SCREEN Module

**Total Functions:** 9

### `addMeter`

```python
addMeter(*args) -> None:
    ...


def addTextLine(text: str, line: int, /) -> None
```

*Add text to a line on the screen?*

### `animateText`

```python
animateText(*args) -> None:
    ...


def blank(*args) -> None:
    ...


def displayBar(zero: int, vertical_position: int, text: str, value, bipolar) -> None
```

*Unsure (undocumented)*

### `deInit`

```python
deInit() -> None
```

*De-initialize the screen of the AKAI Fire*

### `displayText`

```python
displayText(font: int,
    justification: int,
    text_row: int,
    text: str,
    check_if_same: bool,
    display_time: int,) -> None
```

*Unsure (undocumented), but probably displays text on the Akai Fire*

### `displayTimedText`

```python
displayTimedText(text: str, text_row: int) -> None
```

*Unsure (undocumented), but probably displays text for a limited time*

### `drawRect`

```python
drawRect(*args) -> None:
    ...


def drawText(*args) -> None:
    ...


def eraseRect(*args) -> None:
    ...


def fillRect(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    value: int,
    /,) -> None
```

*Draw a filled rectangle to the given position on the screen.*

### `init`

```python
init(display_width: int,
    display_height: int,
    text_row_height: int,
    font_size: int,
    value_a: int,
    value_b: int,
    /,) -> None
```

*Initialize the screen of the AKAI Fire*

### `setup`

```python
setup(sysex_header: int,
    screen_active_timeout: int,
    screen_auto_timeout: int,
    text_scroll_pause: int,
    text_scroll_speed: int,
    text_display_time: int,
    /,) -> None
```

*Set up the AKAI Fire screen.*

### `update`

```python
update() -> None
```

*Notify the Fire that it should update its screen contents*

---

## LAUNCHMAPPAGES Module

**Total Functions:** 12

### `checkMapForHiddenItem`

```python
checkMapForHiddenItem() -> None
```

*Checks for launchpad hidden item???*

### `createOverlayMap`

```python
createOverlayMap(offColor: int,
    onColor: int,
    width: int,
    height: int,) -> None
```

*Creates an overlay map.*

### `getMapCount`

```python
getMapCount(index: int) -> int
```

*Returns the number of items in page at `index`.*

### `getMapItemAftertouch`

```python
getMapItemAftertouch(index: int, itemIndex: int) -> int
```

*Returns the aftertouch for item at `itemIndex` on page at `index`.*

### `getMapItemChannel`

```python
getMapItemChannel(index: int, itemIndex: int) -> int
```

*Returns the channel for item at `itemIndex` on page at `index`.*

### `getMapItemColor`

```python
getMapItemColor(index: int, itemIndex: int) -> int
```

*Returns item color of `itemIndex` in map `index`.*

### `init`

```python
init(deviceName: str, width: int, height: int) -> None
```

*Initialise launchmap pages.*

### `length`

```python
length() -> int
```

*Returns launchmap pages length.*

### `processMapItem`

```python
processMapItem(eventData: FlMidiMsg,
    index: int,
    itemIndex: int,
    velocity: int,) -> None
```

*Process map item at `itemIndex` of page at `index`*

### `releaseMapItem`

```python
releaseMapItem(eventData: FlMidiMsg, index: int) -> None
```

*Release map item at `itemIndex` of page at `index`.*

### `setMapItemTarget`

```python
setMapItemTarget(index: int, itemIndex: int, target: int) -> int
```

*Set target for item at `itemIndex` of page at `index`.*

### `updateMap`

```python
updateMap(index: int) -> None
```

*Updates launchmap page at `index`.*
