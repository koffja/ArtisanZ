# GUI Modernization Phase 4 Shortcut Policy Plan

**Goal:** Route remaining keyboard/PID production-mode gates through `WorkspacePolicy` so task workspaces use the same information-architecture contract as menus and toolbars.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add small helpers for legacy-shortcut and compact-control decisions from current `workspace_policy`.
- [x] Replace direct `self.ui_mode is UI_MODE.PRODUCTION` shortcut/PID gates with helpers.
- [x] Preserve existing Production vs Default/Expert behavior.
- [x] Add focused unit tests for helper behavior with current and legacy states.
- [x] Update roadmap status.
- [x] Run focused verification and request review.
- [ ] Fix review findings and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py -q
.venv/bin/python -m py_compile artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

## 2026-07-01 Result

- Added `workspace_allows_legacy_shortcuts()` and `workspace_uses_compact_controls()`.
- Routed load-alarm, screenshot, PID lookahead, and PID compact-toggle gates through workspace policy while preserving non-Production shortcut behavior.
- Preserved legacy fallback for minimal window objects that only expose `ui_mode`.
- Focused verification passed: `63 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
