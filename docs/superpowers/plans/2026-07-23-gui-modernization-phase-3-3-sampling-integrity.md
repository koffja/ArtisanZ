# Phase 3.3: Sampling Integrity While Worker Is Busy

**Parent roadmap:** `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

**Status:** Closed on 2026-07-23 after implementation, repair, independent review, and commit.

## Goal

Prevent the live processed-frame worker boundary from silently discarding the newest device reading when a previous frame is still being consumed.

## Implementation

- `sample_processing()` coalesces a pending callback into one immutable-copy `_DeferredSampleInput`.
- The newest raw ET/BT/extra-device batch replaces the older deferred batch.
- After the current frame finalizes, the deferred batch resumes through the same GUI-owned sampling path.
- Generation invalidation clears both the worker continuation and deferred input during reset, profile clearing, recording stop, monitor stop, and shutdown.
- A batch-identity check preserves ordering if a newer sampling signal arrives before the queued deferred resume callback.
- Perf counters distinguish coalesced pending inputs from lock skips.
- Deferred lock contention uses one deduplicated 10ms retry; the slot is cleared only after lock acquisition.

## Sampling Contract

This slice uses a bounded latest-value merge. It prevents stale backlog and preserves the newest reading, but it does not promise lossless retention of every high-frequency sample. Phase 3.3 thermal precompute must benchmark this contract at 1 Hz, 5 Hz, and 10 Hz before moving smoothing/RoR/PID computation off the GUI thread.

## Tasks

- [x] Add latest-value coalescing for pending worker callbacks.
- [x] Preserve generation cancellation and ordering during deferred resume.
- [x] Keep reset, stop, fallback, and shutdown paths safe.
- [x] Run focused tests and WebSocket sampling smoke.
- [x] Independent review and repair. Final review: `.sisyphus/phase-3-3-sampling-integrity-final-review.md`, PASS.
- [x] Commit the sampling-integrity slice.

## Evidence

- Focused Qt/data suite: `157 passed, 2 warnings`.
- WebSocket main-window autorun, 8 seconds, fixed-step 30 seconds: `samples=14`, `timeindex=[1, 10, 0, 0, 0, 0, 0, 0]`, state restored, normal finish.
- Non-empty evidence: `/tmp/artisanz-phase33-final8b.png`, `/tmp/artisanz-phase33-final8b-perf.jsonl`.
- Final review: `.sisyphus/phase-3-3-sampling-integrity-final-review.md`, PASS.

## Next Boundary

Phase 3.3-B will migrate temperature smoothing, pure RoR numeric calculation, and PID process-value selection using immutable nested snapshots and differential tests. Input-filter write-back, math expressions, device branches, and all control side effects remain on the GUI thread until separately audited.
