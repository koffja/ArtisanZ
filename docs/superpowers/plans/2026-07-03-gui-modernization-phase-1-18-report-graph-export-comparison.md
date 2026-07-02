# Phase 1.18: Report Graph Export Comparison

## Goal

Create a report-oriented comparison adapter for Matplotlib and PyQtGraph graph images, so the future report/export replacement can be evaluated with report-ready assets before changing `roastReport()`.

## Scope

- Add a report graph export comparison helper and CLI.
- Load saved `.alog` profiles through the existing saved-profile snapshot adapter.
- Generate Matplotlib and PyQtGraph graph image assets from the same renderer-neutral snapshot.
- Return report-style `file://` URLs with optional cache busters matching the existing HTML report reload pattern.
- Include dimensions, byte counts, PyQtGraph nonblank pixel evidence, view-state equality, and overlay counts.
- Keep `roastReport()` and existing Matplotlib report/export behavior unchanged.

## Out Of Scope

- No replacement of the HTML/PDF roast report graph.
- No flavor-chart replacement.
- No report template changes.

## Implementation Tasks

1. Add `artisanlib.plot_report_export`.
2. Add unit coverage for report image URLs, saved-profile report graph comparison, non-profile rejection, and missing profile rejection.
3. Run a real saved-profile CLI comparison using `test/data/profile1.alog`.
4. Keep the existing Matplotlib report path untouched.

## Completion Evidence

Closed on 2026-07-03 after compile, focused tests, lint, diff check, CLI validation, and code review.

- `python3 -m py_compile artisanlib/plot_report_export.py`
- `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_report_export.py -q`: `6 passed`
- `.venv/bin/python -m ruff check artisanlib/plot_report_export.py test/unitary/artisanlib/test_plot_report_export.py`
- CLI validation:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_report_export test/data/profile1.alog --output-dir /tmp/artisanz-phase118-report-graph --prefix phase118-profile1-report --width 1280 --height 720 --dpi 100 --cache-buster 118`

CLI evidence:

- `source_kind=profile`, `source_path=test/data/profile1.alog`, `title=Guji Shakiso`
- `sample_count=1735`
- `view_state_matches=true`, `view_state_max_delta=0.0`, `view_state_within_tolerance=true`
- `event_count=14`, `event_value_count=10`, `phase_band_count=3`, `area_count=1`
- Matplotlib asset: `/tmp/artisanz-phase118-report-graph/phase118-profile1-report-matplotlib.png`, `byte_count=233509`, `url=file:///tmp/artisanz-phase118-report-graph/phase118-profile1-report-matplotlib.png?dummy=118`
- PyQtGraph asset: `/tmp/artisanz-phase118-report-graph/phase118-profile1-report-pyqtgraph.png`, `byte_count=69659`, `sampled_non_background_pixel_count=14492`, `url=file:///tmp/artisanz-phase118-report-graph/phase118-profile1-report-pyqtgraph.png?dummy=118`

Reviewer follow-up fixed:

- Relative `--output-dir` values now resolve to absolute `file://` URLs before report embedding.
- `report_graph_comparison_from_parity()` now rejects non-profile parity results even if they carry a source path.

## Remaining Gate

This produces report-ready comparison assets but still does not switch `roastReport()`. The next report step should either run this comparison across the Phase 1.16 profile matrix or add an env-gated report image backend switch with Matplotlib fallback.
