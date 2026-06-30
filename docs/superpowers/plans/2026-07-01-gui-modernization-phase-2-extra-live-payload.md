# GUI Modernization Phase 2 Extra-Device Live Payload Plan

**Goal:** Route extra-device live curve Matplotlib updates through the same `LiveCurveData` payload boundary used by ET, BT, Delta ET, and Delta BT.

**Scope:**

- `src/artisanlib/canvas.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Preserve existing extra-device visibility checks, line counters, and line selection logic.
- [x] Build `LiveCurveData` from the already prepared `full_curve_data()` payloads for extra channel 1 and 2.
- [x] Apply those payloads through `apply_matplotlib_live_curve_data()`.
- [x] Keep runtime renderer selection unchanged.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/canvas.py artisanlib/plot_live_frame.py
.venv/bin/python -m ruff check artisanlib/canvas.py artisanlib/plot_live_frame.py
git diff --check
```

Result: `145 passed`; compile, ruff, and diff check passed.

## Notes

This completes the first pass of live Matplotlib curve update isolation for the curves touched directly by `sample_processing()`. Axis/projection updates and the eventual guarded PyQtGraph runtime switch remain separate follow-up slices.
