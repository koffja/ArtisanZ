# GUI Modernization Phase 2 Renderer Selection Settings Plan

**Goal:** Add a small, tested runtime renderer-selection seam so future live canvas wiring can choose a renderer id without hard-coding policy in `canvas.py`.

**Scope:**

- `src/artisanlib/plot_renderer_settings.py`
- `src/test/unitary/artisanlib/test_plot_renderer_settings.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Define `ARTISANZ_RENDERER_ID` and the default `matplotlib-snapshot` renderer id.
- [x] Add a pure selection helper that reads an env mapping, validates the id against a runtime registry, and falls back safely.
- [x] Report requested id, selected id, and fallback reason in a typed result object.
- [x] Prove external plugin ids discovered through the runtime registry can be selected and smoke-rendered.
- [x] Keep `main.py` and `canvas.py` untouched.
- [x] Update the roadmap with the renderer-selection setting seam status.
- [x] Run focused verification and request review.
- [x] Fix review findings and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_settings.py test/unitary/artisanlib/test_plot_renderer_plugin_loader.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_registry.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_settings.py test/unitary/artisanlib/test_plot_renderer_settings.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_settings.py test/unitary/artisanlib/test_plot_renderer_settings.py
git diff --check
```

## 2026-07-01 Result

- Added `plot_renderer_settings.py` with `ARTISANZ_RENDERER_ID`, `DEFAULT_RENDERER_ID`, and a typed `RendererSelection` result.
- Added `select_renderer()` to validate requested renderer ids against a runtime registry and fall back to `matplotlib-snapshot` for unknown or unavailable ids.
- `RendererSelection` carries the runtime registry so filesystem-discovered renderer ids remain instantiable by later factory calls.
- If the default renderer is not usable, selection falls back to the first available renderer or raises `RendererSelectionError` when none are available.
- Added `available_renderer_ids()` for UI/diagnostic callers that need available renderer choices.
- Proved a filesystem-discovered renderer id can be selected and then smoke-rendered through `smoke_renderer_factory()`.
- `main.py` and `canvas.py` remained untouched.
- Focused renderer selection verification passed: `41 passed`.
- Expanded renderer suite passed: `54 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
- Code review findings were fixed; re-review found no remaining issues.
