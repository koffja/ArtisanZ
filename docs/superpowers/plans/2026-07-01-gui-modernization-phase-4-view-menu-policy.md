# GUI Modernization Phase 4 View Menu Policy Plan

**Goal:** Route View menu full-menu visibility through `WorkspacePolicy` while preserving Production-mode runtime fallbacks for controls that are already active.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Preserve the current View menu item lists for Expert, Default, and Production modes.
- [x] Use `policy.show_full_menus` instead of direct non-Production checks.
- [x] Preserve Production-mode runtime fallbacks for buttons, sliders, PID LCDs, extra-device LCDs, and scale LCDs.
- [x] Keep scheduler disabling for ArtisanViewer mode unchanged.
- [x] Add tests for legacy behavior, Production runtime fallbacks, and policy-driven full View controls.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

Result: `42 passed`; compile, ruff, and diff check passed. Code review requested fallback-combination, scheduler, fullscreen, and policy-list test strengthening; those fixes were applied before commit.

## Notes

This is the highest-risk menu policy slice because View visibility combines workspace chrome with live runtime state. The implementation keeps every existing runtime fallback while moving the static full-menu decision into the workspace policy model.
