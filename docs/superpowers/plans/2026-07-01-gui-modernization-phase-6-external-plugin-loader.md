# GUI Modernization Phase 6 External Plugin Loader Plan

**Goal:** Let renderer plugin specs be discovered from package-external Python files and merged into the runtime renderer registry without editing `main.py` or `canvas.py`.

**Scope:**

- `src/artisanlib/plot_renderer_plugin_loader.py`
- `src/test/unitary/artisanlib/test_plot_renderer_plugin_loader.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add `discover_external_renderer_plugins()` for `.py` files in explicit search paths.
- [x] Add `build_runtime_registry()` that starts from built-ins and merges discovered external specs.
- [x] Read default plugin search paths from `ARTISANZ_RENDERER_PLUGIN_PATH` using `os.pathsep`.
- [x] Keep external plugin loading opt-in and isolate bad plugin files with warnings.
- [x] Prove a filesystem plugin id can render through the existing factory smoke seam.
- [x] Keep `main.py` and `canvas.py` untouched.
- [x] Update the roadmap with the runtime plugin-loader status.
- [x] Run focused verification and request review.
- [x] Fix review findings and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_plugin_loader.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_registry.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_plugin_loader.py test/unitary/artisanlib/test_plot_renderer_plugin_loader.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_plugin_loader.py test/unitary/artisanlib/test_plot_renderer_plugin_loader.py
git diff --check
```

## 2026-07-01 Result

- Added `plot_renderer_plugin_loader.py` with opt-in filesystem discovery for renderer plugin spec files.
- Added `build_runtime_registry()` to merge built-in renderer plugins with specs discovered from explicit paths or `ARTISANZ_RENDERER_PLUGIN_PATH`.
- Plugin loading isolates import/register failures with `RuntimeWarning` and leaves built-ins usable.
- Duplicate renderer ids are warned and skipped so a colliding external plugin cannot disable built-ins.
- Hookless `.py` files are inspected with AST and are not imported or executed.
- Filesystem-discovered plugin ids can render through `smoke_renderer_factory()` using the existing Matplotlib adapter.
- Plugin-local renderer classes can remain importable through generated module names.
- `main.py` and `canvas.py` remained untouched.
- Focused plugin-loader verification passed: `31 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
- Code review findings were fixed; re-review found no remaining issues.
