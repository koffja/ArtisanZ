# GUI Modernization Phase 2 Projection Payload Plan

**Goal:** Route live projection curve updates through the renderer-facing `LiveCurveData` boundary without changing projection math or runtime renderer selection.

**Scope:**

- `src/artisanlib/canvas.py`
- `src/artisanlib/plot_live_frame.py`
- `src/test/unitary/artisanlib/test_plot_live_frame.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Keep existing linear, quadratic, and RoR projection calculations unchanged.
- [x] Add a small sequence applier for Matplotlib line updates that normalizes caller-owned sequences into `LiveCurveData`.
- [x] Route BT, ET, Delta BT, and Delta ET projection lines through the shared live-curve applier.
- [x] Preserve projection clearing for disabled projection state and exception recovery.
- [x] Cover empty projection clearing against a real Matplotlib `Line2D`.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_sample_processing.py test/unitary/artisanlib/test_canvas.py::TestXAxisToSM -q
.venv/bin/python -m py_compile artisanlib/canvas.py artisanlib/plot_live_frame.py test/unitary/artisanlib/test_plot_live_frame.py
.venv/bin/python -m ruff check artisanlib/canvas.py artisanlib/plot_live_frame.py test/unitary/artisanlib/test_plot_live_frame.py
git diff --check
```

Result: `153 passed`; compile, ruff, and diff check passed. Code review found no blocking issues; the suggested non-empty real `Line2D` helper test was added before commit.

## Notes

This continues Phase 2 by shrinking the remaining direct Matplotlib mutation surface in `canvas.updateProjection()`. The projection payload uses the same contract consumed by the PyQtGraph proof-of-concept applier, so the future renderer switch can consume projection data without learning about canvas internals.
