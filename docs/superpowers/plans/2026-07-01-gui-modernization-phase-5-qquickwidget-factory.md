# GUI Modernization Phase 5 QQuickWidget Factory Plan

**Goal:** Make the workspace-status QML island embeddable in the existing PyQt Widgets application without adding external QML resource files.

**Scope:**

- `src/artisanlib/workspace_status_model.py`
- `src/test/unitary/artisanlib/test_workspace_status_model.py`
- `src/artisan-mac.spec`
- `src/artisan-linux.spec`
- `src/artisan-win.spec`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a data-URL helper for inline QML source.
- [x] Add a `QQuickWidget` factory that injects the Python `WorkspaceStatusModel`.
- [x] Verify the widget loads the QML panel and receives the Python model in an offscreen test.
- [x] Add real PyQt6 QtQuick/QML hidden imports to macOS, Linux, and Windows PyInstaller specs.
- [x] Add a regression test that rejects phantom PyQt6 hidden imports in the platform specs.
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

The factory uses a `data:text/plain` URL instead of a `.qml` file so this slice does not require new package data copy rules. The platform specs still receive explicit hidden imports for the real PyQt6 QtQuick/QML Python modules because this is the first Widgets-embedded Qt Quick path in ArtisanZ.

Result: `58 passed`; compile, ruff, and diff check passed. Code review found phantom QtQml hidden imports and a missing macOS hidden-import update; both were fixed, and a regression test now rejects those phantom module names in the platform specs.
