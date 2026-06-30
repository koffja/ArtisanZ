# GUI Modernization Phase 4 Menu Policy Plan

**Goal:** Move the first menu visibility decision from hard-coded `UI_MODE` checks to the workspace policy layer without changing the current visible menu behavior.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a focused `set_menu()` fake-menu test proving Expert and Standard still show Tools, while Production hides it.
- [x] Add a policy monkeypatch test proving `set_menu()` reads `workspace_policy_for_mode(...).show_full_menus` rather than hard-coding the legacy `UI_MODE` set.
- [x] Route Tools-menu visibility through `WorkspacePolicy.show_full_menus`.
- [x] Run focused verification:

```bash
QT_QPA_PLATFORM=offscreen src/.venv/bin/python -m pytest src/test/unitary/artisanlib/test_ui_workspaces.py src/test/unitary/artisanlib/test_gui_theme.py src/test/unitary/artisanlib/test_main.py::TestMakeLCDbox src/test/unitary/artisanlib/test_main.py::TestSetLabelColor::test_setLabelColor_preserves_lcd_label_padding -q
```

Result: `26 passed, 2 warnings`.

## Notes

This slice intentionally affects only the Tools menu gate. Other menu internals still use legacy `UI_MODE` checks until each decision has a policy name and a behavior-preserving test.
