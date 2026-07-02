# Phase 1.15: Saved Profile Export Parity

## Goal

Validate PyQtGraph export parity against real saved Artisan `.alog` profile data, not only synthetic WebSocket samples.

## Scope

- Add a saved-profile snapshot source that loads Artisan `.alog` files through the existing `artisanlib.util.deserialize()` path.
- Convert profile dictionaries into the renderer-neutral `RoastPlotSnapshot` contract through the existing extractor.
- Supply reasonable historical-profile defaults for:
  - axis ranges
  - ET/BT visibility
  - computed RoR curves when saved deltas are absent
  - phase bands
  - AUC area
  - event colors and event labels
- Extend the export parity CLI with `--profile-file`.
- Add unit tests using `test/data/profile1.alog`.
- Keep production report/export menus untouched.

## Out Of Scope

- No production report/export UI switch.
- No attempt to perfectly reproduce every legacy Matplotlib report annotation.
- No real hardware timing validation.

## Implementation Tasks

1. Add `artisanlib.plot_profile_snapshot`.
2. Extend `artisanlib.plot_export_parity_smoke` with `run_profile_export_parity_smoke()` and `--profile-file`.
3. Add tests for `.alog` snapshot extraction and saved-profile export parity.
4. Run CLI evidence on `test/data/profile1.alog`.

## Completion Evidence

Closed on 2026-07-03 after compile, tests, lint, diff check, and CLI validation.

- `python3 -m py_compile artisanlib/plot_profile_snapshot.py artisanlib/plot_export_parity_smoke.py`
- `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_profile_snapshot.py test/unitary/artisanlib/test_plot_export_parity_smoke.py -q`: `7 passed`
- `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_profile_snapshot.py test/unitary/artisanlib/test_plot_export_parity_smoke.py test/unitary/artisanlib/test_plot_matplotlib_smoke.py test/unitary/artisanlib/test_plot_matplotlib_adapter.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py test/unitary/artisanlib/test_websocket_renderer_smoke.py -q`: `28 passed`
- CLI evidence command:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_export_parity_smoke --profile-file test/data/profile1.alog --output-dir /tmp/artisanz-phase115-profile-export-parity-final --prefix phase115-profile1 --width 1280 --height 720 --dpi 100`
- WebSocket regression command:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_export_parity_smoke --samples 24 --fixed-step-ms 15000 --scenario event-heavy --output-dir /tmp/artisanz-phase115-websocket-parity-final --prefix phase115-websocket-event-heavy --width 1280 --height 720 --dpi 100`

CLI evidence:

- `source_kind=profile`, `source_path=test/data/profile1.alog`, `sample_count=1735`
- `time_axis.minimum=795.4684590097568`, `time_axis.maximum=1474.1684661597471`, matching saved Artisan profile semantics of `xmin` plus `xmax` duration
- `view_state_matches=true`, `view_state_max_delta=0.0`, `view_state_within_tolerance=true`
- `event_count=14`, `event_value_count=10`, `phase_band_count=3`, `area_count=1`
- Matplotlib: `byte_count=233509`, `event_artist_count=28`, `event_value_artist_count=10`, `phase_artist_count=3`, `area_artist_count=1`, `ror_line_count=2`
- PyQtGraph: `byte_count=69659`, `sampled_non_background_pixel_count=14492`, `renderer_event_item_count=28`, `renderer_event_value_item_count=10`, `renderer_area_item_count=1`, `ror_item_count=2`

Reviewer follow-up fixed:

- Saved profile `xmax` is treated as a duration from `xmin`, not an absolute right edge.
- Missing, empty, or sample-less profile inputs now fail instead of producing false-positive empty evidence.

## Remaining Gate

This validates saved-profile parity for an automated profile fixture. The next export/report step should compare a small matrix of saved profiles and then decide whether to expose PyQtGraph export as an opt-in user action.
