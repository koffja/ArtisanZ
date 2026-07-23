# Phase 1.27: Event Value and Renderer-Neutral Curve Style Finish

## Objective

Finish two remaining visual regressions in the default PyQtGraph surface:

- Dense event values remain readable without becoming solid vertical color blocks.
- The toolbar Lines action edits visible curve styles without opening the Matplotlib-only editor.

## Scope

- Keep the existing snapshot contract and Matplotlib compatibility path.
- Replace PyQtGraph event-value stems with compact value markers.
- Preserve event opacity semantics across both renderers.
- Add a small renderer-neutral ET/BT/Delta ET/Delta BT style dialog.
- Keep the existing Matplotlib `figureoptions` path unchanged.
- Preserve unrelated user-owned worktree changes.

## Execution Checklist

- [x] Inspect event-value extraction and PyQtGraph item creation.
- [x] Replace full-height event-value stems with one-point markers.
- [x] Add coordinate, point-count, symbol, and opacity regression tests.
- [x] Add renderer-neutral curve style dialog with confirm/cancel semantics.
- [x] Route PyQtGraph Lines action to the new dialog.
- [x] Fix the Cotrix brand width regression exposed by visual metrics tests.
- [x] Run focused adapter, dialog, toolbar, syntax, and lint checks.
- [x] Run independent code review and patch findings.
- [x] Commit only owned files after final phase review passes.

## Review Gate

The phase is complete only when the reviewer reports PASS, focused tests pass,
and event-heavy WebSocket smoke produces nonblank output without full-height
event-value bars.

## Completion Evidence

- Final independent review: `.sisyphus/phase-1-visual-parity-final-review-2.md` — PASS, 0 findings.
- Focused regression suite: 108 passed, 2 dependency deprecation warnings.
- Event-heavy WebSocket smoke: 90 samples, 2 event-value items, 9 event items, 2 RoR items, nonblank 1280x720 screenshot.
- Static checks: `py_compile`, targeted `ruff check`, and `git diff --check` passed.
- Closed: 2026-07-23.
