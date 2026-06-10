# ArtisanZ ASET Virtual Metrics and Charge Target Design

Date: 2026-06-10

## Goal

Update `/Users/chengzhe/Projects/ArtisanZ/src/includes/artisan-adv-setting-260604.aset` so it is easier to use during roasting:

- Rename the Virtual Machine / Extra Device metrics from terse English labels to readable Chinese titles.
- Use a "精简战情盘" layout: only decision-ready values stay on LCD, while trend-oriented values stay on curves.
- Save the charge target feature defaults in the same setting file so loading this profile enables the on-curve charge prompt by default.

## Scope

Only the `.aset` setting file is in implementation scope. Application code, charge readiness logic, virtual formulas, translations, and simulator code are out of scope unless verification reveals that the setting file cannot support the intended behavior.

The browser companion files under `.superpowers/brainstorm/` are temporary brainstorming artifacts and should not be committed.

## Charge Target Defaults

Add these keys to the `[General]` section:

```ini
ChargeTargetEnabled=true
TargetChargeTemp=160.0
TargetChargeRoR=60.0
ChargeTargetTempTol=1.0
ChargeTargetRoRTol=6.0
```

Expected display behavior remains the current ArtisanZ behavior:

- Before CHARGE: a Matplotlib annotation appears on the roast curve with `【接近目标】`, `【可以投豆】`, or another readiness status. This is not an LCD.
- After CHARGE: the annotation changes to a fixed top-left `【已投豆】` summary showing target and actual charge temp / RoR / RWT.

## Virtual Metrics

Keep the existing formulas unchanged. Rename only the labels and adjust default LCD/curve visibility.

| Formula slot | Old title | New title | Default display | Reason |
|---|---|---|---|---|
| `extraname1[0]` | `BT Δ Dry` | `转黄升幅` | LCD | A direct operational number: expected BT rise before DRY. |
| `extraname2[0]` | `BT Δ FCs` | `一爆升幅` | LCD | A direct operational number: expected BT rise before FCs. |
| `extraname1[1]` | `BT +60s` | `一分钟豆温` | LCD | Easy to understand at a glance during live control. |
| `extraname2[1]` | `ETA FCs` | `一爆倒数` | LCD | Countdown values are more useful as numbers than curves. |
| `extraname1[2]` | `ET-BT Δ` | `炉豆温差` | Curve | The trend matters more than the instantaneous number. |
| `extraname2[2]` | `ΔETBT Slope` | `温差趋势` | Curve | Slope readings are noisy; curve direction is clearer. |
| `extraname1[3]` | `RoR Accel` | `升温加速` | Curve | Useful for trend and oscillation, not as a jumping LCD value. |
| `extraname2[3]` | `ETA Dry` | `转黄倒数` | Hidden by default | Useful only early, so keep configured but do not occupy screen space. |
| `extraname1[4]` | `Post-FC %` | `发展占比` | LCD | Development percentage is naturally a summary number. |
| `extraname2[4]` | `Post-FC Avg RoR` | `发展均升` | LCD | A compact development-stage control summary. |

## ASET Visibility Values

Use these exact values:

```ini
extraLCDvisibility1=true, true, false, false, true, false, false, false, false, false
extraLCDvisibility2=true, true, false, false, true, false, false, false, false, false
extraCurveVisibility1=false, false, true, true, false, true, true, true, true, true
extraCurveVisibility2=false, false, true, false, false, true, true, true, true, true
extraname1=转黄升幅, 一分钟豆温, 炉豆温差, 升温加速, 发展占比
extraname2=一爆升幅, 一爆倒数, 温差趋势, 转黄倒数, 发展均升
```

The lists keep ten booleans because Artisan expects up to `nLCDS` visibility entries. Only the first five entries correspond to the current five virtual devices.

## Verification Plan

1. Static inspect the `.aset` file and confirm the five charge target keys are present in `[General]`.
2. Static inspect `[ExtraDev]` and confirm label lists and visibility lists match this spec.
3. Run focused code checks from `/Users/chengzhe/Projects/ArtisanZ/src` using the project venv:

```bash
/Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py
/Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m pytest test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_charge_readiness_annotation_text.py test/unitary/artisanlib/test_main.py::TestLoadFile::test_show_charge_target_dialog_redraws_canvas_after_save -q
```

## Open Risks

- The `.aset` file uses Qt setting serialization. Plain UTF-8 Chinese labels are already present elsewhere in this file, so Chinese titles are acceptable.
- Extra LCD and curve visibility are independent in ArtisanZ; a metric can stay on LCD while its curve is hidden. The label may still show with a hidden-curve color state, which is acceptable for the streamlined layout.
- The charge target prompt will still not show if the loaded profile already contains a CHARGE event; in that case the expected display is the `【已投豆】` summary.
