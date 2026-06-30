# GUI Modernization Phase 3 Decay Average Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:verification-before-completion before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving live decay-weighted averaging out of `tgraphcanvas.decay_average()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` as the compatibility owner of the existing `decay_average(...)` method name and call sites. Move the deterministic resampling, dropout skipping, weighted average, and fallback average behavior to `sample_processing.py`.

**Tech Stack:** Pure Python helper with NumPy interpolation/average, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `decay_weighted_average(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Delegate `tgraphcanvas.decay_average(...)` to the pure helper.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover no-weight fallback.
  - Cover dropout/`None` skipping with legacy resampling semantics.
  - Cover no-valid-value fallback.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 decay-average progress.

## Task 1: Extract Decay Average

- [x] **Step 1: Write failing tests**

Initial result: test collection failed because `decay_weighted_average` did not exist.

- [x] **Step 2: Implement pure helper**

Implemented `decay_weighted_average(...)` in `sample_processing.py`, preserving:

- latest-value fallback when weights are missing or unusable
- `None`/`-1` dropout skipping
- legacy resampling to a linear interval based on the current sampling delay
- fallback to a standard average if weighted averaging fails

- [x] **Step 3: Integrate `canvas.py`**

`tgraphcanvas.decay_average(...)` now delegates to the pure helper with `self.delay / 1000.` while preserving the old method signature and call sites.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Result: focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `82 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `110 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Review**

Review for behavior equivalence, exception/fallback behavior, and preservation of the public `canvas.decay_average(...)` compatibility surface.

Review result: `canvas.decay_average(...)` keeps the old method signature and now delegates to `decay_weighted_average(...)` with `self.delay / 1000.`. The helper preserves the old no-weight fallback, dropout skipping, NumPy resampling, and weighted-average exception fallback behavior.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
