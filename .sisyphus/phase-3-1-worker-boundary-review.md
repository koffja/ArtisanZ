---
phase: 3.1-processed-frame-worker-boundary
reviewed: 2026-07-23T15:10:58Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - src/artisanlib/processed_frame_worker.py
  - src/test/unitary/artisanlib/test_processed_frame_worker.py
  - docs/superpowers/plans/2026-07-23-gui-modernization-phase-3-1-processed-frame-worker-boundary.md
  - docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 3.1: Code Review Report

**Reviewed:** 2026-07-23T15:10:58Z  
**Depth:** standard  
**Files Reviewed:** 4  
**Status:** issues_found

## Summary

Boundary shape is sound. `ProcessedFrameWorker.process()` is a queued `@pyqtSlot`; the pure helper has no live-state access; the result is immutable; and the current runtime sampling path is still unchanged. No injection, secret, or authorization issue found. Focused tests passed: 3 tests, `py_compile`, targeted `ruff`, and `git diff --check`.

Two warnings remain before Phase 3.2: the frozen request does not enforce its mutable-sequence boundary at construction, and the worker error path is untested and can silently discard a frame when no error receiver is connected. The Phase 3.1-specific plan text correctly defers runtime migration and shutdown ownership. The roadmap's high-level Phase 3 outcome needs one qualification to avoid implying that migration already happened.

## Warnings

### WR-01: Frozen request accepts a live mutable `sample_times` list

**File:** `src/artisanlib/processed_frame_worker.py:47`  
**Issue:** `frozen=True` protects attribute rebinding, but it does not coerce or freeze values passed to the constructor. A caller can pass a `list` despite the annotation, and `request.sample_times` then aliases that GUI-owned list. `asdict()` copies it only when `process()` starts, after queued delivery; mutations between `request` construction and worker execution can therefore change the decision inputs. The snapshot test passes a tuple at line 68, so it does not exercise the failing construction path.
**Fix:** Normalize at construction (or expose a factory that always snapshots):

```python
def __post_init__(self) -> None:
    object.__setattr__(self, 'sample_times', tuple(self.sample_times))
```

Add a test that passes a list, mutates the list after construction, and asserts the request remains unchanged. Also assert frozen-field assignment raises `FrozenInstanceError`.

### WR-02: Error and teardown behavior are not regression-tested

**File:** `src/artisanlib/processed_frame_worker.py:67-75`  
**Issue:** A helper exception emits only `str(exc)` and returns. With no connected `error` slot, the frame is silently dropped; the signal carries no exception type or traceback. The focused suite covers only success. It does not verify that one failing request produces exactly one error with the correct sequence, no result, and a worker that continues processing later requests. The test also has no `try/finally` around the thread lifecycle, so an unexpected setup/event-loop failure can leave the `QThread` running.
**Fix:** Define the error contract before Phase 3.2, preserve useful diagnostics (at least exception type plus message, or a logged traceback), add an error-path test with a monkeypatched helper, and wrap thread setup/use in `try/finally` that calls `quit()` and waits before cleanup.

## Info

### IN-01: High-level roadmap outcome can imply runtime migration already happened

**File:** `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md:59`  
**Issue:** The Phase 3 table says the outcome is “GUI thread consumes snapshots instead of doing heavy processing inline,” while Phase 3.1 is explicitly boundary-only and the live continuation remains Phase 3.2. The detailed Phase 3.1 section at lines 438-440 corrects this, but readers using the table alone can infer a current runtime handoff.
**Fix:** Qualify the table outcome as the eventual Phase 3 target, for example: “After Phase 3.2, GUI thread consumes snapshots instead of doing heavy processing inline.”

---

_Reviewed: 2026-07-23T15:10:58Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
