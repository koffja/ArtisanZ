# GUI Modernization Phase 3 Windowed Curve Data Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving the deterministic Delta ET/BT line-window data preparation out of `tgraphcanvas.sample_processing()` and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for live sampling state, visibility flags, Matplotlib `Line2D` mutation, and numpy conversion for the current renderer. Move the charge/drop RoR window slicing result into `sample_processing.py` as a renderer-facing data payload so future PyQtGraph/OpenGL adapters can consume prepared curve data without duplicating `canvas.py` slice rules.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add immutable `CurveWindowData`.
  - Add `windowed_curve_data(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use `windowed_curve_data(...)` for live Delta ET and Delta BT line updates.
  - Preserve the existing `numpy.array(...)` conversion at the Matplotlib boundary.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover no-window empty payload behavior.
  - Cover existing `start:end` slice semantics, including `None` values.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 renderer-facing curve payload progress.

## Task 1: Extract Windowed Curve Data Payload

- [x] **Step 1: Write failing tests**

Tests require:

- `None` window returns empty times and values
- an explicit `(start, end)` window returns the same `start:end` slices previously passed inline to Matplotlib
- `None` curve values are preserved for renderer-specific handling

Initial result: the focused sample-processing suite collected successfully and failed because `windowed_curve_data` did not exist.

- [x] **Step 2: Implement pure helper**

Add `CurveWindowData` and `windowed_curve_data(...)` to `sample_processing.py` and export both.

- [x] **Step 3: Integrate `canvas.py`**

Replace the two inline Delta ET/BT line data slices with calls to `windowed_curve_data(...)`, preserving visibility checks, `Line2D.set_data(...)`, and Matplotlib-side numpy conversion.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `115 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior Phase 2/3 slices.

Result: `143 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, renderer-boundary clarity, and whether the tuple payload is safe for current Matplotlib and future PyQtGraph/OpenGL use.

Review result: request-code-reviewer found no Critical, Important, or Minor issues. Review artifact: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-windowed-curve-data-REVIEW.md`.

- [ ] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
