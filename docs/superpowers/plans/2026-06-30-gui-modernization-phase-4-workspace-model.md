# GUI Modernization Phase 4 Workspace Model Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for implementation, superpowers:requesting-code-review before commit, and superpowers:verification-before-completion before claiming completion. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start Phase 4 by introducing a tested task-oriented workspace model that can guide future UI information architecture changes without immediately rewriting existing menus or dialogs.

**Architecture:** Keep the existing `UI_MODE` values for settings/backward compatibility. Add a pure `ui_workspaces.py` model with Roast Control, QC Analysis, Device Setup, Production, and Expert workspaces. Map existing `UI_MODE` values into workspaces and connect `ApplicationWindow.workspace_mode` so future UI slices can use task-oriented state instead of adding more scattered `UI_MODE` checks.

**Tech Stack:** Pure Python model, pytest, py_compile, ruff.

---

## Files

- Add: `src/artisanlib/ui_workspaces.py`
  - Define `WorkspaceMode`, `WorkspaceArea`, and `WorkspaceSpec`.
  - Define workspace specs and existing `UI_MODE` value mapping.
- Modify: `src/artisanlib/main.py`
  - Track `ApplicationWindow.workspace_mode`.
  - Use workspace mapping for toolbar expert navigation policy.
- Add: `src/test/unitary/artisanlib/test_ui_workspaces.py`
  - Cover Standard/Production/Expert mapping.
  - Cover fallback behavior for unknown legacy values.
  - Cover Production compact surface policy.
  - Cover Expert all-surface availability.
- Modify: `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`
  - Record Phase 4 start and workspace model progress.

## Task 1: Establish Workspace Model

- [x] **Step 1: Write failing tests**

Initial result: the focused workspace suite collected successfully and failed because `artisanlib.ui_workspaces` did not exist.

- [x] **Step 2: Implement pure model**

Add the workspace enum/spec model, stable labels, visible areas, compact-chrome policy, and legacy `UI_MODE` value mapping.

- [x] **Step 3: Integrate `ApplicationWindow` state**

Add `workspace_mode` to `ApplicationWindow`, initialize it from the existing `UI_MODE`, update it in `set_ui_mode()`, and use the workspace mapping for toolbar expert line-configuration policy.

## Task 2: Verify, Review, Commit

- [x] **Step 1: Run focused verification**

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/ui_workspaces.py artisanlib/main.py
.venv/bin/python -m ruff check artisanlib/ui_workspaces.py artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
```

Focused verification passed on 2026-06-30:

- `test/unitary/artisanlib/test_ui_workspaces.py`: `6 passed`
- `py_compile artisanlib/ui_workspaces.py artisanlib/main.py`: passed
- `ruff check artisanlib/ui_workspaces.py artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py`: passed

- [x] **Step 2: Run broader regression group**

Run `test/unitary/artisanlib/test_main.py::TestMakeLCDbox`, `test/unitary/artisanlib/test_gui_theme.py`, and the workspace tests.

Broader regression passed on 2026-06-30:

- `test/unitary/artisanlib/test_ui_workspaces.py`
- `test/unitary/artisanlib/test_gui_theme.py`
- `test/unitary/artisanlib/test_main.py::TestMakeLCDbox`
- `test/unitary/artisanlib/test_main.py::TestSetLabelColor::test_setLabelColor_preserves_lcd_label_padding`

Result: `14 passed, 2 warnings` (existing Yoctopuce Python 3.14 deprecation warnings).

Additional checks:

- `py_compile artisanlib/ui_workspaces.py artisanlib/main.py`: passed
- `ruff check artisanlib/ui_workspaces.py artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py`: passed
- `git diff --check`: passed

- [x] **Step 3: Request code review**

Use request-code-reviewer focused on backward compatibility, enum/value mapping, hidden import cycles, and whether the model meaningfully advances Phase 4 without changing existing behavior prematurely.

Code review result on 2026-06-30: no Critical or Important findings.

Minor follow-ups resolved:

- Added a lightweight `ApplicationWindow.set_ui_mode()` integration test with fake actions and toolbar to verify `workspace_mode` sync and Expert/Default/Production toolbar policy.
- Renamed the unknown-value fallback test to clarify that fallback applies to the pure mapper, not to invalid persisted `QSettings` values parsed through `UI_MODE(...)`.

- [x] **Step 4: Commit**

Stage only implementation, tests, and planning documents. Leave `.codebase-memory/*` unstaged.
