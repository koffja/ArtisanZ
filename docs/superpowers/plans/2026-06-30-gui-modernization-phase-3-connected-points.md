# GUI Modernization Phase 3 Connected Points Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:requesting-code-review before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting the deterministic connected-curve append decision from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep `inputFilter(...)`, math-expression evaluation, list mutation, Matplotlib `set_data(...)`, and GUI signaling in `canvas.py`. Move only the pure decision that determines whether a reading should produce a connected curve point, a disconnected `None` marker after long dropout runs, or no connected point yet.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add a pure helper for connected curve point selection.
- Modify: `src/artisanlib/canvas.py`
  - Replace duplicated ET/BT and extra-device connected point conditions with helper calls while preserving mutation and rendering.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover normal readings, short dropout gaps, and long dropout gaps.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record this Phase 3 extraction.

## Task 1: Extract Connected Curve Point Decision

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- valid readings append the reading value
- short dropout runs do not append a connected point
- dropout runs longer than `interpolate_max` append a `None` disconnection marker
- the helper uses the post-append readings sequence, matching existing `sample_processing()` semantics

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the connected-curve helper is not exported yet.

- [x] **Step 3: Implement helper**

Add a pure helper to `sample_processing.py`:

- `connected_curve_point(reading, readings, interpolate_max) -> ConnectedCurvePoint`

The public API should make the "do not append" case explicit without overloading it with `None`, because `None` is already a real disconnection marker.

- [x] **Step 4: Integrate `canvas.py`**

Use the helper for:

- ET connected sample (`sample_ctimex1` / `sample_ctemp1`)
- BT connected sample (`sample_ctimex2` / `sample_ctemp2`)
- extra device channel 1 connected samples
- extra device channel 2 connected samples

Preserve all list mutation, graph-line `set_data(...)` calls, input filtering, and expression evaluation.

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-connected-points.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for connected curve point decisions.

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

Ask for an independent review focused on behavior equivalence, dropout/disconnection semantics, and side-effect boundaries.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
