# ArtisanZ GUI Modernization Phase 1.8: WebSocket Main-Window Validation

**Goal:** Validate the default PyQtGraph GUI through the real Artisan main-window sampling path using deterministic WebSocket virtual roast data.

**Execution Status:** Implemented and verified on 2026-07-02.

**Reason:** Phase 1.7 proved protocol-level WebSocket data can feed the PyQtGraph renderer harness. It did not prove that the full `ApplicationWindow -> qmc.device == 111 -> wsport -> sample_processing -> live renderer/LCD` path works with the same virtual data. This phase closes that gap before physical-device testing.

## Scope

- Add a reusable threaded wrapper around the existing `dev_simulator.ws_server.AsyncServer`.
- Add an env-gated GUI autorun mode: `ARTISANZ_GUI_PERF_AUTORUN_MODE=websocket-recording`.
- Configure the main WebSocket device in memory only for the autorun session:
  - device id `111`
  - host/port/path from the in-process simulator
  - `getData` request command
  - channel 0 node `BT`, mode `C`
  - channel 1 node `ET`, mode `C`
- Allow accelerated validation by combining a short real sampling delay with a larger virtual WebSocket fixed step.
- Capture screenshot, status, and performance JSONL evidence.
- Restore the original device/WebSocket settings before quitting so normal user settings are not polluted.

## Non-Goals

- Do not replace physical roaster validation.
- Do not change default user device configuration.
- Do not make OpenGL the default.
- Do not implement remaining export/deep-analysis PyQtGraph parity.

## Implementation Tasks

1. Create `src/dev_simulator/threaded_ws_server.py`.
   - Run `AsyncServer` in a daemon thread.
   - Support port `0` and update the actual bound port after startup.
   - Provide explicit `start()` and `stop()` methods.

2. Extend `src/artisanlib/main.py`.
   - Route `ARTISANZ_GUI_PERF_AUTORUN_MODE=websocket-recording` to a new autorun helper.
   - Start the threaded simulator.
   - Temporarily configure `appWindow.qmc.device` and `appWindow.ws`.
   - Start recording through the existing `ToggleRecorder()` path.
   - Capture status/screenshot/perf metrics.
   - Stop the simulator and restore original state.

3. Add tests.
   - Verify the threaded simulator serves `getData`, emits CHARGE, exposes an assigned port, and stops cleanly.

4. Run full-app validation.
   - Launch `artisan.py` offscreen with WebSocket autorun.
   - Require status lines proving endpoint setup, active recording, sample count, time indexes, state restoration, and finish.
   - Require non-empty screenshot and JSONL performance output.

## Validation Command

```bash
cd src
QT_QPA_PLATFORM=offscreen \
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_MODE=websocket-recording \
ARTISANZ_GUI_PERF_AUTORUN_DURATION_MS=16000 \
ARTISANZ_GUI_PERF_AUTORUN_SAMPLE_DELAY_MS=500 \
ARTISANZ_GUI_PERF_AUTORUN_WEBSOCKET_FIXED_STEP_MS=30000 \
ARTISANZ_GUI_PERF_AUTORUN_STATUS_FILE=/tmp/artisanz-ws-main-status.txt \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-ws-main-perf.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-ws-main.png \
.venv/bin/python artisan.py
```

## Exit Gate

- `py_compile` passes for touched Python modules.
- Focused simulator/WebSocket/PyQtGraph tests pass.
- Offscreen full-app WebSocket autorun exits by itself.
- Status shows samples and roast event indexes generated from WebSocket traffic.
- Screenshot and perf JSONL files exist and are non-empty.
- Code review finds no blocking issues.

## Result

- `py_compile`: passed for `src/dev_simulator/threaded_ws_server.py` and `src/artisanlib/main.py`.
- Focused tests: `19 passed` across threaded WebSocket server, WebSocket renderer smoke, PyQtGraph adapter, and PyQtGraph widget tests.
- Full-app autorun: passed with `/tmp/artisanz-ws-main-status.txt`, `/tmp/artisanz-ws-main-perf.jsonl`, and `/tmp/artisanz-ws-main.png`.
- Status evidence: `samples=30 timeindex=[1, 10, 19, 22, 26, 0, 26, 0]`.
- Performance evidence: `sample_processing max=4.160ms avg=1.601ms`, `updategraphics max=17.878ms avg=6.110ms`, `updateBackground max=71.821ms avg=27.362ms`, `redraw max=100.403ms avg=65.904ms`.
