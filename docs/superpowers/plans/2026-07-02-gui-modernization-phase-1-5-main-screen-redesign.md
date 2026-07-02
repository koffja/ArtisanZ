# GUI Modernization Phase 1.5 Main Screen Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ArtisanZ visibly modern on first launch by defaulting the live plot to PyQtGraph and applying an opinionated main-screen control-console visual language.

**Architecture:** Keep the existing PyQt6 Widgets runtime and current behavior paths. Use renderer selection to default to `pyqtgraph-snapshot` with Matplotlib as fallback, then apply property-targeted styling to the main screen instead of broad widget rewrites. Preserve `ARTISANZ_LEGACY_UI=1` and `ARTISANZ_RENDERER_ID=matplotlib-snapshot` as escape hatches.

**Tech Stack:** PyQt6 Widgets, PyQtGraph, existing ArtisanZ stylesheet/theme tokens, existing GUI autorun screenshot and performance probes.

---

## Design Direction

Subject: a roast control console for an operator who needs fast visual hierarchy under heat, noise, and time pressure.

Palette:
- `charcoal`: `#20272B`
- `porcelain`: `#F7F4EA`
- `control_blue`: `#376B7A`
- `charge_clay`: `#B4685C`
- `bean_green`: `#6F875E`
- `line_mist`: `#D7DDDE`

Type:
- Use Qt's platform sans fonts, but make data/control hierarchy stronger through weight, spacing, and size rather than introducing a risky bundled font dependency.

Layout signature:
- The first screen should read as a control console: a distinct top command rail, a pale full-width graph well, bottom major event controls, and compact right-side telemetry cards.

## Task 1: Make PyQtGraph the Default Renderer

**Files:**
- Modify: `src/artisanlib/plot_renderer_settings.py`
- Modify: `src/artisanlib/workspace_status_model.py`
- Modify: `src/test/unitary/artisanlib/test_plot_renderer_settings.py`
- Modify: `src/test/unitary/artisanlib/test_canvas_renderer_selection.py`
- Modify: `src/test/unitary/artisanlib/test_workspace_status_model.py`

- [x] Change `DEFAULT_RENDERER_ID` from `matplotlib-snapshot` to `pyqtgraph-snapshot`.
- [x] Keep fallback behavior to Matplotlib if PyQtGraph is unavailable or fails at runtime.
- [x] Update tests so default selection and workspace status expect PyQtGraph.
- [x] Verify Matplotlib override still works with `ARTISANZ_RENDERER_ID=matplotlib-snapshot`.

## Task 2: Add Main-Screen Visual Roles

**Files:**
- Modify: `src/artisanlib/main.py`
- Modify: `src/test/unitary/artisanlib/test_main.py`

- [x] Assign `mainControlRole` properties to Reset, ON/OFF, START/STOP, and Control buttons.
- [x] Assign `roastEventRole` properties to Charge, Drop, dry/crack/cool, and aux event buttons.
- [x] Mark the graph widget and lower event rail with stable properties for stylesheet targeting.
- [x] Mark LCD frames with a `telemetryCard` property while preserving the existing `lcdSurface` property.

## Task 3: Apply a More Distinct Main-Screen Theme

**Files:**
- Modify: `src/artisanlib/gui_theme.py`
- Modify: `src/test/unitary/artisanlib/test_gui_theme.py`

- [x] Update `ModernTheme` tokens away from neutral desktop grey into a clearer roast-console palette.
- [x] Add stylesheet rules for `mainGraphPanel`, `mainControlRole`, `roastEventRail`, `roastEventRole`, and `telemetryCard`.
- [x] Replace the fragile nested LCD card/value treatment with transparent LCD containers and self-contained rounded value surfaces.
- [x] Add tests that assert the new targeted selectors exist.

## Task 4: Baseline and Visual Evidence

**Files:**
- Modify: `docs/GUI_MODERNIZATION_BASELINE.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: this plan.

- [x] Run focused unit tests for renderer selection, canvas renderer selection, workspace status, GUI theme, and main UI properties.
- [x] Run py_compile and ruff on touched files.
- [x] Capture default-launch screenshot with no renderer env override; it should report PyQtGraph in Workspace Status when the dock is visible.
- [x] Capture `ARTISANZ_RENDERER_ID=matplotlib-snapshot` override screenshot or at least run focused selector tests to prove fallback remains accessible.
- [x] Update docs with screenshot paths and metrics.

## Task 5: PyQtGraph Visual Parity Follow-up

**Files:**
- Modify: `src/artisanlib/plot_pyqtgraph_widget.py`
- Modify: `src/artisanlib/canvas.py`
- Modify: `src/artisanlib/axis.py`
- Modify: `src/artisanlib/main.py`
- Modify: `src/artisanlib/gui_theme.py`

- [x] Render RoR on the same PyQtGraph plot as temperature using a linked right-side axis.
- [x] Add a Config > Axes time-label mode control for minute labels vs second labels.
- [x] Apply PyQtGraph x/y/RoR tick spacing from the existing axis settings, including temperature grid step.
- [x] Make PyQtGraph grid rendering use the existing grid visibility and opacity controls with a visible minimum alpha.
- [x] Constrain and wrap LCD telemetry labels so long titles cannot widen the right-side card column.
- [x] Add spacing above the bottom event rail.

## Task 6: Phase 1.6 Visual Parity Handoff

**Files:**
- Modify: `src/artisanlib/plot_pyqtgraph_widget.py`
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Modify: `src/artisanlib/plot_snapshot_extractor.py`
- Modify: `src/artisanlib/gui_theme.py`
- Modify: `src/artisanlib/main.py`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Add: `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md`

- [x] Replace faint PyQtGraph built-in grid rendering with a dedicated grid overlay tied to the existing grid visibility, opacity, width, color, and tick-step settings.
- [x] Make default phase background bands visibly distinct with soft Morandi colors while preserving user/custom palette overrides.
- [x] Remove the right LCD outer visual frame so the value surface cannot visually detach from a nested rounded rectangle.
- [x] Apply a flatter light Morandi base to standard dialogs and dialog controls.
- [x] Track remaining Matplotlib overlay parity gaps as executable Phase 1.6 tasks.

## Implementation Results

- Default renderer now resolves to `pyqtgraph-snapshot`; `ARTISANZ_RENDERER_ID=matplotlib-snapshot` keeps the compatibility path available.
- Historical profile redraws now sync a full canvas snapshot into the embedded PyQtGraph renderer, so default profile loading is nonblank instead of only supporting future live frames.
- Runtime PyQtGraph snapshot failures fall back to the Matplotlib canvas and record `pyqtgraph_snapshot_error`.
- The PyQtGraph widget now allows horizontal compression, preserves the right-side LCD telemetry column beside the plot, uses a single plot with a right-side RoR axis, and formats the default time axis in minutes.
- Config > Axes now persists `time_axis_label_mode` with Minutes/Seconds choices, while the existing x/y/RoR step controls drive PyQtGraph ticks.
- PyQtGraph gridlines now use a dedicated overlay instead of relying on faint built-in grid rendering, and default phase backgrounds use higher-contrast Morandi colors.
- LCD telemetry containers are transparent; only the data surface is visually framed, which removes the recurring nested-card alignment defect.
- Standard dialogs now inherit a flatter light Morandi base before individual high-traffic dialogs are redesigned.
- The bottom event rail has more top/bottom breathing room.
- Main-screen visual roles are present for top control buttons, event buttons, graph panel, event rail, and telemetry cards.
- Focused tests currently pass: `252 passed, 1 skipped, 2 warnings` for the GUI/PyQtGraph visual-parity subset; earlier Phase 1.5 focused suite remains covered by the default-renderer tests.
- Visual evidence:
  - Default PyQtGraph screenshot: `/tmp/artisanz-phase15-default-pyqtgraph.png`
  - Matplotlib override screenshot: `/tmp/artisanz-phase15-matplotlib-override.png`
  - PyQtGraph axis/LCD follow-up screenshot: `/tmp/artisanz-pyqtgraph-axis-fixes.png`

## Self-Review

- Spec coverage: The user asked to begin replacing Matplotlib by changing defaults and to start Phase 1.5. This plan does both while retaining fallback safety.
- Placeholder scan: No `TBD` or unspecified implementation steps remain.
- Type consistency: Renderer ids remain the existing string ids; stylesheet selectors use Qt dynamic properties already used by LCD styling.
