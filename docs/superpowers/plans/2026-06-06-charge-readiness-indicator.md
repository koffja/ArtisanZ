# Charge Readiness Indicator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade ArtisanZ's existing charge target feature into a simple pre-charge readiness indicator that shows users a small operational decision instead of many raw metrics.

**Architecture:** Keep readiness logic in `ChargeTargetManager` as testable pure Python. Keep `canvas.py` responsible for collecting live values and rendering the existing chart annotation. Keep `charge_dialog.py` simple; it remains a target-setting dialog, not a diagnostic dashboard.

**Tech Stack:** Python 3.12+, PyQt6, matplotlib annotations, Artisan symbolic/Virtual-device settings, pytest.

---

## Scope and Constraints

- Work on the `ArtisanZ` branch only.
- Do not commit or push unless the user explicitly requests it in the execution session.
- Do not change `.aset`, `.alog`, or QSettings schema for this feature.
- Do not add type suppression such as `as any`, `@ts-ignore`, or Python broad hacks.
- User-facing Chinese must be short and clear; avoid unexplained English jargon.
- The default user view should not require watching 5-10 Virtual LCD values.
- Preserve the existing optional Virtual formulas for advanced analysis, but reduce what is shown by default in the ArtisanZ preset.

## File Structure

### Files to Modify

- `src/artisanlib/charge_manager.py`
  - Add a `ChargeReadiness` dataclass and a `ReadinessStatus` type alias.
  - Add `evaluate_readiness(...)` as the single source of truth for pre-charge state.
  - Keep existing `predict(...)`, `calculate_rwt(...)`, and `calculate_ror(...)` behavior compatible.
  - Update `get_status_message(...)` to call `evaluate_readiness(...)` for backward-compatible text and color.

- `src/test/unitary/artisanlib/test_charge_manager.py`
  - Replace the old `should_show_annotation()` expectation with readiness-centered tests.
  - Add tests for ready, near, hot, unstable, waiting, and insufficient-data states.

- `src/artisanlib/canvas.py`
  - Add small helper methods near `draw_charge_target_annotation()` for pre-charge context:
    - `_charge_window_average_delta(...)`
    - `_charge_et_bt_gap(...)`
  - Replace the active-state annotation text with the readiness result.
  - Keep the already-charged annotation unchanged in this implementation pass.

- `src/includes/artisan-adv-setting-260604.aset`
  - Keep the Virtual formulas and labels intact.
  - Change default `extraLCDvisibility1/2` so only a small subset appears by default.
  - Do not alter the `[ExtraDev]` list lengths or QSettings format.

### Files to Verify but Not Modify Unless Needed

- `src/artisanlib/charge_dialog.py`
  - Confirm the dialog still works with unchanged setting fields.

- `src/artisanlib/main.py`
  - Confirm no new settings keys are needed.
  - Confirm `showChargeTargetDialog()` still opens and calls `self.qmc.update()` after save.

---

## Readiness Model

### Status Values

Use these exact status strings internally:

```python
ReadinessStatus = Literal['insufficient', 'waiting', 'near', 'ready', 'hot', 'unstable']
```

### User-Facing Messages

| Internal status | Display title | Display reason |
|---|---|---|
| `insufficient` | `等待数据` | `升温数据不足` |
| `waiting` | `等待升温` | `距离目标还远` |
| `near` | `接近目标` | `接近目标，继续观察` |
| `ready` | `可以投豆` | `温度到位，升温稳定` |
| `hot` | `偏热` | `温度超过目标` |
| `unstable` | `趋势不稳` | `升温变化过大` |

### Readiness Inputs

- `current_temp`: current BT.
- `current_ror`: current BT RoR.
- `short_ror`: BT RoR average over roughly 6-10 seconds.
- `long_ror`: BT RoR average over roughly 20-30 seconds.
- `et_bt_gap`: current ET minus current BT.
- `reference_et_bt_gap`: optional future input, left as `None` in the first implementation.

### Readiness Logic

Use the simplest deterministic rule that matches roasting discussion:

1. If BT or BT RoR is missing, not finite, or BT RoR is non-positive, return `insufficient`.
2. If BT is above target temperature plus tolerance, return `hot`.
3. Compute prediction with the existing `predict(current_temp, current_ror)`.
4. Compute trend instability if both `short_ror` and `long_ror` are valid and `abs(short_ror - long_ror) > max(1.5, ror_tolerance / 2)`.
5. If BT is within temperature tolerance and RoR is within RoR tolerance:
   - return `ready` when trend is stable;
   - return `unstable` when trend is unstable.
6. If BT is within temperature tolerance but RoR is outside tolerance, return `unstable`.
7. If prediction is valid and `prediction <= max(10.0, prediction_window)`, return `near`.
8. Otherwise return `waiting`.

---

## Task 1: Add Readiness Tests First

**Files:**
- Modify: `src/test/unitary/artisanlib/test_charge_manager.py`
- Verify: `src/artisanlib/charge_manager.py`

- [ ] **Step 1: Replace `test_should_show_annotation` with readiness tests**

Replace lines 53-66 in `src/test/unitary/artisanlib/test_charge_manager.py` with this exact block:

```python
    def test_should_show_annotation_tracks_enabled_flag(self):
        manager = ChargeTargetManager()
        assert manager.should_show_annotation() is False

        manager.update_settings(200.0, 60.0, True)
        assert manager.should_show_annotation() is True

        manager.update_settings(200.0, 60.0, False)
        assert manager.should_show_annotation() is False

    def test_readiness_ready_when_temperature_and_ror_match(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(
            current_temp=200.2,
            current_ror=59.0,
            short_ror=59.5,
            long_ror=59.0,
        )

        assert readiness.status == 'ready'
        assert readiness.color == 'green'
        assert readiness.title == '可以投豆'
        assert readiness.reason == '温度到位，升温稳定'
        assert readiness.prediction_seconds == 0.0
        assert readiness.current_rwt == pytest.approx(600.0 / 59.0)
        assert readiness.target_rwt == pytest.approx(10.0)

    def test_readiness_near_when_prediction_is_short(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(
            current_temp=194.0,
            current_ror=60.0,
            short_ror=60.0,
            long_ror=60.0,
        )

        assert readiness.status == 'near'
        assert readiness.color == 'green'
        assert readiness.title == '接近目标'
        assert readiness.prediction_seconds == pytest.approx(6.0)

    def test_readiness_hot_when_temperature_exceeds_tolerance(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(current_temp=202.0, current_ror=50.0)

        assert readiness.status == 'hot'
        assert readiness.color == 'red'
        assert readiness.title == '偏热'
        assert readiness.reason == '温度超过目标'

    def test_readiness_unstable_when_ror_trend_changes_too_fast(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(
            current_temp=200.0,
            current_ror=60.0,
            short_ror=66.0,
            long_ror=60.0,
        )

        assert readiness.status == 'unstable'
        assert readiness.color == 'blue'
        assert readiness.title == '趋势不稳'
        assert readiness.reason == '升温变化过大'

    def test_readiness_waiting_when_far_from_target(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(current_temp=180.0, current_ror=30.0)

        assert readiness.status == 'waiting'
        assert readiness.color == 'gray'
        assert readiness.title == '等待升温'
        assert readiness.reason == '距离目标还远'

    def test_readiness_insufficient_when_ror_is_invalid(self):
        manager = ChargeTargetManager()
        manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

        readiness = manager.evaluate_readiness(current_temp=198.0, current_ror=0.0)

        assert readiness.status == 'insufficient'
        assert readiness.color == 'gray'
        assert readiness.title == '等待数据'
        assert readiness.reason == '升温数据不足'
        assert readiness.prediction_seconds is None
```

- [ ] **Step 2: Run the focused tests and confirm the expected failure**

Run from repo root:

```bash
cd src
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q
```

Expected result before implementation:

```text
FAILED test/unitary/artisanlib/test_charge_manager.py::TestChargeTargetManager::test_readiness_ready_when_temperature_and_ror_match
AttributeError: 'ChargeTargetManager' object has no attribute 'evaluate_readiness'
```

- [ ] **Step 3: Review the diff and do not commit yet**

Run from repo root:

```bash
git diff -- src/test/unitary/artisanlib/test_charge_manager.py
```

Expected: only `test_should_show_annotation` changed and six readiness tests were added.

---

## Task 2: Implement the Pure Readiness Model

**Files:**
- Modify: `src/artisanlib/charge_manager.py:1-120`
- Test: `src/test/unitary/artisanlib/test_charge_manager.py`

- [ ] **Step 1: Update imports and add dataclass definitions**

Replace line 1 in `src/artisanlib/charge_manager.py` with:

```python
from dataclasses import dataclass
import math
from typing import Literal, Optional, Tuple


ReadinessStatus = Literal['insufficient', 'waiting', 'near', 'ready', 'hot', 'unstable']


@dataclass(frozen=True)
class ChargeReadiness:
    status: ReadinessStatus
    title: str
    reason: str
    color: str
    prediction_seconds: Optional[float]
    current_rwt: float
    target_rwt: float
```

- [ ] **Step 2: Add finite-number helper methods inside `ChargeTargetManager`**

Insert these methods after `reset()`:

```python
    @staticmethod
    def _is_valid_number(value: Optional[float]) -> bool:
        return value is not None and math.isfinite(value)

    @staticmethod
    def _is_valid_positive_number(value: Optional[float]) -> bool:
        return value is not None and math.isfinite(value) and value > 0
```

- [ ] **Step 3: Add `evaluate_readiness(...)` after `predict(...)`**

Insert this method after `predict(...)` and before `should_show_annotation(...)`:

```python
    def evaluate_readiness(
        self,
        current_temp: float,
        current_ror: Optional[float],
        short_ror: Optional[float] = None,
        long_ror: Optional[float] = None,
        et_bt_gap: Optional[float] = None,
        reference_et_bt_gap: Optional[float] = None,
    ) -> ChargeReadiness:
        target_rwt = self.calculate_rwt(self.target_ror)
        current_rwt = self.calculate_rwt(current_ror)

        if not self._is_valid_number(current_temp) or not self._is_valid_positive_number(current_ror):
            self.prediction_time = None
            return ChargeReadiness(
                status='insufficient',
                title='等待数据',
                reason='升温数据不足',
                color='gray',
                prediction_seconds=None,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        if current_temp > self.target_temp + self.temp_tolerance:
            self.prediction_time = 0.0
            return ChargeReadiness(
                status='hot',
                title='偏热',
                reason='温度超过目标',
                color='red',
                prediction_seconds=0.0,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        prediction_seconds = self.predict(current_temp, current_ror)
        temp_in_range = abs(current_temp - self.target_temp) <= self.temp_tolerance
        ror_in_range = abs(current_ror - self.target_ror) <= self.ror_tolerance

        trend_limit = max(1.5, self.ror_tolerance / 2.0)
        trend_unstable = (
            self._is_valid_number(short_ror)
            and self._is_valid_number(long_ror)
            and abs(short_ror - long_ror) > trend_limit
        )

        heat_gap_limit = max(3.0, self.temp_tolerance * 2.0)
        heat_gap_unstable = (
            self._is_valid_number(et_bt_gap)
            and self._is_valid_number(reference_et_bt_gap)
            and abs(et_bt_gap - reference_et_bt_gap) > heat_gap_limit
        )

        if temp_in_range and ror_in_range and not trend_unstable and not heat_gap_unstable:
            return ChargeReadiness(
                status='ready',
                title='可以投豆',
                reason='温度到位，升温稳定',
                color='green',
                prediction_seconds=prediction_seconds,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        if temp_in_range and (trend_unstable or heat_gap_unstable or not ror_in_range):
            reason = '升温变化过大' if trend_unstable else '升温偏离目标'
            if heat_gap_unstable:
                reason = '炉内热状态偏离参考'
            return ChargeReadiness(
                status='unstable',
                title='趋势不稳',
                reason=reason,
                color='blue',
                prediction_seconds=prediction_seconds,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        near_window = max(10.0, self.prediction_window)
        if prediction_seconds is not None and prediction_seconds <= near_window:
            return ChargeReadiness(
                status='near',
                title='接近目标',
                reason='接近目标，继续观察',
                color='green',
                prediction_seconds=prediction_seconds,
                current_rwt=current_rwt,
                target_rwt=target_rwt,
            )

        return ChargeReadiness(
            status='waiting',
            title='等待升温',
            reason='距离目标还远',
            color='gray',
            prediction_seconds=prediction_seconds,
            current_rwt=current_rwt,
            target_rwt=target_rwt,
        )
```

- [ ] **Step 4: Update `get_status_message(...)` to use readiness**

Replace the body of `get_status_message(...)` with:

```python
        readiness = self.evaluate_readiness(current_temp=current_temp, current_ror=current_ror)
        return readiness.reason, readiness.color
```

The full method should read:

```python
    def get_status_message(self, current_ror: Optional[float], current_temp: float) -> Tuple[str, str]:
        """
        Returns a tuple of (Message, ColorString) based on Temp and RoR comparison.
        """
        readiness = self.evaluate_readiness(current_temp=current_temp, current_ror=current_ror)
        return readiness.reason, readiness.color
```

- [ ] **Step 5: Run the focused tests and confirm they pass**

Run from repo root:

```bash
cd src
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q
```

Expected:

```text
13 passed
```

- [ ] **Step 6: Run py_compile for the pure logic files**

Run from repo root:

```bash
cd src
python3 -m py_compile artisanlib/charge_manager.py test/unitary/artisanlib/test_charge_manager.py
```

Expected: no output and exit code 0.

- [ ] **Step 7: Review the diff and do not commit yet**

Run from repo root:

```bash
git diff -- src/artisanlib/charge_manager.py src/test/unitary/artisanlib/test_charge_manager.py
```

Expected: `ChargeReadiness`, `ReadinessStatus`, and `evaluate_readiness(...)` were added; tests cover the new statuses.

---

## Task 3: Feed Live Trend Context Into the Chart Annotation

**Files:**
- Modify: `src/artisanlib/canvas.py:18380-18535`
- Test: `src/test/unitary/artisanlib/test_charge_manager.py`

- [ ] **Step 1: Add a helper for averaging recent RoR values**

Insert this method immediately after `set_charge_manager(...)` in `src/artisanlib/canvas.py`:

```python
    def _charge_window_average_delta(self, window_seconds: float) -> Optional[float]:
        if not hasattr(self, 'timex') or not hasattr(self, 'delta2'):
            return None
        if len(self.timex) < 2 or len(self.delta2) < 2:
            return None

        latest_time = self.timex[-1]
        values: list[float] = []
        for idx in range(len(self.delta2) - 1, -1, -1):
            if idx >= len(self.timex):
                continue
            if latest_time - self.timex[idx] > window_seconds:
                break
            value = self.delta2[idx]
            if value is not None and value > 0:
                values.append(value)

        if not values:
            return None
        return sum(values) / len(values)
```

- [ ] **Step 2: Add a helper for ET-BT gap**

Insert this method after `_charge_window_average_delta(...)`:

```python
    def _charge_et_bt_gap(self) -> Optional[float]:
        if not hasattr(self, 'temp1') or not hasattr(self, 'temp2'):
            return None
        if len(self.temp1) == 0 or len(self.temp2) == 0:
            return None
        et = self.temp1[-1]
        bt = self.temp2[-1]
        if et is None or bt is None:
            return None
        return et - bt
```

- [ ] **Step 3: Replace active-state readiness calculation**

In `draw_charge_target_annotation(...)`, find this existing block:

```python
            # --- ACTIVE STATE (Dynamic) ---
            pred_time = self.charge_manager.predict(current_temp, current_ror)
            status_msg, color = self.charge_manager.get_status_message(current_ror, current_temp)
```

Replace it with:

```python
            # --- ACTIVE STATE (Dynamic) ---
            short_ror = self._charge_window_average_delta(9.0)
            long_ror = self._charge_window_average_delta(30.0)
            readiness = self.charge_manager.evaluate_readiness(
                current_temp=current_temp,
                current_ror=current_ror,
                short_ror=short_ror,
                long_ror=long_ror,
                et_bt_gap=self._charge_et_bt_gap(),
            )
            pred_time = readiness.prediction_seconds
            color = readiness.color
```

- [ ] **Step 4: Replace active annotation text with operational wording**

In the active-state section, find this existing `lines = [...]` block:

```python
                lines = [
                    f'【目标】 温:{target_temp:.1f}° | RoR:{tror_str} | RWT:{trwt_str}',
                    f'【当前】 温:{current_temp:.1f}° | RoR:{ror_val_str} | RWT:{rwt_str}',
                    '──────────────────────',
                    f'预计到达: {time_str}',
                    f'[{status_msg}]'
                ]
```

Replace it with:

```python
                lines = [
                    f'【{readiness.title}】',
                    f'预计: {time_str}',
                    f'原因: {readiness.reason}',
                    '──────────────────────',
                    f'目标 {target_temp:.1f}° / {tror_str}',
                    f'当前 {current_temp:.1f}° / {ror_val_str}',
                    f'升10° {rwt_str} / 目标 {trwt_str}',
                ]
```

- [ ] **Step 5: Run py_compile for the chart integration**

Run from repo root:

```bash
cd src
python3 -m py_compile artisanlib/canvas.py artisanlib/charge_manager.py
```

Expected: no output and exit code 0.

- [ ] **Step 6: Run focused charge manager tests**

Run from repo root:

```bash
cd src
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q
```

Expected:

```text
13 passed
```

- [ ] **Step 7: Review the diff and do not commit yet**

Run from repo root:

```bash
git diff -- src/artisanlib/canvas.py src/artisanlib/charge_manager.py
```

Expected: `canvas.py` gained only the two small helper methods and the active annotation now displays title, estimate, reason, and compact target/current values.

---

## Task 4: Reduce Default Virtual LCD Noise in the ArtisanZ Preset

**Files:**
- Modify: `src/includes/artisan-adv-setting-260604.aset:480-496`

- [ ] **Step 1: Keep formulas but reduce default visible LCD count**

In `src/includes/artisan-adv-setting-260604.aset`, replace lines 488-489:

```ini
extraLCDvisibility1=true, true, true, true, true, false, false, false, false, false
extraLCDvisibility2=true, true, true, true, true, false, false, false, false, false
```

with:

```ini
extraLCDvisibility1=true, false, true, false, false, false, false, false, false, false
extraLCDvisibility2=false, true, false, false, false, false, false, false, false, false
```

This keeps only three default LCDs visible:

- `BT Δ Dry`
- `ETA FCs`
- `ET-BT Δ`

All other formulas remain available in the device table for advanced users.

- [ ] **Step 2: Verify `[ExtraDev]` list lengths remain aligned**

Run this command from repo root:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path('src/includes/artisan-adv-setting-260604.aset')
lines = path.read_text(encoding='utf-8').splitlines()
keys = {
    'extraLCDvisibility1': 10,
    'extraLCDvisibility2': 10,
    'extraCurveVisibility1': 10,
    'extraCurveVisibility2': 10,
    'extradevices': 5,
    'extraname1': 5,
    'extraname2': 5,
}

def split_values(value: str) -> list[str]:
    return [part.strip() for part in value.split(',')]

seen: dict[str, int] = {}
for line in lines:
    for key, expected_count in keys.items():
        if line.startswith(f'{key}='):
            values = split_values(line.split('=', 1)[1])
            seen[key] = len(values)
            assert len(values) == expected_count, (key, len(values), expected_count)

missing = sorted(set(keys) - set(seen))
assert not missing, missing
print('ExtraDev list lengths OK')
PY
```

Expected:

```text
ExtraDev list lengths OK
```

- [ ] **Step 3: Review the diff and do not commit yet**

Run from repo root:

```bash
git diff -- src/includes/artisan-adv-setting-260604.aset
```

Expected: only `extraLCDvisibility1` and `extraLCDvisibility2` changed.

---

## Task 5: Add a Small Manual Smoke Script for Readiness Text

**Files:**
- Create: `src/test/unitary/artisanlib/test_charge_readiness_annotation_text.py`
- Verify: `src/artisanlib/charge_manager.py`

- [ ] **Step 1: Add tests for short Chinese text length and compatibility**

Create `src/test/unitary/artisanlib/test_charge_readiness_annotation_text.py` with:

```python
from artisanlib.charge_manager import ChargeTargetManager


def test_readiness_user_facing_text_is_short():
    manager = ChargeTargetManager()
    manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

    readiness = manager.evaluate_readiness(200.0, 60.0, short_ror=60.0, long_ror=60.0)

    assert readiness.title == '可以投豆'
    assert len(readiness.title) <= 6
    assert readiness.reason == '温度到位，升温稳定'
    assert len(readiness.reason) <= 12


def test_legacy_status_message_uses_readiness_reason_and_color():
    manager = ChargeTargetManager()
    manager.update_settings(200.0, 60.0, True, temp_tolerance=1.0, ror_tolerance=3.0)

    message, color = manager.get_status_message(current_ror=60.0, current_temp=200.0)

    assert message == '温度到位，升温稳定'
    assert color == 'green'
```

- [ ] **Step 2: Run the new tests**

Run from repo root:

```bash
cd src
python3 -m pytest test/unitary/artisanlib/test_charge_readiness_annotation_text.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 3: Run both charge-related test files**

Run from repo root:

```bash
cd src
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_charge_readiness_annotation_text.py -q
```

Expected:

```text
15 passed
```

- [ ] **Step 4: Review the diff and do not commit yet**

Run from repo root:

```bash
git diff -- src/test/unitary/artisanlib/test_charge_readiness_annotation_text.py src/artisanlib/charge_manager.py
```

Expected: new tests only assert concise Chinese text and backward-compatible `get_status_message(...)` behavior.

---

## Task 6: Final Verification

**Files:**
- Verify: `src/artisanlib/charge_manager.py`
- Verify: `src/artisanlib/canvas.py`
- Verify: `src/artisanlib/charge_dialog.py`
- Verify: `src/artisanlib/main.py`
- Verify: `src/includes/artisan-adv-setting-260604.aset`
- Verify: `src/test/unitary/artisanlib/test_charge_manager.py`
- Verify: `src/test/unitary/artisanlib/test_charge_readiness_annotation_text.py`

- [ ] **Step 1: Run focused py_compile**

Run from repo root:

```bash
cd src
python3 -m py_compile artisanlib/charge_manager.py artisanlib/canvas.py artisanlib/charge_dialog.py artisanlib/main.py test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_charge_readiness_annotation_text.py
```

Expected: no output and exit code 0.

- [ ] **Step 2: Run focused tests**

Run from repo root:

```bash
cd src
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py test/unitary/artisanlib/test_charge_readiness_annotation_text.py -q
```

Expected:

```text
15 passed
```

- [ ] **Step 3: Run the existing ArtisanZ charge-feature verification subset**

Run from repo root:

```bash
cd src
python3 -m py_compile artisanlib/charge_manager.py artisanlib/charge_dialog.py artisanlib/main.py artisanlib/canvas.py
python3 -m pytest test/unitary/artisanlib/test_charge_manager.py -q
```

Expected:

```text
13 passed
```

- [ ] **Step 4: Inspect working tree**

Run from repo root:

```bash
git status --short
```

Expected modified or created files only in:

```text
M src/artisanlib/charge_manager.py
M src/artisanlib/canvas.py
M src/includes/artisan-adv-setting-260604.aset
M src/test/unitary/artisanlib/test_charge_manager.py
?? src/test/unitary/artisanlib/test_charge_readiness_annotation_text.py
```

The existing untracked `.research/` path may still appear and must not be staged or modified.

- [ ] **Step 5: Produce a verification summary**

Write a final implementation summary containing:

```text
Implemented:
- Added ChargeReadiness/evaluate_readiness in charge_manager.py.
- Updated chart annotation to show 状态/预计/原因 instead of raw-heavy text.
- Reduced default Virtual LCD visibility in artisan-adv-setting-260604.aset.

Verified:
- py_compile charge_manager.py charge_dialog.py main.py canvas.py passed.
- pytest test_charge_manager.py passed.
- pytest test_charge_readiness_annotation_text.py passed.

Not committed:
- No git commit was created because repository rules require explicit user request.
```

---

## Self-Review Checklist

- Spec coverage:
  - Simple user view: Task 3 changes annotation to status, estimate, reason.
  - Rich internal parameters: Task 2 supports current BT, BT RoR, short/long trend, ET-BT gap, optional reference gap.
  - Existing ArtisanZ charge feature: Task 2 extends `ChargeTargetManager`; Task 3 reuses `draw_charge_target_annotation()`.
  - Existing BT pre-charge RoR: Task 3 passes `current_ror` and window averages from live `delta2`.
  - Reduce Virtual noise: Task 4 lowers default visible LCD count without changing formulas.
  - Tests: Tasks 1, 2, 5, and 6 cover focused behavior.
- Placeholder scan:
  - This plan contains no undefined functions except those created in earlier steps.
  - This plan contains no deferred implementation instructions.
- Type consistency:
  - `ChargeReadiness`, `ReadinessStatus`, and `evaluate_readiness(...)` names are consistent across tests and implementation steps.
  - `prediction_seconds`, `current_rwt`, and `target_rwt` property names are consistent across tests and UI integration.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-06-charge-readiness-indicator.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Choose one approach before implementation begins.
