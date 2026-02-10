# Piano Roll & Edison Audio Scripting API

## Table of Contents

**Piano Roll API:**
- [flpianoroll.Note class (properties and methods)](#flpianorollnote)
- [flpianoroll.Marker class (properties and methods)](#flpianorollmarker)
- [flpianoroll.ScriptDialog class (methods)](#flpianorollscriptdialog)
- [flpianoroll.score object (properties and methods)](#flpianorollscore)

**Edison Audio API:**
- [enveditor.Utils module](#enveditorutils)

---

## Piano Roll Scripting API

### Overview

Piano roll scripts provide direct access to notes and markers in FL Studio's piano roll editor. They run within the context of the active piano roll when the user invokes them.

### Core Classes

### `flpianoroll.Note`

Represents a single note in the piano roll.

**Properties:**
- `number` (int) - MIDI note number (0-127), where 60 = Middle C
- `time` (int) - Note start time in ticks
- `length` (int) - Note duration in ticks
- `velocity` (float) - Note velocity (0.0-1.0)
- `pan` (float) - Panning (-1.0 to 1.0, 0.5 = center)
- `release` (float) - Note release (0.0-1.0)
- `color` (int) - Note color index (0-15)
- `fcut` (float) - Filter cutoff (0.0-1.0)
- `fres` (float) - Filter resonance (0.0-1.0)
- `pitchofs` (int) - Pitch offset in cents
- `repeats` (int) - Repeat mode (0-14)
- `slide` (bool) - Slide note flag
- `porta` (bool) - Portamento note flag
- `group` (int) - Group number for linking notes

**Methods:**
- `__init__()` - Create new note instance

### `flpianoroll.Marker`

Represents a marker in the piano roll.

**Properties:**
- `name` (str) - Marker name/label
- `time` (int) - Marker position in ticks
- `color` (int) - Marker color (0-15)

**Methods:**
- `__init__()` - Create new marker instance

### `flpianoroll.ScriptDialog`

Create and display dialog windows in piano roll scripts.

**Methods:**
- `__init__(title: str)` - Create dialog with title
- `add...()` - Various add methods for buttons, sliders, etc.
- `show()` - Display the dialog window

### `flpianoroll.score`

Access the current piano roll pattern.

**Properties:**
- `notes` - List of Note objects
- `markers` - List of Marker objects
- `length` - Pattern length in ticks

**Methods:**
- `addNote(note: Note) -> Note` - Add a note to the pattern
- `deleteNote(note: Note)` - Remove a note
- `clear()` - Clear all notes and markers
- `undo()` / `redo()` - Undo/redo operations

---

## Edison Audio Scripting API

### Overview

Edison scripts run within the Edison sample editor and can manipulate audio samples and access the audio editor's utilities.

### Key Modules

### `enveditor.Utils`

Utility functions for Edison sample editing.

**Available utilities:**
- Audio processing helpers
- Sample analysis functions
- Visualization utilities
