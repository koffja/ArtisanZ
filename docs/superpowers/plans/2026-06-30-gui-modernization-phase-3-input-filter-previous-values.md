# GUI Modernization Phase 3 Input Filter Previous Values Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:requesting-code-review before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting the deterministic input-filter previous-reading snapshot decision from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep `inputFilter(...)`, list mutation, Matplotlib `set_data(...)`, and GUI signaling in `canvas.py`. Move only the pure decision that captures the latest and previous raw readings before input filters potentially mutate them.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add a pure helper for previous-reading snapshot selection.
- Modify: `src/artisanlib/canvas.py`
  - Replace duplicated ET/BT and extra-device previous-reading capture blocks with helper calls while preserving mutation and rendering.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover disabled filters, empty readings, one reading, and two-or-more readings.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record this Phase 3 extraction.

## Task 1: Extract Input Filter Previous-Value Snapshot

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- disabled input filters return empty previous values without reading the sequence
- enabled input filters with no readings return empty previous values
- enabled input filters with one reading return latest only
- enabled input filters with two-or-more readings return latest and previous

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the previous-values helper is not exported yet.

- [x] **Step 3: Implement helper**

Add pure helpers to `sample_processing.py`:

- `PreviousReadings(latest, previous)`
- `input_filter_previous_values(readings, input_filters_enabled) -> PreviousReadings`

- [x] **Step 4: Integrate `canvas.py`**

Use the helper for:

- ET previous-value capture
- BT previous-value capture
- extra device channel 1 previous-value capture
- extra device channel 2 previous-value capture

Preserve all list mutation and only replace the duplicated snapshot decision.

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-input-filter-previous-values.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for input-filter previous-reading snapshots.

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

Ask for an independent review focused on behavior equivalence, disabled-filter access, and side-effect boundaries.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
