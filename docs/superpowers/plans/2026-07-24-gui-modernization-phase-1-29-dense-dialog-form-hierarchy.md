# GUI Modernization Phase 1.29 Dense Dialog Form Hierarchy

**Status:** Closed 2026-07-24 after repair, visual verification, and independent review.

**Goal:** Close the remaining high-density Roast Properties visual gap without changing roast data, validation, tab behavior, or persistence.

## Scope

- Keep the free-form bean description useful while preventing it from expanding into the entire first tab.
- Group Roast Properties details, measurements, and ambient conditions into three intentional form surfaces.
- Use the existing Morandi theme tokens, flat controls, padding, and borders.
- Preserve the existing widgets, signal connections, validators, and save/cancel flow.
- Keep Devices on the already-validated dense-dialog role layer; no hardware-specific form rewrite in this slice.

## Implementation

- `src/artisanlib/roast_properties.py`
  - Bounds the bean description editor to a scrollable 88-220px working range.
  - Increases form spacing and padding.
  - Wraps the existing `textLayout`, `propGrid`, and `ambientGrid` in `modernFormSurface` frames.
- `src/artisanlib/gui_theme.py`
  - Adds Roast Properties form-surface, label, and value-control styling without changing other tabs' pane chrome.
- `src/test/unitary/artisanlib/test_gui_theme.py`
  - Locks the role-specific stylesheet contract.

## Evidence

- Saved screenshot: `/tmp/artisanz-roast-properties-after.png`.
- Visual result: three aligned Morandi surfaces, controlled description height, padded controls, and preserved Save/Cancel actions.
- Focused verification: `84 passed, 1 skipped, 2 warnings`.
- `ruff`, `py_compile`, and `git diff --check` passed.

## Review Gate

- Independent review: `PASS`, P0/P1/P2/P3 all zero after removing the overly broad tab-pane selector.
- Wide `test/unitary/artisanlib` run: `2452 passed, 30 failed, 3 skipped`; failures are pre-existing environment/tooling issues (missing async pytest plugin, network-dependent DNS assertion, and a stale QtQuick smoke size expectation). The focused GUI/dialog suite remains the authoritative gate for this slice.
