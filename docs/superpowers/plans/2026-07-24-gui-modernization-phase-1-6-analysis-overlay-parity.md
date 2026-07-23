# GUI Modernization Phase 1.6 Analysis Overlay Parity Plan

**Status:** Implemented, reviewed, and regression-tested 2026-07-24

**Goal:** Restore roast-analysis visuals lost during the PyQtGraph migration without coupling the new renderer to Matplotlib objects.

## Scope

- Preserve the legacy eight analysis-mask regions: four full-height excluded ranges plus four 2.5% top/bottom interval edge bands.
- Carry curve-fit and analysis interval guides through the renderer-neutral snapshot contract.
- Render segment and analysis result text boxes with axes-fraction positions, Morandi background, translated text, and stable z-order.
- Preserve independent statistics flags: time/label (`statisticsflags[0]`), phase bar (`[1]`), and delta temperature (`[6]`).
- Clear all analysis state during reset, profile load, background removal, and `clearResults()`.

## Implementation

- `plot_snapshot.py`: added immutable `AnalysisMaskSnapshot` and `StatisticsBackgroundSnapshot` contracts.
- `plot_snapshot_extractor.py`: extracts valid finite intervals, palette/opacity, result text, positions, phase flags, and Qt-translated phase labels.
- `plot_pyqtgraph_adapter.py`: renders and removes masks, edge bands, result boxes, and stable z-order overlays.
- `canvas.py`: owns the new state in `__slots__` and initializes/clears it with the canvas lifecycle.
- `main.py`: writes all analysis state before the PyQtGraph redraw so the first result frame is complete.

## Verification

- Focused GUI suite: `350 passed, 1 skipped, 2 warnings`.
- `py_compile` passed for all touched runtime modules.
- `git diff --check` passed.
- Independent review: `.sisyphus/phase-analysis-overlay-review-pass.md` (`PASS`, P0/P1/P2/P3 all zero).

## Remaining Follow-up

- Matplotlib-style draggable/editable analysis result boxes are not part of this bounded renderer parity slice.
- Native-window screenshot evidence for saved-profile analysis and long translated result text remains a visual QA gate.
- Report/export remains Matplotlib-backed by design.
