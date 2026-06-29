# GUI Modernization Phase 3 Input Filter Backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:requesting-code-review before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting the deterministic input-filter backfill decision from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep `inputFilter(...)`, list mutation, Matplotlib `set_data(...)`, and GUI signaling in `canvas.py`. Move only the pure decision that determines which already-rendered connected curve samples need to be overwritten after input filters destructively adjust the latest or previous raw readings.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add a pure helper for backfill update selection.
- Modify: `src/artisanlib/canvas.py`
  - Replace duplicated ET/BT and extra-device backfill condition blocks with helper calls while preserving mutation and rendering.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover latest-sample backfill, previous-sample backfill, timestamp mismatch, unchanged values, and missing previous sentinels.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record this Phase 3 extraction.

## Task 1: Extract Input Filter Backfill Decisions

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- latest connected sample is backfilled when timestamp matches and value changed
- previous connected sample is backfilled when timestamp matches and value changed
- no update when timestamp differs
- no update when old and new values are equal
- no update when the saved previous value is `None`

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the backfill helper is not exported yet.

- [x] **Step 3: Implement helper**

Add pure helpers to `sample_processing.py`:

- `BackfillUpdate(index, value)`
- `input_filter_backfill_updates(connected_times, raw_times, raw_values, previous_latest, previous_previous) -> tuple[BackfillUpdate, ...]`

- [x] **Step 4: Integrate `canvas.py`**

Use the helper for:

- ET connected curve backfill
- BT connected curve backfill
- extra device channel 1 connected curve backfill
- extra device channel 2 connected curve backfill

Preserve all list mutation and only replace the duplicated decision conditions.

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-input-filter-backfill.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for input-filter connected curve backfill decisions.

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

Ask for an independent review focused on behavior equivalence, timestamp matching, and side-effect boundaries.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
