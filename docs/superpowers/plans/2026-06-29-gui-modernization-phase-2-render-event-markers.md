# GUI Modernization Phase 2 Matplotlib Event Marker Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Matplotlib snapshot adapter render `EventMarkerSnapshot` data so the renderer boundary carries visible event markers end to end.

**Architecture:** Extend `MatplotlibSnapshotRenderer` with event artist management while keeping it duck-typed and independent from Qt imports. Events render as vertical guide lines plus labels when the target axis supports `axvline()` and `annotate()`, and old event artists are removed on snapshot replacement. The live `canvas.py` runtime path remains untouched.

**Tech Stack:** Python duck typing, pytest fake axes/artists, Matplotlib Agg smoke test, ruff, py_compile.

---

## Files

- Modify: `src/artisanlib/plot_matplotlib_adapter.py`
  - Add event artist creation/removal and a `event_artist_count()` inspection helper.
- Modify: `src/test/unitary/artisanlib/test_plot_matplotlib_adapter.py`
  - Cover fake-axis event marker rendering and replacement cleanup.
- Modify: `src/artisanlib/plot_matplotlib_smoke.py`
  - Return event artist count from the real Agg diagnostic render.
- Modify: `src/test/unitary/artisanlib/test_plot_matplotlib_smoke.py`
  - Cover real Matplotlib event marker rendering.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 2 event markers are now extracted and renderable through the Matplotlib adapter.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-render-event-markers.md`
  - Track this plan's execution.

## Task 1: Adapter Event Tests

**Files:**
- Modify: `src/test/unitary/artisanlib/test_plot_matplotlib_adapter.py`

- [x] **Step 1: Write failing fake-axis tests**

Add fake axis support for:

```python
axvline(time, color=..., linestyle=..., linewidth=..., alpha=...)
annotate(label, xy=(time, top), xytext=(time, top), color=...)
```

Add a test that creates a snapshot with one `EventMarkerSnapshot` and asserts:

- `set_snapshot()` creates one vertical line and one annotation.
- The vertical line uses the event time/color.
- `event_artist_count()` returns `2`.
- A later snapshot with no events removes both old event artists.

- [x] **Step 2: Run tests to verify they fail**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_adapter.py -q
```

Expected: FAIL because `MatplotlibSnapshotRenderer` does not render event markers yet.

## Task 2: Adapter Event Implementation

**Files:**
- Modify: `src/artisanlib/plot_matplotlib_adapter.py`

- [x] **Step 1: Implement event artist management**

Implement:

- `_event_artists: list[object]`
- `event_artist_count() -> int`
- `_apply_events(snapshot)`
- `_clear_event_artists()`
- `_create_event_artists(event, snapshot)`

Rules:

- `set_snapshot()` and `update_live_frame()` call `_apply_events(snapshot)`.
- Existing event artists are removed before adding the new snapshot's event artists.
- Use `temperature_axis.axvline()` when present.
- Use `temperature_axis.annotate()` when present.
- Label y-position uses `snapshot.temperature_axis.maximum`.
- Store both returned artist objects.
- Artist removal uses `remove()` when available.

- [x] **Step 2: Run tests to verify they pass**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_adapter.py -q
.venv/bin/python -m py_compile artisanlib/plot_matplotlib_adapter.py
.venv/bin/python -m ruff check artisanlib/plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py
```

Expected: PASS.

## Task 3: Offscreen Smoke Event Coverage

**Files:**
- Modify: `src/artisanlib/plot_matplotlib_smoke.py`
- Modify: `src/test/unitary/artisanlib/test_plot_matplotlib_smoke.py`

- [x] **Step 1: Write failing smoke assertion**

Update the smoke test snapshot with an `EventMarkerSnapshot` and assert `result.event_artist_count == 2`.

- [x] **Step 2: Update smoke result**

Add `event_artist_count: int` to `MatplotlibSmokeRenderResult` and return `renderer.event_artist_count()`.

- [x] **Step 3: Run smoke verification**

Run:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_smoke.py -q
.venv/bin/python -m py_compile artisanlib/plot_matplotlib_smoke.py
.venv/bin/python -m ruff check artisanlib/plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py
```

Expected: PASS.

## Task 4: Roadmap Update and Commit

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-render-event-markers.md`

- [x] **Step 1: Update roadmap status**

Record that event markers are now extracted into snapshots and renderable through the Matplotlib adapter/offscreen smoke path.

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
git add src/artisanlib/plot_matplotlib_adapter.py src/test/unitary/artisanlib/test_plot_matplotlib_adapter.py src/artisanlib/plot_matplotlib_smoke.py src/test/unitary/artisanlib/test_plot_matplotlib_smoke.py docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-phase-2-render-event-markers.md
git commit -m "feat(gui): render snapshot event markers"
```

## Next Slice After This Plan

After this plan is complete, extract phase-band snapshot data or add a PyQtGraph POC that consumes curves plus event markers.

## Self-Review

- Spec coverage: This plan closes the event-marker loop from extractor to Matplotlib rendering and smoke verification.
- Placeholder scan: No placeholder markers are present.
- Type consistency: `EventMarkerSnapshot`, `MatplotlibSnapshotRenderer`, `event_artist_count()`, and `MatplotlibSmokeRenderResult` names are consistent across tests and implementation.
