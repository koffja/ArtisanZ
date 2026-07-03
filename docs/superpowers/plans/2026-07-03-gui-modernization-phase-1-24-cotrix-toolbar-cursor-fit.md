# Phase 1.24: Cotrix Toolbar and Cursor Fit Pass

## Objective

Fix the two visible regressions reported after Phase 1.23: PyQtGraph cursor telemetry clipped at the bottom of the toolbar, and the top toolbar still reading as an old Artisan Plus/Matplotlib toolbar rather than a Cotrix roast-control surface.

## Design Direction

Subject: Cotrix roast control for operators who need quick graph orientation while monitoring a roast.

Signature element: a Cotrix brand entry at the left edge of the toolbar, replacing the legacy plus sign. The rest of the toolbar stays quiet and utilitarian: compact icon buttons, no decorative separator block, and no empty subscription placeholder.

## Implementation Summary

- Replaced the visible plus-service icon with `cotrix.svg` / `white_cotrix.svg`.
- Changed the service action label to `Cotrix` while keeping the existing backend callback path.
- Kept subscription behavior available internally but hid the subscription action when it has no active icon, eliminating the large blank gap between the brand entry and graph navigation.
- Removed the old toolbar separator entry that rendered as a gray square in the current Qt toolbar style.
- Reworked toolbar button sizing and hover/checked states for a flatter, more modern control strip.
- Reduced `locLabel` font scaling, set a minimum height, and vertically centered the label.
- Changed PyQtGraph cursor messages from a two-line `<PRE>` block to a single-line readout: `time   BT value   RoR value`.

## Verification

- `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py::test_update_plus_status_uses_cotrix_brand_and_hides_empty_subscription -q`
- `cd src && .venv/bin/python -m py_compile artisanlib/main.py artisanlib/canvas.py artisanlib/gui_theme.py`
- `cd src && .venv/bin/python -m ruff check artisanlib/main.py artisanlib/canvas.py artisanlib/gui_theme.py test/unitary/artisanlib/test_canvas_renderer_selection.py test/unitary/artisanlib/test_gui_theme.py test/unitary/artisanlib/test_main.py`
- `git diff --check`
- `cd src && QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_AUTORUN=1 ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=4 ARTISANZ_GUI_PERF_AUTORUN_INTERVAL_MS=40 ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-toolbar-redesign-perf.jsonl ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-toolbar-redesign.png .venv/bin/python artisan.py /Users/chengzhe/Projects/ArtisanZ/src/test/sanity/data/artisan/profile1.alog`

Latest result: `29 passed`, `py_compile` passed, `ruff check` passed, `git diff --check` passed, and the screenshot smoke produced `/tmp/artisanz-toolbar-redesign.png`.

## Remaining Follow-Up

The toolbar still keeps Home/Back/Forward/Pan/Zoom because those are valid on the Matplotlib compatibility path. The next deliberate step is a PyQtGraph-native toolbar policy: replace Matplotlib navigation actions with controls that act on the visible PyQtGraph surface, such as fit view, reset roast window, and interaction mode.
