# GUI Modernization Phase 6 Renderer Factory Plan

**Goal:** Turn the renderer plugin metadata seam into a callable factory seam without changing live roast rendering behavior.

**Scope:**

- `src/artisanlib/plot_renderer_factory.py`
- `src/test/unitary/artisanlib/test_plot_renderer_factory.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a `create_renderer()` factory that instantiates a renderer by `renderer_id`.
- [x] Use the existing renderer registry and keep external plugin registration supported.
- [x] Check plugin dependency availability before importing or constructing the renderer class.
- [x] Return objects typed against the existing `LivePlotRenderer` protocol.
- [x] Add tests for built-in Matplotlib/PyQtGraph creation, external plugin creation, missing dependencies, and unknown ids.
- [x] Keep `main.py` and `canvas.py` untouched.
- [x] Update the roadmap with the factory seam status.
- [x] Run focused verification, request code review, fix findings, and commit.

Verification:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_registry.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_factory.py artisanlib/plot_renderer_registry.py test/unitary/artisanlib/test_plot_renderer_factory.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_factory.py artisanlib/plot_renderer_registry.py test/unitary/artisanlib/test_plot_renderer_factory.py
git diff --check
```

## 2026-07-01 Result

- Added `create_renderer()` and `missing_renderer_dependencies()`.
- Verified built-in Matplotlib and PyQtGraph renderer creation by id.
- Verified externally registered renderer creation through a custom registry.
- Verified dependency checks happen before renderer class loading.
- Code review approved the slice with one info-level test gap; the dependency-before-import sentinel test was added.
- Focused renderer tests passed: `25 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
