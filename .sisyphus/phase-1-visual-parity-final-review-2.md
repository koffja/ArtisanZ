---
phase: 1.27-visual-parity
reviewed: 2026-07-23T14:14:17Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - src/artisanlib/plot_curve_style_dialog.py
  - src/artisanlib/plot_pyqtgraph_adapter.py
  - src/artisanlib/plot_snapshot.py
  - src/artisanlib/plot_snapshot_extractor.py
  - src/artisanlib/main.py
  - src/artisanlib/plot_style_defaults.py
  - src/test/unitary/artisanlib/test_plot_curve_style_dialog.py
  - src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
  - src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
  - src/test/unitary/artisanlib/test_plot_snapshot.py
  - src/test/unitary/artisanlib/test_main.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
verdict: PASS
---

# Phase 1.27: Visual Parity Final Review 2

**Reviewed:** 2026-07-23T14:14:17Z
**Depth:** deep
**Files Reviewed:** 11
**Status:** PASS

## Summary

Current owned changes reviewed. All prior findings resolved. No Critical, Warning, or Info findings.

- Active target gating: `src/artisanlib/main.py:821-825` requires both the PyQtGraph surface and a non-null live target before opening the renderer-neutral editor. Fallback clears the target in `src/artisanlib/canvas.py:5816-5835` and `5840-5848`, so Matplotlib routing remains reachable.
- View restore: `src/artisanlib/main.py:828-838` captures the renderer view before redraw and restores it in `finally`. Regression test: `src/test/unitary/artisanlib/test_main.py:3468-3497`.
- Event markers: `src/artisanlib/plot_snapshot_extractor.py:440-473` carries marker, size, and width settings. `src/artisanlib/plot_pyqtgraph_adapter.py:571-607` preserves `*` via `star`, `H` via the supported hexagon symbol, and `None` as no marker; valid legacy ranges remain size `1..14` and width `1..10`. Tests cover `*`, `H`, `None`, maximum size, and maximum width at `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py:923-969`.
- Canonical colors: `src/artisanlib/plot_style_defaults.py:7-12` is used by both `src/artisanlib/plot_curve_style_dialog.py:22,39-43,187-198` and `src/artisanlib/plot_snapshot_extractor.py:28-35`. Restore Defaults test confirms `BT=#3A7CA5` at `src/test/unitary/artisanlib/test_plot_curve_style_dialog.py:76-90`.
- i18n: `Curves` uses the existing `Tab` context at `src/artisanlib/plot_curve_style_dialog.py:102-106`. `Delta ET` and `Delta BT` reuse the existing delta prefix plus `Label` translations for `ET`/`BT` at `src/artisanlib/plot_curve_style_dialog.py:120-125`, matching `src/artisanlib/curves.py:366-371`. Existing catalog entries were verified in `src/translations/artisan_zh_CN.ts:12055-12085` and `19608`.

## Verification

- `test_plot_curve_style_dialog.py`, `test_plot_pyqtgraph_adapter.py`, `test_plot_snapshot_extractor.py`: **64 passed**
- Focused `test_main.py`: **3 passed**
- Snapshot/live-frame/Matplotlib compatibility tests: **38 passed**
- PyQtGraph/WebSocket smoke tests: **8 passed**
- `py_compile`: passed
- `git diff --check`: passed

An explicit Ruff run also reports the pre-existing, unrelated `F401` at `src/artisanlib/main.py:28677`; that line is outside the current owned diff and is not a review finding.

---

_Reviewed: 2026-07-23T14:14:17Z_
_Reviewer: Codex (gsd-code-reviewer)_
_Depth: deep_
