# GUI Modernization Phase 5 Workspace Status QML Island Plan

**Goal:** Prove a small Qt Quick island can consume Python workspace state without touching the roast graph or packaging data files.

**Scope:**

- `src/artisanlib/workspace_status_model.py`
- `src/test/unitary/artisanlib/test_workspace_status_model.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a `QObject` workspace status model backed by `WorkspaceMode`, `WorkspaceSpec`, and `WorkspacePolicy`.
- [x] Expose QML-friendly properties for label, primary area, compact chrome, analysis tools, device setup tools, and advanced controls.
- [x] Add a slot for QML/string-driven workspace updates.
- [x] Keep the first QML panel as an in-Python string to avoid new package data paths.
- [x] Compile the QML panel with `QQmlComponent` in an offscreen unit test.
- [x] Instantiate the QML panel and attach the Python model in an offscreen unit test.
- [x] Run focused verification and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/workspace_status_model.py test/unitary/artisanlib/test_workspace_status_model.py
.venv/bin/python -m ruff check artisanlib/workspace_status_model.py test/unitary/artisanlib/test_workspace_status_model.py
git diff --check
```

## Notes

This is intentionally not wired into `ApplicationWindow` yet. The purpose of the first Phase 5 slice is to validate the Python-to-QML state seam and QML runtime availability with minimal risk.

Result: `55 passed`; compile, ruff, and diff check passed.
