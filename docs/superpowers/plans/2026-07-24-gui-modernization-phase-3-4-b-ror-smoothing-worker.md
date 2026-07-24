# GUI Modernization Phase 3.4-B: RoR Smoothing Worker

## Status

- [x] Extend the immutable thermal request with RoR smoothing settings.
- [x] Compute ordinary ET/BT RoR smoothing in `build_live_thermal_input_result()`.
- [x] Preserve GUI evaluation for custom `DeltaETfunction` / `DeltaBTfunction` formulas.
- [x] Keep GUI-owned RoR history, LCD state, plots, and display-limit behavior unchanged.
- [x] Add pure-contract regression coverage.
- [ ] Move custom Delta expressions after a dedicated pure-expression/runtime-context contract.

## Compatibility Rules

- Worker smoothing activates only when the corresponding custom Delta expression is empty.
- The existing GUI smoothing path remains the fallback for custom formulas and worker failures.
- `LiveThermalInputRequest` copies all histories before the worker sees them.
- RoR values still enter the existing display-window and renderer-neutral plot path.

## Verification

- Focused sample-processing and worker tests pass.
- Native WebSocket autorun remains the integration gate for the live thermal chain.
