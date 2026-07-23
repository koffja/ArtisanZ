# Phase 3.3-B: Thermal Precompute Contract

**Parent roadmap:** `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

**Status:** Closed on 2026-07-23 after runtime handoff, fallback repair, WebSocket validation, review, and commit.

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
- [x] Connect the thermal request to the live GUI continuation.
- [x] Run end-to-end WebSocket smoke and runtime perf capture; differential contract coverage remains in focused tests.
- [x] Independent review of the contract slice and repair. Final review: `.sisyphus/phase-3-3b-thermal-contract-final-review.md`, PASS.
- [x] Commit the contract slice.

## Guardrails

- Worker receives snapshots only; no `qmc` lists, Qt widgets, PID objects, device I/O, math-expression state, or renderer objects.
- `len(sample_times) <= 1` preserves the live path's zero-RoR warm-up behavior.
- The existing Phase 3.2 processed-frame worker path remains unchanged until runtime handoff equivalence is proven.

## Runtime Handoff

- `canvas.py` now queues thermal work after GUI-owned input filtering and connected-history append.
- Accepted thermal results append smoothed histories, apply Delta math expressions, smooth display RoR, update PID, then enter the existing processed-frame worker.
- ET/BT and extra curve payloads remain GUI-owned; event, alarm, projection, and redraw decisions remain on the GUI side.
- Thermal worker errors fall back to the pure helper; stale generations and shutdown cancel both thermal and frame continuations.

## Evidence

- `test_sample_processing.py` + `test_processed_frame_worker.py` + renderer selection: `176 passed, 2 warnings`.
- `py_compile` and Ruff pass for changed runtime modules/tests.
- WebSocket main-window smoke: 16 seconds, 30 samples, `timeindex=[1, 10, 19, 22, 26, 0, 26, 0]`, normal state restoration, non-empty screenshot.
- Runtime report: `/tmp/artisanz-phase33b-runtime-perf.jsonl`; `canvas.sample_processing` average `0.693 ms`, maximum `1.350 ms`.
- Final review: `.sisyphus/phase-3-3b-thermal-runtime-review.md`, PASS.

## Next Boundary

Long-duration and hardware-representative benchmarks remain before claiming device-wide performance gains. Phase 4 can proceed after that evidence gate.
