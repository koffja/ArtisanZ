# GUI Modernization Phase 3 PID PV Update Gate Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving deterministic PID process-value update gating out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for selecting the PID source, computing the process value, and side-effecting `self.pid.update(...)`. Move only the gate for whether the software PID should receive a process value.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `pid_process_value_update_enabled(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helper before PID process-value selection.
  - Preserve the lazy `externalPIDControl()` call by only reading it when the control button flag is enabled.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover disabled control button.
  - Cover external PID control rejection.
  - Cover missing external PID state.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 PID PV update gate progress.

## Task 1: Extract PID PV Update Gate

- [x] **Step 1: Write failing tests**

Tests require:

- disabled control button returns `False` even without external PID state
- enabled control button plus controller code `0` returns `True`
- enabled control button plus external controller codes `1`, `2`, `3`, and `4` returns `False`
- enabled control button with missing external PID state returns `False`

Initial result: test collection failed because `pid_process_value_update_enabled` did not exist.

- [x] **Step 2: Implement pure helper**

Add `pid_process_value_update_enabled(...)` to `sample_processing.py` and export it.

- [x] **Step 3: Integrate `canvas.py`**

Replace the inline control-button/external-PID condition with the pure helper while preserving lazy access to `externalPIDControl()` and keeping `self.pid.update(...)` in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `110 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

After request-code-reviewer found that `externalPIDControl()` returns an integer controller code rather than a boolean, the tests and helper contract were corrected to use `external_pid_controller: int | None`; focused verification still passed with `110 passed`.

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `138 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, lazy `externalPIDControl()` preservation, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical issues. One Important type-contract issue was fixed by changing the helper from a boolean external-PID flag to the real integer external PID controller code (`0` internal, `1..4` external) and updating tests accordingly. Re-review found no remaining issues.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
