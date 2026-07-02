# ArtisanZ GUI Modernization Phase 1.12: Dense Dialog Polish

**Goal:** Improve the highest-density settings dialogs, Devices and Roasting Properties, with explicit modern visual roles for their tables and tabs while preserving their dense operational layouts.

**Execution Status:** Implemented and locally verified on 2026-07-03.

## Scope

- Mark `DeviceAssignmentDlg` with `modernDialogRole="devices"`.
- Mark `editGraphDlg` / Roast Properties with `modernDialogRole="roast_properties"`.
- Add dense-dialog opt-in behavior to `apply_modern_dialog_polish()`:
  - mark dense dialogs with `modernDenseDialog`
  - mark their tables with `modernDenseTable`
  - mark horizontal and vertical headers with `modernDenseHeader`
- Add targeted stylesheet rules for dense dialog tables, headers, item padding, and selected tabs.
- Preserve existing table grid preferences, selection behavior, table cell widget layouts, validators, and settings persistence.

## Non-Goals

- Do not restructure all Devices or Roasting Properties forms.
- Do not change table data, edit triggers, selection modes, row counts, or hardware configuration behavior.
- Do not disable table grids globally.
- Do not claim this replaces future per-panel UX simplification for especially dense hardware sections.

## Validation

```bash
python3 -m py_compile \
  src/artisanlib/gui_theme.py \
  src/artisanlib/dialogs.py \
  src/artisanlib/devices.py \
  src/artisanlib/roast_properties.py

cd src
.venv/bin/python -m pytest \
  test/unitary/artisanlib/test_gui_theme.py \
  test/unitary/artisanlib/test_dialogs.py \
  -q

.venv/bin/python -m ruff check \
  artisanlib/gui_theme.py \
  artisanlib/dialogs.py \
  artisanlib/devices.py \
  artisanlib/roast_properties.py \
  test/unitary/artisanlib/test_gui_theme.py \
  test/unitary/artisanlib/test_dialogs.py

git diff --check
```

## Result

- Devices and Roasting Properties now opt into explicit modern dialog roles.
- Dense table/header roles can be styled without altering table behavior.
- Focused validation: `28 passed, 1 skipped` across GUI theme and dialog tests.
- Static validation: `py_compile`, `ruff check`, and `git diff --check` passed for touched modules.

## Remaining Gate

This closes the first dense-dialog visual role layer. Full per-panel simplification remains future work for hardware-specific Devices sections and the busiest Roasting Properties tabs.
