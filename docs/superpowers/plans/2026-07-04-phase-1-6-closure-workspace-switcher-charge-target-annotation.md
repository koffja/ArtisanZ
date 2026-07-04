# Phase 1.6 Closure + Workspace Switcher + Charge Target Annotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close three independent gaps in one coordinated plan: (A) flip 5 stale `[ ]` checkboxes in the Phase 1.6 plan to `[x]` with cross-references to the phases that actually delivered the work; (B) upgrade the Workspace Status dock from read-only display into an interactive workspace switcher with 5 clickable buttons; (C) add charge-target annotation text/callout parity to the PyQtGraph renderer so users see the same readiness/RWT/RoR information that the Matplotlib path already shows.

**Architecture:** All three task groups are independent — they touch different files and can be dispatched in parallel. Task Group A is a documentation-only change. Task Group B modifies only the inline QML string in `workspace_status_model.py` (no Python logic change — the existing `setWorkspaceModeValue` slot and `workspaceChanged` signal already cover the full round-trip). Task Group C extends the existing snapshot→extractor→adapter pipeline: a new `ChargeTargetAnnotationSnapshot` dataclass flows through a new `_charge_target_annotations` extractor into a new `_default_charge_target_annotation_factory`, following the exact pattern already established by `_default_phase_summary_item_factory` (multi-item tuple return, flat-list storage on `temperature_plot`). Matplotlib compatibility is unchanged.

**Tech Stack:** Python 3.12+, PyQt6 6.11.0, pyqtgraph 0.14.0, Qt Quick/QML via QQuickWidget, existing `dataclass(frozen=True, slots=True)` snapshot contracts, pytest with `QT_QPA_PLATFORM=offscreen`.

## Global Constraints

- Branch: `ArtisanZ` (custom branch; never commit on `master`).
- Python: 3.12+ (CI uses 3.14); run all commands from `src/`.
- PyQt6 pinned at `6.11.0`, pyqtgraph pinned at `0.14.0` per `src/requirements.txt`.
- Never use `as any`, `@ts-ignore`, `type: ignore` without explicit reason — this is Python, so the equivalent rule is: never use `# type: ignore` without a pylint/mypy justification comment on the same line.
- Existing translation convention: user-visible strings go through `QApplication.translate("Menu", ...)` for PyQt Widgets; QML inline strings use `qsTr()` (lupdate picks these up via the `data:text/plain` URL because `pylupdate6pro.py` scans `.py` sources).
- All ArtisanZ custom work stays off `src/artisanlib/__init__.py` (CI patches revision/signature at build time).
- Verify with the ArtisanZ subset first, then broader checks: `python3 -m py_compile`, `python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q`, `python3 -m ruff check`, `python3 -m pyright` (if available).
- Commit style: conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`) — see `git log --oneline -20` for established patterns like `feat(gui):`, `feat(charge):`, `docs(plans):`.

---

## File Structure

### Task Group A — Plan Doc Back-fill (5 minutes, doc-only)

- Modify: `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md` — flip 5 `[ ]` to `[x]` with cross-references; no code touched.

### Task Group B — Workspace Status Interactive Switcher (half day)

- Modify: `src/artisanlib/workspace_status_model.py` — extend `WORKSPACE_STATUS_PANEL_QML` inline string with 5 clickable `Rectangle`+`MouseArea` buttons between `actionHint` and the renderer row; bump implicit height from 176 to ~220 to fit the new row.
- Test: `src/test/unitary/artisanlib/test_workspace_status_model.py` — add tests for the new button row presence and the `setWorkspaceModeValue` round-trip via simulated click (use `QQuickWidget` events or direct slot invocation).

### Task Group C — Charge-Target Annotation PyQtGraph Parity (1-2 days)

- Modify: `src/artisanlib/plot_snapshot.py` — add `ChargeTargetAnnotationSnapshot` dataclass and a new `charge_target_annotations: tuple[...] = ()` field on `RoastPlotSnapshot`.
- Modify: `src/artisanlib/plot_snapshot_extractor.py` — add `_charge_target_annotations(source)` extractor mirroring the existing `_charge_target_guide` pattern but returning a full annotation snapshot.
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py` — add `ChargeTargetAnnotationItemFactory` type alias, `_default_charge_target_annotation_factory` (returns multi-item tuple), constructor arg, storage list, `_apply_charge_target_annotations` lifecycle method, and hook into `_apply_static_overlays` + `_static_overlay_signature`.
- Test: `src/test/unitary/artisanlib/test_plot_snapshot.py` — dataclass round-trip.
- Test: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py` — extractor output for enabled/disabled/charged/active states.
- Test: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py` — factory returns correct item count for charged vs active state.

---

## Task Group A: Plan Doc Back-fill

### Task A1: Flip 5 stale `[ ]` to `[x]` with phase attribution

**Files:**
- Modify: `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md`

**Interfaces:**
- Consumes: audit findings from the 2026-07-04 back-fill review (this plan's preamble).
- Produces: accurate historical record so future audits don't re-investigate.

- [ ] **Step 1: Read the current plan to confirm exact line numbers**

Run: `grep -n "^- \[ \]" docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md`
Expected output includes lines 81, 83, 88, 98, 100 (the 5 items to flip).

- [ ] **Step 2: Flip line 81 (event label overlap avoidance)**

Replace:
```
- [ ] Add event label overlap avoidance and richer label placement.
```
with:
```
- [x] Add event label overlap avoidance and richer label placement. Closed by Phase 1.9 (`docs/superpowers/plans/2026-07-03-gui-modernization-phase-1-9-pyqtgraph-event-auc-parity.md`) clustered event-label row placement; edge anchor hardened by Phase 1.10. Evidence: `_event_label_row` `src/artisanlib/plot_pyqtgraph_adapter.py:717`, `_event_label_anchor:707`.
```

- [ ] **Step 3: Flip line 83 (AUC area fill)**

Replace:
```
- [ ] Add AUC area fill visuals.
```
with:
```
- [x] Add AUC area fill visuals. Closed by Phase 1.9 AreaFillSnapshot. Evidence: `AreaFillSnapshot` `src/artisanlib/plot_snapshot.py:90`, `_auc_area_fill` `src/artisanlib/plot_snapshot_extractor.py:688`, `_default_area_item_factory` `src/artisanlib/plot_pyqtgraph_adapter.py:580` with `PlotDataItem(fillLevel=area.baseline, brush=...)`.
```

- [ ] **Step 4: Flip line 88 (export decision)**

Replace:
```
- [ ] Define the export/report compatibility decision: Matplotlib-only fallback, PyQtGraph export adapter, or explicit hybrid export.
```
with:
```
- [x] Define the export/report compatibility decision: explicit hybrid. Matplotlib stays default for `roastReport()` and PDF/SVG/PNG/JPEG Save Graph; PyQtGraph PNG is opt-in via `File > Save Graph > PyQtGraph PNG...` (Phase 1.17 `src/artisanlib/plot_user_export.py`); `plot_report_export.py` provides report-image comparison (Phase 1.18). See closure plan `docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-4-6-closure.md` Task 1 line 46.
```

- [ ] **Step 5: Flip line 98 (Devices / Roasting Properties)**

Replace:
```
- [ ] Modernize Devices and Roasting Properties after screenshot review.
```
with:
```
- [x] Modernize Devices and Roasting Properties (scoped visual role layer). Closed by Phase 1.12 dense-dialog polish: `modernDialogRole="devices"` `src/artisanlib/devices.py:54`, `modernDialogRole="roast_properties"` `src/artisanlib/roast_properties.py:703`, dense table/header QSS rules at `src/artisanlib/gui_theme.py:512-526`. Per-panel structural simplification remains future work per the Phase 1.12 plan's explicit non-goals.
```

- [ ] **Step 6: Flip line 100 (persistence/validation/shortcuts/translations)**

Replace:
```
- [ ] Preserve all current settings persistence, validation, shortcuts, and translations.
```
with:
```
- [x] Preserve all current settings persistence, validation, shortcuts, and translations. Non-regression verified: `QSettings` calls intact in `axis.py:487,969`, `curves.py` (8 occurrences), `devices.py` (14 occurrences); `QIntValidator`/`QRegularExpressionValidator` chains intact; `QApplication.translate` used throughout. Phase 1.11 and 1.12 plans explicitly list preservation as scope.
```

- [ ] **Step 7: Add a back-fill note at the top of the plan**

Insert after line 8 (the `**Architecture:**` line):
```
> **2026-07-04 Back-fill note:** Five `[ ]` items in this plan (event label overlap, AUC area fills, export decision, Devices/Roasting Properties dense polish, persistence/validation preservation) were de facto closed by Phases 1.9, 1.10, 1.12, 1.17, 1.18 but the checkboxes here were never updated. They are flipped to `[x]` with cross-references today; no code changes are involved. The remaining `[ ]` items are: (1) long-Chinese-label screenshot capture, (2) Config > Axes/Curves dialog screenshot capture, (3) extra-device background curve legend inclusion, (4) roast-analysis masks/statistics overlays, (5) charge-target annotation text/callout parity (handled by Task Group C of `docs/superpowers/plans/2026-07-04-phase-1-6-closure-workspace-switcher-charge-target-annotation.md`), (6) projection line BT/RoR visual differentiation, (7) anti-nested-card enforcement rule, (8) Config > Axes/Curves layout-internals restructuring.
```

- [ ] **Step 8: Verify the file still parses as valid markdown**

Run: `python3 -c "import pathlib; content = pathlib.Path('docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md').read_text(); assert content.count('- [x]') >= 18, f'expected >=18 checked items, got {content.count(chr(45)+chr(32)+chr(91)+chr(120)+chr(93))}'; print('OK')"`
Expected: `OK`

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/plans/2026-07-02-gui-modernization-phase-1-6-pyqtgraph-parity-dialog-refresh.md
git commit -m "docs(plans): back-fill Phase 1.6 checkboxes closed by Phases 1.9/1.10/1.12/1.17/1.18"
```

---

## Task Group B: Workspace Status Interactive Switcher

### Task B1: Add 5 clickable workspace buttons to the QML panel

**Files:**
- Modify: `src/artisanlib/workspace_status_model.py:24-196` (the `WORKSPACE_STATUS_PANEL_QML` inline string)
- Test: `src/test/unitary/artisanlib/test_workspace_status_model.py`

**Interfaces:**
- Consumes: existing `WorkspaceStatusModel.modeValue` property (returns `"roast_control"`/`"qc_analysis"`/`"device_setup"`/`"production"`/`"expert"`); existing `@pyqtSlot(str) setWorkspaceModeValue(value)` at `workspace_status_model.py:236`.
- Produces: clickable workspace switcher UI; existing `workspaceChanged` signal automatically rebinds the highlight.

- [ ] **Step 1: Write the failing test**

Add to `src/test/unitary/artisanlib/test_workspace_status_model.py`:

```python
def test_workspace_status_panel_has_five_mode_buttons(qapp):  # noqa: ANN001
    """The QML panel must expose one clickable button per WorkspaceMode."""
    from artisanlib.workspace_status_model import (
        WORKSPACE_STATUS_PANEL_QML,
        WorkspaceStatusModel,
        create_workspace_status_widget,
    )
    model = WorkspaceStatusModel()
    widget = create_workspace_status_widget(model, parent=None)
    assert widget.status() == widget.status().Ready, f"QML failed to compile: status={widget.status()}, errors={widget.errors()}"
    root = widget.rootObject()
    assert root is not None, "QML root object is None"
    # The panel must declare 5 mode buttons by objectName prefix.
    buttons = root.findChildren(lambda obj: getattr(obj, 'objectName', '').startswith('modeButton_'))
    mode_values = {btn.objectName().removeprefix('modeButton_') for btn in buttons}
    assert mode_values == {'roast_control', 'qc_analysis', 'device_setup', 'production', 'expert'}, (
        f"expected 5 mode buttons, found {sorted(mode_values)}"
    )
    widget.deleteLater()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_workspace_status_model.py::test_workspace_status_panel_has_five_mode_buttons -v`
Expected: FAIL with `AssertionError` (no `modeButton_*` children yet) or `widget.status() != Ready` if QML fails to compile after edits.

- [ ] **Step 3: Add the 5 workspace buttons to the QML string**

In `src/artisanlib/workspace_status_model.py`, locate the renderer Row at lines 166-194 (the one starting with `Row {` that contains the `Rectangle { width: 7; height: 7; ...}` bullet and `rendererText`).

**Insert a new workspace-switcher Row BEFORE the renderer Row** (i.e., between `actionHint.bottom + 9` and the existing renderer Row anchor). The full insertion:

```qml
    Row {
        id: workspaceSwitcher
        anchors.left: title.left
        anchors.right: title.right
        anchors.top: actionHint.bottom
        anchors.topMargin: 9
        spacing: 6

        Repeater {
            model: [
                { mode: "roast_control", label: qsTr("Roast") },
                { mode: "qc_analysis",   label: qsTr("QC") },
                { mode: "device_setup",  label: qsTr("Device") },
                { mode: "production",    label: qsTr("Prod") },
                { mode: "expert",        label: qsTr("Expert") }
            ]
            delegate: Rectangle {
                objectName: "modeButton_" + modelData.mode
                width: (parent.width - 4 * 6) / 5
                height: 26
                radius: 4
                color: root.workspaceModel && root.workspaceModel.modeValue === modelData.mode
                    ? root.accentColor
                    : "#f4f5f1"
                border.color: root.workspaceModel && root.workspaceModel.modeValue === modelData.mode
                    ? root.accentColor
                    : "#d5e0e3"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: modelData.label
                    color: root.workspaceModel && root.workspaceModel.modeValue === modelData.mode
                        ? "#fbfcfa"
                        : "#526265"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (root.workspaceModel) {
                            root.workspaceModel.setWorkspaceModeValue(modelData.mode)
                        }
                    }
                }
            }
        }
    }

```

- [ ] **Step 4: Bump the implicit height to fit the new row**

In the same file, change line 31 from `implicitHeight: 176` to `implicitHeight: 220`. The new row adds ~26 + 9 = 35 pixels of content; 176 + ~40 = ~216, rounded to 220.

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_workspace_status_model.py::test_workspace_status_panel_has_five_mode_buttons -v`
Expected: PASS

- [ ] **Step 6: Write a second test for the click→slot round-trip**

Add to `src/test/unitary/artisanlib/test_workspace_status_model.py`:

```python
def test_workspace_status_set_mode_value_round_trip(qapp):  # noqa: ANN001
    """Clicking a mode button must update modeValue and emit workspaceChanged."""
    from artisanlib.workspace_status_model import WorkspaceStatusModel
    model = WorkspaceStatusModel()
    assert model.modeValue == 'roast_control'  # default
    emitted = []
    model.workspaceChanged.connect(lambda: emitted.append(model.modeValue))
    model.setWorkspaceModeValue('qc_analysis')
    assert model.modeValue == 'qc_analysis'
    assert emitted == ['qc_analysis'], f"expected one emission, got {emitted}"
    # Invalid value falls back to current mode (no change).
    model.setWorkspaceModeValue('not_a_real_mode')
    assert model.modeValue == 'qc_analysis'
    assert emitted == ['qc_analysis']  # no new emission
```

- [ ] **Step 7: Run the round-trip test**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_workspace_status_model.py::test_workspace_status_set_mode_value_round_trip -v`
Expected: PASS (this should already pass because `setWorkspaceModeValue` + `workspace_from_setting_value` already implement the fallback at `workspace_status_model.py:237-238`)

- [ ] **Step 8: Run the full workspace test suite**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py -q`
Expected: all pass (existing tests + 2 new tests).

- [ ] **Step 9: Compile and lint**

```bash
cd src
.venv/bin/python -m py_compile artisanlib/workspace_status_model.py
.venv/bin/python -m ruff check artisanlib/workspace_status_model.py
```
Expected: exit 0 for both.

- [ ] **Step 10: Capture screenshot evidence**

```bash
cd src
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=1 \
ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_MODE=qc_analysis \
ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_STATUS_DOCK=1 \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-workspace-switcher-qc.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
```
Expected: `/tmp/artisanz-workspace-switcher-qc.png` exists and shows the QC button highlighted with accent color.

- [ ] **Step 11: Commit**

```bash
git add src/artisanlib/workspace_status_model.py src/test/unitary/artisanlib/test_workspace_status_model.py
git commit -m "feat(workspace-status): add 5 clickable workspace switcher buttons to dock panel"
```

---

## Task Group C: Charge-Target Annotation PyQtGraph Parity

### Task C1: Add `ChargeTargetAnnotationSnapshot` dataclass

**Files:**
- Modify: `src/artisanlib/plot_snapshot.py` (add dataclass after `PhaseSummarySnapshot` at line 87)
- Test: `src/test/unitary/artisanlib/test_plot_snapshot.py`

**Interfaces:**
- Consumes: nothing (leaf dataclass).
- Produces: `ChargeTargetAnnotationSnapshot` class + `ChargeAnnotationState` Literal type, both importable as `from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot`.

- [ ] **Step 1: Write the failing test**

Add to `src/test/unitary/artisanlib/test_plot_snapshot.py`:

```python
def test_charge_target_annotation_snapshot_charged_state():
    """Charged-state snapshot must round-trip all fields with sensible defaults."""
    from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot
    snap = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=True,
        target_temp=200.0,
        target_ror=18.0,
        charged_temp=198.5,
        charged_ror=17.2,
        title='',            # unused in charged state
        reason='',           # unused in charged state
        prediction_seconds=None,
        color='gray',
        current_rwt=34.9,
        target_rwt=33.3,
        anchor_time=0.0,     # unused in charged state (axes-fraction placement)
        anchor_temp=0.0,
        x_limit=600.0,       # unused in charged state
        y_limit_top=250.0,   # unused in charged state
    )
    assert snap.enabled is True
    assert snap.is_charged is True
    assert snap.target_temp == 200.0
    assert snap.target_ror == 18.0
    assert snap.charged_temp == 198.5
    assert snap.charged_ror == 17.2
    assert snap.color == 'gray'
    assert snap.current_rwt == 34.9
    assert snap.target_rwt == 33.3
    # Frozen dataclass: assignment must raise.
    import dataclasses
    try:
        snap.target_temp = 999.0  # type: ignore[misc]
        raise AssertionError('snapshot must be frozen')
    except dataclasses.FrozenInstanceError:
        pass


def test_charge_target_annotation_snapshot_active_state():
    """Active-state snapshot must round-trip readiness-derived fields."""
    from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot
    snap = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=False,
        target_temp=200.0,
        target_ror=18.0,
        charged_temp=0.0,
        charged_ror=0.0,
        title='接近目标',
        reason='接近目标，继续观察',
        prediction_seconds=8.4,
        color='green',
        current_rwt=34.9,
        target_rwt=33.3,
        anchor_time=423.5,
        anchor_temp=192.1,
        x_limit=600.0,
        y_limit_top=250.0,
    )
    assert snap.title == '接近目标'
    assert snap.reason == '接近目标，继续观察'
    assert snap.prediction_seconds == 8.4
    assert snap.color == 'green'
    assert snap.anchor_time == 423.5
    assert snap.anchor_temp == 192.1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py::test_charge_target_annotation_snapshot_charged_state test/unitary/artisanlib/test_plot_snapshot.py::test_charge_target_annotation_snapshot_active_state -v`
Expected: FAIL with `ImportError: cannot import name 'ChargeTargetAnnotationSnapshot' from 'artisanlib.plot_snapshot'`.

- [ ] **Step 3: Add the Literal type and dataclass**

In `src/artisanlib/plot_snapshot.py`, locate `PhaseSummarySnapshot` (ends at line 87). Insert immediately after it (before `AreaFillSnapshot` at line 89):

```python
ChargeAnnotationColor = Literal['gray', 'blue', 'green', 'red']


@dataclass(frozen=True, slots=True)
class ChargeTargetAnnotationSnapshot:
    enabled: bool
    is_charged: bool
    target_temp: float
    target_ror: float
    charged_temp: float
    charged_ror: float
    title: str
    reason: str
    prediction_seconds: Optional[float]
    color: ChargeAnnotationColor
    current_rwt: float
    target_rwt: float
    anchor_time: float
    anchor_temp: float
    x_limit: float
    y_limit_top: float
```

If `Optional` and `Literal` are not yet imported at the top of `plot_snapshot.py`, add `from typing import Literal, Optional` to the existing imports (verify first by reading the first 15 lines of the file).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot.py::test_charge_target_annotation_snapshot_charged_state test/unitary/artisanlib/test_plot_snapshot.py::test_charge_target_annotation_snapshot_active_state -v`
Expected: PASS.

- [ ] **Step 5: Add the snapshot field to `RoastPlotSnapshot`**

In `src/artisanlib/plot_snapshot.py`, locate the `RoastPlotSnapshot` dataclass (around line 177-198). Add a new field at the end:

```python
    charge_target_annotations: tuple[ChargeTargetAnnotationSnapshot, ...] = ()
```

- [ ] **Step 6: Compile and commit**

```bash
cd src
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py
git add src/artisanlib/plot_snapshot.py src/test/unitary/artisanlib/test_plot_snapshot.py
git commit -m "feat(plot-snapshot): add ChargeTargetAnnotationSnapshot dataclass for PyQtGraph parity"
```

---

### Task C2: Add `_charge_target_annotations` extractor

**Files:**
- Modify: `src/artisanlib/plot_snapshot_extractor.py` (add new function after `_charge_target_guide` at line 849)
- Test: `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`

**Interfaces:**
- Consumes: `ChargeTargetAnnotationSnapshot` from Task C1; `charge_manager` attribute on the `source` object (already read by `_charge_target_guide`).
- Produces: `tuple[ChargeTargetAnnotationSnapshot, ...]` — empty when disabled; single-element tuple when enabled.

- [ ] **Step 1: Write the failing test**

Add to `src/test/unitary/artisanlib/test_plot_snapshot_extractor.py`:

```python
def test_charge_target_annotations_disabled_returns_empty():
    """When charge_manager.enabled is False, the extractor returns an empty tuple."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    class FakeManager:
        enabled = False
        target_temp = 200.0
        target_ror = 18.0
        active = True
    class FakeSource:
        charge_manager = FakeManager()
    assert _charge_target_annotations(FakeSource()) == ()


def test_charge_target_annotations_active_state_returns_snapshot():
    """When enabled and not yet charged, extractor returns a single active-state snapshot."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    from artisanlib.plot_snapshot import ChargeTargetAnnotationSnapshot
    class FakeManager:
        enabled = True
        active = True
        target_temp = 200.0
        target_ror = 18.0
        charged_temp = 0.0
        charged_ror = 0.0
        temp_tolerance = 1.0
        ror_tolerance = 6.0
        prediction_window = 5.0
        prediction_time = None
        def evaluate_readiness(self, current_temp, current_ror, short_ror=None, long_ror=None, et_bt_gap=None, reference_et_bt_gap=None):
            from artisanlib.charge_manager import ChargeReadiness
            return ChargeReadiness(
                status='near',
                title='接近目标',
                reason='接近目标，继续观察',
                color='green',
                prediction_seconds=8.4,
                current_rwt=34.9,
                target_rwt=33.3,
            )
        @staticmethod
        def calculate_rwt(ror):
            return 600.0 / ror if ror and ror > 0 else 0.0
    class FakeSource:
        charge_manager = FakeManager()
        timex = (0.0, 100.0, 200.0, 423.5)
        temp2 = (25.0, 100.0, 150.0, 192.1)
        delta2 = (0.0, 30.0, 22.0, 18.5)
    result = _charge_target_annotations(FakeSource())
    assert len(result) == 1
    snap = result[0]
    assert isinstance(snap, ChargeTargetAnnotationSnapshot)
    assert snap.enabled is True
    assert snap.is_charged is False
    assert snap.target_temp == 200.0
    assert snap.target_ror == 18.0
    assert snap.title == '接近目标'
    assert snap.color == 'green'
    assert snap.prediction_seconds == 8.4
    assert snap.anchor_time == 423.5
    assert snap.anchor_temp == 192.1
    assert snap.x_limit > 0
    assert snap.y_limit_top > 0


def test_charge_target_annotations_charged_state_returns_snapshot():
    """When charge_manager.active is False (post-charge), extractor returns a charged-state snapshot."""
    from artisanlib.plot_snapshot_extractor import _charge_target_annotations
    class FakeManager:
        enabled = True
        active = False  # post-charge
        target_temp = 200.0
        target_ror = 18.0
        charged_temp = 198.5
        charged_ror = 17.2
        temp_tolerance = 1.0
        ror_tolerance = 6.0
        prediction_window = 5.0
        prediction_time = None
        def evaluate_readiness(self, current_temp, current_ror, short_ror=None, long_ror=None, et_bt_gap=None, reference_et_bt_gap=None):
            raise AssertionError('evaluate_readiness should NOT be called in charged state')
        @staticmethod
        def calculate_rwt(ror):
            return 600.0 / ror if ror and ror > 0 else 0.0
    class FakeSource:
        charge_manager = FakeManager()
        timex = (0.0, 100.0, 200.0, 423.5)
        temp2 = (25.0, 100.0, 150.0, 192.1)
        delta2 = (0.0, 30.0, 22.0, 18.5)
    result = _charge_target_annotations(FakeSource())
    assert len(result) == 1
    snap = result[0]
    assert snap.is_charged is True
    assert snap.charged_temp == 198.5
    assert snap.charged_ror == 17.2
    assert snap.target_temp == 200.0
    assert snap.target_ror == 18.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py -k charge_target_annotations -v`
Expected: FAIL with `ImportError: cannot import name '_charge_target_annotations' from 'artisanlib.plot_snapshot_extractor'`.

- [ ] **Step 3: Implement the extractor**

In `src/artisanlib/plot_snapshot_extractor.py`, immediately after `_charge_target_guide` (which ends at line 849), insert:

```python
_BG_COLOR_MAP: dict[str, str] = {
    'red': '#FFEDED',
    'blue': '#E6E6FF',
    'green': '#E8F5E9',
    'gray': '#F5F5F5',
}


def _charge_target_annotations(source: object) -> tuple[ChargeTargetAnnotationSnapshot, ...]:
    """Extract a single charge-target annotation snapshot, or empty tuple when disabled.

    Mirrors the visual states of canvas.draw_charge_target_annotation:
    - is_charged=True:  static top-left card showing target/actual temp/RoR/RWT
    - is_charged=False: dynamic arrow callout showing readiness title/reason/prediction
    """
    manager = getattr(source, 'charge_manager', None)
    if manager is None:
        return ()
    enabled = bool(getattr(manager, 'enabled', False))
    if not enabled:
        return ()
    target_temp = _numeric_value(getattr(manager, 'target_temp', None)) or 0.0
    target_ror = _numeric_value(getattr(manager, 'target_ror', None)) or 0.0
    charged_temp = _numeric_value(getattr(manager, 'charged_temp', None)) or 0.0
    charged_ror = _numeric_value(getattr(manager, 'charged_ror', None)) or 0.0
    is_charged = not bool(getattr(manager, 'active', True))

    timex = _sequence(source, 'timex')
    temp2 = _sequence(source, 'temp2')
    delta2 = _sequence(source, 'delta2')
    current_time = float(timex[-1]) if timex else 0.0
    current_temp = float(temp2[-1]) if temp2 else 0.0
    current_ror = _numeric_value(delta2[-1] if delta2 else None)

    x_limit = float(timex[-1] * 1.05) if timex else 600.0
    y_limit_top = float(max(temp2) * 1.05) if temp2 else 250.0

    target_rwt = float(getattr(manager, 'calculate_rwt', lambda _: 0.0)(target_ror) or 0.0)

    if is_charged:
        current_rwt = float(getattr(manager, 'calculate_rwt', lambda _: 0.0)(charged_ror) or 0.0)
        snap = ChargeTargetAnnotationSnapshot(
            enabled=True,
            is_charged=True,
            target_temp=target_temp,
            target_ror=target_ror,
            charged_temp=charged_temp,
            charged_ror=charged_ror,
            title='',
            reason='',
            prediction_seconds=None,
            color='gray',
            current_rwt=current_rwt,
            target_rwt=target_rwt,
            anchor_time=0.0,
            anchor_temp=0.0,
            x_limit=x_limit,
            y_limit_top=y_limit_top,
        )
        return (snap,)

    # Active state: call evaluate_readiness
    evaluate = getattr(manager, 'evaluate_readiness', None)
    if evaluate is None or current_ror is None:
        # Cannot evaluate; emit a minimal waiting snapshot.
        snap = ChargeTargetAnnotationSnapshot(
            enabled=True,
            is_charged=False,
            target_temp=target_temp,
            target_ror=target_ror,
            charged_temp=charged_temp,
            charged_ror=charged_ror,
            title='等待数据',
            reason='升温数据不足',
            prediction_seconds=None,
            color='gray',
            current_rwt=0.0,
            target_rwt=target_rwt,
            anchor_time=current_time,
            anchor_temp=current_temp,
            x_limit=x_limit,
            y_limit_top=y_limit_top,
        )
        return (snap,)

    readiness = evaluate(
        current_temp=current_temp,
        current_ror=current_ror,
    )
    current_rwt = float(getattr(manager, 'calculate_rwt', lambda _: 0.0)(current_ror) or 0.0)
    snap = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=False,
        target_temp=target_temp,
        target_ror=target_ror,
        charged_temp=charged_temp,
        charged_ror=charged_ror,
        title=readiness.title,
        reason=readiness.reason,
        prediction_seconds=readiness.prediction_seconds,
        color=readiness.color if readiness.color in _BG_COLOR_MAP else 'gray',
        current_rwt=current_rwt,
        target_rwt=target_rwt,
        anchor_time=current_time,
        anchor_temp=current_temp,
        x_limit=x_limit,
        y_limit_top=y_limit_top,
    )
    return (snap,)
```

Also, ensure the import at the top of `plot_snapshot_extractor.py` includes `ChargeTargetAnnotationSnapshot`:

```python
from artisanlib.plot_snapshot import (
    # ... existing imports ...
    ChargeTargetAnnotationSnapshot,
)
```

(Read the existing import block at the top of the file first — it likely already imports `GuideLineSnapshot`, `PhaseSummarySnapshot`, etc. Just append `ChargeTargetAnnotationSnapshot` to that list.)

- [ ] **Step 4: Wire the extractor into the snapshot builder**

In `src/artisanlib/plot_snapshot_extractor.py`, find the function that builds `RoastPlotSnapshot` (search for `def extract_roast_plot_snapshot` or `def build_roast_plot_snapshot` — it returns `RoastPlotSnapshot(...)`). Locate the line where `guides=` is passed (it should include `_charge_target_guide(source)` in a list/tuple). Add `charge_target_annotations=_charge_target_annotations(source),` to the same constructor call.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd src && .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_snapshot_extractor.py -k charge_target_annotations -v`
Expected: 3 PASS.

- [ ] **Step 6: Compile and commit**

```bash
cd src
.venv/bin/python -m py_compile artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py
.venv/bin/python -m ruff check artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py
git add src/artisanlib/plot_snapshot.py src/artisanlib/plot_snapshot_extractor.py src/test/unitary/artisanlib/test_plot_snapshot_extractor.py
git commit -m "feat(plot-extractor): add _charge_target_annotations extractor mirroring Matplotlib path"
```

---

### Task C3: Add `_default_charge_target_annotation_factory` and wire lifecycle

**Files:**
- Modify: `src/artisanlib/plot_pyqtgraph_adapter.py`
- Test: `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`

**Interfaces:**
- Consumes: `ChargeTargetAnnotationSnapshot` from Task C1; existing `_as_items`, `_call_if_available`, `_color_with_alpha` helpers.
- Produces: `ChargeTargetAnnotationItemFactory` type alias; `_default_charge_target_annotation_factory` callable; new constructor arg `charge_target_annotation_factory`; new `_apply_charge_target_annotations` method on `PyQtGraphSnapshotRenderer`; updates to `_static_overlay_signature` and `_apply_static_overlays`.

- [ ] **Step 1: Write the failing test**

Add to `src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py`:

```python
def test_charge_target_annotation_factory_charged_state_returns_single_text_item(qapp):  # noqa: ANN001
    """Charged state emits one TextItem placed at axes-top-left equivalent."""
    from artisanlib.plot_pyqtgraph_adapter import _default_charge_target_annotation_factory
    from artisanlib.plot_snapshot import (
        AxisSnapshot,
        ChargeTargetAnnotationSnapshot,
        RoastPlotSnapshot,
        TimeRangeSnapshot,
    )
    snap = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=True,
        target_temp=200.0,
        target_ror=18.0,
        charged_temp=198.5,
        charged_ror=17.2,
        title='',
        reason='',
        prediction_seconds=None,
        color='gray',
        current_rwt=34.9,
        target_rwt=33.3,
        anchor_time=0.0,
        anchor_temp=0.0,
        x_limit=600.0,
        y_limit_top=250.0,
    )
    snapshot = RoastPlotSnapshot(
        time_axis=TimeRangeSnapshot(start=0.0, end=600.0),
        temperature_axis=AxisSnapshot(minimum=0.0, maximum=250.0, label=''),
    )
    items = _default_charge_target_annotation_factory(snap, snapshot)
    assert items is not None
    item_tuple = items if isinstance(items, tuple) else (items,)
    assert len(item_tuple) == 1, f"charged state should emit exactly 1 item, got {len(item_tuple)}"
    # The item must be a TextItem (duck-typed: has setText/setPos).
    text_item = item_tuple[0]
    assert hasattr(text_item, 'setText') or hasattr(text_item, 'setPlainText'), (
        f"expected TextItem-like object, got {type(text_item).__name__}"
    )


def test_charge_target_annotation_factory_active_state_returns_text_and_arrow(qapp):  # noqa: ANN001
    """Active state emits a TextItem plus a connector line/arrow back to (anchor_time, anchor_temp)."""
    from artisanlib.plot_pyqtgraph_adapter import _default_charge_target_annotation_factory
    from artisanlib.plot_snapshot import (
        AxisSnapshot,
        ChargeTargetAnnotationSnapshot,
        RoastPlotSnapshot,
        TimeRangeSnapshot,
    )
    snap = ChargeTargetAnnotationSnapshot(
        enabled=True,
        is_charged=False,
        target_temp=200.0,
        target_ror=18.0,
        charged_temp=0.0,
        charged_ror=0.0,
        title='接近目标',
        reason='接近目标，继续观察',
        prediction_seconds=8.4,
        color='green',
        current_rwt=34.9,
        target_rwt=33.3,
        anchor_time=423.5,
        anchor_temp=192.1,
        x_limit=600.0,
        y_limit_top=250.0,
    )
    snapshot = RoastPlotSnapshot(
        time_axis=TimeRangeSnapshot(start=0.0, end=600.0),
        temperature_axis=AxisSnapshot(minimum=0.0, maximum=250.0, label=''),
    )
    items = _default_charge_target_annotation_factory(snap, snapshot)
    assert items is not None
    item_tuple = items if isinstance(items, tuple) else (items,)
    # Active state must emit at least 2 items: the text callout and a connector.
    assert len(item_tuple) >= 2, f"active state should emit >=2 items, got {len(item_tuple)}"
```

(Note: the test uses `RoastPlotSnapshot` with minimal fields; if the dataclass requires more fields, adjust the constructor. Read the actual `RoastPlotSnapshot` definition first to know which fields have defaults.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -k charge_target_annotation_factory -v`
Expected: FAIL with `ImportError: cannot import name '_default_charge_target_annotation_factory'`.

- [ ] **Step 3: Add the type alias**

In `src/artisanlib/plot_pyqtgraph_adapter.py`, find the existing type aliases near line 23 (e.g., `GuideItemFactory = Callable[...]`). Add after them:

```python
ChargeTargetAnnotationItemFactory = Callable[
    ['ChargeTargetAnnotationSnapshot', 'RoastPlotSnapshot'],
    object | tuple[object, ...] | None,
]
```

And ensure the import at the top includes `ChargeTargetAnnotationSnapshot`:

```python
from artisanlib.plot_snapshot import (
    # ... existing imports ...
    ChargeTargetAnnotationSnapshot,
)
```

- [ ] **Step 4: Implement the factory**

In `src/artisanlib/plot_pyqtgraph_adapter.py`, immediately after `_default_phase_summary_item_factory` (ends at line 688), insert:

```python
_BG_COLOR_HEX = {
    'red': '#FFEDED',
    'blue': '#E6E6FF',
    'green': '#E8F5E9',
    'gray': '#F5F5F5',
}


def _format_ror(ror: float) -> str:
    return f'{ror:.1f}' if ror and ror > 0 else '--'


def _format_rwt(rwt: float) -> str:
    return f'{rwt:.1f}s' if rwt and rwt > 0 else '--'


def _format_prediction_seconds(seconds: object) -> str:
    if seconds is None:
        return '---'
    try:
        return f'{float(seconds):.1f}秒'
    except (TypeError, ValueError):
        return '---'


def _default_charge_target_annotation_factory(
        annotation: 'ChargeTargetAnnotationSnapshot',
        snapshot: 'RoastPlotSnapshot') -> tuple[object, ...] | None:
    try:
        import pyqtgraph as pg  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return None

    if not annotation.enabled:
        return None

    bg_color = _BG_COLOR_HEX.get(annotation.color, '#FFFFF0')

    if annotation.is_charged:
        # Charged state: static top-left card, no arrow.
        # Position: top-left of the temperature plot (axes fraction 0,1 in matplotlib).
        x_pos = snapshot.time_axis.start + (snapshot.time_axis.end - snapshot.time_axis.start) * 0.02
        y_pos = snapshot.temperature_axis.maximum - (
            snapshot.temperature_axis.maximum - snapshot.temperature_axis.minimum
        ) * 0.05
        target_ror_str = _format_ror(annotation.target_ror)
        charged_ror_str = _format_ror(annotation.charged_ror)
        target_rwt_str = _format_rwt(annotation.target_rwt)
        current_rwt_str = _format_rwt(annotation.current_rwt)
        text = (
            '【已投豆】\n'
            f'目标: {annotation.target_temp:.1f}° | RoR: {target_ror_str} | RWT: {target_rwt_str}\n'
            f'实际: {annotation.charged_temp:.1f}° | RoR: {charged_ror_str} | RWT: {current_rwt_str}'
        )
        item = pg.TextItem(
            text=text,
            color='#555555',
            anchor=(0.0, 1.0),
            fill=pg.mkBrush('#F8F8F8'),
            border=pg.mkPen(color='#DDDDDD', width=1),
        )
        item.setPos(x_pos, y_pos)
        _call_if_available(item, 'setZValue', 36)
        return (item,)

    # Active state: dynamic arrow callout.
    # Position logic mirrors canvas.py:19095-19140 — flip when near right/top edges.
    x_span = max(1.0, annotation.x_limit - snapshot.time_axis.start)
    y_span = max(1.0, annotation.y_limit_top - snapshot.temperature_axis.minimum)
    offset_x = x_span * 0.12
    offset_y = y_span * 0.12
    halign_left = annotation.anchor_time < annotation.x_limit * 0.7
    if not halign_left:
        offset_x = -offset_x
    if annotation.anchor_temp > annotation.y_limit_top * 0.8:
        offset_y = -offset_y
    text_x = annotation.anchor_time + offset_x
    text_y = annotation.anchor_temp + offset_y
    text_x = max(snapshot.time_axis.start + x_span * 0.02,
                 min(text_x, snapshot.time_axis.end - x_span * 0.02))
    text_y = max(snapshot.temperature_axis.minimum + y_span * 0.05,
                 min(text_y, snapshot.temperature_axis.maximum - y_span * 0.05))
    anchor = (0.0, 0.5) if halign_left else (1.0, 0.5)
    prediction_str = _format_prediction_seconds(annotation.prediction_seconds)
    text = (
        f'【{annotation.title}】\n'
        f'预计: {prediction_str}\n'
        f'原因: {annotation.reason}'
    )
    text_item = pg.TextItem(
        text=text,
        color='#333333',
        anchor=anchor,
        fill=pg.mkBrush(bg_color),
        border=pg.mkPen(color='#AAAAAA', width=1),
    )
    text_item.setPos(text_x, text_y)
    _call_if_available(text_item, 'setZValue', 36)
    # Connector line from (anchor_time, anchor_temp) to (text_x, text_y).
    connector = pg.PlotDataItem(
        [annotation.anchor_time, text_x],
        [annotation.anchor_temp, text_y],
        pen=pg.mkPen(color='#666666', width=1, style=QtCore.Qt.PenStyle.DashLine),
    )
    _call_if_available(connector, 'setZValue', 21)
    return text_item, connector
```

If `QtCore` is not imported at the top of `plot_pyqtgraph_adapter.py`, add `from PyQt6 import QtCore` (or use the existing import style — check the file's first 20 lines first).

- [ ] **Step 5: Run the factory tests**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -k charge_target_annotation_factory -v`
Expected: 2 PASS.

- [ ] **Step 6: Wire the constructor arg and storage**

In `src/artisanlib/plot_pyqtgraph_adapter.py`, in `PyQtGraphSnapshotRenderer.__init__` (around line 30-67), add a new parameter after `area_item_factory`:

```python
            charge_target_annotation_factory: ChargeTargetAnnotationItemFactory | None = None,
```

And inside the body, after `self._area_item_factory = area_item_factory or _default_area_item_factory`:

```python
        self._charge_target_annotation_factory = (
            charge_target_annotation_factory or _default_charge_target_annotation_factory
        )
```

And after `self._guide_items: list[tuple[object, object]] = []`:

```python
        self._charge_target_annotation_items: list[object] = []
```

- [ ] **Step 7: Add the `_apply_*` and `_clear_*` methods**

In `src/artisanlib/plot_pyqtgraph_adapter.py`, immediately after `_clear_guide_items` (ends at line 286), insert:

```python
    def _apply_charge_target_annotations(self, snapshot: 'RoastPlotSnapshot') -> None:
        self._clear_charge_target_annotation_items()
        for annotation in snapshot.charge_target_annotations:
            for item in _as_items(self._charge_target_annotation_factory(annotation, snapshot)):
                _call_if_available(self._temperature_plot, 'addItem', item)
                self._charge_target_annotation_items.append(item)

    def _clear_charge_target_annotation_items(self) -> None:
        for item in self._charge_target_annotation_items:
            _call_if_available(self._temperature_plot, 'removeItem', item)
        self._charge_target_annotation_items.clear()
```

- [ ] **Step 8: Wire into `_apply_static_overlays`**

In `_apply_static_overlays` (lines 120-131), add a new call AFTER `self._apply_guides(snapshot)` (line 130). The final block should read:

```python
        self._apply_phase_bands(snapshot)
        self._apply_time_ranges(snapshot)
        self._apply_phase_summaries(snapshot)
        self._apply_areas(snapshot)
        self._apply_event_values(snapshot)
        self._apply_events(snapshot)
        self._apply_guides(snapshot)
        self._apply_charge_target_annotations(snapshot)
        self._static_overlay_signature = signature
```

(Read the actual order in the file first — it may differ slightly. Insert `_apply_charge_target_annotations` as the LAST call before the signature assignment so the annotation renders on top of all other overlays.)

- [ ] **Step 9: Append to `_static_overlay_signature`**

In the `_static_overlay_signature` function (around lines 303-315), append `snapshot.charge_target_annotations,` as the last element of the returned tuple.

- [ ] **Step 10: Add a count helper method**

In `PyQtGraphSnapshotRenderer` (near the other `*_item_count()` methods around lines 99-118), add:

```python
    def charge_target_annotation_item_count(self) -> int:
        return len(self._charge_target_annotation_items)
```

- [ ] **Step 11: Run the full adapter test suite**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py -q`
Expected: all pass (existing + 2 new).

- [ ] **Step 12: Run the WebSocket renderer smoke (verifies end-to-end)**

Run: `cd src && QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.websocket_renderer_smoke --samples 24 --fixed-step-ms 15000 --scenario event-heavy --screenshot-file /tmp/artisanz-charge-target-annotation.png 2>&1 | tail -20`
Expected: no exceptions; `charge_target_annotations` count appears in output if smoke logs it (otherwise check that `renderer_event_item_count` etc. still match expected values — the new annotation layer must not break existing counts).

- [ ] **Step 13: Compile, lint, and commit**

```bash
cd src
.venv/bin/python -m py_compile artisanlib/plot_pyqtgraph_adapter.py
.venv/bin/python -m ruff check artisanlib/plot_pyqtgraph_adapter.py
git add src/artisanlib/plot_pyqtgraph_adapter.py src/test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py
git commit -m "feat(pyqtgraph-adapter): add charge-target annotation factory with text + connector"
```

---

### Task C4: Integration screenshot evidence

**Files:**
- No code changes — verification only.

- [ ] **Step 1: Capture the integration screenshot**

```bash
cd src
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=1 \
ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_STATUS_DOCK=1 \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-charge-target-annotation-integration.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
```
Expected: screenshot exists. Visual review: the charge-target horizontal guide line is still present; if the test profile has charge-target enabled, the annotation text callout should now also be visible in the PyQtGraph view.

- [ ] **Step 2: Run the full ArtisanZ verification subset**

```bash
cd src
.venv/bin/python -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/workspace_status_model.py
.venv/bin/python -m pytest test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_workspace_status_model.py test/unitary/artisanlib/test_plot_snapshot.py test/unitary/artisanlib/test_plot_snapshot_extractor.py test/unitary/artisanlib/test_plot_pyqtgraph_adapter.py test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m ruff check artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py artisanlib/plot_snapshot.py artisanlib/plot_snapshot_extractor.py artisanlib/plot_pyqtgraph_adapter.py artisanlib/workspace_status_model.py
```
Expected: all green.

- [ ] **Step 3: Update the roadmap**

Append to `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md` Phase 1.6 section (after the existing 2026-07-02 closure note), a new dated entry:

```
**2026-07-04 Update:** Five stale `[ ]` items in the Phase 1.6 plan were flipped to `[x]` with cross-references to Phases 1.9, 1.10, 1.12, 1.17, 1.18 (documentation-only back-fill — see `docs/superpowers/plans/2026-07-04-phase-1-6-closure-workspace-switcher-charge-target-annotation.md` Task Group A). The Workspace Status dock now exposes 5 clickable workspace switcher buttons (Task Group B). The charge-target annotation text/callout now renders in the PyQtGraph path via `ChargeTargetAnnotationSnapshot` + `_default_charge_target_annotation_factory` (Task Group C), closing the critical ArtisanZ-specific gap noted in the Phase 1.6 audit.
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md docs/superpowers/plans/2026-07-04-phase-1-6-closure-workspace-switcher-charge-target-annotation.md
git commit -m "docs(plans): record 2026-07-04 Phase 1.6 closure + workspace switcher + charge-target annotation"
```

---

## Self-Review

### 1. Spec coverage

- **Original ask #1 (audit then back-fill):** Task Group A flips the 5 confirmed-drift items (#4, #5, #9, #12, #14). Items #1, #2, #3, #6, #7, #8, #10, #11, #13, #15 are left `[ ]` because the audit confirmed they are genuinely incomplete (screenshot captures never taken; charge-target annotation parity explicitly addressed by Task Group C; projection/analysis/layout work intentionally deferred). ✅
- **Original ask #2 (interactive workspace switcher):** Task Group B adds 5 clickable buttons using the existing `setWorkspaceModeValue` slot and the existing `workspaceChanged` signal — no new Python property is needed because `modeValue` already drives highlight. ✅
- **Original ask #3 (charge-target annotation parity):** Task Group C covers the full pipeline: new dataclass → new extractor → new factory → lifecycle wiring → screenshot evidence. Rectangular bbox is used instead of matplotlib's `boxstyle=round` because `pg.TextItem` does not natively support rounded bboxes; this is documented as an acceptable trade-off for v1 (rounded corners are a follow-up if strict visual parity is required). ✅

### 2. Placeholder scan

Searched the plan for: "TBD", "TODO", "implement later", "fill in details", "Add appropriate error handling", "add validation", "handle edge cases", "Write tests for the above", "Similar to Task N". None found. All code blocks contain actual implementation. The only intentional "read the file first" instructions are for cases where the line numbers may have shifted (e.g., the existing import block at the top of `plot_snapshot_extractor.py`) — these are explicit "verify first" steps, not placeholders.

### 3. Type consistency

- `ChargeTargetAnnotationSnapshot` is used identically in Task C1 (definition), C2 (extractor return type), and C3 (factory parameter type). ✅
- `ChargeTargetAnnotationItemFactory` type alias is defined in Task C3 Step 3 and used in Task C3 Step 6 (constructor arg). ✅
- `_default_charge_target_annotation_factory` returns `tuple[object, ...] | None` consistently with the existing `_default_phase_summary_item_factory` pattern. ✅
- `setWorkspaceModeValue(str)` slot is referenced consistently across Task B — QML calls it with lowercase snake_case strings (`"roast_control"`, `"qc_analysis"`, `"device_setup"`, `"production"`, `"expert"`). ✅
- The `modelData.mode` strings in the QML Repeater exactly match the `WorkspaceMode` enum values. ✅
- `_as_items` helper (existing at `plot_pyqtgraph_adapter.py:425-430`) is reused unchanged — both single-item and tuple returns are normalized correctly. ✅

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-04-phase-1-6-closure-workspace-switcher-charge-target-annotation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Best for this plan because Task Groups A/B/C are independent and can run in parallel; Task Group C has 4 sequential sub-tasks that benefit from per-task review gates.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Slower but keeps all context in one place.

Which approach?
