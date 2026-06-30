# GUI Modernization Phase 3 Post-Sample Update Decisions Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving post-sample side-effect gating decisions out of `tgraphcanvas.sample_processing()` and into tested pure helpers.

**Architecture:** Keep `canvas.py` responsible for calling UI/application side effects (`updateAUC`, `updateAUCguide`, `calcBBPMetrics`). Move the deterministic decisions about whether those calls should happen into `sample_processing.py`.

**Tech Stack:** Pure Python dataclass helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `PostSampleUpdateDecisions`.
  - Add `post_sample_update_decisions(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Use the pure decisions before calling AUC/AUC guide/BBP side effects.
  - Preserve the separate exception boundaries for AUC and BBP updates.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover non-recording mode.
  - Cover recording mode with/without AUC guide.
  - Cover BBP update timing at `charge_index + 5`.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 post-sample update progress.

## Task 1: Extract Post-Sample Update Decisions

- [x] **Step 1: Write failing tests**

Tests require:

- no AUC/AUC guide/BBP work outside recording mode
- AUC updates during recording, with AUC guide following `AUCguideFlag`
- BBP metrics only at `sample_count == charge_index + 5` with a valid charge index

Initial result: test collection failed because `post_sample_update_decisions` did not exist.

- [x] **Step 2: Implement pure helper**

Add `PostSampleUpdateDecisions` and `post_sample_update_decisions(...)` to `sample_processing.py`.

- [x] **Step 3: Integrate `canvas.py`**

Replace the inline AUC/AUC guide/BBP gating logic with the pure decision object while keeping side effects and exception handling in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Result: focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_sample_processing.py`: `85 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior slices.

Result: `113 passed, 2 warnings` on 2026-06-30. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on behavior equivalence, exception-boundary preservation, and whether the helper meaningfully advances the worker-ready data boundary.

Review result: request-code-reviewer found no Critical or Important issues. Minor documentation status feedback was addressed by recording the broader regression result and review outcome.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
