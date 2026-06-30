# GUI Modernization Phase 3 Extra Device Length Diagnostics Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving deterministic extra-device buffer length diagnostics out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for detecting the mismatch branch and raising the exception. Move only the message selection and formatting logic to `sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `extra_device_length_error_message(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure helper in the extra-device buffer mismatch branch.
  - Preserve the existing exception boundary.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover matching buffers.
  - Cover precise near-mismatch diagnostics.
  - Cover fallback general mismatch diagnostics.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 extra-device length diagnostic progress.

## Task 1: Extract Extra Device Length Diagnostic

- [x] **Step 1: Write failing tests**

Tests require:

- matching serial/device/temp counts return `None`
- one-off serial count mismatch names `Extra-Serial`
- one-off temp count mismatch names `Extra-Temp`
- a simultaneous `nxdevices + 1` and `nxdevices - 1` mismatch reports the `nxdevices - 1` location first
- unclear mismatch returns the legacy summary string

Initial result: test collection failed because `extra_device_length_error_message` did not exist.

- [x] **Step 2: Implement pure helper**

Add `extra_device_length_error_message(...)` to `sample_processing.py` and export it.

- [x] **Step 3: Integrate `canvas.py`**

Replace inline mismatch-message construction with the pure helper while keeping the mismatch branch and raised exception in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `104 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `132 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on exact legacy message compatibility, exception-boundary preservation, and whether the helper advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical, Important, or Minor issues. Two optional hardening recommendations were applied: an explicit `nxdevices - 1` before `nxdevices + 1` priority test, and an assertion for the unreachable matching-buffer fallback in `canvas.py`. Review artifact: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-extra-device-lengths-REVIEW.md`.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
