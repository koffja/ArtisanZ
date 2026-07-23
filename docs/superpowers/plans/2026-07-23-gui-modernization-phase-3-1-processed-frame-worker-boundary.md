# Phase 3.1: Processed-Frame Worker Boundary

**Parent roadmap:** `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

**Status:** Boundary contract complete; live orchestration intentionally deferred to Phase 3.2.

## Goal

Define a safe queued Qt worker boundary for the already-pure `ProcessedSampleFrame` decision function without moving GUI-owned roast state across threads.

## Scope

- Add a frozen `ProcessedFrameRequest` containing every input required by `build_live_processed_sample_frame()`.
- Copy `sample_times` into an immutable tuple before crossing the thread boundary.
- Add a dedicated `QThread` event-loop worker and GUI-owned request channel.
- Return the existing `ProcessedSampleFrame` object through a queued result signal.
- Prove direct equivalence, immutable input behavior, worker-thread execution, and GUI-thread result delivery.

## Explicit Non-Goals

- Do not move `qmc` list mutation, smoothing/RoR history mutation, PID calls, alarm state, event signals, or renderer updates.
- Do not reuse `SampleThread`; its custom `run()` loop does not run a Qt event loop.
- Do not claim a live sampling latency improvement until the asynchronous continuation is integrated and benchmarked.

## Tasks

- [x] Add immutable request and queued worker modules.
- [x] Add helper-equivalence and snapshot-isolation tests.
- [x] Add a real `QThread` queued request/result smoke test.
- [x] Record the safe ownership boundary and Phase 3.2 prerequisite.
- [x] Run independent code review and repair findings.
- [x] Commit the boundary slice.

## Review Gate

Before Phase 3.2, review the continuation design against these invariants:

1. At most one sample transaction is pending.
2. The GUI owns the semaphore for the full transaction and releases it exactly once.
3. Results carry a monotonic sequence and stale results are ignored.
4. Worker shutdown waits for in-flight work before QObject destruction.
5. GUI-only side effects remain in the GUI-thread continuation.

## Evidence

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_processed_frame_worker.py -q`
- `py_compile` for `src/artisanlib/processed_frame_worker.py` and its focused test.
- Targeted `ruff check` and `git diff --check`.
- Final review: `.sisyphus/phase-3-1-worker-boundary-final-review.md`.

## Phase 3.2 Prerequisite

Extract the post-frame suffix of `tgraphcanvas.sample_processing()` into a GUI-owned continuation context. Only after that extraction is equivalence-tested should this worker be connected to live sampling. The continuation must carry immutable request identity plus GUI-owned list references and must finalize playback, semaphore release, and `updategraphicsSignal` exactly once.

**Closed:** 2026-07-23 as a boundary-only slice. No runtime sampling behavior changed.
