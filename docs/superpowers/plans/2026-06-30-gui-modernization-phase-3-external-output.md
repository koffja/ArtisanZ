# GUI Modernization Phase 3 External Output Decisions Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving deterministic external-output program payload decisions out of `tgraphcanvas.sample_processing()` and into tested pure helpers.

**Architecture:** Keep `canvas.py` responsible for background index lookup and the side-effecting `call_prog_with_args(...)` call. Move background lookup-time selection and external command formatting to `sample_processing.py`.

**Tech Stack:** Pure Python helpers, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `external_program_background_lookup_time(...)`.
  - Add `external_program_output_command(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helpers inside the existing external-output try/except block.
  - Preserve behavior for foreground, background-before-charge, and background-after-charge cases.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover disabled background lookup.
  - Cover background lookup before and after CHARGE.
  - Cover external command formatting with one decimal and `-1` background fallback.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 external-output payload progress.

## Task 1: Extract External Output Decisions

- [x] **Step 1: Write failing tests**

Tests require:

- no background lookup time when no background is active
- lookup time equals current time before CHARGE
- lookup time subtracts CHARGE timestamp after CHARGE
- command string preserves one-decimal formatting and `-1.0` background fallback

Initial result: test collection failed because `external_program_background_lookup_time` did not exist.

- [x] **Step 2: Implement pure helpers**

Add helpers to `sample_processing.py` and export them.

- [x] **Step 3: Integrate `canvas.py`**

Replace inline external-output lookup-time and command formatting with helpers while keeping side effects and exception handling in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Result: focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `89 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `117 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, exception-boundary preservation, command formatting safety, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical, Important, or blocking Minor issues. Recommendation was to keep the command-string helper behavior-preserving because `call_prog_with_args(...)` currently accepts a single command string.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
