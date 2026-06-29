# GUI Modernization Phase 2 Real PyQtGraph And Phase 3 Smoothing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the PyQtGraph renderer POC against the newly installed dependencies, then start Phase 3 by extracting a tested pure smoothing-weight decision from `sample_processing()`.

**Architecture:** Keep live `canvas.py` rendering on Matplotlib while adding a real PyQtGraph smoke helper that builds actual `PlotWidget` objects offscreen and renders the existing `RoastPlotSnapshot`. For Phase 3, add a small data-only processing module and replace only the local smoothing-weight selection inside `sample_processing()`, preserving current behavior and cache semantics.

**Tech Stack:** PyQt6 offscreen widgets, pyqtgraph 0.14.0, PyOpenGL 3.1.10, pytest, pure Python processing helpers, ruff, py_compile.

---

## Files

- Modify: `src/requirements.txt`
  - Track the installed `pyqtgraph` and `PyOpenGL` dependencies.
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
  - Add a real `pyqtgraph.mkPen()` default pen path while preserving duck-typed fake tests through an injectable pen factory.
- Create: `src/artisanlib/plot_pyqtgraph_smoke.py`
  - Render a `RoastPlotSnapshot` through real `pyqtgraph.PlotWidget` objects in offscreen mode.
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`
  - Pass a fake pen factory so tests stay deterministic when pyqtgraph is installed.
- Create: `src/test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py`
  - Verify real PyQtGraph PlotWidgets accept snapshot curves, event markers, ranges, and OpenGL request plumbing.
- Create: `src/artisanlib/sample_processing.py`
  - Own pure smoothing-weight helpers for Phase 3.
- Create: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover smoothing weights with/without dropouts and invalid curve filter values.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure smoothing helper inside `tgraphcanvas.sample_processing()`.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Mark Phase 2 as dependency-backed and Phase 3 as started.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-real-pyqtgraph-phase-3-smoothing.md`
  - Track execution.

## Task 1: Real PyQtGraph Smoke

**Files:**
- Create: `src/test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py`
- Create: `src/artisanlib/plot_pyqtgraph_smoke.py`
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`

- [x] **Step 1: Write failing smoke test**

Add a test that imports `render_snapshot_with_pyqtgraph()`, renders a snapshot with one temperature curve, one RoR curve, and one event marker, and asserts:

- `temperature_item_count == 1`
- `ror_item_count == 1`
- `event_item_count == 2`
- exported view state matches the snapshot axes
- `opengl_requested is True`

- [x] **Step 2: Run the smoke test to verify it fails**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py -q
```

Expected: FAIL because `artisanlib.plot_pyqtgraph_smoke` does not exist yet.

- [x] **Step 3: Implement real smoke helper and pen factory**

Implement `plot_pyqtgraph_smoke.py` with:

- `PyQtGraphSmokeRenderResult`
- `render_snapshot_with_pyqtgraph(snapshot, use_opengl=True)`

Update `PyQtGraphSnapshotRenderer` so:

- tests can inject `pen_factory`
- default pen creation uses `pyqtgraph.mkPen()` when installed
- line style strings map to Qt pen styles for `'-'`, `'--'`, `':'`, and `'-.'

- [x] **Step 4: Run PyQtGraph verification**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py -q
.venv/bin/python -m py_compile artisanlib/plot_pyqtgraph_adapter.py artisanlib/plot_pyqtgraph_smoke.py
.venv/bin/python -m ruff check artisanlib/plot_pyqtgraph_adapter.py artisanlib/plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py
```

Expected: PASS.

## Task 2: Phase 3 Pure Smoothing Helper

**Files:**
- Create: `src/test/unitary/artisanlib/test_sample_processing.py`
- Create: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- `decay_weight_sequence(4) == (1, 2, 3, 4)`
- `decay_weight_sequence(0) == (1,)`
- `smoothing_weights_for_recent_readings([100, 101, 102], (1, 2), 2) == (1, 2)`
- `smoothing_weights_for_recent_readings([100, -1, 102], (1, 2), 2) == (1,)`
- `smoothing_weights_for_recent_readings([], (1, 2), 2) == (1, 2)`

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because `artisanlib.sample_processing` does not exist yet.

- [x] **Step 3: Implement helper and integrate `canvas.py`**

Create `sample_processing.py` with:

- `decay_weight_sequence(curve_filter: int) -> tuple[int, ...]`
- `smoothing_weights_for_recent_readings(readings, decay_weights, curve_filter) -> tuple[int, ...]`

In `canvas.py`, replace the inline `numpy.arange()` and `-1 in sample_temp[-(cf+1):]` blocks with calls to the new helper while still assigning `self.temp_decay_weights` as a list for compatibility with existing `decay_average()` calls.

- [x] **Step 4: Run processing verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Expected: PASS.

## Task 3: Roadmap, Verification, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-real-pyqtgraph-phase-3-smoothing.md`

- [x] **Step 1: Update roadmap**

Record:

- Phase 2 has dependency-backed PyQtGraph smoke coverage.
- Phase 3 has started with a tested pure smoothing helper integrated into `sample_processing()`.
- Live renderer replacement and broad worker-thread extraction remain gated by benchmark comparison.

- [x] **Step 2: Run focused verification**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_sample_processing.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py::TestMakeLCDbox test/unitary/artisanlib/test_main.py::TestSetLabelColor::test_setLabelColor_preserves_lcd_label_padding -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/plot_pyqtgraph_smoke.py artisanlib/sample_processing.py artisanlib/gui_theme.py artisanlib/main.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/plot_pyqtgraph_smoke.py artisanlib/sample_processing.py artisanlib/gui_theme.py artisanlib/main.py artisanlib/canvas.py test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_sample_processing.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py
```

Expected: PASS.

- [x] **Step 3: Commit**

Run:

```bash
git add src/requirements.txt src/artisanlib/plot_pyqtgraph_adapter.py src/artisanlib/plot_pyqtgraph_smoke.py src/artisanlib/sample_processing.py src/artisanlib/canvas.py src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py src/test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py src/test/unitary/artisanlib/test_sample_processing.py docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-real-pyqtgraph-phase-3-smoothing.md
git commit -m "feat(gui): validate pyqtgraph and start phase 3 processing"
```

## Self-Review

- Spec coverage: This validates installed PyQtGraph/PyOpenGL and starts Phase 3 with a real pure computation extraction.
- Placeholder scan: No placeholder markers are present.
- Type consistency: `PyQtGraphSmokeRenderResult`, `render_snapshot_with_pyqtgraph`, `decay_weight_sequence`, and `smoothing_weights_for_recent_readings` are named consistently across tasks.
