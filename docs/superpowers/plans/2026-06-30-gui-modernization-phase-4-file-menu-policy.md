# GUI Modernization Phase 4 File Menu Policy Plan

**Goal:** Move File menu full-menu and expert-only gates from legacy `UI_MODE` checks to `WorkspacePolicy` while preserving the current Expert, Standard, and Production item layout.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add a fake File menu test that pins the existing Expert, Standard, and Production item sequences.
- [x] Add a policy monkeypatch test proving Production can show full/expert File menu sections when policy says so.
- [x] Route import/export/save-graph/report sections through `WorkspacePolicy.show_full_menus`.
- [x] Route save-copy-as/statistics sections through `WorkspacePolicy.show_advanced_controls`.
- [x] Run focused verification:

```bash
QT_QPA_PLATFORM=offscreen src/.venv/bin/python -m pytest src/test/unitary/artisanlib/test_ui_workspaces.py src/test/unitary/artisanlib/test_gui_theme.py src/test/unitary/artisanlib/test_main.py::TestMakeLCDbox src/test/unitary/artisanlib/test_main.py::TestSetLabelColor::test_setLabelColor_preserves_lcd_label_padding -q
```

Result: `30 passed, 2 warnings`.

## Notes

The existing Production File menu leaves several separator entries where hidden sections would normally appear. This slice intentionally preserves that behavior and only changes the source of the visibility decisions.
