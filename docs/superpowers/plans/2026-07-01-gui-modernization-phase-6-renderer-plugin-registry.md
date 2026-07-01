# GUI Modernization Phase 6 Renderer Plugin Registry Plan

**Goal:** Establish the first renderer plugin metadata seam around the renderer adapters without changing live roast rendering behavior.

**Scope:**

- `src/artisanlib/plot_renderer_registry.py`
- `src/test/unitary/artisanlib/test_plot_renderer_registry.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a renderer plugin spec that describes an adapter by id, label, class path, dependency list, and stability.
- [x] Add a small registry that can list, look up, register, and load renderer classes.
- [x] Keep availability checks metadata-only by using import discovery instead of dependency imports.
- [x] Validate loaded renderer classes against the `LivePlotRenderer` method surface.
- [x] Register the existing Matplotlib and PyQtGraph snapshot adapters as built-in renderer plugins.
- [x] Keep this registry side-effect-light and avoid changing `main.py` or `canvas.py`.
- [x] Add tests for built-in discovery, class loading, duplicate protection, dependency availability, and external registration.
- [x] Update the roadmap with the Phase 6 start point.
- [x] Run focused verification, request code review, fix findings, and commit.

Verification:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_registry.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_registry.py test/unitary/artisanlib/test_plot_renderer_registry.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_registry.py test/unitary/artisanlib/test_plot_renderer_registry.py
git diff --check
```

## 2026-07-01 Result

- Added `RendererPluginSpec` and `RendererPluginRegistry`.
- Registered `matplotlib-snapshot` and `pyqtgraph-snapshot` as built-in renderer plugins.
- Verified custom external renderer registration can be added without changing `main.py` or `canvas.py`.
- Code review found that availability filtering imported dependencies and that loaded classes were not checked against the renderer protocol. Both were fixed with `find_spec()` discovery and structural method validation.
- Focused renderer tests passed: `18 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
