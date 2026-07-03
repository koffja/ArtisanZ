# Phase 1.26: Toolbar Visual Fit Pass

## Objective

Fix the remaining toolbar visual regressions after the PyQtGraph toolbar reduction: the Cotrix brand pill could be clipped vertically, the Lines icon looked undersized, and the strip still felt like mismatched legacy toolbar parts.

## Design Direction

Subject: Cotrix roast monitoring toolbar for fast graph orientation.

Visual policy: one quiet 58px band, fixed 44px controls, centered icon-only buttons, and a compact Cotrix brand pill. The toolbar should read as a deliberate control strip, not as individual old desktop actions dropped into a blank area.

## Implementation Summary

- Added `roast_toolbar_visual_metrics()` as the single source of toolbar dimensions.
- Applied fixed toolbar height, vertical padding, icon size, brand width, compact button size, and readout height from that metric set.
- Moved action button styling into `VMToolbar._style_toolbar_action_button()` so initial actions and the later Lines action receive the same sizing rules.
- Rebuilt `qt4_editor_options.svg` and `white_qt4_editor_options.svg` as stronger 32x32 assets so the Lines action no longer reads as tiny.
- Updated `QToolBar#roastNavigationToolbar` global QSS to match the runtime height.
- Added toolbar rules to `docs/GUI_VISUAL_DESIGN_REFERENCE.md`.

## Verification

- `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_main.py::test_roast_toolbar_visual_metrics_prevent_brand_clipping -q`
- `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_gui_theme.py::test_lines_toolbar_icons_are_full_size_modern_assets -q`
- `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_main.py::test_update_plus_status_uses_cotrix_brand_and_hides_empty_subscription test/unitary/artisanlib/test_main.py::test_toolbar_callback_visibility_hides_legacy_matplotlib_nav_for_pyqtgraph test/unitary/artisanlib/test_main.py::test_apply_toolbar_surface_policy_hides_only_unsupported_pyqtgraph_actions test/unitary/artisanlib/test_main.py::test_reset_pyqtgraph_toolbar_target_syncs_current_graph_view test/unitary/artisanlib/test_main.py::test_reset_pyqtgraph_toolbar_target_ignores_matplotlib_surface test/unitary/artisanlib/test_main.py::test_roast_toolbar_visual_metrics_prevent_brand_clipping test/unitary/artisanlib/test_gui_theme.py -q`
- `cd src && .venv/bin/python -m py_compile artisanlib/main.py artisanlib/gui_theme.py`
- `cd src && .venv/bin/python -m ruff check artisanlib/main.py artisanlib/gui_theme.py test/unitary/artisanlib/test_main.py test/unitary/artisanlib/test_gui_theme.py`
- `git diff --check`
- `cd src && QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_AUTORUN=1 ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=4 ARTISANZ_GUI_PERF_AUTORUN_INTERVAL_MS=40 ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-toolbar-polish-perf.jsonl ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-toolbar-polish.png .venv/bin/python artisan.py /Users/chengzhe/Projects/ArtisanZ/src/test/sanity/data/artisan/profile1.alog`

Latest result: focused and related toolbar/theme tests produced `18 passed`; compile, ruff, and diff checks passed. Screenshot smoke produced `/tmp/artisanz-toolbar-polish.png`.

## Remaining Follow-Up

The toolbar now fits visually, but the Lines action still opens the legacy Matplotlib curve-style editor. The next functional toolbar step is a renderer-neutral curve style panel that can edit PyQtGraph curves directly.
