# GUI Modernization Phase 2 Matplotlib Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested Matplotlib-compatible renderer adapter that consumes `RoastPlotSnapshot` without changing Artisan's current live plotting runtime path.

**Architecture:** Create a small duck-typed adapter that works with Matplotlib-like axes and line artists, but does not import Qt or Matplotlib. The adapter implements the `LivePlotRenderer` protocol surface by applying snapshots to line artists, preserving view state, and requesting a lazy canvas redraw when available. This slice is a compatibility foundation only; `canvas.py` keeps using the existing `updategraphics()` and `redraw()` paths.

**Tech Stack:** Python dataclasses/protocol consumers, pytest fake axes/lines, ruff, py_compile.

---

## Files

- Create: `src/artisanlib/plot_matplotlib_adapter.py`
  - Owns `MatplotlibSnapshotRenderer`, a duck-typed adapter from `RoastPlotSnapshot` to axes and line artists.
- Create: `src/test/unitary/artisanlib/test_plot_matplotlib_adapter.py`
  - Covers line creation, style propagation, view reset/export, incremental data update, hidden/missing curve behavior, and draw-idle requests.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Mark Phase 2 as having a Matplotlib adapter foundation.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-matplotlib-adapter.md`
  - Track execution of this adapter slice.

## Task 1: Adapter Tests

**Files:**
- Create: `src/test/unitary/artisanlib/test_plot_matplotlib_adapter.py`

- [x] **Step 1: Write the failing tests**

Create `src/test/unitary/artisanlib/test_plot_matplotlib_adapter.py`:

```python
from __future__ import annotations

from artisanlib.plot_matplotlib_adapter import MatplotlibSnapshotRenderer
from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, RendererViewState, RoastPlotSnapshot


class FakeCanvas:
    def __init__(self) -> None:
        self.draw_idle_count = 0

    def draw_idle(self) -> None:
        self.draw_idle_count += 1


class FakeFigure:
    def __init__(self) -> None:
        self.canvas = FakeCanvas()


class FakeLine:
    def __init__(self) -> None:
        self.x: tuple[float, ...] = ()
        self.y: tuple[float | None, ...] = ()
        self.color = ''
        self.line_style = ''
        self.line_width = 0.0
        self.visible = True

    def set_data(self, x: tuple[float, ...], y: tuple[float | None, ...]) -> None:
        self.x = x
        self.y = y

    def set_color(self, color: str) -> None:
        self.color = color

    def set_linestyle(self, line_style: str) -> None:
        self.line_style = line_style

    def set_linewidth(self, line_width: float) -> None:
        self.line_width = line_width

    def set_visible(self, visible: bool) -> None:
        self.visible = visible


class FakeAxis:
    def __init__(self) -> None:
        self.figure = FakeFigure()
        self.lines: list[FakeLine] = []
        self.xlim = (0.0, 1.0)
        self.ylim = (0.0, 1.0)

    def plot(
            self,
            x: tuple[float, ...],
            y: tuple[float | None, ...],
            *,
            label: str,
            color: str,
            linestyle: str,
            linewidth: float) -> list[FakeLine]:
        line = FakeLine()
        line.set_data(x, y)
        line.set_color(color)
        line.set_linestyle(linestyle)
        line.set_linewidth(linewidth)
        self.lines.append(line)
        return [line]

    def set_xlim(self, minimum: float, maximum: float) -> None:
        self.xlim = (minimum, maximum)

    def set_ylim(self, minimum: float, maximum: float) -> None:
        self.ylim = (minimum, maximum)

    def get_xlim(self) -> tuple[float, float]:
        return self.xlim

    def get_ylim(self) -> tuple[float, float]:
        return self.ylim


def _snapshot(*curves: CurveSnapshot) -> RoastPlotSnapshot:
    return RoastPlotSnapshot(
        curves=curves,
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )


def test_set_snapshot_creates_lines_and_applies_axes() -> None:
    temperature_axis = FakeAxis()
    ror_axis = FakeAxis()
    renderer = MatplotlibSnapshotRenderer(temperature_axis=temperature_axis, ror_axis=ror_axis)

    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(
            name='BT',
            x=[0, 1],
            y=[140, 142],
            color='#4E7180',
            line_style='--',
            line_width=2.5,
        ),
        CurveSnapshot.from_sequences(
            name='Delta BT',
            x=[0, 1],
            y=[None, 5.5],
            color='#78905D',
            y_axis='ror',
        ),
    ))

    assert len(temperature_axis.lines) == 1
    assert len(ror_axis.lines) == 1
    assert renderer.line_for('BT') is temperature_axis.lines[0]
    assert temperature_axis.lines[0].x == (0.0, 1.0)
    assert temperature_axis.lines[0].y == (140.0, 142.0)
    assert temperature_axis.lines[0].color == '#4E7180'
    assert temperature_axis.lines[0].line_style == '--'
    assert temperature_axis.lines[0].line_width == 2.5
    assert ror_axis.lines[0].y == (None, 5.5)
    assert temperature_axis.xlim == (-1.0, 12.0)
    assert temperature_axis.ylim == (70.0, 270.0)
    assert ror_axis.xlim == (-1.0, 12.0)
    assert ror_axis.ylim == (-15.0, 25.0)
    assert temperature_axis.figure.canvas.draw_idle_count == 1


def test_update_live_frame_reuses_lines_and_hides_missing_curves_without_resetting_view() -> None:
    temperature_axis = FakeAxis()
    ror_axis = FakeAxis()
    renderer = MatplotlibSnapshotRenderer(temperature_axis=temperature_axis, ror_axis=ror_axis)
    renderer.set_snapshot(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0], y=[140], color='#4E7180'),
        CurveSnapshot.from_sequences(name='Delta BT', x=[0], y=[None], color='#78905D', y_axis='ror'),
    ))
    bt_line = renderer.line_for('BT')
    delta_line = renderer.line_for('Delta BT')
    temperature_axis.set_xlim(2.0, 4.0)

    renderer.update_live_frame(_snapshot(
        CurveSnapshot.from_sequences(name='BT', x=[0, 1, 2], y=[140, 142, 144], color='#4E7180'),
    ))

    assert renderer.line_for('BT') is bt_line
    assert bt_line.x == (0.0, 1.0, 2.0)
    assert bt_line.y == (140.0, 142.0, 144.0)
    assert delta_line.visible is False
    assert temperature_axis.xlim == (2.0, 4.0)


def test_reset_and_export_view_state_round_trip_axes() -> None:
    temperature_axis = FakeAxis()
    ror_axis = FakeAxis()
    renderer = MatplotlibSnapshotRenderer(temperature_axis=temperature_axis, ror_axis=ror_axis)

    renderer.reset_view(RendererViewState(
        time_axis=AxisSnapshot(minimum=3.0, maximum=9.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=100.0, maximum=240.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-8.0, maximum=18.0, label='RoR'),
    ))

    assert renderer.export_view_state() == RendererViewState(
        time_axis=AxisSnapshot(minimum=3.0, maximum=9.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=100.0, maximum=240.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-8.0, maximum=18.0, label='RoR'),
    )
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_adapter.py -q
```

Expected: FAIL because `artisanlib.plot_matplotlib_adapter` does not exist.

## Task 2: Adapter Implementation

**Files:**
- Create: `src/artisanlib/plot_matplotlib_adapter.py`

- [x] **Step 1: Write the minimal adapter**

Create `src/artisanlib/plot_matplotlib_adapter.py`:

```python
from __future__ import annotations

from typing import Any

from artisanlib.plot_snapshot import AxisSnapshot, RendererViewState, RoastPlotSnapshot


class MatplotlibSnapshotRenderer:
    def __init__(self, *, temperature_axis: object, ror_axis: object | None = None, draw_idle: bool = True) -> None:
        self._temperature_axis = temperature_axis
        self._ror_axis = ror_axis
        self._draw_idle = draw_idle
        self._lines: dict[str, object] = {}
        self._last_view_state = RendererViewState(
            time_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Time'),
            temperature_axis=AxisSnapshot(minimum=0.0, maximum=0.0, label='Temperature'),
        )

    def set_snapshot(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_curves(snapshot)
        self.reset_view(snapshot.export_view_state())
        self._request_draw_idle()

    def update_live_frame(self, snapshot: RoastPlotSnapshot) -> None:
        self._apply_curves(snapshot)
        self._request_draw_idle()

    def reset_view(self, view_state: RendererViewState) -> None:
        self._set_axis_limits(self._temperature_axis, view_state.time_axis, view_state.temperature_axis)
        if self._ror_axis is not None and view_state.ror_axis is not None:
            self._set_axis_limits(self._ror_axis, view_state.time_axis, view_state.ror_axis)
        self._last_view_state = view_state

    def export_view_state(self) -> RendererViewState:
        time_axis = _read_axis(self._temperature_axis, 'get_xlim', self._last_view_state.time_axis.label)
        temperature_axis = _read_axis(
            self._temperature_axis,
            'get_ylim',
            self._last_view_state.temperature_axis.label)
        ror_axis = None
        if self._ror_axis is not None and self._last_view_state.ror_axis is not None:
            ror_axis = _read_axis(self._ror_axis, 'get_ylim', self._last_view_state.ror_axis.label)
        return RendererViewState(time_axis=time_axis, temperature_axis=temperature_axis, ror_axis=ror_axis)

    def line_for(self, curve_name: str) -> object | None:
        return self._lines.get(curve_name)

    def _apply_curves(self, snapshot: RoastPlotSnapshot) -> None:
        active_names = {curve.name for curve in snapshot.curves}
        for curve in snapshot.curves:
            line = self._lines.get(curve.name)
            if line is None:
                line = self._create_line(curve)
                self._lines[curve.name] = line
            _call_if_available(line, 'set_data', curve.x, curve.y)
            _call_if_available(line, 'set_color', curve.color)
            _call_if_available(line, 'set_linestyle', curve.line_style)
            _call_if_available(line, 'set_linewidth', curve.line_width)
            _call_if_available(line, 'set_visible', curve.visible)
        for name, line in self._lines.items():
            if name not in active_names:
                _call_if_available(line, 'set_visible', False)

    def _create_line(self, curve: object) -> object:
        axis = self._axis_for_curve(curve)
        plotted = axis.plot(
            curve.x,
            curve.y,
            label=curve.name,
            color=curve.color,
            linestyle=curve.line_style,
            linewidth=curve.line_width,
        )
        if isinstance(plotted, (list, tuple)):
            return plotted[0]
        return plotted

    def _axis_for_curve(self, curve: object) -> Any:
        if getattr(curve, 'y_axis', 'temperature') == 'ror' and self._ror_axis is not None:
            return self._ror_axis
        return self._temperature_axis

    def _set_axis_limits(self, axis: object, time_axis: AxisSnapshot, value_axis: AxisSnapshot) -> None:
        _call_if_available(axis, 'set_xlim', time_axis.minimum, time_axis.maximum)
        _call_if_available(axis, 'set_ylim', value_axis.minimum, value_axis.maximum)

    def _request_draw_idle(self) -> None:
        if not self._draw_idle:
            return
        for axis in (self._temperature_axis, self._ror_axis):
            if axis is None:
                continue
            figure = getattr(axis, 'figure', None)
            if figure is None:
                get_figure = getattr(axis, 'get_figure', None)
                if callable(get_figure):
                    figure = get_figure()
            canvas = getattr(figure, 'canvas', None)
            draw_idle = getattr(canvas, 'draw_idle', None)
            if callable(draw_idle):
                draw_idle()
                return


def _read_axis(axis: object, method_name: str, label: str) -> AxisSnapshot:
    method = getattr(axis, method_name)
    minimum, maximum = method()
    return AxisSnapshot(minimum=float(minimum), maximum=float(maximum), label=label)


def _call_if_available(target: object, method_name: str, *args: object) -> None:
    method = getattr(target, method_name, None)
    if callable(method):
        method(*args)


__all__ = ['MatplotlibSnapshotRenderer']
```

- [x] **Step 2: Run tests to verify they pass**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_adapter.py -q
.venv/bin/python -m py_compile artisanlib/plot_matplotlib_adapter.py
.venv/bin/python -m ruff check artisanlib/plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py
```

Expected: PASS.

## Task 3: Roadmap Update and Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-matplotlib-adapter.md`

- [x] **Step 1: Update roadmap status**

Change the Phase 2 status row to `Snapshot contract + Matplotlib adapter started`.

Update the Phase 2 started note to mention `plot_matplotlib_adapter.py` as an unhooked compatibility foundation.

- [x] **Step 2: Run focused verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py::TestMakeLCDbox -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/gui_theme.py artisanlib/main.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/gui_theme.py artisanlib/main.py test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py
```

Expected: PASS.

- [x] **Step 3: Commit**

Run:

```bash
git add src/artisanlib/plot_matplotlib_adapter.py src/test/unitary/artisanlib/test_plot_matplotlib_adapter.py docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-matplotlib-adapter.md
git commit -m "feat(gui): add matplotlib snapshot adapter"
```

## Next Slice After This Plan

After this plan is complete, add a no-runtime-risk adapter smoke path that renders a `RoastPlotSnapshot` into an offscreen Matplotlib figure during tests or diagnostics. Do not connect it to live `tgraphcanvas.updategraphics()` until benchmark parity and visual equivalence are proven.

## Self-Review

- Spec coverage: This plan adds the Matplotlib compatibility foundation promised by Phase 2 while preserving the existing runtime plotting path.
- Placeholder scan: No placeholder markers are present.
- Type consistency: `MatplotlibSnapshotRenderer`, `RoastPlotSnapshot`, `RendererViewState`, and `AxisSnapshot` names match the existing contract and tests.
