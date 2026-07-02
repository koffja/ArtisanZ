# Phase 1.19: PyQtGraph Grid and Phase Background Live Parity

## Goal

Fix the PyQtGraph default renderer regression where gridlines and roast phase temperature bands could be absent or too faint during live updates, even though the static snapshot path had partial support.

## Problem

- `PyQtGraphSnapshotRenderer.set_snapshot()` rendered static overlays, but `update_live_frame()` only updated curves.
- `tgraphcanvas.apply_pyqtgraph_live_plot_frame()` converted `LivePlotFrame` into a curve-only `RoastPlotSnapshot`, so the live/default PyQtGraph path did not consistently receive phase bands, event overlays, guides, or area fills.
- Gridlines and pale phase bands existed in code but were too low-contrast on the light roast canvas, making them visually easy to miss.

## Implemented

- Added `build_roast_plot_static_overlay_snapshot()` so live updates can extract only events, event values, phase bands, guides, and area fills without rebuilding all curve payloads.
- Added `merge_static_plot_overlays()` to combine live curve snapshots with renderer-neutral static overlays from the current canvas state.
- Updated `apply_pyqtgraph_live_plot_frame()` to feed merged live/static snapshots to the embedded PyQtGraph renderer, with a safe fallback to curve-only updates if static overlay extraction fails.
- Updated `PyQtGraphSnapshotRenderer.update_live_frame()` to apply static overlays on every live snapshot, clear stale overlays when the incoming snapshot has none, and avoid repeated remove/add churn when the axis-aware overlay payload is unchanged.
- Increased PyQtGraph grid contrast and alpha floor.
- Increased phase-band opacity floor for light-canvas visibility.
- Added regression tests for live overlay merging, live renderer static overlay application, stale-overlay clearing, axis-dependent overlay refresh, canvas live-path static overlay delivery, and visibility floors.

## Verification

- `cd src && ./.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_websocket_renderer_smoke.py -q`
  - Result: `79 passed`
- `cd src && ./.venv/bin/python -m py_compile artisanlib/plot_snapshot_extractor.py artisanlib/plot_live_frame.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/plot_pyqtgraph_widget.py artisanlib/canvas.py`
  - Result: passed
- `cd src && ./.venv/bin/ruff check artisanlib/canvas.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_live_frame.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/plot_pyqtgraph_widget.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py`
  - Result: passed
- `cd src && QT_QPA_PLATFORM=offscreen ./.venv/bin/python -m artisanlib.websocket_renderer_smoke --scenario event-heavy --samples 90 --fixed-step-ms 1000 --screenshot-file /tmp/artisanz-pyqtgraph-grid-phase-fix.png`
  - Result: `avg_update_ms=1.6805`, `max_update_ms=4.2407`, `live_update_count=87`, `full_snapshot_count=3`, `renderer_event_item_count=6`, `renderer_event_value_item_count=2`, `renderer_guide_item_count=3`, `screenshot_byte_count=64841`, `screenshot_sampled_non_background_pixel_count=27707`.
  - Visual review confirmed visible background gridlines and horizontal phase temperature bands.

## Remaining Gate

This closes the immediate grid/phase visual regression on the default PyQtGraph live path. Remaining PyQtGraph parity work should focus on richer historical overlays, interactive edit parity, and report/export backend switching rather than claiming all Matplotlib graph features are already matched.
