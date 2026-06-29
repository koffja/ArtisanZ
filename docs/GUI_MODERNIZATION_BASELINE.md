# GUI Modernization Baseline

**Status:** Automated profile redraw baseline and 20-second internal simulator live-sampling smoke baseline captured; longer live/device baselines remain pending.

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

## Decision Log

Record decisions after benchmark runs:

- If `canvas.updategraphics` dominates, prioritize renderer boundary and PyQtGraph POC.
- If `canvas.sample_processing` dominates, prioritize processing decoupling before renderer replacement.
- If `canvas.redraw` dominates only during settings/profile actions, prioritize full-redraw reduction but keep live renderer scope narrow.
- If lock skip counters rise under normal sampling, prioritize signal scheduling and critical-section reduction.

Current automated profile redraw result: `canvas.updateBackground`, `canvas.redraw`, and `canvas.redraw_keep_view` dominate. The 20-second simulator recording smoke baseline shows `canvas.sample_processing` around 1ms average and 2ms max, while live `canvas.updategraphics` reaches a 47ms max and full redraw/background paths remain larger. This supports starting Phase 2 renderer-boundary planning before Phase 3 processing extraction, while still requiring longer simulator/device runs before broad threading changes.

## Capture Troubleshooting

- If no metrics appear, confirm Artisan was launched from `src/` with `ARTISANZ_GUI_PERF=1`.
- If no explicit output path is set, run `.venv/bin/python -m artisanlib.performance_report` from `src/`; it reads the default temp-file path.
- If Artisan is killed rather than closed, the `atexit` fallback should still export metrics for normal Python shutdown, but force-kill paths may still lose data.
