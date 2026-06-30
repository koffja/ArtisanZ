# GUI Modernization Phase 2 Live Frame Payload Plan

**Goal:** Start isolating the live Matplotlib payload mutations identified by the Phase 3 audit, without changing the default renderer or user-visible graph behavior.

**Scope:**

- `src/artisanlib/plot_live_frame.py`
- `src/artisanlib/canvas.py`
- `src/test/unitary/artisanlib/test_plot_live_frame.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add an immutable `LiveCurveData` payload for live curve x/y data.
- [x] Add a `LivePlotFrame` grouping for future multi-curve renderer updates.
- [x] Add Matplotlib applier helpers that call `set_data` through the payload boundary and safely skip missing/incompatible line objects.
- [x] Route main ET, BT, Delta ET, and Delta BT canvas updates through the payload boundary.
- [x] Keep extra-device curve loops unchanged for this slice because they still combine device indexing, visibility counters, and line selection.
- [x] Run focused verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/plot_live_frame.py artisanlib/canvas.py test/unitary/artisanlib/test_plot_live_frame.py
.venv/bin/python -m ruff check artisanlib/plot_live_frame.py artisanlib/canvas.py test/unitary/artisanlib/test_plot_live_frame.py
git diff --check
```

Result: `151 passed` for the focused renderer/sample-processing tests; compile, ruff, and diff check passed.

## Notes

This is a bridge slice, not the live PyQtGraph switch. It narrows one canvas mutation surface so a future `LivePlotRenderer` can consume the same payloads from Matplotlib and PyQtGraph paths.
