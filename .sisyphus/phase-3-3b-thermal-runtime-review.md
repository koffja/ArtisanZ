# Phase 3.3-B Thermal Runtime Handoff Review

Date: 2026-07-23
Status: PASS

## Scope

- `src/artisanlib/canvas.py`
- `src/artisanlib/processed_frame_worker.py`
- `src/artisanlib/sample_processing.py`
- focused unit tests and WebSocket main-window smoke

## Review Results

1. **Worker boundary**: `sample_processing()` performs device reads, input filters, connected-history updates, and extra-device math on the GUI thread, then submits an immutable `LiveThermalInputRequest`. `ProcessedFrameWorker.process_thermal()` computes smoothing, raw RoR, and PID input in the worker thread.
2. **Continuation ownership**: `_ThermalContinuation` retains GUI-owned histories and curve payloads while the worker runs. Accepted thermal results enter the existing processed-frame worker, preserving event, alarm, projection, and redraw behavior.
3. **Semaphore ownership**: the GUI lock is released after thermal submission; thermal and final-frame callbacks reacquire it before mutating histories. Synchronous fallback keeps the original lock until finalization. Cancellation releases only continuations that still own the lock.
4. **Stale/shutdown safety**: thermal and frame continuations share generation and sequence validation. Reset, mode changes, and shutdown clear both pending stages. Deferred samples are coalesced while either stage is pending.
5. **Error fallback**: thermal worker errors call `build_live_thermal_input_result()` synchronously, then use the same continuation path. Frame worker errors retain the existing synchronous frame fallback.
6. **Visual/data parity**: ET, BT, extra curves, RoR histories, PID updates, projection/event decisions, and frame redraw all remain represented. ET/BT curve data is appended once in the accepted thermal continuation.

## Evidence

- Focused tests: `176 passed, 2 warnings`.
- Ruff: passed for all changed runtime and test files.
- Python compilation: passed for `canvas.py`, `processed_frame_worker.py`, and `sample_processing.py`.
- WebSocket main-window smoke: 16 seconds, 30 samples, `timeindex=[1, 10, 19, 22, 26, 0, 26, 0]`, normal state restoration, non-empty screenshot.
- Smoke perf: `canvas.sample_processing` average `0.693 ms`, maximum `1.350 ms`; thermal and frame worker submission counters each recorded 30 calls.

## Residual Risk

- Hardware-specific device timing and a long-duration soak remain outside this offscreen smoke. Run those after Phase 3.3-B before claiming hardware-wide performance gains.
