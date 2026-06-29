# GUI Modernization Phase 1 Implementation Plan

**Status:** Main-screen visual first pass completed on 2026-06-29.

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
- [x] Modernize event button styles without gradients.
- [x] Modernize LCD surfaces and labels.
- [x] Add screenshot review for OFF, profile-loaded, and event-button states.

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
ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_AUTORUN=1 ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=16 ARTISANZ_GUI_PERF_AUTORUN_INTERVAL_MS=50 ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-gui-perf.jsonl ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-phase1.png QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" .venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
.venv/bin/python -m artisanlib.performance_report /tmp/artisanz-gui-perf.jsonl --sort-by max_ms --limit 20
```

## 2026-06-29 Verification Result

- Focused tests passed: `test_gui_theme.py`, `test_event_button_style.py`.
- `py_compile` passed for `gui_theme.py`, `event_button_style.py`, `widgets.py`, and `main.py`.
- `ruff check` passed for changed GUI/theme/test files.
- Profile-loaded screenshot: `/tmp/artisanz-phase1.png`.
- OFF screenshot: `/tmp/artisanz-phase1-off.png`.
- Profile-loaded metrics after event/LCD styling: `updateBackground max=156.639ms avg=65.746ms`; `redraw max=138.665ms avg=84.735ms`; `redraw_keep_view max=127.508ms avg=81.386ms`; `updategraphics max=0.007ms avg=0.002ms`.
- OFF metrics: `redraw max=95.335ms avg=81.990ms`; `updateBackground max=83.124ms avg=55.925ms`; `redraw_keep_view max=76.211ms avg=73.894ms`; `updategraphics max=0.006ms avg=0.002ms`.
- Screenshot review: no obvious overlap or text clipping in the 800x533 offscreen main-window capture. Event buttons use flat states; LCD side panels have clearer surface boundaries.

## 2026-06-29 LCD Value Surface Correction

- Fixed nested LCD value surfaces so the inner numeric display uses square top corners and rounded bottom corners.
- Aligned the inner LCD value display with the bottom of the outer LCD frame by removing the frame's bottom content gap.
- Added `lcd_value_stylesheet()` and focused tests to prevent the older `border-radius:4` inline LCD styles from returning in color refresh paths.
- START-state screenshot reviewed at `/tmp/artisanz-lcd-fix.png`.
