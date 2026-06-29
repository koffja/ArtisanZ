# GUI Modernization Phase 3 Processed Frame Contract Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:requesting-code-review before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Phase 3 from isolated helper extraction toward a stable processed-frame data boundary that can later be produced outside the GUI thread.

**Architecture:** Keep all current GUI-thread side effects in `canvas.py`: Matplotlib line mutation, PID update, signal emission, x-axis mutation, and TP/DRY/FCs event marking. Add a pure `ProcessedSampleFrame` contract in `sample_processing.py` that aggregates deterministic display, axis, and pre-TP auto-event decisions already extracted in earlier Phase 3 slices. Keep DRY/FCs as a separate post-TP phase-event helper because TP timeout/check can update `TPalarmtimeindex` before those phase events are evaluated.

**Tech Stack:** Pure Python dataclasses, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `AutoEventDecisions`.
  - Add `PhaseEventDecisions`.
  - Add `ProcessedSampleFrame`.
  - Add `build_live_processed_sample_frame(...)`.
  - Add `phase_event_candidates_after_turning_point(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Build a processed frame after smoothing/RoR calculation.
  - Read displayed RoR values, RoR line windows, x-axis extension, and pre-TP auto-event candidates from the frame.
  - Preserve post-TP DRY/FCs behavior by evaluating those phase events through a separate helper after possible TP state mutation.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover the frame's display/axis/event aggregation.
  - Cover closed-gate behavior that avoids unnecessary sample-time access.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 processed-frame progress.

## Task 1: Add Processed Frame Contract

- [x] **Step 1: Write failing tests**

Add tests that require `build_live_processed_sample_frame(...)` to collect:

- latest ET/BT and smoothed ET/BT
- PID process value
- displayed RoR values after limits
- RoR curve windows
- live x-axis extension target
- auto CHARGE, TP timeout/check, and DROP candidates

Add a separate test that applies the TP timeout result before evaluating DRY/FCs phase-event candidates.

Also add a closed-gate test using `NoAccessSequence` to verify fixed-axis and uncharged-event gates do not touch sample-time data.

- [x] **Step 2: Implement dataclasses and builder**

Add immutable frame dataclasses and compose the already-tested pure helpers.

- [x] **Step 3: Integrate `canvas.py`**

Use the processed frame inside `sample_processing()` while preserving side effects in the original location.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior Phase 3 slices.

Result: `94 passed, 2 warnings` on 2026-06-30 after code-review fixes. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

Additional simulator smoke result:

- Scenario: 20-second `ARTISANZ_GUI_PERF_AUTORUN_MODE=simulator-recording` against `test/sanity/data/artisan/profile1.alog`.
- Screenshot: `/tmp/artisanz-phase3-frame.png`.
- Metrics: `sample_processing max=0.574ms avg=0.500ms`; `updategraphics max=40.563ms avg=3.957ms`; `updateBackground max=84.649ms avg=39.025ms`; `redraw max=136.098ms avg=98.929ms`.

- [x] **Step 3: Request code review**

Ask for an independent review focused on behavior equivalence, event ordering, frame field semantics, and future threading suitability.

Result: review found no critical issues, one important API-boundary issue, and two minor issues. Fixes applied:

- Removed stale pre-TP DRY/FCs fields from `AutoEventDecisions`.
- Added `PhaseEventDecisions` and `phase_event_candidates_after_turning_point(...)`.
- Added a TP-timeout regression test that evaluates phase events after the timeout state is applied.
- Changed the frame test fixture to use realistic sample-time length.
- Softened benchmark language so the short smoke result is directional, not causal proof.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
