# GUI Modernization Phase 5 Workspace Status Dock Plan

**Goal:** Make the QML workspace-status island visible through the existing PyQt Widgets shell while keeping QML creation lazy and reversible.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a checkable View menu action for `Workspace Status`.
- [x] Add a dock placeholder with stable object name for main-window state compatibility.
- [x] Lazily create the `QQuickWidget` only when the dock is opened.
- [x] Keep the dock synchronized when the active workspace changes.
- [x] Add tests for View menu reachability, dock toggling, and workspace model synchronization.
- [x] Run focused verification, request review, fix findings, and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_workspace_status_model.py -q
.venv/bin/python -m py_compile artisanlib/main.py artisanlib/workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_workspace_status_model.py
.venv/bin/python -m ruff check artisanlib/main.py artisanlib/workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_workspace_status_model.py
git diff --check
```

## Notes

The dock is intentionally a small visible entry point rather than a full dashboard. It proves that a QML island can be opened from the real Widgets UI without moving the roast graph or settings dialogs to QML.
