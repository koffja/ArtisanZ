# GUI Modernization Native QA Audit

**Status:** Code-side audit closed 2026-07-24. Physical-device release gate remains open.

**Purpose:** Record the final native-window and packaging evidence after the PyQtGraph default-renderer, dialog, toolbar, and QML-island work. Keep environment failures separate from GUI regressions.

## Evidence

- Native macOS WebSocket main-window autorun completed with 18 samples, restored device/WebSocket state, and screenshot `/tmp/artisanz-native-window.png`.
- Native screenshot shows the Cotrix toolbar, LCD telemetry, PyQtGraph roast surface, linked RoR axis, event points/leaders/labels, legend, minute labels, and event rail.
- Native PyQtGraph probe reported `useOpenGL=True`, `requested=True`, and viewport class `GraphicsViewGLWidget`.
- Qt Quick packaging smoke passed with `PyInstaller 6.21.0`, real `PyQt6.QtQml`/`PyQt6.QtQuick`/`PyQt6.QtQuickWidgets` imports, and `Workspace Status QML widget: ready 320x220`.
- Full `test/unitary/artisanlib` run: `2453 passed, 29 failed, 3 skipped`. The 29 failures are environment/tooling failures: missing `pytest-asyncio` for async tests and a DNS-dependent invalid-host assertion. No GUI modernization test failed; Qt Quick size baseline now passes.

## Closed Code Gates

- Default PyQtGraph renderer and Matplotlib compatibility renderer remain selectable.
- Grid, phase bands, RoR, background/projection curves, event values, phase summaries, analysis overlays, legend, cursor telemetry, i18n labels, and opt-in report PNG handoff are implemented and covered by focused tests/smokes.
- Axes, Curves, Events, Alarms, Devices, and Roast Properties use the shared flat Morandi dialog layer; Roast Properties received the final form-surface hierarchy pass.
- Qt Quick remains isolated to the Workspace Status island; packaging and subprocess smoke coverage are green.

## Remaining Gates

1. Run a representative physical-device session at the supported sampling rates and compare native timing against the simulator evidence. This cannot be completed from the current environment without hardware.
2. Review hardware-specific Devices tabs with real device configurations. The shared visual layer is complete; deeper per-panel simplification remains optional follow-up, not a renderer blocker.
3. Keep Matplotlib as the default report/export compatibility path. PyQtGraph report graph handoff is explicit opt-in until broader real-profile report comparison is approved.

## Next Action

Use a real Artisan device session for the final release evidence. Any code change after this point should be driven by a concrete native/device defect, not by another broad renderer rewrite.
