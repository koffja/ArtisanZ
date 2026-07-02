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

## Decision Log

Record decisions after benchmark runs:

- If `canvas.updategraphics` dominates, prioritize renderer boundary and PyQtGraph POC.
- If `canvas.sample_processing` dominates, prioritize processing decoupling before renderer replacement.
- If `canvas.redraw` dominates only during settings/profile actions, prioritize full-redraw reduction but keep live renderer scope narrow.
- If lock skip counters rise under normal sampling, prioritize signal scheduling and critical-section reduction.

Current automated profile redraw result: `canvas.updateBackground`, `canvas.redraw`, and `canvas.redraw_keep_view` dominate. The original 20-second simulator recording smoke baseline showed `canvas.sample_processing` around 1ms average and 2ms max, while live `canvas.updategraphics` reached a 47ms max and full redraw/background paths remained larger. After the Phase 3 processed-frame contract slice, one comparable short simulator smoke measured `canvas.sample_processing` around 0.5ms average and 0.6ms max. Later 20-second smokes measured `canvas.sample_processing` around 1.0ms average after PID/manual/extra diagnostics, around 1.1ms after curve data payload extraction, and around 0.6ms after input-filter extraction. The 60-second simulator baseline after the workspace status dock restoration fix measured `canvas.sample_processing avg=0.702ms max=1.530ms`, still below `updategraphics`, `updateBackground`, and `redraw`. This supports continuing renderer/update-path work before broad processing-thread migration. A real-device baseline is still required before treating simulator-only timing as representative hardware evidence.

Renderer benchmark decision: the current synthetic adapter benchmark shows PyQtGraph roughly 4x faster than the Matplotlib adapter for the same snapshot, with or without requesting OpenGL. The offscreen platform reports `opengl_widget_supported=false`, and the first guarded embed smoke with OpenGL produced a blank graph surface in this environment. The guarded main-window target therefore uses software PyQtGraph until a real-window/device OpenGL run proves the accelerated path is valid. The 2026-07-02 offscreen and native-window PyQtGraph simulator captures are nonblank, use the light Widgets surface, and keep `updategraphics` in the same short-smoke range as the prior Matplotlib live path; this supports continuing Phase 3/4 UI decomposition while leaving Matplotlib available as the default/fallback renderer.

## Capture Troubleshooting

- If no metrics appear, confirm Artisan was launched from `src/` with `ARTISANZ_GUI_PERF=1`.
- If no explicit output path is set, run `.venv/bin/python -m artisanlib.performance_report` from `src/`; it reads the default temp-file path.
- If Artisan is killed rather than closed, the `atexit` fallback should still export metrics for normal Python shutdown, but force-kill paths may still lose data.
