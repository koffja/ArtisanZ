# Task C1 Report — ChargeTargetAnnotationSnapshot dataclass

## Status

**DONE** (with two minor deviations from spec, both improvements — see Concerns).

## Commit

- Hash: `117930598f1327c5a25aac8bd0f98d8a87da8226`
- Message: `feat(plot-snapshot): add ChargeTargetAnnotationSnapshot dataclass for PyQtGraph parity`
- Diff stat:
  - `src/artisanlib/plot_snapshot.py` — +24 lines
  - `src/test/unitary/artisanlib/test_plot_snapshot.py` — +70 lines
  - 2 files changed, 94 insertions(+)

## Test Results

- `test_charge_target_annotation_snapshot_charged_state` — PASS
- `test_charge_target_annotation_snapshot_active_state` — PASS
- Full `test/unitary/artisanlib/test_plot_snapshot.py`: **8 passed** (6 pre-existing + 2 new), 0 failed, 0 regression
- RED-then-GREEN cycle verified: tests failed with `ImportError: cannot import name 'ChargeTargetAnnotationSnapshot'` before implementation; passed after.

## Import Confirmation

- `Literal` was ALREADY present in `from typing import Literal, Protocol` (line 5 of plot_snapshot.py).
- `Optional` was NOT imported. The spec said "If `Optional` … is NOT already imported, add it"; however, importing `Optional` and using `Optional[float]` triggered ruff `UP045` (non-ignored, enforced: `lint.select = ["E", "F", "UP", "B", ...]`). To keep both ruff exit-0 AND match the existing codebase decoration pattern (e.g., `EventMarkerSnapshot.value: float | None = None`), the annotation was written as `float | None` and `Optional` was NOT added to the typing import. See Concerns #1.

## Concerns

1. **`Optional[float]` → `float | None` deviation.** The plan spec used `Optional[float]` for `prediction_seconds`. This was changed to `float | None` because:
   - ruff `UP045` is enforced (no entry in `lint.ignore` at `pyproject.toml:306`).
   - Existing dataclasses in the same file use `float | None` (e.g., `EventMarkerSnapshot.value: float | None = None`).
   - `from __future__ import annotations` is at line 1, so both forms work at runtime.
   - Net result: spec literal text differs, but ruff exits 0 and decoration pattern matches.

2. **`__all__` updated.** The plan did not mention modifying `__all__`, but every existing Literal type and every existing snapshot class is listed there. Added `ChargeAnnotationColor` and `ChargeTargetAnnotationSnapshot` in alphabetical order to avoid breaking the file's export convention.

3. **Pre-existing failure in `test_plot_snapshot_extractor.py` (NOT touched).** Running the full plot_snapshot-directory suite reveals 1 pre-existing failure in `test_plot_snapshot_extractor.py` where extracted `PhaseBandSnapshot` items have `opacity=0.3` but the snapshot's `from_sequences` clamps/expects `0.22` (off by rounding on `max(0.0, min(1.0, float(opacity)))`). I did NOT touch this file (`git status --short` confirms only the two expected files were modified). Unaffected by C1.

## Files Changed

1. `src/artisanlib/plot_snapshot.py`
   - Added `ChargeAnnotationColor = Literal['gray', 'blue', 'green', 'red']` to the Literal block (between `AreaFillKind` and `@dataclass AxisSnapshot`).
   - Added `ChargeTargetAnnotationSnapshot` dataclass with `@dataclass(frozen=True, slots=True)` between `PhaseSummarySnapshot` and `AreaFillSnapshot` (matches existing decoration pattern).
   - Appended `charge_target_annotations: tuple[ChargeTargetAnnotationSnapshot, ...] = ()` as the LAST field of `RoastPlotSnapshot` (no existing field touched or reordered).
   - Added `ChargeAnnotationColor` and `ChargeTargetAnnotationSnapshot` to `__all__` in alphabetical position.

2. `src/test/unitary/artisanlib/test_plot_snapshot.py` (NOTE: actual path is `artisanlib`, not `artisan` as in the plan spec)
   - Appended 2 new tests using the existing local-import pattern (`from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot`) — matches the rest of the file's conventions.

## Path Correction Note

The plan spec referenced `src/test/unitary/artisan/test_plot_snapshot.py`, but the actual file lives at `src/test/unitary/artisanlib/test_plot_snapshot.py`. The git commit used the real path.

## Next Steps (out of scope for C1)

- C2: extract `ChargeTargetAnnotationSnapshot` values from existing charge-target code in `main.py` / `charge_manager.py` and pass them into `RoastPlotSnapshot.charge_target_annotations`.
- C3: render annotations in the PyQtGraph backend.
- C4: integration / e2e verification.
