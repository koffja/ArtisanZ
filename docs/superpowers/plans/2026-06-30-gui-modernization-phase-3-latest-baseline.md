# GUI Modernization Phase 3 Latest Simulator Baseline

> **For agentic workers:** Use this record when deciding whether Phase 3 is ready for broader threading work or Phase 4 information architecture.

**Goal:** Capture a fresh 20-second internal simulator live-sampling smoke after the Phase 3 curve-data payload extraction slices.

**Scenario:** START recording through the built-in profile simulator from `test/sanity/data/artisan/profile1.alog`.

**Command:**

```bash
cd src
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_MODE=simulator-recording \
ARTISANZ_GUI_PERF_AUTORUN_DURATION_MS=20000 \
ARTISANZ_GUI_PERF_AUTORUN_SIMULATOR_FILE=test/sanity/data/artisan/profile1.alog \
ARTISANZ_GUI_PERF_AUTORUN_STATUS_FILE=/tmp/artisanz-phase3-full-curve-status.txt \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-phase3-full-curve-perf.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-phase3-full-curve-live-sim.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
```

**Status Log:**

```text
2026-06-30T10:33:06.906962+00:00 mode=simulator-recording
2026-06-30T10:33:08.110437+00:00 simulator-recording:start
2026-06-30T10:33:08.175204+00:00 simulator:file=/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/../test/sanity/data/artisan/profile1.alog
2026-06-30T10:33:08.175325+00:00 simulator-recording:scheduled
2026-06-30T10:33:28.295028+00:00 simulator-recording:stop flagon=True flagstart=True
2026-06-30T10:33:29.323591+00:00 finish
```

**Metrics:**

```text
metric                       count     total_ms      avg_ms      max_ms
-----------------------------------------------------------------------
canvas.redraw                       2      171.129      85.564     109.547
canvas.updateBackground             4      132.652      33.163      67.517
canvas.updategraphics              13       55.297       4.254      36.701
canvas.sample_processing           10       11.179       1.118       1.755
canvas.updateBackground.skip        1        0.000       0.000       0.000
```

**Artifacts:**

- Metrics JSONL: `/tmp/artisanz-phase3-full-curve-perf.jsonl`
- Screenshot: `/tmp/artisanz-phase3-full-curve-live-sim.png`
- Status log: `/tmp/artisanz-phase3-full-curve-status.txt`

**Conclusion:** This short smoke remains consistent with Phase 3 being useful for boundary cleanup but not yet evidence for broad threading work: `canvas.sample_processing` is comparable to the original 20-second smoke (`avg=1.103ms`, `max=2.015ms`) and still much smaller than the full redraw/background paths. The screenshot was inspected and did not show a regression in the corrected LCD value-surface alignment. Treat this as a noisy smoke check, not causal proof. Do not start broad threading work until a longer simulator/device baseline confirms the processing path is a material bottleneck.
