# GUI Modernization Phase 6 Renderer Factory Smoke Plan

**Goal:** Prove the renderer factory seam can swap renderer backends by id against the same snapshot without changing `main.py` or `canvas.py`.

**Scope:**

- `src/artisanlib/plot_renderer_factory_smoke.py`
- `src/test/unitary/artisanlib/test_plot_renderer_factory_smoke.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a reusable smoke snapshot built from the existing renderer benchmark workload.
- [x] Add a factory smoke runner that renders the same snapshot through `matplotlib-snapshot`.
- [x] Add a factory smoke runner that renders the same snapshot through `pyqtgraph-snapshot`.
- [x] Return backend-neutral result metrics for view state, item counts, events, and optional PNG size.
- [x] Add a small CLI for manual `renderer_id` smoke checks.
- [x] Add tests proving Matplotlib and PyQtGraph can be swapped by id through the same smoke runner.
- [x] Keep `main.py` and `canvas.py` untouched.
- [x] Update the roadmap with the smoke-proven factory seam status.
- [x] Run focused verification, request code review, fix findings, and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_renderer_factory_smoke --renderer matplotlib-snapshot --points 24 --events 3
QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_renderer_factory_smoke --renderer pyqtgraph-snapshot --points 24 --events 3
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_renderer_factory_smoke.py test/unitary/artisanlib/test_plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_registry.py -q
.venv/bin/python -m py_compile artisanlib/plot_renderer_factory_smoke.py artisanlib/plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py
.venv/bin/python -m ruff check artisanlib/plot_renderer_factory_smoke.py artisanlib/plot_renderer_factory.py test/unitary/artisanlib/test_plot_renderer_factory_smoke.py
git diff --check
```

## 2026-07-01 Result

- Added `smoke_renderer_factory()` and `RendererFactorySmokeResult`.
- Added CLI smoke checks for `matplotlib-snapshot` and `pyqtgraph-snapshot`.
- Both renderers now consume the same synthetic roast snapshot through `create_renderer()`.
- PyQtGraph smoke defaults to offscreen-safe, non-OpenGL rendering; `--opengl` is opt-in for manual checks.
- PyQtGraph smoke and its unit tests also pass when `QT_QPA_PLATFORM` is not preset by the caller.
- CLI smoke output confirmed matching backend-neutral metrics: `temperature_item_count=4`, `ror_item_count=2`, `event_item_count=6`.
- Related renderer tests passed: `33 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
- Code review found no critical issues; the headless/OpenGL stability warning was fixed before commit.
