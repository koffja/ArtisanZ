# PyQtGraph Visual Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pyqtgraph-native visual enhancements (phase bands, curve gradients, ROR fills, draggable event markers, shadow pens) to ArtisanZ's roasting curve display, leveraging features matplotlib cannot provide.

**Architecture:** All enhancements are additive to the existing `plot_pyqtgraph_widget.py` → `PyQtGraphPlotTarget` class. Each enhancement is an optional overlay that can be toggled via settings. The matplotlib renderer path in `canvas.py` remains untouched as fallback.

**Tech Stack:** pyqtgraph 0.14.0, PyQt6 6.11.0, PyOpenGL 3.1.10, Python 3.14

## Global Constraints

- pyqtgraph version: `==0.14.0` (locked in `requirements.txt:72`)
- All new code goes in `src/arrassin/plot_pyqtgraph_widget.py` unless noted
- Each enhancement must degrade gracefully (try/except, log warning, skip overlay)
- The matplotlib renderer in `canvas.py` must not be modified
- Colors should use the existing `DEFAULT_GRAPH_PALETTE` from `canvas.py` where possible
- Chinese UI strings must use `QApplication.translate('Label', ...)`

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `src/arrassin/plot_pyqtgraph_widget.py` | Main pyqtgraph widget factory + overlays | **Modify** — add overlay factories |
| `src/arrassin/plot_pyqtgraph_overlays.py` | **New** — overlay classes (phase bands, gradient pen, fills, markers) | **Create** |
| `src/arrassin/plot_pyqtgraph_widget.py:PyQtGraphPlotTarget` | Add methods to attach/detach overlays | **Modify** |
| `src/arrassin/canvas.py` | Pass roasting phase data to pyqtgraph renderer | **Modify** — add data bridge |
| `src/test/unitary/arrassin/test_pyqtgraph_overlays.py` | **New** — unit tests for overlay classes | **Create** |

---

## Task 1: Roasting Phase Bands (LinearRegionItem)

**Visual effect:** Semi-transparent colored bands behind the curves showing Drying (yellow), Maillard (orange), Development (red) phases. Users can drag band edges to adjust phase boundaries.

**Files:**
- Create: `src/arrassin/plot_pyqtgraph_overlays.py`
- Modify: `src/arrassin/plot_pyqtgraph_widget.py` — add `_attach_phase_bands()` call in `create_pyqtgraph_plot_target()`
- Modify: `src/arrassin/canvas.py` — expose phase time boundaries via `tgraphcanvas` attributes
- Test: `src/test/unitary/arrassin/test_pyqtgraph_overlays.py`

**Interfaces:**
- Consumes: `tgraphcanvas.timeindex[0]` (CHARGE time), `tgraphcanvas.timeindex[2]` (DRY end), `tgraphcanvas.timeindex[3]` (FCs), `tgraphcanvas.timeindex[6]` (DROP)
- Produces: `PhaseBandOverlay` class with `update_phases(times: dict) -> None` and `clear() -> None`

**Implementation sketch:**
```python
# In plot_pyqtgraph_overlays.py
from __future__ import annotations
from typing import Any

class PhaseBandOverlay:
    """Manages LinearRegionItem bands for roasting phases on a pyqtgraph plot."""

    PHASE_COLORS = {
        'drying':      (255, 220, 100, 40),   # translucent yellow
        'maillard':    (255, 150, 80, 40),     # translucent orange
        'development': (255, 80, 80, 40),      # translucent red
    }

    def __init__(self, plot: Any, pg: Any) -> None:
        self._plot = plot
        self._pg = pg
        self._regions: list[Any] = []

    def update_phases(self, phase_bounds: dict[str, tuple[float, float] | None]) -> None:
        """phase_bounds example: {'drying': (0.0, 300.0), 'maillard': (300.0, 480.0), ...}"""
        self.clear()
        for name, bounds in phase_bounds.items():
            if bounds is None or bounds[0] is None or bounds[1] is None:
                continue
            t0, t1 = bounds
            if t1 <= t0:
                continue
            rgba = self.PHASE_COLORS.get(name, (200, 200, 200, 30))
            region = self._pg.LinearRegionItem(
                values=[t0, t1],
                orientation='vertical',
                brush=self._pg.mkBrush(*rgba),
                pen=self._pg.mkPen(rgba[0], rgba[1], rgba[2], 120, width=1),
                movable=True,
                swapMode='block',
            )
            region.sigRegionChangeFinished.connect(
                lambda r, n=name: _on_phase_dragged(n, r.getRegion())
            )
            self._plot.addItem(region)
            self._regions.append(region)

    def clear(self) -> None:
        for r in self._regions:
            try:
                self._plot.removeItem(r)
            except Exception:
                pass
        self._regions.clear()


def _on_phase_dragged(name: str, region: tuple[float, float]) -> None:
    """Called when user drags a phase band boundary."""
    # Future: emit a signal to update canvas.py timeindex values
    pass
```

**Integration point in `plot_pyqtgraph_widget.py`:**
```python
# In create_pyqtgraph_plot_target(), after temperature plot is configured:
from artisanlib.plot_pyqtgraph_overlays import PhaseBandOverlay
target._phase_bands = PhaseBandOverlay(temperature_plot, pg)
# Called later when phase data is available:
# target._phase_bands.update_phases(canvas.get_phase_bounds())
```

**Test:**
```python
# test_pyqtgraph_overlays.py
def test_phase_band_overlay_creates_regions():
    overlay = PhaseBandOverlay(mock_plot, mock_pg)
    overlay.update_phases({'drying': (0, 300), 'maillard': (300, 480), 'development': (480, 720)})
    assert len(overlay._regions) == 3

def test_phase_band_overlay_skips_none_bounds():
    overlay = PhaseBandOverlay(mock_plot, mock_pg)
    overlay.update_phases({'drying': (0, 300), 'maillard': (None, 480)})
    assert len(overlay._regions) == 1  # only drying created

def test_phase_band_overlay_clear_removes_all():
    overlay = PhaseBandOverlay(mock_plot, mock_pg)
    overlay.update_phases({'drying': (0, 300)})
    overlay.clear()
    assert len(overlay._regions) == 0
```

---

## Task 2: BT Curve Gradient Coloring (ColorMap.getPen)

**Visual effect:** BT temperature curve color shifts from cool blue at 150°C to hot red at 220°C, encoding temperature magnitude directly in the line color.

**Files:**
- Modify: `src/arrassin/plot_pyqtgraph_overlays.py` — add `create_gradient_pen()` function
- Modify: `src/arrassin/plot_pyqtgraph_widget.py` — apply gradient pen in `_configure_temperature_plot()`

**Interfaces:**
- Consumes: BT temperature data range (min/max from `canvas.py` palette or settings)
- Produces: `QPen` object with gradient applied

**Implementation sketch:**
```python
# In plot_pyqtgraph_overlays.py
def create_gradient_pen(pg: Any, temp_min: float = 150.0, temp_max: float = 250.0,
                        width: int = 2, cmap_name: str = 'CET-L17') -> Any:
    """Create a QPen whose color varies along the Y-axis by temperature value."""
    try:
        cm = pg.colormap.get(cmap_name)
        cm.reverse()  # CET-L17 goes blue→white→red; reversed = red at high temp
        return cm.getPen(span=(temp_min, temp_max), width=width, orientation='vertical')
    except Exception:
        # Fallback: solid color pen
        return pg.mkPen('#FFB300', width=width)
```

**Integration:**
```python
# In _configure_temperature_plot() or a new _apply_bt_gradient() helper:
# Only when pyqtgraph renderer is active and BT curve exists:
gradient_pen = create_gradient_pen(pg, temp_min=150, temp_max=250, width=2)
# Apply to the BT PlotDataItem:
bt_curve.setPen(gradient_pen)
```

---

## Task 3: ROR Area Fill (FillBetweenItem)

**Visual effect:** Semi-transparent red fill between the ROR curve and zero baseline, visually representing ROR intensity duration.

**Files:**
- Modify: `src/arrassin/plot_pyqtgraph_overlays.py` — add `RORFillOverlay` class
- Modify: `src/arrassin/plot_pyqtgraph_widget.py` — attach overlay in `_create_ror_overlay()`

**Implementation sketch:**
```python
class RORFillOverlay:
    """Manages a FillBetweenItem between the ROR curve and a zero baseline."""

    def __init__(self, ror_plot: Any, pg: Any, brush_color: tuple = (255, 100, 100, 80)) -> None:
        self._ror_plot = ror_plot
        self._pg = pg
        self._brush_color = brush_color
        self._zero_curve: Any | None = None
        self._fill_item: Any | None = None

    def attach(self, ror_curve: Any) -> None:
        """Attach fill below the given ROR PlotDataItem."""
        try:
            self._zero_curve = self._pg.PlotDataItem([], [], pen=None)
            self._fill_item = self._pg.FillBetweenItem(
                curve1=ror_curve,
                curve2=self._zero_curve,
                brush=self._pg.mkBrush(*self._brush_color),
            )
            target = self._ror_plot if hasattr(self._ror_plot, 'addItem') else self._ror_plot.plotItem
            target.addItem(self._fill_item)
        except Exception:
            pass

    def update_zero_baseline(self, x_data: list[float]) -> None:
        """Update the zero baseline to match the current x range."""
        if self._zero_curve is not None and x_data:
            self._zero_curve.setData(x_data, [0.0] * len(x_data))

    def detach(self) -> None:
        if self._fill_item is not None:
            try:
                target = self._ror_plot if hasattr(self._ror_plot, 'addItem') else self._ror_plot.plotItem
                target.removeItem(self._fill_item)
            except Exception:
                pass
        self._fill_item = None
        self._zero_curve = None
```

---

## Task 4: Draggable Event Markers (InfiniteLine + InfLineLabel)

**Visual effect:** Vertical lines for CHARGE/DRY/FCs/FCe/SCs/SCe/DROP events, each with a formatted label showing event code + temperature + time. Lines are draggable to fine-tune event timing.

**Files:**
- Modify: `src/arrassin/plot_pyqtgraph_overlays.py` — add `EventMarkerOverlay` class
- Modify: `src/arrassin/canvas.py` — expose event data for pyqtgraph renderer
- Modify: `src/arrassin/plot_pyqtgraph_widget.py` — attach overlay

**Implementation sketch:**
```python
class EventMarkerOverlay:
    """Manages draggable InfiniteLine markers for roasting events."""

    EVENT_COLORS = {
        'CHARGE': '#4CAF50',
        'DRY': '#FF9800',
        'FCs': '#F44336',
        'FCe': '#E91E63',
        'SCs': '#9C27B0',
        'SCe': '#673AB7',
        'DROP': '#795548',
    }

    def __init__(self, plot: Any, pg: Any) -> None:
        self._plot = plot
        self._pg = pg
        self._lines: dict[str, Any] = {}

    def update_events(self, events: list[dict]) -> None:
        """events: [{'code': 'FCs', 'time': 480.0, 'temp': 178.0}, ...]"""
        # Remove lines for events no longer present
        current_codes = {e['code'] for e in events}
        for code in list(self._lines):
            if code not in current_codes:
                self._remove_line(code)

        for event in events:
            code = event['code']
            time_val = event.get('time')
            temp_val = event.get('temp')
            if time_val is None:
                continue

            color = self.EVENT_COLORS.get(code, '#888888')
            label_text = code
            if temp_val is not None:
                label_text += f'\n{temp_val:.0f}°C'

            if code in self._lines:
                self._lines[code].setValue(time_val)
            else:
                line = self._pg.InfiniteLine(
                    pos=time_val,
                    angle=90,
                    pen=self._pg.mkPen(color, width=2, style=QtCore.Qt.PenStyle.DashLine),
                    movable=True,
                    label=self._pg.InfiniteLine(line).label if False else None,  # InfLineLabel setup below
                    labelOpts={
                        'position': 0.95,
                        'color': color,
                        'fill': (255, 255, 255, 200),
                        'movable': True,
                    },
                )
                self._plot.addItem(line)
                self._lines[code] = line

    def _remove_line(self, code: str) -> None:
        line = self._lines.pop(code, None)
        if line is not None:
            try:
                self._plot.removeItem(line)
            except Exception:
                pass

    def clear(self) -> None:
        for code in list(self._lines):
            self._remove_line(code)
```

---

## Task 5: Curve Shadow Pen (shadowPen)

**Visual effect:** BT curve has a black outline behind the colored line, making it readable on any background color (light or dark themes).

**Files:**
- Modify: `src/arrassin/plot_pyqtgraph_widget.py` — apply `shadowPen` when configuring BT/ET curves

**This is the simplest enhancement — one line per curve:**

```python
# In _configure_temperature_plot() or wherever BT/ET PlotDataItem is created:
bt_curve = pg.PlotDataItem(
    pen=pg.mkPen('#FFB300', width=2),         # yellow core
    shadowPen=pg.mkPen('#000000', width=4),   # black outline behind
)
et_curve = pg.PlotDataItem(
    pen=pg.mkPen('#4E7180', width=2),          # blue core
    shadowPen=pg.mkPen('#000000', width=4),    # black outline behind
)
```

---

## Task 6: Crosshair Cursor Enhancement

**Visual effect:** When mouse hovers over the plot, a crosshair line tracks the position, and a TextItem in the corner shows precise time/temperature/ROR values.

**Files:**
- Modify: `src/arrassin/plot_pyqtgraph_widget.py` — enhance `_connect_cursor_tracking()` (L160)

**Current state:** The widget already has cursor tracking at L160-181 (`_connect_cursor_tracking`). This task enhances it with a visual crosshair line:

```python
# Enhancement in _connect_cursor_tracking:
def _connect_cursor_tracking(target: PyQtGraphPlotTarget) -> None:
    vline = None
    hline = None

    def on_mouse_moved(scene_pos):
        # ... existing cursor callback code ...
        # Add crosshair lines:
        nonlocal vline, hline
        if vline is None:
            vline = target._pg.InfiniteLine(angle=90, pen=target._pg.mkPen('#888', width=1, style=QtCore.Qt.PenStyle.DashLine))
            hline = target._pg.InfiniteLine(angle=0, pen=target._pg.mkPen('#888', width=1, style=QtCore.Qt.PenStyle.DashLine))
            target._temperature_plot.addItem(vline, ignoreBounds=True)
            target._temperature_plot.addItem(hline, ignoreBounds=True)
        if point is not None:
            vline.setValue(point.x())
            hline.setValue(point.y())
```

---

## Implementation Priority

| Phase | Tasks | Effort | Visual Impact |
|---|---|---|---|
| **Phase 1** (immediate) | Task 5 (shadowPen), Task 3 (ROR fill) | 30 min | 🔴 High |
| **Phase 2** (1-2 days) | Task 1 (phase bands), Task 4 (event markers) | 2-4 hrs | 🔴 High |
| **Phase 3** (optional) | Task 2 (gradient pen), Task 6 (crosshair) | 2-3 hrs | 🟡 Medium |

---

## Testing Strategy

Each task has unit tests in `test_pyqtgraph_overlays.py`. Integration tests require a running QApplication (use `QT_QPA_PLATFORM=offscreen`).

**Verification commands:**
```bash
cd src
python3 -m pytest test/unitary/arrassin/test_pyqtgraph_overlays.py -q
python3 -m py_compile artisanlib/plot_pyqtgraph_overlays.py artisanlib/plot_pyqtgraph_widget.py
python3 artisan.py  # visual smoke test
```

---

## Rollback

Each enhancement is isolated in `PhaseBandOverlay`, `RORFillOverlay`, `EventMarkerOverlay` classes. To disable any enhancement, comment out the `_attach_*()` call in `create_pyqtgraph_plot_target()`. No other code needs to change.
