# Phase 3.3-B Thermal Contract Final Review

Status: **PASS**

Scope: latest versions of:

- `src/artisanlib/sample_processing.py`
- `src/artisanlib/processed_frame_worker.py`
- `src/test/unitary/artisanlib/test_sample_processing.py`
- `src/test/unitary/artisanlib/test_processed_frame_worker.py`

Checked contract:

- **None history:** `LiveThermalInputRequest` preserves `None` in smoothed histories; `build_live_thermal_input_result()` maps those entries to dropout values before RoR calculation. Dedicated test passes.
- **NumPy deep tuple:** `_deep_tuple()` converts NumPy arrays and nested sequences recursively. Snapshot remains detached after source mutation. Dedicated tests pass.
- **Thermal error / queued path:** `ProcessedFrameWorker` emits isolated `thermal_error`; thermal requests use `thermal_request` with `QueuedConnection`, and results return on the GUI thread. Dedicated tests pass.

Verification:

```text
cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  test/unitary/artisanlib/test_sample_processing.py \
  test/unitary/artisanlib/test_processed_frame_worker.py -q
159 passed in 0.15s
```

Findings: none.

No commit made.
