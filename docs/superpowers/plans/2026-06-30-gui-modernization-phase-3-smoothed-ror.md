# GUI Modernization Phase 3 Smoothed RoR Value Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving the deterministic smoothed RoR value calculation out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for deciding whether each delta filter window is ready, maintaining the shared decay-weight cache, applying Delta ET/BT math expressions, and mutating `self.rateofchange*`. Move only the final decay-weighted smoothing value rule for unfiltered RoR arrays to `sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `smoothed_rate_of_change_value(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helper for ET and BT RoR smoothing.
  - Preserve decay-weight cache mutation and rate-of-change side effects in `canvas.py`.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover no-weight latest fallback.
  - Cover decay-weighted resampling semantics.
  - Cover empty-rate fallback.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 smoothed-RoR progress.

## Task 1: Extract Smoothed RoR Value Rule

- [x] **Step 1: Write failing tests**

Tests require:

- no usable decay weights returns the latest unfiltered RoR value
- decay weights use the existing decay-weighted average/resampling semantics
- empty unfiltered RoR arrays return `-1`

Initial result: test collection failed because `smoothed_rate_of_change_value` did not exist.

- [x] **Step 2: Implement pure helper**

Add `smoothed_rate_of_change_value(...)` to `sample_processing.py` and export it.

- [x] **Step 3: Integrate `canvas.py`**

Replace the two inline RoR `self.decay_average(...)` smoothing calls with the pure helper while keeping filter-readiness checks, cache updates, and `self.rateofchange*` mutation in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `113 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `141 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, no hidden side-effect movement, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical, Important, or Minor issues. It noted the intentional internal dispatch change away from `self.decay_average(...)`, and found no in-tree subclass or override relying on that method. Review artifact: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-smoothed-ror-REVIEW.md`.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
