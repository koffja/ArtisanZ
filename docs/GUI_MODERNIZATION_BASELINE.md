# GUI Modernization Baseline

**Status:** Phase 0 instrumentation ready; manual GUI baseline pending.

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

## Results Template

| Date | Branch | Scenario | Sampling Interval | Visible Curves | Key Metrics | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-29 | ArtisanZ | Not yet run | Not recorded | Not recorded | Not recorded | Instrumentation implemented and verified; capture hardened before real GUI baseline |
| 2026-06-29 | ArtisanZ | First manual run follow-up | Not recorded | Not recorded | No metrics file found | Default path and `ARTISANZ_GUI_PERF_FILE` search found no ArtisanZ JSONL; capture flow hardened with default temp export and `atexit` fallback |

## Decision Log

Record decisions after benchmark runs:

- If `canvas.updategraphics` dominates, prioritize renderer boundary and PyQtGraph POC.
- If `canvas.sample_processing` dominates, prioritize processing decoupling before renderer replacement.
- If `canvas.redraw` dominates only during settings/profile actions, prioritize full-redraw reduction but keep live renderer scope narrow.
- If lock skip counters rise under normal sampling, prioritize signal scheduling and critical-section reduction.

## Capture Troubleshooting

- If no metrics appear, confirm Artisan was launched from `src/` with `ARTISANZ_GUI_PERF=1`.
- If no explicit output path is set, run `.venv/bin/python -m artisanlib.performance_report` from `src/`; it reads the default temp-file path.
- If Artisan is killed rather than closed, the `atexit` fallback should still export metrics for normal Python shutdown, but force-kill paths may still lose data.
