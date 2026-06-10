# ArtisanZ ASET Virtual Metrics and Charge Target Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the advanced ArtisanZ `.aset` preset with readable Chinese virtual metric labels, a streamlined LCD/curve layout, and enabled charge target defaults.

**Architecture:** This is a setting-file-only change. The implementation edits `/Users/chengzhe/Projects/ArtisanZ/src/includes/artisan-adv-setting-260604.aset` and verifies existing ArtisanZ charge target code still compiles and passes focused tests.

**Tech Stack:** Artisan Qt `.aset` settings, Python 3.14 project venv, pytest.

---

## File Structure

- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/includes/artisan-adv-setting-260604.aset`
  - `[General]`: add charge target defaults.
  - `[ExtraDev]`: update virtual metric labels and LCD/curve visibility flags.
- Read-only verification: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/charge_manager.py`
- Read-only verification: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/charge_dialog.py`
- Read-only verification: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/main.py`
- Read-only verification: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/canvas.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_charge_manager.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_charge_readiness_annotation_text.py`
- Test: `/Users/chengzhe/Projects/ArtisanZ/src/test/unitary/artisanlib/test_main.py`

## Scope Check

The spec covers one configuration change in one `.aset` file. It does not require code changes, generated translation updates, or simulator changes.

### Task 1: Add Charge Target Defaults

**Files:**
- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/includes/artisan-adv-setting-260604.aset`

- [ ] **Step 1: Confirm branch, remotes, and dirty worktree**

Run:

```bash
git branch --show-current
git status --short
git remote -v
```

Expected:

```text
ArtisanZ
```

Expected status may include unrelated modified/untracked files. Do not stage or edit anything except `src/includes/artisan-adv-setting-260604.aset` during implementation tasks.

- [ ] **Step 2: Run the failing static charge-target check**

Run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("src/includes/artisan-adv-setting-260604.aset")
text = path.read_text(encoding="utf-8")
expected = {
    "ChargeTargetEnabled": "true",
    "TargetChargeTemp": "160.0",
    "TargetChargeRoR": "60.0",
    "ChargeTargetTempTol": "1.0",
    "ChargeTargetRoRTol": "6.0",
}
missing = [f"{key}={value}" for key, value in expected.items() if f"{key}={value}" not in text]
assert not missing, "missing charge target defaults: " + ", ".join(missing)
PY
```

Expected before editing: `AssertionError` listing the missing charge target defaults.

- [ ] **Step 3: Insert charge target defaults in `[General]`**

Apply this patch from `/Users/chengzhe/Projects/ArtisanZ`:

```patch
*** Begin Patch
*** Update File: src/includes/artisan-adv-setting-260604.aset
@@
 ChannelTares=0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
+ChargeTargetEnabled=true
+TargetChargeTemp=160.0
+TargetChargeRoR=60.0
+ChargeTargetTempTol=1.0
+ChargeTargetRoRTol=6.0
*** End Patch
```

- [ ] **Step 4: Re-run the static charge-target check**

Run the same command from Step 2.

Expected after editing: no output and exit code `0`.

- [ ] **Step 5: Commit charge target defaults**

Run:

```bash
git add src/includes/artisan-adv-setting-260604.aset
git commit -m "config(aset): enable charge target defaults"
```

Expected: one commit containing only `src/includes/artisan-adv-setting-260604.aset`.

### Task 2: Rename Virtual Metrics and Streamline LCD/Curve Defaults

**Files:**
- Modify: `/Users/chengzhe/Projects/ArtisanZ/src/includes/artisan-adv-setting-260604.aset`

- [ ] **Step 1: Run the failing static virtual-metric check**

Run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("src/includes/artisan-adv-setting-260604.aset")
text = path.read_text(encoding="utf-8")
expected_lines = [
    "extraLCDvisibility1=true, true, false, false, true, false, false, false, false, false",
    "extraLCDvisibility2=true, true, false, false, true, false, false, false, false, false",
    "extraCurveVisibility1=false, false, true, true, false, true, true, true, true, true",
    "extraCurveVisibility2=false, false, true, false, false, true, true, true, true, true",
    "extraname1=转黄升幅, 一分钟豆温, 炉豆温差, 升温加速, 发展占比",
    "extraname2=一爆升幅, 一爆倒数, 温差趋势, 转黄倒数, 发展均升",
]
missing = [line for line in expected_lines if line not in text]
assert not missing, "missing virtual metric settings: " + " | ".join(missing)
PY
```

Expected before editing: `AssertionError` listing the lines that have not been updated yet.

- [ ] **Step 2: Replace `[ExtraDev]` labels and visibility values**

Apply this patch from `/Users/chengzhe/Projects/ArtisanZ`:

```patch
*** Begin Patch
*** Update File: src/includes/artisan-adv-setting-260604.aset
@@
-extraCurveVisibility1=true, true, true, true, false, true, true, true, true, true
-extraCurveVisibility2=true, false, true, false, false, true, true, true, true, true
+extraCurveVisibility1=false, false, true, true, false, true, true, true, true, true
+extraCurveVisibility2=false, false, true, false, false, true, true, true, true, true
@@
-extraLCDvisibility1=true, false, true, false, false, false, false, false, false, false
-extraLCDvisibility2=false, true, false, false, false, false, false, false, false, false
+extraLCDvisibility1=true, true, false, false, true, false, false, false, false, false
+extraLCDvisibility2=true, true, false, false, true, false, false, false, false, false
@@
-extraname1=BT Δ Dry, BT +60s, ET-BT Δ, RoR Accel, Post-FC %
-extraname2=BT Δ FCs, ETA FCs, ΔETBT Slope, ETA Dry, Post-FC Avg RoR
+extraname1=转黄升幅, 一分钟豆温, 炉豆温差, 升温加速, 发展占比
+extraname2=一爆升幅, 一爆倒数, 温差趋势, 转黄倒数, 发展均升
*** End Patch
```

Do not change `extramathexpression1` or `extramathexpression2`; the formulas stay as-is.

- [ ] **Step 3: Re-run the static virtual-metric check**

Run the same command from Step 1.

Expected after editing: no output and exit code `0`.

- [ ] **Step 4: Inspect the `.aset` diff**

Run:

```bash
git diff -- src/includes/artisan-adv-setting-260604.aset
```

Expected: diff shows only the five charge target lines from Task 1 if they are not already committed, plus the `[ExtraDev]` visibility and name changes from this task. There should be no changes to formula lines.

- [ ] **Step 5: Commit virtual metric labels and visibility**

Run:

```bash
git add src/includes/artisan-adv-setting-260604.aset
git commit -m "config(aset): localize virtual metric display"
```

Expected: one commit containing only `src/includes/artisan-adv-setting-260604.aset`.

### Task 3: Focused Verification

**Files:**
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/includes/artisan-adv-setting-260604.aset`
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/charge_manager.py`
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/charge_dialog.py`
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/main.py`
- Verify: `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/canvas.py`

- [ ] **Step 1: Run the combined static setting check**

Run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("src/includes/artisan-adv-setting-260604.aset")
text = path.read_text(encoding="utf-8")
expected_lines = [
    "ChargeTargetEnabled=true",
    "TargetChargeTemp=160.0",
    "TargetChargeRoR=60.0",
    "ChargeTargetTempTol=1.0",
    "ChargeTargetRoRTol=6.0",
    "extraLCDvisibility1=true, true, false, false, true, false, false, false, false, false",
    "extraLCDvisibility2=true, true, false, false, true, false, false, false, false, false",
    "extraCurveVisibility1=false, false, true, true, false, true, true, true, true, true",
    "extraCurveVisibility2=false, false, true, false, false, true, true, true, true, true",
    "extraname1=转黄升幅, 一分钟豆温, 炉豆温差, 升温加速, 发展占比",
    "extraname2=一爆升幅, 一爆倒数, 温差趋势, 转黄倒数, 发展均升",
]
missing = [line for line in expected_lines if line not in text]
assert not missing, "missing expected settings: " + " | ".join(missing)

for key in (
    "extraLCDvisibility1",
    "extraLCDvisibility2",
    "extraCurveVisibility1",
    "extraCurveVisibility2",
):
    line = next(line for line in text.splitlines() if line.startswith(f"{key}="))
    values = [value.strip() for value in line.split("=", 1)[1].split(",")]
    assert len(values) == 10, f"{key} must keep 10 boolean entries"
    assert all(value in {"true", "false"} for value in values), f"{key} contains non-boolean values"
PY
```

Expected: no output and exit code `0`.

- [ ] **Step 2: Compile charge-target-related modules**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
/Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py
```

Expected: no output and exit code `0`.

- [ ] **Step 3: Run focused charge target tests**

Run from `/Users/chengzhe/Projects/ArtisanZ/src`:

```bash
/Users/chengzhe/Projects/ArtisanZ/src/.venv/bin/python -m pytest test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_charge_readiness_annotation_text.py test/unitary/artisanlib/test_main.py::TestLoadFile::test_show_charge_target_dialog_redraws_canvas_after_save -q
```

Expected: all collected tests pass. A passing run before planning collected 17 items and passed them with two Yoctopuce deprecation warnings.

- [ ] **Step 4: Confirm git scope**

Run from `/Users/chengzhe/Projects/ArtisanZ`:

```bash
git status --short
git log --oneline -n 5
```

Expected: the new implementation commits are on `ArtisanZ`. Existing unrelated modified/untracked files may remain, but no staged changes should remain from this implementation.
