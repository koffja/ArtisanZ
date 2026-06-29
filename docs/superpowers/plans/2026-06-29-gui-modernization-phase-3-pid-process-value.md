# GUI Modernization Phase 3 PID Process Value Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting PID process-value source selection from `tgraphcanvas.sample_processing()` into a tested pure helper.

**Architecture:** Keep device sampling, PID mutation, Qt signals, and rendering in their existing runtime locations. Move only the deterministic selection of ET, BT, or extra-device channel values into `src/artisanlib/sample_processing.py` so the long GUI-thread method becomes thinner without changing roast behavior.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `pid_process_value()` for PID source selection.
- Modify: `src/artisanlib/canvas.py`
  - Replace the inline PID source-selection branch with the helper call.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover ET, BT, extra-device channel 1, extra-device channel 2, and missing-source fallback.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record the Phase 3 processing boundary progress.

## Task 1: Extract PID Source Selection

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- PID source `0` and `1` use smoothed BT.
- PID source `2` uses smoothed ET.
- PID source `5` uses extra device 2 channel 1.
- PID source `6` uses extra device 2 channel 2.
- Missing extra source falls back to `0.0`.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because `pid_process_value` is not exported yet.

- [x] **Step 3: Implement helper**

Add `pid_process_value()` to `sample_processing.py` with:

- default/BT sources returning smoothed BT
- ET source returning smoothed ET
- extra-device sources mapping PID source `3, 5, 7...` to channel 1
- extra-device sources mapping PID source `4, 6, 8...` to channel 2
- safe `0.0` fallback when a configured extra source is missing

- [x] **Step 4: Integrate `canvas.py`**

Replace the inline PID process-value branch in `tgraphcanvas.sample_processing()` with a call to `pid_process_value()`, then keep the existing `self.pid.update(process_value)` side effect in place.

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-3-pid-process-value.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for smoothing-weight selection and PID process-value source selection.

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

Ask for an independent review of this Phase 3 slice before commit, focused on behavior equivalence, missing edge cases, and accidental GUI-thread side effects.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
