# GUI Modernization Phase 5 Visual Validation Plan

**Goal:** Make QML island visual validation repeatable from the existing GUI performance autorun path.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add an autorun screenshot option to switch the active workspace before capture.
- [x] Add an autorun screenshot option to open the Workspace Status dock before capture.
- [x] Keep both controls disabled by default so existing performance baselines are unchanged.
- [x] Add focused tests for workspace switching and dock opening behavior.
- [x] Capture an offscreen screenshot of the QML dock in the real main window.
- [x] Update the roadmap with the new validation path and screenshot evidence.
- [x] Run focused verification, review findings, fix issues, and commit.

Verification:

```bash
cd src
.venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_workspace_status_model.py -q
.venv/bin/python -m py_compile artisanlib/main.py artisanlib/workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_workspace_status_model.py
.venv/bin/python -m ruff check artisanlib/main.py artisanlib/workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_workspace_status_model.py
git diff --check
```

Screenshot smoke:

```bash
cd src
ARTISANZ_GUI_PERF=1 \
ARTISANZ_GUI_PERF_AUTORUN=1 \
ARTISANZ_GUI_PERF_AUTORUN_ITERATIONS=1 \
ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_MODE=qc_analysis \
ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_STATUS_DOCK=1 \
ARTISANZ_GUI_PERF_FILE=/tmp/artisanz-phase5-qml-dock-perf.jsonl \
ARTISANZ_GUI_PERF_SCREENSHOT_FILE=/tmp/artisanz-phase5-qml-dock.png \
QT_QPA_PLATFORM=offscreen \
QTWEBENGINE_DISABLE_SANDBOX=1 \
QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer" \
.venv/bin/python artisan.py test/sanity/data/artisan/profile1.alog
```

## 2026-07-01 Result

- Added `ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_MODE` so autorun screenshots can switch to a target workspace before capture.
- Added `ARTISANZ_GUI_PERF_AUTORUN_WORKSPACE_STATUS_DOCK=1` so autorun screenshots can open the QML Workspace Status dock before capture.
- The first screenshot exposed a real visual defect: the dock could collapse to a narrow strip and clip the QML content.
- Fixed the defect by giving the dock and embedded `QQuickWidget` a stable 320px minimum width.
- Polished the QML island into a larger 320x132 status panel with mode color, status chips, and clearer hierarchy.
- Screenshot evidence: `/tmp/artisanz-phase5-qml-dock.png`.
- Smoke metrics from the screenshot run are useful only as a launch sanity check, not as a performance conclusion: `canvas.redraw max=94.166ms`, `canvas.updateBackground max=56.952ms`, `canvas.updategraphics max=0.006ms`.
