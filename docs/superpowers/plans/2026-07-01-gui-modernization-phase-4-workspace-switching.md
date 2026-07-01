# GUI Modernization Phase 4 Workspace Switching Plan

**Goal:** Make the task-oriented workspace model user-selectable while preserving legacy `UI_MODE` settings compatibility.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Keep legacy Production, Default, and Expert modes compatible with the existing `UI_mode` setting.
- [x] Add user-selectable Roast Control, QC Analysis, and Device Setup entries to the Mode menu.
- [x] Use the current `workspace_policy` as the menu and toolbar policy source when it belongs to the active `ui_mode`.
- [x] Ensure QC Analysis and Device Setup can drive different menus while retaining the legacy Default baseline.
- [x] Keep checked action state synchronized across all workspace entries.
- [x] Add tests for task workspace switching, legacy fallback, toolbar policy resolution, and QC Analysis menu visibility.
- [x] Run focused verification and code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

## Notes

This slice intentionally keeps QC Analysis and Device Setup mapped to the legacy Default `UI_MODE` value for settings compatibility. The visible behavior is driven by `workspace_mode` and `workspace_policy`; the old integer `UI_mode` remains the compatibility baseline for existing settings and non-modernized conditionals.

Result: `46 passed`; compile, ruff, and diff check passed. Self-review kept workspace persistence out of this slice to avoid changing settings semantics while the menu/toolbar policy path is still being migrated.
