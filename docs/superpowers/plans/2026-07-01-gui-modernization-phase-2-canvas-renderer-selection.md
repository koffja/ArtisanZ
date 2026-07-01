# GUI Modernization Phase 2 Canvas Renderer Selection Plan

**Goal:** Attach the tested renderer-selection seam to `tgraphcanvas` initialization so the live canvas has an inspected renderer choice before any rendering behavior changes.

**Scope:**

- `src/artisanlib/canvas.py`
- `src/artisanlib/plot_renderer_registry.py`
- `src/artisanlib/plot_renderer_settings.py`
- `src/test/unitary/artisanlib/test_canvas_renderer_selection.py`
- `src/test/unitary/artisanlib/test_plot_renderer_settings.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Store a `RendererSelection` on `tgraphcanvas`.
- [x] Keep the selected renderer in diagnostic state only; do not change actual Matplotlib drawing yet.
- [x] Fall back to Matplotlib if selection fails during canvas construction.
- [x] Add focused tests for default, env-requested PyQtGraph, and selection failure fallback.
- [x] Add review-fix tests for bad dotted dependency metadata and `tgraphcanvas.__slots__`.
- [x] Keep `main.py` untouched.
- [x] Update the roadmap with the canvas-level selection seam status.
- [x] Run focused verification and request review.
- [x] Fix review findings and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_plot_renderer_settings.py -q
.venv/bin/python -m py_compile artisanlib/canvas.py artisanlib/plot_renderer_registry.py artisanlib/plot_renderer_settings.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_plot_renderer_settings.py
.venv/bin/python -m ruff check artisanlib/canvas.py artisanlib/plot_renderer_registry.py artisanlib/plot_renderer_settings.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_plot_renderer_settings.py
git diff --check
```

## 2026-07-01 Result

- Added `select_canvas_renderer()` to bridge the pure renderer-selection seam into `canvas.py`.
- `tgraphcanvas` now stores `plot_renderer_selection` during initialization.
- The selected renderer remains diagnostic state only; drawing still uses the existing Matplotlib path.
- Selection failure falls back to the default Matplotlib renderer metadata and logs a warning with `selection_error`.
- Bad dotted dependency metadata is treated as unavailable instead of crashing renderer selection.
- Review found one warning and two info items; all were addressed.
- Focused verification passed: `16 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
