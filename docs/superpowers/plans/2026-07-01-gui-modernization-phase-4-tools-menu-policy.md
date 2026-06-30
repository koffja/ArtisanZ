# GUI Modernization Phase 4 Tools Menu Policy Plan

**Goal:** Route Tools menu item visibility through `WorkspacePolicy` while preserving existing Expert, Default, and Production UI-mode behavior.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Preserve the current Tools menu item lists for Expert, Default, and Production modes.
- [x] Use `policy.show_full_menus` for normal Tools entries.
- [x] Use `policy.show_analysis_tools` for the Analyze menu.
- [x] Use `policy.show_advanced_controls` for simulator, wheel editor, and transform entries.
- [x] Add tests proving analysis and advanced entries can be independently controlled by policy.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

Result: `28 passed`; compile, ruff, and diff check passed. Code review found no blocking issues.

## Notes

This continues Phase 4 by separating general tools, QC analysis tools, and advanced expert tools. The current legacy modes remain unchanged, while future QC Analysis and Device Setup workspaces can expose the right subset without pretending to be Expert mode.
