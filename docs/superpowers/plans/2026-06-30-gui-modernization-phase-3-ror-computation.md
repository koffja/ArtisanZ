# GUI Modernization Phase 3 RoR Computation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:requesting-code-review before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving live RoR computation out of `tgraphcanvas` methods and into tested pure helpers.

**Architecture:** Keep `canvas.py` as the compatibility owner of `compute_ror_simple(...)` and `compute_ror(...)` method names, exception logging, and call sites. Move the deterministic rate-of-rise math, legacy left-point averaging, dropout fallback, sample-window choice, and optional polyfit slope calculation to `sample_processing.py`.

**Tech Stack:** Pure Python helpers with NumPy polyfit, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `simple_rate_of_rise_per_minute(...)`.
  - Add `rate_of_rise_per_minute(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Delegate `compute_ror_simple(...)` and `compute_ror(...)` to the pure helpers.
  - Preserve existing exception logging and method names.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover legacy left-point averaging.
  - Cover dropout fallback to the previous RoR value.
  - Cover sample-window selection.
  - Cover optional polyfit slope calculation.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 RoR computation progress.

## Task 1: Extract RoR Computation

- [x] **Step 1: Write failing tests**

Add tests that require:

- simple RoR to preserve the legacy left-point averaging rule
- dropout samples to repeat the previous RoR value or fall back to `0.0`
- full RoR helper to choose `max(2, delta_samples + 1)` within available samples
- polyfit mode to use the least-squares slope when enabled
- polyfit failures to fall back to the legacy simple RoR calculation

- [x] **Step 2: Implement pure helpers**

Add helpers to `sample_processing.py` and keep Windows/OpenBLAS polyfit failures falling back to the simple algorithm.

- [x] **Step 3: Integrate `canvas.py`**

Make the existing `tgraphcanvas.compute_ror_simple(...)` and `compute_ror(...)` delegate to the pure helpers so call sites stay stable.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Result: focused verification passed on 2026-06-30 after adding the polyfit-fallback regression:

- `test/unitary/artisanlib/test_sample_processing.py`: `79 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior Phase 3 slices.

Result: `104 passed, 2 warnings` on 2026-06-30 after adding the polyfit-fallback regression. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Review**

Review focused on RoR behavior equivalence, polyfit fallback, dropout behavior, and future worker-thread suitability. Under the current tool rules, subagent review requires explicit user authorization, so this slice used local review plus an added regression for `polyfit` failure fallback.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
