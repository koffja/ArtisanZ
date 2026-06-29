# GUI Modernization Phase 3 Alarm Source Value Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by extracting alarm source-value and limit-condition decisions from `tgraphcanvas.sample_processing()` into tested pure helpers.

**Architecture:** Keep alarm semaphore handling, alarm state mutation, signal emission, logging, and action execution in `canvas.py`. Move only the deterministic data selection and comparison logic into `src/artisanlib/sample_processing.py`.

**Tech Stack:** Pure Python helper, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `relative_alarm_index()`, `alarm_source_value()`, and `alarm_temperature_reaches_limit()`.
- Modify: `src/artisanlib/canvas.py`
  - Replace the inline alarm temperature source branch and threshold condition with helper calls.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover IF ALARM relative index handling, ET/BT/RoR/extra source values, missing-source fallback, and threshold conditions.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record the Phase 3 alarm decision extraction.

## Task 1: Extract Alarm Source Value

**Files:**
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
- Modify: `src/artisanlib/sample_processing.py`
- Modify: `src/artisanlib/canvas.py`

- [x] **Step 1: Write failing pure-function tests**

Add tests for:

- non-IF alarms have no relative alarm index
- IF alarms use their triggering sample index
- IF alarms beyond the sample window preserve the existing `-1` fallback
- DeltaET and DeltaBT source values
- ET and BT source values
- extra-device channel 1 and 2 source values
- missing or empty source returns `None`
- greater-than, less-than, equality, inequality, dropout, and relative equality limit conditions

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
```

Expected: FAIL because the alarm helpers are not exported yet.

- [x] **Step 3: Implement helpers**

Add pure helpers to `sample_processing.py`:

- `relative_alarm_index(alarm_time, if_alarm_state, sample_count)`
- `alarm_source_value(alarm_source, alarm_index, sample_delta1, sample_delta2, sample_temp1, sample_temp2, sample_extratemp1, sample_extratemp2, extra_device_count)`
- `alarm_temperature_reaches_limit(alarm_temp, alarm_cond, alarm_limit, alarm_index)`

- [x] **Step 4: Integrate `canvas.py`**

Use the helpers inside the alarm loop while preserving:

- `alarm_ready` mutation
- `self.alarmstate` updates
- `processAlarmSignal.emit(...)`
- semaphore acquire/release
- broad exception logging behavior around the alarm loop

## Task 2: Roadmap, Review, Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-3-alarm-source-value.md`

- [x] **Step 1: Update roadmap**

Record that Phase 3 now has tested helpers for smoothing-weight selection, PID process-value source selection, and alarm source/condition decisions.

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

Ask for an independent review of this Phase 3 alarm slice before commit, focused on behavior equivalence and alarm edge cases.

- [x] **Step 4: Commit**

Stage only the implementation, tests, and planning documents for this slice. Leave codebase-memory artifacts unstaged unless explicitly requested.
