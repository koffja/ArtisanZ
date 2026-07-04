# Historical Roast Curve Overlay Design Spec

> **Status**: Approved Approach A — new comparison overlay module
> **Date**: 2026-07-04

## Goal

Allow users to load 2-10 historical roast profiles (.alog files) and overlay them as semi-transparent curves on the main pyqtgraph roasting graph, enabling visual comparison between the current roast and past roasts.

## Architecture

A new self-contained module `plot_comparison_overlay.py` manages the lifecycle of overlay curves. It loads .alog files using ArtisanZ's existing `deserialize()` function, extracts BT/ET/RoR data, and creates semi-transparent `PlotDataItem` objects on the pyqtgraph temperature plot.

The current roast curve remains at full opacity (thick line, z-value 10). Historical curves render at z-value 5 with 30% opacity and 1px width.

Phase 2 (cloud) will extend the data source via `plus/sync.py` without changing the overlay rendering layer.

## Scope

**In scope (Phase 1):**
- Local .alog file selection (multi-select QFileDialog)
- Parse BT/ET time-series from each file
- Render as semi-transparent overlay curves on pyqtgraph plot
- Menu item + toolbar action to trigger
- Clear overlays action
- Auto-clear when new roast or new profile is loaded

**Out of scope (Phase 2 backlog):**
- Cloud data via Cotrix/tastermatrix sync
- BoxplotItem statistical distribution panel
- Auto-detection of same-bean/same-recipe roasts
- Curve labeling/tooltips on hover

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `src/arrassin/plot_comparison_overlay.py` | Overlay curve management | **Create** |
| `src/arrassin/plot_pyqtgraph_widget.py` | Add `comparison_overlay` attribute + cleanup | **Modify** |
| `src/arrassin/main.py` | Add menu item + file dialog handler | **Modify** |
| `src/arrassin/canvas.py` | Auto-clear overlays on redraw/profile load | **Modify** |

## Components

### 1. ComparisonOverlay class (`plot_comparison_overlay.py`)

```python
class ComparisonOverlay:
    """Manages semi-transparent historical roast curves on a pyqtgraph plot."""

    OVERLAY_ALPHA = 70        # 0-255, ~27% opacity
    OVERLAY_WIDTH = 1         # px
    OVERLAY_Z_VALUE = 5       # behind main curves (z=10)
    MAX_OVERLAYS = 10

    def __init__(self, temperature_plot, ror_view_box, pg):
        self._plot = temperature_plot
        self._ror_vb = ror_view_box
        self._pg = pg
        self._curves: list[dict] = []  # each: {'bt': PlotDataItem, 'et': PlotDataItem, 'ror': PlotDataItem|None, 'label': str}

    def add_from_file(self, filepath: str) -> bool:
        """Load a .alog file and add its curves as overlay. Returns True on success."""
        ...

    def clear(self) -> None:
        """Remove all overlay curves."""
        ...

    def set_visible(self, visible: bool) -> None:
        """Show/hide all overlay curves without removing them."""
        ...

    @property
    def count(self) -> int:
        return len(self._curves)
```

### 2. .alog parsing (reuses existing deserialize)

The existing `deserialize(filepath)` function from `atypes.py` returns a `ProfileData` dict containing:
- `time`: list of time values
- `temp1`: ET temperature array
- `temp2`: BT temperature array
- `delta1`: ET RoR array (or computed)
- `delta2`: BT RoR array

ComparisonOverlay calls `deserialize()` on each selected file, extracts these arrays, normalizes time to start at 0, and creates PlotDataItems.

### 3. UI integration (main.py)

- **Menu item**: Roast menu → "对比历史炉次..." (Compare Historical Roasts)
- **Action**: Opens `QFileDialog.getOpenFileNames(filter='*.alog')`
- For each selected file: `target.comparison_overlay.add_from_file(path)`
- **Clear action**: Roast menu → "清除对比曲线" (Clear Comparison Curves)
- **Auto-clear**: In `loadFile()` and `startRoasting()`, call `target.comparison_overlay.clear()`

### 4. Visual design

- Overlay BT curves: pen color `#90A1A8` (DeltaBT palette), alpha=70, width=1
- Overlay ET curves: pen color `#C18A6B` (DeltaET palette), alpha=70, width=1
- Overlay RoR curves: skipped in Phase 1 (keeps graph clean)
- Current roast curves: unchanged (full opacity, thick, shadow pen)
- Overlay curves are NOT clickable, NOT draggable, NOT in legend

## Data Flow

```
User selects .alog files (QFileDialog)
  → ComparisonOverlay.add_from_file(filepath)
    → deserialize(filepath) → ProfileData dict
    → Extract time/temp1/temp2 arrays
    → Normalize time to start at CHARGE
    → Create PlotDataItem(pen=semi-transparent, z=5)
    → temperature_plot.addItem(curve)
    → Store in self._curves
```

## Error Handling

- File not found / corrupt .alog → skip with warning log, continue with other files
- deserialize raises exception → catch, log, skip that file
- More than MAX_OVERLAYS files selected → load first MAX_OVERLAYS, warn user
- No pyqtgraph target active → menu item disabled (check `plot_pyqtgraph_target is not None`)

## Testing

```bash
cd src
python3 -m py_compile artisanlib/plot_comparison_overlay.py
python3 -m pytest test/unitary/arrassin/test_comparison_overlay.py -q
python3 artisan.py  # manual: load a roast, then add comparison curves via menu
```
