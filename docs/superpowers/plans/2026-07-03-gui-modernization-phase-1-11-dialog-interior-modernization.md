# ArtisanZ GUI Modernization Phase 1.11: Dialog Interior Modernization

**Goal:** Make common Artisan settings dialogs feel less like legacy gray Qt forms by applying consistent light Morandi surfaces, spacing, viewport backgrounds, table styling, tab behavior, and primary/secondary button roles inside `ArtisanDialog` windows.

**Execution Status:** Implemented and locally verified on 2026-07-03.

## Scope

- Add a reusable runtime polish helper for `ArtisanDialog` content.
- Apply the helper once when an Artisan dialog is shown.
- Preserve existing dialog construction, validation, translations, shortcuts, and persistence.
- Improve common internals shared by Axes, Curves, Events, Alarms, Devices, Roasting Properties, and other `ArtisanDialog` subclasses:
  - root/nested layout margins and spacing
  - group-box panel roles
  - tab widget document mode and non-expanding tabs
  - scroll/table viewport background roles
  - alternating table rows and flatter table presentation
  - existing table grid preferences remain intact
  - primary/secondary button roles for standard dialog buttons
- Extend the modern stylesheet with targeted selectors for the new runtime roles.

## Non-Goals

- Do not rewrite individual settings dialog forms in this slice.
- Do not alter settings persistence, validators, shortcuts, or accept/reject behavior.
- Do not touch native file dialogs or message box workflows beyond existing global styling.
- Do not claim full visual redesign for every device-specific nested panel.

## Validation

```bash
python3 -m py_compile src/artisanlib/gui_theme.py src/artisanlib/dialogs.py

cd src
.venv/bin/python -m pytest \
  test/unitary/artisanlib/test_gui_theme.py \
  test/unitary/artisanlib/test_dialogs.py \
  -q

.venv/bin/python -m ruff check \
  artisanlib/gui_theme.py \
  artisanlib/dialogs.py \
  test/unitary/artisanlib/test_gui_theme.py \
  test/unitary/artisanlib/test_dialogs.py

git diff --check
```

## Result

- Added `apply_modern_dialog_polish()` to `artisanlib.gui_theme`.
- `ArtisanDialog.showEvent()` now applies the polish once per dialog instance.
- Added stylesheet selectors for dialog viewports, scroll areas, checkboxes, standard-button primary/secondary roles, and transparent button boxes.
- Added tests proving runtime polish applies margins, tab behavior, table viewport roles, alternating rows while preserving existing table grids, table cell layout preservation, legacy fallback no-op behavior, inherited `ArtisanDialog.showEvent()` behavior, and OK/Cancel button visual roles.
- Focused validation: `27 passed, 1 skipped` across GUI theme and dialog tests.
- Static validation: `py_compile`, `ruff check`, and `git diff --check` passed for touched modules.

## Remaining Gate

This closes the shared interior polish layer. Later visual slices should still inspect and reshape especially dense dialog-specific layouts, starting with Devices and Roasting Properties, where tables and hardware-specific panels remain information-dense by design.
