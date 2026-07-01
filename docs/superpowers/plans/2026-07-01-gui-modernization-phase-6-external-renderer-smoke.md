# GUI Modernization Phase 6 External Renderer Smoke Plan

**Goal:** Prove an externally registered renderer can be smoke-tested through the same factory seam without editing `main.py` or `canvas.py`.

**Scope:**

- `src/artisanlib/plot_renderer_registry.py`
- `src/artisanlib/plot_renderer_factory_smoke.py`
- `src/test/unitary/artisanlib/test_plot_renderer_factory.py`
- `src/test/unitary/artisanlib/test_plot_renderer_registry.py`
- `src/test/unitary/artisanlib/test_plot_renderer_factory_smoke.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add renderer surface metadata to `RendererPluginSpec`.
- [x] Mark built-in Matplotlib and PyQtGraph renderers with the correct surface.
- [x] Route `smoke_renderer_factory()` by plugin surface instead of hard-coded renderer ids.
- [x] Add an external-registry smoke test that renders the same snapshot through a non-built-in id.
- [x] Keep `main.py` and `canvas.py` untouched.
- [x] Update the roadmap with the external-registry smoke status.
- [x] Run focused verification, request review, fix findings, and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_registry.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_renderer_benchmark.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_registry.py artisanlib/plot_renderer_factory.py artisanlib/plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_registry.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_registry.py artisanlib/plot_renderer_factory.py artisanlib/plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_registry.py
git diff --check
```

## 2026-07-01 Result

- Added explicit `RendererSurface` metadata to each renderer plugin spec.
- Built-in Matplotlib and PyQtGraph renderers now declare the construction surface they require.
- `smoke_renderer_factory()` dispatches by plugin surface from the active registry instead of hard-coded renderer ids.
- Added an external-registry smoke test for `external-matplotlib-smoke`, proving a non-built-in id can render the same roast snapshot through the factory seam.
- `main.py` and `canvas.py` remained untouched.
- Expanded renderer verification passed: `34 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
- Code review found no code-level blocker; documentation scope and verification-result findings were fixed before commit.
