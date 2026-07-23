# Phase 3.2: Live Processed-Frame Continuation

**Parent roadmap:** `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

**Status:** Closed on 2026-07-23 after implementation, repair, independent review, and commit.

## Goal

Connect the Phase 3.1 worker to the live sampling path while keeping every mutable roast state, Qt signal, alarm, PID, event, and renderer operation on the GUI thread.

## Implementation

- `tgraphcanvas.sample_processing()` now creates an immutable `ProcessedFrameRequest` and queues it to the dedicated worker.
- A GUI-owned `_ProcessedFrameContinuation` retains the current sample transaction while the worker runs.
- The worker result is checked by monotonic sequence and consumed by `_apply_processed_frame()` on the GUI thread.
- Pending samples are single-flight: later queued samples skip instead of mutating lists out of order.
- `profileDataSemaphore` is released while the worker is pending, then reacquired with a bounded retry before applying the result. This prevents an older queued redraw from blocking the result callback.
- Common playback, semaphore, and `updategraphicsSignal` cleanup runs exactly once after the continuation.
- Worker shutdown clears pending state, releases an owned lock, quits the event-loop thread, and waits before application exit.
- The existing synchronous helper fallback uses the same GUI continuation, so there is one frame-consumption implementation.

## Tasks

- [x] Extract GUI-owned frame consumption into `_apply_processed_frame()`.
- [x] Connect the immutable worker request/result boundary to live sampling.
- [x] Add single-flight, stale-result, bounded-lock, and shutdown handling.
- [x] Keep `updategraphics()` from waiting behind a pending frame result.
- [x] Run focused tests and a real WebSocket main-window smoke.
- [x] Independent review and repair. Final review: `.sisyphus/phase-3-2-live-continuation-final-review.md`, PASS.
- [x] Commit the live continuation slice.

## Guardrails

- Smoothing/RoR history calculation, math expressions, PID process-value calculation, and input filtering remain in the GUI transaction in this slice.
- No worker touches `qmc` lists, Qt widgets, Matplotlib/PyQtGraph items, or event/alarm state.
- A worker failure falls back to the same pure helper on the GUI thread and preserves finalization.

## Evidence

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_processed_frame_worker.py test/unitary/artisanlib/test_sample_processing.py test/unitary/artisanlib/test_canvas_renderer_selection.py -q`: `157 passed, 2 warnings`.
- `py_compile`: `canvas.py`, `main.py`, `processed_frame_worker.py` passed.
- WebSocket main-window autorun, 16 seconds, fixed-step 30 seconds: `samples=30`, `timeindex=[1, 10, 19, 22, 26, 0, 26, 0]`, state restored, normal finish; non-empty screenshot `/tmp/artisanz-phase32-ws-final-fixed.png`, non-empty perf JSONL `/tmp/artisanz-phase32-ws-final-fixed-perf.jsonl`.
- Live sampling metric: worker submit count `30`; pending redraw skips remained bounded at `5`.
- Final review: `.sisyphus/phase-3-2-live-continuation-final-review.md`, PASS; only pre-existing `main.py` `QFileDialog` `F401` remains.

## Remaining Phase 3 Work

This closes the first runtime handoff, not the whole sampling-decoupling phase. A later slice should move heavier filtering/RoR/PID-input computation only after equivalent immutable inputs and a larger hardware-representative benchmark exist.
