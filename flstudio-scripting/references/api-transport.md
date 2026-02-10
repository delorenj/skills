# Transport Module API Reference

**Total Functions:** 20

## Table of Contents

1. [`continuousMove`](#continuousmove)
2. [`continuousMovePos`](#continuousmovepos)
3. [`fastForward`](#fastforward)
4. [`getHWBeatLEDState`](#gethwbeatledstate)
5. [`getLoopMode`](#getloopmode)
6. [`getSongLength`](#getsonglength)
7. [`getSongPos`](#getsongpos)
8. [`getSongPosHint`](#getsongposhint)
9. [`globalTransport`](#globaltransport)
10. [`isPlaying`](#isplaying)
11. [`isRecording`](#isrecording)
12. [`markerJumpJog`](#markerjumpjog)
13. [`markerSelJog`](#markerseljog)
14. [`record`](#record)
15. [`rewind`](#rewind)
16. [`setLoopMode`](#setloopmode)
17. [`setPlaybackSpeed`](#setplaybackspeed)
18. [`setSongPos`](#setsongpos)
19. [`start`](#start)
20. [`stop`](#stop)

### `continuousMove`

```python
continuousMove(speed: int, startStop: int) -> None
```

*Sets playback speed, allowing a scrub-like functionality.*

### `continuousMovePos`

```python
continuousMovePos(speed: int, startStop: int) -> None
```

*Sets playback speed, allowing a scrub-like functionality.*

### `fastForward`

```python
fastForward(startStop: int, flags: int = midi.GT_All) -> None
```

*Fast-forwards the playback position.*

### `getHWBeatLEDState`

```python
getHWBeatLEDState() -> int
```

*Returns the state of the beat indicator.*

### `getLoopMode`

```python
getLoopMode() -> int
```

*Returns the current looping mode.*

### `getSongLength`

```python
getSongLength(mode: int) -> int
```

*Returns the total length of the song.*

### `getSongPos`

```python
getSongPos(mode: Literal[-1] = -1) -> float:
    ...


@overload
def getSongPos(mode: Literal[0, 1, 2, 3, 4, 5]) -> int:
    ...


def getSongPos(mode: int = -1) -> 'float | int'
```

*Returns the playback position.*

### `getSongPosHint`

```python
getSongPosHint() -> str
```

*Returns a hint for the current playback position in .*

### `globalTransport`

```python
globalTransport(command: int,
    value: int,
    pmeflags: int = midi.PME_System,
    flags=midi.GT_All,) -> int
```

*Used as a generic way to run transport commands if a specific function*

### `isPlaying`

```python
isPlaying() -> bool
```

*Returns `True` if playback is currently occurring.*

### `isRecording`

```python
isRecording() -> bool
```

*Returns whether recording is enabled.*

### `markerJumpJog`

```python
markerJumpJog(value: int, flags: int = midi.GT_All) -> None
```

*Jump to a marker position, where `value` is an delta (increment) value.*

### `markerSelJog`

```python
markerSelJog(value: int, flags: int = midi.GT_All) -> None
```

*Select a marker, where `value` is an delta (increment) value.*

### `record`

```python
record() -> None
```

*Toggles recording.*

### `rewind`

```python
rewind(startStop: int, flags: int = midi.GT_All) -> None
```

*Rewinds the playback position.*

### `setLoopMode`

```python
setLoopMode() -> None
```

*Toggles the looping mode between pattern and song.*

### `setPlaybackSpeed`

```python
setPlaybackSpeed(speedMultiplier: float) -> None
```

*Sets a playback speed multiplier.*

### `setSongPos`

```python
setSongPos(position: float, mode: Literal[-1] = -1) -> None:
    ...


@overload
def setSongPos(position: int, mode: Literal[0, 1, 2, 3, 4, 5]) -> None:
    ...


def setSongPos(position: 'float | int', mode: int = -1) -> None
```

*Sets the playback position.*

### `start`

```python
start() -> None
```

*Start or pause playback (play/pause).*

### `stop`

```python
stop() -> None
```

*Stop playback.*
