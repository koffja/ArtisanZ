# GUI Modernization Phase 2 PyQtGraph Widget Target Plan

**Goal:** Create the real PyQtGraph widget target that the future guarded live renderer switch can embed, instead of limiting PyQtGraph coverage to fake plot objects or standalone smoke code.

**Scope:**

- `src/artisanlib/plot_pyqtgraph_widget.py`
- `src/artisanlib/plot_pyqtgraph_smoke.py`
- `src/artisanlib/plot_pyqtgraph_adapter.py`
- `src/test/unitary/artisanlib/test_plot_pyqtgraph_widget.py`
- `src/test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py`
- `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a `GraphicsLayoutWidget` target factory with temperature and optional RoR plots.
- [x] Return a `PyQtGraphSnapshotRenderer` wired to the real target plots.
- [x] Restore the previous PyQtGraph OpenGL config when the target is closed.
- [x] Reuse the target factory from the existing PyQtGraph smoke path.
- [x] Stabilize the PyQtGraph adapter range reset by disabling auto-range before applying explicit view state.
- [x] Add tests for real target rendering, optional RoR target creation, and OpenGL config restoration.
- [x] Update the roadmap with widget-target status.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -q
.venv/bin/python -m py_compile artisanlib/plot_pyqtgraph_widget.py artisanlib/plot_pyqtgraph_smoke.py artisanlib/plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
.venv/bin/python -m ruff check artisanlib/plot_pyqtgraph_widget.py artisanlib/plot_pyqtgraph_smoke.py artisanlib/plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
git diff --check
```

## Result

- Focused verification passed: `9 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.

## Next Step

Embed this target behind a guarded canvas/UI switch, then run a simulator screenshot/baseline with `ARTISANZ_RENDERER_ID=pyqtgraph-snapshot`.
