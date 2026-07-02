# GUI Modernization Phase 2 Live Renderer Dispatch Plan

**Goal:** Wire the existing renderer selection into the live main-curve update path without pretending PyQtGraph is active before a real PyQtGraph plot widget exists.

**Scope:**

- `src/artisanlib/plot_live_frame.py`
- `src/artisanlib/canvas.py`
- `src/test/unitary/artisanlib/test_plot_live_frame.py`
- `src/test/unitary/artisanlib/test_canvas_renderer_selection.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a backend-aware `apply_selected_live_frame()` helper with a structured result.
- [x] Route Matplotlib selections through the existing Matplotlib live-frame applier.
- [x] Route PyQtGraph selections through PyQtGraph items when targets exist.
- [x] Fall back to Matplotlib with `pyqtgraph_targets_unavailable` when PyQtGraph is selected before a widget target is embedded.
- [x] Add `tgraphcanvas.apply_live_plot_frame()` and store the latest apply result for diagnostics.
- [x] Route ET, BT, Delta ET, and Delta BT sample updates through one `LivePlotFrame` dispatch.
- [x] Update roadmap status and runtime-dispatch notes.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_canvas_renderer_selection.py -q
.venv/bin/python -m py_compile artisanlib/plot_live_frame.py artisanlib/canvas.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_canvas_renderer_selection.py
.venv/bin/python -m ruff check artisanlib/plot_live_frame.py artisanlib/canvas.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_canvas_renderer_selection.py
git diff --check
```

## Result

- Focused verification passed: `27 passed`.
- Broader related verification passed: `173 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.

## Next Step

Embed or factory-create a real PyQtGraph plot widget target behind the existing renderer-selection seam, then run a simulator screenshot/baseline with `ARTISANZ_RENDERER_ID=pyqtgraph-snapshot`.
