# Phase 1.28: Opt-In PyQtGraph Report Graph Handoff

## Objective

Validate the renderer-neutral PyQtGraph snapshot path in the real roast HTML/PDF report flow while preserving the current Matplotlib default and automatic fallback.

## Scope

- Add a small report graph renderer selector with source override and environment override.
- Render only the report's main roast graph through PyQtGraph when explicitly enabled.
- Keep the flavor chart, report template, PDF conversion, and Matplotlib default unchanged.
- Fall back to the existing Matplotlib SVG path when PyQtGraph export is unavailable or fails.
- Add focused resolver tests and saved-profile export evidence.

## Execution Checklist

- [x] Add renderer selector and PyQtGraph report export helper.
- [x] Integrate the guarded branch into `roastReport()`.
- [x] Add resolver and fallback regression tests.
- [x] Validate a saved `.alog` profile through the PyQtGraph report graph path.
- [x] Run independent code review and patch findings.
- [x] Commit only owned files after review passes.

## Review Gate

The phase is complete only when the default renderer remains Matplotlib, the explicit PyQtGraph path writes a nonblank graph asset, and a simulated export failure reaches the Matplotlib fallback without changing report generation behavior.

## Completion Evidence

- Final independent review: `.sisyphus/phase-1-28-report-graph-review-2.md` — PASS, 0 findings.
- Focused report/export suite: 18 passed.
- Saved `tmp/TEST012.alog` snapshot with explicit `ARTISANZ_REPORT_GRAPH_RENDERER=pyqtgraph`: nonblank `roastlog-graph.png`, 95,140 bytes, 3,139 sampled non-background pixels, 18 temperature items, 2 RoR items, 29 event items.
- Default renderer check: Matplotlib SVG path selected when no override is present.
- Blank-output injection: automatically falls back to Matplotlib SVG.
- Static checks: `py_compile`, targeted `ruff check`, and `git diff --check` passed.
- Closed: 2026-07-23.
