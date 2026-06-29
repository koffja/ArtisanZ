# GUI Modernization Phase 3 Axis Extension Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:requesting-code-review before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting the deterministic x-axis auto-extension decisions from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep `self.endofx` mutation, Matplotlib `set_xlim(...)`, and `xaxistosm()` in `canvas.py`. Move only the pure decisions that determine whether live-recording and manual-mode sampling should extend the x-axis and to which new end time.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add pure helpers for live and manual x-axis extension decisions.
- Modify: `src/artisanlib/canvas.py`
  - Replace inline x-axis extension calculations with helper calls while preserving side effects.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover disabled access, no-extension thresholds, charge-offset behavior, and extension values.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record this Phase 3 extraction.

## Task 1: Extract Axis Extension Decisions

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- live x-axis extension skips sample-time access when fixed or locked
- live x-axis extension returns `None` before the trigger threshold
- live x-axis extension preserves charge-offset and 1/14 trigger-period semantics
- manual x-axis extension skips sample-time access when fixed or locked
- manual x-axis extension returns `None` before the 45-second threshold
- manual x-axis extension preserves charge-offset and +180 second extension semantics

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the axis extension helpers are not exported yet.

- [x] **Step 3: Implement helpers**

Add pure helpers to `sample_processing.py`:

- `live_x_axis_extension_end(...) -> float | None`
- `manual_x_axis_extension_end(...) -> float | None`

- [x] **Step 4: Integrate `canvas.py`**

Use the helpers while preserving:

- `self.endofx = ...`
- `self.ax.set_xlim(...)` in manual mode
- `self.xaxistosm()`

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-axis-extension.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for x-axis auto-extension decisions.

- [x] **Step 2: Run focused verification**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Expected: PASS.

- [x] **Step 3: Request code review**

Ask for an independent review focused on behavior equivalence, disabled-state access, axis math, and side-effect boundaries.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
