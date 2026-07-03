# GUI Modernization Baseline

**Status:** Automated profile redraw baseline, 20-second internal simulator live-sampling smoke baselines, a 60-second internal simulator live-sampling baseline, and guarded PyQtGraph offscreen/real-window simulator baselines are captured; real-device baselines remain pending.

## Purpose

This document records the performance evidence used to guide ArtisanZ GUI modernization. Update it whenever instrumentation is run against a representative profile, simulator session, or device session.

## Python Environment

Use the project virtual environment from `src/.venv`. On this machine, the system `python3` is Python 3.9 and cannot parse current ArtisanZ source syntax.

From the repository root:

```bash
cd src
.venv/bin/python --version
```

Expected Python version: 3.12 or newer.

## How To Enable Probes

From the repository root:

```bash
cd src
ARTISANZ_GUI_PERF=1 .venv/bin/python artisan.py
```

The probes are disabled unless `ARTISANZ_GUI_PERF` is set to `1`, `true`, `yes`, or `on`.
When probes are enabled, ArtisanZ writes metrics to the default operating-system temp path on exit, even if `ARTISANZ_GUI_PERF_FILE` is not set.

## Optional JSONL Export

To choose the output path explicitly:

```bash
cd src
ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-gui-perf.jsonl .venv/bin/python artisan.py
```

## Summarize JSONL Metrics

After Artisan exits and writes the default JSONL file:

```bash
cd src
.venv/bin/python -m artisanlib.performance_report --sort-by max_ms --limit 10
```

If `ARTISANZ_GUI_PERF_FILE` was set explicitly:

```bash
cd src
.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-gui-perf.jsonl --sort-by max_ms --limit 10
```

Useful sort keys are `max_ms`, `avg_ms`, `total_ms`, and `count`.

## Hot Paths

- `canvas.sample_processing`: GUI-thread post-processing after samples are read.
- `canvas.updategraphics`: GUI-thread live LCD and Matplotlib blit/update path.
- `canvas.updateBackground`: full background draw and Matplotlib background cache refresh.
- `canvas.redraw`: full graph redraw path.
- `canvas.redraw_keep_view`: redraw path preserving current graph view.

## Baseline Scenario

Run each scenario for at least five minutes where possible:

1. OFF -> ON monitoring with simulator or a safe test device.
2. OFF -> START recording with ET, BT, Delta ET, and Delta BT visible.
3. START recording with a background profile loaded.
4. START recording with extra event buttons visible.
5. Load a representative historical profile and trigger a full redraw.

## Automated Profile Redraw Scenario

For repeatable local confirmation:

```bash
cd src
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=16 \
ARTISANZ_GUI_PERF_AUTORUN_INTERVAL_MS=50 \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-gui-perf.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-phase1.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog

.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-gui-perf.jsonl --sort-by max_ms --limit 20
```

## Automated Simulator Recording Scenario

For a repeatable short live-sampling smoke baseline that exercises START recording through the built-in profile simulator:

```bash
cd src
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

.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-gui-perf-live.jsonl --sort-by max_ms --limit 20
```

## WebSocket Virtual Roast Renderer Scenario

For deterministic WebSocket-driven renderer validation without a physical machine:

```bash
cd src
QT_QPA_PLATFORM=offscreen \
.venv/bin/python -m artisanlib.websocket_renderer_smoke --samples 24 --fixed-step-ms 15000
```

This starts the in-process `dev_simulator` WebSocket server, requests Artisan-compatible `getData` samples, converts the stream into `RoastPlotSnapshot` frames, and feeds the PyQtGraph renderer. It validates live BT/ET/RoR curves plus event labels, event value rails, phase bands, and AUC/BBP/charge-target guide overlays.

## WebSocket Main-Window Recording Scenario

For deterministic WebSocket validation through the real Artisan main window and sampling path:

```bash
cd src
QT_QPA_PLATFORM=offscreen \
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_MODE=websocket-recording \
ARTISANZ_GUI_PERF_AUTORUN_DURATION_MS=16000 \
ARTISANZ_GUI_PERF_AUTORUN_SAMPLE_DELAY_MS=500 \
ARTISANZ_GUI_PERF_AUTORUN_WEBSOCKET_FIXED_STEP_MS=30000 \
ARTISANZ_GUI_PERF_AUTORUN_STATUS_FILE=/tmp/artisanz-ws-main-status.txt \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-ws-main-perf.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-ws-main.png \
.venv/bin/python artisan.py

.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-ws-main-perf.jsonl
```

This starts a threaded in-process `dev_simulator` WebSocket server, temporarily configures the main WebSocket device (`qmc.device == 111`) in memory, records through the normal `ToggleRecorder()` path, captures screenshot/status/performance output, and restores the original WebSocket/device settings before quitting.

## Results Template

| Date | Branch | Scenario | Sampling Interval | Visible Curves | Key Metrics | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-29 | ArtisanZ | Not yet run | Not recorded | Not recorded | Not recorded | Instrumentation implemented and verified; capture hardened before real GUI baseline |
| 2026-06-29 | ArtisanZ | First manual run follow-up | Not recorded | Not recorded | No metrics file found | Default path and `ARTISANZ_GUI_PERF_FILE` search found no ArtisanZ JSONL; capture flow hardened with default temp export and `atexit` fallback |
| 2026-06-29 | ArtisanZ | Automated profile redraw baseline | N/A | Historical profile `profile1.alog` | `redraw max=106.627ms avg=75.284ms`; `redraw_keep_view max=103.192ms avg=73.427ms`; `updateBackground max=85.556ms avg=57.277ms`; `updategraphics max=0.006ms avg=0.002ms` | Baseline before Phase 1 stylesheet |
| 2026-06-29 | ArtisanZ | Automated profile redraw after Phase 1 stylesheet | N/A | Historical profile `profile1.alog` | `redraw max=110.339ms avg=76.577ms`; `redraw_keep_view max=108.581ms avg=74.567ms`; `updateBackground max=80.033ms avg=56.631ms`; `updategraphics max=0.005ms avg=0.002ms` | Visual stylesheet did not materially worsen measured redraw path |
| 2026-06-29 | ArtisanZ | Automated profile redraw after event/LCD styling | N/A | Historical profile `profile1.alog` | `redraw max=138.665ms avg=84.735ms`; `redraw_keep_view max=127.508ms avg=81.386ms`; `updateBackground max=156.639ms avg=65.746ms`; `updategraphics max=0.007ms avg=0.002ms` | Screenshot: `/tmp/artisanz-phase1.png`; event buttons flattened; LCD surfaces styled; one higher `updateBackground` max observed in offscreen run, but live update path stayed negligible |
| 2026-06-29 | ArtisanZ | Automated OFF screenshot smoke after event/LCD styling | N/A | Empty main graph | `redraw max=95.335ms avg=81.990ms`; `redraw_keep_view max=76.211ms avg=73.894ms`; `updateBackground max=83.124ms avg=55.925ms`; `updategraphics max=0.006ms avg=0.002ms` | Screenshot: `/tmp/artisanz-phase1-off.png`; no obvious overlap or text clipping in 800x533 offscreen capture |
| 2026-06-29 | ArtisanZ | Automated simulator recording live-sampling smoke | 20s | START recording through internal simulator from `profile1.alog` | `redraw max=191.663ms avg=120.704ms`; `updateBackground max=117.205ms avg=52.165ms`; `updategraphics max=47.248ms avg=5.580ms`; `sample_processing max=2.015ms avg=1.103ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-live-sim.png`; status log confirms `flagon=True flagstart=True` before capture; short smoke baseline, not a replacement for 5-minute simulator/device runs |
| 2026-06-30 | ArtisanZ | Automated simulator recording after Phase 3 processed-frame contract | 20s | START recording through internal simulator from `profile1.alog` | `redraw max=136.098ms avg=98.929ms`; `updateBackground max=84.649ms avg=39.025ms`; `updategraphics max=40.563ms avg=3.957ms`; `sample_processing max=0.574ms avg=0.500ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-phase3-frame.png`; status log confirms `flagon=True flagstart=True`; `sample_processing` measured lower in one comparable short smoke, but longer simulator/device runs are needed before treating this as a causal performance win |
| 2026-06-30 | ArtisanZ | Automated simulator recording after Phase 3 PID/manual/extra diagnostics slices | 20s | START recording through internal simulator from `profile1.alog` | `redraw max=130.766ms avg=105.468ms`; `updateBackground max=90.709ms avg=43.554ms`; `updategraphics max=47.004ms avg=5.077ms`; `sample_processing max=1.799ms avg=0.975ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-phase3-latest-live-sim.png`; status log confirms `flagon=True flagstart=True`; still slightly below the original 20s `sample_processing` smoke, but above the processed-frame run, so short offscreen runs remain too noisy for causal claims |
| 2026-06-30 | ArtisanZ | Automated simulator recording after Phase 3 curve data payload slices | 20s | START recording through internal simulator from `profile1.alog` | `redraw max=109.547ms avg=85.564ms`; `updateBackground max=67.517ms avg=33.163ms`; `updategraphics max=36.701ms avg=4.254ms`; `sample_processing max=1.755ms avg=1.118ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-phase3-full-curve-live-sim.png`; status log confirms `flagon=True flagstart=True`; LCD value surfaces remained visually aligned in the smoke screenshot; `sample_processing` is comparable to the original short smoke and still smaller than live update/redraw paths |
| 2026-06-30 | ArtisanZ | Automated simulator recording after Phase 3 input-filter extraction | 20s | START recording through internal simulator from `profile1.alog` | `redraw max=115.892ms avg=78.940ms`; `updateBackground max=75.626ms avg=34.997ms`; `updategraphics max=34.669ms avg=3.608ms`; `sample_processing max=1.402ms avg=0.594ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-phase3-input-filter-live-sim.png`; status log confirms `flagon=True flagstart=True`; LCD value surfaces remained visually aligned; `sample_processing` measured below the original smoke in this short run, but longer simulator/device runs are still required for causal claims |
| 2026-06-30 | ArtisanZ | Renderer adapter benchmark after OpenGL capability probe | N/A | Synthetic `900` point, `6` curve, `8` event snapshot; `5` iterations | OpenGL requested: Matplotlib avg `0.010817674966529012s`, PyQtGraph avg `0.0025607582181692125s`, `opengl_widget_supported=false`; no OpenGL: Matplotlib avg `0.010901808366179466s`, PyQtGraph avg `0.0026710582431405784s`, `opengl_widget_supported=null` | PyQtGraph adapter remains about 4x faster in the offscreen adapter benchmark, but the platform cannot create a valid `QOpenGLWidget`; current evidence supports a PyQtGraph live-renderer POC, not an OpenGL-specific claim |
| 2026-07-01 | ArtisanZ | Automated simulator recording after workspace status dock restoration fix | 60s | START recording through internal simulator from `profile1.alog` | `redraw max=145.282ms avg=93.455ms`; `updateBackground max=82.276ms avg=39.768ms`; `updategraphics max=37.662ms avg=2.693ms`; `sample_processing max=1.530ms avg=0.702ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-phase0-60s-after-dock-fix-live-sim.png`; status log confirms `flagon=True flagstart=True`; first 60s screenshot exposed a restored blank Workspace Status dock, fixed before this re-run; live processing remains smaller than update/redraw paths |
| 2026-07-02 | ArtisanZ | Automated profile redraw visual QA after guarded PyQtGraph embed | N/A | Historical profile `profile1.alog`, default Matplotlib renderer | `redraw max=236.974ms avg=152.126ms`; `redraw_keep_view max=171.558ms avg=139.569ms`; `updateBackground max=128.589ms avg=83.509ms`; `updategraphics max=0.007ms avg=0.002ms` | Screenshot: `/tmp/artisanz-phase1-qa-default-profile-abs.png`; current main screen, LCD spacing/value surfaces, workspace dock, and renderer status inspected in offscreen capture |
| 2026-07-02 | ArtisanZ | Guarded PyQtGraph offscreen simulator recording after review fixes | 20s | START recording through internal simulator from `profile1.alog`; `ARTISANZ_RENDERER_ID=pyqtgraph-snapshot` | `redraw max=155.610ms avg=100.076ms`; `updateBackground max=110.425ms avg=51.544ms`; `updategraphics max=41.895ms avg=3.903ms`; `sample_processing max=4.912ms avg=2.389ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-pyqtgraph-live-final.png`; status log confirms `flagon=True flagstart=True`; software PyQtGraph target is nonblank and visually aligned with the light Widgets theme; hidden Matplotlib lines remain synchronized for export compatibility |
| 2026-07-02 | ArtisanZ | Guarded PyQtGraph real-window simulator recording after review fixes | 12s | START recording through internal simulator from `profile1.alog`; `ARTISANZ_RENDERER_ID=pyqtgraph-snapshot` | `redraw max=118.040ms avg=81.885ms`; `updateBackground max=80.907ms avg=38.028ms`; `updategraphics max=37.760ms avg=4.839ms`; `sample_processing max=7.377ms avg=2.897ms`; `updateBackground.skip count=1` | Screenshot: `/tmp/artisanz-pyqtgraph-realwindow-final.png`; status log confirms `flagon=True flagstart=True`; native macOS window capture verifies the guarded widget path outside `QT_QPA_PLATFORM=offscreen`; real-device hardware capture is still unavailable |
| 2026-07-02 | ArtisanZ | Phase 1.5 default PyQtGraph profile redraw | N/A | Historical profile `profile1.alog`, default renderer with no `ARTISANZ_RENDERER_ID` override | `redraw max=202.388ms avg=152.376ms`; `redraw_keep_view max=176.383ms avg=147.030ms`; `updateBackground max=95.783ms avg=57.432ms`; `updategraphics max=0.011ms avg=0.003ms` | Screenshot: `/tmp/artisanz-phase15-default-pyqtgraph.png`; Workspace Status reports `Renderer: PyQtGraph Snapshot - Selected`; right LCD telemetry column remains visible; historical profile snapshot is nonblank |
| 2026-07-02 | ArtisanZ | Phase 1.5 Matplotlib override profile redraw | N/A | Historical profile `profile1.alog`, `ARTISANZ_RENDERER_ID=matplotlib-snapshot` | `redraw max=197.679ms avg=147.718ms`; `redraw_keep_view max=175.239ms avg=138.826ms`; `updateBackground max=115.753ms avg=80.708ms`; `updategraphics max=0.005ms avg=0.002ms` | Screenshot: `/tmp/artisanz-phase15-matplotlib-override.png`; Workspace Status reports `Renderer: Matplotlib Snapshot - Selected`; compatibility path remains available |
| 2026-07-02 | ArtisanZ | Phase 1.5 PyQtGraph axis/LCD follow-up profile redraw | N/A | Historical profile `profile1.alog`, default PyQtGraph renderer | `redraw max=215.606ms avg=178.485ms`; `redraw_keep_view max=200.670ms avg=169.374ms`; `updateBackground max=137.921ms avg=81.471ms`; `updategraphics max=0.008ms avg=0.003ms` | Screenshot: `/tmp/artisanz-pyqtgraph-axis-fixes.png`; PyQtGraph renders RoR on the same plot with a right axis, default time labels are minute-style, LCD cards stay fixed-width with wrapped labels, and no PyQtGraph AxisItem errors were logged after the tick-spacing fix |
| 2026-07-02 | ArtisanZ | Phase 1.6 PyQtGraph grid/phase visual follow-up | N/A | Historical profile redraw plus explicit PyQtGraph grid/phase target screenshot | `redraw max=87.658ms avg=53.171ms`; `redraw_keep_view max=50.516ms avg=48.676ms`; `updateBackground max=30.605ms avg=24.606ms`; `updategraphics max=0.006ms avg=0.003ms` | Main-window screenshot: `/tmp/artisanz-phase16-grid-phase-v2.png`; explicit grid/phase screenshot: `/tmp/artisanz-phase16-grid-unit.png`; PyQtGraph grid now uses a dedicated overlay and default phase bands use visible Morandi colors. The profile redraw run used settings with x/y grid disabled, so the explicit target screenshot verifies grid rendering with grid enabled. |
| 2026-07-02 | ArtisanZ | Phase 1.7 WebSocket virtual roast PyQtGraph validation | 24 WebSocket `getData` samples, fixed 15s virtual step | In-process `dev_simulator` WebSocket stream with BT/ET/RoR, 6 push events, 2 event values, 3 guide overlays | `avg_update_ms=1.1859`; `max_update_ms=4.7771`; `data_message_count=24`; `push_message_count=6`; `event_count=6`; `event_value_count=2`; `guide_count=3`; `full_snapshot_count=6`; `live_update_count=18` | Command: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke --samples 24 --fixed-step-ms 15000`; validates the default PyQtGraph renderer with real WebSocket protocol traffic instead of only static profile snapshots. |
| 2026-07-02 | ArtisanZ | Phase 1.8 WebSocket main-window recording autorun | 500ms wall-clock sample delay, fixed 30s virtual WebSocket step | Full Artisan main window, real WebSocket device path, default PyQtGraph renderer, virtual CHARGE/DRY/FCs/FCe/SCs/DROP traffic | `redraw max=100.403ms avg=65.904ms`; `updateBackground max=71.821ms avg=27.362ms`; `updategraphics max=17.878ms avg=6.110ms`; `sample_processing max=4.160ms avg=1.601ms`; `samples=30`; `timeindex=[1, 10, 19, 22, 26, 0, 26, 0]` | Screenshot: `/tmp/artisanz-ws-main.png`; status log confirms endpoint setup, active recording, restored state, and finish. Accelerated virtual time covers roast events quickly while the visible main timer remains wall-clock time, so this proves plumbing/renderer behavior but not physical-device timing. |
| 2026-07-03 | ArtisanZ | Phase 1.19 PyQtGraph grid/phase live parity validation | 90 WebSocket `getData` samples, fixed 1s virtual step | In-process `dev_simulator` WebSocket stream through PyQtGraph snapshot renderer with live updates and static overlay merging | `avg_update_ms=1.6805`; `max_update_ms=4.2407`; `data_message_count=90`; `push_message_count=3`; `event_count=3`; `event_value_count=2`; `guide_count=3`; `full_snapshot_count=3`; `live_update_count=87`; `screenshot_sampled_non_background_pixel_count=27707` | Screenshot: `/tmp/artisanz-pyqtgraph-grid-phase-fix.png`; visual review confirmed visible background gridlines and horizontal roast phase temperature bands after live/static overlay merge and visibility-floor fixes. |
| 2026-07-03 | ArtisanZ | Phase 1.20 PyQtGraph major-grid and dialog-control visual fix | 90 WebSocket `getData` samples, fixed 1s virtual step, smoke harness explicitly enabling grid | In-process `dev_simulator` WebSocket stream through PyQtGraph snapshot renderer with 60s time grid and 20C temperature grid | `avg_update_ms=2.0669`; `max_update_ms=6.0646`; `data_message_count=90`; `push_message_count=3`; `event_count=3`; `event_value_count=2`; `guide_count=3`; `full_snapshot_count=3`; `live_update_count=87`; `screenshot_sampled_non_background_pixel_count=24988` | Screenshot: `/tmp/artisanz-pyqtgraph-major-grid-phase-v2.png`; PyQtGraph now uses a major-only custom grid item instead of dense default grid rendering. Axes dialog spinboxes/dropdowns were widened and restyled to prevent clipped values and native 3D dropdown chrome. |
| 2026-07-03 | ArtisanZ | Phase 1.21 PyQtGraph roast-analysis visual parity pass | 360 WebSocket `getData` samples, fixed 1s virtual step, completed-roast event schedule | In-process `dev_simulator` WebSocket stream through PyQtGraph snapshot renderer with CHARGE/DRY/FCs/DROP, RoR curves, AUC area, development range, phase summaries, event values, guides, legend | `avg_update_ms=6.4701`; `max_update_ms=49.1963`; `data_message_count=360`; `push_message_count=6`; `event_count=6`; `event_value_count=2`; `guide_count=3`; `full_snapshot_count=6`; `live_update_count=354`; `renderer_event_item_count=12`; `renderer_area_item_count=1`; `ror_item_count=2`; `temperature_item_count=8`; `screenshot_sampled_non_background_pixel_count=34024` | Screenshot: `/tmp/artisanz-pyqtgraph-parity-phase-summary-v2.png`; restored main-event temperature labels, right-bottom legend, development time-range highlight, top phase summary bars/text, grid linestyle mapping, and stronger RoR curve pens. |
| 2026-07-03 | ArtisanZ | Phase 1.22 PyQtGraph original-annotation and RoR visibility pass | 360 WebSocket `getData` samples, fixed 1s virtual step, completed-roast event schedule with derived TP marker | In-process `dev_simulator` WebSocket stream through PyQtGraph snapshot renderer with original-style event point/leader annotations, TP, visible RoR overlay, thicker top phase bars, phase summaries, development range, event values, guides, legend | `avg_update_ms=9.7526`; `max_update_ms=31.9163`; `data_message_count=360`; `push_message_count=6`; `event_count=7`; `event_value_count=2`; `guide_count=3`; `full_snapshot_count=6`; `live_update_count=354`; `renderer_event_item_count=29`; `renderer_area_item_count=1`; `ror_item_count=2`; `temperature_item_count=23`; `screenshot_sampled_non_background_pixel_count=33983` | Screenshot: `/tmp/artisanz-pyqtgraph-original-annotations-v4.png`; TP now appears, main events use point/leader/two-text annotations rather than vertical-line labels, first phase BT delta uses TP-to-DRY and is no longer negative, RoR overlay is layered above the temperature surface, and toolbar icons now prefer project-owned flat SVG assets. |

## Decision Log

Record decisions after benchmark runs:

- If `canvas.updategraphics` dominates, prioritize renderer boundary and PyQtGraph POC.
- If `canvas.sample_processing` dominates, prioritize processing decoupling before renderer replacement.
- If `canvas.redraw` dominates only during settings/profile actions, prioritize full-redraw reduction but keep live renderer scope narrow.
- If lock skip counters rise under normal sampling, prioritize signal scheduling and critical-section reduction.

Current automated profile redraw result: `canvas.updateBackground`, `canvas.redraw`, and `canvas.redraw_keep_view` dominate. The original 20-second simulator recording smoke baseline showed `canvas.sample_processing` around 1ms average and 2ms max, while live `canvas.updategraphics` reached a 47ms max and full redraw/background paths remained larger. After the Phase 3 processed-frame contract slice, one comparable short simulator smoke measured `canvas.sample_processing` around 0.5ms average and 0.6ms max. Later 20-second smokes measured `canvas.sample_processing` around 1.0ms average after PID/manual/extra diagnostics, around 1.1ms after curve data payload extraction, and around 0.6ms after input-filter extraction. The 60-second simulator baseline after the workspace status dock restoration fix measured `canvas.sample_processing avg=0.702ms max=1.530ms`, still below `updategraphics`, `updateBackground`, and `redraw`. This supports continuing renderer/update-path work before broad processing-thread migration. A real-device baseline is still required before treating simulator-only timing as representative hardware evidence.

Renderer benchmark decision: the current synthetic adapter benchmark shows PyQtGraph roughly 4x faster than the Matplotlib adapter for the same snapshot, with or without requesting OpenGL. The offscreen platform reports `opengl_widget_supported=false`, and the first guarded embed smoke with OpenGL produced a blank graph surface in this environment. The guarded main-window target therefore uses software PyQtGraph until a real-window/device OpenGL run proves the accelerated path is valid. The 2026-07-02 offscreen and native-window PyQtGraph simulator captures are nonblank, use the light Widgets surface, and keep `updategraphics` in the same short-smoke range as the prior Matplotlib live path.

Phase 1.5 decision: PyQtGraph is now the default selected renderer. Matplotlib remains available through `ARTISANZ_RENDERER_ID=matplotlib-snapshot` and runtime fallback paths. The default PyQtGraph profile-redraw capture now displays historical profile curves, preserves the LCD telemetry column, uses one graph with a right-side RoR axis, applies the existing axis tick/grid settings, and supports minute/second time-label selection from Config > Axes. PyQtGraph still has lower overlay parity than Matplotlib for rich annotations/background analysis. Continue treating Matplotlib as the compatibility/export renderer while Phase 1.6 improves PyQtGraph visual parity and dialog styling.

Phase 1.6 decision: the PyQtGraph grid should be drawn by a dedicated overlay rather than relying on built-in `PlotItem.showGrid()` styling, because the default light theme makes the built-in grid too faint. Default phase bands should use visible Morandi colors while preserving user/custom colors. LCD telemetry should avoid nested outer-card/value compositions; transparent containers plus self-contained value surfaces are less fragile.

Phase 1.6/4/5/6 closure decision: the 2026-07-02 closure work adds renderer-neutral event value rails and guide-line snapshots, renders those overlays in PyQtGraph, applies scoped modern dialog chrome to Axes/Curves/Events/Alarms, exposes workspace action hints in the QML status island, and adds typed plugin categories for renderer/report/analyzer/filter/profile-comparison boundaries. This is a visual/runtime and architecture-boundary closure, not a new performance baseline; Matplotlib remains the compatibility/export renderer, and real-device/OpenGL validation remains a future gate.

Phase 1.7 decision: deterministic WebSocket virtual-roast validation is now available as a repeatable bridge between static renderer smokes and real-device sessions. The first 24-sample run shows the PyQtGraph renderer can consume WebSocket-derived BT/ET/RoR frames, overlay push events/event values/guides, and keep renderer update work below 5ms max in this offscreen harness. This supports continuing PyQtGraph parity and event-heavy visual QA before physical-device testing, but it is still not a substitute for hardware timing.

Phase 1.8 decision: the same deterministic WebSocket stream can now drive the full Artisan main-window recording path. The autorun temporarily configures `qmc.device == 111`, channel 0/1 as `BT`/`ET`, and the generated WebSocket endpoint without persisting those settings. The first full-app run produced 30 samples, CHARGE/DRY/FCs/FCe/SCs/DROP indexes, a non-empty PyQtGraph screenshot, and performance metrics in the same short-smoke range as prior simulator runs. This closes the virtual-data plumbing gate before hardware testing; real-time physical-device sessions remain pending.

Phase 1.19 decision: live PyQtGraph updates must carry the same static overlay payload as full snapshots for grid/phase/event parity to be credible. The live path now merges current canvas static overlays into curve-only live frames, and the renderer applies those static layers without repeated churn when the payload is unchanged. Gridlines and phase bands now use explicit visibility floors because the default light canvas made technically-rendered overlays too faint to inspect reliably.

Phase 1.20 decision: grid visibility remains controlled by the existing Axes dialog checkboxes. The PyQtGraph renderer now draws only major grid lines at configured tick steps, so validation screenshots must explicitly state the grid step used. Initial PyQtGraph target creation now forces one static-overlay sync so phase bands appear before live samples when `watermarksflag` is enabled. Modern dialog controls must reserve right-side button padding and expand legacy fixed-width spinboxes/combos rather than letting text clip under arrows.

Phase 1.21 decision: switching the default renderer to PyQtGraph requires snapshot parity for roast-analysis semantics, not just curve parity. Event markers now carry BT temperature values, completed roasts emit development time-range and phase-summary overlays, the renderer manages a legend including RoR curves, and grid style maps the original Axes dialog solid/dashed/dash-dot/dotted choice. Remaining refinements should focus on exact Matplotlib label placement and collision avoidance, not missing data paths.

Phase 1.22 decision: PyQtGraph main-event rendering must follow the original Artisan annotation model closely enough to preserve roast-analysis meaning: a curve point, leader lines, BT temperature text, and event/time text. TP is part of that model and must be derived when available. Saved-profile RoR curves must use the same visible segment rules as Matplotlib and the right-axis overlay must be drawn above the temperature surface. The top phase summary delta must use TP-to-DRY for the first phase to avoid misleading negative values during the turning-point dip.

## Capture Troubleshooting

- If no metrics appear, confirm Artisan was launched from `src/` with `ARTISANZ_GUI_PERF=1`.
- If no explicit output path is set, run `.venv/bin/python -m artisanlib.performance_report` from `src/`; it reads the default temp-file path.
- If Artisan is killed rather than closed, the `atexit` fallback should still export metrics for normal Python shutdown, but force-kill paths may still lose data.
