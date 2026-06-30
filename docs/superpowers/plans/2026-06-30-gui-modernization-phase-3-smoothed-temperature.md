# GUI Modernization Phase 3 Smoothed Temperature Value Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving the deterministic smoothed ET/BT value selection out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for maintaining the decay-weight caches, choosing decay weights, appending smoothed values, and updating Matplotlib lines. Move only the "no connected values -> `-1`, otherwise decay-weighted average" value rule to `sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `smoothed_temperature_value(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helper for ET and BT smoothed value computation.
  - Preserve cache mutation, array appends, and rendering side effects in `canvas.py`.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover empty connected values.
  - Cover no-weight latest fallback.
  - Cover decay-weighted resampling semantics.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 smoothed-temperature progress.

## Task 1: Extract Smoothed Temperature Value Rule

- [x] **Step 1: Write failing tests**

Tests require:

- empty connected temperature values return `-1`
- connected values without usable decay weights return the latest connected value
- connected values with decay weights use the existing resampling/weighted-average semantics

Initial result: test collection failed because `smoothed_temperature_value` did not exist.

- [x] **Step 2: Implement pure helper**

Add `smoothed_temperature_value(...)` to `sample_processing.py` and export it.

- [x] **Step 3: Integrate `canvas.py`**

Replace the inline `len(sample_ctemp*) > 0` branches with the pure helper while keeping decay-weight cache mutation, smoothed-array appends, and line updates in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `107 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `135 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, no hidden side-effect movement, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical, Important, or Minor issues. It noted that direct helper use bypasses any external `decay_average` override, but found no in-tree subclass or monkeypatch relying on that boundary. Review artifact: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-smoothed-temperature-REVIEW.md`.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
