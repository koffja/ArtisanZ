# GUI Modernization Phase 4 Help Menu Policy Plan

**Goal:** Move the Help menu's full-menu and expert-diagnostic gates from hard-coded `UI_MODE` checks to `WorkspacePolicy` while preserving current Expert, Standard, and Production behavior.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a fake `QMenu` test that records the current Help menu contents for Expert, Standard, and Production modes.
- [x] Add a policy monkeypatch test proving Production can receive full Help menu sections when policy says so.
- [x] Route Help menu update/settings sections through `WorkspacePolicy.show_full_menus`.
- [x] Route Help menu diagnostic sections through `WorkspacePolicy.show_advanced_controls`.
- [x] Run focused verification:

```bash
QT_QPA_PLATFORM=offscreen src/.venv/bin/python -m pytest src/test/unitary/artisanlib/test_ui_workspaces.py src/test/unitary/artisanlib/test_gui_theme.py src/test/unitary/artisanlib/test_main.py::TestMakeLCDbox src/test/unitary/artisanlib/test_main.py::TestSetLabelColor::test_setLabelColor_preserves_lcd_label_padding -q
```

Result: `28 passed, 2 warnings`.

## Notes

This keeps existing user-visible menu behavior intact while making Help menu sections obey workspace policy. The remaining menu creators can now be migrated one section at a time with the same fake-menu pattern.
