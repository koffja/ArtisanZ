---
phase: 1.27-visual-parity
reviewed: 2026-07-23T14:04:25Z
depth: deep
files_reviewed: 10
files_reviewed_list:
  - src/artisanlib/plot_curve_style_dialog.py
  - src/artisanlib/plot_pyqtgraph_adapter.py
  - src/artisanlib/plot_snapshot.py
  - src/artisanlib/plot_snapshot_extractor.py
  - src/artisanlib/main.py
  - src/test/unitary/artisanlib/test_plot_curve_style_dialog.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
  - src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_plot_snapshot.py
  - src/test/unitary/artisanlib/test_main.py
findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
status: issues_found
---

# Phase 1.27: Code Review Report

**Reviewed:** 2026-07-23T14:04:25Z  
**Depth:** deep  
**Files Reviewed:** 10  
**Status:** NEEDS PATCH

## Summary

Final review covered the five requested prior findings and current owned GUI changes.

Resolved:

- PyQtGraph Lines routing now requires the active `pyqtgraph-plot` surface and a live target (`src/artisanlib/main.py:821-825`).
- Style redraw captures and restores the active PyQtGraph view (`src/artisanlib/main.py:828-838`).
- Snapshot extraction now carries event marker shape, size, and width (`src/artisanlib/plot_snapshot_extractor.py:457-459`).

Remaining blocking warnings: configured event marker values are still rewritten by the adapter, Restore Defaults uses non-canonical colors, and two dialog labels bypass existing i18n contexts.

Focused verification passed with `src/.venv`:

- `test_plot_curve_style_dialog.py`: 4 passed
- `test_plot_pyqtgraph_adapter.py`: 28 passed
- `test_plot_snapshot_extractor.py`: 30 passed
- selected `test_main.py` toolbar/view tests: 6 passed
- `py_compile`: passed
- `git diff --check`: passed

System pytest was not used because it is pytest 8.4.2 while project config requires pytest 9.0. No broad tests run. No Critical or security findings.

## Warnings

### WR-01: PyQtGraph does not preserve all configured event marker shapes and widths

**File:** `src/artisanlib/plot_pyqtgraph_adapter.py:584-601`  
**Related extraction:** `src/artisanlib/plot_snapshot_extractor.py:457-459`

**Issue:** The snapshot now carries configuration, but the adapter still changes valid settings. `_event_value_marker_symbol()` maps legacy `*` and `H` to `o`, and maps `None` to a visible circle. The legacy event editor permits `None`, `o`, `s`, `p`, `D`, `*`, `h`, `H`, `+`, and `x` (`src/artisanlib/events.py:404-416`). The adapter also caps line width at `4.0`, while the legacy control permits `1..10` (`src/artisanlib/events.py:468-493`). A runtime check with `marker='*'`, `marker_size=14`, `line_width=10` produced `o`, `14.0`, `4.0`.

**Fix:** Use an explicit source-to-PyQtGraph symbol map (`'*' -> 'star'`, `D -> d`, and a deliberate no-marker path for `None`) and preserve the supported application ranges, e.g. marker size `1..14` and line width `1..10`. Add tests for `*`, `H`, `None`, and a width above `4.0`.

### WR-02: Restore Defaults uses the Morandi/current palette, not canonical Artisan curve colors

**File:** `src/artisanlib/plot_curve_style_dialog.py:34-38,179-190`

**Issue:** The dialog correctly no longer reads the current palette when restoring, but its constants are still `ET=#A76557`, `BT=#4E7180`, and `Delta BT=#90A1A8`. Canonical ArtisanZ curve defaults are `ET=#C0504D`, `BT=#3A7CA5`, `Delta ET=#D4943A`, and `Delta BT=#5B9BD5` (`src/artisanlib/main.py:20695-20698`; also `src/artisanlib/plot_snapshot_extractor.py:30-33`). Clicking Restore Defaults therefore resets to the wrong product defaults.

**Fix:** Define one shared canonical curve-default table and use it in `CURVE_STYLE_BINDINGS` and `_restore_defaults()`. Update the dialog test to assert the canonical values, not the current palette values.

### WR-03: New dialog labels do not consistently reuse existing i18n contexts

**File:** `src/artisanlib/plot_curve_style_dialog.py:71-74,101-106`

**Issue:** The `Curves` form row requests `QApplication.translate('Curves', 'Curves')`, but existing UI/catalog usage is `QApplication.translate('Tab', 'Curves')` (`src/artisanlib/colors.py:551`; `src/translations/artisan_zh_CN.ts:19381-19609`). For `Delta ET` and `Delta BT`, the `else` branch inserts raw English strings; existing UI composes the delta prefix with translated `ET`/`BT` labels (`src/artisanlib/curves.py:366-371`). These labels fall back to English in translated builds.

**Fix:** Reuse `Tab` for the `Curves` row and construct delta labels with the existing delta-prefix plus the existing `Label` translation for `ET`/`BT`. Add a focused context/source assertion if this dialog remains independently maintained.

## Resolved Prior Findings

- **Active target gating:** fixed and covered by `test_pyqtgraph_curve_style_editor_requires_live_target` (`src/test/unitary/artisanlib/test_main.py:3456-3465`).
- **View preservation after redraw:** fixed and covered by `test_pyqtgraph_curve_style_redraw_restores_active_view` (`src/test/unitary/artisanlib/test_main.py:3468-3497`).
- **Event marker extraction:** shape, size, and width now cross the snapshot boundary; adapter fidelity issue remains WR-01.
- **Restore Defaults current-palette bug:** current palette is no longer used by `_restore_defaults`; canonical constants remain wrong, tracked as WR-02.
- **i18n context reuse:** `Lines`, `Line style`, `Width`, and `Line Color` reuse existing contexts; `Curves`, `Delta ET`, and `Delta BT` still need WR-03.

---

_Reviewed: 2026-07-23T14:04:25Z_  
_Reviewer: Codex (gsd-code-reviewer)_  
_Depth: deep_
