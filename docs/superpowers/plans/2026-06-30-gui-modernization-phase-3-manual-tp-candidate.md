# GUI Modernization Phase 3 Manual TP Candidate Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving the deterministic manual-mode turning-point candidate condition out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for calling `checkTPalarmtime()`, `findTP()`, mutating `TPalarmtimeindex`, and emitting `markTPSignal`. Move only the pure readiness condition to `sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `manual_turning_point_check_candidate(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helper in the manual-device branch.
  - Preserve `checkTPalarmtime()`, `findTP()`, and signal side effects in `canvas.py`.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover recording, missing TP, charge index, and strict five-sample gap requirements.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 manual TP candidate progress.

## Task 1: Extract Manual TP Candidate Condition

- [x] **Step 1: Write failing tests**

Tests require:

- no candidate outside recording
- no candidate when TP is already set
- no candidate before CHARGE
- no candidate at exactly `charge_index + 5` samples
- candidate once sample count is strictly greater than `charge_index + 5`

Initial result: test collection failed because `manual_turning_point_check_candidate` did not exist.

- [x] **Step 2: Implement pure helper**

Add `manual_turning_point_check_candidate(...)` to `sample_processing.py` and export it.

- [x] **Step 3: Integrate `canvas.py`**

Replace the inline manual-mode TP candidate condition with the pure helper while keeping `checkTPalarmtime()`, `findTP()`, and `markTPSignal.emit()` unchanged.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `100 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `128 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, strict sample-count boundary, side-effect preservation, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical, Important, or Minor issues. Review artifact: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-manual-tp-candidate-REVIEW.md`.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
