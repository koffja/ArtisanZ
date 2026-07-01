# GUI Modernization Phase 6 Runtime Smoke CLI Plan

**Goal:** Make the renderer factory smoke CLI use the runtime registry so package-external renderer ids from `ARTISANZ_RENDERER_PLUGIN_PATH` can be smoke-tested without code edits.

**Scope:**

- `src/artisanlib/plot_renderer_factory_smoke.py`
- `src/test/unitary/artisanlib/test_plot_renderer_factory_smoke.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Replace CLI hard-coded renderer choices with runtime-registry lookup.
- [x] Keep built-in renderer smoke behavior unchanged.
- [x] Add a CLI-level test for an external filesystem renderer id.
- [x] Keep `main.py` and `canvas.py` untouched.
- [x] Update the roadmap with the runtime smoke CLI status.
- [x] Run focused verification and request review.
- [x] Fix review findings and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_plugin_loader.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py
git diff --check
```

## 2026-07-01 Result

- The CLI now passes `build_runtime_registry()` into `smoke_renderer_factory()`.
- `smoke_renderer_factory()` keeps its built-in registry default so direct smoke calls are not affected by ambient `ARTISANZ_RENDERER_PLUGIN_PATH`.
- The CLI no longer hard-codes renderer id choices, so ids discovered through `ARTISANZ_RENDERER_PLUGIN_PATH` can be smoke-tested.
- Unknown CLI renderer ids now report a clean argparse error instead of an unhandled traceback.
- Added a CLI-level external filesystem renderer smoke test.
- Built-in Matplotlib and PyQtGraph smoke behavior remains covered.
- Focused verification passed: `18 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
