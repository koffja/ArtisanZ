# GUI Modernization Phase 2 Offscreen Matplotlib Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the snapshot renderer boundary can drive a real Matplotlib Agg figure without touching the live `canvas.py` runtime path.

**Architecture:** Add a tiny diagnostic renderer helper that builds a Matplotlib `Figure`, renders a `RoastPlotSnapshot` through `MatplotlibSnapshotRenderer`, and returns PNG bytes plus exported view state. Matplotlib imports stay inside the helper so ordinary module import stays light. Tests run headlessly through Agg and assert the PNG signature, axis round-trip state, and real line creation.

**Tech Stack:** Matplotlib Agg, `BytesIO`, pytest, ruff, py_compile.

---

## Files

- Create: `src/artisanlib/plot_matplotlib_smoke.py`
  - Owns `render_snapshot_to_png_bytes()`, a no-Qt diagnostic smoke helper for real Matplotlib rendering.
- Create: `src/test/unitary/artisanlib/test_plot_matplotlib_smoke.py`
  - Covers offscreen PNG rendering, view-state export, and real Matplotlib line creation.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Mark Phase 2 as having an offscreen Matplotlib smoke foundation.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-offscreen-matplotlib-smoke.md`
  - Track this plan's execution.

## Task 1: Offscreen Smoke Tests

**Files:**
- Create: `src/test/unitary/artisanlib/test_plot_matplotlib_smoke.py`

- [x] **Step 1: Write the failing test**

Create `src/test/unitary/artisanlib/test_plot_matplotlib_smoke.py`:

```python
from __future__ import annotations

from artisanlib.plot_matplotlib_smoke import render_snapshot_to_png_bytes
from artisanlib.plot_snapshot import AxisSnapshot, CurveSnapshot, RendererViewState, RoastPlotSnapshot


def test_render_snapshot_to_png_bytes_uses_real_matplotlib_axes() -> None:
    snapshot = RoastPlotSnapshot(
        curves=(
            CurveSnapshot.from_sequences(name='BT', x=[0, 1, 2], y=[140, 142, 144], color='#4E7180'),
            CurveSnapshot.from_sequences(
                name='Delta BT',
                x=[0, 1, 2],
                y=[None, 5.0, 5.5],
                color='#78905D',
                y_axis='ror',
            ),
        ),
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )

    result = render_snapshot_to_png_bytes(snapshot, width=3.0, height=2.0, dpi=80)

    assert result.png_bytes.startswith(b'\x89PNG\r\n\x1a\n')
    assert len(result.png_bytes) > 1000
    assert result.temperature_line_count == 1
    assert result.ror_line_count == 1
    assert result.view_state == RendererViewState(
        time_axis=AxisSnapshot(minimum=-1.0, maximum=12.0, label='Time'),
        temperature_axis=AxisSnapshot(minimum=70.0, maximum=270.0, label='Temperature'),
        ror_axis=AxisSnapshot(minimum=-15.0, maximum=25.0, label='RoR'),
    )
```

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_smoke.py -q
```

Expected: FAIL because `artisanlib.plot_matplotlib_smoke` does not exist.

## Task 2: Diagnostic Smoke Helper

**Files:**
- Create: `src/artisanlib/plot_matplotlib_smoke.py`

- [x] **Step 1: Write the minimal implementation**

Create `src/artisanlib/plot_matplotlib_smoke.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from artisanlib.plot_matplotlib_adapter import MatplotlibSnapshotRenderer
from artisanlib.plot_snapshot import RendererViewState, RoastPlotSnapshot


@dataclass(frozen=True, slots=True)
class MatplotlibSmokeRenderResult:
    png_bytes: bytes
    view_state: RendererViewState
    temperature_line_count: int
    ror_line_count: int


def render_snapshot_to_png_bytes(
        snapshot: RoastPlotSnapshot,
        *,
        width: float = 4.0,
        height: float = 3.0,
        dpi: int = 100) -> MatplotlibSmokeRenderResult:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    figure = Figure(figsize=(width, height), dpi=dpi)
    FigureCanvasAgg(figure)
    temperature_axis = figure.add_subplot(111)
    ror_axis = temperature_axis.twinx() if snapshot.ror_axis is not None else None
    renderer = MatplotlibSnapshotRenderer(
        temperature_axis=temperature_axis,
        ror_axis=ror_axis,
        draw_idle=False,
    )

    renderer.set_snapshot(snapshot)
    buffer = BytesIO()
    figure.savefig(buffer, format='png')

    return MatplotlibSmokeRenderResult(
        png_bytes=buffer.getvalue(),
        view_state=renderer.export_view_state(),
        temperature_line_count=len(temperature_axis.lines),
        ror_line_count=0 if ror_axis is None else len(ror_axis.lines),
    )


__all__ = ['MatplotlibSmokeRenderResult', 'render_snapshot_to_png_bytes']
```

- [x] **Step 2: Run tests to verify they pass**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_smoke.py -q
.venv/bin/python -m py_compile artisanlib/plot_matplotlib_smoke.py
.venv/bin/python -m ruff check artisanlib/plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py
```

Expected: PASS.

## Task 3: Roadmap Update and Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-offscreen-matplotlib-smoke.md`

- [x] **Step 1: Update roadmap status**

Change the Phase 2 status row to `Snapshot contract + offscreen Matplotlib smoke`.

Update the Phase 2 started note to mention `plot_matplotlib_smoke.py` as a diagnostic path only, not a live renderer replacement.

- [x] **Step 2: Run focused verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py
```

Expected: PASS.

- [x] **Step 3: Commit**

Run:

```bash
git add src/artisanlib/plot_matplotlib_smoke.py src/test/unitary/artisanlib/test_plot_matplotlib_smoke.py docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-offscreen-matplotlib-smoke.md
git commit -m "feat(gui): add offscreen matplotlib snapshot smoke"
```

## Next Slice After This Plan

After this plan is complete, expand `RoastPlotSnapshot` coverage to include event markers and phase bands before attempting a PyQtGraph live plot prototype.

## Self-Review

- Spec coverage: This plan proves the Matplotlib adapter can render through a real offscreen Matplotlib backend while keeping live plotting untouched.
- Placeholder scan: No placeholder markers are present.
- Type consistency: `MatplotlibSmokeRenderResult`, `render_snapshot_to_png_bytes`, `RoastPlotSnapshot`, and `RendererViewState` names are consistent across tests and implementation.
