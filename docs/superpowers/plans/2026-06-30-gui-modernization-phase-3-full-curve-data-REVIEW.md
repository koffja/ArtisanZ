# GUI Modernization Phase 3 Full Curve Data Review

**Reviewer:** request-code-reviewer (`Helmholtz`)
**Date:** 2026-06-30
**Scope:** Uncommitted Phase 3 slice extracting renderer-facing full connected curve data for live ET/BT and extra-device lines from inline `tgraphcanvas.sample_processing()` payload preparation.

## Strengths

- `full_curve_data()` matches the existing `CurveWindowData` payload shape and keeps it tuple-backed, which is suitable for renderer adapters.
- The helper preserves order and `None` gaps without moving numpy concerns into pure processing code.
- `canvas.py` keeps visibility checks, `Line2D.set_data(...)` mutation, and numpy conversion at the Matplotlib boundary.
- Tests cover the key helper contract: empty payloads and connected values with gaps.
- Roadmap and phase plan accurately describe the Phase 3 progress.

## Issues

### Critical

None found.

### Important

None found.

### Minor

None found.

## Recommendations

- Keep `.codebase-memory/*` out of the commit unless intentionally updating the graph artifact.
- A future slice could add a narrow canvas-facing test around the `set_data(...)` payloads, but this is not required for this mechanical extraction.

## Assessment

Ready to merge: **Yes**.

Reasoning: The implementation is small, behavior-preserving, plan-aligned, and covered by focused helper tests plus the verification already run.
