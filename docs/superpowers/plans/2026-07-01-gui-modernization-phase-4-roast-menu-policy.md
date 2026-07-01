# GUI Modernization Phase 4 Roast Menu Policy Plan

**Goal:** Route Roast menu profile-switch entries through `WorkspacePolicy` while preserving existing Expert, Default, and Production UI-mode behavior.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Preserve the current Roast menu item lists for Expert, Default, and Production modes.
- [x] Keep core roast/profile actions and the charge-target entry always visible.
- [x] Use `policy.show_full_menus` for profile switching.
- [x] Use `policy.show_advanced_controls` for ET/BT switching.
- [x] Add tests proving full-menu and advanced-control entries can be independently controlled by policy.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

Result: `32 passed`; compile, ruff, and diff check passed. Code review found no blocking issues; minor test typing and charge-target signal assertions were addressed before commit.

## Notes

This keeps roast-control essentials available in every mode while moving profile-switch affordances into the same policy model used by File, Config, Tools, and Help menus.
