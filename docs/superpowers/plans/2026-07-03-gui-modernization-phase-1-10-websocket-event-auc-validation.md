# ArtisanZ GUI Modernization Phase 1.10: WebSocket Event/AUC Visual Validation

**Goal:** Validate the default PyQtGraph renderer with deterministic WebSocket virtual roast data that includes dense events, event value rails, RoR, guide lines, and post-DROP AUC area rendering.

**Execution Status:** Implemented and verified on 2026-07-03.

## Scope

- Extend the WebSocket renderer smoke harness with an `event-heavy` virtual roast scenario.
- Include AUC area fills in snapshots produced from WebSocket samples after DROP.
- Report AUC area counts and renderer area item counts in the smoke result JSON.
- Add optional PyQtGraph screenshot capture to the smoke CLI.
- Fix edge-event label anchoring so CHARGE/DROP labels do not clip at the plot boundaries.
- Cover the new behavior with focused tests.

## Non-Goals

- Do not replace the full main-window autorun from Phase 1.8.
- Do not claim hardware-device parity from virtual data.
- Do not add PyQtGraph export/report replacement.
- Do not implement event drag/edit interaction in this slice.

## Validation

```bash
cd src
.venv/bin/python -m pytest \
  test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py \
  test/unitary/artisanlib/test_websocket_renderer_smoke.py \
  -q

.venv/bin/python -m ruff check \
  artisanlib/plot_pyqtgraph_adapter.py \
  artisanlib/websocket_renderer_smoke.py \
  test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py \
  test/unitary/artisanlib/test_websocket_renderer_smoke.py

QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke \
  --samples 24 \
  --fixed-step-ms 15000 \
  --scenario event-heavy \
  --screenshot-file /tmp/artisanz-websocket-event-heavy.png
```

## Result

- `event-heavy` WebSocket smoke output produced `sample_count=24`, `data_message_count=24`, `push_message_count=11`, `event_count=11`, `event_value_count=7`, `area_count=1`, `renderer_area_item_count=1`, `guide_count=3`, `temperature_item_count=10`, `ror_item_count=2`, `full_snapshot_count=7`, and `live_update_count=17`.
- Renderer timing for the final event-heavy smoke was `avg_update_ms=2.5528` and `max_update_ms=14.5805`.
- Screenshot evidence: `/tmp/artisanz-websocket-event-heavy.png`.
- Screenshot review confirmed nonblank PyQtGraph output with visible grid, dense event labels, RoR axis, AUC fill, and unclipped CHARGE label.
- Focused validation: `15 passed` across PyQtGraph adapter and WebSocket renderer smoke tests.
- Static validation: `py_compile`, `ruff check`, and `git diff --check` passed for touched modules.

## Remaining Gate

This closes virtual event/AUC renderer validation. Remaining GUI modernization validation still needs a real-device or long real-time hardware-like session and deeper PyQtGraph parity for event drag/edit, analysis masks/statistics, and export/report handoff.
