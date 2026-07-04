# PyQtGraph Visual Fixes + Curves Dialog Phase Tab Design

**Date:** 2026-07-04
**Status:** Draft — awaiting user review
**Author:** Sisyphus (based on user feedback + code diagnosis)

**Selected approach:** B (Medium fix) — fix all reported visual bugs + add CurvesDlg "Phase & Style" tab for user-adjustable controls. Workspace Status enhancement deferred to a separate spec pending clearer requirements.

---

## Problem Statement

User loaded a real roast profile (`26YUN-COE165_26-06-24_1400W487.alog`) and reported 5 issues in the default PyQtGraph renderer:

1. **Phase band colors look saturated yellow/red** — the drying/maillard/development background regions are visually unpleasant. User wants: drying = semi-transparent light white, maillard = light ivory, development = unchanged.
2. **Curve colors abnormally dark** — the BT curve's CET-L17 temperature gradient pen makes high-temperature segments appear deep red.
3. **Background curves and main curves have no visible depth differentiation** — both look the same weight/color depth despite background alpha being 0.45 vs main 1.0.
4. **Phase summary progress bars lack phase name labels** — only show duration/percent/delta, not "Drying"/"Maillard"/"Development".
5. **Curves dialog (Lines button) lacks Phase 1.6 feature controls** — no UI to adjust phase colors, opacity, BT gradient, background curve style.

---

## Root Causes (from code diagnosis)

| Issue | Root cause | File:line evidence |
|---|---|---|
| 1. Phase band colors | User's saved `palette['rect1/2/3']` overrides defaults; opacity capped at 0.38 (too high for light colors on light background); 3 inconsistent color sources | `plot_snapshot_extractor.py:1039-1044`, `plot_pyqtgraph_adapter.py:837-838`, `canvas.py:183-185` |
| 2. BT curve too dark | CET-L17 gradient pen (`orientation='vertical'`, `span=(150,250)`) makes high-temp BT segments red; always-on, no toggle | `plot_pyqtgraph_adapter.py:366-388` |
| 3. Background vs main no depth diff | Both use solid line style (`'-'`); background alpha 0.45 not visually distinct enough for saturated colors | `plot_snapshot_extractor.py:165-237` |
| 4. Progress bar no phase name | `summary.label` is computed but never rendered in factory | `plot_pyqtgraph_adapter.py:703-709` vs `plot_snapshot_extractor.py:611-615` |
| 5. No CurvesDlg controls | CurvesDlg has 6 tabs (RoR/Filters/Plotter/Math/Analyze/UI), none for phase styling; `rect1Button`/`rect2Button`/`rect3Button` live in a separate UI file | `curves.py:1408-1450`, `canvas.py:13438-13440` |

---

## Design Decisions

### D1: Phase band default colors (assumes approach A — change code defaults)

**New defaults** (user-specified):

| Phase | Current fallback | New default | Rationale |
|---|---|---|---|
| Drying (rect1) | `#DDE8E0` (gray-green) / `#F7F6F0` (canvas) | `#F5F5F0` (semi-transparent light white) | User request: "半透明淡白色" |
| Maillard (rect2) | `#E7DEC9` (cream) / `#EEF2F0` (canvas) | `#F5F0E1` (light ivory) | User request: "淡象牙白" |
| Development (rect3) | `#D9E4EA` (blue-gray) / `#F4F2EC` (canvas) | unchanged (keep `#F4F2EC`) | User request: "发展期可以不用变" |

**Files to change:**
- `plot_snapshot_extractor.py:1044` — gray-fallback tuple
- `canvas.py:183-185` — canvas palette defaults
- `plot_snapshot_extractor.py:612-614` — phase summary defaults (make consistent with band colors)

**Opacity cap reduction:**
- `_visible_phase_band_opacity` in `plot_pyqtgraph_adapter.py:837-838`: change from `min(0.38, max(0.24, opacity * 1.5))` to `min(0.22, max(0.10, opacity * 1.2))`
- This makes bands more subtle on light background

**Important note:** If user has a saved `palette['rect1/2/3']` that is NOT in the gray-default set (`#e5e5e5`/`#b2b2b2`/`#d3d3d3`), the saved value still overrides. The CurvesDlg tab (D5) provides UI to change this per-profile.

### D2: BT gradient pen — default off + toggle

**Current:** BT curve always gets CET-L17 gradient pen (`plot_pyqtgraph_adapter.py:378-388`).

**New:** Add a setting `bt_gradient_enabled` (default `False`). The pen factory checks this setting before applying gradient:

```python
if curve.name == 'BT' and curve.y_axis == 'temperature' and bt_gradient_enabled:
    # gradient pen
else:
    # solid pen
```

**Files to change:**
- `plot_pyqtgraph_adapter.py:366-388` — add condition
- `plot_renderer_settings.py` or `gui_theme.py` — add `bt_gradient_enabled` setting
- The setting is persisted via QSettings and exposed in CurvesDlg (D5)

### D3: Background curve visual differentiation

**Current:** Background curves use `opacity=0.45`, `line_style='-'` (solid).

**New defaults:**
- Opacity: 0.35 (down from 0.45)
- Line style: `'--'` (dashed) for all 4 background curves
- This creates clear visual hierarchy: main = solid+opaque, background = dashed+translucent

**Files to change:**
- `plot_snapshot_extractor.py:165-237` — change `_background_curve` line_style default and opacity
- Add `background_line_style` setting for CurvesDlg override (D5)

### D4: Phase summary progress bar labels

**Current:** `text=f'{summary.duration_text}  {summary.percent_text}'` — no phase name.

**New:** Include phase name as first line:
```python
text=f'{summary.label}\n{summary.duration_text}  {summary.percent_text}'
```

Renders as:
```
Drying
4:48  50.3%
```

**Bump y position** slightly to accommodate the extra line: adjust `y_text` offset in `_default_phase_summary_item_factory`.

**Add toggle setting** `phase_summary_labels` (default `True`) for users who want to hide it.

**Files to change:**
- `plot_pyqtgraph_adapter.py:703-709` — add `summary.label` to text + adjust y position
- Add setting + CurvesDlg checkbox (D5)

### D5: CurvesDlg "Phase & Style" tab (tab index 6)

**New tab** in `CurvesDlg` (`curves.py`), placed after "UI" tab (index 5).

**UI layout** (QFormLayout or QGridLayout):

```
┌─ Phase & Style ────────────────────────────────┐
│                                                │
│  Phase Band Colors                             │
│  ┌──────────────┬──────────────────────────┐  │
│  │ Drying:      │ [ColorButton] rect1      │  │
│  │ Maillard:    │ [ColorButton] rect2      │  │
│  │ Development: │ [ColorButton] rect3      │  │
│  │ Opacity:     │ [====slider====] 0.10-0.50│  │
│  └──────────────┴──────────────────────────┘  │
│                                                │
│  Curve Styling                                 │
│  ┌──────────────┬──────────────────────────┐  │
│  │ BT gradient: │ [☑] Enabled             │  │
│  │ BG alpha:    │ [====slider====] 0.20-0.80│  │
│  │ BG style:    │ [Dashed ▼]              │  │
│  │ Phase labels:│ [☑] Show on progress bar │  │
│  └──────────────┴──────────────────────────┘  │
│                                                │
│  [Restore Defaults]                            │
│                                                │
└────────────────────────────────────────────────┘
```

**Bindings:**

| UI Widget | Setting key | Type | Default | Persistence |
|---|---|---|---|---|
| Drying color button | `palette['rect1']` | str (hex) | `#F5F5F0` | QSettings `rect1` |
| Maillard color button | `palette['rect2']` | str (hex) | `#F5F0E1` | QSettings `rect2` |
| Development color button | `palette['rect3']` | str (hex) | `#F4F2EC` | QSettings `rect3` |
| Opacity slider | `phase_band_opacity` | float | `0.18` | QSettings `phase_band_opacity` |
| BT gradient checkbox | `bt_gradient_enabled` | bool | `False` | QSettings `bt_gradient_enabled` |
| BG alpha slider | `backgroundalpha` | float | `0.35` | existing setting |
| BG style combo | `background_line_style` | str | `'--'` | QSettings `background_line_style` |
| Phase labels checkbox | `phase_summary_labels` | bool | `True` | QSettings `phase_summary_labels` |
| Restore Defaults button | — | — | — | resets all above to defaults |

**Files to change/create:**
- `curves.py` — add tab 6 UI + bindings + persistence
- `plot_snapshot_extractor.py` — read new settings (`background_line_style`, `phase_summary_labels`)
- `plot_pyqtgraph_adapter.py` — read `bt_gradient_enabled`, `phase_summary_labels`, `phase_band_opacity`
- `gui_theme.py` — add modern styling for the new tab (consistent with Phase 1.11 dialog polish)

### D6: Workspace Status (deferred)

**Not included in this spec.** User feedback "还是没有什么其他重要的信息" is too vague to design against. Deferred to a separate brainstorming session where the user specifies what information they want (recording state, charge target, device status, live temperatures, alarms, etc.).

---

## Architecture

```
User opens CurvesDlg → Phase & Style tab
    ↓ adjusts settings
QSettings persistence (rect1/2/3, phase_band_opacity, bt_gradient_enabled, etc.)
    ↓ on dialog OK
main.py updates palette + settings on qmc (canvas)
    ↓ next redraw
plot_snapshot_extractor reads settings → builds PhaseBandSnapshot / CurveSnapshot
    ↓
plot_pyqtgraph_adapter reads settings → factory functions apply colors/styles
    ↓
PyQtGraph renders with new visual config
```

**No new files** — all changes in existing modules. No new dependencies.

---

## Scope Boundaries

### In scope
- 5 visual fixes (D1-D4)
- 1 new CurvesDlg tab (D5)
- QSettings persistence for all new settings
- "Restore Defaults" button on new tab

### Out of scope (explicitly deferred)
- Workspace Status information enhancement (D6) — needs separate requirements gathering
- Time-axis (X-axis) curve color gradient — currently only Y-axis (temperature) gradient exists; X-axis gradient is a larger refactor requiring per-segment pen construction
- Background curve time-based gradient — same as above
- Matplotlib adapter parity for these settings — Matplotlib path already has its own phase band controls via `rect1Button`/`rect2Button`/`rect3Button`

---

## Testing Strategy

1. **Unit tests** for new settings reading in extractor/adapter:
   - `test_phase_band_color_uses_new_defaults`
   - `test_background_curve_uses_dashed_style_by_default`
   - `test_phase_summary_includes_label_when_enabled`
   - `test_bt_gradient_disabled_by_default`

2. **Integration test** for CurvesDlg tab:
   - Tab exists, all widgets present
   - Changing color button updates `palette['rect1']`
   - Restore Defaults resets all settings

3. **Visual smoke** (offscreen screenshot):
   - Load `profile1.alog` → screenshot → verify phase bands are light/subtle
   - Toggle BT gradient on → screenshot → verify gradient visible
   - Set background style to dashed → screenshot → verify differentiation

---

## Open Questions for User Review

1. **Phase band opacity default** — I chose 0.18 (subtle). If you want them more visible, increase to 0.22-0.28. The slider in CurvesDlg lets you adjust at runtime.

2. **BT gradient** — I'm defaulting it OFF. If you want it ON by default (like current behavior), change the default to `True`. The checkbox lets you toggle at runtime.

3. **Background curve style** — I chose dashed (`'--'`). If you prefer dotted (`':'`) or a different visual, adjust the default. The combo box lets you choose at runtime.

4. **Development phase color** — You said "发展期可以不用变". The current canvas default is `#F4F2EC` (very light cream). I'm keeping this. If you want a specific different color, specify it.

5. **Phase summary label position** — I'm adding the phase name as a first line above the duration/percent text. This slightly raises the text block. If you prefer the name beside the bar (horizontal layout) instead of above, note it.

6. **CurvesDlg tab name** — I called it "Phase & Style". Alternatives: "Visual", "Phase Bands", "Appearance". Preference?

---

## Implementation Order (for writing-plans skill)

1. **Task 1:** Change phase band default colors + opacity cap (D1) — `plot_snapshot_extractor.py`, `plot_pyqtgraph_adapter.py`, `canvas.py`
2. **Task 2:** BT gradient default off + setting (D2) — `plot_pyqtgraph_adapter.py`, settings
3. **Task 3:** Background curve dashed + lower alpha (D3) — `plot_snapshot_extractor.py`
4. **Task 4:** Phase summary labels (D4) — `plot_pyqtgraph_adapter.py`
5. **Task 5:** CurvesDlg Phase & Style tab (D5) — `curves.py`, wiring to settings
6. **Task 6:** Visual smoke screenshots + verify
