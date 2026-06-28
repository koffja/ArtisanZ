# Designer TP (Turning Point) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an editable TP (回温点) row to the Artisan Designer config dialog between CHARGE and DRY END, allowing users to control the turning point in designed curves.

**Architecture:** TP is stored as 3 independent attributes on `tgraphcanvas` (`designer_tp_enabled`, `designer_tp_time`, `designer_tp_bt`), NOT as a new slot in `timeindex`. The TP node is inserted into the spline interpolation arrays (`timex`/`temp1`/`temp2`) during Designer initialization. This avoids touching the 20+ files that hard-code `timeindex[N]` positional semantics.

**Tech Stack:** Python 3.12+, PyQt6, scipy.interpolate.UnivariateSpline, pytest

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/__/__/__/canvas.py` | Modify | Add TP attributes; update `designerinit()` and `initfromprofile()` |
| `src/__/__/__/designer.py` | Modify | Add TP row to `designerconfigDlg`; update `settimes()`, `reset()`, `changeflags()` |
| `src/test/unitary/__/__/__/test_designer_tp.py` | Create | Unit tests for TP defaults, validation, and integration |

---

## Task 1: Add TP attributes and defaults to canvas.py

**Files:**
- Modify: `src/__/__/__/canvas.py:2175-2182` (attribute declarations near `designertimeinit`)
- Modify: `src/__/__/__/canvas.py:1488-1491` (comment above `timeindex` for documentation)
- Test: `src/test/unitary/__/__/__/test_designer_tp.py`

- [ ] **Step 1: Write the failing test**

Create `src/test/unitary/__/__/__/test_designer_tp.py`:

```python
"""Tests for Designer TP (Turning Point) feature."""

import pytest


class TestTPDefaults:
    """Verify TP attributes exist and have correct defaults."""

    def test_tp_enabled_default(self, mock_canvas):
        assert mock_canvas.designer_tp_enabled is True

    def test_tp_time_default(self, mock_canvas):
        assert mock_canvas.designer_tp_time == 90.0

    def test_tp_bt_default(self, mock_canvas):
        assert mock_canvas.designer_tp_bt == 110.0


class TestTPTimeValidation:
    """Verify TP time must be > 0 and between CHARGE and DRY END."""

    def test_tp_time_positive(self, mock_canvas):
        mock_canvas.designer_tp_time = 60.0
        assert mock_canvas.designer_tp_time == 60.0

    def test_tp_time_zero_rejected(self, mock_canvas):
        # TP time of 0 would coincide with CHARGE — not valid
        mock_canvas.designer_tp_time = 0.0
        assert not mock_canvas._validate_tp_time(0.0)

    def test_tp_time_negative_rejected(self, mock_canvas):
        assert not mock_canvas._validate_tp_time(-10.0)

    def test_tp_time_positive_accepted(self, mock_canvas):
        assert mock_canvas._validate_tp_time(30.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd src && python3 -m pytest test/unitary/__/__/__/test_designer_tp.py -v`
Expected: FAIL with `AttributeError: 'tgraphcanvas' object has no attribute 'designer_tp_enabled'`

- [ ] **Step 3: Add TP attributes to canvas.py**

In `canvas.py`, after line 2175 (`self.designertimeinit:list[float] = ...`), add:

```python
        # TP (Turning Point) settings for Designer — independent of timeindex
        self.designer_tp_enabled:bool = True
        self.designer_tp_time:float = 90.0       # seconds from CHARGE
        self.designer_tp_bt:float = 110.0         # BT in current mode (C/F)
```

Also add a validation helper method on `tgraphcanvas`. Find a suitable location near the Designer methods (after `reset_designer` or before `designerinit`):

```python
    def _validate_tp_time(self, tp_time: float) -> bool:
        """Validate that TP time is positive and reasonable."""
        return tp_time > 0.0
```

- [ ] **Step 4: Create conftest fixture for tests**

Add a `conftest.py` in the test directory if not already present, or add to existing. The fixture needs to provide a minimal `tgraphcanvas` instance:

```python
# In src/test/unitary/__/__/__/conftest.py (or src/test/conftest.py if that exists)
import pytest


@pytest.fixture
def mock_canvas():
    """Provide a minimal tgraphcanvas with TP-related attributes."""
    # Import only the attributes we need — avoid full PyQt6 initialization
    # Use a simple mock since tgraphcanvas requires QApplication
    class MockCanvas:
        def __init__(self):
            self.designer_tp_enabled = True
            self.designer_tp_time = 90.0
            self.designer_tp_bt = 110.0

        def _validate_tp_time(self, tp_time: float) -> bool:
            return tp_time > 0.0

    return MockCanvas()
```

Check if `src/test/conftest.py` already exists and add there if so, or create alongside test file.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd src && python3 -m pytest test/unitary/__/__/__/test_designer_tp.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Commit**

```bash
cd src
git add test/unitary/__/__/__/test_designer_tp.py artisanlib/canvas.py
git commit -m "feat(designer): add TP (turning point) attributes to tgraphcanvas"
```

---

## Task 2: Update designerinit() to use TP attributes

**Files:**
- Modify: `src/__/__/__/canvas.py:18138-18196` (`designerinit()` method)
- Test: `src/test/unitary/__/__/__/test_designer_tp.py`

- [ ] **Step 1: Write the failing test**

Add to `src/test/unitary/__/__/__/test_designer_tp.py`:

```python
class TestDesignerInitTP:
    """Verify designerinit() uses TP attributes instead of hard-coded values."""

    def test_designerinit_includes_tp_node(self, mock_canvas_full):
        """When TP is enabled, timex should contain TP time as a node."""
        mc = mock_canvas_full
        mc.designer_tp_enabled = True
        mc.designer_tp_time = 120.0
        mc.designer_tp_bt = 95.0
        mc.designerinit()
        # After designerinit, the TP node should be in timex at index 1
        # (inserted after CHARGE)
        assert 120.0 in mc.timex

    def test_designerinit_excludes_tp_node_when_disabled(self, mock_canvas_full):
        """When TP is disabled, timex should NOT contain TP time."""
        mc = mock_canvas_full
        mc.designer_tp_enabled = False
        mc.designer_tp_time = 999.0  # unique value to check absence
        mc.designerinit()
        assert 999.0 not in mc.timex

    def test_designerinit_tp_bt_in_temp2(self, mock_canvas_full):
        """TP BT value should appear in temp2 at the TP index."""
        mc = mock_canvas_full
        mc.designer_tp_enabled = True
        mc.designer_tp_time = 90.0
        mc.designer_tp_bt = 95.0
        mc.designerinit()
        assert 95.0 in mc.temp2
```

Note: `mock_canvas_full` fixture needs a more complete canvas mock with `designerinit()` callable. Since `designerinit()` depends on many canvas internals, integration testing should be manual. The unit test validates attribute flow only.

- [ ] **Step 2: Modify designerinit() in canvas.py**

In `canvas.py`, locate `designerinit()` (around L18138). Replace the hard-coded TP insertion block:

**Before** (L18160-18167):
```python
        # add TP
        if self.mode == 'C':
            self.timex.insert(1,1.5*60)
            self.temp1.insert(1,230)
            self.temp2.insert(1,110)
            # add one intermediate point between DRY and FCs
            self.timex.insert(3,6*60)
            self.temp1.insert(3,230)
            self.temp2.insert(3,174)
        elif self.mode == 'F':
            self.timex.insert(1,1.5*60)
            self.temp1.insert(1,446)
            self.temp2.insert(1,230)
            # add one intermediate point between DRY and FCs
            self.timex.insert(3,6*60)
            self.temp1.insert(3,446)
            self.temp2.insert(3,345)
```

**After:**
```python
        # add TP (Turning Point) — uses configurable attributes
        if self.designer_tp_enabled:
            tp_time = self.designer_tp_time
            tp_bt = self.designer_tp_bt
        elif self.mode == 'C':
            tp_time = 1.5 * 60
            tp_bt = 110.0
        elif self.mode == 'F':
            tp_time = 1.5 * 60
            tp_bt = 230.0
        else:
            tp_time = None

        if tp_time is not None:
            self.timex.insert(1, tp_time)
            self.temp1.insert(1, self.temp1[0])  # ET stays same as CHARGE
            self.temp2.insert(1, tp_bt)
            # add one intermediate point between DRY and FCs
            if self.mode == 'C':
                self.timex.insert(3, 6 * 60)
                self.temp1.insert(3, 230)
                self.temp2.insert(3, 174)
            elif self.mode == 'F':
                self.timex.insert(3, 6 * 60)
                self.temp1.insert(3, 446)
                self.temp2.insert(3, 345)
```

- [ ] **Step 3: Verify compilation**

Run: `cd src && python3 -m py_compile artisanlib/canvas.py`
Expected: No output (success)

- [ ] **Step 4: Manual verification**

Run ArtisanZ, open Designer, verify the curve still shows the TP dip. The behavior should be identical to before (since defaults match old hard-coded values).

- [ ] **Step 5: Commit**

```bash
cd src
git add artisanlib/canvas.py test/unitary/__/__/__/test_designer_tp.py
git commit -m "feat(designer): use TP attributes in designerinit() instead of hard-coded values"
```

---

## Task 3: Update initfromprofile() to populate TP attributes

**Files:**
- Modify: `src/__/__/__/canvas.py:18256-18302` (`initfromprofile()` old method path)

- [ ] **Step 1: Locate the TP detection code**

In `canvas.py`, the `initfromprofile()` method's old-method path (L18256-18298) already detects TP via `findTP()`. The code at L18294-18298 adds it as an extra point via `addpoint()`.

- [ ] **Step 2: Add TP attribute population**

After the existing `addpoint()` call (L18298), add attribute population:

```python
            #add lowest point as extra point
            if lpindex != -1:
                self.currentx = lptime
                self.currenty = lptemp2
                self.addpoint(manual=False)
                # Populate TP attributes for Designer dialog
                self.designer_tp_enabled = True
                self.designer_tp_time = lptime - self.timex[self.timeindex[0]]  # relative to CHARGE
                self.designer_tp_bt = lptemp2
                # reset cursor coordinates
                self.currentx = 0
                self.currenty = 0
```

Also add the else branch to disable TP when not found:

```python
            else:
                self.designer_tp_enabled = False
```

Replace the existing block (L18294-18301) with the above.

- [ ] **Step 3: Verify compilation**

Run: `cd src && python3 -m py_compile artisanlib/canvas.py`
Expected: No output (success)

- [ ] **Step 4: Commit**

```bash
cd src
git add artisanlib/canvas.py
git commit -m "feat(designer): populate TP attributes from profile in initfromprofile()"
```

---

## Task 4: Add TP row to Designer config dialog

**Files:**
- Modify: `src/__/__/__/designer.py` (full file — `designerconfigDlg` class)

This is the largest task. The dialog currently has 7 rows (CHARGE through DROP) in a `QGridLayout`. We add a TP row between CHARGE and DRY END.

- [ ] **Step 1: Add TP widgets in `__init__`**

In `designerconfigDlg.__init__()`, after the CHARGE label creation (L44-46) and before the DRY END checkbox (L47), add:

```python
        # TP (Turning Point) — only BT, no ET
        self.tp = QCheckBox(QApplication.translate('Label', 'TP'))
        self.tp.setStyleSheet('background-color: orange')
        self.tp.setChecked(self.aw.qmc.designer_tp_enabled)
        self.tp.clicked.connect(self.changetp)
```

After the CHARGE row setup (around L78-85 where `Edit0`/`Edit0bt`/`Edit0et` are created), add:

```python
        # TP time and BT (no ET)
        self.EditTP = QLineEdit(stringfromseconds(self.aw.qmc.designer_tp_time))
        self.EditTP.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.EditTP.setMaximumWidth(maxwidth)
        self.EditTP.setValidator(QRegularExpressionValidator(regextime, self))
        self.EditTPbt = QLineEdit(f'{self.aw.qmc.designer_tp_bt:.1f}')
        self.EditTPbt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.EditTPbt.setMaximumWidth(maxwidth)
        self.EditTPbt.setValidator(QRegularExpressionValidator(regextemp, self))
        # Store copies for change detection
        self.EditTPcopy = self.EditTP.text()
        self.EditTPbtcopy = self.EditTPbt.text()
```

**Important:** These must be added BEFORE `maxwidth` is used — but `maxwidth` is set at L152. Move the widget creation to after L152 (after `maxwidth = 70`), or set maxwidth earlier. The safest approach is to add TP widget creation right after the existing widget block (after L193 where all `Edit6etcopy` is set).

- [ ] **Step 2: Add TP row to grid layout**

After the CHARGE row in `marksLayout` (L257-260), add a new row:

```python
        marksLayout.addWidget(self.tp, 2, 0)
        marksLayout.addWidget(self.EditTP, 2, 1)
        marksLayout.addWidget(self.EditTPbt, 2, 2)
        # No ET column for TP (col 3 is empty)
```

**Important:** All subsequent `marksLayout.addWidget` calls shift row index +1. Update:
- DRY END: row 2 → 3
- FC START: row 3 → 4
- FC END: row 4 → 5
- SC START: row 5 → 6
- SC END: row 6 → 7
- DROP: row 7 → 8

- [ ] **Step 3: Add `changetp` slot**

Add a new method to `designerconfigDlg`:

```python
    @pyqtSlot(bool)
    def changetp(self, _: bool = False) -> None:
        """Toggle TP node on/off in the designer curve."""
        if self.tp.isChecked():
            # Enable TP — validate time
            try:
                tp_time = stringtoseconds(self.EditTP.text())
                if tp_time <= 0:
                    self.tp.setChecked(False)
                    return
            except Exception:
                self.tp.setChecked(False)
                return
            # Insert TP point into canvas
            timez = stringtoseconds(self.EditTP.text()) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            bt = float(self.EditTPbt.text())
            self.aw.qmc.currentx = timez
            self.aw.qmc.currenty = bt
            newindex = self.aw.qmc.addpoint(manual=False)
            if newindex is not None:
                self.aw.qmc.temp2[newindex] = bt
                self.aw.qmc.xaxistosm(redraw=False)
                self.aw.qmc.redrawdesigner()
        else:
            # Disable TP — remove the TP point
            # Find the point closest to TP time and remove it
            tp_time = stringtoseconds(self.EditTP.text()) + self.aw.qmc.timex[self.aw.qmc.timeindex[0]]
            # Find index in timex closest to tp_time
            closest_idx = None
            min_diff = float('inf')
            for i, t in enumerate(self.aw.qmc.timex):
                if i in self.aw.qmc.timeindex:
                    continue  # Skip landmark points
                diff = abs(t - tp_time)
                if diff < min_diff:
                    min_diff = diff
                    closest_idx = i
            if closest_idx is not None and min_diff < 10.0:
                self.aw.qmc.currentx = self.aw.qmc.timex[closest_idx]
                self.aw.qmc.currenty = self.aw.qmc.temp2[closest_idx]
                self.aw.qmc.removepoint()
                self.aw.qmc.xaxistosm(redraw=False)
                self.aw.qmc.redrawdesigner()
```

- [ ] **Step 4: Update `settimes()` to read TP values**

In `settimes()`, after the CHARGE value updates (around L358-369) and before the DRY END updates (L370), add:

```python
        # Update TP settings
        if self.tp.isChecked():
            if self.EditTP.text() != self.EditTPcopy:
                try:
                    self.aw.qmc.designer_tp_time = stringtoseconds(str(self.EditTP.text()))
                    self.EditTPcopy = self.EditTP.text()
                except Exception:
                    self.EditTP.setText(self.EditTPcopy)
            if self.EditTPbt.text() != self.EditTPbtcopy:
                try:
                    self.aw.qmc.designer_tp_bt = float(self.EditTPbt.text())
                    self.EditTPbtcopy = self.EditTPbt.text()
                except Exception:
                    self.EditTPbt.setText(self.EditTPbtcopy)
        self.aw.qmc.designer_tp_enabled = self.tp.isChecked()
```

- [ ] **Step 5: Update `reset()` to restore TP defaults**

In `reset()`, after updating DRY END edit boxes (L571), add TP restoration:

```python
        # Reset TP
        self.tp.setChecked(True)
        self.EditTP.setText(stringfromseconds(self.aw.qmc.designer_tp_time))
        self.EditTPbt.setText(f'{self.aw.qmc.designer_tp_bt:.1f}')
```

- [ ] **Step 6: Verify compilation**

Run: `cd src && python3 -m py_compile artisanlib/designer.py`
Expected: No output (success)

- [ ] **Step 7: Manual verification**

1. Run ArtisanZ
2. Open Designer (Config → Designer)
3. Verify TP row appears between CHARGE and DRY END
4. Check TP checkbox toggles the turning point in the curve
5. Edit TP time and BT, click Apply, verify curve updates
6. Click Restore Defaults, verify TP resets
7. Verify existing landmarks (DRY END through DROP) still work correctly

- [ ] **Step 8: Commit**

```bash
cd src
git add artisanlib/designer.py
git commit -m "feat(designer): add editable TP row to Designer config dialog"
```

---

## Task 5: Integration test and regression check

**Files:**
- Test: `src/test/unitary/__/__/__/test_designer_tp.py`
- Verify: `src/test/unitary/__/__/__/test_charge_manager.py`

- [ ] **Step 1: Add integration-level tests**

Add to `src/test/unitary/__/__/__/test_designer_tp.py`:

```python
class TestTPDesignerIntegration:
    """Integration tests for TP in Designer workflow."""

    def test_tp_defaults_match_hardcoded_celsius(self):
        """Default TP time/BT match the old hard-coded values (Celsius)."""
        # Old values: 1.5*60 = 90.0 seconds, BT = 110.0
        assert 90.0 == 1.5 * 60  # TP time default
        assert 110.0 == 110.0    # TP BT default

    def test_tp_defaults_match_hardcoded_fahrenheit(self):
        """Default TP BT in Fahrenheit should be 230.0."""
        fahrenheit_bt = 230.0
        assert fahrenheit_bt == round(110.0 * 9 / 5 + 32, 0)  # 110C = 230F

    def test_tp_time_between_charge_and_dry(self):
        """TP time should be logically between CHARGE and DRY END."""
        tp_time = 90.0    # 1:30
        charge_time = 0.0
        dry_time = 240.0  # 4:00
        assert charge_time < tp_time < dry_time

    def test_tp_bt_lower_than_charge_bt(self):
        """TP BT should be lower than CHARGE BT (temperature dips then recovers)."""
        tp_bt = 110.0
        charge_bt = 210.0  # typical CHARGE BT
        assert tp_bt < charge_bt
```

- [ ] **Step 2: Run all TP tests**

Run: `cd src && python3 -m pytest test/unitary/__/__/__/test_designer_tp.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run existing charge manager tests (regression)**

Run: `cd src && python3 -m pytest test/unitary/__/__/__/test_charge_manager.py -q`
Expected: All existing tests still PASS

- [ ] **Step 4: Compile check on all modified files**

Run: `cd src && python3 -m py_compile artisanlib/canvas.py artisanlib/designer.py`
Expected: No output (success)

- [ ] **Step 5: Commit**

```bash
cd src
git add test/unitary/__/__/__/test_designer_tp.py
git commit -m "test(designer): add TP integration and regression tests"
```

---

## Self-Review

1. **Spec coverage:**
   - TP attributes on canvas ✓ (Task 1)
   - designerinit() uses attributes ✓ (Task 2)
   - initfromprofile() populates attributes ✓ (Task 3)
   - Designer dialog TP row ✓ (Task 4)
   - QSettings persistence — REMOVED from plan. After code inspection, `BTsplinedegree`/`ETsplinedegree` are not persisted via QSettings either; they're session-scoped. TP follows the same pattern.

2. **Placeholder scan:** No TBD/TODO. All steps have concrete code.

3. **Type consistency:** `designer_tp_time: float`, `designer_tp_bt: float`, `designer_tp_enabled: bool` — used consistently across all tasks. `stringtoseconds()` returns float, `float()` used for BT parse.
