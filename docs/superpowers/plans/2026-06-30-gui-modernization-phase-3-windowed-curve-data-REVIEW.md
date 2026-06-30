# GUI Modernization Phase 3 Windowed Curve Data Review

**Reviewer:** request-code-reviewer (`Popper`)
**Date:** 2026-06-30
**Scope:** Uncommitted Phase 3 slice extracting renderer-facing Delta ET/BT windowed curve data from `tgraphcanvas.sample_processing()`.

## Strengths

- `windowed_curve_data()` preserves the old `start:end` slicing behavior exactly for both times and Delta values, including `None` payload values.
- `CurveWindowData` is frozen and tuple-backed, which fits the renderer-facing immutable data boundary.
- `canvas.py` still owns visibility checks, `Line2D.set_data(...)`, and `numpy.array(...)` conversion at the Matplotlib boundary.
- Tests cover the two required behaviors: no-window empty payload and explicit slice semantics with `None`.
- Documentation accurately records Phase 3 progress; the unchecked review/commit steps in the new plan are appropriate for the current state.

## Issues

### Critical

None found.

### Important

None found.

### Minor

None found.

## Recommendations

- Keep `.codebase-memory/artifact.json` and `.codebase-memory/graph.db.zst` out unless those graph updates are intentional for this phase.
- After accepting this review, update the plan checklist's code-review step if using it as the source of truth.

## Assessment

Ready to merge: **Yes**.

Reasoning: The helper extraction is behavior-preserving, renderer-boundary placement is clean, and the test coverage matches the stated requirements.
