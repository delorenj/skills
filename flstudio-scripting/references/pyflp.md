# FLP File Parsing with PyFLP

## Table of Contents

- [Overview and Use Cases](#overview-and-use-cases)
- [pyflp.Project class](#pyflpproject)
- [pyflp.Channel class](#pyflpchannel)
- [pyflp.Pattern class](#pyflppattern)
- [Example: Load, Modify, Save](#pyflp-example)

## Overview and Use Cases

### Overview

PyFLP is a Python library for reading and writing FL Studio project files (.flp) programmatically, without needing FL Studio running.

### Use Cases

- Batch project processing
- Project analysis and statistics
- Automated project generation
- External project editing tools
- CI/CD pipeline integration

## PyFLP Structure

### `pyflp.Project`

Represents an entire FL Studio project file.

**Attributes:**
- `channels` - List of all channels in the project
- `patterns` - List of all patterns
- `arrangement` - Playlist arrangement
- `mixer` - Mixer track settings
- `tempo` - Project tempo (BPM)
- `version` - FL Studio version that saved the file

**Methods:**
- `load(filename)` - Load FLP file
- `save(filename)` - Save FLP file
- `open(filename)` - Context manager for file access

### `pyflp.Channel`

Represents a synthesizer or sampler channel.

**Attributes:**
- `name` - Channel name
- `color` - Channel color
- `active` - Whether channel is enabled
- `volume` - Channel volume (0-1)
- `pan` - Channel panning (-1 to 1)

**Methods:**
- `get_plugins()` - Get effects on channel

### `pyflp.Pattern`

Represents a pattern/clip in the project.

**Attributes:**
- `name` - Pattern name
- `length` - Pattern length in ticks
- `notes` - List of Note objects in pattern

**Methods:**
- `add_note()` - Add note to pattern
- `delete_note()` - Remove note from pattern

## PyFLP Example

```python
import pyflp

# Load a project
project = pyflp.Project.open('my_song.flp')

# Access channels
for channel in project.channels:
    print(f"{channel.name}: Volume={channel.volume}")

# Modify project
channel = project.channels[0]
channel.volume = 0.5
channel.name = "New Name"

# Save changes
project.save('my_song_modified.flp')
```
