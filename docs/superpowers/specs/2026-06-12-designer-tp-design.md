# Designer TP (Turning Point) Design

## Summary

Add an editable Turning Point (TP / 回温点) row to the Artisan Designer config dialog, positioned between CHARGE and DRY END. The TP specifies only time and BT temperature. It participates in the spline interpolation as a regular curve node. The existing `timeindex` array (8 elements) is not modified.

## Motivation

TP is a critical roast milestone marking the lowest BT temperature after charge, when beans begin absorbing heat and temperature starts rising. Currently:

- `designerinit()` hard-codes TP at 1:30 / 110C (Celsius mode) as a hidden interpolation node
- `initfromprofile()` auto-detects TP via `findTP()` and adds it as an extra point
- Users cannot see or edit TP in the Designer config dialog

Making TP editable gives roasters control over the turning point in their designed curves, which is especially important for replicating real roast profiles.

## Approach: Independent Extra Node (Option B)

TP is stored as a separate attribute pair (`designer_tp_time`, `designer_tp_bt`) rather than a new slot in `timeindex`. This avoids touching the 20+ files that hard-code `timeindex[N]` semantics.

### Why not extend `timeindex` (Option A)?

`timeindex` uses positional semantics: `[0]=CHARGE, [1]=DRY, [2]=FCs, [3]=FCe, [4]=SCs, [5]=SCe, [6]=DROP, [7]=COOL`. Inserting TP at index 1 would shift all subsequent indices, requiring changes across `canvas.py`, `main.py`, `util.py`, `orbiter.py`, `ikawa.py`, `kaleido.py`, `rubasse.py`, `plus/schedule.py`, all profile importers, and ~30+ test files. The risk-reward ratio is unfavorable for a single feature addition.

## Data Model

New attributes on `tgraphcanvas` (canvas.py):

```python
# TP settings for Designer (independent of timeindex)
self.designer_tp_enabled: bool = True
self.designer_tp_time: float = 90.0       # seconds from roast start
self.designer_tp_bt: float = 110.0        # BT in current mode (C/F)
```

These are NOT added to `timeindex`. TP data flows into the spline as an extra node during Designer initialization and redraw.

## UI Changes

### designerconfigDlg (designer.py)

Insert a new row between CHARGE (row 1) and DRY END (row 2) in the `marksLayout` QGridLayout:

| Row | Marker | Time | BT | ET |
|-----|--------|------|----|----|
| 1 | CHARGE (fixed label) | Edit0 (disabled) | Edit0bt | Edit0et |
| **2** | **TP (checkbox)** | **EditTP** | **EditTPbt** | _(empty — TP has no ET)_ |
| 3 | DRY END (checkbox) | Edit1 | Edit1bt | Edit1et |
| 4 | FC START (checkbox) | Edit2 | Edit2bt | Edit2et |
| ... | ... | ... | ... |

New widgets:
- `self.tpCheckbox: QCheckBox` — "TP" label, toggles TP on/off in the curve
- `self.EditTP: QLineEdit` — time input (same regex validator as other time fields)
- `self.EditTPbt: QLineEdit` — BT temperature input (same regex validator as other BT fields)
- No ET field (TP only concerns BT)

All existing `EditN` indices remain unchanged (Edit1=DRY, Edit2=FCs, etc.). The TP row uses dedicated variable names to avoid index confusion.

### Behavior

- **Checkbox checked**: TP node is included in the spline. User can edit time and BT.
- **Checkbox unchecked**: TP node is removed from the spline.
- **Defaults**: On `designerinit()`, TP defaults to the current hard-coded values (1:30 / 110C in Celsius mode, 1:30 / 230F in Fahrenheit mode).
- **From profile**: On `initfromprofile()`, TP defaults to `findTP()` result if detected, otherwise checkbox is unchecked.

## Algorithm Changes

### designerinit() (canvas.py L18138)

Replace the hard-coded `timex.insert(1, ...)` with attribute-driven insertion:

```python
# Current (hard-coded):
self.timex.insert(1, 1.5*60)
self.temp1.insert(1, 230)
self.temp2.insert(1, 110)

# New (attribute-driven):
if self.designer_tp_enabled:
    self.timex.insert(1, self.designer_tp_time)
    self.temp1.insert(1, self.temp1[0])  # ET stays same as CHARGE
    self.temp2.insert(1, self.designer_tp_bt)
```

The intermediate point between DRY and FCs (currently also hard-coded at `timex.insert(3, 6*60)`) is unchanged.

### initfromprofile() (canvas.py L18199)

The existing `findTP()` logic (L18258-18298) is preserved but now populates the new attributes instead of using `addpoint()`:

```python
if lpindex != -1:
    self.designer_tp_enabled = True
    self.designer_tp_time = lptime - self.timex[self.timeindex[0]]  # relative to CHARGE
    self.designer_tp_bt = lptemp2
    # Insert TP as extra node (same as before)
    self.currentx = lptime
    self.currenty = lptemp2
    self.addpoint(manual=False)
else:
    self.designer_tp_enabled = False
```

### settimes() (designer.py)

When the user clicks Apply, read TP values and update canvas attributes:

```python
if self.tpCheckbox.isChecked():
    aw.qmc.designer_tp_enabled = True
    aw.qmc.designer_tp_time = stringtoseconds(self.EditTP.text())
    aw.qmc.designer_tp_bt = float(self.EditTPbt.text())
else:
    aw.qmc.designer_tp_enabled = False
```

### redrawdesigner() (canvas.py L18568)

No changes needed. The spline already interpolates over all points in `timex`/`temp1`/`temp2`, including any TP node that was inserted during initialization. The redraw is agnostic to where points came from.

## Persistence

TP settings are saved to `QSettings` alongside existing Designer preferences:

- `DesignerTPEnabled` (bool)
- `DesignerTPTime` (float, seconds)
- `DesignerTPBt` (float, degrees)

Loaded in the same `QSettings` restore block as other Designer config (main.py ~L19640).

## Mode Awareness

When `self.mode` switches between C and F, `designer_tp_bt` must be converted. This follows the same pattern as existing Designer temperature defaults:

- Celsius: `designer_tp_bt = 110.0`
- Fahrenheit: `designer_tp_bt = 230.0`

## Files Modified

| File | Change |
|------|--------|
| `src/__/__/__/canvas.py` | Add 3 attributes; modify `designerinit()` and `initfromprofile()` to use them |
| `src/__/__/__/designer.py` | Add TP row (checkbox + 2 LineEdits) to `designerconfigDlg`; update `settimes()`, `reset()`, `changeflags()` |
| `src/__/__/__/main.py` | Add QSettings save/load for 3 new TP keys |

## Files NOT Modified

- `timeindex` array — no changes to length or semantics
- Profile file format — TP is a Designer-only feature, not persisted in roast profiles
- Profile importers (ikawa, rubasse, aillio, etc.) — they populate `timeindex`, not Designer attributes
- `plus/schedule.py`, `orbiter.py`, or any upstream code referencing `timeindex[N]`
- Test files for existing functionality

## Risks

1. **Spline quality**: Adding a TP node very close to CHARGE (e.g., 0:10) may cause spline oscillation. Mitigation: validate that TP time > CHARGE time + minimum gap (e.g., 30 seconds) in `settimes()`.
2. **Mode conversion**: Forgetting to convert `designer_tp_bt` on C/F switch. Mitigation: follow existing `designertemp2init` conversion pattern.
3. **Profile compatibility**: Old profiles without TP data load fine — `designer_tp_enabled` defaults to `True` with reasonable defaults, matching current hard-coded behavior.

## Testing

- `test_charge_manager.py` pattern: add unit tests for TP attribute defaults and time validation
- Manual verification: open Designer, toggle TP checkbox, edit TP time/BT, confirm curve passes through TP point
- Regression: verify existing Designer workflows (add/remove landmarks, change curviness) still work
