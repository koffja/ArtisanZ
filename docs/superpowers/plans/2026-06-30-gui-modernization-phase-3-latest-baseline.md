# GUI Modernization Phase 3 Latest Simulator Baseline

> **For agentic workers:** Use this record when deciding whether Phase 3 is ready for broader threading work or Phase 4 information architecture.

**Goal:** Capture a fresh 20-second internal simulator live-sampling smoke after the Phase 3 PID/manual/extra-device extraction slices.

**Scenario:** START recording through the built-in profile simulator from `test/sanity/data/artisan/profile1.alog`.

**Command:**

```bash
cd src
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_MODE=simulator-recording \
ARTISANZ_GUI_PERF_AUTORUN_DURATION_MS=20000 \
ARTISANZ_GUI_PERF_AUTORUN_SIMULATOR_FILE=test/sanity/data/artisan/profile1.alog \
ARTISANZ_GUI_PERF_AUTORUN_STATUS_FILE=/tmp/artisanz-phase3-latest-status.txt \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-phase3-latest-gui-perf-live.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-phase3-latest-live-sim.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
```

**Status Log:**

```text
2026-06-30T05:09:20.714016+00:00 mode=simulator-recording
2026-06-30T05:09:21.915405+00:00 simulator-recording:start
2026-06-30T05:09:21.963745+00:00 simulator:file=/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/../test/sanity/data/artisan/profile1.alog
2026-06-30T05:09:21.964002+00:00 simulator-recording:scheduled
2026-06-30T05:09:42.186911+00:00 simulator-recording:stop flagon=True flagstart=True
2026-06-30T05:09:43.200594+00:00 finish
```

**Metrics:**

```text
metric                       count     total_ms      avg_ms      max_ms
-----------------------------------------------------------------------
canvas.redraw                       2      210.936     105.468     130.766
canvas.updateBackground             4      174.215      43.554      90.709
canvas.updategraphics              13       65.995       5.077      47.004
canvas.sample_processing           10        9.753       0.975       1.799
canvas.updateBackground.skip        1        0.000       0.000       0.000
```

**Artifacts:**

- Metrics JSONL: `/tmp/artisanz-phase3-latest-gui-perf-live.jsonl`
- Screenshot: `/tmp/artisanz-phase3-latest-live-sim.png`
- Status log: `/tmp/artisanz-phase3-latest-status.txt`

**Conclusion:** This short smoke remains consistent with Phase 3 being worthwhile: `canvas.sample_processing` is slightly below the original 20-second smoke (`avg=1.103ms`, `max=2.015ms`) but above the processed-frame run (`avg=0.500ms`, `max=0.574ms`). Treat this as a noisy smoke check, not causal proof. Do not start broad threading work until a longer simulator/device baseline confirms the processing path is a material bottleneck.
