# GUI Modernization Phase 2 Renderer Benchmark Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:verification-before-completion before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable renderer benchmark entry so Matplotlib and PyQtGraph snapshot adapters can be compared before any live renderer swap or broader Phase 3 threading work.

**Architecture:** Keep the benchmark outside the live roast UI. Generate a deterministic `RoastPlotSnapshot` workload, render it through the existing Matplotlib and PyQtGraph snapshot adapters, and return a JSON-serializable timing report.

**Tech Stack:** PyQt6 offscreen, pyqtgraph/PyOpenGL, Matplotlib Agg, pytest, py_compile, ruff.

---

## Files

- Add: `src/artisanlib/plot_renderer_benchmark.py`
  - Build a synthetic multi-curve roast workload.
  - Benchmark Matplotlib and PyQtGraph adapters against the same snapshot.
  - Provide a CLI JSON output path via `python -m artisanlib.plot_renderer_benchmark`.
- Add: `src/test/unitary/artisanlib/test_plot_renderer_benchmark.py`
  - Verify benchmark snapshot shape.
  - Verify both backend measurements include timing, event counts, and OpenGL request metadata.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record the new renderer benchmark entry and first measured result.

## Task 1: Add Renderer Benchmark Entry

- [x] **Step 1: Write failing tests**

Tests require:

- a synthetic roast workload with temperature curves, RoR curves, projection/background curves, and foreground events
- a benchmark report with Matplotlib and PyQtGraph measurements
- event marker counts and OpenGL-request metadata to be observable

Initial result: test collection failed because `artisanlib.plot_renderer_benchmark` did not exist.

- [x] **Step 2: Implement benchmark module**

Implemented deterministic snapshot generation, adapter timing, JSON report conversion, and a CLI entry point.

- [x] **Step 3: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_benchmark.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_benchmark.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_benchmark.py test/unitary/artisanlib/test_plot_renderer_benchmark.py
```

Result: focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_plot_renderer_benchmark.py`: `3 passed`
- `py_compile artisanlib/plot_renderer_benchmark.py`: passed
- `ruff check artisanlib/plot_renderer_benchmark.py test/unitary/artisanlib/test_plot_renderer_benchmark.py`: passed

- [x] **Step 4: Capture first benchmark sample**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_renderer_benchmark --points 900 --events 8 --iterations 3
```

Result on 2026-06-30:

- Matplotlib adapter: average `0.030763930330673855s`, total `0.09229179099202156s`
- PyQtGraph adapter: average `0.004651458390677969s`, total `0.013954375172033906s`
- Snapshot workload: `900` points, `6` curves, `8` events
- Qt emitted `QOpenGLWidget is not supported on this platform`, so the PyQtGraph OpenGL-request path was exercised but not proven with a real OpenGL widget in the offscreen environment.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `107 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 2: Review**

Review for benchmark fairness, cleanup guarantees, and future CI/offscreen stability.

Review result: benchmark code keeps heavy GUI imports inside backend functions, restores PyQtGraph's previous OpenGL config in a `finally` block, closes temporary widgets, and records the offscreen `QOpenGLWidget` limitation in the plan and roadmap. Added a minimum `point_count=2` regression after local review.

- [x] **Step 3: Commit**

Stage only benchmark implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
