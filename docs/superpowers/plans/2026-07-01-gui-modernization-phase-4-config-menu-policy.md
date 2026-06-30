# GUI Modernization Phase 4 Config Menu Policy Plan

**Goal:** Route Config menu item visibility through `WorkspacePolicy` while preserving existing Expert, Default, and Production UI-mode behavior.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Preserve the current Config menu item lists for Expert, Default, and Production modes.
- [x] Use `policy.show_full_menus` for normal configuration sections.
- [x] Use `policy.show_device_setup_tools` for device, communication, calibration-delay, and curve configuration entries.
- [x] Use `policy.show_advanced_controls` for statistics and color configuration entries.
- [x] Add tests that prove Config menu visibility is policy-driven rather than hard-coded to `UI_MODE`.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

Result: `25 passed`; compile, ruff, and diff check passed. Code review found no blocking issues; the suggested independent device-policy test was added before commit.

## Notes

This continues Phase 4 by moving the densest legacy menu surface away from direct `UI_MODE` checks. It keeps Production compact today while allowing future Device Setup workspaces to expose hardware configuration without requiring Expert mode.
