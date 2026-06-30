# GUI Modernization Phase 4 Workspace Policy Integration Plan

**Goal:** Wire the pure `WorkspacePolicy` model into `ApplicationWindow` without changing the existing Expert/Default/Production visible behavior.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add failing tests that expect `ApplicationWindow.set_ui_mode()` to synchronize both `workspace_mode` and `workspace_policy`.
- [x] Add a focused toolbar-policy test that preserves current behavior: Expert adds line configuration, Default/Production remove it.
- [x] Add `workspace_policy` to `ApplicationWindow.__slots__`, initialize it, and synchronize it in `set_ui_mode()` and settings-load direct `ui_mode` assignments.
- [x] Route `set_toolbar()` through `workspace_policy_for_mode(...).show_advanced_controls`.
- [x] Run focused verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/ui_workspaces.py artisanlib/main.py
.venv/bin/python -m ruff check artisanlib/ui_workspaces.py artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
```

Result: `16 passed, 2 warnings` for the workspace suite; compile and ruff passed.

## Notes

This slice intentionally keeps menu visibility and workspace switching UI unchanged. It only replaces another scattered mode check with policy-backed state, preparing the next Phase 4 slice to integrate menu/panel policy incrementally.
