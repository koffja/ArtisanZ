# GUI Modernization Phase 5 Renderer Status Panel Plan

**Goal:** Surface the selected plot renderer metadata in the Qt Quick workspace-status island so the modern status panel reflects the Phase 2 renderer seam without changing live plotting behavior.

**Scope:**

- `src/artisanlib/workspace_status_model.py`
- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_workspace_status_model.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `src/test/unitary/artisanlib/test_qtquick_packaging_smoke.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Add renderer properties to `WorkspaceStatusModel`.
- [x] Show renderer label/status in the QML status panel without adding another nested card.
- [x] Sync `ApplicationWindow` status model from `qmc.plot_renderer_selection` when the dock is created or refreshed.
- [x] Keep live Matplotlib drawing unchanged.
- [x] Add focused model, QML, and main-window sync tests.
- [x] Run focused verification and request review.
- [x] Fix review findings and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_qtquick_packaging_smoke.py -q
.venv/bin/python -m py_compile artisanlib/workspace_status_model.py artisanlib/main.py artisanlib/qtquick_packaging_smoke.py test/unitary/artisanlib/test_workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_qtquick_packaging_smoke.py
.venv/bin/python -m ruff check artisanlib/workspace_status_model.py artisanlib/main.py test/unitary/artisanlib/test_workspace_status_model.py test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_qtquick_packaging_smoke.py
QT_QPA_PLATFORM=offscreen .venv/bin/python -m artisanlib.qtquick_packaging_smoke
git diff --check
```

## 2026-07-01 Result

- `WorkspaceStatusModel` now exposes renderer id, label, fallback reason, and status label.
- The QML status island shows `Renderer: Matplotlib Snapshot - Selected` in a compact text row with a small status marker.
- `ApplicationWindow` syncs the dock model from `qmc.plot_renderer_selection` without changing graph drawing.
- Renderer fallback status labels and reset-to-default behavior have focused coverage.
- Focused verification passed: `73 passed`.
- `py_compile`, `ruff check`, `git diff --check`, and `python -m artisanlib.qtquick_packaging_smoke` passed.
- Screenshot smoke passed: `/tmp/artisanz-phase5-renderer-status.png`.
