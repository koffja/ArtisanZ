# ArtisanZ GUI Modernization Roadmap

**Purpose:** Track the multi-phase GUI modernization effort from measurement through visual refresh, plotting improvements, processing decoupling, and optional QML adoption.

**Status:** Phase 0 automated profile redraw baseline, 20-second simulator smokes, a 60-second internal simulator live-sampling baseline, and guarded PyQtGraph offscreen/native-window simulator baselines are captured as of 2026-07-02; real-device baseline remains pending. Phase 1 Widgets visual modernization has a main-screen first pass with corrected LCD spacing, label padding, a transparent LCD container strategy that avoids nested card/value misalignment, and a 2026-07-02 multi-state visual QA pass covering default historical-profile redraw plus guarded PyQtGraph live simulator captures. Phase 1.5 makes PyQtGraph the default selected renderer, syncs historical profile snapshots into the PyQtGraph widget, preserves the LCD telemetry column under the new widget, renders RoR on the same graph with a right-side axis, restores PyQtGraph grid/tick-step parity for existing axis settings, adds a Minutes/Seconds time-label mode in Config > Axes, and keeps `ARTISANZ_RENDERER_ID=matplotlib-snapshot` as the compatibility escape hatch. Phase 1.6 is closed for high-value PyQtGraph visual parity and scoped dialog chrome: it adds a dedicated PyQtGraph grid overlay, stronger phase-background colors, event value rails, AUC/BBP/charge-target guide lines, a no-outer-frame LCD strategy, and scoped Morandi dialog styling for Axes, Curves, Events, and Alarms. Phase 1.7 adds deterministic WebSocket virtual-roast validation: the in-process `dev_simulator` can advance by fixed virtual steps, emit Artisan-compatible `getData` responses and push events, and feed those frames through the PyQtGraph renderer with JSON timing/item-count evidence. Phase 1.8 closes the next validation gap by launching the full Artisan main window, temporarily configuring the real WebSocket device path, recording through `ToggleRecorder()`, and proving samples/events/LCD/main graph rendering from virtual WebSocket traffic with screenshot and performance evidence. Phase 1.9 improves event-heavy PyQtGraph visual parity with clustered event-label row placement and renderer-neutral AUC area fills rendered in PyQtGraph. Phase 1.10 validates that work with deterministic event-heavy WebSocket virtual data, AUC area item counts, renderer item counts, screenshot capture, and an edge-label anchor fix for unclipped CHARGE/DROP labels. Phase 1.11 adds a shared ArtisanDialog interior polish layer for modern spacing, flat viewports, table presentation, tab behavior, and primary/secondary button roles across common settings dialogs. Phase 1.12 opt-ins Devices and Roast Properties to dense-dialog roles so their table-heavy interiors can receive modern table/header styling without changing hardware/configuration behavior. Phase 1.13 closes a PyQtGraph export/evidence handoff by rendering `RoastPlotSnapshot` through the real PyQtGraph target into PNG files and reporting dimensions, byte counts, sampled non-background pixels, renderer item counts, and view state; WebSocket event-heavy smoke now uses the same PNG evidence path. Phase 1.14 adds a renderer-neutral export parity smoke: deterministic WebSocket event-heavy snapshots are exported through Matplotlib and PyQtGraph, Matplotlib snapshot rendering now covers phase bands, AUC/area fills, event value rails, and guide lines, and the CLI reports matching view state plus overlay counts for both backends. Phase 2 has a renderer snapshot contract, a canvas-like extractor with foreground event markers, an unhooked Matplotlib adapter that renders snapshot events, offscreen Agg smoke coverage, dependency-backed PyQtGraph smoke coverage, a repeatable Matplotlib-vs-PyQtGraph renderer benchmark entry, explicit `QOpenGLWidget` runtime support reporting, live-frame payload boundaries wired into Matplotlib ET/BT, Delta ET/BT, extra-device, and live x-axis canvas updates, matching PyQtGraph live-frame applier helpers, a backend-aware main-curve live-frame dispatch, a real PyQtGraph `GraphicsLayoutWidget` target factory used by smoke coverage, and a guarded main-splitter embed path using software PyQtGraph by default when available. Phase 3 has extracted the live smoothing-weight decision, smoothed temperature value selection, decay-weighted averaging, PID process-value update gate/source selection, PID SV update target selection, PID SV update decisions, extra-device length diagnostics, alarm source/limit decisions, alarm readiness/offset timing, alarm trigger evaluation, auto-event detection gates, manual-mode TP candidate checks, RoR computation/display/filter/smoothing decisions, connected-curve point decisions, input-filter previous-reading snapshots/backfill/result decisions, x-axis auto-extension decisions, post-sample update decisions, external-output payload decisions, renderer-facing Delta ET/BT windowed curve data payloads, renderer-facing full connected ET/BT/extra curve data payloads, and the first processed-frame contract from `sample_processing()` into tested pure helpers; a Phase 3 audit now characterizes the remaining inline work as mostly canvas mutation/orchestration plus renderer payload, with no new high-value pure-helper extraction recommended at this layer. The 60-second simulator baseline still shows `sample_processing` below update/redraw paths, so renderer/update-path work remains higher priority than broad threading; real-device timing remains pending. Phase 4 is closed at the workspace information-architecture layer with tested task-oriented workspaces, menu/toolbar policy, persistence, and one visible next-action hint per workspace. Phase 5 is closed at the local QML-island level with a renderer-aware Workspace Status dock, action hints, packaging smoke coverage, and restored-dock visibility fixes. Phase 6 is closed at typed boundary level: renderer, report, analyzer, filter, and profile-comparison plugin categories can be registered/listed, while only renderer plugins are instantiable by the current runtime.

**Repository Rules:** Work on the `ArtisanZ` branch. Do not commit or push unless explicitly requested. Preserve upstream compatibility and local ArtisanZ customizations.

## Context

ArtisanZ currently uses PyQt6 Widgets with Matplotlib QtAgg for the main roast graph. The main runtime path is `src/artisan.py` -> `artisanlib.command_utility.handleCommands()` -> `artisanlib.main.main()`. The GUI is concentrated in `src/artisanlib/main.py`, while live graphing, sampling, RoR, alarm, event, projection, and rendering logic are concentrated in `src/artisanlib/canvas.py`.

Important observations from the code review:

- `src/requirements.txt` pins `matplotlib==3.10.9`, `PyQt6==6.11.0`, `PyQt6-WebEngine==6.11.0`, `pyqtgraph==0.14.0`, and `PyOpenGL==3.1.10`.
- `src/artisanlib/canvas.py` defines `MplCanvas`, `tgraphcanvas`, `SampleThread`, and `Athreadserver`.
- The live graph already uses Matplotlib blitting paths such as `copy_from_bbox`, `restore_region`, `draw_artist`, and `blit`, so plotting changes must be benchmarked rather than assumed.
- Sampling already runs in `SampleThread`, but `sample_processing()` runs in the GUI thread and mixes data processing, PID, event detection, alarm evaluation, line data mutation, and redraw signaling.
- `src/artisanlib/main.py` already has `UI_MODE` values for Expert, Standard, and Production, but those modes mostly affect menu and toolbar visibility rather than a full modern information architecture.

## Roadmap Principles

- Measure first. No renderer or threading replacement is approved without a baseline comparison.
- Keep Matplotlib available for reports, export, analysis, and compatibility until a replacement proves full coverage.
- Improve visual quality without changing roast behavior in the first user-visible phase.
- Prefer reversible feature flags and adapters over one-way rewrites.
- Keep each phase independently testable and reviewable.
- Do not migrate every dialog to QML. Use Qt Quick only where it clearly improves the user experience.

## Phase Tracking

| Phase | Name | Status | Primary Deliverable | Exit Gate |
| --- | --- | --- | --- | --- |
| 0 | Performance Baseline and Risk Map | Profile + 20s/60s simulator baselines captured; real-device baseline pending | Timing probes, benchmark workflow, baseline report | We know whether rendering, GUI-thread processing, locks, or device sampling dominate latency |
| 1 | Widgets Visual Modernization | Main-screen first pass + LCD value surface alignment corrected + multi-state visual QA captured | Modern theme tokens and refreshed main roast screen styling | Main screen looks modern while behavior and settings compatibility remain intact |
| 1.5 | Default PyQtGraph Main Screen | Complete: default renderer switched, historical profile sync added, single-plot RoR/time-axis/grid/LCD follow-ups verified | PyQtGraph selected by default with nonblank profile redraws and visible LCD telemetry | Users see the modern renderer by default while Matplotlib remains one env var away |
| 1.6 | PyQtGraph Visual Parity and Dialog Refresh | Closed for high-value runtime parity; export/deep-analysis parity remains future work | Grid/phase/event-value/guide overlays and scoped Morandi chrome for key settings dialogs | PyQtGraph first screen no longer feels visually or functionally behind the legacy Matplotlib view |
| 1.7 | WebSocket Virtual Roast Validation | Closed: deterministic WebSocket stream drives PyQtGraph smoke metrics | In-process WebSocket roast stream, live snapshot conversion, renderer update timing JSON | Renderer changes can be tested against protocol-level virtual data before hardware sessions |
| 1.8 | WebSocket Main-Window Validation | Closed: full main-window WebSocket autorun passes with virtual data | Env-gated threaded simulator, temporary WebSocket device config, screenshot/perf/status evidence | The real sampling/UI path consumes WebSocket virtual data before hardware sessions |
| 1.9 | PyQtGraph Event/AUC Parity | Closed: event label clustering and AUC area fills implemented | AreaFill snapshot overlays and denser event label placement | Event-heavy and post-roast AUC views are closer to legacy visual parity |
| 1.10 | WebSocket Event/AUC Visual Validation | Closed: event-heavy virtual data validates PyQtGraph AUC/event overlays | WebSocket event-heavy scenario, screenshot capture, item/timing metrics | Dense events, RoR, guide lines, and AUC fills are visible and measurable from virtual protocol data |
| 1.11 | Dialog Interior Modernization | Closed: shared ArtisanDialog runtime polish implemented | Layout spacing, flat viewports, table polish, tab behavior, and button roles | Common settings dialogs inherit a less gray, more modern interior without per-dialog rewrites |
| 1.12 | Dense Dialog Polish | Closed: Devices/Roast Properties opt into dense-dialog visual roles | Dense table/header styling roles for table-heavy dialogs | Dense settings dialogs look more intentional while preserving grids, cell widgets, and configuration behavior |
| 1.13 | PyQtGraph Export Evidence | Closed: snapshot PNG helper and WebSocket pixel evidence | PyQtGraph PNG export helper, nonblank pixel evidence, WebSocket smoke metrics | Default renderer validation has reusable image/export evidence before any report/export replacement |
| 1.14 | Export Parity Smoke | Closed: Matplotlib/PyQtGraph snapshot export parity evidence | Export parity CLI, Matplotlib overlay support, WebSocket event-heavy parity JSON | Report/export replacement has comparable snapshot evidence before UI wiring |
| 1.15 | Saved Profile Export Parity | Closed: real `.alog` profile export parity evidence | Saved profile snapshot adapter and `--profile-file` parity CLI | Export parity is proven on real saved profile data before user-facing report/export wiring |
| 1.16 | Saved Profile Export Matrix | Closed: four-profile `.alog` matrix plus WebSocket regression evidence | Profile matrix CLI, aggregate parity summary, default sanity fixtures | Report/export replacement evidence covers multiple saved profiles, not a single fixture |
| 1.17 | Opt-In PyQtGraph PNG Export Action | Closed: user-visible Save Graph action added | `File > Save Graph > PyQtGraph PNG...` plus user-export helper | Users can manually export the modern renderer without replacing Matplotlib report/export paths |
| 1.18 | Report Graph Export Comparison | Closed: report-ready graph asset comparison added | Matplotlib/PyQtGraph report graph image assets with file URLs | Future report replacement can compare backend assets before changing `roastReport()` |
| 2 | Plot Renderer Boundary and PyQtGraph POC | Guarded PyQtGraph main-splitter embed implemented and benchmarked in offscreen/native-window simulator smokes | Read-only plot snapshot model, Matplotlib adapter, PyQtGraph live adapter prototype | POC is benchmarkable before any live renderer swap |
| 3 | Sampling Post-Processing Decoupling | Pure helper extraction surface audited; remaining work is orchestration/renderer payload | Pure data pipeline for filtering, RoR, PID inputs, alarm/event decisions | GUI thread consumes snapshots instead of doing heavy processing inline |
| 4 | Main UI Information Architecture | Closed at IA/policy/status-hint layer | Scenario-oriented Roast Control, QC Analysis, Device Setup, Production, and Expert workspaces | Users can switch task modes without losing existing expert controls |
| 5 | Local QML Islands | Closed at Workspace Status island level | A limited Qt Quick panel backed by Python state models, renderer status, and workspace action hints | QML proves useful without breaking packaging, translations, or Windows portable build |
| 6 | Plugin Boundary Exploration | Closed at typed plugin-boundary level | Renderer/report/filter/analyzer/profile-comparison extension categories | Future customization can be isolated without destabilizing upstream sync |

## Phase 0: Performance Baseline and Risk Map

**Goal:** Build factual evidence before UI or plotting rewrites.

**Scope:**

- Add disabled-by-default timing instrumentation.
- Measure `sample_processing()`, `updategraphics()`, `updateBackground()`, and `redraw()`.
- Record skipped updates, lock waits, and high-percentile timings where practical.
- Provide a repeatable simulator/profile benchmark workflow.
- Produce a baseline report that recommends Phase 1 and Phase 2 priorities.

**Out of Scope:**

- No visual restyling.
- No PyQtGraph dependency.
- No QML.
- No behavior changes to roast recording, alarms, events, PID, or profile serialization.

**Tracking Plan:** `docs/superpowers/plans/2026-06-29-gui-modernization-phase-0.md`

**Implementation Note:** Timing probes, automatic/default JSONL export, `atexit` export fallback, JSONL summary utility, automated profile redraw autorun, and internal simulator-recording autorun are in place. The 20-second and 60-second simulator baselines show `sample_processing` is not the immediate simulator bottleneck; prioritize Phase 2 renderer/update-path work before broad processing-thread migration. Keep a real-device run as the remaining gate before treating simulator timing as representative hardware evidence.

## Phase 1: Widgets Visual Modernization

**Goal:** Deliver a noticeably more modern ArtisanZ main screen while staying inside PyQt6 Widgets.

**Started:** 2026-06-29 with an application-level modern stylesheet and theme token module. The first main-screen pass now includes flat event button styling, LCD surface/label styling, and offscreen screenshot capture through `ARTISANZ_GUI_PERF_SCREENSHOT_FILE`. `ARTISANZ_LEGACY_UI=1` can be used as an environment fallback.

**Candidate Work:**

- Create a small theme-token module for colors, spacing, typography, borders, and elevation.
- Replace heavy gradient button styles with flatter, clearer states.
- Modernize LCD boxes, toolbar surface, message area, event buttons, and the graph canvas background.
- Add a modern light theme first, then a dark theme after contrast checks.
- Preserve existing theme settings and user-loaded themes.

**Dependencies:**

- Phase 0 baseline should confirm restyling does not worsen draw/update timing.

**Exit Gate:**

- Screenshot review of OFF, ON, START, event-marked, and background-profile states.
- Focused checks for text fit in English and Simplified Chinese labels.

**2026-07-02 QA Note:** Current visual evidence is tracked in `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-visual-qa.md`. The offscreen historical-profile capture and PyQtGraph live simulator captures show the corrected LCD value panels with padding, bottom-aligned value surfaces, and restored inter-card spacing. Native-window capture validates the same LCD structure outside the offscreen backend. Remaining visual QA should use a real machine/device session for longer START, event-heavy, and language-switch coverage.

## Phase 1.5: Default PyQtGraph Main Screen

**Goal:** Make the PyQtGraph visual path the normal first-run experience without removing Matplotlib compatibility.

**Completed:** 2026-07-02. `DEFAULT_RENDERER_ID` now resolves to `pyqtgraph-snapshot`; Workspace Status labels the selected renderer as `PyQtGraph Snapshot` by default. Historical profile redraws sync a full `RoastPlotSnapshot` into the embedded PyQtGraph renderer, so opening `profile1.alog` is nonblank before live sampling starts. The PyQtGraph widget can compress horizontally, preserving the right-side LCD telemetry column beside the plot. A follow-up pass now renders RoR on the same graph through a linked right-side axis, applies existing x/y/RoR tick-step and grid settings to PyQtGraph, defaults time labels to minute-style labels, adds a persisted Minutes/Seconds option in Config > Axes, and constrains/wraps LCD labels so long telemetry names cannot widen the right column. `ARTISANZ_RENDERER_ID=matplotlib-snapshot` still selects the compatibility renderer.

**Tracking Plan:** `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-5-main-screen-redesign.md`

**Evidence:** Default PyQtGraph screenshot `/tmp/artisanz-phase15-default-pyqtgraph.png`; Matplotlib override screenshot `/tmp/artisanz-phase15-matplotlib-override.png`; axis/LCD follow-up screenshot `/tmp/artisanz-pyqtgraph-axis-fixes.png`; latest focused GUI/PyQtGraph subset `252 passed, 1 skipped, 2 warnings`.

**Remaining Follow-up:** PyQtGraph still has lower overlay parity than Matplotlib for rich annotations, background analysis overlays, and export/report paths. Keep Matplotlib as the compatibility/export path while the PyQtGraph snapshot extractor gains more overlay coverage. Track the detailed parity backlog in Phase 1.6.

## Phase 1.6: PyQtGraph Visual Parity and Dialog Refresh

**Goal:** Close the visible gap introduced by making PyQtGraph the default renderer, and remove the most obvious old-style Widgets surfaces from common configuration dialogs.

**Closed for high-value runtime parity:** 2026-07-02 with a dedicated `GridItem` overlay so grid visibility is not dependent on faint PyQtGraph defaults, higher-contrast Morandi phase-band colors for default phase palettes, foreground/background event value rails, AUC/BBP/charge-target guide lines, a transparent LCD container strategy that removes the fragile nested-card/value composition, and scoped Morandi styling for Axes, Curves, Events, and Alarms dialogs through `modernDialog` roles.

**Tracking Plan:** `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md`

**High-Value PyQtGraph Parity Backlog:**

- Background profile parity beyond the currently extracted ET/BT/Delta background curves: extra-device background curves, background event value rails, and background annotation details.
- Event parity beyond current marker lines/labels: event value bars for the existing event graph modes, richer label placement, overlap avoidance, clustered labels, and drag/edit affordances where Matplotlib currently supports interaction.
- Analysis overlays: AUC guide/area visuals, MET/analysis masks, statistics overlays, charge-target annotations, and other roast-analysis guide marks.
- Projection/guide polish: distinguish forecast/projection lines visually, preserve original line styles more completely, and verify RoR projection placement against legacy behavior.
- Legend/export parity: keep Matplotlib for report/export until PyQtGraph can provide compatible view-state/export handoff or a deliberate export adapter.
- Visual QA: capture historical profile, live simulator, event-heavy, background-profile, long Chinese labels, Config > Axes, Config > Curves, Events, Devices, and Alarms screens.

**Remaining Visual Backlog:**

- Continue deeper per-panel simplification for hardware-specific Devices sections after the shared and dense-dialog polish layers.
- Add event drag/edit parity and deep analysis masks/statistics overlays.
- Keep Matplotlib as the export/report compatibility path until a deliberate PyQtGraph export adapter exists.
- Avoid nested cards, oversized rounded rectangles, and dark gray default widget wells.
- Preserve existing translations, shortcuts, validation, and settings persistence.

## Phase 1.7: WebSocket Virtual Roast Validation

**Goal:** Validate GUI renderer behavior with protocol-level virtual roast data before a physical machine/device session.

**Closed:** 2026-07-02 with `artisanlib.websocket_renderer_smoke`, which starts the existing `dev_simulator` WebSocket server in-process, uses fixed-step virtual time, requests Artisan-compatible `getData` messages, maps push events into snapshot markers/event values, and feeds PyQtGraph with ordinary `update_live_frame()` calls plus full snapshots when overlays change.

**Tracking Plan:** `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-7-websocket-live-validation.md`

**Evidence:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke --samples 24 --fixed-step-ms 15000` produced `data_message_count=24`, `push_message_count=6`, `event_value_count=2`, `guide_count=3`, `full_snapshot_count=6`, `live_update_count=18`, `avg_update_ms=1.1859`, and `max_update_ms=4.7771`.

**Remaining Gate:** This validates WebSocket protocol traffic and PyQtGraph renderer behavior with deterministic virtual data. It does not replace physical-device timing, long START sessions, or OpenGL real-window validation.

## Phase 1.8: WebSocket Main-Window Validation

**Goal:** Prove that deterministic WebSocket virtual data can drive the real Artisan main-window recording path, not only the standalone PyQtGraph renderer harness.

**Closed:** 2026-07-02 with `dev_simulator.threaded_ws_server`, an env-gated `ARTISANZ_GUI_PERF_AUTORUN_MODE=websocket-recording` path in `artisanlib.main`, and a full offscreen `artisan.py` autorun. The autorun starts a threaded in-process WebSocket simulator, temporarily configures `qmc.device == 111`, sets WebSocket channel 0/1 to `BT`/`ET` in Celsius mode, records through the existing `ToggleRecorder()` path, captures screenshot/perf/status output, then restores the original device/WebSocket settings.

**Tracking Plan:** `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-8-websocket-main-window-validation.md`

**Evidence:** `QT_QPA_PLATFORM=offscreen ARTISANZ_GUI_PERF=1 ARTISANZ_GUI_PERF_AUTORUN=1 ARTISANZ_GUI_PERF_AUTORUN_MODE=websocket-recording ... .venv/bin/python artisan.py` produced screenshot `/tmp/artisanz-ws-main.png`, status `samples=30 timeindex=[1, 10, 19, 22, 26, 0, 26, 0]`, and performance summary `sample_processing max=4.160ms avg=1.601ms`, `updategraphics max=17.878ms avg=6.110ms`, `updateBackground max=71.821ms avg=27.362ms`, `redraw max=100.403ms avg=65.904ms`.

**Remaining Gate:** This uses accelerated virtual time to cover roast events quickly while the main-window clock remains real wall time. It proves plumbing and renderer behavior with protocol data, but still does not replace a long real-time hardware session.

## Phase 1.9: PyQtGraph Event/AUC Parity

**Goal:** Improve default PyQtGraph parity for event-heavy and post-roast views.

**Closed:** 2026-07-03 with `AreaFillSnapshot` in the renderer-neutral snapshot contract, AUC area extraction from canvas state, PyQtGraph area-fill rendering using filled `PlotDataItem` overlays, and clustered event-label row placement so labels close in time use separate rows.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-9-pyqtgraph-event-auc-parity.md`

**Evidence:** Focused snapshot/extractor/adapter/widget/WebSocket smoke tests produced `39 passed`. Static validation passed for `py_compile`, `ruff check`, and `git diff --check` on touched modules. Code-review follow-up fixed AUC base-index parity with legacy `-1` samples and removed the dense event-label row wraparound.

**Remaining Gate:** This does not implement event drag/edit parity, report/export handoff, analysis masks, or statistics overlays; those remain in the deep PyQtGraph parity backlog.

## Phase 1.10: WebSocket Event/AUC Visual Validation

**Goal:** Validate the PyQtGraph event/AUC parity work with deterministic protocol-level virtual roast data.

**Closed:** 2026-07-03 with an `event-heavy` scenario in `artisanlib.websocket_renderer_smoke`, AUC area generation from WebSocket samples after DROP, smoke-result area item counts, optional PyQtGraph screenshot capture, and boundary-aware event label anchors so CHARGE/DROP labels do not clip at the plot edges.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-10-websocket-event-auc-validation.md`

**Evidence:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke --samples 24 --fixed-step-ms 15000 --scenario event-heavy --screenshot-file /tmp/artisanz-websocket-event-heavy.png` produced `sample_count=24`, `event_count=11`, `event_value_count=7`, `area_count=1`, `renderer_area_item_count=1`, `guide_count=3`, `avg_update_ms=2.5528`, and `max_update_ms=14.5805`. Screenshot review confirmed visible grid, dense event labels, RoR axis, AUC fill, and unclipped CHARGE label.

**Remaining Gate:** Virtual WebSocket data is now stronger for renderer validation, but this still does not replace a long real-time hardware session or full PyQtGraph export/report parity.

## Phase 1.11: Dialog Interior Modernization

**Goal:** Make common settings dialogs feel flatter, softer, and less like default gray Qt forms without rewriting each dialog.

**Closed:** 2026-07-03 with `apply_modern_dialog_polish()` in `artisanlib.gui_theme` and a one-time `ArtisanDialog.showEvent()` hook. The polish normalizes root/group/tab-page layout spacing, marks group boxes and tab widgets with modern roles, enables document-mode non-expanding tabs, gives table/scroll viewports modern background roles, preserves existing table grid preferences, and marks standard OK/Apply/Save buttons as primary while Cancel/Close/Reset buttons become secondary.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-11-dialog-interior-modernization.md`

**Evidence:** `python3 -m py_compile src/artisanlib/gui_theme.py src/artisanlib/dialogs.py`; focused tests `test_gui_theme.py` and `test_dialogs.py` produced `27 passed, 1 skipped`; `ruff check` and `git diff --check` passed.

**Remaining Gate:** This is the shared polish layer. Dense hardware/settings screens such as Devices and Roasting Properties still need individual layout review before claiming every settings dialog has been fully redesigned.

## Phase 1.12: Dense Dialog Polish

**Goal:** Apply explicit visual roles to Devices and Roasting Properties, the densest settings dialogs, without changing their configuration behavior.

**Closed:** 2026-07-03 with `modernDialogRole="devices"` and `modernDialogRole="roast_properties"` on the relevant dialogs plus dense-dialog table/header roles inside `apply_modern_dialog_polish()`. The stylesheet now has targeted dense-dialog selectors for table item padding, headers, and selected tab color while preserving table grids, selection modes, edit triggers, and table cell widget layouts.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-12-dense-dialog-polish.md`

**Evidence:** `python3 -m py_compile src/artisanlib/gui_theme.py src/artisanlib/dialogs.py src/artisanlib/devices.py src/artisanlib/roast_properties.py`; focused tests `test_gui_theme.py` and `test_dialogs.py` produced `28 passed, 1 skipped`; `ruff check` and `git diff --check` passed.

**Remaining Gate:** Devices still contains intentionally dense hardware-specific panels. Further simplification should be per-panel and workflow-aware rather than global styling.

## Phase 1.13: PyQtGraph Export Evidence

**Goal:** Add a reusable PyQtGraph PNG export/evidence path so renderer validation can prove nonblank rendered pixels, item counts, and view state from real snapshot data.

**Closed:** 2026-07-03 with `artisanlib.plot_pyqtgraph_export`, which can render a `RoastPlotSnapshot` through the same PyQtGraph `GraphicsLayoutWidget` target used by the GUI and write a PNG with dimensions, byte count, sampled pixel count, sampled non-background pixel count, renderer item counts, and exported view state. `artisanlib.websocket_renderer_smoke` now reuses that helper for event-heavy screenshot evidence.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-13-pyqtgraph-export-evidence.md`

**Evidence:** Focused WebSocket renderer tests produced `7 passed`. CLI validation with `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke --samples 24 --fixed-step-ms 15000 --scenario event-heavy --screenshot-file /tmp/artisanz-phase113-websocket-event-heavy.png` produced `sample_count=24`, `event_count=11`, `event_value_count=7`, `area_count=1`, `temperature_item_count=10`, `ror_item_count=2`, `renderer_event_item_count=22`, `screenshot_width=1280`, `screenshot_height=720`, `screenshot_byte_count=71364`, and `screenshot_sampled_non_background_pixel_count=21753`.

**Remaining Gate:** This is evidence/export groundwork only. Matplotlib remains the report/export compatibility path until a deliberate PyQtGraph report/export adapter is designed and compared against existing output.

## Phase 1.14: Export Parity Smoke

**Goal:** Establish comparable Matplotlib/PyQtGraph export evidence from the same renderer-neutral snapshot before wiring PyQtGraph into any user-facing report/export path.

**Closed:** 2026-07-03 with `artisanlib.plot_export_parity_smoke`, a CLI/module that collects deterministic WebSocket virtual data, builds a `RoastPlotSnapshot`, exports it through both Matplotlib and PyQtGraph, and reports file paths, byte counts, view-state equality/tolerance, and backend overlay counts. `MatplotlibSnapshotRenderer` now renders phase bands, AUC/area fills, event value rails, and guide lines in addition to curves and event markers.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-14-export-parity-smoke.md`

**Evidence:** Focused Matplotlib adapter/smoke/export parity tests produced `7 passed`. CLI validation with `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_export_parity_smoke --samples 24 --fixed-step-ms 15000 --scenario event-heavy --output-dir /tmp/artisanz-phase114-export-parity --prefix phase114-event-heavy --width 1280 --height 720 --dpi 100` produced `view_state_matches=true`, `view_state_max_delta=0.0`, `event_count=11`, `event_value_count=7`, `phase_band_count=3`, `guide_count=3`, `area_count=1`, Matplotlib `event_artist_count=22`, `event_value_artist_count=7`, `phase_artist_count=3`, `guide_artist_count=3`, `area_artist_count=1`, and PyQtGraph `renderer_event_item_count=22`, `renderer_event_value_item_count=7`, `renderer_guide_item_count=3`, `renderer_area_item_count=1`, `sampled_non_background_pixel_count=21795`.

**Remaining Gate:** This still does not switch the production report/export menus. The next report/export step should compare real saved profiles and then decide whether a user-facing PyQtGraph export option is safe.

## Phase 1.15: Saved Profile Export Parity

**Goal:** Validate PyQtGraph export parity against real saved Artisan `.alog` profile data, not only synthetic WebSocket samples.

**Closed:** 2026-07-03 with `artisanlib.plot_profile_snapshot`, which loads Artisan `.alog` files through `artisanlib.util.deserialize()`, adapts profile dictionaries into the renderer-neutral snapshot contract, supplies historical-profile defaults for axis ranges, visibility, RoR curves, phase bands, AUC area, event colors, and event labels, and lets `artisanlib.plot_export_parity_smoke --profile-file` export the same saved profile through Matplotlib and PyQtGraph.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-15-saved-profile-export-parity.md`

**Evidence:** Focused profile/export tests produced `7 passed`, and the renderer/export smoke suite produced `28 passed`. CLI validation with `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_export_parity_smoke --profile-file test/data/profile1.alog --output-dir /tmp/artisanz-phase115-profile-export-parity-final --prefix phase115-profile1 --width 1280 --height 720 --dpi 100` produced `source_kind=profile`, `sample_count=1735`, corrected saved-profile `time_axis=795.4684590097568..1474.1684661597471`, `view_state_matches=true`, `view_state_max_delta=0.0`, `event_count=14`, `event_value_count=10`, `phase_band_count=3`, `area_count=1`, Matplotlib `event_artist_count=28`, `event_value_artist_count=10`, `phase_artist_count=3`, `area_artist_count=1`, and PyQtGraph `renderer_event_item_count=28`, `renderer_event_value_item_count=10`, `renderer_area_item_count=1`, `sampled_non_background_pixel_count=14492`. A WebSocket virtual-data regression run with `--scenario event-heavy` also produced `source_kind=websocket`, `sample_count=24`, `view_state_matches=true`, `guide_count=3`, and PyQtGraph `sampled_non_background_pixel_count=21795`.

**Remaining Gate:** This validates one automated saved-profile fixture. The next export/report step should compare a small matrix of saved profiles and then decide whether a user-facing PyQtGraph export option is safe.

## Phase 1.16: Saved Profile Export Matrix

**Goal:** Expand saved-profile export parity from one `.alog` fixture to a small matrix of real saved Artisan profiles, while keeping deterministic WebSocket virtual-data regression in the same evidence path.

**Closed:** 2026-07-03 with `artisanlib.plot_export_parity_matrix`, which accepts explicit profile files or profile globs, runs each saved profile through the existing Matplotlib/PyQtGraph export parity path, summarizes profile count, source paths, samples, events, event values, phase-band coverage, view-state equality/tolerance, PyQtGraph nonblank image evidence, and optional WebSocket regression status.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-16-profile-export-matrix.md`

**Evidence:** Matrix tests produced `6 passed`. CLI validation with `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_export_parity_matrix --profile-glob 'test/sanity/data/artisan/profile*.alog' --include-websocket-regression --websocket-samples 24 --websocket-fixed-step-ms 15000 --websocket-scenario event-heavy --output-dir /tmp/artisanz-phase116-profile-matrix-final --prefix phase116-matrix --width 1280 --height 720 --dpi 100` produced `profile_count=4`, `total_sample_count=2854`, `total_event_count=74`, `total_event_value_count=58`, `minimum_phase_band_count=2`, `maximum_phase_band_count=3`, `all_view_states_match=true`, `all_view_states_within_tolerance=true`, `maximum_view_state_delta=0.0`, `all_pyqtgraph_exports_nonblank=true`, `websocket_regression_included=true`, and `websocket_view_state_matches=true`. Reviewer follow-up also verified that typoed explicit globs now fail instead of silently shrinking the matrix.

**Remaining Gate:** This broadens report/export parity evidence, but the production report/export UI is still intentionally not switched. The next safe step is an opt-in user-facing PyQtGraph export action or a report/export adapter comparison against the existing Matplotlib output.

## Phase 1.17: Opt-In PyQtGraph PNG Export Action

**Goal:** Make the PyQtGraph export work visible to users through an opt-in menu action, without replacing the existing Matplotlib save/report/export compatibility paths.

**Closed:** 2026-07-03 with `artisanlib.plot_user_export`, which builds a renderer-neutral snapshot from the current graph source, exports it through the PyQtGraph PNG renderer, normalizes PNG filenames, and uses the current graph widget size when available. `File > Save Graph` now includes `PyQtGraph PNG...` beside the existing Matplotlib-backed PDF/SVG/PNG/JPEG actions.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-17-pyqtgraph-png-export-action.md`

**Evidence:** Focused user-export/parity/widget tests produced `27 passed`. Offscreen saved-profile validation with `export_current_graph_pyqtgraph_png(ProfileSnapshotSource(deserialize('test/data/profile1.alog')), '/tmp/artisanz-phase117-user-export-profile1', width=1280, height=720, use_opengl=False)` produced `/tmp/artisanz-phase117-user-export-profile1.png`, `byte_count=69659`, `sampled_non_background_pixel_count=14492`, `temperature_item_count=13`, `ror_item_count=2`, `event_item_count=28`, `event_value_item_count=10`, and `area_item_count=1`.

**Remaining Gate:** This is an opt-in user action only. Matplotlib remains the default report/export compatibility path until report-specific output parity is designed and compared.

## Phase 1.18: Report Graph Export Comparison

**Goal:** Create a report-oriented comparison adapter for Matplotlib and PyQtGraph graph images, so the future report/export replacement can be evaluated with report-ready assets before changing `roastReport()`.

**Closed:** 2026-07-03 with `artisanlib.plot_report_export`, which loads saved profiles through the renderer-neutral snapshot path, produces Matplotlib and PyQtGraph report graph image assets, returns report-style `file://` URLs with optional cache busters, and reports dimensions, byte counts, PyQtGraph nonblank pixels, view-state equality, and overlay counts. `roastReport()` and the existing Matplotlib HTML/PDF report path remain unchanged.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-18-report-graph-export-comparison.md`

**Evidence:** Report export tests produced `6 passed`. CLI validation with `QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.plot_report_export test/data/profile1.alog --output-dir /tmp/artisanz-phase118-report-graph --prefix phase118-profile1-report --width 1280 --height 720 --dpi 100 --cache-buster 118` produced `source_kind=profile`, `title=Guji Shakiso`, `sample_count=1735`, `view_state_matches=true`, `view_state_max_delta=0.0`, `event_count=14`, `event_value_count=10`, `phase_band_count=3`, `area_count=1`, Matplotlib `byte_count=233509`, PyQtGraph `byte_count=69659`, and PyQtGraph `sampled_non_background_pixel_count=14492`. Reviewer follow-up fixed relative `--output-dir` URL resolution and strengthened the saved-profile-only helper guard.

**Remaining Gate:** This produces report-ready comparison assets but still does not switch `roastReport()`. The next report step should either run this comparison across the Phase 1.16 profile matrix or add an env-gated report image backend switch with Matplotlib fallback.

## Phase 1.19: PyQtGraph Grid and Phase Background Live Parity

**Goal:** Fix the default PyQtGraph live-renderer visual regression where background gridlines and roast phase temperature bands were either missing from live updates or too faint on the light canvas.

**Closed:** 2026-07-03 with `build_roast_plot_static_overlay_snapshot()`, `merge_static_plot_overlays()`, live/static snapshot merging in `tgraphcanvas.apply_pyqtgraph_live_plot_frame()`, static-overlay application in `PyQtGraphSnapshotRenderer.update_live_frame()`, overlay signature caching to avoid repeated remove/add churn, stronger grid contrast, and a visible phase-band opacity floor.

**Tracking Plan:** `docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-19-pyqtgraph-grid-phase-live-parity.md`

**Evidence:** Focused renderer/canvas/WebSocket tests produced `79 passed`; `py_compile` and `ruff check` passed on changed modules. CLI validation with `QT_QPA_PLATFORM=offscreen ./.venv/bin/python -m artisanlib.websocket_renderer_smoke --scenario event-heavy --samples 90 --fixed-step-ms 1000 --screenshot-file /tmp/artisanz-pyqtgraph-grid-phase-fix.png` produced `avg_update_ms=1.6805`, `max_update_ms=4.2407`, `live_update_count=87`, `renderer_event_item_count=6`, `renderer_event_value_item_count=2`, `renderer_guide_item_count=3`, `screenshot_byte_count=64841`, and `screenshot_sampled_non_background_pixel_count=27707`; visual review confirmed visible gridlines and horizontal phase temperature bands.

**Remaining Gate:** This closes the immediate grid/phase visual regression in the default live PyQtGraph path. Remaining PyQtGraph parity work still needs richer Matplotlib overlay coverage, interactive graph edit parity, and report/export backend switching.

## Phase 2: Plot Renderer Boundary and PyQtGraph POC

**Goal:** Make the live plot renderer replaceable without forcing a full Matplotlib rewrite.

**Started:** 2026-06-29 with a data-only `plot_snapshot.py` contract, `plot_snapshot_extractor.py` canvas-like snapshot builder with foreground event marker extraction, `plot_matplotlib_adapter.py` compatibility adapter with event-marker rendering, `plot_matplotlib_smoke.py` offscreen Agg diagnostic path, `plot_pyqtgraph_adapter.py` as a PyQtGraph-style POC adapter, and `plot_pyqtgraph_smoke.py` as a real PyQtGraph/PyOpenGL dependency smoke path. These do not change runtime plotting behavior yet; they prepare a stable renderer-facing surface before benchmark-backed live canvas integration.

**Completion Note:** The Phase 2 renderer-boundary POC is complete at code level and now has real `pyqtgraph==0.14.0` / `PyOpenGL==3.1.10` smoke coverage plus a repeatable renderer benchmark CLI. A 2026-06-30 offscreen `900` point, `8` event, `5` iteration sample measured Matplotlib adapter average `0.010817674966529012s` and PyQtGraph adapter average `0.0025607582181692125s` with OpenGL requested, while `opengl_widget_supported=false`; the no-OpenGL PyQtGraph average was `0.0026710582431405784s`. This supports a guarded PyQtGraph live-renderer POC, but OpenGL acceleration still needs real-window/device verification before it can be treated as a benefit. The first live-frame payload slice adds `plot_live_frame.py` and routes the main ET/BT plus Delta ET/BT Matplotlib `set_data` calls through a tested payload/applier boundary. Follow-up slices add a PyQtGraph live applier that consumes the same payload, converts dropout `None` values to `nan`, route extra-device Matplotlib live curve updates through `LiveCurveData`, route live x-axis extension through `LiveAxisRange`, and route BT/ET plus Delta projection updates and clearing through `LiveCurveData` without changing runtime renderer selection. The renderer-selection setting seam now reads `ARTISANZ_RENDERER_ID`, validates the requested id against the runtime renderer registry, reports fallback reasons, and can drive a filesystem-discovered renderer id through the factory smoke path. `tgraphcanvas` now stores the selected renderer metadata at initialization for diagnostics and future live wiring; selection failures, including malformed dotted dependency metadata from plugin declarations, fall back to the default Matplotlib renderer metadata with a `selection_error` diagnostic. Actual drawing still uses the existing Matplotlib path until a guarded renderer switch is implemented and benchmarked.

**Runtime Dispatch Note:** A 2026-07-02 slice routes ET/BT/Delta ET/Delta BT main-curve updates through a backend-aware `LivePlotFrame` dispatch. With current Matplotlib UI targets the behavior remains equivalent; if `pyqtgraph-snapshot` is selected before a PyQtGraph plot widget is embedded, `canvas.py` records a `pyqtgraph_targets_unavailable` fallback and applies the frame to the existing Matplotlib lines. This makes the switch explicit and measurable instead of silently claiming PyQtGraph runtime rendering before the widget exists.

**PyQtGraph Target Note:** A follow-up 2026-07-02 slice adds `plot_pyqtgraph_widget.py`, a real `GraphicsLayoutWidget` target factory with temperature/RoR plot items, OpenGL config restoration, linked target smoke coverage, and adapter range stabilization for first-layout auto-range behavior. The smoke path now exercises the same target factory the future UI embed should use.

**Guarded Embed Note:** A 2026-07-02 slice exposes `tgraphcanvas.graph_widget()` and lets the main splitter mount the selected graph widget. PyQtGraph is now the default selected renderer; selecting `matplotlib-snapshot` through `ARTISANZ_RENDERER_ID` creates the compatibility path instead. The PyQtGraph target is fed from live-frame dispatch and full profile snapshots, and falls back to Matplotlib if target creation or snapshot update fails. Toolbar/export compatibility still keeps the Matplotlib canvas alive while the PyQtGraph visual path is evaluated. The first OpenGL embed attempt produced a blank graph surface in this environment, matching the earlier `QOpenGLWidget` support warning, so the guarded target now uses software PyQtGraph until a real-device OpenGL path is proven.

**Candidate Work:**

- Define a read-only `RoastPlotSnapshot` containing visible curve data, axis state, event markers, background curves, phases, projections, and charge-target annotation data.
- Define a `LivePlotRenderer` interface with `set_snapshot()`, `update_live_frame()`, `reset_view()`, and `export_view_state()` methods.
- Wrap existing Matplotlib behavior in a compatibility adapter.
- Build a PyQtGraph prototype for real-time ET, BT, RoR, background curves, and event markers.
- Compare Matplotlib and PyQtGraph under Phase 0 benchmark scenarios.

**Dependencies:**

- Phase 0 timing probes and baseline scenario.

**Exit Gate:**

- POC has measurable benefit or a clear maintainability gain.
- Existing Matplotlib report/export/analysis flows remain untouched.

## Phase 3: Sampling Post-Processing Decoupling

**Goal:** Reduce GUI thread load by moving pure computation out of `tgraphcanvas.sample_processing()`.

**Started:** 2026-06-29 with `sample_processing.py`, tested pure helpers for choosing decay smoothing weights, selecting smoothed temperature values, computing decay-weighted averages, gating PID process-value updates, selecting the PID process value from ET/BT/extra-device channels, selecting the PID SV update target, deciding PID SV updates, formatting extra-device length diagnostics, evaluating alarm source/limit decisions, checking alarm readiness/offset timing, evaluating full alarm trigger decisions, gating automatic CHARGE/TP/DROP/DRY/FCs event detection, checking manual-mode TP candidates, computing and smoothing RoR values, deciding RoR display/filter windows, preparing renderer-facing Delta ET/BT windowed curve data, preparing renderer-facing full connected ET/BT/extra curve data, choosing connected-curve append/disconnection points, identifying input-filter backfill updates, capturing input-filter previous-reading snapshots, deciding input-filter current-reading results/backfills, deciding x-axis auto-extension, deciding post-sample AUC/AUC-guide/BBP update gates, formatting external-output payloads, aggregating the first `ProcessedSampleFrame` contract, and separating post-TP DRY/FCs phase-event decisions. `canvas.py` still owns live mutation, PID calls, event/alarm signals, and rendering; these slices remove deterministic decisions from the 692-line GUI-thread method and establish the data boundary needed before moving computation off the GUI thread. A comparable 20-second simulator smoke after the processed-frame slice measured `canvas.sample_processing max=0.574ms avg=0.500ms`, lower than the earlier `max=2.015ms avg=1.103ms` smoke; a later 20-second smoke after PID/manual/extra diagnostics measured `max=1.799ms avg=0.975ms`, still slightly lower than the original but noisy. A 2026-06-30 Sisyphus/Codex audit now concludes the pure-helper extraction surface is functionally complete at this layer; the follow-up defensive cleanup makes the `SampleThread.sample_processingSignal` connection explicitly queued so `sample_processing()` remains GUI-thread work before any future worker migration. Longer simulator/device runs remain required before treating the change as causal or starting broader threading work.

**Candidate Work:**

- Extract filtering and RoR computation into tested pure functions.
- Extract alarm readiness evaluation into a data-only evaluator.
- Extract auto-event detection decisions into a data-only evaluator.
- Emit a compact processed frame/snapshot to the GUI layer.
- Keep Qt signal delivery for UI mutations and existing event actions.

**Dependencies:**

- Phase 0 identifies concrete processing hotspots.
- Phase 2 snapshot shape should inform renderer-facing data structures.

**Exit Gate:**

- Processing tests prove equivalence for representative profiles.
- GUI-thread timing drops in the same benchmark scenario.

## Phase 4: Main UI Information Architecture

**Goal:** Organize ArtisanZ around actual roasting workflows instead of only feature menus.

**Closed at IA/status-hint layer:** 2026-06-30 with a pure `ui_workspaces.py` model that defines Roast Control, QC Analysis, Device Setup, Production, and Expert workspaces, maps legacy `UI_MODE` values into those workspaces, and stores the current `workspace_mode` on `ApplicationWindow`. A 2026-07-02 closure slice adds a stable next-action hint to every workspace and exposes it through the QML Workspace Status panel. This keeps settings compatibility and existing menu behavior while giving future UI slices a task-oriented state model.

**Policy Note:** A follow-up pure-model slice adds `WorkspacePolicy` and `workspace_policy(mode)` for future menu, toolbar, side-panel, analysis, device-setup, advanced-control, and compact-chrome decisions. The first integration slices store `workspace_policy` on `ApplicationWindow`, synchronize it with existing `UI_MODE` settings paths, route toolbar expert line configuration through `policy.show_advanced_controls`, route File/Tools menu visibility through `policy.show_full_menus`, route File expert-only save-copy/statistics and Help diagnostic sections through `policy.show_advanced_controls`, route Config menu normal/device/advanced sections through `policy.show_full_menus`, `policy.show_device_setup_tools`, and `policy.show_advanced_controls`, route Tools menu analysis and expert-tool entries through `policy.show_analysis_tools` and `policy.show_advanced_controls`, route Roast menu profile-switch entries through `policy.show_full_menus` and `policy.show_advanced_controls`, route View menu full-mode controls through `policy.show_full_menus` while preserving runtime fallbacks, route remaining keyboard shortcut and PID compact-control gates through non-compact workspace policy / `policy.compact_chrome`, preserve current Expert/Default/Production behavior, make Roast Control, QC Analysis, and Device Setup selectable from the Mode menu, and persist the selected workspace through `workspace_mode`. QC Analysis and Device Setup currently reuse legacy Default `UI_MODE` for settings compatibility while their visible menus and toolbar are driven by `workspace_policy`.

**Candidate Work:**

- Extend the existing `UI_MODE` concept into task-oriented workspaces.
- Define Roast Control, QC Analysis, Device Setup, and Expert modes.
- Move non-critical controls out of the main roast control surface.
- Preserve expert-mode access to existing behavior.
- Use user-facing strings through `QApplication.translate()`.

**Dependencies:**

- Phase 1 establishes visual language.
- Phase 2 or Phase 3 should clarify which plot controls belong in the main screen.

**Exit Gate:**

- Core workflows require fewer visible controls in production mode.
- Expert mode remains functionally complete.

## Phase 5: Local QML Islands

**Goal:** Use Qt Quick only where it offers clear value.

**Closed at local-island level:** 2026-07-01 with an isolated `WorkspaceStatusModel` `QObject` and a small QML status panel string compiled by an offscreen `QQmlComponent` test. Follow-up slices add a `QQuickWidget` factory that loads the inline QML through a data URL, injects the Python model, updates macOS/Linux/Windows PyInstaller hidden imports for QtQuick/QML modules, exposes the island through a lazy View-menu dock entry, and adds autorun screenshot controls via `ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_MODE` plus `ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_STATUS_DOCK=1`. The first real screenshot smoke caught and fixed a dock-width clipping defect; current screenshot evidence is `/tmp/artisanz-phase5-qml-dock.png`. A standalone `python -m artisanlib.qtquick_packaging_smoke` command now verifies PyInstaller availability, real PyQt6 QtQuick/QML module imports, platform spec hidden imports, and the offscreen QML widget path; the widget portion runs in a subprocess in tests to avoid repeated QtQuickWidgets initialization crashes. The dock now reflects the Phase 2 renderer-selection seam by showing the selected renderer label and fallback status from `qmc.plot_renderer_selection`, plus a 2026-07-02 workspace action hint exposed from `WorkspaceStatusModel`; current renderer-status screenshot evidence is `/tmp/artisanz-phase5-renderer-status.png`. A 60-second simulator screenshot exposed that a restored visible dock could be empty before the lazy QML widget was created; `visibilityChanged` now creates and syncs the widget whenever the dock becomes visible, and the re-run screenshot evidence is `/tmp/artisanz-phase0-60s-after-dock-fix-live-sim.png`. This validates the Python-to-QML state seam without moving the roast graph or settings dialogs to QML.

**Candidate Work:**

- Prototype a read-only monitor dashboard or status panel.
- Expose Python state via QObject properties/models.
- Keep QML assets isolated from the core roast graph until proven.
- Validate macOS/Linux/Windows packaging implications.

**Dependencies:**

- Phase 3 should provide clean state snapshots.

**Exit Gate:**

- QML panel runs without packaging regressions.
- The panel is easier to maintain or visibly better than the Widgets equivalent.

## Phase 6: Plugin Boundary Exploration

**Goal:** Prepare the codebase for long-term customization and optional commercial-product divergence.

**Closed at typed-boundary level:** 2026-07-01 with a side-effect-light renderer plugin registry that describes the existing Matplotlib and PyQtGraph snapshot adapters as built-in renderer plugins. Follow-up work adds a `create_renderer()` factory that can instantiate built-in or externally registered renderers by id after dependency checks, plus a headless-safe factory smoke runner that renders the same synthetic roast snapshot through either built-in renderer id, `matplotlib-snapshot` or `pyqtgraph-snapshot`. The renderer plugin metadata now records the required rendering surface, and the runtime registry can opt-in to package-external `.py` plugin files from `ARTISANZ_RENDERER_PLUGIN_PATH`. A 2026-07-02 closure slice adds typed plugin categories for renderer, report, analyzer, filter, and profile comparison. Non-renderer plugin specs can be registered and listed, but only renderer plugins can be loaded as live renderer classes. Filesystem-discovered plugin ids can render through the same factory smoke seam without changing `main.py`, `canvas.py`, or the live roast rendering path; the smoke CLI now uses the runtime registry, so an external plugin id can be verified from the command line as well. This meets the extension-boundary exit gate at smoke/runtime-registry level; live non-renderer plugin execution is deliberately outside the current GUI modernization scope.

**Candidate Work:**

- Start with renderer plugin boundaries.
- Explore report, analyzer, filter, and profile-comparison extension seams.
- Keep device driver pluginization last because it has the highest compatibility risk.

**Dependencies:**

- Phase 2 renderer boundary.
- Phase 3 data-processing boundary.

**Exit Gate:**

- At least one extension boundary can be swapped without editing `main.py` or `canvas.py` directly.

## Review Cadence

- Revisit this roadmap at the end of every phase.
- Update the phase status table before starting the next phase.
- Add measured results, screenshots, or compatibility notes directly to this file or to phase-specific reports.
- If upstream Artisan changes `main.py`, `canvas.py`, or dependencies substantially, rerun Phase 0 before continuing deeper modernization.
