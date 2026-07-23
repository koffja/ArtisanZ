# Phase 3.3-B: Thermal Precompute Contract

**Parent roadmap:** `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

**Status:** Contract slice closed on 2026-07-23 after implementation, repair, independent review, and commit. Runtime GUI handoff remains the next bounded slice.

## Goal

Define an immutable, worker-ready boundary for ET/BT smoothing, pure raw RoR calculation, and PID process-value selection without moving GUI-owned history or control side effects.

## Implementation

- Added frozen/slotted `LiveThermalInputRequest` and `LiveThermalInputResult`.
- Deep-converted nested histories to tuples in `__post_init__`.
- Added pure `build_live_thermal_input_result()` using existing smoothing, RoR, and PID-selection helpers.
- Added `ProcessedFrameWorker.process_thermal()` and a separate queued result/error signal pair.
- Kept PID updates, math expressions, input-filter write-back, device branches, event decisions, alarms, and rendering outside the worker boundary.

## Tasks

- [x] Define deep immutable thermal request/result contract.
- [x] Implement pure ET/BT smoothing, raw RoR, and PID-value computation.
- [x] Add worker entry point and typed thermal result/error signals.
- [x] Add golden, differential, dropout, short-history, polyfit, and PID-source tests.
- [ ] Connect the thermal request to the live GUI continuation.
- [ ] Run end-to-end WebSocket and 1/5/10 Hz differential benchmarks.
- [x] Independent review of the contract slice and repair. Final review: `.sisyphus/phase-3-3b-thermal-contract-final-review.md`, PASS.
- [x] Commit the contract slice.

## Guardrails

- Worker receives snapshots only; no `qmc` lists, Qt widgets, PID objects, device I/O, math-expression state, or renderer objects.
- `len(sample_times) <= 1` preserves the live path's zero-RoR warm-up behavior.
- The existing Phase 3.2 processed-frame worker path remains unchanged until runtime handoff equivalence is proven.

## Evidence

- `test_sample_processing.py` + `test_processed_frame_worker.py`: `155 passed`.
- `py_compile` and Ruff pass for changed modules/tests.

## Next Boundary

Runtime integration must build the thermal request after GUI-owned input filtering and connected-history append, hold the continuation while the worker runs, apply only accepted results, preserve Delta math-expression ordering, then submit the existing processed-frame request. Stale/reset/shutdown and latest-input coalescing rules remain mandatory.
