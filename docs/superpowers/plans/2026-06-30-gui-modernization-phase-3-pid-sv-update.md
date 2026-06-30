# GUI Modernization Phase 3 PID SV Update Decisions Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving deterministic PID set-value update decisions out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for calling `calcSV(...)` and side-effecting PID setters. Move the repeated decision about whether a calculated SV should be sent, and how negative values are clamped, to `sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `pid_set_value_update(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helper for FujiPID and regular PID SV update paths.
  - Preserve old behavior: compare the raw calculated SV to the current SV before clamping negative values to `0.0`.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover no update for `None`.
  - Cover no update when calculated SV equals current SV.
  - Cover normal update.
  - Cover current PID SV being `None`.
  - Cover negative calculated SV clamping after the raw comparison.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 PID SV update progress.

## Task 1: Extract PID SV Update Decision

- [x] **Step 1: Write failing tests**

Tests require:

- `None` calculated SV returns no update
- calculated SV equal to current SV returns no update
- positive changed SV is returned unchanged
- negative changed SV returns `0.0`, even when current SV is already `0.0`

Initial result: test collection failed because `pid_set_value_update` did not exist.

- [x] **Step 2: Implement pure helper**

Add `pid_set_value_update(...)` to `sample_processing.py` and export it.

- [x] **Step 3: Integrate `canvas.py`**

Replace duplicated inline SV update checks in the FujiPID and regular PID branches with the pure helper, preserving setter arguments.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Result: focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `92 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed
- `pyright artisanlib/sample_processing.py artisanlib/canvas.py`: not run; `pyright` is not installed in the local `.venv`.

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `120 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, negative-SV clamp ordering, exception-boundary preservation, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical issues. One Important type-contract issue was fixed by widening `current_sv` from `float` to `float | None` and adding coverage for the initial `None` PID SV state. No security or performance concerns were reported.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
