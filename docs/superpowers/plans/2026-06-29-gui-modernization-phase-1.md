# GUI Modernization Phase 1 Implementation Plan

**Status:** Started on 2026-06-29.

## Goal

Modernize the PyQt6 Widgets interface without changing roast behavior, device I/O, plotting semantics, translations, reports, or profile serialization.

## Baseline Input

Automated profile redraw baseline on `test/sanity/data/artisan/profile1.alog` shows:

- `canvas.updateBackground`: highest total time.
- `canvas.redraw` and `canvas.redraw_keep_view`: highest single-call time.
- `canvas.updategraphics`: negligible in this profile-only scenario.

This means Phase 1 should avoid adding redraw work and should focus on static Widgets stylesheet improvements before renderer work.

## Tasks

- [x] Add a small theme-token module: `src/artisanlib/gui_theme.py`.
- [x] Add an application-level modern stylesheet for windows, menus, toolbars, groups, tabs, inputs, tables, scrollbars, and default buttons.
- [x] Add `ARTISANZ_LEGACY_UI=1` fallback.
- [x] Verify the automated profile redraw scenario after applying the stylesheet.
- [ ] Modernize event button styles without gradients.
- [ ] Modernize LCD surfaces and labels.
- [ ] Add screenshot review for OFF, profile-loaded, and event-button states.

## Verification

```bash
cd src
.venv/bin/python -m py_compile artisanlib/gui_theme.py artisanlib/main.py
.venv/bin/python -m pytest test/unitary/artisanlib/test_gui_theme.py -q
.venv/bin/python -m ruff check artisanlib/gui_theme.py artisanlib/main.py test/unitary/artisanlib/test_gui_theme.py
```

Automated profile redraw:

```bash
cd src
ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_AUTORUN=1 ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=16 ARTISANZ_GUI_PERF_AUTORUN_INTERVAL_MS=50 ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-gui-perf.jsonl QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" .venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-gui-perf.jsonl --sort-by max_ms --limit 20
```
