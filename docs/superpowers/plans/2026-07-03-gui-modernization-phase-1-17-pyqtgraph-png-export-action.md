# Phase 1.17: Opt-In PyQtGraph PNG Export Action

## Goal

Make the PyQtGraph export work visible to users through an opt-in menu action, without replacing the existing Matplotlib save/report/export compatibility paths.

## Scope

- Add a user-facing `File > Save Graph > PyQtGraph PNG...` action.
- Keep existing `PDF...`, `SVG...`, `PNG...`, and `JPEG...` actions unchanged.
- Export the current graph through the renderer-neutral snapshot extractor and PyQtGraph PNG renderer.
- Use the current graph widget size when available, with stable fallback dimensions for non-widget smoke paths.
- Add tests for path normalization, export sizing, invalid explicit sizes, and saved-profile PyQtGraph PNG output.

## Out Of Scope

- No replacement of Matplotlib PNG/PDF/SVG export.
- No roast report HTML/PDF changes.
- No autosave format changes.

## Implementation Tasks

1. Add `artisanlib.plot_user_export` as a UI-oriented PyQtGraph PNG export helper.
2. Add `ApplicationWindow.savePyQtGraphPNG()`.
3. Add `PyQtGraph PNG...` to the existing Save Graph menu.
4. Add unit/smoke coverage against `test/data/profile1.alog`.
5. Validate the helper with a real offscreen PyQtGraph PNG export.

## Completion Evidence

Closed on 2026-07-03 after compile, focused tests, lint, diff check, CLI validation, and code review.

- `python3 -m py_compile artisanlib/plot_user_export.py artisanlib/main.py`
- `.venv/bin/python -m pytest test/unitary/artisanlib/test_plot_user_export.py test/unitary/artisanlib/test_plot_export_parity_matrix.py test/unitary/artisanlib/test_plot_profile_snapshot.py test/unitary/artisanlib/test_plot_export_parity_smoke.py test/unitary/artisanlib/test_plot_pyqtgraph_widget.py -q`: `27 passed`
- `.venv/bin/python -m ruff check artisanlib/plot_user_export.py test/unitary/artisanlib/test_plot_user_export.py artisanlib/main.py`
- PyQtGraph user-export smoke:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python - <<'PY' ... export_current_graph_pyqtgraph_png(ProfileSnapshotSource(deserialize('test/data/profile1.alog')), '/tmp/artisanz-phase117-user-export-profile1', width=1280, height=720, use_opengl=False) ... PY`

Smoke evidence:

- `path=/tmp/artisanz-phase117-user-export-profile1.png`
- `width=1280`, `height=720`
- `byte_count=69659`
- `sampled_non_background_pixel_count=14492`
- `temperature_item_count=13`
- `ror_item_count=2`
- `event_item_count=28`
- `event_value_item_count=10`
- `area_item_count=1`

Code review:

- `gsd-code-reviewer` verdict: clean for Phase 1.17 scope; no Critical, Warning, or Info findings.

## Remaining Gate

This is an opt-in user action only. Matplotlib remains the default report/export compatibility path until report-specific output parity is designed and compared.
