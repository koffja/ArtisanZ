---
phase: 1-visual-parity
reviewed: 2026-07-23T00:00:00Z
depth: deep
files_reviewed: 5
files_reviewed_list:
  - src/artisanlib/main.py
  - src/artisanlib/plot_pyqtgraph_adapter.py
  - src/artisanlib/plot_curve_style_dialog.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
  - src/test/unitary/artisanlib/test_plot_curve_style_dialog.py
findings:
  critical: 0
  warning: 5
  info: 2
  total: 7
status: issues_found
verdict: NEEDS_PATCH
---

# Phase 1 Visual Parity Review

**Reviewed:** 2026-07-23
**Depth:** deep
**Files Reviewed:** 5
**Status:** NEEDS_PATCH

## Summary

Reviewed the uncommitted PyQtGraph event-marker change, renderer-neutral curve-style dialog, toolbar routing, Cotrix `brand_width`, and related tests. No critical security issue found. Basic syntax check passed. Functional parity is not ready to PASS because fallback routing, view preservation, event-marker configuration, restore-default semantics, and i18n need fixes.

## Warnings

### WR-01: Matplotlib fallback still opens the PyQtGraph dialog

**File:** `src/artisanlib/main.py:1463-1465`

**Issue:** Routing checks only `qmc.plot_renderer_selection.plugin.surface`. PyQtGraph target creation/live update can fail and fall back to the visible Matplotlib canvas while the selection object still reports `pyqtgraph-plot` (`canvas.py:5812-5815`, `5840-5848`). In that state, Lines opens `CurveStyleDialog`; the required Matplotlib `figureoptions` path is unreachable.

**Fix:** Route on the active target, not only the requested surface. For example, require `renderer_surface_from_qmc(self.qmc) == 'pyqtgraph-plot'` and a live `qmc.plot_pyqtgraph_target`, or update a single active-surface state whenever fallback occurs.

### WR-02: Confirming style changes can reset the user's PyQtGraph view

**File:** `src/artisanlib/main.py:1504-1509`

**Issue:** The callback calls `qmc.redraw_keep_view`, but that method preserves the hidden Matplotlib axes. Its final `sync_pyqtgraph_view_from_canvas()` resets PyQtGraph from `live_*_axis_snapshot()` (`canvas.py:10087-10102`, `6009-6023`), not from the current PyQtGraph `ViewBox`. A user zoom/pan view can therefore jump after pressing OK.

**Fix:** Capture `target.renderer.export_view_state()` before applying styles and restore that state after redraw, or add a PyQtGraph-specific redraw path that preserves the active renderer view.

### WR-03: New markers ignore configured event marker settings

**File:** `src/artisanlib/plot_pyqtgraph_adapter.py:584-587`

**Issue:** `symbol`, size, and pen width are hard-coded. Existing application settings provide per-event `EvalueMarker`, `EvalueMarkerSize`, and `Evaluelinethickness` (`canvas.py:1989-1991`), but `EventValueSnapshot` carries none of them. PyQtGraph therefore cannot match user-configured Matplotlib/legacy event markers; the fourth default also differs (`D` versus `d`).

**Fix:** Extend the snapshot/extractor contract with marker, marker size, and line width, then pass those values to `ScatterPlotItem`. Keep opacity clamping as implemented.

### WR-04: Restore Defaults does not restore event-curve colors

**File:** `src/artisanlib/plot_curve_style_dialog.py:186-189`

**Issue:** The method first selects `binding.default_color`, then replaces it with the current palette value whenever that key exists. Pressing Restore Defaults therefore leaves custom colors unchanged; only style and width reset.

**Fix:** Remove the palette override and use one canonical default-color table. If the product defaults are the migrated palette rather than the literals in this file, use that canonical table consistently.

### WR-05: New dialog strings use missing or mismatched translation contexts

**File:** `src/artisanlib/plot_curve_style_dialog.py:73-81,96,101-104,168`

**Issue:** The inspected `artisan_zh_CN.ts` and `artisan_zh_TW.ts` catalogs contain `Restore Defaults` under `Button`/`Curves`/`HelpDlg`, `Line color` under `Tooltip`, and `Line style`/`Width` under `Label`; the new code requests `Restore Defaults` and dialog-title `Line color` under `Toolbar`, and form-row `Line color` under `Label`. `Curve`, `Delta ET`, `Delta BT`, and the four style names are also not present under the requested contexts. Those controls fall back to English in translated builds.

**Fix:** Add all new source/context pairs to the translation sources and regenerate every `.ts`/`.qm`, or consistently reuse existing contexts whose translations are semantically correct. Add a test that checks the requested context/source pairs exist.

## Info

### IN-01: Dialog test coverage is incomplete

**File:** `src/test/unitary/artisanlib/test_plot_curve_style_dialog.py:31-58`

**Issue:** Tests cover one BT style change and basic cancel behavior only. No coverage for ET/Delta ET/Delta BT, color changes, Restore Defaults, selection switching while edits are pending, callback failure, or PyQtGraph-to-Matplotlib fallback routing.

**Fix:** Add parameterized binding tests plus focused tests for color, defaults, selection capture, routing, and view-state preservation.

### IN-02: Adapter tests cover one marker type and one coordinate case

**File:** `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py:893-939`

**Issue:** Tests do not cover event types 0/2/3, values already inside the temperature range, percentage mapping, clamping, configured marker settings, or renderer add/remove lifecycle.

**Fix:** Parameterize event type and coordinate cases; add an integration-style test asserting one item per event is added and removed on snapshot replacement.

## Verification

- `python3 -m py_compile` for the five reviewed Python files: PASS.
- `git diff --check` for the tracked phase changes: PASS.
- Targeted pytest: BLOCKED. Environment has `pytest 8.4.2` while project config requires `pytest-9.0`, and the active Python 3.9 environment has no `PyQt6`.
- Thread review: dialog and callback execute on the GUI thread; no new worker-thread access found. Direct redraw still needs the view-preservation fix above.
- Security review: no new injection, credential, deserialization, or filesystem vulnerability found.

---

_Reviewed: 2026-07-23_
_Reviewer: Codex (gsd-code-reviewer)_
_Depth: deep_
