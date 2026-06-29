# GUI Modernization Phase 3 Alarm Trigger Evaluator Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation and superpowers:requesting-code-review before commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue Phase 3 by moving the deterministic alarm trigger loop out of `tgraphcanvas.sample_processing()` and into a pure evaluator.

**Architecture:** Keep `canvas.py` responsible for semaphore ownership, `self.alarmstate` mutation, alarm payload lookup, and `processAlarmSignal.emit(...)`. Move the data-only trigger decision into `sample_processing.py`, including guard checks, negative guards, offsets, source value lookup, relative IF alarms, and per-round state updates that make earlier alarm triggers visible to later alarms.

**Tech Stack:** Pure Python dataclass, pytest, py_compile, ruff.

---

## Files

- Modify: `src/artisanlib/sample_processing.py`
  - Add `AlarmTrigger`.
  - Add `evaluate_alarm_triggers(...)`.
- Modify: `src/artisanlib/canvas.py`
  - Replace the inline alarm readiness loop with `evaluate_alarm_triggers(...)`.
  - Preserve queued signal delivery and canvas-owned state writes.
- Modify: `src/test/unitary/artisanlib/test_sample_processing.py`
  - Cover sequential guard state updates inside one evaluation pass.
  - Cover temperature and extra-device alarm source triggers.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 3 alarm trigger evaluator progress.

## Task 1: Extract Alarm Trigger Decisions

- [x] **Step 1: Write failing tests**

Add tests that require `evaluate_alarm_triggers(...)` to:

- return alarm indices and non-negative state indices for triggered alarms
- preserve input `alarm_states`
- update a local state copy after a trigger so a later IF Alarm guard can see the earlier trigger in the same pass
- trigger from direct BT and extra-device temperature sources

- [x] **Step 2: Implement evaluator**

Add immutable `AlarmTrigger` and a pure evaluator that composes the previously extracted alarm helper functions.

- [x] **Step 3: Integrate `canvas.py`**

Use the evaluator inside the existing alarm semaphore block. Keep `self.alarmstate[i] = ...`, `alarm_beep`, `alarm_action`, `alarm_string`, and `processAlarmSignal.emit(...)` in `canvas.py`.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/sample_processing.py artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py
```

Result: focused verification passed on 2026-06-30 before review and again after review fixes:

- `test/unitary/artisanlib/test_sample_processing.py`: `73 passed`
- `py_compile artisanlib/sample_processing.py artisanlib/canvas.py`: passed
- `ruff check artisanlib/sample_processing.py artisanlib/canvas.py test/unitary/artisanlib/test_sample_processing.py`: passed

- [x] **Step 2: Run broader regression group**

Run the plotting/theme/sample regression group used by prior Phase 3 slices.

Result: `98 passed, 2 warnings` on 2026-06-30 after review fixes. Warnings are existing Yoctopuce Python 3.14 deprecation warnings.

- [x] **Step 3: Request code review**

Ask for an independent review focused on alarm behavior equivalence, guard ordering, IF Alarm relative readings, queued signal semantics, and future threading suitability.

Result: review found no critical issues, one important malformed-row behavior issue, and one minor type annotation issue. Fixes applied:

- Added a regression test proving an incomplete later alarm row does not discard an earlier trigger.
- Added a same-pass negative-guard regression test.
- Changed `alarm_flags` typing to `Sequence[int | bool]` and used persisted-style `0`/`1` flags in new evaluator tests.
- Made the evaluator skip incomplete alarm rows while keeping already-found triggers.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
