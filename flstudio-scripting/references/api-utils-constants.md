# Utils, Constants & MIDI Reference

## Table of Contents

- [Utils Module (21 functions)](#utils-module-21-functions)
  - [Color](#color)
    - [ColorToRGB](#colortorgb)
    - [RGBToColor](#rgbtocolor)
    - [FadeColor](#fadecolor)
    - [LightenColor](#lightencolor)
    - [HSVtoRGB](#hsvtorgb)
    - [RGBToHSV](#rgbtohsv)
    - [RGBToHSVColor](#rgbtohsvcolor)
  - [Math](#math)
    - [Limited](#limited)
    - [Sign](#sign)
    - [SignOf](#signof)
    - [InterNoSwap](#internoswap)
    - [DivModU](#divmodu)
    - [SwapInt](#swapint)
  - [Geometry](#geometry)
    - [OffsetRect](#offsetrect)
    - [RectOverlap](#rectoverlap)
    - [RectOverlapEqual](#rectoverlapequal)
  - [Music](#music)
    - [GetNoteName](#getnotename)
    - [VolTodB](#voltodb)
  - [Formatting](#formatting)
    - [Zeros](#zeros)
    - [Zeros_Strict](#zeros_strict)
    - [KnobAccelToRes2](#knobacceltores2)
- [Constants and Flags](#constants-and-flags)
  - [Time Units (transport.getSongPos modes)](#time-units-transportgetsongpos-modes)
  - [Loop Modes](#loop-modes)
  - [Start/Stop Options](#startstop-options)
  - [MIDI Status Codes](#midi-status-codes)
  - [PME Flags](#pme-flags)
  - [Undo Flags](#undo-flags)
- [MIDI Reference Tables](#midi-reference-tables)
  - [MIDI CC Numbers](#midi-cc-numbers)
  - [Note Number Reference](#note-number-reference)
  - [Velocity Reference](#velocity-reference)

---

## Utils Module (21 functions)

**Total Functions:** 21

### Color

#### `ColorToRGB`

```python
ColorToRGB(Color: int) -> 'tuple[int, int, int]'
```

*Convert an integer color to an RGB tuple that uses range 0-255.*

#### `RGBToColor`

```python
RGBToColor(R: int, G: int, B: int) -> int
```

*convert an RGB set to an integer color. values must be 0-255*

#### `FadeColor`

```python
FadeColor(StartColor: int, EndColor: int, Value: float) -> int
```

*Fade between two colors*

#### `LightenColor`

```python
LightenColor(Color: int, Value: float) -> int
```

*Lighten a color by a certain amount*

#### `HSVtoRGB`

```python
HSVtoRGB(H: float, S: float, V: float) -> 'tuple[float, float, float]'
```

*Convert an HSV color to an RGB color*

#### `RGBToHSV`

```python
RGBToHSV(R: float, G: float, B: float) -> 'tuple[float, float, float]'
```

*Convert an RGB color to a HSV color*

#### `RGBToHSVColor`

```python
RGBToHSVColor(Color: int) -> 'tuple[float, float, float]'
```

*Convert an RGB color to a HSV color*

### Math

#### `Limited`

```python
Limited(Value: float, Min: float, Max: float) -> float
```

*Limit a value to within the range `Min` - `Max`*

#### `Sign`

```python
Sign(value: 'float | int') -> int
```

*Equivalent to `SignOf()`*

#### `SignOf`

```python
SignOf(value: 'float | int') -> int
```

*Return the sign of a numerical value*

#### `InterNoSwap`

```python
InterNoSwap(X, A, B) -> bool
```

*Returns whether A <= X <= B, ie. whether X lies between A and B*

#### `DivModU`

```python
DivModU(A: int, B: int) -> 'tuple[int, int]'
```

*Return integer division and modulus*

#### `SwapInt`

```python
SwapInt(A, B) -> None
```

*Given A and B, return B and A*

### Geometry

#### `OffsetRect`

```python
OffsetRect(R: TRect, dx: int, dy: int) -> None
```

*Offset a rectangle by `dx` and `dy`*

#### `RectOverlap`

```python
RectOverlap(R1: TRect, R2: TRect) -> bool
```

*Returns whether two rectangles are overlapping*

#### `RectOverlapEqual`

```python
RectOverlapEqual(R1: TRect, R2: TRect) -> bool
```

*Returns whether two rectangles are overlapping or touching*

### Music

#### `GetNoteName`

```python
GetNoteName(NoteNum: int) -> str
```

*Return the note name given a note number*

#### `VolTodB`

```python
VolTodB(Value: float) -> float
```

*Convert volume as a decimal (0.0 - 1.0) to a decibel value*

### Formatting

#### `Zeros`

```python
Zeros(value, nChars, c='0') -> None
```

*TODO*

#### `Zeros_Strict`

```python
Zeros_Strict(value, nChars, c='0') -> None
```

*TODO*

#### `KnobAccelToRes2`

```python
KnobAccelToRes2(Value) -> None
```

*TODO*

---

## Constants and Flags

### Overview

FL Studio's MIDI scripting API defines numerous constants for flags, modes, and configuration values.

### Time Units (transport.getSongPos modes)

```python
SONGLENGTH_MS = 0          # Milliseconds
SONGLENGTH_S = 1           # Seconds
SONGLENGTH_ABSTICKS = 2    # Absolute ticks
SONGLENGTH_BARS = 3        # Bar component of B:S:T
SONGLENGTH_STEPS = 4       # Step component of B:S:T
SONGLENGTH_TICKS = 5       # Tick component of B:S:T
```

### Loop Modes

```python
LOOPMODE_PATTERN = 0       # Pattern looping
LOOPMODE_SONG = 1          # Song looping
```

### Start/Stop Options

```python
SS_Stop = 0                # Stop
SS_StartStep = 1           # Start (step edit mode only)
SS_Start = 2               # Start
```

### MIDI Status Codes

```python
NOTEOFF = 0x8              # Note off status
NOTEON = 0x9               # Note on status
CONTROLCHANGE = 0xB        # CC status
PROGRAMCHANGE = 0xC        # PC status
```

### PME Flags

```python
PME_System = 0x1           # System processing
PME_User = 0x2             # User processing
```

### Undo Flags

```python
UFT_All = 0                # All undo flags
```

---

## MIDI Reference Tables

### MIDI CC Numbers

```
0   Bank Select
1   Modulation
7   Volume
10  Pan
11  Expression
64  Sustain Pedal
120 All Sound Off
121 Reset All Controllers
122 Local Control
123 All Notes Off
```

### Note Number Reference

```
C-1:  0
C0:  12 (lowest MIDI note)
C4:  60 (Middle C)
C5:  72
C8:  108
G9: 127 (highest MIDI note)
```

### Velocity Reference

```
0         Note Off
1-63      Soft (pianissimo)
64-95     Medium (mezzo-forte)
96-127    Loud (fortissimo)
```
