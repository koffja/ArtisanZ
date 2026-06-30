# GUI Modernization Phase 2 OpenGL Capability Benchmark Review

**Date:** 2026-06-30

**Scope:**

- `src/artisanlib/plot_renderer_benchmark.py`
- `src/test/unitary/artisanlib/test_plot_renderer_benchmark.py`
- `docs/GUI_MODERNIZATION_BASELINE.md`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- `docs/superpowers/plans/2026-06-30-gui-modernization-phase-2-opengl-capability.md`

## Findings

No Critical or Important findings.

## Minor Notes

- The benchmark report JSON gains a new `opengl_widget_supported` field. Existing callers that ignore extra JSON keys remain compatible; Python callers constructing `PlotRendererBenchmarkMeasurement` by position are internal to this module.
- The `QOpenGLWidget` probe runs before timed iterations, so it does not contaminate the measured render loop.
- The probe is guarded: when OpenGL is not requested it returns `None`, and probe exceptions are reported as `False`.

## Assessment

This slice corrects a decision-quality issue in the Phase 2 benchmark: `use_opengl=True` previously meant only that PyQtGraph OpenGL was requested. The report now distinguishes requested OpenGL from a runtime-valid `QOpenGLWidget`, which matters in offscreen/headless runs where Qt prints that `QOpenGLWidget` is unsupported.

The documentation does not claim OpenGL acceleration is proven. It records that PyQtGraph is faster in the synthetic adapter benchmark, with or without requesting OpenGL, while `opengl_widget_supported=false` in the current offscreen environment.

## Verification

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_plot_renderer_benchmark.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_benchmark.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_benchmark.py test/unitary/artisanlib/test_plot_renderer_benchmark.py
git diff --check
```

Results:

- Renderer suite: `21 passed`
- `py_compile`: passed
- `ruff check`: passed
- `git diff --check`: passed
