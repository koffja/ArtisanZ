# GUI Modernization Phase 3.4-A: Primary Input Filter Worker

## Status

- [x] Define an immutable ET/BT input-filter request/result contract.
- [x] Run primary ET/BT filter decisions through the existing `ProcessedFrameWorker` thread.
- [x] Preserve GUI ownership of raw/connected history mutation and backfill writes.
- [x] Coalesce newer samples while the filter result is pending.
- [x] Guard stale results and worker errors with the existing generation/fallback policy.
- [x] Add contract, equivalence, immutability, and worker tests.
- [x] Keep ET/BT expressions that depend on `Y3+` extra channels on the original post-extra-device ordering.
- [ ] Move extra-device input filtering after device-specific adapter review.

## Scope

This slice removes the primary ET/BT `inputFilter()` calculation from the GUI sampling callback. The worker receives copied histories and immutable filter settings. The GUI applies the accepted result to its owned history lists, then continues the existing extra-device, thermal, RoR, event, alarm, and redraw stages.

## Compatibility Rules

- Keep `input_filter_result()` as the canonical pure decision function.
- Preserve the existing ordering: expression evaluation, filter decision, raw-history backfill, connected-curve backfill, append, thermal processing.
- Expressions referencing `Y3+` remain after extra-device runtime values are populated; the worker path applies only when that ordering is independent.
- Do not let the worker hold references to GUI-owned lists.
- Keep the synchronous pure-helper fallback when the worker is unavailable or errors.
- Leave extra-device filtering on the legacy path until each device family has a focused contract review.

## Verification

- `test_sample_processing.py` and `test_processed_frame_worker.py`: contract and worker tests pass.
- `py_compile`, `ruff`, and `git diff --check` pass for touched modules.
- Native WebSocket autorun remains the required follow-up for the complete live sampling path.
