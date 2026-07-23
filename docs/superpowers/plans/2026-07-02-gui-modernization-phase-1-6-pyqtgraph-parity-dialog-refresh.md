# GUI Modernization Phase 1.6 PyQtGraph Parity and Dialog Refresh Plan

> **For agentic workers:** Use `superpowers:executing-plans` for direct implementation, and request code review before marking the phase complete.

**Goal:** Make the default PyQtGraph main screen visually credible against the legacy Matplotlib view, then reduce the old desktop-tool feeling in the most-used settings dialogs.

**Architecture:** Keep the existing PyQt6 Widgets runtime. Improve PyQtGraph through the existing snapshot/widget adapter boundary, not by mutating Matplotlib state from the new renderer. Improve dialogs first through theme tokens and safe selectors, then by targeted per-dialog layout work.

> **2026-07-24 implementation update:** Extra-device background curve extraction, fixed-width dialog control hardening, nested-layout margin preservation, roast-analysis mask/statistics/guide parity, and snapshot-owned phase/event overlay parity are implemented and independently reviewed. Real themed screenshots now cover long Chinese LCD labels and Config > Axes/Curves. The remaining follow-up is: draggable/editable analysis result boxes, charge-target rounded-corner/deeper interaction polish, drag/edit event interactions, and report/export parity remains Matplotlib-backed by design.

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
- [x] PyQtGraph snapshots now carry foreground/background event value rails plus AUC, BBP, and charge-target guide lines when source data exists.
- [x] `PyQtGraphSnapshotRenderer` now renders event value rails and guide lines through the snapshot adapter boundary.
- [x] Axes, Curves, Events, and Alarms dialogs now have scoped modern dialog roles with Morandi group-box/tab/table/header/input/button styling.
- [x] Extra-device background curves preserve legacy 1-based odd/even selection, raw/smoothed data, CHARGE/DROP masking, style, opacity, color, and temperature/RoR axis routing.
- [x] Axis value controls opt into width expansion only where time/temperature values need it; ordinary fixed-width controls and combo popups remain bounded.
- [x] Workspace Status now exposes a concrete action hint per workspace mode.
- [x] Plugin registry now has typed renderer/report/analyzer/filter/profile-comparison categories while keeping only renderer plugins instantiable.

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
- [x] Capture a long-Chinese-label screenshot proving the telemetry column stays fixed and visually aligned.

## Task 3: Dialog Base Refresh

**Files:**
- Modify: `src/artisanlib/gui_theme.py`
- Modify: `src/test/unitary/artisanlib/test_gui_theme.py`

- [x] Add light Morandi dialog background tokens.
- [x] Apply flatter styling to `QDialog`, `QMessageBox`, `QFileDialog`, and dialog buttons.
- [x] Add tests that assert the dialog selectors exist in the modern stylesheet.
- [x] Capture Config > Axes and Config > Curves screenshots.

## Task 4: Remaining PyQtGraph Overlay Parity

**Files:**
- Modify: `src/artisanlib/plot_snapshot.py`
- Modify: `src/artisanlib/plot_snapshot_extractor.py`
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`

- [x] Add extra-device background curves and verify their color/visibility, style, opacity, masking, selection, and axis-routing behavior. Background curves remain excluded from the compact main legend, matching the existing adapter policy.
- [x] Add event value rail/bar rendering for foreground/background event values available in the snapshot path.
- [x] Add event label overlap avoidance and richer label placement. Closed by Phase 1.9 (`docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-9-pyqtgraph-event-auc-parity.md`) clustered event-label row placement; edge anchor hardened by Phase 1.10. Evidence: `_event_label_row` `src/artisanlib/plot_pyqtgraph_adapter.py:717`, `_event_label_anchor:707`.
- [x] Add AUC guide line visuals when `AUCguideFlag` and `AUCguideTime` are active.
- [x] Add AUC area fill visuals. Closed by Phase 1.9 AreaFillSnapshot. Evidence: `AreaFillSnapshot` `src/artisanlib/plot_snapshot.py:90`, `_auc_area_fill` `src/artisanlib/plot_snapshot_extractor.py:688`, `_default_area_item_factory` `src/artisanlib/plot_pyqtgraph_adapter.py:580` with `PlotDataItem(fillLevel=area.baseline, brush=...)`.
- [x] Add BBP and charge-target guide line visuals when source data exists.
- [x] Add roast-analysis masks, analysis interval guides, and statistics result boxes through the renderer-neutral snapshot path. Full draggable/editable box parity remains follow-up. Tracking: `docs/superpowers/plans/2026-07-24-gui-modernization-phase-1-6-analysis-overlay-parity.md`.
- [x] Add full charge-target annotation text/callout parity. Closed by Task Group C of `docs/superpowers/plans/2026-07-04-phase-1-6-closure-workspace-switcher-charge-target-annotation.md`; rounded-corner and deeper interaction polish remain follow-up.
- [x] Improve projection line visual differentiation and verify RoR projection placement. Projection curves now preserve legacy `-.`, `8.0`, `0.3` styling, route Delta projections to the RoR plot only when `delta_ax` exists, use projection z-order `45`, and remain excluded from the compact legend. Review: `.sisyphus/phase-projection-parity-review.md`.
- [x] Suppress duplicate legacy phase/event overlay managers when the snapshot renderer owns static overlays, then restore the complete snapshot semantics: drying/Maillard/development time ranges (including partial live-roast ranges), full-height main-event lines, and empty-state cleanup for legacy targets. This removes extra default red/caramel vertical blocks and duplicate event lines from saved-profile redraws while retaining the legacy manager path for non-snapshot targets. Verification: `131 passed, 2 warnings`; cross-dialog/renderer parity suite: `244 passed, 1 skipped, 2 warnings`.
- [x] Define the export/report compatibility decision: explicit hybrid. Matplotlib stays default for `roastReport()` and PDF/SVG/PNG/JPEG Save Graph; PyQtGraph PNG is opt-in via `File > Save Graph > PyQtGraph PNG...` (Phase 1.17 `src/artisanlib/plot_user_export.py`); `plot_report_export.py` provides report-image comparison (Phase 1.18). See closure plan `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-4-6-closure.md` Task 1 line 46.

## Task 5: Per-Dialog Modernization

**Files:** to be narrowed per dialog after inspection.

- [x] Apply scoped modern dialog roles to Axes, Curves, Events, and Alarms.
- [x] Add Morandi group-box, tab, table, header, input, and button styling under `modernDialog=true`.
- [x] Modernize Config > Axes layout internals beyond scoped styling because it is now part of the PyQtGraph renderer controls. Control rows now use aligned grid layouts, stable section properties, and explicit inter-column spacing.
- [x] Modernize Config > Curves layout internals beyond scoped styling because curve visibility/color controls determine PyQtGraph parity. Untitled helper cards are unframed, all seven tab pages have stable outer spacing and the same modern tab-page marker, and semantic group sections use the flat Axes/Curves role treatment. The Analyze-page margin typo was also corrected.
- [x] Modernize Devices and Roasting Properties (scoped visual role layer). Closed by Phase 1.12 dense-dialog polish: `modernDialogRole="devices"` `src/artisanlib/devices.py:54`, `modernDialogRole="roast_properties"` `src/artisanlib/roast_properties.py:703`, dense table/header QSS rules at `src/artisanlib/gui_theme.py:512-526`. Per-panel structural simplification remains future work per the Phase 1.12 plan's explicit non-goals.
- [x] Avoid nested cards and heavy gray widget wells. Axes/Curves semantic sections now use transparent surfaces and hairline separators; the untitled Plotter helper container is a plain widget.
- [x] Preserve all current settings persistence, validation, shortcuts, and translations. Non-regression verified: `QSettings` calls intact in `axis.py:487,969`, `curves.py` (8 occurrences), `devices.py` (14 occurrences); `QIntValidator`/`QRegularExpressionValidator` chains intact; `QApplication.translate` used throughout. Phase 1.11 and 1.12 plans explicitly list preservation as scope.

## Verification

- [x] `python3 -m py_compile` for touched Python files.
- [x] Focused pytest for plot snapshot, PyQtGraph widget/adapter, theme, and main UI selector tests.
- [x] `ruff check` for touched files.
- [x] PyQtGraph smoke for nonblank rendering.
- [x] Screenshot evidence for main-window phase bands and explicit PyQtGraph grid/phase rendering.
- [x] Focused tests cover event value rails, guide extraction/rendering, analysis masks/statistics, scoped dialog properties/selectors, workspace action hints, and typed plugin categories.
- [x] Current parity/dialog slice verification: `120 passed, 1 skipped`; final independent review: `.sisyphus/phase-1-6-1-12-final-review.md` (P0/P1/P2/P3 all zero).
- [x] Analysis-overlay slice verification: `350 passed, 1 skipped, 2 warnings`; final independent review: `.sisyphus/phase-analysis-overlay-review-pass.md` (P0/P1/P2/P3 all zero).
- [x] Screenshot evidence for profile, live simulator, background profile, event-heavy profile, analysis overlays, long Chinese LCD labels, Config > Axes, and Config > Curves.

## Evidence

- Main-window phase-band screenshot: `/tmp/artisanz-phase16-grid-phase-v2.png`
- Explicit PyQtGraph grid/phase screenshot: `/tmp/artisanz-phase16-grid-unit.png`
- Main-window profile redraw metrics from `/tmp/artisanz-phase16-grid-phase-v2.jsonl`: `redraw max=87.658ms avg=53.171ms`, `updateBackground max=30.605ms avg=24.606ms`, `updategraphics max=0.006ms avg=0.003ms`.
- Closure code evidence: `GuideLineSnapshot`, `EventValueSnapshot`, scoped dialog roles, workspace `actionHint`, and typed plugin categories are covered by focused unit tests. Export/report compatibility remains intentionally Matplotlib-backed.
- Dialog visual evidence: `/tmp/artisanz-phase16-long-lcd-column.png`, `/tmp/artisanz-phase16-axes-dialog-final.png`, and `/tmp/artisanz-phase16-curves-dialog-final.png` were captured from real `ApplicationWindow` dialogs with `modern_application_stylesheet()`. Focused theme/dialog result: `39 passed, 1 skipped`. Nested row margins now remain intact; the Axes time-step combo no longer uses the macOS native width cap.

## Exit Gate

Phase 1.6 high-value parity is closed when the default PyQtGraph view has visible gridlines, visible phase bands, event labels, event value rails, AUC/BBP/charge-target guide lines, analysis masks/statistics, stable LCD telemetry, and scoped modern chrome for Axes/Curves/Events/Alarms. Full export parity, draggable analysis result boxes, drag/edit event interactions, and real-device OpenGL validation remain future gates rather than hidden unfinished work.
