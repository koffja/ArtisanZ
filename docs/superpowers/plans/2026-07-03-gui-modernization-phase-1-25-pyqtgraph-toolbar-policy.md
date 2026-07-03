# Phase 1.25: PyQtGraph-Native Toolbar Policy

## Objective

Remove misleading Matplotlib-only navigation controls from the default PyQtGraph main graph while preserving Matplotlib compatibility and keeping one clear reset action for the visible graph.

## Design Direction

Subject: Cotrix roast monitoring with PyQtGraph as the default graph surface.

Toolbar policy: keep only controls that either identify the product, operate on the visible PyQtGraph graph, or open a still-needed graph configuration path. Hide legacy controls that are technically present but do not match the active renderer.

Resulting PyQtGraph toolbar:

- Cotrix brand action.
- Home action, repurposed as the visible graph reset.
- Lines action, retained as a temporary compatibility bridge for curve styling.
- Cursor/status telemetry.

Matplotlib renderer policy: keep the original Home/Back/Forward/Pan/Zoom controls because they still act on the Matplotlib canvas.

## Implementation Summary

- Added a renderer-surface toolbar policy in `artisanlib.main`.
- Added `toolbar_callback_visible_for_surface()` to define which callbacks are visible on each renderer surface.
- Added `apply_toolbar_surface_policy()` so actions can be hidden without hard-coding UI object details into tests.
- Added `reset_pyqtgraph_toolbar_target()` and routed `VMToolbar.home()` through it when the active surface is `pyqtgraph-plot`.
- Preserved the existing recording-mode `zoom_follow` toggle after Home.
- Kept the Matplotlib toolbar behavior unchanged on `matplotlib-axis`.

## Verification

- `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_main.py::test_toolbar_callback_visibility_hides_legacy_matplotlib_nav_for_pyqtgraph test/unitary/artisanlib/test_main.py::test_apply_toolbar_surface_policy_hides_only_unsupported_pyqtgraph_actions test/unitary/artisanlib/test_main.py::test_reset_pyqtgraph_toolbar_target_syncs_current_graph_view test/unitary/artisanlib/test_main.py::test_reset_pyqtgraph_toolbar_target_ignores_matplotlib_surface -q`
- `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_main.py::test_update_plus_status_uses_cotrix_brand_and_hides_empty_subscription test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_gui_theme.py -q`
- `cd src && .venv/bin/python -m py_compile artisanlib/main.py artisanlib/canvas.py artisanlib/gui_theme.py`
- `cd src && .venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_main.py`
- `git diff --check`
- `cd src && QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_AUTORUN=1 ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=4 ARTISANZ_GUI_PERF_AUTORUN_INTERVAL_MS=40 ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-toolbar-policy-perf.jsonl ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-toolbar-policy.png .venv/bin/python artisan.py /Users/chengzhe/Projects/ArtisanZ/src/test/sanity/data/artisan/profile1.alog`

Latest result: focused policy tests produced `4 passed`; related toolbar/canvas/theme tests produced `29 passed`; compile, ruff, and diff checks passed. Screenshot smoke produced `/tmp/artisanz-toolbar-policy.png`.

## Remaining Follow-Up

The Lines action still depends on the legacy Matplotlib curve-style editor. The next toolbar-quality pass should replace it with a renderer-neutral style editor or PyQtGraph-aware curve panel, then make the toolbar entirely independent from Matplotlib navigation internals.
