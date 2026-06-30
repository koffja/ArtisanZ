# GUI Modernization Phase 3 Full Curve Data Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving deterministic connected-curve data preparation for live ET/BT and extra-device lines out of inline `tgraphcanvas.sample_processing()` calls and into a tested pure helper.

**Architecture:** Keep `canvas.py` responsible for live state mutation, visibility checks, Matplotlib `Line2D` mutation, and numpy conversion at the current renderer boundary. Use a tuple-backed `CurveWindowData` payload for full connected curves so the same renderer-facing shape can serve current Matplotlib and future PyQtGraph/OpenGL adapters.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `full_curve_data(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use `full_curve_data(...)` for live ET/BT connected line updates.
  - Use `full_curve_data(...)` for visible extra-device connected line updates.
  - Preserve existing visibility checks and `numpy.array(...)` conversion at the Matplotlib boundary.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover empty full-curve payload behavior.
  - Cover connected curve values, including `None` gaps.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 full-curve payload progress.

## Task 1: Extract Full Connected Curve Data Payload

- [x] **Step 1: Write failing tests**

Tests require:

- empty sequences return empty times and values
- full connected curve values are preserved in order
- `None` gaps remain in the payload for renderer-specific handling

Initial result: the focused sample-processing suite collected successfully and failed because `full_curve_data` did not exist.

- [x] **Step 2: Implement pure helper**

Add `full_curve_data(...)` to `sample_processing.py` and export it.

- [x] **Step 3: Integrate `canvas.py`**

Replace inline ET/BT and extra-device connected curve `set_data(...)` payload preparation with calls to `full_curve_data(...)`, preserving existing side effects and Matplotlib conversion.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `117 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior Phase 2/3 slices.

Result: `145 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, renderer-boundary clarity, current Matplotlib safety, and future PyQtGraph/OpenGL suitability.

Review result: request-code-reviewer found no Critical, Important, or Minor issues. Review artifact: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-full-curve-data-REVIEW.md`.

- [ ] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
