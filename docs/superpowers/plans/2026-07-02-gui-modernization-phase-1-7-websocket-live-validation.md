# GUI Modernization Phase 1.7 WebSocket Live Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Validate the default PyQtGraph GUI path with deterministic WebSocket-driven virtual roast data instead of only static snapshots and profile-file simulator captures.

**Architecture:** Extend the existing `dev_simulator` WebSocket server with an optional fixed-step virtual clock for repeatable tests. Add a validation harness that starts the simulator in-process, pulls Artisan-compatible `getData` responses over WebSocket, converts the stream into `RoastPlotSnapshot` frames, feeds the PyQtGraph renderer, and emits JSON metrics. Keep this as a development/verification path; do not alter roast behavior or production device code.

**Tech Stack:** Python asyncio, `websockets`, existing `dev_simulator`, PyQt6, PyQtGraph, existing `RoastPlotSnapshot` and `PyQtGraphSnapshotRenderer`.

---

## File Map

- `src/dev_simulator/ws_server.py`: add optional fixed-step simulated time for deterministic, fast WebSocket streams.
- `src/dev_simulator/artisan_simulator.py`: expose a CLI flag for the fixed-step mode.
- `src/artisanlib/websocket_renderer_smoke.py`: create WebSocket-to-PyQtGraph validation harness and JSON CLI.
- `src/test/dev_simulator/test_ws_server.py`: cover fixed-step time progression.
- `src/test/unitary/artisanlib/test_websocket_renderer_smoke.py`: cover stream-to-snapshot conversion and in-process WebSocket/PyQtGraph validation.
- `docs/GUI_MODERNIZATION_BASELINE.md`: record how to run the WebSocket live validation smoke and the latest local evidence.
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`: record Phase 1.7 status and remaining gates.

## Task 1: Deterministic WebSocket Simulator Clock

**Files:**
- Modify: `src/dev_simulator/ws_server.py`
- Modify: `src/dev_simulator/artisan_simulator.py`
- Modify: `src/test/dev_simulator/test_ws_server.py`

- [x] Add `fixed_step_ms: float | None = None` to `ServerState`.
- [x] Preserve current wall-clock behavior when `fixed_step_ms` is unset.
- [x] When fixed-step is set, first request returns `0.0` and later requests add exactly `fixed_step_ms`.
- [x] Thread fixed-step through `AsyncServer` and the simulator CLI.
- [x] Add tests proving fixed-step mode and existing pause behavior.

## Task 2: WebSocket-To-Snapshot Validation Harness

**Files:**
- Create: `src/artisanlib/websocket_renderer_smoke.py`
- Create: `src/test/unitary/artisanlib/test_websocket_renderer_smoke.py`

- [x] Start `AsyncServer` in-process on a free local port with deterministic roast data.
- [x] Pull `getData` responses over `ws://127.0.0.1:<port>/WebSocket`.
- [x] Convert BT/ET data messages plus event push messages into `RoastPlotSnapshot`.
- [x] Compute RoR curves from live BT/ET samples.
- [x] Include virtual phase bands, event value rails, and AUC/BBP/charge-target guide lines so Phase 1.6 overlays are exercised with live data.

## Task 3: PyQtGraph Live Validation and Metrics

**Files:**
- Modify: `src/artisanlib/websocket_renderer_smoke.py`
- Modify: `src/test/unitary/artisanlib/test_websocket_renderer_smoke.py`

- [x] Feed the generated frames into `create_pyqtgraph_plot_target(use_opengl=False)`.
- [x] Use `update_live_frame()` for ordinary data ticks and `set_snapshot()` when overlays change.
- [x] Emit JSON metrics: sample count, data message count, push message count, event count, item counts, full snapshot count, live update count, max update ms, average update ms, and exported view state.
- [x] Add a CLI entry point usable through `python -m artisanlib.websocket_renderer_smoke`.

## Task 4: Verification and Documentation

**Files:**
- Modify: `docs/GUI_MODERNIZATION_BASELINE.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: this plan.

- [x] Run focused unit tests for simulator and WebSocket renderer smoke.
- [x] Run py_compile for touched files.
- [x] Run ruff for touched files.
- [x] Run the new WebSocket PyQtGraph validation CLI and record the JSON evidence.
- [x] Commit code and docs without staging `.codebase-memory`.

## Closure Definition

Phase 1.7 is closed when a deterministic WebSocket virtual roast stream can drive the PyQtGraph renderer in-process, produce nonzero curve/overlay item counts, report bounded update timing, and document the command/evidence for repeatable future GUI optimization.
