# GUI Modernization Phase 1.6/4/5/6 Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Close the current GUI modernization gaps in PyQtGraph visual parity, high-traffic dialog styling, and the Phase 4/5/6 workspace/QML/plugin skeletons.

**Architecture:** Keep Matplotlib as the compatibility/export backend while making the default PyQtGraph view visibly complete for high-value overlays. Use scoped dynamic Qt properties for dialog styling so legacy dialogs are not globally restyled by accident. Convert Phase 4/5/6 from passive infrastructure into a visible, tested workspace status/action surface and a typed plugin registry boundary.

**Tech Stack:** PyQt6 Widgets, PyQtGraph, Qt Quick/QML, existing snapshot renderer boundary, existing workspace and renderer plugin models.

---

## Design Direction

Subject: a production roast control console. The visual signature is a soft instrumentation palette: pale porcelain work surfaces, sage/blue-green operational accents, low-contrast Morandi phase fields, and clear data overlays. The single risk taken here is removing decorative LCD outer cards entirely and relying on disciplined value surfaces, because nested card/value rectangles have repeatedly produced alignment defects.

## File Map

- `src/artisanlib/plot_snapshot.py`: add renderer-neutral guide and event-value overlay dataclasses.
- `src/artisanlib/plot_snapshot_extractor.py`: extract event value rails, AUC/BBP guide markers, and charge-target markers when source data exists.
- `src/artisanlib/plot_pyqtgraph_adapter.py`: render guide lines and event-value rails in PyQtGraph.
- `src/artisanlib/dialogs.py`: apply common modern dialog dynamic properties in the base dialog.
- `src/artisanlib/axis.py`, `src/artisanlib/curves.py`, `src/artisanlib/events.py`, `src/artisanlib/alarms.py`: mark high-traffic dialogs with stable roles.
- `src/artisanlib/gui_theme.py`: add scoped modern dialog rules for group boxes, tabs, tables, headers, and role-specific accents.
- `src/artisanlib/ui_workspaces.py`: add concise action hints for each workspace.
- `src/artisanlib/workspace_status_model.py`: expose the action hint to QML and show it in the status island.
- `src/artisanlib/plot_renderer_registry.py`: add plugin categories so renderer/report/analyzer/filter boundaries are typed, while only renderer plugins are instantiable today.
- Tests under `src/test/unitary/artisanlib/`: cover the new data contracts, renderer calls, dialog properties, workspace hints, and plugin category behavior.
- Docs: update Phase 1.6 plan, baseline, and roadmap status.

## Task 1: PyQtGraph Overlay Parity Closure

**Files:**
- Modify: `src/artisanlib/plot_snapshot.py`
- Modify: `src/artisanlib/plot_snapshot_extractor.py`
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot.py`
- Modify: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`
- Modify: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`

- [x] Add immutable `GuideLineSnapshot` and `EventValueSnapshot` data contracts.
- [x] Include `guides` and `event_values` in `RoastPlotSnapshot`.
- [x] Extract foreground/background event value rails from existing event marker data when event values are present.
- [x] Extract AUC, BBP, and charge-target guides only when source attributes exist.
- [x] Render guides and event-value rails in `PyQtGraphSnapshotRenderer`.
- [x] Keep export/report compatibility explicitly Matplotlib-backed in docs; PyQtGraph parity here is visual/runtime, not report export replacement.

## Task 2: Scoped Dialog Modernization Closure

**Files:**
- Modify: `src/artisanlib/dialogs.py`
- Modify: `src/artisanlib/axis.py`
- Modify: `src/artisanlib/curves.py`
- Modify: `src/artisanlib/events.py`
- Modify: `src/artisanlib/alarms.py`
- Modify: `src/artisanlib/gui_theme.py`
- Modify: `src/test/unitary/artisanlib/test_dialogs.py`
- Modify: `src/test/unitary/artisanlib/test_gui_theme.py`

- [x] Set `modernDialog=true` on `ArtisanDialog`.
- [x] Mark Axes, Curves, Events, and Alarms dialogs with role values.
- [x] Add scoped Morandi dialog rules for `QGroupBox`, `QTabWidget`, `QTabBar`, `QTableWidget`, `QHeaderView`, inputs, and dialog buttons.
- [x] Add tests proving the base property and role selectors exist.
- [x] Do not change persistence, validation, or dialog business logic.

## Task 3: Phase 4/5 Workspace Status Closure

**Files:**
- Modify: `src/artisanlib/ui_workspaces.py`
- Modify: `src/artisanlib/workspace_status_model.py`
- Modify: `src/test/unitary/artisanlib/test_ui_workspaces.py`
- Modify: `src/test/unitary/artisanlib/test_workspace_status_model.py`

- [x] Add one action hint per workspace mode.
- [x] Expose `actionHint` through `WorkspaceStatusModel`.
- [x] Render `actionHint` in the QML workspace status panel.
- [x] Keep QML dimensions stable and tests compiling.

## Task 4: Phase 6 Plugin Boundary Closure

**Files:**
- Modify: `src/artisanlib/plot_renderer_registry.py`
- Modify: `src/test/unitary/artisanlib/test_plot_renderer_registry.py`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

- [x] Add typed plugin categories for renderer, report, analyzer, filter, and profile comparison.
- [x] Keep runtime class validation strict for renderer plugins.
- [x] Allow non-renderer plugin specs to be registered and listed without pretending they are instantiable renderers.
- [x] Document that Phase 6 is closed at boundary level, with live non-renderer plugin execution deliberately outside current GUI modernization scope.

## Task 5: Verification and Documentation

**Files:**
- Modify: `docs/GUI_MODERNIZATION_BASELINE.md`
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md`
- Modify: this plan.

- [x] Run `python3 -m py_compile` for touched Python files.
- [x] Run focused pytest for plot snapshot/extractor/adapter, dialog/theme, workspace, QML model, and plugin registry.
- [x] Run `ruff check` for touched files.
- [x] Run PyQtGraph smoke and renderer factory smoke.
- [x] Update docs with what is closed and what remains intentionally delegated to Matplotlib/export compatibility or future real-device validation.

## Closure Definition

The requested items 1, 2, and 4 are closed when:

- PyQtGraph has visible grid, phases, event labels, event value rails, and guide annotations from the snapshot boundary.
- Axes/Curves/Events/Alarms inherit a scoped modern dialog chrome without behavior changes.
- Workspace/QML status exposes a concrete next action per mode, not only a label.
- Plugin registry can represent future renderer/report/analyzer/filter/profile-comparison seams while preserving strict renderer instantiation checks.
- Tests and smokes pass, and the plan/roadmap identify export parity and real-device OpenGL validation as deliberate future gates, not forgotten work.
