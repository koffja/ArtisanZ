# GUI Modernization Phase 2 Guarded PyQtGraph Embed Plan

**Goal:** Put the real PyQtGraph plot target behind the renderer-selection seam so the main UI can display it when `ARTISANZ_RENDERER_ID=pyqtgraph-snapshot`, while preserving Matplotlib as the default and fallback path.

**Scope:**

- `src/artisanlib/canvas.py`
- `src/artisanlib/main.py`
- `src/artisanlib/plot_live_frame.py`
- `src/test/unitary/artisanlib/test_canvas_renderer_selection.py`
- `src/test/unitary/artisanlib/test_plot_live_frame.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add style payload to `LiveCurveData` so PyQtGraph can create items from live frames.
- [x] Add `live_frame_to_snapshot()` for renderer adapters that consume `RoastPlotSnapshot`.
- [x] Let `tgraphcanvas` create a PyQtGraph target only when the selected renderer surface is `pyqtgraph-plot`.
- [x] Expose `tgraphcanvas.graph_widget()` so the main splitter can use either Matplotlib or PyQtGraph.
- [x] Keep Matplotlib as the default display and as the fallback when PyQtGraph target creation fails.
- [x] Feed embedded PyQtGraph targets from the same ET/BT/Delta live-frame dispatch.
- [x] Add tests for Matplotlib, selected-but-not-embedded fallback, and embedded PyQtGraph target paths.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py -q
.venv/bin/python -m py_compile artisanlib/canvas.py artisanlib/main.py artisanlib/plot_live_frame.py artisanlib/plot_pyqtgraph_widget.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py
.venv/bin/python -m ruff check artisanlib/canvas.py artisanlib/main.py artisanlib/plot_live_frame.py artisanlib/plot_pyqtgraph_widget.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py
git diff --check
```

## Result

- Focused verification passed: `36 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
- Offscreen PyQtGraph simulator baseline after review fixes: `/tmp/artisanz-pyqtgraph-live-final.png`, `flagon=True flagstart=True`, `redraw max=155.610ms avg=100.076ms`, `updategraphics max=41.895ms avg=3.903ms`, `sample_processing max=4.912ms avg=2.389ms`.
- Native-window PyQtGraph simulator baseline after review fixes: `/tmp/artisanz-pyqtgraph-realwindow-final.png`, `flagon=True flagstart=True`, `redraw max=118.040ms avg=81.885ms`, `updategraphics max=37.760ms avg=4.839ms`, `sample_processing max=7.377ms avg=2.897ms`.
- OpenGL was not promoted: the first OpenGL embed attempt produced a blank graph surface in this environment, consistent with earlier `QOpenGLWidget` capability warnings. The guarded embed uses software PyQtGraph until real-device OpenGL validation is available.
- Code-review fixes applied before commit: runtime PyQtGraph update exceptions now fall back to Matplotlib, hidden Matplotlib lines remain synchronized while PyQtGraph is visible, visible extra-device curves are included in the PyQtGraph live frame, and extra-device renderer keys are unique even when user-facing labels repeat.

## Next Step

Use the guarded PyQtGraph path for continued Phase 3/4 UI decomposition experiments, while keeping Matplotlib as the default and fallback renderer.
