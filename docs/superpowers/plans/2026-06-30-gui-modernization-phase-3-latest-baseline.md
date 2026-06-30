# GUI Modernization Phase 3 Latest Simulator Baseline

> **For agentic workers:** Use this record when deciding whether Phase 3 is ready for broader threading work or Phase 4 information architecture.

**Goal:** Capture a fresh 20-second internal simulator live-sampling smoke after the Phase 3 input-filter extraction slice.

**Scenario:** START recording through the built-in profile simulator from `test/sanity/data/artisan/profile1.alog`.

**Command:**

```bash
cd src
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_MODE=simulator-recording \
ARTISANZ_GUI_PERF_AUTORUN_DURATION_MS=20000 \
ARTISANZ_GUI_PERF_AUTORUN_SIMULATOR_FILE=test/sanity/data/artisan/profile1.alog \
ARTISANZ_GUI_PERF_AUTORUN_STATUS_FILE=/tmp/artisanz-phase3-input-filter-status.txt \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-phase3-input-filter-perf.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-phase3-input-filter-live-sim.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
```

**Status Log:**

```text
2026-06-30T10:54:16.815128+00:00 mode=simulator-recording
2026-06-30T10:54:18.018030+00:00 simulator-recording:start
2026-06-30T10:54:18.052734+00:00 simulator:file=/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/../test/sanity/data/artisan/profile1.alog
2026-06-30T10:54:18.052846+00:00 simulator-recording:scheduled
2026-06-30T10:54:38.158924+00:00 simulator-recording:stop flagon=True flagstart=True
2026-06-30T10:54:39.184405+00:00 finish
```

**Metrics:**

```text
metric                       count     total_ms      avg_ms      max_ms
-----------------------------------------------------------------------
canvas.redraw                       2      157.880      78.940     115.892
canvas.updateBackground             4      139.990      34.997      75.626
canvas.updategraphics              13       46.910       3.608      34.669
canvas.sample_processing           10        5.938       0.594       1.402
canvas.updateBackground.skip        1        0.000       0.000       0.000
```

**Artifacts:**

- Metrics JSONL: `/tmp/artisanz-phase3-input-filter-perf.jsonl`
- Screenshot: `/tmp/artisanz-phase3-input-filter-live-sim.png`
- Status log: `/tmp/artisanz-phase3-input-filter-status.txt`

**Conclusion:** This short smoke remains consistent with Phase 3 being useful for boundary cleanup but not yet evidence for broad threading work: `canvas.sample_processing` measured below the original 20-second smoke (`avg=1.103ms`, `max=2.015ms`) and remains much smaller than the full redraw/background paths. The screenshot was inspected and did not show a regression in the corrected LCD value-surface alignment. Treat this as a noisy smoke check, not causal proof. Do not start broad threading work until a longer simulator/device baseline confirms the processing path is a material bottleneck.
