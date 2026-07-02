# Phase 1.16: Saved Profile Export Matrix

## Goal

Expand saved-profile export parity from one `.alog` fixture to a small matrix of real saved Artisan profiles, while keeping deterministic WebSocket virtual-data regression in the same evidence path.

## Scope

- Add a matrix runner that accepts explicit profile files or profile globs.
- Reuse the existing single-profile Matplotlib/PyQtGraph export parity path for every profile.
- Summarize:
  - profile count and source paths
  - total samples, events, and event values
  - phase-band coverage range
  - view-state equality/tolerance across all exports
  - PyQtGraph nonblank image evidence
  - optional WebSocket virtual-data regression status
- Keep production report/export menus untouched.

## Out Of Scope

- No user-facing export/report switch.
- No new profile fixture generation.
- No visual scoring beyond measurable parity and nonblank image evidence.

## Implementation Tasks

1. Add `artisanlib.plot_export_parity_matrix`.
2. Add unit tests for multi-profile matrix output, empty input rejection, default fixture collection, and input de-duplication.
3. Run CLI evidence on `test/sanity/data/artisan/profile*.alog`.
4. Include deterministic WebSocket `event-heavy` regression in the same CLI evidence run.

## Completion Evidence

Closed on 2026-07-03 after compile, focused tests, lint, diff check, code review, and CLI validation.

- `python3 -m py_compile artisanlib/plot_export_parity_matrix.py`
- `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_export_parity_matrix.py -q`: `6 passed`
- Matrix CLI command:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_export_parity_matrix --profile-glob 'test/sanity/data/artisan/profile*.alog' --include-websocket-regression --websocket-samples 24 --websocket-fixed-step-ms 15000 --websocket-scenario event-heavy --output-dir /tmp/artisanz-phase116-profile-matrix --prefix phase116-matrix --width 1280 --height 720 --dpi 100`

CLI evidence:

- `profile_count=4`
- `total_sample_count=2854`
- `total_event_count=74`
- `total_event_value_count=58`
- `minimum_phase_band_count=2`, `maximum_phase_band_count=3`
- `all_view_states_match=true`
- `all_view_states_within_tolerance=true`
- `maximum_view_state_delta=0.0`
- `all_pyqtgraph_exports_nonblank=true`
- `websocket_regression_included=true`
- `websocket_view_state_matches=true`

Reviewer follow-up fixed:

- Every explicitly requested `--profile-glob` must match at least one saved profile; typoed globs now fail even when another explicit file or glob matched.

## Remaining Gate

This makes report/export parity evidence broader, but the production report/export UI is still intentionally not switched. The next safe step is an opt-in user-facing PyQtGraph export action or a report/export adapter comparison against the existing Matplotlib output.
