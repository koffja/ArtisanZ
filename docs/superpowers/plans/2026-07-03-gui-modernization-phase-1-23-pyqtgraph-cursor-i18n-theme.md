# Phase 1.23: PyQtGraph Cursor, i18n, and Theme Parity

## Objective

Close the immediate user-facing regressions reported after the default PyQtGraph switch: invisible/weak RoR affordances, English graph labels in Chinese mode, clipped Axes dialog values, lost cursor readout, mismatched bottom event rail color, weak BT curve emphasis, stray lower-left PyQtGraph `A` button, and an overly technical default graph palette.

## Scope

- Route PyQtGraph main-event and TP labels through the existing Qt translation path.
- Restore graph cursor feedback into the existing toolbar message area with time, nearest temperature, and nearest RoR.
- Hide PyQtGraph's built-in auto-range button in the main plot surface.
- Widen polished dialog line edits and spinboxes so minute/time values do not clip under arrow controls.
- Match the bottom event-button rail background to the LCD/main surface.
- Make BT visibly stronger than secondary temperature curves by default.
- Confirm Delta ET/Delta BT RoR legend/render paths are active when their visibility flags are enabled.
- Replace the default Config > Colors palette with a softer Morandi/Wu Guanzhong-inspired palette while preserving the old Artisan default as a named theme.

## Out of Scope

- Replacing the Matplotlib report/export backend.
- Reworking all Config > Colors UI workflows.
- Physical-device or long real-time roast validation.
- Fixing user-specific saved-profile RoR visibility if the persisted profile/config disables Delta ET before renderer dispatch.

## Implementation Summary

- `plot_snapshot_extractor.py` now translates event labels via `QApplication.translate()`.
- `plot_pyqtgraph_widget.py` exposes cursor callbacks, maps scene coordinates into temperature/RoR view boxes, and removes the built-in auto-range button from the main roast graph.
- `canvas.py` consumes PyQtGraph cursor callbacks and writes the restored toolbar readout using existing ET/BT/RoR names and temperature formatting.
- `gui_theme.py` widens polished numeric/text controls and aligns the event rail background with the main window surface.
- `plot_pyqtgraph_adapter.py` strengthens the BT default pen and keeps RoR pens visually prominent.
- `includes/Themes/Artisan/Default.athm` now carries the softer ArtisanZ default; the old default is preserved as `includes/Themes/Artisan/Artisan.athm`.

## Verification

- `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_plot_live_frame.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_gui_theme.py -q`
- `cd src && .venv/bin/python -m py_compile artisanlib/plot_snapshot_extractor.py artisanlib/plot_pyqtgraph_widget.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/gui_theme.py artisanlib/canvas.py`
- `cd src && .venv/bin/python -m ruff check artisanlib/plot_snapshot_extractor.py artisanlib/plot_pyqtgraph_widget.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/gui_theme.py artisanlib/canvas.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_canvas_renderer_selection.py`
- `git diff --check`
- `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke --scenario event-heavy --samples 90 --fixed-step-ms 1000 --screenshot-file /tmp/artisanz-phase123-pyqtgraph-cursor-theme.png`

Latest result: `97 passed`, `py_compile` passed, `ruff check` passed, `git diff --check` passed, and the WebSocket smoke produced `ror_item_count=2`, `temperature_item_count=7`, `renderer_event_item_count=9`, and `screenshot_sampled_non_background_pixel_count=25257`.

## Remaining Follow-Up

- If ET RoR still does not appear on a specific saved profile, inspect the persisted `DeltaETflag`/curve visibility and profile RoR data before changing renderer code again.
- Continue PyQtGraph parity work on deeper interaction behavior: drag/edit event affordances, analysis masks, statistics overlays, and report/backend switching.
