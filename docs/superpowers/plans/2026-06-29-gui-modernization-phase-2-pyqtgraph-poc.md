# GUI Modernization Phase 2 PyQtGraph POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Phase 2 by adding a tested PyQtGraph-style renderer POC that consumes the existing `RoastPlotSnapshot` contract without changing the live Matplotlib runtime path.

**Architecture:** Create a small duck-typed adapter for PyQtGraph-like plot widgets/items. The adapter must import successfully even when `pyqtgraph` is not installed; real PyQtGraph item creation stays behind optional factories. It supports curve items, event marker items, view-state reset/export, and hidden-curve updates using the same snapshot data as the Matplotlib adapter.

**Tech Stack:** Python duck typing, optional PyQtGraph imports, pytest fake plot widgets/items, ruff, py_compile.

---

## Files

- Create: `src/artisanlib/plot_pyqtgraph_adapter.py`
  - Owns `PyQtGraphSnapshotRenderer`, a POC renderer adapter for PyQtGraph-like plot objects.
- Create: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`
  - Covers curve item creation/update, view-state reset/export, hidden-curve behavior, optional event item factories, and event cleanup.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 2 as complete at the renderer-boundary/POC level, with live runtime integration still intentionally deferred.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-pyqtgraph-poc.md`
  - Track this plan's execution.

## Task 1: PyQtGraph Adapter Tests

**Files:**
- Create: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`

- [x] **Step 1: Write failing adapter tests**

Create a test module with fake PyQtGraph-like plot and item objects. Cover:

- `set_snapshot()` creates one item on the temperature plot and one item on the RoR plot.
- The created items receive snapshot x/y data and pen style data.
- `reset_view()` maps snapshot axes to `setXRange()` and `setYRange()` with zero padding.
- `update_live_frame()` reuses existing items and hides missing curves.
- Event marker factories create two items per event, add them to the temperature plot, and old event items are removed on replacement.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -q
```

Expected: FAIL because `artisanlib.plot_pyqtgraph_adapter` does not exist yet.

## Task 2: PyQtGraph Adapter Implementation

**Files:**
- Create: `src/artisanlib/plot_pyqtgraph_adapter.py`

- [x] **Step 1: Implement `PyQtGraphSnapshotRenderer`**

Create a renderer with this public surface:

- `set_snapshot(snapshot: RoastPlotSnapshot) -> None`
- `update_live_frame(snapshot: RoastPlotSnapshot) -> None`
- `reset_view(view_state: RendererViewState) -> None`
- `export_view_state() -> RendererViewState`
- `item_for(curve_name: str) -> object | None`
- `event_item_count() -> int`

Implementation rules:

- Store curve items by `CurveSnapshot.name`.
- Use `temperature_plot.plot(curve.x, curve.y, pen=..., name=curve.name)` for temperature curves.
- Use `ror_plot` for `curve.y_axis == 'ror'` when supplied; otherwise fall back to the temperature plot.
- Reuse existing items with `setData()`, `setPen()`, and `setVisible()` when those methods exist.
- Hide items whose curve names are missing from the next snapshot.
- Reset plot ranges using `setXRange(minimum, maximum, padding=0)` and `setYRange(minimum, maximum, padding=0)`.
- Export actual plot ranges from `viewRange()` when available; otherwise return the last reset view state.
- Accept optional `event_line_factory` and `event_label_factory` callables for tests and real PyQtGraph integration.
- Add event items with `temperature_plot.addItem(item)` when available.
- Remove old event items with `temperature_plot.removeItem(item)` when available.
- Default event factories should try to import `pyqtgraph`; when unavailable they return `None` so ordinary imports remain safe.

- [x] **Step 2: Run adapter verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -q
.venv/bin/python -m py_compile artisanlib/plot_pyqtgraph_adapter.py
.venv/bin/python -m ruff check artisanlib/plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
```

Expected: PASS.

## Task 3: Roadmap and Phase Completion

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-pyqtgraph-poc.md`

- [x] **Step 1: Update roadmap**

Record that Phase 2 now has:

- Renderer-neutral snapshot contract.
- Canvas-like extractor for live curves and foreground events.
- Matplotlib compatibility adapter.
- Offscreen Agg smoke render path.
- PyQtGraph-style POC adapter behind optional dependency boundaries.

Also record that live `canvas.py` integration remains deferred until benchmark comparison.

- [x] **Step 2: Run focused verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py::TestMakeLCDbox test/unitary/artisanlib/test_main.py::TestSetLabelColor::test_setLabelColor_preserves_lcd_label_padding -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/gui_theme.py artisanlib/main.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/gui_theme.py artisanlib/main.py test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py
```

Expected: PASS.

- [x] **Step 3: Commit**

Run:

```bash
git add src/artisanlib/gui_theme.py src/artisanlib/main.py src/artisanlib/plot_pyqtgraph_adapter.py src/test/unitary/artisanlib/test_gui_theme.py src/test/unitary/artisanlib/test_main.py src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-pyqtgraph-poc.md
git commit -m "feat(gui): add pyqtgraph renderer poc"
```

## Self-Review

- Spec coverage: This plan fixes the LCD visual regression and completes Phase 2's renderer-boundary POC without altering live Matplotlib behavior.
- Placeholder scan: No placeholder markers are present.
- Type consistency: `PyQtGraphSnapshotRenderer`, `RoastPlotSnapshot`, `RendererViewState`, `event_line_factory`, and `event_label_factory` are named consistently across tests and implementation.
