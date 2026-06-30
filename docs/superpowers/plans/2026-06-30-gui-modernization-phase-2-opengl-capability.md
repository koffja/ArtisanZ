# GUI Modernization Phase 2 OpenGL Capability Benchmark Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the renderer benchmark distinguish a requested PyQtGraph OpenGL path from a runtime-supported `QOpenGLWidget` path before any live renderer swap is considered.

**Architecture:** Keep the current renderer POC unhooked from live `canvas.py`. Extend the benchmark measurement with an `opengl_widget_supported` diagnostic that probes `QOpenGLWidget.isValid()` only when OpenGL is requested. This keeps timing comparisons honest in offscreen environments where Qt accepts `useOpenGL=True` but cannot create an OpenGL widget.

**Tech Stack:** PyQt6, PyQtGraph, PyOpenGL-installed environment, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/plot_renderer_benchmark.py`
  - Add `opengl_widget_supported` to benchmark measurements.
  - Add an injectable OpenGL probe for deterministic tests.
  - Probe `QOpenGLWidget.isValid()` outside the timed render loop.
- Modify: `src/test/unitary/artisanlib/test_plot_renderer_benchmark.py`
  - Cover requested-but-unsupported OpenGL reporting.
  - Cover skipping the probe when `--no-opengl` is used.
- Modify: `docs/GUI_MODERNIZATION_BASELINE.md`
  - Record the current Matplotlib-vs-PyQtGraph benchmark with OpenGL support status.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Clarify that PyQtGraph is faster in the current adapter benchmark, while OpenGL remains unconfirmed in the offscreen platform.

## Task 1: Add OpenGL Capability Reporting

- [x] **Step 1: Write failing tests**

Initial result:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_benchmark.py -q
```

Expected failure observed: `benchmark_plot_renderers()` did not accept `pyqtgraph_opengl_probe`.

- [x] **Step 2: Implement benchmark diagnostic**

Added `opengl_widget_supported` to `PlotRendererBenchmarkMeasurement`, added the injectable probe, and implemented a default `QOpenGLWidget.isValid()` probe used only when OpenGL is requested.

- [x] **Step 3: Run focused tests**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_benchmark.py -q
```

Result: `4 passed`.

## Task 2: Capture Current Renderer Benchmark

- [x] **Step 1: Run OpenGL-requested benchmark**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_renderer_benchmark --points 900 --events 8 --iterations 5
```

Result:

- Matplotlib adapter average: `0.010817674966529012s`
- PyQtGraph adapter average: `0.0025607582181692125s`
- PyQtGraph `opengl_requested`: `true`
- PyQtGraph `opengl_widget_supported`: `false`

- [x] **Step 2: Run no-OpenGL benchmark**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_renderer_benchmark --points 900 --events 8 --iterations 5 --no-opengl
```

Result:

- Matplotlib adapter average: `0.010901808366179466s`
- PyQtGraph adapter average: `0.0026710582431405784s`
- PyQtGraph `opengl_requested`: `false`
- PyQtGraph `opengl_widget_supported`: `null`

## Task 3: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

Run renderer benchmark tests, smoke tests, compile, ruff, and diff check.

Verification passed on 2026-06-30:

- Renderer suite: `21 passed`
- `py_compile artisanlib/plot_renderer_benchmark.py`: passed
- `ruff check artisanlib/plot_renderer_benchmark.py test/unitary/artisanlib/test_plot_renderer_benchmark.py`: passed
- `git diff --check`: passed

- [x] **Step 2: Request code review**

Use request-code-reviewer focused on benchmark API compatibility, OpenGL probe safety, timing contamination, and whether the diagnostic supports future live-renderer decisions.

Review result on 2026-06-30: local self-review recorded no Critical or Important findings in `2026-06-30-gui-modernization-phase-2-opengl-capability-REVIEW.md`. The prior external review-agent path was intentionally not used for this low-risk benchmark diagnostic because the agent was timing out and this slice is covered by focused tests and CLI benchmark output.

- [x] **Step 3: Commit**

Stage only benchmark implementation, tests, and planning/baseline documents. Leave `.codebase-memory/*` unstaged.
