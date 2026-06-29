# GUI Modernization Phase 3 Alarm Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting alarm eligibility and offset-time decisions from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep alarm semaphore handling, state mutation, Qt signal emission, logging, and action execution in `canvas.py`. Move only the deterministic checks that decide whether an alarm is eligible for temperature/time evaluation and whether an alarm offset has elapsed.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `alarm_is_eligible_for_evaluation()` and `alarm_time_offset_reached()`.
- Modify: `src/artisanlib/canvas.py`
  - Replace the inline alarm guard/from-event eligibility branch and offset-time branch with helper calls.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover alarm active state, guard/negative-guard behavior, alarm-from timing gates, and offset calculations.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record the Phase 3 alarm readiness extraction.

## Task 1: Extract Alarm Readiness Decisions

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- inactive alarms and already-triggered alarms are not eligible
- positive guards require the guarded alarm to have fired
- negative guards require the guarded alarm to remain unfired
- ON alarms are eligible before recording
- START alarms require recording
- CHARGE/event alarms require their time indexes
- TP alarms require recording, CHARGE, and a TP alarm index
- IF ALARM requires an alarm guard
- alarm offsets are measured against START, CHARGE, TP, other event indexes, IF ALARM guard indexes, and ON/no-event elapsed time

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the alarm readiness helpers are not exported yet.

- [x] **Step 3: Implement helpers**

Add pure helpers to `sample_processing.py`:

- `alarm_is_eligible_for_evaluation(...) -> bool`
- `alarm_time_offset_reached(...) -> bool`

These helpers should preserve the existing `sample_processing()` branch semantics, including TP truthiness and IF ALARM offset indexing.

- [x] **Step 4: Integrate `canvas.py`**

Use the helpers inside the alarm loop while preserving:

- `alarm_ready` mutation
- alarm temperature/value helper calls
- `self.alarmstate` updates
- `processAlarmSignal.emit(...)`
- semaphore acquire/release
- broad exception logging behavior around the alarm loop

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-3-alarm-readiness.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for smoothing weights, PID input, alarm source/limit, and alarm readiness/offset decisions.

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

Ask for an independent review of this Phase 3 alarm readiness slice before commit, focused on behavior equivalence and alarm timing edge cases.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
