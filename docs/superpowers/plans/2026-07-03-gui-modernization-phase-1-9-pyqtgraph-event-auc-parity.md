# ArtisanZ GUI Modernization Phase 1.9: PyQtGraph Event/AUC Parity

**Goal:** Improve the default PyQtGraph visual parity for event-heavy roasts by reducing event-label overlap and rendering AUC area fills from the same snapshot model.

**Execution Status:** Implemented and verified on 2026-07-03.

## Scope

- Extend `RoastPlotSnapshot` with renderer-neutral area-fill overlays.
- Extract AUC area-fill data from `tgraphcanvas` using the same source fields as the Matplotlib `drawAUC()` path.
- Render area fills in PyQtGraph behind foreground curves and above phase bands.
- Improve default event-label placement so events close in time use separate rows instead of occupying the same label lane.
- Add focused tests for the new snapshot field, extractor behavior, PyQtGraph item lifecycle, and label row placement.

## Non-Goals

- Do not replace Matplotlib report/export paths.
- Do not add interactive event dragging/editing.
- Do not implement all analysis masks/statistics overlays in this slice.
- Do not change roast calculations or persisted profile data.

## Implementation Tasks

1. Add `AreaFillSnapshot` to `src/artisanlib/plot_snapshot.py`.
2. Update `src/artisanlib/plot_snapshot_extractor.py`:
   - Add `areas` to `RoastPlotSnapshot`.
   - Add AUC-area extraction only when AUC display conditions and data are valid.
3. Update `src/artisanlib/plot_pyqtgraph_adapter.py`:
   - Add area item factory and lifecycle.
   - Render AUC fills with `PlotDataItem(fillLevel=baseline, brush=...)`.
   - Add event-label row computation based on time-cluster proximity.
4. Update tests:
   - `test_plot_snapshot.py`
   - `test_plot_snapshot_extractor.py`
   - `test_plot_pyqtgraph_adapter.py`
   - `test_plot_pyqtgraph_widget.py` if real PyQtGraph item behavior needs coverage.

## Validation

```bash
cd src
.venv/bin/python -m pytest \
  test/unitary/artisanlib/test_plot_snapshot.py \
  test/unitary/artisanlib/test_plot_snapshot_extractor.py \
  test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py \
  test/unitary/artisanlib/test_plot_pyqtgraph_widget.py \
  -q

.venv/bin/python -m ruff check \
  artisanlib/plot_snapshot.py \
  artisanlib/plot_snapshot_extractor.py \
  artisanlib/plot_pyqtgraph_adapter.py \
  test/unitary/artisanlib/test_plot_snapshot.py \
  test/unitary/artisanlib/test_plot_snapshot_extractor.py \
  test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py \
  test/unitary/artisanlib/test_plot_pyqtgraph_widget.py
```

## Exit Gate

- Area fills are represented in the snapshot contract and rendered by PyQtGraph.
- Event labels in time-dense clusters use multiple rows.
- Existing PyQtGraph curves/events/guides/phase bands remain intact.
- Code review finds no blocking issues.

## Result

- Added `AreaFillSnapshot` to the renderer-neutral snapshot contract.
- Added AUC area extraction from canvas state when AUC display conditions match the legacy Matplotlib path.
- Added PyQtGraph area-fill lifecycle and `PlotDataItem(fillLevel=...)` rendering.
- Added clustered event-label row placement so labels near each other in time use separate rows.
- Code-review follow-up fixed AUC base-index parity when `stemp2` contains legacy `-1` samples, added AUC edge-case coverage, and removed the six-row event-label wraparound.
- Focused validation: `39 passed` across snapshot, snapshot extractor, PyQtGraph adapter, PyQtGraph widget, and WebSocket renderer smoke tests.
- Static validation: `py_compile`, `ruff check`, and `git diff --check` passed for touched Python modules.
