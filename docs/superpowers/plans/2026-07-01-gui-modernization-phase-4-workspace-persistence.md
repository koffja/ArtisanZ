# GUI Modernization Phase 4 Workspace Persistence Plan

**Goal:** Persist task-oriented workspace selection without changing legacy `UI_mode` semantics.

**Scope:**

- `src/artisanlib/ui_workspaces.py`
- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add string serialization helpers for `WorkspaceMode`.
- [x] Keep unknown or missing workspace settings falling back to the legacy `UI_mode` mapping.
- [x] Save `workspace_mode` beside the existing `UI_mode` setting.
- [x] Load `workspace_mode` preferentially while deriving the compatible legacy `ui_mode`.
- [x] Add tests for round-trip serialization and fallback behavior.
- [x] Run focused verification and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/ui_workspaces.py artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/ui_workspaces.py artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

## Notes

This deliberately writes a new `workspace_mode` string key instead of extending the old integer `UI_mode` enum. Older builds can ignore the new key, and corrupted new values fall back to the legacy `UI_mode` derived workspace.

Result: `49 passed`; compile, ruff, and diff check passed.
