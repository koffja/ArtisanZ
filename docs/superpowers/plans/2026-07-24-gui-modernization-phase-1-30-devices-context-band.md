# GUI Modernization Phase 1.30 Devices Context Band

**Status:** Closed 2026-07-24 after focused visual verification and independent review.

**Goal:** Improve the first Devices tab's hierarchy without rewriting hardware-specific controls.

## Implementation

- `src/artisanlib/devices.py`
  - Wraps the existing ET/BT device selector, curve visibility, LCD visibility, and control toggle in a non-card context band.
  - Increases first-tab grid spacing and outer padding.
  - Keeps all existing widgets, signal connections, validators, device indexes, and save flow unchanged.
- `src/artisanlib/gui_theme.py`
  - Adds a scoped `modernDeviceHeaderBand` surface using the existing Morandi tokens.
- `src/test/unitary/artisanlib/test_gui_theme.py`
  - Locks the role-scoped stylesheet selector.

## Verification

- Focused Devices/dialog/theme tests passed.
- `py_compile`, Ruff, and `git diff --check` passed.
- Visual review must confirm the active-device context reads as one restrained band, without nested-card treatment.

## Boundary

Hardware-specific tabs remain intentionally behavior-compatible and are candidates for later workflow-specific simplification when real device configurations are available.
