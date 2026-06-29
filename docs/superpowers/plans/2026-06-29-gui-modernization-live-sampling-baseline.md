# GUI Modernization Live Sampling Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a repeatable offscreen live-sampling benchmark that runs ArtisanZ against its built-in profile simulator and records GUI performance metrics.

**Architecture:** Extend the existing disabled-by-default `ARTISANZ_GUI_PERF_AUTORUN` hook in `src/artisanlib/main.py` with a second mode that uses an explicit profile file as an internal simulator source, triggers the real START/ON code paths, captures a START-state screenshot, stops sampling, exports metrics, and exits. Keep the existing profile-redraw autorun as the default behavior.

**Tech Stack:** PyQt6 `QTimer`, existing ArtisanZ `Simulator`, existing `artisanlib.performance` JSONL exporter, pytest/ruff/py_compile, offscreen Qt.

---

## Files

- Modify: `src/artisanlib/main.py`
  - Add `ARTISANZ_GUI_PERF_AUTORUN_MODE=redraw|simulator-recording`.
  - Add `ARTISANZ_GUI_PERF_AUTORUN_SIMULATOR_FILE` for deterministic internal simulator startup.
  - Factor the existing redraw autorun into a small helper.
  - Add a simulator-recording autorun helper that creates `Simulator`, calls `ToggleRecorder()`, `ToggleMonitor()`, screenshot/export, and `fileQuit()`.
- Modify: `docs/GUI_MODERNIZATION_BASELINE.md`
  - Document the simulator-recording command and append measured results.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Update Phase 0 status once live sampling data is captured.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-live-sampling-baseline.md`
  - Mark task checkboxes as implementation proceeds.

## Task 1: Add Simulator Recording Autorun Mode

**Files:**
- Modify: `src/artisanlib/main.py`

- [x] **Step 1: Refactor `_schedule_gui_perf_autorun()` into mode dispatch**

Add a mode read from `ARTISANZ_GUI_PERF_AUTORUN_MODE`, defaulting to `redraw`.

Expected behavior:

```python
mode = os.environ.get('ARTISANZ_GUI_PERF_AUTORUN_MODE', 'redraw').strip().lower()
if mode in {'simulator', 'simulator-recording', 'recording'}:
    _schedule_gui_perf_simulator_recording_autorun(appWindow)
else:
    _schedule_gui_perf_redraw_autorun(appWindow)
```

- [x] **Step 2: Preserve current redraw behavior**

Move the existing redraw loop into `_schedule_gui_perf_redraw_autorun(appWindow)` without changing its environment variables:

```python
ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=16
ARTISANZ_GUI_PERF_AUTORUN_INTERVAL_MS=50
ARTISANZ_GUI_PERF_AUTORUN_START_MS=1200
```

- [x] **Step 3: Add simulator-recording behavior**

Add `_schedule_gui_perf_simulator_recording_autorun(appWindow)`:

```python
duration_ms = _gui_perf_env_int('ARTISANZ_GUI_PERF_AUTORUN_DURATION_MS', 5000)
start_delay_ms = _gui_perf_env_int('ARTISANZ_GUI_PERF_AUTORUN_START_MS', 1200)
stop_delay_ms = _gui_perf_env_int('ARTISANZ_GUI_PERF_AUTORUN_STOP_MS', 1000)
```

Sequence:

```python
_start_gui_perf_profile_simulator(appWindow)
QTimer.singleShot(250, lambda: appWindow.qmc.ToggleRecorder(False))
QTimer.singleShot(duration_ms, stop_recording)
```

`stop_recording()` must capture the screenshot before stopping so the saved image shows START-state UI:

```python
_save_gui_perf_autorun_screenshot(appWindow)
if appWindow.qmc.flagon:
    appWindow.qmc.ToggleMonitor(False)
QTimer.singleShot(stop_delay_ms, lambda: _finish_gui_perf_autorun(appWindow))
```

- [x] **Step 4: Add shared finish helper**

Add `_finish_gui_perf_autorun(appWindow)` and use it from both autorun modes:

```python
export_gui_perf_metrics()
appWindow.qmc.safesaveflag = False
appWindow.fileQuit()
```

It must catch and log broad exceptions in the same style as the existing autorun code.

## Task 2: Capture Live Sampling Baseline

**Files:**
- Modify: `docs/GUI_MODERNIZATION_BASELINE.md`

- [x] **Step 1: Run simulator-recording autorun**

```bash
cd src
rm -f /tmp/artisanz-gui-perf-live.jsonl /tmp/artisanz-live-sim.png
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_MODE=simulator-recording \
ARTISANZ_GUI_PERF_AUTORUN_DURATION_MS=20000 \
ARTISANZ_GUI_PERF_AUTORUN_SIMULATOR_FILE=test/sanity/data/artisan/profile1.alog \
ARTISANZ_GUI_PERF_AUTORUN_STATUS_FILE=/tmp/artisanz-live-status.txt \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-gui-perf-live.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-live-sim.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
```

- [x] **Step 2: Summarize metrics**

```bash
cd src
.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-gui-perf-live.jsonl --sort-by max_ms --limit 20
file /tmp/artisanz-live-sim.png
```

- [x] **Step 3: Update the baseline document**

Append a row to `docs/GUI_MODERNIZATION_BASELINE.md` with `canvas.sample_processing`, `canvas.updategraphics`, `canvas.updateBackground`, `canvas.redraw`, skip counters if present, and screenshot path.

Recorded 2026-06-29 result:

- Status log confirmed `flagon=True flagstart=True` before screenshot capture.
- Screenshot: `/tmp/artisanz-live-sim.png`.
- Metrics: `redraw max=191.663ms avg=120.704ms`; `updateBackground max=117.205ms avg=52.165ms`; `updategraphics max=47.248ms avg=5.580ms`; `sample_processing max=2.015ms avg=1.103ms`; `updateBackground.skip count=1`.

## Task 3: Verify and Commit

**Files:**
- Modify: `src/artisanlib/main.py`
- Modify: `docs/GUI_MODERNIZATION_BASELINE.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-live-sampling-baseline.md`

- [x] **Step 1: Run focused verification**

```bash
cd src
.venv/bin/python -m py_compile artisanlib/main.py artisanlib/performance.py artisanlib/performance_report.py
.venv/bin/python -m pytest test/unitary/artisanlib/test_performance.py test/unitary/artisanlib/test_performance_report.py -q
.venv/bin/python -m ruff check artisanlib/main.py artisanlib/performance.py artisanlib/performance_report.py test/unitary/artisanlib/test_performance.py test/unitary/artisanlib/test_performance_report.py
```

- [x] **Step 2: Commit**

```bash
git add src/artisanlib/main.py docs/GUI_MODERNIZATION_BASELINE.md docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-06-29-gui-modernization-live-sampling-baseline.md
git commit -m "perf(gui): add live sampling autorun baseline"
```

## Self-Review

- Spec coverage: The plan adds repeatable live sampling metrics before Phase 2/3, updates baseline evidence, and preserves the existing redraw autorun default.
- Placeholder scan: No TBD/TODO placeholders remain.
- Type consistency: Helper names use existing `ApplicationWindow`, `QTimer`, `export_gui_perf_metrics()`, and `_save_gui_perf_autorun_screenshot()` APIs.
