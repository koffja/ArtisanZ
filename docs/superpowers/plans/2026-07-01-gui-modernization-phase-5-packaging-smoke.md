# GUI Modernization Phase 5 Packaging Smoke Plan

**Goal:** Make the QtQuick/QML packaging risk check explicit and repeatable before closing Phase 5.

**Scope:**

- `src/artisanlib/qtquick_packaging_smoke.py`
- `src/test/unitary/artisanlib/test_qtquick_packaging_smoke.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a standalone smoke command for the Workspace Status QML island packaging path.
- [x] Verify PyInstaller is available in the active packaging environment.
- [x] Verify real PyQt6 QtQuick/QML modules import successfully.
- [x] Verify macOS/Linux/Windows PyInstaller specs keep the real QtQuick/QML hidden imports.
- [x] Reject phantom PyQt6 QtQml hidden imports in specs.
- [x] Run the QQuickWidget smoke in a subprocess during tests to avoid repeated QtQuickWidgets initialization crashes in the pytest process.
- [x] Update the roadmap with packaging smoke evidence.
- [x] Run focused verification, review findings, fix issues, and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.qtquick_packaging_smoke
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_qtquick_packaging_smoke.py test/unitary/artisanlib/test_workspace_status_model.py -q
.venv/bin/python -m py_compile artisanlib/qtquick_packaging_smoke.py artisanlib/workspace_status_model.py test/unitary/artisanlib/test_qtquick_packaging_smoke.py test/unitary/artisanlib/test_workspace_status_model.py
.venv/bin/python -m ruff check artisanlib/qtquick_packaging_smoke.py artisanlib/workspace_status_model.py test/unitary/artisanlib/test_qtquick_packaging_smoke.py test/unitary/artisanlib/test_workspace_status_model.py
git diff --check
```

## 2026-07-01 Result

- Smoke command output confirmed `PyInstaller 6.20.0`.
- Smoke command imported `PyQt6.QtQml`, `PyQt6.QtQuick`, and `PyQt6.QtQuickWidgets` from the active `.venv`.
- Smoke command loaded the Workspace Status QML widget successfully at `320x132`.
- Related focused tests passed: `69 passed`.
- A same-process test version exposed a local QtQuickWidgets segfault when multiple `QQuickWidget` instances were created by separate tests. The final test runs the real widget smoke in a subprocess, which is the safer pattern for future QtQuick packaging checks.
- Code review found that raw substring matching could let `PyQt6.QtQuickWidgets` satisfy the required `PyQt6.QtQuick` check, and that the subprocess test inherited a fragile caller cwd. Both were fixed with exact quoted-string matching and an explicit `cwd=src` subprocess run.
