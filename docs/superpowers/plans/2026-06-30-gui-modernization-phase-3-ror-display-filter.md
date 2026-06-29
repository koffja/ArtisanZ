# GUI Modernization Phase 3 RoR Display Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting RoR filter/window/display decisions from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep `compute_ror()`, `decay_average()`, math-expression evaluation, line mutation, and Matplotlib `set_data()` calls in `canvas.py`. Move only deterministic decisions for delta smoothing filter readiness, displayed RoR limit masking, and RoR curve data window selection into `src/artisanlib/sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add pure RoR helpers for delta smoothing filter size, displayed RoR value masking, and RoR curve window selection.
- Modify: `src/artisanlib/canvas.py`
  - Replace inline RoR filter/window/display decisions with helper calls while preserving all numerical computation and plot mutation side effects.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover smoothing filter boundaries, RoR display bounds, disabled limit behavior, and charge/drop curve-window behavior.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record the Phase 3 RoR display/filter decision extraction.

## Task 1: Extract RoR Display/Filter Decisions

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- delta smoothing filter size uses the existing `int(round(delta_filter / 2.0))` rule
- zero/too-small sample windows disable delta smoothing
- displayed RoR values pass through when limits are disabled
- displayed RoR values become `None` outside or exactly on the open lower/upper bounds
- RoR curve window returns `None` before CHARGE
- RoR curve window starts after CHARGE plus filter/sample warmup and ends at DROP+1 when DROP exists

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the RoR helpers are not exported yet.

- [x] **Step 3: Implement helpers**

Add pure helpers to `sample_processing.py`:

- `delta_smoothing_filter_size(delta_filter, sample_count, unfiltered_count) -> int | None`
- `displayed_ror_value(rate_of_change, ror_limit_enabled, max_ror_limit, ror_limit, ror_limit_min) -> float | None`
- `ror_curve_window(charge_index, drop_index, sample_count, delta_filter, delta_samples) -> tuple[int, int] | None`

- [x] **Step 4: Integrate `canvas.py`**

Use the helpers while preserving:

- `self.compute_ror(...)`
- delta math-expression evaluation
- `self.decay_average(...)`
- `sample_delta1` / `sample_delta2` mutation
- Matplotlib line `set_data(...)` calls

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-ror-display-filter.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for smoothing weights, PID input, alarm decisions/readiness, auto-event gates, and RoR display/filter decisions.

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

Ask for an independent review of this Phase 3 RoR display/filter slice before commit, focused on behavior equivalence and plotting side-effect boundaries.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
