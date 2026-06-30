# GUI Modernization Phase 3 PID SV Target Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving deterministic PID set-value target selection out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for calling `calcSV(...)` and side-effecting PID setters. Move only the choice between Fuji PID, software PID, and no SV update to `sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `PidSvUpdateTarget`.
  - Add `pid_sv_update_target(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helper for the PID SV update branch.
  - Preserve the existing Fuji priority and setter behavior.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover no update when sampling is off.
  - Cover Fuji target only while recording with background-follow enabled.
  - Cover Fuji priority over software PID when both would otherwise be eligible.
  - Cover software PID ramp/soak and background-follow eligibility.
  - Cover inactive ramp mode and manual mode rejection.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 PID SV target progress.

## Task 1: Extract PID SV Target Selection

- [x] **Step 1: Write failing tests**

Tests require:

- sampling off returns no target
- Fuji target requires device `0`, Fuji background follow, and recording
- Fuji target wins before software PID if both are eligible
- software PID target is selected for active ramp/soak mode
- software PID target is selected for background-follow mode even when inactive
- inactive ramp mode and manual mode return no target

Initial result: test collection failed because `pid_sv_update_target` did not exist.

- [x] **Step 2: Implement pure helper**

Add `PidSvUpdateTarget` and `pid_sv_update_target(...)` to `sample_processing.py` and export both.

- [x] **Step 3: Integrate `canvas.py`**

Replace the duplicated inline SV target branch with the pure helper while keeping `calcSV(...)`, `setsv(...)`, and `setSV(...)` in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Result: focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `98 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `126 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, Fuji/software priority, lazy side-effect preservation, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical or Important issues. One Minor lazy-equivalence issue was fixed by allowing `pid_sv_update_target(...)` to select Fuji without software PID state and by reading `pidcontrol` attributes only after Fuji target selection returns no target.

- [ ] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
