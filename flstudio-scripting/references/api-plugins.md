# Plugins Module API Reference

## Table of Contents

### Plugin Info
- [isValid](#isvalid)
- [getPluginName](#getpluginname)
- [getName](#getname)
- [getColor](#getcolor)

### Parameters
- [getParamCount](#getparamcount)
- [getParamName](#getparamname)
- [getParamValue](#getparamvalue)
- [getParamValueString](#getparamvaluestring)
- [setParamValue](#setparamvalue)

### Presets
- [getPresetCount](#getpresetcount)
- [nextPreset](#nextpreset)
- [prevPreset](#prevpreset)

### Pads
- [getPadInfo](#getpadinfo)

**Total Functions:** 13

---

## Plugin Info

### `isValid`

```python
isValid(index: int,
    slotIndex: int = -1,
    useGlobalIndex: bool = False,) -> bool
```

*Returns whether there is a valid plugin at `index`/`slotIndex`.*

### `getPluginName`

```python
getPluginName(index: int,
    slotIndex: int = -1,
    userName: bool = False,
    useGlobalIndex: bool = False,) -> str
```

*Returns the name of the plugin at `index`/slotIndex`. This returns the*

### `getName`

```python
getName(index: int,
    slotIndex: int = -1,
    flag: int = midi.FPN_Param,
    paramIndex: int = 0,
    useGlobalIndex: bool = False,) -> str
```

*Returns various names for parts of plugins for the plugin at*

### `getColor`

```python
getColor(index: int,
    slotIndex: int = -1,
    flag: int = midi.GC_BackgroundColor,
    useGlobalIndex: bool = False,) -> int
```

*Returns various plugin color parameter values for the plugin at*

---

## Parameters

### `getParamCount`

```python
getParamCount(index: int,
    slotIndex: int = -1,
    useGlobalIndex: bool = False,) -> int
```

*Returns the number of parameters that a plugin has.*

### `getParamName`

```python
getParamName(paramIndex: int,
    index: int,
    slotIndex: int = -1,
    useGlobalIndex: bool = False,) -> str
```

*Returns the name of the parameter at `paramIndex` for the plugin at*

### `getParamValue`

```python
getParamValue(paramIndex: int,
    index: int,
    slotIndex: int = -1,
    useGlobalIndex: bool = False,) -> float
```

*Returns the value of the parameter at `paramIndex` for the plugin at*

### `getParamValueString`

```python
getParamValueString(paramIndex: int,
    index: int,
    slotIndex: int = -1,
    pickupMode: int = midi.PIM_None,
    useGlobalIndex: bool = False,) -> str
```

*Returns a string value of the parameter at `paramIndex` for the plugin at*

### `setParamValue`

```python
setParamValue(value: float,
    paramIndex: int,
    index: int,
    slotIndex: int = -1,
    pickupMode: int = 0,
    useGlobalIndex: bool = False,) -> None
```

*Sets the value of the parameter at `paramIndex` for the plugin at*

---

## Presets

### `getPresetCount`

```python
getPresetCount(index: int,
    slotIndex: int = -1,
    useGlobalIndex: bool = False,) -> int
```

*Returns the number of presets available for the selected plugin.*

### `nextPreset`

```python
nextPreset(index: int,
    slotIndex: int = -1,
    useGlobalIndex: bool = False,) -> None
```

*Navigate to the next preset for plugin at `index`/`slotIndex`.*

### `prevPreset`

```python
prevPreset(index: int,
    slotIndex: int = -1,
    useGlobalIndex: bool = False,) -> None
```

*Navigate to the previous preset for plugin at `index`/`slotIndex`.*

---

## Pads

### `getPadInfo`

```python
getPadInfo(chanIndex: int,
    slotIndex: int = -1,
    paramOption: int = 0,
    paramIndex: int = -1,
    useGlobalIndex: bool = False,) -> int
```

*Returns info about drum pads.*
