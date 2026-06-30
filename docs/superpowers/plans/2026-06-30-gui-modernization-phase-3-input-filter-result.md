# GUI Modernization Phase 3 Input Filter Result Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving deterministic input-filter reading decisions out of `tgraphcanvas.inputFilter()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for exception logging and mutating existing sample arrays. Move duplicate/min-max/spike classification and historical-reading correction decisions to `sample_processing.py` as an `InputFilterResult` containing the current value plus explicit backfill updates.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add immutable `InputFilterResult`.
  - Add `input_filter_result(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Replace inline `inputFilter()` decision logic with `input_filter_result(...)`.
  - Apply returned backfill updates to the existing `tempx` list.
  - Preserve `canvas.py` exception logging and fallback behavior.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover duplicate-reading repeat behavior.
  - Cover min/max rejection after repeated historical readings.
  - Cover disabled-filter pass-through.
  - Cover one- and two-point historical correction backfills.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 input-filter decision progress.

## Task 1: Extract Input Filter Result Decision

- [x] **Step 1: Write failing tests**

Initial result: the focused sample-processing suite collected successfully and failed because `input_filter_result` did not exist.

- [x] **Step 2: Implement pure helper**

Add `InputFilterResult` and `input_filter_result(...)` to `sample_processing.py` and export both.

- [x] **Step 3: Integrate `canvas.py`**

Replace the inline `tgraphcanvas.inputFilter()` duplicate/min-max/spike decision logic with the pure helper. Keep array mutation limited to applying returned `BackfillUpdate` entries.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `122 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior Phase 2/3 slices.

Result: `150 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, backfill semantics, hidden mutation changes, and whether the extracted helper advances worker-ready processing boundaries.

Review result: request-code-reviewer found no Critical, Important, or Minor issues. It also ran an in-memory equivalence harness over 16,128 input combinations and found the old and new branches equivalent. Review artifact: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-input-filter-result-REVIEW.md`.

- [ ] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
