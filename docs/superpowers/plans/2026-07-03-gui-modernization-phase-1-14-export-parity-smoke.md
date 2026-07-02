# Phase 1.14: Export Parity Smoke

## Goal

Move PyQtGraph export work from a standalone screenshot helper toward a comparable export/report handoff by proving that the same renderer-neutral `RoastPlotSnapshot` can be exported through both Matplotlib and PyQtGraph with matching view state and overlay counts.

## Scope

- Add a CLI/module that exports the same snapshot through Matplotlib and PyQtGraph.
- Use deterministic WebSocket virtual roast data as the default smoke input.
- Extend the Matplotlib snapshot adapter to render snapshot overlays already supported by PyQtGraph:
  - phase bands
  - AUC/area fills
  - event value rails
  - guide lines
- Return JSON evidence for both backends:
  - PNG paths and byte counts
  - view-state match/tolerance data
  - line/item/artist counts
  - phase/event/event-value/guide/area counts
- Keep the existing Matplotlib report/export UI path untouched.

## Out Of Scope

- No user-facing export menu change.
- No replacement of HTML/PDF report graph generation.
- No claim of pixel-perfect parity with legacy Artisan report graphs.

## Implementation Tasks

1. Add `artisanlib.plot_export_parity_smoke`.
2. Extend `MatplotlibSnapshotRenderer` with overlay rendering/counts.
3. Extend Matplotlib smoke result metadata.
4. Add unit coverage for direct snapshot export parity and WebSocket event-heavy export parity.
5. Run a CLI WebSocket event-heavy export parity smoke and record evidence.

## Completion Evidence

Closed on 2026-07-03 after compile and focused test verification.

- `python3 -m py_compile artisanlib/plot_matplotlib_adapter.py artisanlib/plot_matplotlib_smoke.py artisanlib/plot_export_parity_smoke.py`
- `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_export_parity_smoke.py -q`: `7 passed`
- CLI evidence command:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_export_parity_smoke --samples 24 --fixed-step-ms 15000 --scenario event-heavy --output-dir /tmp/artisanz-phase114-export-parity --prefix phase114-event-heavy --width 1280 --height 720 --dpi 100`

CLI evidence:

- `view_state_matches=true`, `view_state_max_delta=0.0`, `view_state_within_tolerance=true`
- `event_count=11`, `event_value_count=7`, `phase_band_count=3`, `guide_count=3`, `area_count=1`
- Matplotlib: `byte_count=89990`, `event_artist_count=22`, `event_value_artist_count=7`, `phase_artist_count=3`, `guide_artist_count=3`, `area_artist_count=1`, `ror_line_count=2`
- PyQtGraph: `byte_count=71815`, `sampled_non_background_pixel_count=21795`, `renderer_event_item_count=22`, `renderer_event_value_item_count=7`, `renderer_guide_item_count=3`, `renderer_area_item_count=1`, `ror_item_count=2`

## Remaining Gate

This validates renderer-neutral export parity for the snapshot smoke path. It still does not switch the production report/export menus. That should remain gated on a deliberate report adapter and visual comparison against real saved profiles.
