# GUI Modernization Phase 2 PyQtGraph Live Applier Plan

**Goal:** Give the live-frame payload boundary a PyQtGraph consumer before switching runtime rendering, so Matplotlib and PyQtGraph paths can share the same curve payload contract.

**Scope:**

- `src/artisanlib/plot_live_frame.py`
- `src/test/unitary/artisanlib/test_plot_live_frame.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add `apply_pyqtgraph_live_curve_data()` that calls `setData()` on PyQtGraph-style items.
- [x] Convert live dropout values from `None` to `math.nan`, matching the existing snapshot PyQtGraph adapter behavior.
- [x] Add `apply_pyqtgraph_live_frame()` for named multi-curve item updates.
- [x] Keep runtime rendering unchanged; this slice only prepares the PyQtGraph live path.
- [x] Run focused verification:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_live_frame.py -q
```

Result: `10 passed` for live-frame payload tests before broader verification.

Broader verification also passed:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_smoke.py test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/plot_live_frame.py test/unitary/artisanlib/test_plot_live_frame.py
.venv/bin/python -m ruff check artisanlib/plot_live_frame.py test/unitary/artisanlib/test_plot_live_frame.py
git diff --check
```

Result: `155 passed`; compile, ruff, and diff check passed.

## Notes

The next Phase 2 slice can either wire extra-device Matplotlib payloads through `LiveCurveData` or prototype a guarded PyQtGraph live renderer using these applier helpers.
