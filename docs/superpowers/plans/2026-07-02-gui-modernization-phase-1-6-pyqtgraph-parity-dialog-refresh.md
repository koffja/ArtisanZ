# GUI Modernization Phase 1.6 PyQtGraph Parity and Dialog Refresh Plan

> **For agentic workers:** Use `superpowers:executing-plans` for direct implementation, and request code review before marking the phase complete.

**Goal:** Make the default PyQtGraph main screen visually credible against the legacy Matplotlib view, then reduce the old desktop-tool feeling in the most-used settings dialogs.

**Architecture:** Keep the existing PyQt6 Widgets runtime. Improve PyQtGraph through the existing snapshot/widget adapter boundary, not by mutating Matplotlib state from the new renderer. Improve dialogs first through theme tokens and safe selectors, then by targeted per-dialog layout work.

---

## Current Progress

- [x] Default renderer is `pyqtgraph-snapshot`, with Matplotlib retained through `ARTISANZ_RENDERER_ID=matplotlib-snapshot`.
- [x] Historical profiles and live frames render in the embedded PyQtGraph widget.
- [x] RoR renders on the same PyQtGraph plot with a linked right-side axis.
- [x] Existing time, temperature, and RoR tick-step settings are applied to PyQtGraph.
- [x] Config > Axes includes Minutes/Seconds time-label mode.
- [x] Background ET/BT and Delta ET/BT curves, projection curves, phase bands, and main/special/background event labels are represented in the snapshot path.
- [x] Gridlines now use a dedicated PyQtGraph grid overlay with visible alpha and configured tick spacing.
- [x] Default phase bands now use soft Morandi colors instead of barely visible gray defaults.
- [x] Right LCD telemetry no longer uses an outer visual frame; only the value surface is drawn.
- [x] Standard dialogs now inherit a flatter light Morandi base style.

## Task 1: Grid and Phase Visual Verification

**Files:**
- Modify: `src/artisanlib/plot_pyqtgraph_widget.py`
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Modify: `src/artisanlib/plot_snapshot_extractor.py`
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_widget.py`
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`

- [x] Use a dedicated `GridItem` overlay instead of faint built-in PyQtGraph grid rendering.
- [x] Respect x/y grid visibility flags.
- [x] Respect existing x/y tick-step settings, including temperature step.
- [x] Make phase bands visible above the plot background and below curves/grid.
- [x] Preserve user-defined phase colors when they are not default grayscale values.
- [x] Capture screenshot evidence for the improved phase bands in the main window and explicit grid/phase rendering in the PyQtGraph target.

## Task 2: LCD Visual Stabilization

**Files:**
- Modify: `src/artisanlib/gui_theme.py`
- Modify: `src/artisanlib/main.py`
- Modify: `src/test/unitary/artisanlib/test_gui_theme.py`
- Modify: `src/test/unitary/artisanlib/test_main.py`

- [x] Remove the visible outer card frame from LCD containers.
- [x] Keep label/value padding inside the fixed-width telemetry column.
- [x] Draw a self-contained value surface so it cannot detach from a parent rounded rectangle.
- [x] Add/update selector tests for transparent `lcdSurface` and `telemetryCard` containers.
- [ ] Capture a long-Chinese-label screenshot proving the telemetry column stays fixed and visually aligned.

## Task 3: Dialog Base Refresh

**Files:**
- Modify: `src/artisanlib/gui_theme.py`
- Modify: `src/test/unitary/artisanlib/test_gui_theme.py`

- [x] Add light Morandi dialog background tokens.
- [x] Apply flatter styling to `QDialog`, `QMessageBox`, `QFileDialog`, and dialog buttons.
- [x] Add tests that assert the dialog selectors exist in the modern stylesheet.
- [ ] Capture Config > Axes and Config > Curves screenshots.

## Task 4: Remaining PyQtGraph Overlay Parity

**Files:**
- Modify: `src/artisanlib/plot_snapshot.py`
- Modify: `src/artisanlib/plot_snapshot_extractor.py`
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`

- [ ] Add extra-device background curves and verify their legend/color/visibility behavior.
- [ ] Add event value rail/bar rendering for the existing event graph modes.
- [ ] Add event label overlap avoidance and richer label placement.
- [ ] Add AUC guide/area visuals.
- [ ] Add roast-analysis overlays that still exist only in the Matplotlib path, including masks/statistics/guide marks.
- [ ] Add charge-target annotations when charge-target data is active.
- [ ] Improve projection line visual differentiation and verify RoR projection placement.
- [ ] Define the export/report compatibility decision: Matplotlib-only fallback, PyQtGraph export adapter, or explicit hybrid export.

## Task 5: Per-Dialog Modernization

**Files:** to be narrowed per dialog after inspection.

- [ ] Modernize Config > Axes first because it is now part of the PyQtGraph renderer controls.
- [ ] Modernize Config > Curves second because curve visibility/color controls determine PyQtGraph parity.
- [ ] Modernize Events, Devices, Alarms, and Roasting Properties after screenshot review.
- [ ] Avoid nested cards and heavy gray widget wells.
- [ ] Preserve all current settings persistence, validation, shortcuts, and translations.

## Verification

- [x] `python3 -m py_compile` for touched Python files.
- [x] Focused pytest for plot snapshot, PyQtGraph widget/adapter, theme, and main UI selector tests.
- [x] `ruff check` for touched files.
- [x] PyQtGraph smoke for nonblank rendering.
- [x] Screenshot evidence for main-window phase bands and explicit PyQtGraph grid/phase rendering.
- [ ] Screenshot evidence for profile, live simulator, background profile, event-heavy profile, long Chinese LCD labels, Config > Axes, and Config > Curves.

## Evidence

- Main-window phase-band screenshot: `/tmp/artisanz-phase16-grid-phase-v2.png`
- Explicit PyQtGraph grid/phase screenshot: `/tmp/artisanz-phase16-grid-unit.png`
- Main-window profile redraw metrics from `/tmp/artisanz-phase16-grid-phase-v2.jsonl`: `redraw max=87.658ms avg=53.171ms`, `updateBackground max=30.605ms avg=24.606ms`, `updategraphics max=0.006ms avg=0.003ms`.

## Exit Gate

Phase 1.6 is complete when the default PyQtGraph view has visible gridlines, visible phase bands, high-value event/background overlays, stable LCD telemetry, and the first two settings dialogs no longer read as unstyled gray desktop forms.
