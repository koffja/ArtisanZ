# GUI Modernization Phase 3 Auto Event Decisions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting automatic roast-event detection gate decisions from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep `BTbreak()`, `checkTPalarmtime()`, `findTP()`, Qt signal emission, and event-index mutation in `canvas.py`. Move only deterministic gate checks for CHARGE, DROP, DRY, FCs, TP timeout fallback, TP check eligibility, and TP temperature validity into `src/artisanlib/sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add pure auto-event helpers for CHARGE, DROP, TP timeout fallback, TP check gate, TP temperature validity, DRY, and FCs.
- Modify: `src/artisanlib/canvas.py`
  - Replace inline auto-event gate conditions with helper calls while preserving all event side effects.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover Celsius/Fahrenheit thresholds, index gates, elapsed-time gates, TP truthiness, and boundary rejection cases.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record the Phase 3 auto-event decision extraction.

## Task 1: Extract Auto Event Gate Decisions

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- auto CHARGE requires enabled flags, no existing CHARGE index, at least 5 samples, and BT above the C/F threshold
- TP timeout fallback returns the current sample index only after CHARGE and after the configured max roast time
- TP check gate requires no TP alarm index, CHARGE, no DRY index, and enough BT samples
- TP candidate temperature validity matches the existing C/F ranges
- auto DROP requires enabled flags, CHARGE, no DROP index, at least 5 samples, BT above C/F threshold, and more than 7 minutes since CHARGE
- auto DRY requires enabled flags, truthy TP alarm index, CHARGE, no DRY/FCs, and BT at/above phase threshold
- auto FCs requires enabled flags, truthy TP alarm index, CHARGE, no FCs/FCe, and BT at/above phase threshold

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the auto-event helpers are not exported yet.

- [x] **Step 3: Implement helpers**

Add pure helpers to `sample_processing.py`:

- `auto_charge_event_candidate(...) -> bool`
- `turning_point_timeout_index(...) -> int | None`
- `turning_point_check_candidate(...) -> bool`
- `turning_point_temperature_is_valid(...) -> bool`
- `auto_drop_event_candidate(...) -> bool`
- `auto_dry_event_candidate(...) -> bool`
- `auto_fcs_event_candidate(...) -> bool`

- [x] **Step 4: Integrate `canvas.py`**

Use the helpers inside the existing `local_flagstart` block while preserving:

- `self.aw.BTbreak(...)`
- `self.checkTPalarmtime()`
- `self.aw.findTP()`
- `self.autoChargeIdx`, `self.autoDropIdx`, `self.TPalarmtimeindex` mutation
- `markChargeSignal`, `markTPSignal`, `markDropSignal`, `markDRYSignal`, and `markFCsSignal` emission
- current `if`/`elif` relationship among CHARGE, TP timeout fallback, and TP check

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-30-gui-modernization-phase-3-auto-event-decisions.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for smoothing weights, PID input, alarm decisions/readiness, and auto-event detection gates.

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

Ask for an independent review of this Phase 3 auto-event slice before commit, focused on behavior equivalence, event thresholds, and side-effect boundaries.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
