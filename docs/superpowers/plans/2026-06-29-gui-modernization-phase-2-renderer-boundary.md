# GUI Modernization Phase 2 Renderer Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start Phase 2 by adding a tested read-only plot snapshot contract that future Matplotlib and PyQtGraph renderers can consume.

**Architecture:** Add a small data-only module that describes curves, event markers, axis ranges, and renderer view state without importing Qt, Matplotlib, or PyQtGraph. This first slice does not alter `canvas.py` runtime behavior; it creates the stable boundary needed before adapters and renderer experiments.

**Current Slice:** The boundary now includes a read-only extractor that can convert a canvas-like object into `RoastPlotSnapshot` for the main ET, BT, Delta ET, and Delta BT curves. It still does not change runtime plotting behavior.

**Tech Stack:** Python dataclasses, `typing.Protocol`, pytest, ruff, py_compile.

---

## Files

- Create: `src/artisanlib/plot_snapshot.py`
  - Owns immutable renderer-facing data types and the `LivePlotRenderer` protocol.
- Create: `src/artisanlib/plot_snapshot_extractor.py`
  - Builds `RoastPlotSnapshot` from canvas-like state without importing Qt or Matplotlib.
- Create: `src/test/unitary/artisanlib/test_plot_snapshot.py`
  - Covers immutability, sequence normalization, visible-curve filtering, axis/view-state export, and length validation.
- Create: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`
  - Covers extraction of main live curves, visibility flags, colors, y-axis assignment, and axis limits.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Mark Phase 2 as started with a renderer-boundary foundation.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-renderer-boundary.md`
  - Track this first Phase 2 slice.

## Task 1: Snapshot Data Contract

**Files:**
- Create: `src/artisanlib/plot_snapshot.py`
- Create: `src/test/unitary/artisanlib/test_plot_snapshot.py`

- [x] **Step 1: Write failing tests**

Create `src/test/unitary/artisanlib/test_plot_snapshot.py`:

```python
import pytest

from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, RoastPlotSnapshot


def test_curve_snapshot_from_sequences_normalizes_to_immutable_tuples() -> None:
    curve = CurveSnapshot.from_sequences(
        name='BT',
        x=[0, 1.5, 3],
        y=[120, None, 145.5],
        color='#4E7180',
        y_axis='temperature',
    )

    assert curve.x == (0.0, 1.5, 3.0)
    assert curve.y == (120.0, None, 145.5)
    assert curve.visible is True
    assert curve.y_axis == 'temperature'


def test_curve_snapshot_rejects_mismatched_sequence_lengths() -> None:
    with pytest.raises(ValueError, match='same length'):
        CurveSnapshot.from_sequences(name='BT', x=[0, 1], y=[120], color='#4E7180')


def test_roast_plot_snapshot_filters_visible_curves_and_exports_view_state() -> None:
    visible = CurveSnapshot.from_sequences(name='BT', x=[0], y=[120], color='#4E7180')
    hidden = CurveSnapshot.from_sequences(name='ET', x=[0], y=[130], color='#B5644F', visible=False)
    snapshot = RoastPlotSnapshot(
        curves=(visible, hidden),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0),
    )

    assert snapshot.visible_curves() == (visible,)
    assert snapshot.export_view_state().time_axis == AxisSnapshot(minimum=-1.0, maximum=12.0)
```

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py -q
```

Expected: FAIL because `artisanlib.plot_snapshot` does not exist.

- [x] **Step 2: Implement the data module**

Create `src/artisanlib/plot_snapshot.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

YAxisName = Literal['temperature', 'ror']


@dataclass(frozen=True, slots=True)
class AxisSnapshot:
    minimum: float
    maximum: float
    label: str = ''


@dataclass(frozen=True, slots=True)
class EventMarkerSnapshot:
    time: float
    label: str
    event_type: int
    color: str
    value: float | None = None


@dataclass(frozen=True, slots=True)
class CurveSnapshot:
    name: str
    x: tuple[float, ...]
    y: tuple[float | None, ...]
    color: str
    visible: bool = True
    y_axis: YAxisName = 'temperature'
    line_style: str = '-'
    line_width: float = 1.0
    fill_to_zero: bool = False

    @classmethod
    def from_sequences(
            cls,
            *,
            name: str,
            x: Sequence[float],
            y: Sequence[float | None],
            color: str,
            visible: bool = True,
            y_axis: YAxisName = 'temperature',
            line_style: str = '-',
            line_width: float = 1.0,
            fill_to_zero: bool = False) -> CurveSnapshot:
        if len(x) != len(y):
            raise ValueError('x and y must have the same length')
        return cls(
            name=name,
            x=tuple(float(value) for value in x),
            y=tuple(None if value is None else float(value) for value in y),
            color=color,
            visible=visible,
            y_axis=y_axis,
            line_style=line_style,
            line_width=line_width,
            fill_to_zero=fill_to_zero,
        )


@dataclass(frozen=True, slots=True)
class RendererViewState:
    time_axis: AxisSnapshot
    temperature_axis: AxisSnapshot
    ror_axis: AxisSnapshot | None = None


@dataclass(frozen=True, slots=True)
class RoastPlotSnapshot:
    curves: tuple[CurveSnapshot, ...]
    temperature_axis: AxisSnapshot
    time_axis: AxisSnapshot
    ror_axis: AxisSnapshot | None = None
    events: tuple[EventMarkerSnapshot, ...] = ()

    def visible_curves(self) -> tuple[CurveSnapshot, ...]:
        return tuple(curve for curve in self.curves if curve.visible)

    def export_view_state(self) -> RendererViewState:
        return RendererViewState(
            time_axis=self.time_axis,
            temperature_axis=self.temperature_axis,
            ror_axis=self.ror_axis,
        )


class LivePlotRenderer(Protocol):
    def set_snapshot(self, snapshot: RoastPlotSnapshot) -> None:
        ...

    def update_live_frame(self, snapshot: RoastPlotSnapshot) -> None:
        ...

    def reset_view(self, view_state: RendererViewState) -> None:
        ...

    def export_view_state(self) -> RendererViewState:
        ...


__all__ = [
    'AxisSnapshot',
    'CurveSnapshot',
    'EventMarkerSnapshot',
    'LivePlotRenderer',
    'RendererViewState',
    'RoastPlotSnapshot',
    'YAxisName',
]
```

- [x] **Step 3: Verify the tests pass**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot.py
```

Expected: PASS.

## Task 2: Roadmap Update and Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-renderer-boundary.md`

- [x] **Step 1: Update roadmap status**

Change the Phase 2 status row from `Not started` to `Boundary contract started`.

Add this implementation note under Phase 2:

```markdown
**Started:** 2026-06-29 with a data-only `plot_snapshot.py` contract. This does not change runtime plotting behavior yet; it prepares a stable renderer-facing surface before Matplotlib adapter or PyQtGraph POC work.
```

- [x] **Step 2: Run focused verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py::TestMakeLCDbox -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/gui_theme.py artisanlib/main.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py artisanlib/gui_theme.py artisanlib/main.py test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py
```

Expected: PASS.

- [x] **Step 3: Commit**

Run:

```bash
git add src/artisanlib/plot_snapshot.py src/test/unitary/artisanlib/test_plot_snapshot.py docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-renderer-boundary.md
git commit -m "feat(gui): add plot snapshot renderer boundary"
```

## Task 3: Canvas-Like Snapshot Extractor

**Files:**
- Create: `src/artisanlib/plot_snapshot_extractor.py`
- Create: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-renderer-boundary.md`

- [x] **Step 1: Write failing tests**

Create `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py` with a fake canvas and fake axes. Verify:

- `timex`, `temp1`, `temp2`, `delta1`, and `delta2` are preserved as immutable snapshot tuples.
- `BTcurve`, `ETcurve`, `DeltaBTflag`, and `DeltaETflag` control visibility.
- `palette` colors are copied into curve snapshots.
- `ax.get_xlim()`, `ax.get_ylim()`, and `delta_ax.get_ylim()` become time, temperature, and RoR axes.

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py -q
```

Expected: FAIL because `artisanlib.plot_snapshot_extractor` does not exist.

- [x] **Step 2: Implement the extractor**

Create `src/artisanlib/plot_snapshot_extractor.py` with `build_roast_plot_snapshot(source: object) -> RoastPlotSnapshot`.

The extractor reads the same canvas-like field names used by the current Matplotlib graph state:

- `timex`
- `temp1` / `temp2`
- `delta1` / `delta2`
- `ETcurve` / `BTcurve`
- `DeltaETflag` / `DeltaBTflag`
- `palette`
- `ax`
- `delta_ax`

It produces BT, ET, Delta BT, and Delta ET curves and axis snapshots only. Event markers, background curves, phase bands, projections, and charge-target annotations remain future slices.

- [x] **Step 3: Verify the extractor slice**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot_extractor.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_snapshot_extractor.py
```

Expected: PASS.

## Next Slice After This Plan

After this plan is complete, create a second Phase 2 plan for a Matplotlib compatibility adapter. That adapter should consume `RoastPlotSnapshot` while keeping existing `updategraphics()` behavior available until benchmarked.

## Self-Review

- Spec coverage: This plan starts Phase 2 by creating the renderer-facing contract promised in the roadmap.
- Placeholder scan: No TBD/TODO placeholders are present.
- Type consistency: `RoastPlotSnapshot`, `RendererViewState`, and `LivePlotRenderer` names are consistent across tests, implementation, and roadmap notes.
