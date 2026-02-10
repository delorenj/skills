# UI & General Module API Reference

## Table of Contents

### UI Module (71 functions)

- **Window Control:** showWindow, hideWindow, getVisible, getFocused, setFocused, nextWindow, selectWindow, closeAllMenu
- **Navigation:** jog, jog2, moveJog, up, down, left, right, next, previous
- **Clipboard:** copy, cut, paste, delete, insert
- **Zoom:** horZoom, verZoom
- **Browser:** navigateBrowser, navigateBrowserMenu, navigateBrowserTabs, toggleBrowserNode, previewBrowserMenuItem, selectBrowserMenuItem, isBrowserAutoHide, setBrowserAutoHide
- **Popup:** closeActivePopupMenu, isInPopupMenu
- **Snap:** getSnapMode, setSnapMode, snapMode, snapOnOff
- **Display Rectangles:** crDisplayRect, miDisplayRect, miDisplayDockRect
- **Hint:** getHintMsg, setHintMsg, getHintValue
- **Info:** getProgTitle, getFocusedFormCaption, getFocusedFormID, getFocusedNodeCaption, getFocusedNodeFileType, getFocusedPluginName
- **State:** isClosing, isLoopRecEnabled, isMetronomeEnabled, isPrecountEnabled, isStartOnInputEnabled, getStepEditMode, setStepEditMode, getTimeDispMin, setTimeDispMin
- **Strip:** strip, stripHold, stripJog
- **Audio:** launchAudioEditor, openEventEditor
- **Version:** getVersion
- **Keys:** enter, escape, no, yes
- **Scroll:** scrollWindow
- **Notification:** showNotification

### General Module (24 functions)

- **Undo System:** undo, undoUp, undoDown, undoUpDown, saveUndo, restoreUndo, restoreUndoLevel
- **History:** getUndoHistoryCount, setUndoHistoryCount, getUndoHistoryLast, setUndoHistoryLast, getUndoHistoryPos, setUndoHistoryPos, getUndoLevelHint
- **State:** getChangedFlag, safeToEdit
- **Timing:** getRecPPB, getRecPPQ
- **Version:** getVersion
- **Score:** clearLog, dumpScoreLog
- **Events:** processRECEvent
- **Audio:** getPrecount, getUseMetronome

---

## UI Module

**Total Functions:** 71

### `closeActivePopupMenu`

```python
closeActivePopupMenu() -> None
```

*Closes a currently-open popup menu (for example a rick-click or drop-down*

### `closeAllMenu`

```python
closeAllMenu() -> None
```

*Close all visible windows, except for the most recently-used FL Studio*

### `copy`

```python
copy() -> int
```

*Copy the selection.*

### `crDisplayRect`

```python
crDisplayRect(left: int,
    top: int,
    right: int,
    bottom: int,
    duration: int,
    flags: int = 0,) -> None
```

*Displays a selection rectangle on the channel rack.*

### `cut`

```python
cut() -> int
```

*Cut the selection.*

### `delete`

```python
delete() -> int
```

*Press the delete key.*

### `down`

```python
down(value: int = 1) -> int
```

*Press the down arrow key.*

### `enter`

```python
enter() -> int
```

*Press the enter key.*

### `escape`

```python
escape() -> int
```

*Press the escape key.*

### `getFocused`

```python
getFocused(index: int) -> bool
```

*Returns whether an FL Studio window is focused (meaning it is the currently*

### `getFocusedFormCaption`

```python
getFocusedFormCaption() -> str
```

*Returns the caption (title) of the focused FL Studio window. This isn't*

### `getFocusedFormID`

```python
getFocusedFormID() -> int
```

*Returns ID of the focused window.*

### `getFocusedNodeCaption`

```python
getFocusedNodeCaption() -> str
```

*Returns the filename associated with the currently selected item in the*

### `getFocusedNodeFileType`

```python
getFocusedNodeFileType() -> int
```

*Returns a value based on the type of the selected file in the browser.*

### `getFocusedPluginName`

```python
getFocusedPluginName() -> str
```

*Returns the plugin name for the active window if it is a plugin, otherwise*

### `getHintMsg`

```python
getHintMsg() -> str
```

*Returns the current message in FL Studio's hint panel.*

### `getHintValue`

```python
getHintValue(value: int, max: int) -> str
```

*Returns `value/max` as a percentage.*

### `getProgTitle`

```python
getProgTitle() -> str
```

*Returns the title of the FL Studio window.*

### `getSnapMode`

```python
getSnapMode() -> int
```

*Returns the current snap mode.*

### `getStepEditMode`

```python
getStepEditMode() -> bool
```

*Returns the value of the "step edit mode" within FL Studio.*

### `getTimeDispMin`

```python
getTimeDispMin() -> bool
```

*Returns `True` when the song position panel is displaying time, rather*

### `getVersion`

```python
getVersion(mode: Literal[0, 1, 2, 3]) -> int:
    ...


@overload
def getVersion(mode: Literal[4, 5, 6] = 4) -> str:
    ...


def getVersion(mode: int = 4) -> 'str | int'
```

*Returns the version number of FL Studio.*

### `getVisible`

```python
getVisible(index: int) -> bool
```

*Returns whether an FL Studio window is currently open.*

### `hideWindow`

```python
hideWindow(index: int) -> None
```

*Hides an FL Studio window specified by `index`.*

### `horZoom`

```python
horZoom(value: int) -> int
```

*Zoom horizontally by `value`.*

### `insert`

```python
insert() -> int
```

*Press the insert key.*

### `isBrowserAutoHide`

```python
isBrowserAutoHide() -> bool
```

*Returns whether the browser is set to auto-hide.*

### `isClosing`

```python
isClosing() -> bool
```

*Returns `True` when FL Studio is closing.*

### `isInPopupMenu`

```python
isInPopupMenu() -> bool
```

*Returns `True` when a popup menu is open (for example a right-click or*

### `isLoopRecEnabled`

```python
isLoopRecEnabled() -> bool
```

*Returns whether loop recording is enabled.*

### `isMetronomeEnabled`

```python
isMetronomeEnabled() -> bool
```

*Returns whether the metronome is enabled.*

### `isPrecountEnabled`

```python
isPrecountEnabled() -> bool
```

*Returns whether precount is enabled.*

### `isStartOnInputEnabled`

```python
isStartOnInputEnabled() -> bool
```

*Returns whether start on input is enabled.*

### `jog`

```python
jog(value: int) -> int
```

*Jog control. Used to map a jog wheel to selections.*

### `jog2`

```python
jog2(value: int) -> int
```

*Alternate jog control. Used to map a jog wheel to relocate.*

### `launchAudioEditor`

```python
launchAudioEditor(reuse: int,
    filename: str,
    index: int,
    preset: str,
    presetGUID: str,) -> int
```

*Launches an audio editor for track at `index` and returns the state of*

### `left`

```python
left(value: int = 1) -> int
```

*Press the left arrow key.*

### `miDisplayDockRect`

```python
miDisplayDockRect(start: int,
    length: int,
    dock_side: int,
    time: int,) -> None
```

*Display a red guide rectangle on the mixer, but contained to one side of*

### `miDisplayRect`

```python
miDisplayRect(start: int,
    end: int,
    duration: int,
    flags: int = 0,) -> None
```

*Displays a selection rectangle on the mixer.*

### `moveJog`

```python
moveJog(value: int) -> int
```

*Used to relocate items with a jog control.*

### `navigateBrowser`

```python
navigateBrowser(direction: int, shiftHeld: bool) -> str
```

*Navigates through the browser. `direction` can be 0 for previous*

### `navigateBrowserMenu`

```python
navigateBrowserMenu(direction: int, shiftHeld: bool) -> str
```

*Navigates through the browser. `direction` can be 0 for previous*

### `navigateBrowserTabs`

```python
navigateBrowserTabs(direction: int) -> str
```

*Navigates between browser tabs, returning the name of the newly selected*

### `next`

```python
next() -> int
```

*Move selection to next element.*

### `nextWindow`

```python
nextWindow() -> int
```

*Switch to the next window.*

### `no`

```python
no() -> int
```

*Press the n key.*

### `openEventEditor`

```python
openEventEditor(eventId: int,
    mode: int,
    newWindow: bool = False,) -> int
```

*Launches an event editor for `eventId`.*

### `paste`

```python
paste() -> int
```

*Paste the selection.*

### `previewBrowserMenuItem`

```python
previewBrowserMenuItem() -> None
```

*Preview the highlighted item in the browser.*

### `previous`

```python
previous() -> int
```

*Move selection to previous element.*

### `right`

```python
right(value: int = 1) -> int
```

*Press the right arrow key.*

### `scrollWindow`

```python
scrollWindow(index: int, value: int, directionFlag: int = 0) -> None
```

*Scrolls on the window specified by `index`. Value is index for whatever is*

### `selectBrowserMenuItem`

```python
selectBrowserMenuItem() -> None
```

*Selects the currently highlighted browser menu item, which is the*

### `selectWindow`

```python
selectWindow(shift: bool) -> int
```

*Switch to the next window, like pressing the `Tab` key. If `shift` is*

### `setBrowserAutoHide`

```python
setBrowserAutoHide(value: bool) -> None
```

*Toggle whether the browser is set to auto-hide.*

### `setFocused`

```python
setFocused(index: int) -> None
```

*Sets which FL Studio window should be focused (meaning it is the currently*

### `setHintMsg`

```python
setHintMsg(msg: str) -> None
```

*Sets the current hint message in FL Studio's hint panel to `msg`.*

### `setSnapMode`

```python
setSnapMode(value: int) -> None
```

*Set the snap mode using an absolute value.*

### `setStepEditMode`

```python
setStepEditMode(newValue: bool) -> None
```

*Sets the value of the "step edit mode" within FL Studio.*

### `setTimeDispMin`

```python
setTimeDispMin() -> None
```

*Toggles whether the song position panel is displaying time or bar and*

### `showNotification`

```python
showNotification(notificationId: int) -> None
```

*Show a notification to the user, which is chosen from a set of notification*

### `showWindow`

```python
showWindow(index: int) -> None
```

*Shows an FL Studio window specified by `index`.*

### `snapMode`

```python
snapMode(value: int) -> int
```

*Changes the snap mode, by shifting it by `value` in the list of modes.*

### `snapOnOff`

```python
snapOnOff() -> int
```

*Toggle whether snapping is enabled globally.*

### `strip`

```python
strip(value: int) -> int
```

*Used by touch-sensitive strip controls.*

### `stripHold`

```python
stripHold(value: int) -> int
```

*Touch-sensitive strip in hold mode.*

### `stripJog`

```python
stripJog(value: int) -> int
```

*Touch-sensitive strip in jog mode.*

### `toggleBrowserNode`

```python
toggleBrowserNode(value: int = -1) -> None
```

*Toggle whether the browser node is expanded.*

### `up`

```python
up(value: int = 1) -> int
```

*Press the up arrow key.*

### `verZoom`

```python
verZoom(value: int) -> int
```

*Zoom vertically by `value`.*

### `yes`

```python
yes() -> int
```

*Press the y key.*

---

## General Module

**Total Functions:** 24

### `clearLog`

```python
clearLog() -> None
```

*Clear the score log.*

### `dumpScoreLog`

```python
dumpScoreLog(time: int, silent: bool = False) -> None
```

*Write recently played MIDI to the selected pattern.*

### `getChangedFlag`

```python
getChangedFlag() -> int
```

*Returns whether a project has been changed since the last save.*

### `getPrecount`

```python
getPrecount() -> bool
```

*Returns whether precount before recording is enabled.*

### `getRecPPB`

```python
getRecPPB() -> int
```

*Returns the current timebase (PPQN) multiplied by the number of beats in a*

### `getRecPPQ`

```python
getRecPPQ() -> int
```

*Returns the current timebase (PPQN), which represents the number of ticks*

### `getUndoHistoryCount`

```python
getUndoHistoryCount() -> int
```

*Returns the total number of items that have ever been added to the undo*

### `getUndoHistoryLast`

```python
getUndoHistoryLast() -> int
```

*Returns the current position in the undo history. The most recent position*

### `getUndoHistoryPos`

```python
getUndoHistoryPos() -> int
```

*Returns the length of the undo history.*

### `getUndoLevelHint`

```python
getUndoLevelHint() -> str
```

*Returns a fraction-like string that shows the position in the undo*

### `getUseMetronome`

```python
getUseMetronome() -> bool
```

*Returns whether the metronome is active.*

### `getVersion`

```python
getVersion() -> int
```

*Returns MIDI Scripting API version number. Note that this is the API*

### `processRECEvent`

```python
processRECEvent(eventId: int, value: int, flags: int) -> int
```

*Processes a REC event, usually changing an automatable value.*

### `restoreUndo`

```python
restoreUndo() -> int
```

*Undo-redo toggle. This behaves in the same way as `undo()`.*

### `restoreUndoLevel`

```python
restoreUndoLevel(level: int) -> int
```

*Undo-redo toggle. This behaves in the same way as `undo()`.*

### `safeToEdit`

```python
safeToEdit() -> bool
```

*Returns whether it is currently safe to perform edit operations in FL*

### `saveUndo`

```python
saveUndo(undoName: str, flags: int, update: bool = True) -> None
```

*Save an undo point into FL Studio's history.*

### `setUndoHistoryCount`

```python
setUndoHistoryCount(value: int) -> None
```

*Removes old elements from the undo history, leaving only the latest*

### `setUndoHistoryLast`

```python
setUndoHistoryLast(index: int, /) -> None
```

*Sets the position in the undo history, where `index = 0` is the most*

### `setUndoHistoryPos`

```python
setUndoHistoryPos(index: int) -> None
```

*Removes recent elements from the undo history, leaving only the earliest*

### `undo`

```python
undo() -> int
```

*Perform an undo toggle, much like pressing Ctrl+Z. If the position in the*

### `undoDown`

```python
undoDown() -> int
```

*Move down in the undo history. This is much like redo in most programs.*

### `undoUp`

```python
undoUp() -> int
```

*Move up in the undo history. This is much like undo in most programs.*

### `undoUpDown`

```python
undoUpDown(value: int) -> int
```

*Move in the undo history by delta `value`.*
