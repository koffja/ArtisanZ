# ArtisanZ GUI Modernization Roadmap

**Purpose:** Track the multi-phase GUI modernization effort from measurement through visual refresh, plotting improvements, processing decoupling, and optional QML adoption.

**Status:** Phase 0 automated profile redraw baseline and a 20-second internal simulator live-sampling smoke baseline are captured as of 2026-06-29. Phase 1 Widgets visual modernization has a main-screen first pass with corrected LCD spacing, label padding, and full-width bottom value surfaces. Phase 2 has a renderer snapshot contract, a canvas-like extractor with foreground event markers, an unhooked Matplotlib adapter that renders snapshot events, offscreen Agg smoke coverage, and dependency-backed PyQtGraph smoke coverage. Phase 3 has started by extracting the live smoothing-weight decision and PID process-value source selection from `sample_processing()` into tested pure helpers; longer simulator/device baselines remain pending before broad threading work.

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
| 0 | Performance Baseline and Risk Map | Profile + simulator smoke baselines captured | Timing probes, benchmark workflow, baseline report | We know whether rendering, GUI-thread processing, locks, or device sampling dominate latency |
| 1 | Widgets Visual Modernization | Main-screen first pass + LCD value surface alignment corrected | Modern theme tokens and refreshed main roast screen styling | Main screen looks modern while behavior and settings compatibility remain intact |
| 2 | Plot Renderer Boundary and PyQtGraph POC | Renderer boundary + dependency-backed PyQtGraph smoke complete | Read-only plot snapshot model, Matplotlib adapter, PyQtGraph live adapter prototype | POC is ready for benchmark comparison before any live renderer swap |
| 3 | Sampling Post-Processing Decoupling | Started: smoothing weights + PID input selection extracted | Pure data pipeline for filtering, RoR, PID inputs, alarm/event decisions | GUI thread consumes snapshots instead of doing heavy processing inline |
| 4 | Main UI Information Architecture | Not started | Scenario-oriented Roast Control, QC Analysis, and Device Setup workspaces | Users can switch task modes without losing existing expert controls |
| 5 | Local QML Islands | Not started | A limited Qt Quick panel or dashboard backed by Python state models | QML proves useful without breaking packaging, translations, or Windows portable build |
| 6 | Plugin Boundary Exploration | Not started | Renderer/report/filter/analyzer extension seams | Future customization can be isolated without destabilizing upstream sync |

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

**Implementation Note:** Timing probes, automatic/default JSONL export, `atexit` export fallback, JSONL summary utility, automated profile redraw autorun, and internal simulator-recording autorun are in place. The 20-second simulator smoke baseline shows `sample_processing` is not the immediate short-window bottleneck; prioritize Phase 2 renderer-boundary planning before Phase 3 processing extraction, but keep longer simulator/device runs as a gate before broad threading changes.

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

## Phase 2: Plot Renderer Boundary and PyQtGraph POC

**Goal:** Make the live plot renderer replaceable without forcing a full Matplotlib rewrite.

**Started:** 2026-06-29 with a data-only `plot_snapshot.py` contract, `plot_snapshot_extractor.py` canvas-like snapshot builder with foreground event marker extraction, `plot_matplotlib_adapter.py` compatibility adapter with event-marker rendering, `plot_matplotlib_smoke.py` offscreen Agg diagnostic path, `plot_pyqtgraph_adapter.py` as a PyQtGraph-style POC adapter, and `plot_pyqtgraph_smoke.py` as a real PyQtGraph/PyOpenGL dependency smoke path. These do not change runtime plotting behavior yet; they prepare a stable renderer-facing surface before benchmark-backed live canvas integration.

**Completion Note:** The Phase 2 renderer-boundary POC is complete at code level and now has real `pyqtgraph==0.14.0` / `PyOpenGL==3.1.10` smoke coverage. Do not replace the live `canvas.py` renderer until the PyQtGraph path is benchmarked against the Phase 0 scenarios.

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

**Started:** 2026-06-29 with `sample_processing.py`, tested pure helpers for choosing decay smoothing weights and selecting the PID process value from ET, BT, or extra-device channels. `canvas.py` still owns live mutation, PID calls, event/alarm signals, and rendering; these first slices remove deterministic decisions from the 692-line GUI-thread method without moving side effects.

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
