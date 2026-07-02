# Phase 1.13: PyQtGraph Export Evidence and WebSocket Validation

## Goal

Create a small, reusable PyQtGraph PNG export/evidence path so default-renderer changes can be validated with rendered pixels and item counts, not only by checking that a widget exists.

## Scope

- Add a PyQtGraph snapshot-to-PNG helper that renders a `RoastPlotSnapshot` through the real `GraphicsLayoutWidget` target.
- Add sampled pixel evidence so automated validation can reject blank or background-only captures.
- Reuse the same PNG helper from the WebSocket renderer smoke path.
- Extend WebSocket event-heavy validation to report screenshot dimensions, byte count, sampled pixels, and sampled non-background pixels.
- Keep Matplotlib report/export as the compatibility path until a deliberate report/export adapter is designed.

## Out Of Scope

- No user-facing menu switch from Matplotlib export to PyQtGraph export.
- No replacement of HTML/PDF report graph generation.
- No OpenGL default change; software PyQtGraph remains the validated path in this environment.

## Implementation Tasks

1. Add `artisanlib.plot_pyqtgraph_export` with widget PNG and snapshot PNG export helpers.
2. Record renderer item counts and view state in the snapshot export result.
3. Replace the private WebSocket screenshot helper with the shared PNG export helper.
4. Add tests that render WebSocket-derived snapshots to PNG and assert non-background pixels.
5. Run the event-heavy WebSocket smoke with screenshot output and record the evidence.

## Exit Gate

- Focused tests pass for WebSocket renderer smoke and PyQtGraph PNG export.
- CLI WebSocket smoke with `--scenario event-heavy --screenshot-file ...` returns nonzero sampled non-background pixels.
- Code review finds no blocking issues.

## Completion Evidence

Closed on 2026-07-03 after focused compile, unit, lint, diff, and CLI WebSocket validation.

- `python3 -m py_compile artisanlib/plot_pyqtgraph_export.py artisanlib/websocket_renderer_smoke.py`
- `.venv/bin/python -m pytest test/unitary/artisanlib/test_websocket_renderer_smoke.py -q`: `7 passed`
- `.venv/bin/python -m ruff check artisanlib/plot_pyqtgraph_export.py artisanlib/websocket_renderer_smoke.py test/unitary/artisanlib/test_websocket_renderer_smoke.py`
- `git diff --check`
- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke --samples 24 --fixed-step-ms 15000 --scenario event-heavy --screenshot-file /tmp/artisanz-phase113-websocket-event-heavy.png`

WebSocket evidence from the CLI smoke:

- `sample_count=24`, `data_message_count=24`, `push_message_count=11`
- `event_count=11`, `event_value_count=7`, `guide_count=3`, `area_count=1`
- `temperature_item_count=10`, `ror_item_count=2`
- `renderer_event_item_count=22`, `renderer_event_value_item_count=7`, `renderer_guide_item_count=3`, `renderer_area_item_count=1`
- `screenshot_width=1280`, `screenshot_height=720`, `screenshot_byte_count=71364`
- `screenshot_sampled_pixel_count=57600`, `screenshot_sampled_non_background_pixel_count=21753`
- `avg_update_ms=1.2337535930176575`, `max_update_ms=5.728333024308085`
