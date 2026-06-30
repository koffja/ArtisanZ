# GUI Modernization Phase 3 Sample Thread Queued Boundary Plan

**Goal:** Make the existing sampling-thread to GUI-thread boundary explicit before any future worker/threading refactor.

**Scope:**

- `src/artisanlib/canvas.py`
- `docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md`

## Tasks

- [x] Confirm `sample_processing()` is documented as GUI-thread work.
- [x] Route `SampleThread.sample_processingSignal` to `tgraphcanvas.sample_processing()` with an explicit `Qt.ConnectionType.QueuedConnection`.
- [x] Clarify the inline comment so future maintainers do not treat `sample_processing()` as sample-thread work.
- [x] Run focused verification and request code review before commit.

Verification:

```bash
cd src
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest test/unitary/artisanlib/test_canvas.py::TestXAxisToSM test/unitary/artisanlib/test_sample_processing.py -q
.venv/bin/python -m py_compile artisanlib/canvas.py
.venv/bin/python -m ruff check artisanlib/canvas.py
git diff --check
```

Result: `136 passed`; compile, ruff, and diff check passed. Code review found no blocking issues.

## Notes

This is a defensive Phase 3 cleanup, not a threading migration. The current runtime behavior already relies on Qt queueing work from `SampleThread` to the GUI-owned canvas object; the change makes that contract explicit so future refactors cannot silently turn the slot into direct sample-thread execution.
