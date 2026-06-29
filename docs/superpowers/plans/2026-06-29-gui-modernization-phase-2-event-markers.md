# GUI Modernization Phase 2 Event Marker Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the plot snapshot boundary so foreground roast events can be carried as renderer-neutral `EventMarkerSnapshot` data.

**Architecture:** Add event extraction to `plot_snapshot_extractor.py` without importing Qt or Matplotlib and without changing `canvas.py`. The extractor reads canvas-like event arrays, skips malformed/out-of-range event entries, and stores marker time, label, event type, color, and value in the existing `RoastPlotSnapshot.events` field.

**Tech Stack:** Python dataclasses, pytest fake canvas, ruff, py_compile.

---

## Files

- Modify: `src/artisanlib/plot_snapshot_extractor.py`
  - Add event marker extraction from `specialevents`, `specialeventstype`, `specialeventsvalue`, `specialeventsStrings`, `etypes`, `showEtypes`, `EvalueColor`, and `palette`.
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`
  - Cover event extraction, label fallback, color selection, visibility filtering, and invalid index skipping.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 2 event marker snapshot coverage.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-event-markers.md`
  - Track this plan's execution.

## Task 1: Event Marker Tests

**Files:**
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`

- [x] **Step 1: Write failing tests**

Add assertions that a fake canvas with:

```python
specialevents = [1, 2, 99]
specialeventstype = [1, 2, 0]
specialeventsvalue = [55.0, 25.0, 10.0]
specialeventsStrings = ['power up', '', 'ignored']
etypes = ['None', 'Power', 'Fan', 'Damper']
showEtypes = [True, True, True, True]
EvalueColor = ['#111111', '#222222', '#333333', '#444444']
```

produces two `EventMarkerSnapshot` entries at `timex[1]` and `timex[2]`, with label fallback from `etypes` for the empty event string and invalid index `99` skipped.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py -q
```

Expected: FAIL because `build_roast_plot_snapshot()` currently returns no events.

## Task 2: Event Marker Extraction

**Files:**
- Modify: `src/artisanlib/plot_snapshot_extractor.py`

- [x] **Step 1: Implement minimal extractor support**

Add `_event_markers(source)` and pass its result to `RoastPlotSnapshot(events=...)`.

Extraction rules:

- Use `specialevents` as integer indices into `timex`.
- Skip events whose indices are outside `timex`.
- Use `specialeventstype` as `event_type`.
- Use `specialeventsvalue` as `value`, converted to `float` when present.
- Use `specialeventsStrings[i]` as `label` when non-empty after stripping.
- Use `etypes[event_type]` as fallback label when available.
- Use `Event {event_type}` as final fallback label.
- Use `EvalueColor[event_type]` as marker color when available.
- Use `palette['specialeventtext']` or `#ffffff` as color fallback.
- Respect `showEtypes[event_type]` when present.

- [x] **Step 2: Run tests to verify they pass**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot_extractor.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_snapshot_extractor.py
```

Expected: PASS.

## Task 3: Roadmap Update and Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-event-markers.md`

- [x] **Step 1: Update roadmap status**

Record that Phase 2 now carries foreground event markers in `RoastPlotSnapshot.events`, still without touching live `canvas.py`.

- [x] **Step 2: Run focused verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py::TestMakeLCDbox -q
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py artisanlib/gui_theme.py artisanlib/main.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py artisanlib/gui_theme.py artisanlib/main.py test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py
```

Expected: PASS.

- [x] **Step 3: Commit**

Run:

```bash
git add src/artisanlib/plot_snapshot_extractor.py src/test/unitary/artisanlib/test_plot_snapshot_extractor.py docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-event-markers.md
git commit -m "feat(gui): add event markers to plot snapshots"
```

## Next Slice After This Plan

After this plan is complete, add basic Matplotlib adapter rendering for `EventMarkerSnapshot` or extract phase-band snapshot data before starting the PyQtGraph POC.

## Self-Review

- Spec coverage: This plan adds renderer-neutral event marker coverage and keeps live plotting untouched.
- Placeholder scan: No placeholder markers are present.
- Type consistency: `EventMarkerSnapshot`, `RoastPlotSnapshot.events`, and `build_roast_plot_snapshot()` names match the existing snapshot contract.
