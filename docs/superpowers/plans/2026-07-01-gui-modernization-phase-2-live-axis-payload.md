# GUI Modernization Phase 2 Live Axis Payload Plan

**Goal:** Move live x-axis range application behind the same renderer payload boundary used by live curve data.

**Scope:**

- `src/artisanlib/plot_live_frame.py`
- `src/artisanlib/canvas.py`
- `src/test/unitary/artisanlib/test_plot_live_frame.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add immutable `LiveAxisRange` payload with bound validation.
- [x] Add `apply_matplotlib_live_axis_range()` for Matplotlib `set_xlim()` application.
- [x] Route the `xaxistosm()` Matplotlib `set_xlim()` application through `LiveAxisRange`.
- [x] Route manual-mode live x-axis extension through `LiveAxisRange`.
- [x] Keep `xaxistosm()` calls in place so existing tick/scale behavior stays unchanged.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_canvas.py::TestXAxisToSM test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/canvas.py artisanlib/plot_live_frame.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_canvas.py
.venv/bin/python -m ruff check artisanlib/canvas.py artisanlib/plot_live_frame.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_canvas.py
git diff --check
```

Result: `150 passed`; compile, ruff, and diff check passed.

## Notes

This slice does not alter projection logic or renderer selection. It only turns live axis range mutation into an explicit payload/application step, preparing the same responsibility to move behind a future `LivePlotRenderer`.

Code review note: the first draft added a manual-mode pre-call with mixed coordinate systems. Review caught that it could reject a valid post-CHARGE state before `xaxistosm()` applied the charge offset. The final version removes that pre-call and tests the `startofx > endofx` but corrected-final-range case directly through `xaxistosm()`.
