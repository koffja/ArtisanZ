# GUI Modernization Phase 0 60-Second Simulator Baseline Plan

**Goal:** Capture a longer simulator live-sampling baseline before broader threading or guarded live-renderer changes, and fix any visual defect exposed by the capture.

**Scope:**

- `src/artisanlib/main.py`
- `src/test/unitary/artisanlib/test_ui_workspaces.py`
- `docs/GUI_MODERNIZATION_BASELINE.md`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Run a 60-second offscreen simulator recording baseline.
- [x] Inspect the screenshot for visual regressions.
- [x] Fix the restored blank Workspace Status dock found in the first 60-second screenshot.
- [x] Re-run the 60-second baseline after the dock restoration fix.
- [x] Record metrics, status log, and screenshot artifacts.
- [x] Run focused verification and request review.
- [ ] Fix review findings and commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_ui_workspaces.py test/unitary/artisanlib/test_workspace_status_model.py -q
.venv/bin/python -m py_compile artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
.venv/bin/python -m ruff check artisanlib/main.py test/unitary/artisanlib/test_ui_workspaces.py
git diff --check
```

## 2026-07-01 Result

- Initial 60-second run produced `/tmp/artisanz-phase0-60s-live-sim.png` and exposed a restored-but-empty Workspace Status dock.
- `workspaceStatusDock.visibilityChanged` now ensures the QML widget is lazily created and synchronized whenever the dock becomes visible.
- Re-run screenshot passed visual inspection: `/tmp/artisanz-phase0-60s-after-dock-fix-live-sim.png`.
- Re-run metrics: `redraw max=145.282ms avg=93.455ms`; `updateBackground max=82.276ms avg=39.768ms`; `updategraphics max=37.662ms avg=2.693ms`; `sample_processing max=1.530ms avg=0.702ms`; `updateBackground.skip count=1`.
- Status log confirmed `flagon=True flagstart=True` before screenshot capture.
- Focused verification passed: `76 passed`.
- `py_compile`, `ruff check`, and `git diff --check` passed.
